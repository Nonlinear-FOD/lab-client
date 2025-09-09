from clients.base_client import LabDeviceClient


class ArduinoADCClient(LabDeviceClient):
    def __init__(
        self,
        base_url: str,
        device_name: str,
        *,
        port: str | None = None,
        baudrate: int | None = None,
        bytesize: int | None = None,
        parity: str | None = None,
        stopbits: int | None = None,
        timeout_s: float | None = None,
        terminator: str | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        init_params = {
            "port": port,
            "baudrate": baudrate,
            "bytesize": bytesize,
            "parity": parity,
            "stopbits": stopbits,
            "timeout_s": timeout_s,
            "terminator": terminator,
        }
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    def get_voltage(self) -> float:
        resp = self.call("get_voltage")
        # server returns {'result': <float>}
        return float(resp)

    def close(self) -> None:
        self.call("close")

