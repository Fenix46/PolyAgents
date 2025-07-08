"""Advanced health check system for monitoring all components."""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import aiohttp
from sqlalchemy import text
import redis.asyncio as redis

from .config import settings

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health information for a component."""
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    last_check: Optional[datetime] = None


class HealthChecker:
    """Advanced health checker for all system components."""
    
    def __init__(self):
        self.timeout = settings.health_check_timeout
        self.check_external = settings.health_check_external_services
        self._last_full_check: Optional[datetime] = None
        self._cached_results: Dict[str, ComponentHealth] = {}
        self._cache_duration = timedelta(seconds=30)  # Cache results for 30 seconds
    
    async def check_all_components(self, use_cache: bool = True) -> Dict[str, ComponentHealth]:
        """Check health of all system components."""
        current_time = datetime.utcnow()
        
        # Use cached results if recent enough
        if (use_cache and self._last_full_check and 
            current_time - self._last_full_check < self._cache_duration):
            return self._cached_results.copy()
        
        logger.info("Running comprehensive health check")
        start_time = time.time()
        
        # Define all health checks
        checks = [
            ("redis", self._check_redis),
            ("postgresql", self._check_postgresql),
            ("qdrant", self._check_qdrant),
            ("disk_space", self._check_disk_space),
            ("memory", self._check_memory),
        ]
        
        # Add external service checks if enabled
        if self.check_external:
            checks.extend([
                ("gemini_api", self._check_gemini_api),
                ("internet_connectivity", self._check_internet_connectivity),
            ])
        
        # Run all checks concurrently
        results = {}
        check_tasks = []
        
        for component_name, check_func in checks:
            task = asyncio.create_task(self._run_check_with_timeout(component_name, check_func))
            check_tasks.append((component_name, task))
        
        # Wait for all checks to complete
        for component_name, task in check_tasks:
            try:
                results[component_name] = await task
            except Exception as e:
                logger.error(f"Health check failed for {component_name}: {e}")
                results[component_name] = ComponentHealth(
                    name=component_name,
                    status=HealthStatus.UNHEALTHY,
                    error=str(e),
                    last_check=current_time
                )
        
        # Cache the results
        self._cached_results = results
        self._last_full_check = current_time
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Health check completed in {total_time:.2f}ms")
        
        return results
    
    async def _run_check_with_timeout(self, component_name: str, check_func) -> ComponentHealth:
        """Run a health check with timeout."""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(check_func(), timeout=self.timeout)
            result.response_time_ms = (time.time() - start_time) * 1000
            result.last_check = datetime.utcnow()
            return result
            
        except asyncio.TimeoutError:
            return ComponentHealth(
                name=component_name,
                status=HealthStatus.UNHEALTHY,
                error=f"Health check timeout after {self.timeout}s",
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow()
            )
        except Exception as e:
            return ComponentHealth(
                name=component_name,
                status=HealthStatus.UNHEALTHY,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow()
            )
    
    async def _check_redis(self) -> ComponentHealth:
        """Check Redis connectivity and performance."""
        try:
            client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=self.timeout
            )
            
            # Test basic connectivity
            ping_result = await client.ping()
            if not ping_result:
                raise Exception("Redis ping failed")
            
            # Test write/read operation
            test_key = "health_check_test"
            test_value = str(time.time())
            
            await client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            stored_value = await client.get(test_key)
            
            if stored_value != test_value:
                raise Exception("Redis write/read test failed")
            
            # Get Redis info
            info = await client.info()
            memory_usage = info.get('used_memory', 0)
            connected_clients = info.get('connected_clients', 0)
            
            await client.close()
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                details={
                    "memory_usage_bytes": memory_usage,
                    "connected_clients": connected_clients,
                    "redis_version": info.get('redis_version', 'unknown')
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
    
    async def _check_postgresql(self) -> ComponentHealth:
        """Check PostgreSQL connectivity and performance."""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            
            database_url = (
                f"postgresql+asyncpg://{settings.postgres_user}:"
                f"{settings.postgres_password}@{settings.postgres_host}:"
                f"{settings.postgres_port}/{settings.postgres_db}"
            )
            
            engine = create_async_engine(
                database_url,
                pool_timeout=self.timeout,
                pool_size=1,
                max_overflow=0
            )
            
            async with engine.begin() as conn:
                # Test basic connectivity
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() != 1:
                    raise Exception("PostgreSQL basic query failed")
                
                # Get database stats
                stats_query = text("""
                    SELECT 
                        current_database() as database_name,
                        pg_database_size(current_database()) as database_size,
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections
                """)
                
                stats_result = await conn.execute(stats_query)
                stats = stats_result.fetchone()
                
                # Check table existence
                table_check = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'conversations'
                    )
                """)
                
                tables_exist = await conn.execute(table_check)
                
            await engine.dispose()
            
            return ComponentHealth(
                name="postgresql",
                status=HealthStatus.HEALTHY,
                details={
                    "database_name": stats[0],
                    "database_size_bytes": stats[1],
                    "active_connections": stats[2],
                    "tables_exist": tables_exist.scalar()
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="postgresql",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
    
    async def _check_qdrant(self) -> ComponentHealth:
        """Check Qdrant connectivity."""
        try:
            url = f"http://{settings.qdrant_host}:{settings.qdrant_port}/collections"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Qdrant returned status {response.status}")
                    
                    data = await response.json()
                    collections = data.get('result', {}).get('collections', [])
                    
                    return ComponentHealth(
                        name="qdrant",
                        status=HealthStatus.HEALTHY,
                        details={
                            "collections_count": len(collections),
                            "collections": [col.get('name') for col in collections]
                        }
                    )
                    
        except Exception as e:
            return ComponentHealth(
                name="qdrant",
                status=HealthStatus.DEGRADED,  # Qdrant is optional
                error=str(e)
            )
    
    async def _check_gemini_api(self) -> ComponentHealth:
        """Check Google Gemini API connectivity."""
        try:
            if not settings.gemini_api_key:
                return ComponentHealth(
                    name="gemini_api",
                    status=HealthStatus.DEGRADED,
                    error="No Gemini API key configured"
                )
            
            # Import here to avoid dependency issues if not available
            from google import genai
            
            client = genai.Client(api_key=settings.gemini_api_key)
            
            # Try to list models (lightweight operation)
            models = client.models.list()
            model_count = len(list(models))
            
            return ComponentHealth(
                name="gemini_api",
                status=HealthStatus.HEALTHY,
                details={
                    "available_models": model_count,
                    "api_key_configured": True
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="gemini_api",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
    
    async def _check_internet_connectivity(self) -> ComponentHealth:
        """Check internet connectivity."""
        try:
            test_urls = [
                "https://www.google.com",
                "https://1.1.1.1",  # Cloudflare DNS
            ]
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                for url in test_urls:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                return ComponentHealth(
                                    name="internet_connectivity",
                                    status=HealthStatus.HEALTHY,
                                    details={"test_url": url}
                                )
                    except:
                        continue
                
                raise Exception("All connectivity tests failed")
                
        except Exception as e:
            return ComponentHealth(
                name="internet_connectivity",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
    
    async def _check_disk_space(self) -> ComponentHealth:
        """Check disk space availability."""
        try:
            import shutil
            
            # Check current directory disk space
            total, used, free = shutil.disk_usage(".")
            
            free_percentage = (free / total) * 100
            
            # Determine status based on free space
            if free_percentage < 5:
                status = HealthStatus.UNHEALTHY
            elif free_percentage < 15:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return ComponentHealth(
                name="disk_space",
                status=status,
                details={
                    "total_bytes": total,
                    "used_bytes": used,
                    "free_bytes": free,
                    "free_percentage": round(free_percentage, 2)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                error=str(e)
            )
    
    async def _check_memory(self) -> ComponentHealth:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            # Determine status based on memory usage
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return ComponentHealth(
                name="memory",
                status=status,
                details={
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_percentage": memory.percent,
                    "swap_total": psutil.swap_memory().total,
                    "swap_used": psutil.swap_memory().used
                }
            )
            
        except ImportError:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                error="psutil not available"
            )
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                error=str(e)
            )
    
    def get_overall_status(self, component_healths: Dict[str, ComponentHealth]) -> HealthStatus:
        """Determine overall system health status."""
        if not component_healths:
            return HealthStatus.UNKNOWN
        
        # Critical components that affect overall health
        critical_components = {"redis", "postgresql"}
        
        unhealthy_critical = any(
            health.status == HealthStatus.UNHEALTHY 
            for name, health in component_healths.items()
            if name in critical_components
        )
        
        if unhealthy_critical:
            return HealthStatus.UNHEALTHY
        
        # Check for any unhealthy components
        any_unhealthy = any(
            health.status == HealthStatus.UNHEALTHY
            for health in component_healths.values()
        )
        
        if any_unhealthy:
            return HealthStatus.DEGRADED
        
        # Check for degraded components
        any_degraded = any(
            health.status == HealthStatus.DEGRADED
            for health in component_healths.values()
        )
        
        if any_degraded:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def format_health_response(self, component_healths: Dict[str, ComponentHealth]) -> Dict[str, Any]:
        """Format health check results for API response."""
        overall_status = self.get_overall_status(component_healths)
        
        components = {}
        for name, health in component_healths.items():
            components[name] = {
                "status": health.status.value,
                "response_time_ms": health.response_time_ms,
                "last_check": health.last_check.isoformat() if health.last_check else None,
                "error": health.error,
                "details": health.details
            }
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "components": components,
            "summary": {
                "total_components": len(component_healths),
                "healthy": sum(1 for h in component_healths.values() if h.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for h in component_healths.values() if h.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for h in component_healths.values() if h.status == HealthStatus.UNHEALTHY),
                "unknown": sum(1 for h in component_healths.values() if h.status == HealthStatus.UNKNOWN)
            }
        }


# Global health checker instance
health_checker = HealthChecker() 