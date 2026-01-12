# IPG EDFA Amplifier

- Client: `clients.ipg_edfa_client.IPGEDFAClient`
- Server driver: `devices.ipg_edfa.IPGEDFA`

## Quickstart

```python
from clients.ipg_edfa_client import IPGEDFAClient

base = "http://127.0.0.1:5000"
user = "alice"

# Initialize the IPG EDFA client
edfa = IPGEDFAClient(base_url=base, device_name="ipg_edfa_1", user=user)

# Configure device: power unit, mode, and setpoints
edfa.power_unit = "dBm"         # Power unit can be 'dBm' or 'W'
edfa.mode = "APC"               # Control mode: APC, ACC, AGC
edfa.power_set_point = "20"     # Target output power
edfa.gain_set_point = "25"      # Target gain (for AGC mode)
edfa.current_set_point = "1.2"  # Target diode current (for ACC mode)
edfa.emission = 1               # Turn on emission

# Read values
print("Output power:", edfa.read_output_power())
print("Input power:", edfa.input_power())
print("Diode current:", edfa.read_diode_current())
print("Back-reflection level:", edfa.back_reflection_level())
print("Device status:", edfa.stat())

# Low-level SCPI commands
edfa.write("SOUR:POW 20")
response = edfa.query("SOUR:POW?")
print("SCPI query response:", response)

# Turn off emission and close connection
edfa.emission = 0
edfa.close()
