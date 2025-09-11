from clients.base_client import LabDeviceClient
from typing import Any, Protocol


class _HasDeviceName(Protocol):
    @property
    def device_name(self) -> str: ...


class PolarizationOptimizerClient(LabDeviceClient):
    """Client for Polarization Optimizer service.

    Server-side driver: `devices.pol_opt_service.PolarizationOptimizer`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Service name in server config (default `pol_opt`).
        debug: When true, server returns detailed error payloads.

    Notes:
        - Stateless service. It composes MPC320 and a fast ADC by resolving
          `*_device` arguments to live device instances on the server.
        - Instantiate without `user` (no lock) — the service config sets `no_lock=true`.
    """

    def __init__(
        self, base_url: str, device_name: str = "pol_opt", debug: bool = False
    ) -> None:
        # no user header needed; server config sets no_lock=true for this service
        super().__init__(base_url, device_name, user=None, debug=debug)
        # stateless: connect without init params
        self._initialize_device({})

    @staticmethod
    def _name(x: str | _HasDeviceName) -> str:
        return x if isinstance(x, str) else x.device_name

    def brute_force_optimize_single_paddle(
        self,
        mpc_device: str | _HasDeviceName,
        pm_device: str | _HasDeviceName,
        paddle_num: int,
        start_pos: float = 0.0,
        end_pos: float = 165.9,
        max_or_min: str = "max",
    ) -> dict:
        """Continuously scan a single paddle and snap to the best position.

        Args:
            mpc_device: Name of a connected MPC320 device (can use .device_name).
            pm_device: Name of a connected ADC/PM implementing `get_voltage()` (can use .device_name).
            paddle_num: Paddle index (1–3).
            start_pos: Start position of scan (deg).
            end_pos: End position of scan (deg).
            max_or_min: Optimize for `'max'` or `'min'` signal.

        Returns:
            Dict with keys `angles` and `values` (lists of floats).
        """
        return self.call(
            "brute_force_optimize_single_paddle",
            mpc_device=self._name(mpc_device),
            pm_device=self._name(pm_device),
            paddle_num=paddle_num,
            start_pos=start_pos,
            end_pos=end_pos,
            max_or_min=max_or_min,
        )

    def brute_force_optimize(
        self,
        mpc_device: str | _HasDeviceName,
        pm_device: str | _HasDeviceName,
        start_pos: float = 0.0,
        end_pos: float = 165.9,
        max_or_min: str = "max",
    ) -> dict:
        """Continuously scan all paddles of one MPC320 and snap to best positions of all paddles.

        Args:
            mpc_device: Name of the MPC320 device (can use .device_name).
            pm_device: Name of the ADC/PM device (can use .device_name).
            start_pos: Start position of scan (deg).
            end_pos: End position of scan (deg).
            max_or_min: Optimize for `'max'` or `'min'` signal.
        """
        return self.call(
            "brute_force_optimize",
            mpc_device=self._name(mpc_device),
            pm_device=self._name(pm_device),
            start_pos=start_pos,
            end_pos=end_pos,
            max_or_min=max_or_min,
        )

    def move_and_monitor(
        self,
        mpc_device: str | _HasDeviceName,
        pm_device: str | _HasDeviceName,
        paddle_num: int,
        start_pos: float,
        end_pos: float,
        interval_ms: int = 10,
        timeout_s: float = 60.0,
    ) -> dict:
        """Move a paddle while continuously monitoring power.

        Args:
            mpc_device: MPC320 device name or client object.
            pm_device: ADC/PM device name or client object.
            paddle_num: Paddle index (1–3).
            start_pos: Start position of scan (deg).
            end_pos: End position of scan (deg).
            interval_ms: Polling interval for monitor thread (ms).
            timeout_s: Move timeout on the server (s).

        Returns:
            Dict with keys `positions` and `values` (lists of floats).
        """
        return self.call(
            "move_and_monitor",
            mpc_device=self._name(mpc_device),
            pm_device=self._name(pm_device),
            paddle_num=paddle_num,
            start_pos=start_pos,
            end_pos=end_pos,
            interval_ms=interval_ms,
            timeout_s=timeout_s,
        )

    def optimize_multiple_pol_cons(
        self,
        pm_device: str | _HasDeviceName,
        mpc_a_device: str | _HasDeviceName,
        mpc_b_device: str | _HasDeviceName | None = None,
        mpc_c_device: str | _HasDeviceName | None = None,
        max_or_min: str = "max",
        tolerance: float | None = None,
        start_pos: float = 0.0,
        end_pos: float = 165.9,
    ) -> dict:
        """Optimize multiple MPC320 controllers sequentially using `brute_force_optimize`.

        Args:
            pm_device: Name of ADC/PM device.
            mpc_a_device: First MPC320 device name.
            mpc_b_device: Optional second MPC320 device.
            mpc_c_device: Optional third MPC320 device.
            max_or_min: Optimize for `'max'` or `'min'` signal.
            tolerance: Stop when absolute improvement <= tolerance (if set).
            start_pos: Start position of scan (deg).
            end_pos: End position of scan (deg).
        """
        payload: dict[str, Any] = {
            "pm_device": self._name(pm_device),
            "mpc_a_device": self._name(mpc_a_device),
            "max_or_min": max_or_min,
            "start_pos": start_pos,
            "end_pos": end_pos,
        }
        if tolerance is not None:
            payload["tolerance"] = tolerance
        if mpc_b_device is not None:
            payload["mpc_b_device"] = self._name(mpc_b_device)
        if mpc_c_device is not None:
            payload["mpc_c_device"] = self._name(mpc_c_device)
        return self.call("optimize_multiple_pol_cons", **payload)
