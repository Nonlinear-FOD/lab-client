from __future__ import annotations

from clients.tenma_psu_client import TenmaPSUClient


BASE = "http://127.0.0.1:5000"
DEVICE = "tenma_psu"
USER = "your-name"


psu = TenmaPSUClient(BASE, DEVICE, com_port=None, user=USER, debug=True)

# Channel 1
psu.channel = 1
psu.voltage_set = 5.00
psu.current_set = 0.50
psu.output = True
print("CH1 V/I:", psu.voltage, psu.current)

# Channel 2
psu.channel = 2
psu.voltage_set = 12.00
psu.current_set = 0.25
print("CH2 V/I:", psu.voltage, psu.current)

# Global status and output off
print(psu.status())
psu.output = False
psu.close()
