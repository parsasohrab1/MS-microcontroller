"""Segmentation evaluation metrics against reference masks."""

from __future__ import annotations

from typing import Dict

import numpy as np
from scipy import ndimage

_S3 = np.ones((3, 3, 3))


def _b(x) -> np.ndarray:
    return np.asarray(x).astype(bool)


def dice(pred, ref) -> float:
    p, r = _b(pred), _b(ref)
    s = p.sum() + r.sum()
    return 1.0 if s == 0 else float(2.0 * (p & r).sum() / s)


def iou(pred, ref) -> float:
    p, r = _b(pred), _b(ref)
    u = (p | r).sum()
    return 1.0 if u == 0 else float((p & r).sum() / u)


def sensitivity(pred, ref) -> float:
    p, r = _b(pred), _b(ref)
    return 1.0 if r.sum() == 0 else float((p & r).sum() / r.sum())


def precision(pred, ref) -> float:
    p, r = _b(pred), _b(ref)
    return (
        1.0
        if p.sum() == 0 and r.sum() == 0
        else (0.0 if p.sum() == 0 else float((p & r).sum() / p.sum()))
    )


def volume_difference(pred, ref, voxel_volume_mm3: float = 1.0) -> Dict[str, float]:
    pv, rv = _b(pred).sum() * voxel_volume_mm3, _b(ref).sum() * voxel_volume_mm3
    return {
        "pred_volume_mm3": float(pv),
        "ref_volume_mm3": float(rv),
        "abs_volume_diff_mm3": float(abs(pv - rv)),
        "rel_volume_diff": (
            float((pv - rv) / rv) if rv > 0 else (0.0 if pv == 0 else float("inf"))
        ),
    }


def _surface(mask: np.ndarray) -> np.ndarray:
    return mask & ~ndimage.binary_erosion(
        mask, structure=ndimage.generate_binary_structure(3, 1)
    )


def surface_distances(pred, ref, spacing=(1.0, 1.0, 1.0)) -> Dict[str, float]:
    """Symmetric surface distances (mm): HD95, Hausdorff, ASSD. NaN if either empty."""
    p, r = _b(pred), _b(ref)
    if not p.any() or not r.any():
        return {"hd95_mm": float("nan"), "hd_mm": float("nan"), "assd_mm": float("nan")}
    sp, sr = _surface(p), _surface(r)
    d_to_r = ndimage.distance_transform_edt(~sr, sampling=spacing)[sp]
    d_to_p = ndimage.distance_transform_edt(~sp, sampling=spacing)[sr]
    both = np.concatenate([d_to_r, d_to_p])
    return {
        "hd95_mm": float(np.percentile(both, 95)),
        "hd_mm": float(both.max()),
        "assd_mm": float(both.mean()),
    }


def lesion_wise_metrics(pred, ref, min_overlap_voxels: int = 1) -> Dict[str, float]:
    """Lesion-wise detection: a reference lesion is detected if any predicted
    component overlaps it; a predicted component is a TP if it overlaps any
    reference lesion, otherwise a false positive."""
    p, r = _b(pred), _b(ref)
    pl, pn = ndimage.label(p, structure=_S3)
    rl, rn = ndimage.label(r, structure=_S3)
    tp_ref = sum(
        1 for i in range(1, rn + 1) if (p & (rl == i)).sum() >= min_overlap_voxels
    )
    tp_pred = sum(
        1 for i in range(1, pn + 1) if (r & (pl == i)).sum() >= min_overlap_voxels
    )
    fn, fp = rn - tp_ref, pn - tp_pred
    recall = 1.0 if rn == 0 else tp_ref / rn
    prec = 1.0 if pn == 0 and rn == 0 else (0.0 if pn == 0 else tp_pred / pn)
    f1 = (
        1.0
        if (pn == 0 and rn == 0)
        else (0.0 if recall + prec == 0 else 2 * recall * prec / (recall + prec))
    )
    return {
        "n_ref_lesions": rn,
        "n_pred_lesions": pn,
        "lesion_tp": tp_ref,
        "lesion_fn": fn,
        "lesion_fp": fp,
        "lesion_recall": float(recall),
        "lesion_precision": float(prec),
        "lesion_f1": float(f1),
    }


def compute_all_metrics(pred, ref, spacing=(1.0, 1.0, 1.0)) -> Dict[str, float]:
    p, r = _b(pred), _b(ref)
    if p.shape != r.shape:
        raise ValueError(f"shape mismatch: pred {p.shape} vs ref {r.shape}")
    out = {
        "dice": dice(p, r),
        "iou": iou(p, r),
        "sensitivity": sensitivity(p, r),
        "precision": precision(p, r),
    }
    out.update(volume_difference(p, r, float(np.prod(spacing))))
    out.update(surface_distances(p, r, spacing))
    out.update(lesion_wise_metrics(p, r))
    return out
