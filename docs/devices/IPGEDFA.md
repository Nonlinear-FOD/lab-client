# IPG EDFA Amplifier

- Client: `clients.ipg_edfa_client.IPGEDFAClient`
- Server driver: `devices.ipg_edfa.IPGEDFA`

## Quickstart

```python
from clients.ipg_edfa_client import IPGEDFAClient

base = "http://127.0.0.1:5000"
user = "alice"
edfa = IPGEDFAClient(
    base_url=base,
    device_name="ipg_edfa",
    user=user,
)

# Configure device: power unit, mode, and setpoints
edfa.power_unit = "dBm"
edfa.mode = "APC"
edfa.power_set_point = "20"
edfa.gain_set_point = "25"
edfa.current_set_point = "1.2"
edfa.emission = 1

# Read output and input power
print("Output power:", edfa.read_output_power())
print("Input power:", edfa.input_power())

# Read diode current and back-reflection level
print("Diode current:", edfa.read_diode_current())
print("Back-reflection level:", edfa.back_reflection_level())

# Read raw device status
print("Device status:", edfa.stat())

# Low-level SCPI commands
edfa.write("SOUR:POW 20")
response = edfa.query("SOUR:POW?")
print("SCPI query response:", response)

# Turn off emission and close connection
edfa.emission = 0
edfa.close()
