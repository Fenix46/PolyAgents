"""Security module for API authentication, rate limiting, and validation."""

import asyncio
import hashlib
import logging
import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Permission constants for API access control."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class SecurityConfig:
    """Security configuration settings."""

    # JWT settings
    JWT_SECRET_KEY = settings.jwt_secret_key if hasattr(settings, 'jwt_secret_key') else secrets.token_urlsafe(32)
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

    # Rate limiting settings
    RATE_LIMIT_REQUESTS = 100  # requests per window
    RATE_LIMIT_WINDOW = 3600   # window in seconds (1 hour)
    RATE_LIMIT_BURST = 10      # burst allowance

    # API Key settings
    API_KEY_LENGTH = 32
    API_KEY_PREFIX = "pa_"  # PolyAgents prefix


class APIKey(BaseModel):
    """API Key model."""
    key_id: str
    key_hash: str
    name: str
    permissions: list[str]
    created_at: datetime
    last_used: datetime | None = None
    is_active: bool = True
    usage_count: int = 0


class RateLimitInfo(BaseModel):
    """Rate limit information."""
    requests_made: int
    window_start: float
    burst_tokens: int
    blocked_until: float | None = None


class AuthToken(BaseModel):
    """Authentication token model."""
    user_id: str
    permissions: list[str]
    issued_at: datetime
    expires_at: datetime


class SecurityManager:
    """Main security manager for authentication and rate limiting."""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.api_keys: dict[str, APIKey] = {}
        self.rate_limits: dict[str, RateLimitInfo] = defaultdict(
            lambda: RateLimitInfo(
                requests_made=0,
                window_start=time.time(),
                burst_tokens=SecurityConfig.RATE_LIMIT_BURST
            )
        )
        self.blocked_ips: dict[str, float] = {}
        self._cleanup_task: asyncio.Task | None = None

        # Load default API keys if configured
        self._load_default_keys()

    def _load_default_keys(self):
        """Load default API keys from configuration."""
        if hasattr(settings, 'default_api_keys') and settings.default_api_keys:
            try:
                import json
                keys_config = json.loads(settings.default_api_keys)
                for key_config in keys_config:
                    self.create_api_key(
                        name=key_config.get('name', 'Default'),
                        permissions=key_config.get('permissions', ['chat:read', 'chat:write']),
                        key_value=key_config.get('key')
                    )
                logger.info(f"Loaded {len(keys_config)} default API keys")
            except Exception as e:
                logger.warning(f"Failed to load default API keys: {e}")

    def start_cleanup_task(self):
        """Start background cleanup task."""
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self):
        """Background cleanup of expired rate limits and blocks."""
        try:
            while True:
                await asyncio.sleep(300)  # Run every 5 minutes
                current_time = time.time()

                # Clean up expired rate limits
                expired_limits = [
                    key for key, limit in self.rate_limits.items()
                    if current_time - limit.window_start > SecurityConfig.RATE_LIMIT_WINDOW * 2
                ]
                for key in expired_limits:
                    del self.rate_limits[key]

                # Clean up expired IP blocks
                expired_blocks = [
                    ip for ip, block_time in self.blocked_ips.items()
                    if current_time > block_time
                ]
                for ip in expired_blocks:
                    del self.blocked_ips[ip]

                logger.debug(f"Cleaned up {len(expired_limits)} rate limits and {len(expired_blocks)} IP blocks")

        except asyncio.CancelledError:
            logger.info("Security cleanup task cancelled")

    def hash_key(self, key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    def generate_api_key(self) -> str:
        """Generate a new API key."""
        return f"{SecurityConfig.API_KEY_PREFIX}{secrets.token_urlsafe(SecurityConfig.API_KEY_LENGTH)}"

    def create_api_key(
        self,
        name: str,
        permissions: list[str],
        key_value: str | None = None
    ) -> str:
        """Create a new API key."""
        if not key_value:
            key_value = self.generate_api_key()

        key_id = secrets.token_urlsafe(16)
        key_hash = self.hash_key(key_value)

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            created_at=datetime.utcnow()
        )

        self.api_keys[key_hash] = api_key
        logger.info(f"Created API key '{name}' with permissions: {permissions}")

        return key_value

    def validate_api_key(self, key: str) -> APIKey | None:
        """Validate an API key and return associated data."""
        if not key or not key.startswith(SecurityConfig.API_KEY_PREFIX):
            return None

        key_hash = self.hash_key(key)
        api_key = self.api_keys.get(key_hash)

        if api_key and api_key.is_active:
            # Update usage statistics
            api_key.last_used = datetime.utcnow()
            api_key.usage_count += 1
            return api_key

        return None

    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key."""
        key_hash = self.hash_key(key)
        if key_hash in self.api_keys:
            self.api_keys[key_hash].is_active = False
            logger.info(f"Revoked API key: {self.api_keys[key_hash].name}")
            return True
        return False

    def check_permission(self, api_key: APIKey, required_permission: str) -> bool:
        """Check if API key has required permission."""
        if not api_key or not api_key.is_active:
            return False

        # Admin permission grants all access
        if "admin:all" in api_key.permissions:
            return True

        # Check for specific permission
        return required_permission in api_key.permissions

    def _check_rate_limit_internal(self, identifier: str) -> tuple[bool, dict[str, Any]]:
        """Check rate limit for an identifier."""
        current_time = time.time()
        rate_limit = self.rate_limits[identifier]

        # Check if we're in a new window
        if current_time - rate_limit.window_start > SecurityConfig.RATE_LIMIT_WINDOW:
            rate_limit.requests_made = 0
            rate_limit.window_start = current_time
            rate_limit.burst_tokens = SecurityConfig.RATE_LIMIT_BURST
            rate_limit.blocked_until = None

        # Check if currently blocked
        if rate_limit.blocked_until and current_time < rate_limit.blocked_until:
            retry_after = int(rate_limit.blocked_until - current_time)
            return False, {
                "blocked": True,
                "retry_after": retry_after,
                "reason": "Rate limit exceeded"
            }

        # Check burst tokens first
        if rate_limit.burst_tokens > 0:
            rate_limit.burst_tokens -= 1
            return True, {"burst_used": True}

        # Check regular rate limit
        if rate_limit.requests_made < SecurityConfig.RATE_LIMIT_REQUESTS:
            rate_limit.requests_made += 1
            return True, {"requests_remaining": SecurityConfig.RATE_LIMIT_REQUESTS - rate_limit.requests_made}

        # Rate limit exceeded - block for a period
        block_duration = min(300, SecurityConfig.RATE_LIMIT_WINDOW)  # Block for up to 5 minutes
        rate_limit.blocked_until = current_time + block_duration

        return False, {
            "blocked": True,
            "retry_after": block_duration,
            "reason": "Rate limit exceeded"
        }

    async def check_rate_limit(self, client_id: str, client_ip: str) -> None:
        """Check rate limit for a client."""
        identifier = f"{client_id}:{client_ip}"
        allowed, info = self._check_rate_limit_internal(identifier)

        if not allowed:
            raise ValueError(f"Rate limit exceeded. Try again in {info.get('retry_after', 60)} seconds")

    def generate_jwt_token(self, user_id: str, permissions: list[str]) -> str:
        """Generate JWT token for user."""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=SecurityConfig.JWT_EXPIRATION_HOURS)

        payload = {
            "user_id": user_id,
            "permissions": permissions,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": "polyagents"
        }

        return jwt.encode(payload, SecurityConfig.JWT_SECRET_KEY, algorithm=SecurityConfig.JWT_ALGORITHM)

    def validate_jwt_token(self, token: str) -> AuthToken | None:
        """Validate JWT token and return user data."""
        try:
            payload = jwt.decode(
                token,
                SecurityConfig.JWT_SECRET_KEY,
                algorithms=[SecurityConfig.JWT_ALGORITHM]
            )

            return AuthToken(
                user_id=payload["user_id"],
                permissions=payload["permissions"],
                issued_at=datetime.fromtimestamp(payload["iat"]),
                expires_at=datetime.fromtimestamp(payload["exp"])
            )

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def initialize(self) -> None:
        """Initialize the security manager."""
        logger.info("Initializing SecurityManager")
        self.start_cleanup_task()

    async def start_background_tasks(self) -> None:
        """Start background tasks (alias for start_cleanup_task)."""
        self.start_cleanup_task()

    async def cleanup(self) -> None:
        """Clean up the security manager."""
        logger.info("Cleaning up SecurityManager")
        await self.stop_cleanup_task()

    async def verify_api_key(self, api_key: str) -> dict[str, Any]:
        """Verify API key and return user info."""
        if not api_key:
            raise ValueError("API key is required")

        api_key_data = self.validate_api_key(api_key)
        if not api_key_data:
            raise ValueError("Invalid API key")

        return {
            "authenticated": True,
            "client_id": api_key_data.key_id,
            "permissions": api_key_data.permissions,
            "name": api_key_data.name
        }

    async def check_rate_limit(self, client_id: str, client_ip: str) -> None:
        """Check rate limit for a client."""
        identifier = f"{client_id}:{client_ip}"
        allowed, info = self._check_rate_limit_internal(identifier)

        if not allowed:
            raise ValueError(f"Rate limit exceeded. Try again in {info.get('retry_after', 60)} seconds")


# Global security manager instance
security_manager = SecurityManager()

# FastAPI security schemes
bearer_scheme = HTTPBearer(auto_error=False)


class InputValidator:
    """Input validation and sanitization utilities."""

    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        """Sanitize text input."""
        if not text:
            return ""

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]

        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

        return text.strip()

    @staticmethod
    def validate_conversation_id(conversation_id: str) -> str:
        """Validate conversation ID format."""
        if not conversation_id:
            raise ValueError("Conversation ID cannot be empty")

        # Should be UUID format or similar safe string
        if len(conversation_id) > 100:
            raise ValueError("Conversation ID too long")

        # Only allow alphanumeric, hyphens, and underscores
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        if not all(c in allowed_chars for c in conversation_id):
            raise ValueError("Conversation ID contains invalid characters")

        return conversation_id

    @staticmethod
    def validate_search_term(search_term: str) -> str:
        """Validate search term."""
        if not search_term:
            raise ValueError("Search term cannot be empty")

        if len(search_term) < 2:
            raise ValueError("Search term too short (minimum 2 characters)")

        if len(search_term) > 500:
            raise ValueError("Search term too long (maximum 500 characters)")

        return InputValidator.sanitize_text(search_term)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
) -> APIKey | None:
    """Dependency to get current authenticated user."""
    client_ip = security_manager.get_client_ip(request)

    # Check rate limiting first
    allowed, limit_info = security_manager.check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "retry_after": limit_info.get("retry_after", 3600)
            },
            headers={"Retry-After": str(limit_info.get("retry_after", 3600))}
        )

    # Check authentication
    if not credentials:
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return None
    else:
        # Bearer token could be JWT or API key
        token = credentials.credentials

        # Try JWT first
        auth_token = security_manager.validate_jwt_token(token)
        if auth_token:
            # Convert JWT to APIKey-like object for consistency
            return APIKey(
                key_id=auth_token.user_id,
                key_hash="jwt_token",
                name=f"JWT User {auth_token.user_id}",
                permissions=auth_token.permissions,
                created_at=auth_token.issued_at,
                last_used=datetime.utcnow(),
                is_active=True,
                usage_count=0
            )

        # Try as API key
        api_key = token

    if api_key:
        validated_key = security_manager.validate_api_key(api_key)
        if validated_key:
            return validated_key

    return None


async def require_permission(permission: str):
    """Dependency factory for permission checking."""
    async def check_permission(
        request: Request,
        current_user: APIKey | None = Depends(get_current_user)
    ):
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )

        if not security_manager.check_permission(current_user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission required: {permission}"
            )

        return current_user

    return check_permission


# Common permission dependencies
require_chat_read = require_permission("chat:read")
require_chat_write = require_permission("chat:write")
require_admin = require_permission("admin:all")
require_stats_read = require_permission("stats:read")
