# LPG Fabrication Setup

The LPG write/read workflow combines the OSA, Zaber stage, Tenma PSU, and
Keithley 2700 clients into a single reusable coordinator. All public helpers
live in `setups.lpg_fabrication`.

## Quick Start

```python
from pathlib import Path
from setups.lpg_fabrication import LPGFab, LPGRunSettings

base_url = "http://127.0.0.1:5000"
defaults_path = Path.home() / "Documents" / "lpg_defaults.json"

if not defaults_path.exists():
    defaults_path.parent.mkdir(parents=True, exist_ok=True)
    LPGRunSettings().to_json(defaults_path)

settings = LPGRunSettings.from_json(defaults_path)
settings.file_prefix = "sample_A1"
settings.directory = r"C:\\data\\lpg_runs"

lpg = LPGFab(
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

settings.to_json(defaults_path)
```

All artefacts (spectra CSV, optional plot, settings JSON) are written beneath
`settings.directory` using `settings.file_prefix`.

## Default Settings File

The repository does not ship a baked-in defaults JSON. Create one once, keep it
under version control alongside your experiment notes, and load it with
`LPGRunSettings.from_json()` in scripts or notebooks. A minimal bootstrap looks
like:

```python
from pathlib import Path
from setups.lpg_fabrication import LPGRunSettings

defaults_path = Path.home() / "Documents" / "lpg_defaults.json"
defaults_path.parent.mkdir(parents=True, exist_ok=True)

settings = LPGRunSettings()
settings.directory = r"C:\\data\\lpg_runs"
settings.file_prefix = "sample_A1"
settings.to_json(defaults_path)
```

Later runs can load the same file, tweak fields in-memory (e.g.
`settings.n_periods = 30`), and call `settings.to_json(defaults_path)` to persist
your new baseline.

## Run Settings Reference

The table below lists the values returned by `LPGRunSettings()` before any
customisation:

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

## Generated Artefacts

`settings.file_prefix` determines the stem used for all outputs. For example,
with `settings.directory = r"C:\\data\\lpg_runs"` and
`settings.file_prefix = "sample_A1"`, a run produces:

- `C:\data\lpg_runs\sample_A1_spectra.csv`
- `C:\data\lpg_runs\sample_A1_plot.png` (only when `plot_stack=True`)
- `C:\data\lpg_runs\sample_A1_log.csv`
- `C:\data\lpg_runs\sample_A1_run.json`

Disable live plotting by setting `plot_stack=False` in the run settings.
## API Reference

::: setups.lpg_fabrication.LPGFab
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      filters:
        - "!^_"
