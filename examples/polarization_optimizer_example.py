from clients.arduino_adc_client import ArduinoADCClient
from clients.thorlabs_mpc320_client import ThorlabsMPC320Client
from clients.polarization_optimizer_client import PolarizationOptimizerClient


def main():
    base = "http://127.0.0.1:5000"
    user = "your-name"

    # 1) Connect required devices
    adc = ArduinoADCClient(base, "arduino_adc_1", port=None, user=user)
    mpc = ThorlabsMPC320Client(base, "mpc320_1", user=user)

    # 2) Connect optimizer service (no user/lock needed)
    opt = PolarizationOptimizerClient(base, device_name="pol_opt")

    # 3) Run a quick single-paddle scan (adjust range/step for your setup)
    res = opt.brute_force_optimize_single_paddle(
        mpc_device=mpc.device_name,
        pm_device=adc.device_name,
        paddle_num=1,
        start_pos=0.0,
        end_pos=10.0,
        step_size=1.0,
        max_or_min="max",
    )
    print("Scan result keys:", list(res.keys()))


if __name__ == "__main__":
    main()
