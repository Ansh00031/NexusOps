import time
import logging
from typing import Callable, Any, Dict, Optional, Tuple

logger = logging.getLogger("nexusops.resilience")

class MicroserviceTransientError(Exception):
    """Simulated transient 503 / network timeout error."""
    pass

class ResilienceManager:
    """
    Handles exponential backoff retries, caching, and chaos mode injection.
    """

    def __init__(self, chaos_mode: bool = False):
        self.chaos_mode = chaos_mode
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.default_ttl_seconds = 300.0  # 5 minutes TTL

    def get_from_cache(self, key: str) -> Optional[Any]:
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self.default_ttl_seconds:
                return val
            else:
                del self._cache[key]
        return None

    def set_in_cache(self, key: str, value: Any):
        self._cache[key] = (time.time(), value)

    def execute_with_retry(
        self,
        operation_name: str,
        func: Callable[[], Any],
        max_retries: int = 3,
        base_delay: float = 0.05,
        backoff_factor: float = 2.0
    ) -> Tuple[Any, int, bool]:
        """
        Executes func with exponential backoff retries.
        Returns (result, retries_attempted, was_degraded).
        """
        attempts = 0
        current_delay = base_delay

        while attempts < max_retries:
            attempts += 1
            try:
                # If Chaos Mode is on and operation is CRM, simulate 503 failure
                if self.chaos_mode and "crm" in operation_name.lower():
                    # Fail first 2 attempts, succeed on 3rd if max_retries >= 3, or simulate persistent outage
                    if attempts < 3:
                        logger.warning(f"[ChaosMode] Injecting simulated 503 HTTP Timeout on {operation_name} (attempt {attempts}/{max_retries})")
                        raise MicroserviceTransientError(f"503 Service Unavailable: Simulated transient failure on {operation_name}")

                result = func()
                return result, attempts - 1, False

            except MicroserviceTransientError as e:
                logger.warning(f"Transient error in {operation_name} on attempt {attempts}: {e}")
                if attempts < max_retries:
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    logger.error(f"Exhausted retries ({max_retries}) for {operation_name}. Triggering graceful degradation.")
                    return None, attempts, True
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}")
                return None, attempts, True

        return None, attempts, True
