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
    """Relative power summary plus intermediate maps and spectra."""

    wavelengths_nm: np.ndarray
    dgd_axis_ps: np.ndarray
    dgd_spectrum: np.ndarray
    dominant_map: np.ndarray
    hom_map: np.ndarray
    dominant_vs_wavelength: np.ndarray
    hom_vs_wavelength: np.ndarray
    hom_peak_dgd_ps: float
    hom_phase_map: np.ndarray
    relative_power_db: float
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
    """Replicate the legacy MPI computation from LGN code using FFT/DGD filtering."""
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
    # avg_fundamental = simpson(fundamental, axis=0) / steps
    avg_fundamental = simpson(fundamental, axis=0)
    avg_fundamental += meas_offset

    safe = np.clip(fundamental, config.min_intensity, None)
    j_term = (meas_shifted - fundamental) / (2 * np.sqrt(safe))
    j_fft = np.fft.rfft(j_term, axis=0)
    dgd_spectrum = np.sum(np.abs(ft), axis=1)
    dist_filter = _bandpass(j_fft.shape[0], i_hom_start, i_hom_end)[:, None]
    j_filtered = np.fft.irfft(j_fft * dist_filter, n=steps, axis=0)

    spatial_shape = np.moveaxis(cube, config.wavelength_axis, 0).shape[1:]
    dominant_map = np.asarray(avg_fundamental).reshape(spatial_shape)
    dominant_map = np.clip(dominant_map, config.min_intensity, None)
    # hom_map = (2 * simpson(j_filtered**2, axis=0) / steps).reshape(spatial_shape)
    hom_map = np.asarray(2 * simpson(j_filtered**2, axis=0)).reshape(spatial_shape)

    total_dom = _simps2d(dominant_map)
    total_hom = _simps2d(hom_map)
    eps = 1e-18
    relative_power_db = 10 * np.log10(max(total_hom, eps) / max(total_dom, eps))

    safe_dom = np.clip(fundamental, config.min_intensity, None)
    # dominant_vs_wl = simpson(safe_dom, axis=1)
    # hom_vs_wl = 2 * simpson(j_filtered**2, axis=1)
    dominant_vs_wl = np.asarray(simpson(safe_dom, axis=1))
    hom_vs_wl = np.asarray(2 * simpson(j_filtered**2, axis=1))

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
        relative_power_db=relative_power_db,
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


def process_scan(
    path: str | Path,
    *,
    fmt: Literal["auto", "npz", "legacy"] = "auto",
    filters: DGDFilters | None = None,
    show_plots: bool = True,
    save_figs: bool = False,
    output_dir: str | Path | None = None,
) -> S2AnalysisResult:
    """Convenience helper replicating the legacy analyzer workflow.

    Args:
        path: Path to a .npz (new) or .npy (legacy) scan file.
        fmt: Force a specific loader; defaults to auto-detection.
        filters: DGD window used for the DC and HOM bands.
        show_plots: When True, open a summary Matplotlib figure.
        save_figs: When True, write individual figures mirroring the legacy GUI
            (FFT spectrum, dominant map, HOM map, HOM phase).
        output_dir: Directory for saved figures (defaults to the scan's parent).
    """

    filters = filters or DGDFilters()
    path = Path(path)
    wavelengths, cube = load_scan(path, fmt=fmt)
    result = compute_mpi(
        cube,
        wavelengths,
        config=S2AnalysisConfig(filters=filters),
    )

    if not (show_plots or save_figs):
        return result

    import matplotlib.pyplot as plt  # Local import to avoid heavy dependency
    from matplotlib.figure import Figure

    def _plot_summary() -> Figure:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        im0 = axes[0, 0].imshow(result.dominant_map, cmap="viridis")
        axes[0, 0].set_title("Dominant mode intensity")
        axes[0, 0].set_xlabel("Pixel")
        axes[0, 0].set_ylabel("Pixel")
        plt.colorbar(im0, ax=axes[0, 0], fraction=0.046, pad=0.04)

        im1 = axes[0, 1].imshow(result.hom_map, cmap="viridis")
        axes[0, 1].set_title(
            f"HOM intensity @ {filters.hom_start_ps:.2f}–{filters.hom_end_ps:.2f} ps",
        )
        axes[0, 1].set_xlabel("Pixel")
        axes[0, 1].set_ylabel("Pixel")
        plt.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04)

        im2 = axes[0, 2].imshow(result.hom_phase_map, cmap="twilight")
        axes[0, 2].set_title(
            f"HOM phase @ {result.hom_peak_dgd_ps:.2f} ps",
        )
        axes[0, 2].set_xlabel("Pixel")
        axes[0, 2].set_ylabel("Pixel")
        plt.colorbar(im2, ax=axes[0, 2], fraction=0.046, pad=0.04)

        dgd_db = 10 * np.log10(np.clip(result.dgd_spectrum, 1e-30, None))
        axes[1, 0].plot(result.dgd_axis_ps, dgd_db)
        axes[1, 0].axvspan(
            0,
            filters.dc_end_ps,
            color="red",
            alpha=0.15,
            label="DC band",
        )
        axes[1, 0].axvspan(
            filters.hom_start_ps,
            filters.hom_end_ps,
            color="green",
            alpha=0.15,
            label="HOM band",
        )
        axes[1, 0].set_xlabel("DGD (ps)")
        axes[1, 0].set_ylabel("FFT amplitude (dB)")
        axes[1, 0].set_title("DGD spectrum")
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].legend()

        axes[1, 1].plot(
            result.wavelengths_nm,
            result.dominant_vs_wavelength,
            label="Dominant",
        )
        axes[1, 1].plot(
            result.wavelengths_nm,
            result.hom_vs_wavelength,
            label="HOM",
        )
        axes[1, 1].set_title("Integrated power vs wavelength")
        axes[1, 1].set_xlabel("Wavelength (nm)")
        axes[1, 1].set_ylabel("Integrated counts")
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].legend()

        ratio = result.hom_vs_wavelength / np.clip(
            result.dominant_vs_wavelength,
            1e-18,
            None,
        )
        axes[1, 2].plot(
            result.wavelengths_nm,
            10 * np.log10(np.clip(ratio, 1e-18, None)),
        )
        axes[1, 2].set_title("HOM/Dominant (dB)")
        axes[1, 2].set_xlabel("Wavelength (nm)")
        axes[1, 2].set_ylabel("dB")
        axes[1, 2].grid(True, alpha=0.3)

        fig.suptitle(f"Relative power {result.relative_power_db:.2f} dB")
        fig.tight_layout()
        return fig

    def _ensure_dir() -> Path:
        directory = Path(output_dir) if output_dir else path.parent
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _save_fft(fig_dir: Path) -> None:
        fig, ax = plt.subplots(figsize=(6, 4))
        dgd_db = 10 * np.log10(np.clip(result.dgd_spectrum[1:], 1e-30, None))
        ax.plot(result.dgd_axis_ps[1:], dgd_db)
        ax.set(
            xlabel="DGD [ps]",
            ylabel="FFT Amplitude [dB]",
            title="FFT amplitude spectrum",
        )
        ax.grid(True)
        fig.savefig(fig_dir / f"FFT Amp {path.stem}.png", dpi=150)
        plt.close(fig)

    def _save_map(data: np.ndarray, title: str, fname: Path) -> None:
        fig, ax = plt.subplots(figsize=(5, 5))
        cmap = ax.pcolormesh(data, cmap="viridis")
        ax.set_xlabel("Pixel")
        ax.set_ylabel("Pixel")
        ax.set_title(title)
        fig.colorbar(cmap, ax=ax, fraction=0.046, pad=0.04)
        fig.savefig(fname, dpi=150)
        plt.close(fig)

    def _save_hom_phase(fig_dir: Path) -> None:
        fig, ax = plt.subplots(figsize=(5, 5))
        cmap = ax.pcolormesh(result.hom_phase_map, cmap="twilight")
        ax.set_xlabel("Pixel")
        ax.set_ylabel("Pixel")
        ax.set_title(f"HOM phase. DGD = {result.hom_peak_dgd_ps:.2f} ps")
        fig.colorbar(cmap, ax=ax, fraction=0.046, pad=0.04)
        fig.savefig(fig_dir / f"HOM phase distributed {path.stem}.png", dpi=150)
        plt.close(fig)

    if save_figs:
        out_dir = _ensure_dir()
        summary_fig = _plot_summary()
        summary_fig.savefig(out_dir / f"Summary {path.stem}.png", dpi=150)
        plt.close(summary_fig)
        _save_fft(out_dir)
        _save_map(
            result.dominant_map,
            "Dominant",
            out_dir / f"Dominant {path.stem}.png",
        )
        _save_map(
            result.hom_map,
            (
                "HOM amplitude. "
                f"{filters.hom_start_ps:.2f}–{filters.hom_end_ps:.2f} ps\n"
                f"Rel. power = {result.relative_power_db:.1f} dB"
            ),
            out_dir / f"HOM amp distributed {path.stem}.png",
        )
        _save_hom_phase(out_dir)

    if show_plots:
        fig = _plot_summary()
        fig.show()

    return result
