import json
from enum import Enum
from functools import partial
from pickle import HIGHEST_PROTOCOL, dumps, loads
from typing import Any, Optional

try:
    from redis import Redis
except ImportError:
    Redis = None  # type: ignore

try:
    from aioredis import Redis as AioRedis
except ImportError:
    AioRedis = None  # pragma: no cover

try:
    from pymemcache.client.base import Client as Memcache
except ImportError:
    Memcache = None  # pragma: no cover

try:
    from aiomcache import Client as AioMemcache
except ImportError:
    AioMemcache = None  # pragma: no cover


from starlette_session.interfaces import ISessionBackend

_dumps = partial(dumps, protocol=HIGHEST_PROTOCOL)
_loads = partial(loads)


class MemcacheJSONSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value, 1
        return json.dumps(value), 2

    def deserialize(self, key, value, flags):
        if flags == 1:
            return value

        if flags == 2:
            return json.loads(value)

        raise Exception(f"Unknown flags for value: {flags}")


class BackendType(Enum):
    redis = "redis"
    aioRedis = "aioRedis"
    cookie = "cookie"
    memcache = "memcache"
    aioMemcache = "aioMemcache"


class RedisSessionBackend(ISessionBackend):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[dict]:
        value = self.redis.get(key)
        return _loads(value) if value else None

    async def set(
        self, key: str, value: dict, exp: Optional[int] = None
    ) -> Optional[str]:
        self.redis.set(key, _dumps(value), exp)
        return None

    async def delete(self, key: str) -> Any:
        return self.redis.delete(key)


class AioRedisSessionBackend(ISessionBackend):
    def __init__(self, redis: AioRedis):  # pragma: no cover
        self.redis = redis

    async def get(self, key: str) -> Optional[dict]:  # pragma: no cover
        value = await self.redis.get(key)
        return _loads(value) if value else None

    async def set(
        self, key: str, value: dict, exp: Optional[int] = None
    ) -> Optional[str]:  # pragma: no cover
        return await self.redis.set(key, _dumps(value), exp)

    async def delete(self, key: str) -> Any:  # pragma: no cover
        return await self.redis.delete(key)


class MemcacheSessionBackend(ISessionBackend):
    def __init__(self, memcache: Memcache):
        self.memcache = memcache
        self.memcache.serde = MemcacheJSONSerde()

    async def get(self, key: str) -> Optional[dict]:
        value = self.memcache.get(key)
        return value if value else None

    async def set(
        self, key: str, value: dict, exp: Optional[int] = None
    ) -> Optional[str]:
        return self.memcache.set(key, value, expire=exp)

    async def delete(self, key: str) -> Any:
        return self.memcache.delete(key)


class AioMemcacheSessionBackend(ISessionBackend):
    def __init__(self, memcache: AioMemcache):  # pragma: no cover
        self.memcache = memcache

    async def get(self, key: str) -> Optional[dict]:  # pragma: no cover
        value = await self.memcache.get(key.encode())
        return _loads(value) if value else None

    async def set(
        self, key: str, value: dict, exp: Optional[int] = None
    ) -> Optional[str]:  # pragma: no cover
        return await self.memcache.set(key.encode(), _dumps(value), exptime=exp)

    async def delete(self, key: str) -> Any:  # pragma: no cover
        return await self.memcache.delete(key.encode())
