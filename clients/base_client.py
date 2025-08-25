import requests
from typing import Any
import numpy as np


class LabDeviceClient:
    def __init__(self, base_url: str, device_name: str):
        self.base_url = base_url
        self.device_url = f"{self.base_url}/{device_name}"

    def list_instruments(self) -> dict:
        url = f"{self.base_url}/instruments"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Could not retrieve instruments from {url}: {e}")

    def _initialize_device(self, init_payload: dict) -> None:
        url = f"{self.device_url}/connect"
        try:
            response = requests.post(url, json=init_payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Could not connect to device at {self.base_url}: {e}"
            )

    # TODO: Add a method to disconnect the device
    # TODO: Add generic type hints to the methods
    def _request(self, endpoint: str, method: str, value=None):
        url = f"{self.device_url}/{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url)
                data = resp.json()
                if "error" in data:
                    raise ValueError(
                        f"Server error: {data['error']}\nFull response: {data}"
                    )
                result = data["value"]
                if isinstance(result, list):
                    result = np.array(result)
                return result
            elif method == "POST":
                data = requests.post(url, json={"value": value}).json()
                if "error" in data:
                    raise ValueError(
                        f"Server error: {data['error']}\nFull response: {data}"
                    )
                return data
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Could not reach {self.base_url}")

    def get_property(self, name: str):
        return self._request(name, "GET")

    def set_property(self, name: str, value):
        self._request(name, "POST", value)

    def call_method(self, name: str, *args, expect_response: bool = False) -> Any:
        url = f"{self.device_url}/{name}"
        payload = {"args": args} if args else {}
        response = requests.post(url, json=payload)
        if expect_response:
            json_response = response.json()
            return json_response.get("result", None)
        return None

    # def call_method(self, name: str, *args) -> None:
    #     url = f"{self.device_url}/{name}"
    #     payload = {"args": args} if args else {}
    #     requests.post(url, json=payload)
