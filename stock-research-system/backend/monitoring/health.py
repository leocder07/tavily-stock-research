"""Health check module for Stock Research System"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import os

logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health checking for all system components"""

    def __init__(
        self,
        mongodb_uri: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None
    ):
        """Initialize health checker

        Args:
            mongodb_uri: MongoDB connection URI
            redis_host: Redis host
            redis_port: Redis port
        """
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI')
        self.redis_host = redis_host or os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = redis_port or int(os.getenv('REDIS_PORT', 6379))
        self.start_time = datetime.utcnow()

    async def check_mongodb(self) -> Dict[str, Any]:
        """Check MongoDB connectivity and performance

        Returns:
            Health status dictionary
        """
        try:
            start_time = time.time()
            client = AsyncIOMotorClient(self.mongodb_uri)

            # Ping database
            await client.admin.command('ping')

            # Get database stats
            db = client.get_database()
            stats = await db.command('dbstats')

            latency = (time.time() - start_time) * 1000  # Convert to ms

            return {
                'status': 'healthy',
                'latency_ms': round(latency, 2),
                'collections': stats.get('collections', 0),
                'data_size': stats.get('dataSize', 0),
                'indexes': stats.get('indexes', 0)
            }
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance

        Returns:
            Health status dictionary
        """
        try:
            start_time = time.time()
            r = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=2
            )

            # Ping Redis
            r.ping()

            # Get info
            info = r.info()

            latency = (time.time() - start_time) * 1000

            return {
                'status': 'healthy',
                'latency_ms': round(latency, 2),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'uptime_days': info.get('uptime_in_days', 0)
            }
        except redis.ConnectionError:
            return {
                'status': 'unavailable',
                'message': 'Redis not configured or not running'
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def check_tavily_api(self) -> Dict[str, Any]:
        """Check Tavily API connectivity

        Returns:
            Health status dictionary
        """
        try:
            tavily_api_key = os.getenv('TAVILY_API_KEY')
            if not tavily_api_key:
                return {
                    'status': 'unconfigured',
                    'message': 'Tavily API key not configured'
                }

            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.tavily.com/search',
                    json={
                        'api_key': tavily_api_key,
                        'query': 'test',
                        'max_results': 1
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    latency = (time.time() - start_time) * 1000

                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'latency_ms': round(latency, 2)
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'status_code': response.status,
                            'latency_ms': round(latency, 2)
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': 'Request timeout'
            }
        except Exception as e:
            logger.error(f"Tavily API health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def check_openai_api(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity

        Returns:
            Health status dictionary
        """
        try:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                return {
                    'status': 'unconfigured',
                    'message': 'OpenAI API key not configured'
                }

            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {openai_api_key}'},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    latency = (time.time() - start_time) * 1000

                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'latency_ms': round(latency, 2)
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'status_code': response.status,
                            'latency_ms': round(latency, 2)
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': 'Request timeout'
            }
        except Exception as e:
            logger.error(f"OpenAI API health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status

        Returns:
            Complete health status
        """
        # Run all health checks concurrently
        results = await asyncio.gather(
            self.check_mongodb(),
            self.check_redis(),
            self.check_tavily_api(),
            self.check_openai_api(),
            return_exceptions=True
        )

        # Process results
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
            'components': {
                'mongodb': results[0] if not isinstance(results[0], Exception) else {'status': 'error', 'error': str(results[0])},
                'redis': results[1] if not isinstance(results[1], Exception) else {'status': 'error', 'error': str(results[1])},
                'tavily_api': results[2] if not isinstance(results[2], Exception) else {'status': 'error', 'error': str(results[2])},
                'openai_api': results[3] if not isinstance(results[3], Exception) else {'status': 'error', 'error': str(results[3])}
            }
        }

        # Determine overall status
        critical_components = ['mongodb', 'tavily_api', 'openai_api']
        for component in critical_components:
            if health_status['components'][component].get('status') not in ['healthy', 'unavailable']:
                health_status['status'] = 'degraded'
                break

        # Check if any critical component is unhealthy
        if health_status['components']['mongodb'].get('status') == 'unhealthy':
            health_status['status'] = 'unhealthy'

        return health_status

    async def get_readiness(self) -> Dict[str, Any]:
        """Check if system is ready to serve requests

        Returns:
            Readiness status
        """
        health = await self.get_system_health()

        ready = True
        reasons = []

        # Check critical components
        if health['components']['mongodb'].get('status') != 'healthy':
            ready = False
            reasons.append('MongoDB not healthy')

        if health['components']['tavily_api'].get('status') == 'unhealthy':
            ready = False
            reasons.append('Tavily API not healthy')

        if health['components']['openai_api'].get('status') == 'unhealthy':
            ready = False
            reasons.append('OpenAI API not healthy')

        return {
            'ready': ready,
            'timestamp': datetime.utcnow().isoformat(),
            'reasons': reasons if not ready else []
        }

    async def get_liveness(self) -> Dict[str, Any]:
        """Simple liveness check

        Returns:
            Liveness status
        """
        return {
            'alive': True,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds()
        }


# Singleton instance
_health_checker = None

def get_health_checker() -> HealthChecker:
    """Get or create health checker instance

    Returns:
        HealthChecker instance
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


async def get_health_status() -> Dict[str, Any]:
    """Get current health status

    Returns:
        Health status dictionary
    """
    checker = get_health_checker()
    return await checker.get_system_health()