"""Case- and dataset-level evaluation against reference masks."""

from __future__ import annotations

import csv
import json
from typing import Dict, Iterable, List, Optional

import numpy as np

from .io import Volume, load_volume
from .metrics import compute_all_metrics
from .segmentation import Segmenter

_AGG_KEYS = ["dice", "iou", "sensitivity", "precision", "hd95_mm", "assd_mm",
             "abs_volume_diff_mm3", "lesion_recall", "lesion_precision", "lesion_f1"]


def evaluate_case(pred_mask: np.ndarray, ref_mask: np.ndarray, spacing=(1.0, 1.0, 1.0)) -> Dict[str, float]:
    return compute_all_metrics(pred_mask, ref_mask, spacing)


def evaluate_dataset(cases: Iterable[dict], segmenter: Segmenter,
                     output_csv: Optional[str] = None, output_json: Optional[str] = None) -> dict:
    """Each case: {"id", "image": path|Volume, "reference": path|Volume|ndarray}."""
    rows: List[dict] = []
    for c in cases:
        img = c["image"] if isinstance(c["image"], Volume) else load_volume(c["image"])
        ref = c["reference"]
        ref = ref.data if isinstance(ref, Volume) else (ref if isinstance(ref, np.ndarray) else load_volume(ref).data)
        pred = segmenter.segment(img)
        rows.append({"id": c.get("id", img.path), **evaluate_case(pred, ref > 0.5, img.spacing)})

    summary: Dict[str, dict] = {}
    for k in _AGG_KEYS:
        v = np.array([r[k] for r in rows if np.isfinite(r[k])], dtype=float)
        summary[k] = ({"mean": float(v.mean()), "std": float(v.std()),
                       "median": float(np.median(v)), "n": int(v.size)} if v.size else {})
    result = {"n_cases": len(rows), "summary": summary, "per_case": rows}

    if output_csv and rows:
        with open(output_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    if output_json:
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2)
    return result
