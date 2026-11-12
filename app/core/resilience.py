import logging
import time
from typing import Callable, Any, Type

logger = logging.getLogger("BUTL-R.Resilience")


def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Any:
    """Execute a function with exponential backoff on transient failures."""
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except exceptions as err:
            last_exception = err
            if attempt == max_retries:
                logger.error(
                    f"Action failed after {max_retries} attempts: {err}"
                )
                raise
            logger.warning(
                f"Attempt {attempt}/{max_retries} failed ({err}). Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)
            delay *= backoff_factor

    if last_exception:
        raise last_exception


class FallbackHandler:
    """Provides safe, graceful degradation replies when models or external services fail."""

    SERVICE_UNAVAILABLE = (
        "I am currently having trouble connecting to my local AI engine. "
        "Please check that Ollama is running in the background."
    )

    TIMEOUT_MESSAGE = (
        "My local AI model took longer than expected to respond. "
        "Try switching to Fast Mode ('fast') for faster CPU performance."
    )

    GENERIC_ERROR = (
        "I encountered an unexpected issue while processing your request. "
        "Your conversation history and saved memories remain safe."
    )

    @classmethod
    def get_fallback(cls, exception: Exception) -> str:
        if isinstance(exception, (ConnectionError, ConnectionRefusedError)):
            return cls.SERVICE_UNAVAILABLE
        if isinstance(exception, TimeoutError):
            return cls.TIMEOUT_MESSAGE
        return cls.GENERIC_ERROR
