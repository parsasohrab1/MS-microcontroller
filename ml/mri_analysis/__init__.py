"""Standalone MRI analysis module for MS lesion segmentation.

Pipeline: load -> QC -> preprocess -> segment -> evaluate (Dice etc.).
"""

from .io import Volume, load_volume, save_volume
from .qc import QCReport, run_qc
from .preprocessing import brain_mask, correct_bias, normalize, resample_isotropic
from .segmentation import (
    Segmenter,
    ThresholdSegmenter,
    CallableSegmenter,
    ONNXSegmenter,
)
from .metrics import (
    dice,
    iou,
    sensitivity,
    precision,
    volume_difference,
    surface_distances,
    lesion_wise_metrics,
    compute_all_metrics,
)
from .evaluation import evaluate_case, evaluate_dataset
from .pipeline import analyze_case

__all__ = [
    "Volume", "load_volume", "save_volume", "QCReport", "run_qc",
    "brain_mask", "correct_bias", "normalize", "resample_isotropic",
    "Segmenter", "ThresholdSegmenter", "CallableSegmenter", "ONNXSegmenter",
    "dice", "iou", "sensitivity", "precision", "volume_difference",
    "surface_distances", "lesion_wise_metrics", "compute_all_metrics",
    "evaluate_case", "evaluate_dataset", "analyze_case",
]
