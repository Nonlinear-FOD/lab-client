import requests
import numpy as np
from typing import Any


class LabDeviceClient:
    PROPERTY_METHODS: tuple[str, ...] = ("GET", "POST")

    def __init__(self, base_url: str, device_name: str):
        self.base_url = base_url.rstrip("/")
        self.device_name = device_name
        self.device_url = f"{self.base_url}/devices/{device_name}"

    def _json_or_raise(self, resp: requests.Response) -> dict[str, Any]:
        """
        Raise for HTTP errors. Normalize FastAPI error bodies.
        """
        try:
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            # Try to extract FastAPI-style {"detail": ...}
            try:
                payload = resp.json()
                if isinstance(payload, dict) and "detail" in payload:
                    raise RuntimeError(f"Server error: {payload['detail']}") from e
                if isinstance(payload, dict) and "error" in payload:
                    raise RuntimeError(f"Server error: {payload['error']}") from e
            except Exception:
                pass
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}") from e

    def list_instruments(self) -> dict[str, Any]:
        url = f"{self.base_url}/devices"
        try:
            return self._json_or_raise(requests.get(url))
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Could not retrieve instruments from {url}: {e}"
            ) from e

    def _initialize_device(self, init_payload: dict[str, Any]) -> None:
        url = f"{self.device_url}/connect"
        cleaned_payload = {k: v for k, v in init_payload.items() if v is not None}
        try:
            self._json_or_raise(requests.post(url, json=cleaned_payload))
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Could not connect to device at {self.base_url}: {e}"
            ) from e

    def _request(self, endpoint: str, method: str, value: Any | None = None) -> object:
        url = f"{self.device_url}/{endpoint}"
        if method not in self.PROPERTY_METHODS:
            raise ValueError(f"Method must be {' or '.join(self.PROPERTY_METHODS)}")
        try:
            if method == "GET":
                data = self._json_or_raise(requests.get(url))
                result = data.get("value")
                if isinstance(result, list):
                    return np.array(result)
                return result
            else:  # POST setter
                data = self._json_or_raise(requests.post(url, json={"value": value}))
                return data
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Could not reach {self.base_url}")

    def get_property(self, name: str) -> Any:
        return self._request(name, "GET")

    def set_property(self, name: str, value: Any) -> None:
        self._request(name, "POST", value)

    def disconnect(self) -> None:
        url = f"{self.base_url}/devices/{self.device_name}/disconnect"
        self._json_or_raise(requests.post(url))

    def call(self, name: str, **kwargs: Any) -> Any:
        """
        Call a device method with named kwargs.
        Returns the 'result' field (converted to numpy arrays where appropriate).
        """
        url = f"{self.device_url}/{name}"
        resp = self._json_or_raise(requests.post(url, json=kwargs or {}))
        result = resp.get("result")
        if isinstance(result, list):
            try:
                arr = np.array(result, dtype=object)
                if arr.dtype != object:
                    return arr
            except Exception:
                pass
        return result
