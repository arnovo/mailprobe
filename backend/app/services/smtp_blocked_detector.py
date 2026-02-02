"""SMTP outbound blocked detector using Redis.

Detects when SMTP port 25 is blocked at the infrastructure level
by tracking timeout errors across multiple distinct MX hosts.
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import redis

from app.core.config import settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Redis keys
REDIS_KEY_BLOCKED = "smtp:outbound_blocked"
REDIS_KEY_TIMEOUT_HOSTS = "smtp:timeout_hosts"

# Detection thresholds
THRESHOLD_HOSTS = 3  # Distinct hosts with timeout to trigger blocked flag
WINDOW_SECONDS = 300  # 5 min window for tracking timeouts
TTL_BLOCKED_SECONDS = 900  # 15 min TTL for blocked flag

# Lazy Redis connection
_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    """Get or create Redis connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


def record_smtp_timeout(host: str) -> None:
    """
    Record an SMTP timeout for a host.
    
    If enough distinct hosts have timed out within the window,
    sets the global smtp_blocked flag.
    """
    try:
        r = _get_redis()
        
        # Add host to sorted set with current timestamp as score
        now = time.time()
        r.zadd(REDIS_KEY_TIMEOUT_HOSTS, {host: now})
        
        # Remove old entries outside the window
        cutoff = now - WINDOW_SECONDS
        r.zremrangebyscore(REDIS_KEY_TIMEOUT_HOSTS, "-inf", cutoff)
        
        # Set TTL on the set so it auto-expires if no new timeouts
        r.expire(REDIS_KEY_TIMEOUT_HOSTS, WINDOW_SECONDS + 60)
        
        # Check if threshold reached
        distinct_hosts = r.zcard(REDIS_KEY_TIMEOUT_HOSTS)
        
        if distinct_hosts >= THRESHOLD_HOSTS:
            # Set blocked flag with TTL
            r.setex(REDIS_KEY_BLOCKED, TTL_BLOCKED_SECONDS, "1")
            logger.warning(
                f"SMTP outbound blocked detected: {distinct_hosts} distinct hosts "
                f"with timeouts in last {WINDOW_SECONDS}s. Flag set for {TTL_BLOCKED_SECONDS}s."
            )
    except redis.RedisError as e:
        # Don't fail verification if Redis is down
        logger.error(f"Redis error recording SMTP timeout: {e}")


def is_smtp_blocked() -> bool:
    """
    Check if SMTP outbound is currently detected as blocked.
    
    Returns:
        True if SMTP port 25 appears blocked at infrastructure level.
    """
    try:
        r = _get_redis()
        return r.exists(REDIS_KEY_BLOCKED) == 1
    except redis.RedisError as e:
        # If Redis is down, assume SMTP is not blocked
        logger.error(f"Redis error checking SMTP blocked status: {e}")
        return False


def clear_smtp_blocked() -> None:
    """
    Clear the SMTP blocked flag (for testing/admin use).
    """
    try:
        r = _get_redis()
        r.delete(REDIS_KEY_BLOCKED)
        r.delete(REDIS_KEY_TIMEOUT_HOSTS)
        logger.info("SMTP blocked flag and timeout hosts cleared.")
    except redis.RedisError as e:
        logger.error(f"Redis error clearing SMTP blocked status: {e}")


def get_smtp_blocked_info() -> dict:
    """
    Get detailed info about SMTP blocked status (for debugging/admin).
    
    Returns:
        Dict with blocked status, timeout hosts, and timing info.
    """
    try:
        r = _get_redis()
        blocked = r.exists(REDIS_KEY_BLOCKED) == 1
        blocked_ttl = r.ttl(REDIS_KEY_BLOCKED) if blocked else 0
        
        # Get hosts with timestamps
        hosts_with_scores = r.zrange(REDIS_KEY_TIMEOUT_HOSTS, 0, -1, withscores=True)
        hosts = [
            {"host": host, "timestamp": score}
            for host, score in hosts_with_scores
        ]
        
        return {
            "smtp_blocked": blocked,
            "blocked_ttl_seconds": blocked_ttl if blocked_ttl > 0 else 0,
            "timeout_hosts_count": len(hosts),
            "timeout_hosts": hosts,
            "threshold": THRESHOLD_HOSTS,
            "window_seconds": WINDOW_SECONDS,
        }
    except redis.RedisError as e:
        logger.error(f"Redis error getting SMTP blocked info: {e}")
        return {
            "smtp_blocked": False,
            "error": str(e),
        }
