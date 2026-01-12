# IPG EDFA Amplifier

- Client: `clients.ipg_edfa_client.IPGEDFAClient`
- Server driver: `devices.ipg_edfa.IPGEDFA`

## Quickstart

```python
from clients.ipg_edfa_client import IPGEDFAClient

base = "http://127.0.0.1:5000"
user = "alice"
edfa = IPGEDFAClient(base, "ipg_edfa_1", user=user)

# Configure the EDFA
edfa.power_unit = "dBm"          # Set units for power
edfa.mode = "APC"                # Control mode: APC, ACC, AGC
edfa.power_set_point = "20"      # Target output power
edfa.gain_set_point = "25"       # Target gain (AGC mode)
edfa.current_set_point = "1.2"   # Target diode current (ACC mode)
edfa.emission = 1                # Turn on emission

# Read device values
print(edfa.read_output_power())
print(edfa.input_power())
print(edfa.read_diode_current())
print(edfa.back_reflection_level())
print(edfa.stat())

# Send raw SCPI command
edfa.write("SOUR:POW 20")
response = edfa.query("SOUR:POW?")
print(response)

# Turn off emission and close
edfa.emission = 0
edfa.close()
```

## API Reference

::: clients.ipg_edfa_client.IPGEDFAClient
    options:
      show_source: false
      members_order: source

