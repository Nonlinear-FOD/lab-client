"""Updated S2 post-processing helpers based on the legacy Fourier pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Tuple

import numpy as np
from scipy.integrate import simpson

SPEED_OF_LIGHT = 299_792_458.0  # m/s


def _bandpass(size: int, start: int, end: int) -> np.ndarray:
    arr = np.zeros(size, dtype=float)
    start = max(0, min(start, size - 1))
    end = max(start, min(end, size - 1))
    arr[start : end + 1] = 1.0
    return arr


def _simps2d(array: np.ndarray) -> float:
    """Apply Simpson integration over both spatial axes."""
    return float(simpson(simpson(array, axis=0), axis=0))


@dataclass
class DGDFilters:
    """DGD-based band definitions (ps) for the Fourier filter."""

    dc_end_ps: float = 0.5
    hom_start_ps: float = 5.05
    hom_end_ps: float = 6.55


@dataclass
class S2AnalysisConfig:
    """Configuration for S2 Fourier-domain analysis."""

    filters: DGDFilters = field(default_factory=DGDFilters)
    wavelength_axis: int = 0
    min_intensity: float = 1e-12


@dataclass
class S2AnalysisResult:
    """MPI summary plus intermediate maps and spectra."""

    wavelengths_nm: np.ndarray
    dgd_axis_ps: np.ndarray
    dgd_spectrum: np.ndarray
    dominant_map: np.ndarray
    hom_map: np.ndarray
    dominant_vs_wavelength: np.ndarray
    hom_vs_wavelength: np.ndarray
    hom_peak_dgd_ps: float
    hom_phase_map: np.ndarray
    mpi_db: float
    dominant_power: float
    hom_power: float


def _prepare_cube(
    cube: np.ndarray,
    wavelengths_nm: np.ndarray,
    config: S2AnalysisConfig,
) -> Tuple[np.ndarray, np.ndarray]:
    cube = np.asarray(cube, dtype=float)
    wavelengths_nm = np.asarray(wavelengths_nm, dtype=float)
    if cube.ndim != 3:
        raise ValueError("cube must be (steps, rows, cols)")
    if cube.shape[config.wavelength_axis] != wavelengths_nm.size:
        raise ValueError("wavelength axis does not match wavelength array length")
    if np.any(np.diff(wavelengths_nm) <= 0):
        raise ValueError("wavelength array must be strictly increasing")
    steps = wavelengths_nm.size
    if steps < 4:
        raise ValueError("need at least 4 wavelength samples for FFT processing")
    diff = np.diff(wavelengths_nm)
    if not np.allclose(diff, diff[0], rtol=1e-4, atol=1e-6):
        raise ValueError("wavelength spacing must be uniform for Fourier analysis")
    delta_wav = diff[0]
    reshaped = np.moveaxis(cube, config.wavelength_axis, 0)
    flattened = reshaped.reshape(steps, -1)
    return flattened, delta_wav


def compute_mpi(
    cube: np.ndarray,
    wavelengths_nm: np.ndarray,
    config: S2AnalysisConfig | None = None,
) -> S2AnalysisResult:
    """Replicate the legacy MPI computation using FFT/DGD filtering."""
    config = config or S2AnalysisConfig()
    filters = config.filters
    meas, delta_wav = _prepare_cube(cube, wavelengths_nm, config)
    steps, pixels = meas.shape
    meas_offset = float(np.min(meas))
    meas_shifted = meas - meas_offset

    ft = np.fft.rfft(meas_shifted, axis=0)
    freq = np.fft.rfftfreq(steps, d=delta_wav)
    wav_start = wavelengths_nm[0]
    wav_end = wavelengths_nm[-1]
    dgd_ps = 1e3 * freq * (wav_end + wav_start) ** 2 / (4 * SPEED_OF_LIGHT)

    i_dc = int(np.abs(dgd_ps - filters.dc_end_ps).argmin())
    i_hom_start = int(np.abs(dgd_ps - filters.hom_start_ps).argmin())
    i_hom_end = int(np.abs(dgd_ps - filters.hom_end_ps).argmin())

    dc_filter = _bandpass(ft.shape[0], 0, i_dc)[:, None]
    fundamental_fft = ft * dc_filter
    fundamental = np.fft.irfft(fundamental_fft, n=steps, axis=0)
    avg_fundamental = simpson(fundamental, axis=0) / steps
    avg_fundamental += meas_offset

    safe = np.clip(fundamental, config.min_intensity, None)
    j_term = (meas_shifted - fundamental) / (2 * np.sqrt(safe))
    j_fft = np.fft.rfft(j_term, axis=0)
    dgd_spectrum = np.sum(np.abs(ft), axis=1)
    dist_filter = _bandpass(j_fft.shape[0], i_hom_start, i_hom_end)[:, None]
    j_filtered = np.fft.irfft(j_fft * dist_filter, n=steps, axis=0)

    spatial_shape = np.moveaxis(cube, config.wavelength_axis, 0).shape[1:]
    dominant_map = avg_fundamental.reshape(spatial_shape)
    dominant_map = np.clip(dominant_map, config.min_intensity, None)
    hom_map = (2 * simpson(j_filtered**2, axis=0) / steps).reshape(spatial_shape)

    total_dom = _simps2d(dominant_map)
    total_hom = _simps2d(hom_map)
    eps = 1e-18
    mpi_db = 10 * np.log10(max(total_hom, eps) / max(total_dom, eps))

    dominant_vs_wl = np.sum(fundamental, axis=1)
    hom_vs_wl = 2 * np.sum(j_filtered**2, axis=1)

    hom_band = slice(i_hom_start, i_hom_end + 1)
    hom_band_fft = ft[hom_band]
    band_power = np.sum(np.abs(hom_band_fft), axis=1)
    peak_rel = int(np.argmax(band_power))
    peak_idx = hom_band.start + peak_rel
    hom_phase_map = np.angle(ft[peak_idx]).reshape(spatial_shape)
    hom_peak_dgd_ps = float(dgd_ps[peak_idx])

    return S2AnalysisResult(
        wavelengths_nm=np.asarray(wavelengths_nm, dtype=float),
        dgd_axis_ps=dgd_ps,
        dgd_spectrum=dgd_spectrum,
        dominant_map=dominant_map,
        hom_map=hom_map,
        dominant_vs_wavelength=dominant_vs_wl,
        hom_vs_wavelength=hom_vs_wl,
        hom_peak_dgd_ps=hom_peak_dgd_ps,
        hom_phase_map=hom_phase_map,
        mpi_db=mpi_db,
        dominant_power=total_dom,
        hom_power=total_hom,
    )


def load_scan(
    path: str | Path, fmt: Literal["auto", "npz", "legacy"] = "auto"
) -> Tuple[np.ndarray, np.ndarray]:
    """Load either the new .npz format or the legacy GUI .npy layout."""
    path = Path(path)
    if fmt == "auto":
        fmt = "npz" if path.suffix.lower() == ".npz" else "legacy"

    if fmt == "npz":
        data = np.load(path, allow_pickle=True)
        wavelengths = np.asarray(data["wavelengths"], dtype=float)
        cube = np.asarray(data["cube"], dtype=float)
        return wavelengths, cube
    if fmt == "legacy":
        data = np.load(path, allow_pickle=True)
        wavelengths = np.asarray(data[:, 0], dtype=float)
        frames = np.asarray(data[:, 1:], dtype=float)
        pixels = frames.shape[1]
        side = int(round(np.sqrt(pixels)))
        if side * side != pixels:
            raise ValueError("legacy file does not contain square images")
        cube = frames.reshape(len(wavelengths), side, side)
        return wavelengths, cube
    raise ValueError(f"Unknown format '{fmt}'")
