"""Volume I/O. NIfTI via nibabel; .npy/.npz supported for lightweight use."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Tuple

import numpy as np


@dataclass
class Volume:
    data: np.ndarray
    spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # mm
    affine: np.ndarray = field(default_factory=lambda: np.eye(4))
    path: str = ""

    @property
    def voxel_volume_mm3(self) -> float:
        return float(np.prod(self.spacing))

    @property
    def shape(self) -> Tuple[int, ...]:
        return tuple(self.data.shape)


def load_volume(path: str) -> Volume:
    """Load a 3D volume from .nii/.nii.gz/.npy/.npz."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    lower = path.lower()
    if lower.endswith((".nii", ".nii.gz")):
        try:
            import nibabel as nib
        except ImportError as e:  # pragma: no cover
            raise ImportError("nibabel is required to read NIfTI files") from e
        img = nib.load(path)
        data = np.asarray(img.dataobj, dtype=np.float32)
        spacing = tuple(float(z) for z in img.header.get_zooms()[:3])
        return Volume(data, spacing, np.asarray(img.affine), path)
    if lower.endswith(".npy"):
        data = np.load(path).astype(np.float32)
        return Volume(data, path=path)
    if lower.endswith(".npz"):
        with np.load(path) as z:
            data = z["data"].astype(np.float32)
            spacing = tuple(float(s) for s in z["spacing"]) if "spacing" in z else (1.0,) * 3
        return Volume(data, spacing, path=path)
    raise ValueError(f"Unsupported file format: {path}")


def save_volume(vol: Volume, path: str) -> None:
    lower = path.lower()
    if lower.endswith((".nii", ".nii.gz")):
        import nibabel as nib
        nib.save(nib.Nifti1Image(vol.data, vol.affine), path)
    elif lower.endswith(".npz"):
        np.savez_compressed(path, data=vol.data, spacing=np.asarray(vol.spacing))
    elif lower.endswith(".npy"):
        np.save(path, vol.data)
    else:
        raise ValueError(f"Unsupported file format: {path}")
