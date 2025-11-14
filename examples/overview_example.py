from clients.lab_overview_client import LabOverviewClient


def main():
    base = "http://127.0.0.1:5000"  # replace with your server
    user = "your-name"
    ov = LabOverviewClient(base, user=user)

    print("Devices:", ov.devices())
    print("Locks:", ov.list_used_instruments())
    print("Resources:", ov.list_connected_instruments())


if __name__ == "__main__":
    main()
