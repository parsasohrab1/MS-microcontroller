"""Image quality control for MRI volumes."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List

import numpy as np
from scipy import ndimage

from .io import Volume
from .preprocessing import brain_mask

DEFAULT_THRESHOLDS = {
    "min_snr": 10.0,
    "max_saturation_fraction": 0.01,
    "max_anisotropy": 6.0,
    "min_dim": 16,
    "max_ghosting_ratio": 0.5,
    "min_mask_fraction": 0.02,
}


@dataclass
class QCReport:
    passed: bool
    metrics: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def run_qc(vol: Volume, thresholds: dict | None = None) -> QCReport:
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    d = vol.data
    issues: List[str] = []
    warnings: List[str] = []
    m: Dict[str, float] = {}

    if d.ndim != 3:
        return QCReport(False, {}, [f"expected 3D volume, got {d.ndim}D"])
    if not np.isfinite(d).all():
        return QCReport(False, {}, ["volume contains NaN/Inf"])
    if min(d.shape) < th["min_dim"]:
        issues.append(f"volume too small: {d.shape}")
    if float(d.max() - d.min()) == 0.0:
        return QCReport(False, {"dynamic_range": 0.0}, issues + ["constant image"])

    sp = np.asarray(vol.spacing, dtype=float)
    if (sp <= 0).any():
        issues.append(f"invalid voxel spacing {tuple(sp)}")
    else:
        m["anisotropy"] = float(sp.max() / sp.min())
        if m["anisotropy"] > th["max_anisotropy"]:
            warnings.append(f"highly anisotropic voxels ({m['anisotropy']:.1f}:1)")

    mask = brain_mask(d)
    m["mask_fraction"] = float(mask.mean())
    if m["mask_fraction"] < th["min_mask_fraction"]:
        issues.append("foreground mask nearly empty")

    fg, bg = d[mask], d[~mask]
    if fg.size and bg.size > 100:
        # Rician background: sigma ~= std / 0.655
        sigma = float(bg.std()) / 0.655
        m["snr"] = float(fg.mean() / sigma) if sigma > 0 else float("inf")
        if m["snr"] < th["min_snr"]:
            issues.append(f"low SNR ({m['snr']:.1f} < {th['min_snr']})")
        # Ghosting/ringing proxy: background structure relative to foreground
        m["ghosting_ratio"] = float(np.percentile(bg, 99) / (fg.mean() + 1e-9))
        if m["ghosting_ratio"] > th["max_ghosting_ratio"]:
            warnings.append("possible ghosting/artifact in background")
    else:
        warnings.append("no background voxels; SNR not estimated")

    m["saturation_fraction"] = float((d >= d.max() * 0.999).mean())
    if m["saturation_fraction"] > th["max_saturation_fraction"]:
        issues.append("intensity saturation/clipping")

    # Motion/blur proxy: mean gradient magnitude inside mask (normalised)
    g = ndimage.gaussian_gradient_magnitude(d.astype(np.float32), 1.0)
    m["sharpness"] = float(g[mask].mean() / (fg.mean() + 1e-9)) if fg.size else 0.0
    m["intensity_mean"] = float(fg.mean()) if fg.size else 0.0
    m["intensity_std"] = float(fg.std()) if fg.size else 0.0

    return QCReport(not issues, m, issues, warnings)
