from clients.osa_clients import OSAClient


def main():
    base = "http://127.0.0.1:5000"
    user = "your-name"
    osa = OSAClient(base, "osa_1", span=(1549, 1551), user=user)
    osa.sweep()
    wl = osa.wavelengths
    p = osa.powers
    print(f"OSA points: {len(wl)}; first few wl={wl[:3]}")


if __name__ == "__main__":
    main()

