# Error Recovery Templates

## Exception Handling Patterns

### Basic Try-Except with Logging

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Handle or re-raise
    raise
```

### Multiple Exception Types

```python
try:
    result = operation()
except (ValueError, TypeError) as e:
    logger.warning(f"Input validation failed: {e}")
    return default_value
except ConnectionError as e:
    logger.error(f"Network error: {e}")
    return None
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    raise
```

## Retry Strategies

### Exponential Backoff

```python
import time
from typing import Callable, Any

def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Any:
    """Retry function with exponential backoff"""

    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s")
            time.sleep(delay)
```

### Retry with Custom Logic

```python
def retry_on_condition(
    func: Callable,
    should_retry: Callable[[Exception], bool],
    max_attempts: int = 3
) -> Any:
    """Retry only on specific conditions"""

    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if not should_retry(e) or attempt == max_attempts - 1:
                raise
            logger.info(f"Retrying after: {e}")

    raise last_exception
```

## Graceful Degradation

### Fallback Chain

```python
def get_data_with_fallback(key: str) -> Any:
    """Try multiple data sources in order"""

    # Try primary source
    try:
        return primary_cache.get(key)
    except CacheError:
        logger.warning("Primary cache failed, trying secondary")

    # Try secondary source
    try:
        return secondary_cache.get(key)
    except CacheError:
        logger.warning("Secondary cache failed, fetching from DB")

    # Final fallback
    try:
        return database.fetch(key)
    except DatabaseError as e:
        logger.error(f"All sources failed for key {key}: {e}")
        return None
```

### Partial Success Handling

```python
def process_batch(items: List[Any]) -> Dict[str, List]:
    """Process items and track successes/failures"""

    results = {
        'succeeded': [],
        'failed': []
    }

    for item in items:
        try:
            processed = process_item(item)
            results['succeeded'].append(processed)
        except Exception as e:
            logger.error(f"Failed to process {item}: {e}")
            results['failed'].append({'item': item, 'error': str(e)})

    return results
```

## Circuit Breaker Pattern

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

## Context Managers for Resource Cleanup

```python
from contextlib import contextmanager

@contextmanager
def safe_resource(resource_path: str):
    """Ensure resource cleanup even on error"""
    resource = None
    try:
        resource = open_resource(resource_path)
        yield resource
    except Exception as e:
        logger.error(f"Error using resource {resource_path}: {e}")
        raise
    finally:
        if resource:
            resource.close()
            logger.debug(f"Resource {resource_path} closed")
```

## Validation and Sanitization

```python
from typing import Optional

def safe_dict_access(data: dict, key: str, default: Any = None) -> Any:
    """Safe dictionary access with validation"""
    if not isinstance(data, dict):
        logger.warning(f"Expected dict, got {type(data)}")
        return default

    return data.get(key, default)

def validate_input(value: Any, expected_type: type, constraints: Optional[Callable] = None) -> bool:
    """Validate input with type and constraint checking"""
    if not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type}, got {type(value)}")

    if constraints and not constraints(value):
        raise ValueError(f"Value {value} failed constraint check")

    return True
```
