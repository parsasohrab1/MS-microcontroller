"""End-to-end single-case analysis: load -> QC -> segment -> (optional) evaluate."""

from __future__ import annotations

from typing import Optional

import numpy as np

from .evaluation import evaluate_case
from .io import Volume, load_volume, save_volume
from .qc import run_qc
from .segmentation import Segmenter, ThresholdSegmenter


def analyze_case(
    image_path: str,
    reference_path: Optional[str] = None,
    segmenter: Optional[Segmenter] = None,
    output_mask_path: Optional[str] = None,
    qc_thresholds: Optional[dict] = None,
    fail_on_qc: bool = False,
) -> dict:
    vol = load_volume(image_path)
    qc = run_qc(vol, qc_thresholds)
    if not qc.passed and fail_on_qc:
        return {"image": image_path, "qc": qc.to_dict(), "segmented": False}

    seg = (segmenter or ThresholdSegmenter()).segment(vol)
    result = {
        "image": image_path,
        "qc": qc.to_dict(),
        "segmented": True,
        "lesion_volume_mm3": float(seg.sum() * vol.voxel_volume_mm3),
    }
    if output_mask_path:
        save_volume(
            Volume(seg.astype(np.uint8), vol.spacing, vol.affine), output_mask_path
        )
    if reference_path:
        ref = load_volume(reference_path).data > 0.5
        result["metrics"] = evaluate_case(seg, ref, vol.spacing)
    return result
