# LPG Measurement Setup

The LPG write/read workflow combines the OSA, Zaber stage, Tenma PSU, and
Keithley 2700 clients into a single reusable coordinator. All public helpers
live in `setups.lpg_measurement` so you can script or experiment from an
interactive console without re-implementing the sequencing logic.

## Quick Start

```python
from setups.lpg_measurement import LPGMeasurement, LPGRunSettings

base_url = "http://127.0.0.1:5000"
settings = LPGRunSettings(
    directory="~/lab_runs/lpg",
    file_prefix="sample",
    n_periods=20,
    start_period=0,
    period_um=450.0,
    heat_time_s=5.0,
    measure_delay_s=1.0,
    sleep_before_scan_s=2.0,
    dip_limit_db=10.0,
    burn_factor=1.5,
    headroom=None,
    fixed_voltage_limit_v=10.0,
    wire_power_w=6.2,
    wire_res_ohm=0.1494,
    osa_span_nm=(1450.0, 1650.0),
    osa_resolution_nm=0.5,
    osa_sensitivity="SMID",
    osa_trace="A",
    tension_g=3.5,
    home_offset_um=100.0,
    stage_units="um",
    comment="",
    psu_type="Tenma",
    measure_reference=True,
    reference_path=None,
    plot_stack=True,
    zaber_com_port=None,
    psu_com_port=None,
    psu_channel=2,
)

lpg = LPGMeasurement(
    base_url,
    osa_id="osa_1",
    zaber_id="zaber_1d",
    psu_id="tenma_psu",
    dmm_id="keithley_2700",
    run_settings=settings,
    user="your_name",
    debug=False,
)

result = lpg.run()
wl = result.wavelengths
spectra = result.spectra
lpg.close()
```

All artefacts (spectra CSV, optional plot, settings JSON) are written beneath
`settings.directory` using `settings.file_prefix`.

## Run Settings Reference

A JSON template with the defaults above is tracked at
`testing_client/config/lpg_defaults.json`. You can load or modify it via the
helpers:

```python
from setups.lpg_measurement import LPGRunSettings
settings = LPGRunSettings.from_json("testing_client/config/lpg_defaults.json")
settings.to_json("~/configs/lpg_custom.json")
```

Field overview:

| Field | Default | Description |
| --- | --- | --- |
| `directory` | `"testing_client/_runs/lpg"` | Output folder for spectra, plots, logs, JSON. |
| `file_prefix` | `"lpg_demo"` | Prefix for saved artefacts. |
| `n_periods` | `20` | Maximum periods to write during the run. |
| `start_period` | `0` | Starting index when resuming an existing grating. |
| `period_um` | `450.0` | Stage step per period in micrometres. |
| `heat_time_s` | `5.0` | Duration to hold PSU current. |
| `measure_delay_s` | `1.0` | Extra delay before DMM reading. |
| `sleep_before_scan_s` | `2.0` | Wait before triggering each OSA sweep. |
| `dip_limit_db` | `10.0` | Stop if the spectral dip exceeds this (dB). |
| `burn_factor` | `1.5` | Abort if measured resistance > `burn_factor * wire_res_ohm`. |
| `headroom` | `None` | Optional multiplier for PSU voltage headroom (None → fixed limit). |
| `fixed_voltage_limit_v` | `10.0` | PSU voltage ceiling when `headroom` is `None`. |
| `wire_power_w` | `6.2` | Target heating power, used to derive current. |
| `wire_res_ohm` | `0.1494` | Initial wire resistance estimate. |
| `osa_span_nm` | `(1450.0, 1650.0)` | OSA sweep span (start, stop). |
| `osa_resolution_nm` | `0.5` | OSA resolution bandwidth in nm. |
| `osa_sensitivity` | `"SMID"` | OSA sensitivity mode. |
| `osa_trace` | `"A"` | Active OSA trace to read. |
| `tension_g` | `3.5` | Reference tension value recorded in logs. |
| `home_offset_um` | `100.0` | Stage offset after homing before writing period 0. |
| `stage_units` | `"um"` | Zaber units requested on connect. |
| `comment` | `""` | Free-form note stored in run logs. |
| `psu_type` | `"Tenma"` | Metadata field carried into CSV log. |
| `measure_reference` | `True` | Capture a fresh reference spectrum before writing. |
| `reference_path` | `None` | Optional explicit path to reference CSV. |
| `plot_stack` | `True` | Enable live Matplotlib plot and PNG export. |
| `zaber_com_port` | `None` | Override COM port when instantiating `Zaber1DMotorClient`. |
| `psu_com_port` | `None` | Override COM port for `TenmaPSUClient`. |
| `psu_channel` | `2` | Active PSU channel to drive. |

## Dependency Injection for Testing

`LPGMeasurement` accepts optional client instances via the `osa`, `zaber`,
`psu`, and `dmm` keyword arguments. Each must implement the minimal protocol
(`span`, `sweep`, `move_relative`, etc.), which makes it easy to supply fakes or
wrap existing simulator classes during offline testing. Omitting one of the
arguments creates the standard HTTP client for you.

## Generated Artefacts

During a run the coordinator:

- saves stacked spectra to `<prefix>_spectra.csv`
- optionally captures a stack plot to `<prefix>_plot.png`
- records the run configuration in `<prefix>_log.csv` (legacy format) and
  `<prefix>_run.json`

Disable live plotting by setting `plot_stack=False` in the run settings.
## API Reference

::: setups.lpg_measurement.LPGMeasurement
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      filters:
        - "!^_"
