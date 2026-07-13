import time
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class KeyManager:
    """Manages a pool of API keys with rotation and cooldown on rate limits."""

    def __init__(self, provider: str, keys: List[str], cooldown_seconds: float = 60.0) -> None:
        self.provider = provider
        self.keys = [k for k in keys if k.strip()]
        self.cooldown_seconds = cooldown_seconds
        # Map of key -> timestamp (seconds since epoch) when it is usable again
        self.cooldowns = {k: 0.0 for k in self.keys}
        self.current_index = 0

    def update_keys(self, keys: List[str]) -> None:
        """Update the active keys while maintaining the cooldown state of surviving keys."""
        cleaned_keys = [k for k in keys if k.strip()]
        new_cooldowns = {}
        for key in cleaned_keys:
            new_cooldowns[key] = self.cooldowns.get(key, 0.0)
        self.cooldowns = new_cooldowns
        self.keys = cleaned_keys
        self.current_index = 0

    def get_key(self) -> Optional[str]:
        """Retrieve the next key not on cooldown using round-robin.

        If all keys are on cooldown, returns the key that expires earliest.
        Returns None if there are no keys in the pool.
        """
        if not self.keys:
            return None

        now = time.time()
        num_keys = len(self.keys)
        # Scan keys starting from the current index
        for i in range(num_keys):
            idx = (self.current_index + i) % num_keys
            key = self.keys[idx]
            if self.cooldowns[key] <= now:
                self.current_index = (idx + 1) % num_keys
                return key

        # If all keys are on cooldown, pick the one with the earliest cooldown expiry
        earliest_key = min(self.keys, key=lambda k: self.cooldowns[k])
        logger.warning(
            "All %s API keys are on cooldown. Selecting key with earliest expiry.",
            self.provider
        )
        return earliest_key

    def report_rate_limit(self, key: str, custom_cooldown: float | None = None) -> None:
        """Place a key on cooldown for the configured duration."""
        if key not in self.cooldowns:
            return
        duration = custom_cooldown if custom_cooldown is not None else self.cooldown_seconds
        self.cooldowns[key] = time.time() + duration
        logger.warning(
            "API key for %s (%s...) hit rate limit. Cool down for %ds.",
            self.provider,
            key[:10],
            duration
        )
