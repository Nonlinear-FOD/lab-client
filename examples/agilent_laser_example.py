from clients.laser_clients import AgilentLaserClient


def main():
    base = "http://127.0.0.1:5000"
    user = "your-name"
    laser = AgilentLaserClient(base, "agilent_laser_1", target_wavelength=1550, power=-10, source=1, user=user)
    print("Unit:", laser.unit)
    print("Wavelength:", laser.wavelength)


if __name__ == "__main__":
    main()

