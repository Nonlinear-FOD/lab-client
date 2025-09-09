from clients.laser_clients import VerdiLaserClient


def main():
    base = "http://127.0.0.1:5000"
    user = "your-name"
    verdi = VerdiLaserClient(base, "verdi_1", com_port=None, user=user)
    print("Power:", verdi.power)
    verdi.close()


if __name__ == "__main__":
    main()

