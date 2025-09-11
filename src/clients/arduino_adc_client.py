from clients.base_client import LabDeviceClient


class ArduinoADCClient(LabDeviceClient):
    """Client for Arduino ADC (power meter) service.

    Server-side driver: devices.arduino_adc.ArduinoADC
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        *,
        com_port: int | None = None,
        baudrate: int | None = None,
        bytesize: int | None = None,
        stopbits: int | None = None,
        timeout_s: float | None = None,
        terminator: str | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        init_params = {
            "com_port": com_port,
            "baudrate": baudrate,
            "bytesize": bytesize,
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
        self.disconnect()
