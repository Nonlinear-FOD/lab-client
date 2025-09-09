from clients.laser_clients import AndoLaserClient


def main():
    base = "http://127.0.0.1:5000"
    user = "your-name"
    laser = AndoLaserClient(base, "ando_laser_1", target_wavelength=1550, power=0.0, user=user)
    laser.enable()
    print("Laser wavelength:", laser.wavelength)
    laser.disable()


if __name__ == "__main__":
    main()

