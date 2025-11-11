# S2 Processing

Fourier-domain analysis helpers that reproduce the legacy MPI/DGD calculations on saved S2 scan cubes.

- Module: `setups.s2_processing`
- Key functions/classes: `process_scan`, `compute_mpi`, `S2AnalysisConfig`, `DGDFilters`

## Quickstart

```python
from setups.s2_processing import process_scan, DGDFilters

result = process_scan(
    "scan_cube.npz",
    fmt="auto",                 # auto-detects .npz vs legacy .npy
    filters=DGDFilters(dc_end_ps=0.5, hom_start_ps=5.0, hom_end_ps=6.5),
    show_plots=True,
    save_figs=False,
)

print(f"Relative power: {result.relative_power_db:.1f} dB")
print(f"HOM peak DGD: {result.hom_peak_dgd_ps:.2f} ps")
```

## Workflow

1. `load_scan()` reads either the modern `.npz` (from `S2RemoteSetup.save_npz`) or legacy `.npy` format.
2. `compute_mpi()` performs FFT filtering, builds dominant/HOM maps, integrates power, and extracts the HOM phase map.
3. `process_scan()` wraps both steps, optionally shows/saves Matplotlib plots, and returns an `S2AnalysisResult`.

## Configuration Highlights

- `DGDFilters` defines the differential group delay bands (in picoseconds) used to isolate fundamental vs HOM components.
- `S2AnalysisConfig` controls the wavelength axis, intensity floor, and filter set if you call `compute_mpi()` directly.
- `S2AnalysisResult` exposes NumPy arrays for the dominant/hom maps, spectra, per-wavelength traces, and aggregate powers (linear + dB).

## API Reference

::: setups.s2_processing.process_scan
    options:
      show_source: false
      show_root_heading: true

::: setups.s2_processing.S2AnalysisResult
    options:
      show_source: false
      show_root_heading: true
