import time
from typing import Any, Dict

import requests


class APIClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(3):  # Retry logic
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = 2**attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                raise APIError(f"HTTP {e.response.status_code}: {e}")

            except requests.exceptions.Timeout:
                if attempt == 2:  # Last attempt
                    raise APIError("Request timed out after 3 attempts")
                continue

            except requests.exceptions.RequestException as e:
                raise APIError(f"Request failed: {e}")

    def get(self, endpoint: str, params: Dict = None) -> Dict:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict) -> Dict:
        return self._request("POST", endpoint, json=data)


class APIError(Exception):
    """Custom exception for API errors"""

    pass
