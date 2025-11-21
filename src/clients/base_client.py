import os
from pathlib import Path
from typing import Any

import numpy as np
import requests

from .auth_manager import AuthError, LabAuthManager


class LabDeviceClient:
    """Base client for device endpoints exposed by the lab server. If None is passed to `__init__`, default values
    defined in the `config*.json` files or defaults from the `server*/devices*/.py` will be used.

    What it does:

    - Stores the server `base_url` and `device_name` and builds request URLs.
    - Adds `X-User` and `X-Debug` headers when configured (locks + rich errors).
    - Handles GitHub-based auth via LabAuthManager, storing tokens per server.
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
        auth: LabAuthManager | None = None,
        token_path: str | Path | None = None,
        interactive_auth: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.device_name = device_name
        self.device_url = f"{self.base_url}/devices/{device_name}"
        self._auth = auth
        if self._auth is None and not _auth_disabled():
            self._auth = LabAuthManager(
                self.base_url,
                token_path=token_path,
                interactive=interactive_auth,
            )
        self.user = user or (self._auth.user_login() if self._auth else None)
        self.debug = bool(debug)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.user:
            headers["X-User"] = self.user
        if self.debug:
            headers["X-Debug"] = "1"
        if self._auth:
            try:
                headers["Authorization"] = self._auth.authorization_header()
                if "X-User" not in headers:
                    login = self._auth.user_login()
                    if login:
                        headers["X-User"] = login
                        self.user = login
            except AuthError as exc:
                raise RuntimeError(
                    f"Authentication with {self.base_url} failed: {exc}"
                ) from exc
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
        resp = self._perform_request("POST", url, json=cleaned_payload)
        self._json_or_raise(resp)

    def _request(self, endpoint: str, method: str, value: Any | None = None) -> object:
        url = f"{self.device_url}/{endpoint}"
        if method not in self.PROPERTY_METHODS:
            raise ValueError(f"Method must be {' or '.join(self.PROPERTY_METHODS)}")
        if method == "GET":
            resp = self._perform_request("GET", url)
            data = self._json_or_raise(resp)
            result = data.get("value")
            if isinstance(result, list):
                return np.array(result)
            return result
        else:
            resp = self._perform_request("POST", url, json={"value": value})
            return self._json_or_raise(resp)

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
        resp = self._perform_request("POST", url)
        self._json_or_raise(resp)

    def call(self, name: str, **kwargs: Any) -> Any:
        """
        Call a device method with named kwargs.
        Returns the 'result' field (converted to numpy arrays where appropriate).
        """
        url = f"{self.device_url}/{name}"
        resp = self._perform_request("POST", url, json=kwargs or {})
        resp = self._json_or_raise(resp)
        if "detail" in resp and "result" not in resp:
            raise RuntimeError(str(resp["detail"]))
        result = resp.get("result")
        if isinstance(result, list):
            try:
                arr = np.array(result, dtype=object)
                if arr.dtype != object:
                    return arr
            except Exception:
                pass
        return result

    def _perform_request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """
        Send an HTTP request with auth retry logic. If the server responds 401 once,
        the cached session is dropped and the request is re-issued (triggering a fresh login).
        """
        base_payload = dict(kwargs)
        timeout = base_payload.pop("timeout", None)
        attempts = 0
        while True:
            payload = dict(base_payload)
            try:
                resp = requests.request(
                    method,
                    url,
                    headers=self._headers(),
                    timeout=timeout,
                    **payload,
                )
            except requests.exceptions.RequestException as exc:
                raise ConnectionError(f"Could not reach {self.base_url}: {exc}") from exc

            if (
                resp.status_code == 401
                and self._auth
                and attempts == 0
            ):
                self._auth.reset_session()
                attempts += 1
                continue
            return resp


def _auth_disabled() -> bool:
    return os.environ.get("LAB_CLIENT_DISABLE_AUTH", "").lower() in (
        "1",
        "true",
        "yes",
    )
