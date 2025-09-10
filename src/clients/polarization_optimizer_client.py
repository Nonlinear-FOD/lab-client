from clients.base_client import LabDeviceClient
from typing import Any


class PolarizationOptimizerClient(LabDeviceClient):
    """Client for Polarization Optimizer service.

    Server-side driver: devices.pol_opt_service.PolarizationOptimizer
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
