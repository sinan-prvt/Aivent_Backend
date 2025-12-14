from django.core.cache import cache
import os
import logging


logger = logging.getLogger(__name__)


FAILED_KEY_PREFIX = "captcha_failed_count:"
BLOCK_KEY_PREFIX = "captcha_blocked:"
FAILED_ATTEMPTS = int(os.environ.get("CAPTCHA_FAILED_ATTEMPTS", 3))
BLOCK_SECONDS = int(os.environ.get("CAPTCHA_BLOCK_SECONDS", 900))


def _failed_key(key): return f"{FAILED_KEY_PREFIX}{key}"
def _blocked_key(key): return f"{BLOCK_KEY_PREFIX}{key}"

def increment_failed_attempts(key: str) -> int:
    k = _failed_key(key)
    current = cache.get(k) or 0
    current += 1
    cache.set(k, current, BLOCK_SECONDS)
    if current >= FAILED_ATTEMPTS:
        cache.set(_blocked_key(key), True, BLOCK_SECONDS)
    return current

def requires_captcha(key: str) -> bool:
    return bool(cache.get(_blocked_key(key)))

def reset_failed_attempts(key: str):
    cache.delete(_failed_key(key))
    cache.delete(_blocked_key(key))


