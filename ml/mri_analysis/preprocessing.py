"""Preprocessing: masking, bias-field correction, normalisation, resampling."""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def _otsu(x: np.ndarray, bins: int = 256) -> float:
    hist, edges = np.histogram(x, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = w0[-1] - w0
    s0 = np.cumsum(hist * centers)
    mu0 = s0 / np.maximum(w0, 1)
    mu1 = (s0[-1] - s0) / np.maximum(w1, 1)
    between = w0 * w1 * (mu0 - mu1) ** 2
    return float(centers[np.argmax(between)])


def brain_mask(data: np.ndarray) -> np.ndarray:
    """Foreground mask: Otsu threshold, largest component, holes filled."""
    smooth = ndimage.gaussian_filter(data.astype(np.float32), 1.0)
    mask = smooth > _otsu(smooth[smooth > smooth.min()]) * 0.5
    lab, n = ndimage.label(mask)
    if n == 0:
        return mask
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    mask = lab == (int(np.argmax(sizes)) + 1)
    mask = ndimage.binary_closing(mask, iterations=2)
    return ndimage.binary_fill_holes(mask)


def correct_bias(
    data: np.ndarray, mask: np.ndarray | None = None, sigma: float = 8.0
) -> np.ndarray:
    """Simple homomorphic bias correction (masked low-pass in log domain).

    Lightweight stand-in for N4; swap in SimpleITK N4 for production use.
    """
    if mask is None:
        mask = brain_mask(data)
    d = data.astype(np.float32)
    logd = np.log(np.maximum(d, 1e-3))
    w = mask.astype(np.float32)
    num = ndimage.gaussian_filter(logd * w, sigma)
    den = ndimage.gaussian_filter(w, sigma)
    field_ = np.where(den > 1e-3, num / np.maximum(den, 1e-3), 0.0)
    field_ -= field_[mask].mean() if mask.any() else 0.0
    out = np.exp(logd - field_)
    out[~mask] = d[~mask]
    return out


def normalize(data: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    """Z-score normalisation inside the mask (outside set to 0)."""
    if mask is None:
        mask = brain_mask(data)
    vals = data[mask]
    std = vals.std() or 1.0
    out = (data - vals.mean()) / std
    out[~mask] = 0.0
    return out.astype(np.float32)


def resample_isotropic(data: np.ndarray, spacing, target: float = 1.0, order: int = 1):
    """Resample to isotropic voxels; returns (data, new_spacing)."""
    zoom = np.asarray(spacing, dtype=float) / target
    out = ndimage.zoom(data, zoom, order=order)
    return out, (target,) * 3
