from __future__ import annotations

import json
import os
import time
import webbrowser
from pathlib import Path
from typing import Any

import requests

DEFAULT_TOKEN_PATH = Path(
    os.environ.get("LAB_CLIENT_TOKEN_PATH", Path.home() / ".remote_lab_auth.json")
)


class AuthError(RuntimeError):
    """Base class for auth failures."""


class AuthHttpError(AuthError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"HTTP {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class LabAuthManager:
    """
    Handles GitHub-backed auth against the lab server:
    - Stores tokens per server under ~/.remote_lab_auth.json (override via LAB_CLIENT_TOKEN_PATH).
    - Runs the GitHub device code flow on first use (interactive prompt).
    - Refreshes tokens automatically and injects Authorization headers for requests.
    """

    def __init__(
        self,
        base_url: str,
        token_path: str | Path | None = None,
        interactive: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.token_path = Path(token_path) if token_path else DEFAULT_TOKEN_PATH
        self.interactive = interactive
        self._session: dict[str, Any] | None = None

    # ------------------------------
    # Public API
    # ------------------------------
    def authorization_header(self, force_refresh: bool = False) -> str:
        session = self._ensure_session(force_login=force_refresh)
        return f"Bearer {session['access_token']}"

    def user_login(self) -> str | None:
        session = self._session or self._load_session_from_disk()
        if not session:
            return None
        user = session.get("user") or {}
        return user.get("login")

    def reset_session(self) -> None:
        """Drop cached tokens so the next call triggers a fresh login."""
        self._clear_session()

    # ------------------------------
    # Session lifecycle helpers
    # ------------------------------
    def _ensure_session(self, *, force_login: bool = False) -> dict[str, Any]:
        if force_login:
            self._clear_session()
        session = self._session or self._load_session_from_disk()
        if session and not self._expired(session.get("access_token_expires_at")):
            self._session = session
            return session

        if session and not self._expired(session.get("refresh_token_expires_at")):
            try:
                refreshed = self._refresh(session["refresh_token"])
                self._persist(refreshed)
                self._session = refreshed
                return refreshed
            except AuthHttpError as exc:
                if exc.status_code in (400, 401):
                    self._clear_session()
                else:
                    raise

        if not self.interactive:
            raise AuthError(
                "Authentication required but interactive login is disabled. "
                "Set interactive=True or pass a valid session."
            )
        new_session = self._interactive_login()
        self._persist(new_session)
        self._session = new_session
        return new_session

    def _refresh(self, refresh_token: str) -> dict[str, Any]:
        data = self._request(
            "POST",
            "/auth/token",
            json={"refresh_token": refresh_token},
        )
        return self._normalize_session(data)

    def _interactive_login(self) -> dict[str, Any]:
        start = self._request("POST", "/auth/device/start")
        verification = start.get("verification_uri_complete") or start.get(
            "verification_uri"
        )
        user_code = start.get("user_code")
        visit_line = (
            f"  1. Visit {verification}"
            if verification
            else "  1. Visit https://github.com/login/device"
        )
        print(
            f"[remote-lab] Sign in to GitHub to access {self.base_url}:\n"
            f"{visit_line}\n"
            f"  2. Enter the code: {user_code}"
        )
        if verification:
            try:
                webbrowser.open(verification)
            except Exception:
                pass
        device_code = start["device_code"]
        interval = int(start.get("interval", 5))
        while True:
            time.sleep(interval)
            result = self._request(
                "POST", "/auth/device/poll", json={"device_code": device_code}
            )
            status_flag = result.get("status")
            if status_flag == "pending":
                interval = int(result.get("interval", interval))
                continue
            if status_flag == "ok":
                return self._normalize_session(result)
            raise AuthError(result.get("detail", "Device flow failed"))

    # ------------------------------
    # Disk helpers
    # ------------------------------
    def _persist(self, session: dict[str, Any]) -> None:
        payload = self._read_file()
        payload[self.base_url] = session
        self._write_file(payload)

    def _load_session_from_disk(self) -> dict[str, Any] | None:
        data = self._read_file()
        session = data.get(self.base_url)
        if session and self._expired(session.get("refresh_token_expires_at")):
            self._clear_session()
            return None
        return session

    def _clear_session(self) -> None:
        data = self._read_file()
        if self.base_url in data:
            data.pop(self.base_url, None)
            self._write_file(data)
        self._session = None

    def _read_file(self) -> dict[str, Any]:
        if not self.token_path.exists():
            return {}
        try:
            with open(self.token_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_file(self, data: dict[str, Any]) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.token_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp_path, self.token_path)
        try:
            os.chmod(self.token_path, 0o600)
        except PermissionError:
            pass

    # ------------------------------
    # HTTP helpers
    # ------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.request(method, url, timeout=15, **kwargs)
        except requests.RequestException as exc:
            raise AuthError(f"Failed to reach {url}: {exc}") from exc
        if resp.status_code >= 400:
            detail = self._extract_detail(resp)
            raise AuthHttpError(resp.status_code, detail)
        try:
            return resp.json()
        except ValueError as exc:
            raise AuthError(f"Invalid JSON response from {url}") from exc

    @staticmethod
    def _extract_detail(resp: requests.Response) -> str:
        try:
            data = resp.json()
            if isinstance(data, dict):
                for key in ("detail", "error", "message"):
                    if key in data:
                        return str(data[key])
        except ValueError:
            pass
        return resp.text

    # ------------------------------
    # Utility helpers
    # ------------------------------
    @staticmethod
    def _expired(timestamp: float | int | None, skew: int = 30) -> bool:
        if not timestamp:
            return True
        return float(timestamp) <= time.time() + skew

    @staticmethod
    def _normalize_session(raw: dict[str, Any]) -> dict[str, Any]:
        user = raw.get("user") or {}
        issued = raw.get("issued_at", int(time.time()))
        return {
            "user": user,
            "issued_at": issued,
            "access_token": raw["access_token"],
            "access_token_expires_at": issued + int(raw["access_token_expires_in"]),
            "refresh_token": raw["refresh_token"],
            "refresh_token_expires_at": issued + int(raw["refresh_token_expires_in"]),
        }
