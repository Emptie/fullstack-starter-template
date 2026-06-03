"""Async Redis-backed token store for refresh tokens and password reset tokens.

Replaces the PostgreSQL refresh_tokens and password_reset_tokens tables.
Redis automatically evicts expired tokens via TTL — no cleanup needed.

Usage in FastAPI routes::

    from starter_shared.token_store import get_token_store, TokenStore

    token_store: TokenStore = Depends(get_token_store)

Usage in app lifespan::

    from starter_shared.token_store import init_redis, close_redis

    async def lifespan(app):
        await init_redis()
        yield
        await close_redis()
"""

from __future__ import annotations

from redis.asyncio import Redis

from starter_shared.config import settings

# Redis key patterns
_RT_KEY = "rt:{hash}"  # refresh token → user_id
_USER_RT_KEY = "user_rt:{uid}"  # SET of token hashes for a user
_PRT_KEY = "prt:{hash}"  # password reset token → user_id


class TokenStore:
    """Async Redis-backed store for short-lived tokens.

    All methods are async and require a connected Redis instance.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    # ── Refresh tokens ─────────────────────────────────────

    async def store_refresh_token(
        self, token_hash: str, user_id: int, ttl_seconds: int
    ) -> None:
        """Store a refresh token hash mapped to user_id, with TTL."""
        rt_key = _RT_KEY.format(hash=token_hash)
        user_key = _USER_RT_KEY.format(uid=user_id)
        pipe = self._redis.pipeline()
        pipe.set(rt_key, str(user_id), ex=ttl_seconds)
        pipe.sadd(user_key, token_hash)
        pipe.expire(user_key, ttl_seconds + 60)
        await pipe.execute()

    async def get_refresh_token(self, token_hash: str) -> int | None:
        """Get user_id for a refresh token hash. Returns None if revoked/expired."""
        val = await self._redis.get(_RT_KEY.format(hash=token_hash))
        return int(val) if val is not None else None

    async def revoke_refresh_token(self, token_hash: str, user_id: int) -> None:
        """Revoke a single refresh token (used during rotation)."""
        pipe = self._redis.pipeline()
        pipe.delete(_RT_KEY.format(hash=token_hash))
        pipe.srem(_USER_RT_KEY.format(uid=user_id), token_hash)
        await pipe.execute()

    async def revoke_all_user_refresh_tokens(self, user_id: int) -> None:
        """Revoke ALL refresh tokens for a user (theft detection / password change)."""
        user_key = _USER_RT_KEY.format(uid=user_id)
        hashes = await self._redis.smembers(user_key)
        if hashes:
            pipe = self._redis.pipeline()
            for h in hashes:
                if isinstance(h, bytes):
                    h = h.decode()
                pipe.delete(_RT_KEY.format(hash=h))
            pipe.delete(user_key)
            await pipe.execute()
        else:
            await self._redis.delete(user_key)

    # ── Password reset tokens ──────────────────────────────

    async def store_password_reset_token(
        self, token_hash: str, user_id: int, ttl_seconds: int
    ) -> None:
        """Store a password reset token hash mapped to user_id, with TTL."""
        await self._redis.set(
            _PRT_KEY.format(hash=token_hash), str(user_id), ex=ttl_seconds
        )

    async def consume_password_reset_token(self, token_hash: str) -> int | None:
        """Consume a password reset token (atomic GETDEL). Returns user_id or None."""
        val = await self._redis.getdel(_PRT_KEY.format(hash=token_hash))
        if val is None:
            return None
        return int(val) if isinstance(val, str) else int(val.decode())


# ── Module-level Redis client and FastAPI dependency ───────────

_redis: Redis | None = None


def get_redis() -> Redis:
    """Get the shared Redis client instance."""
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis


async def init_redis(url: str | None = None) -> None:
    """Initialize the Redis connection pool. Call in app lifespan startup."""
    global _redis
    _redis = Redis.from_url(
        url or settings.redis.redis_url, decode_responses=True
    )


async def close_redis() -> None:
    """Close the Redis connection pool. Call in app lifespan shutdown."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_token_store() -> TokenStore:
    """FastAPI dependency that provides a TokenStore instance."""
    return TokenStore(get_redis())
