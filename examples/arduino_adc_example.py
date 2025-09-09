from clients.arduino_adc_client import ArduinoADCClient


def main():
    base = "http://127.0.0.1:5000"
    user = "your-name"
    adc = ArduinoADCClient(base, "arduino_adc_1", port=None, user=user)
    print("Voltage:", adc.get_voltage())
    adc.close()


if __name__ == "__main__":
    main()

