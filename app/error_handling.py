"""Advanced error handling with retry logic, circuit breakers, and graceful degradation."""

import asyncio
import logging
import time
import random
from typing import Any, Callable, Dict, Optional, List, Type, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import traceback

from .config import settings

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker state enumeration."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    timeout_seconds: float = 60.0
    success_threshold: int = 3  # For half-open state


class RetryableError(Exception):
    """Exception that indicates an operation should be retried."""
    pass


class NonRetryableError(Exception):
    """Exception that indicates an operation should not be retried."""
    pass


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class ErrorHandler:
    """Centralized error handling with retry and circuit breaker functionality."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, 'CircuitBreaker'] = {}
        self.error_stats: Dict[str, List[datetime]] = {}
        self.default_retry_config = RetryConfig(
            max_attempts=settings.retry_max_attempts,
            base_delay=settings.retry_base_delay,
            max_delay=settings.retry_max_delay
        )
        self.default_circuit_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            timeout_seconds=settings.circuit_breaker_timeout
        )
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> 'CircuitBreaker':
        """Get or create a circuit breaker for a service."""
        if name not in self.circuit_breakers:
            circuit_config = config or self.default_circuit_config
            self.circuit_breakers[name] = CircuitBreaker(name, circuit_config)
        return self.circuit_breakers[name]
    
    def log_error(self, operation: str, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with context information."""
        error_info = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if context:
            error_info.update(context)
        
        # Track error statistics
        if operation not in self.error_stats:
            self.error_stats[operation] = []
        
        self.error_stats[operation].append(datetime.utcnow())
        
        # Clean old error records (keep last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.error_stats[operation] = [
            timestamp for timestamp in self.error_stats[operation]
            if timestamp > cutoff
        ]
        
        logger.error(f"Operation failed: {operation}", extra=error_info, exc_info=error)
    
    def get_error_rate(self, operation: str, window_hours: int = 1) -> float:
        """Get error rate for an operation within a time window."""
        if operation not in self.error_stats:
            return 0.0
        
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent_errors = [
            timestamp for timestamp in self.error_stats[operation]
            if timestamp > cutoff
        ]
        
        return len(recent_errors) / max(window_hours, 1)  # errors per hour
    
    async def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with retry logic and optional circuit breaker."""
        config = retry_config or self.default_retry_config
        circuit_breaker = None
        
        if circuit_breaker_name:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)
        
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                # Check circuit breaker before attempting
                if circuit_breaker:
                    circuit_breaker.check_state()
                
                # Execute operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # Record success in circuit breaker
                if circuit_breaker:
                    circuit_breaker.record_success()
                
                # Log successful retry if not first attempt
                if attempt > 0:
                    logger.info(f"Operation {operation_name} succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Record failure in circuit breaker
                if circuit_breaker:
                    circuit_breaker.record_failure()
                
                # Check if this is the last attempt
                if attempt == config.max_attempts - 1:
                    self.log_error(operation_name, e, {
                        "attempt": attempt + 1,
                        "max_attempts": config.max_attempts,
                        "final_attempt": True
                    })
                    break
                
                # Check if error is retryable
                if isinstance(e, NonRetryableError):
                    self.log_error(operation_name, e, {
                        "attempt": attempt + 1,
                        "reason": "non_retryable_error"
                    })
                    break
                
                if not isinstance(e, config.retryable_exceptions):
                    self.log_error(operation_name, e, {
                        "attempt": attempt + 1,
                        "reason": "non_retryable_exception_type"
                    })
                    break
                
                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt, config)
                
                self.log_error(operation_name, e, {
                    "attempt": attempt + 1,
                    "max_attempts": config.max_attempts,
                    "retry_delay": delay,
                    "retrying": True
                })
                
                # Wait before retrying
                await asyncio.sleep(delay)
        
        # All retries exhausted, raise the last exception
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Operation {operation_name} failed with no exception captured")
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for exponential backoff with jitter."""
        # Exponential backoff
        delay = config.base_delay * (config.exponential_base ** attempt)
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(delay, 0)  # Ensure non-negative delay


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state_change_time = datetime.utcnow()
    
    def check_state(self):
        """Check circuit breaker state and throw exception if open."""
        current_time = datetime.utcnow()
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has elapsed
            if (current_time - self.state_change_time).total_seconds() >= self.config.timeout_seconds:
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Timeout in {self.config.timeout_seconds - (current_time - self.state_change_time).total_seconds():.1f}s"
                )
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # In half-open state, allow limited requests to test service
            pass
    
    def record_success(self):
        """Record a successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed operation."""
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self._transition_to_open()
        
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to open state."""
        self.state = CircuitBreakerState.OPEN
        self.state_change_time = datetime.utcnow()
        self.success_count = 0
        
        logger.warning(
            f"Circuit breaker '{self.name}' opened after {self.failure_count} failures. "
            f"Will retry in {self.config.timeout_seconds}s"
        )
    
    def _transition_to_half_open(self):
        """Transition to half-open state."""
        self.state = CircuitBreakerState.HALF_OPEN
        self.state_change_time = datetime.utcnow()
        self.success_count = 0
        
        logger.info(f"Circuit breaker '{self.name}' entering half-open state for testing")
    
    def _transition_to_closed(self):
        """Transition to closed state."""
        self.state = CircuitBreakerState.CLOSED
        self.state_change_time = datetime.utcnow()
        self.failure_count = 0
        self.success_count = 0
        
        logger.info(f"Circuit breaker '{self.name}' closed - service recovered")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "state_change_time": self.state_change_time.isoformat(),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "success_threshold": self.config.success_threshold
            }
        }


# Decorator for automatic retry
def with_retry(
    operation_name: str,
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker_name: Optional[str] = None
):
    """Decorator to add retry logic to functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await error_handler.execute_with_retry(
                func,
                operation_name,
                retry_config,
                circuit_breaker_name,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


# Decorator for circuit breaker
def with_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to add circuit breaker to functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            circuit_breaker = error_handler.get_circuit_breaker(name, config)
            circuit_breaker.check_state()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                circuit_breaker.record_success()
                return result
                
            except Exception as e:
                circuit_breaker.record_failure()
                raise
        
        return wrapper
    return decorator


class GracefulDegradation:
    """Utilities for graceful degradation when services are unavailable."""
    
    @staticmethod
    def fallback_response(operation: str, fallback_data: Any = None) -> Dict[str, Any]:
        """Generate a fallback response when primary operation fails."""
        return {
            "status": "degraded",
            "message": f"Primary {operation} service unavailable, using fallback",
            "data": fallback_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def cached_response(operation: str, cached_data: Any, cache_age: timedelta) -> Dict[str, Any]:
        """Generate a response using cached data when fresh data is unavailable."""
        return {
            "status": "cached",
            "message": f"Using cached {operation} data due to service unavailability",
            "data": cached_data,
            "cache_age_seconds": cache_age.total_seconds(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def minimal_response(operation: str, essential_data: Any = None) -> Dict[str, Any]:
        """Generate a minimal response with only essential data."""
        return {
            "status": "minimal",
            "message": f"Providing minimal {operation} response due to service degradation",
            "data": essential_data,
            "timestamp": datetime.utcnow().isoformat()
        }


# Exception hierarchy for different error types
class PolyAgentsError(Exception):
    """Base exception for PolyAgents application."""
    pass


class ConfigurationError(PolyAgentsError):
    """Configuration-related errors."""
    pass


class DatabaseError(PolyAgentsError, RetryableError):
    """Database operation errors."""
    pass


class ExternalServiceError(PolyAgentsError, RetryableError):
    """External service errors (Gemini API, etc.)."""
    pass


class AuthenticationError(PolyAgentsError, NonRetryableError):
    """Authentication and authorization errors."""
    pass


class ValidationError(PolyAgentsError, NonRetryableError):
    """Input validation errors."""
    pass


class RateLimitError(PolyAgentsError, RetryableError):
    """Rate limiting errors."""
    pass


# Global error handler instance
error_handler = ErrorHandler()


def handle_known_exceptions(operation: str):
    """Decorator to convert known exceptions to PolyAgents exceptions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                # Convert known exceptions to PolyAgents exceptions
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    raise ExternalServiceError(f"{operation} connection error: {e}") from e
                elif "permission" in str(e).lower() or "unauthorized" in str(e).lower():
                    raise AuthenticationError(f"{operation} authentication error: {e}") from e
                elif "invalid" in str(e).lower() or "validation" in str(e).lower():
                    raise ValidationError(f"{operation} validation error: {e}") from e
                else:
                    # Re-raise as-is for unknown errors
                    raise
        
        return wrapper
    return decorator 