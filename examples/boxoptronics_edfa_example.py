from clients.boxoptronics_edfa_client import BoxoptronicsEDFAClient


def main():
    base = "http://127.0.0.1:5000"
    user = "your-name"
    edfa = BoxoptronicsEDFAClient(base, "edfa_1", user=user)
    print("Status:", edfa.read_status())


if __name__ == "__main__":
    main()

