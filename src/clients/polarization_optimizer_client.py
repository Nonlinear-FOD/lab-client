from clients.base_client import LabDeviceClient
from typing import Any


class PolarizationOptimizerClient(LabDeviceClient):
    """Client for Polarization Optimizer service.

    Server-side driver: `devices.pol_opt_service.PolarizationOptimizer`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Service name in server config (default `pol_opt`).
        debug: When true, server returns detailed error payloads.

    Notes:
        - Stateless service. It composes an MPC320 and a fast ADC by resolving
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

    def brute_force_optimize_single_paddle(
        self,
        mpc_device: str,
        pm_device: str,
        paddle_num: int,
        start_pos: float = 0.0,
        end_pos: float = 165.9,
        max_or_min: str = "max",
    ) -> dict:
        """Continuously scan a single paddle and snap to the best position.

        Parameters
        - mpc_device: Name of a connected MPC320 device.
        - pm_device: Name of a connected ADC/PM implementing `get_voltage()`.
        - paddle_num: Paddle index (1–3).
        - start_pos, end_pos: Scan bounds in degrees.
        - max_or_min: Optimize for `'max'` or `'min'` signal.

        Returns
        - dict with keys `angles` and `values` (lists of floats).
        """
        return self.call(
            "brute_force_optimize_single_paddle",
            mpc_device=mpc_device,
            pm_device=pm_device,
            paddle_num=paddle_num,
            start_pos=start_pos,
            end_pos=end_pos,
            max_or_min=max_or_min,
        )

    def brute_force_optimize(
        self,
        mpc_device: str,
        pm_device: str,
        start_pos: float = 0.0,
        end_pos: float = 165.9,
        max_or_min: str = "max",
    ) -> dict:
        """Continuously scan all paddles of one MPC320.

        Parameters
        - mpc_device, pm_device, start_pos, end_pos, max_or_min: See single-paddle variant.
        """
        return self.call(
            "brute_force_optimize",
            mpc_device=mpc_device,
            pm_device=pm_device,
            start_pos=start_pos,
            end_pos=end_pos,
            max_or_min=max_or_min,
        )

    def move_and_monitor(
        self,
        mpc_device: str,
        pm_device: str,
        paddle_num: int,
        start_pos: float,
        end_pos: float,
        interval_ms: int = 10,
        timeout_s: float = 60.0,
    ) -> dict:
        """Move a paddle while continuously monitoring power.

        Returns a dict: `{"positions": [...], "values": [...]}`.
        """
        return self.call(
            "move_and_monitor",
            mpc_device=mpc_device,
            pm_device=pm_device,
            paddle_num=paddle_num,
            start_pos=start_pos,
            end_pos=end_pos,
            interval_ms=interval_ms,
            timeout_s=timeout_s,
        )

    def optimize_multiple_pol_cons(
        self,
        pm_device: str,
        mpc_a_device: str,
        mpc_b_device: str | None = None,
        mpc_c_device: str | None = None,
        max_or_min: str = "max",
        tolerance: float | None = None,
        start_pos: float = 0.0,
        end_pos: float = 165.9,
    ) -> dict:
        """Optimize multiple MPC320 controllers sequentially until tolerance.

        Parameters
        - pm_device: Name of ADC/PM device.
        - mpc_a_device/b/c_device: Names of one or more MPC320 devices.
        - max_or_min: Optimize for `'max'` or `'min'` signal.
        - tolerance: Stop when absolute improvement <= tolerance (if set).
        - start_pos, end_pos: Scan parameters.
        """
        payload: dict[str, Any] = {
            "pm_device": pm_device,
            "mpc_a_device": mpc_a_device,
            "max_or_min": max_or_min,
            "start_pos": start_pos,
            "end_pos": end_pos,
        }
        if tolerance is not None:
            payload["tolerance"] = tolerance
        if mpc_b_device is not None:
            payload["mpc_b_device"] = mpc_b_device
        if mpc_c_device is not None:
            payload["mpc_c_device"] = mpc_c_device
        return self.call("optimize_multiple_pol_cons", **payload)
