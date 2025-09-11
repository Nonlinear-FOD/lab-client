import requests
import numpy as np
from typing import Any


class LabDeviceClient:
    """Base client for device endpoints exposed by the lab server. If None is passed to `__init__`, default values
    defined in the `config*.json` files or defaults from the `server*/devices*/.py` will be used.

    What it does:

    - Stores the server `base_url` and `device_name` and builds request URLs.
    - Adds `X-User` and `X-Debug` headers when configured (locks + rich errors).
    - Normalizes HTTP/JSON errors to Python exceptions with readable messages.
    - Provides helpers for property GET/SET, method calls, and disconnect.
    - Converts JSON lists to numpy arrays where appropriate.

    In practice, you will instantiate a device‑specific client (e.g.,
    `OSAClient`, `AndoLaserClient`, etc.). Those call `_initialize_device()`
    in their constructor to POST `/devices/{name}/connect` with init params.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from the server config (e.g., `osa_1`).
        user: Optional user name used for server‑side locking (`X-User`).
        debug: When true, include `X-Debug: 1` to receive detailed server errors.

    Notes:
        - All concrete clients implement `.close()` that delegates to
          `.disconnect()` to drop the server instance and release locks.
        - `get_property()` returns JSON scalars or numpy arrays (for list values).
        - `call()` returns the server `result` field, converted to numpy arrays
          when the payload is a homogeneous list.
        - Initialization: each device has a server-side config keyed by
          `device_name` containing transport details (e.g., VISA resource,
          COM port, serial number) and sensible defaults. Client constructors
          only need `device_name` in the common case; any non-`None` keyword
          arguments you pass will override the config for that session.
    """

    PROPERTY_METHODS: tuple[str, ...] = ("GET", "POST")

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.device_name = device_name
        self.device_url = f"{self.base_url}/devices/{device_name}"
        self.user = user
        self.debug = bool(debug)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.user:
            headers["X-User"] = self.user
        if self.debug:
            headers["X-Debug"] = "1"
        return headers

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

    def _initialize_device(self, init_payload: dict[str, Any]) -> None:
        url = f"{self.device_url}/connect"
        cleaned_payload = {k: v for k, v in init_payload.items() if v is not None}
        try:
            self._json_or_raise(
                requests.post(url, json=cleaned_payload, headers=self._headers())
            )
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
                data = self._json_or_raise(requests.get(url, headers=self._headers()))
                result = data.get("value")
                if isinstance(result, list):
                    return np.array(result)
                return result
            else:  # POST setter
                data = self._json_or_raise(
                    requests.post(url, json={"value": value}, headers=self._headers())
                )
                return data
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Could not reach {self.base_url}")

    def get_property(self, name: str) -> Any:
        return self._request(name, "GET")

    def set_property(self, name: str, value: Any) -> None:
        self._request(name, "POST", value)

    def disconnect(self) -> None:
        """
        Fully tear down the server-side device instance.

        Workflow:
        - Sends POST /devices/{name}/disconnect
        - Server calls the device's own close(), removes the cached instance,
          and releases any user lock so a future connect creates a fresh instance.
        - All client .close() methods delegate to .disconnect() for consistency.
        """
        url = f"{self.base_url}/devices/{self.device_name}/disconnect"
        self._json_or_raise(requests.post(url, headers=self._headers()))

    def call(self, name: str, **kwargs: Any) -> Any:
        """
        Call a device method with named kwargs.
        Returns the 'result' field (converted to numpy arrays where appropriate).
        """
        url = f"{self.device_url}/{name}"
        resp = self._json_or_raise(
            requests.post(url, json=kwargs or {}, headers=self._headers())
        )
        result = resp.get("result")
        if isinstance(result, list):
            try:
                arr = np.array(result, dtype=object)
                if arr.dtype != object:
                    return arr
            except Exception:
                pass
        return result
