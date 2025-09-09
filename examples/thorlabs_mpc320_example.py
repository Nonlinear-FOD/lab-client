from clients.thorlabs_mpc320_client import ThorlabsMPC320Client


def main():
    base = "http://127.0.0.1:5000"
    user = "your-name"
    mpc = ThorlabsMPC320Client(base, "mpc320_1", user=user)
    print("Velocity:", mpc.velocity)
    print("Paddle 1 position:", mpc.get_position(1))
    mpc.set_position(1, 10.0, timeout_s=10)


if __name__ == "__main__":
    main()

