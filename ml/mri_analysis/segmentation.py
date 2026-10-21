"""Lesion segmentation back-ends.

ThresholdSegmenter is a dependency-light classical baseline (FLAIR hyperintensity).
CallableSegmenter / ONNXSegmenter plug in trained models (e.g. nnU-Net exported
to ONNX) behind the same interface.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Callable, Optional

import numpy as np
from scipy import ndimage

from .io import Volume
from .preprocessing import brain_mask, correct_bias, normalize


class Segmenter(ABC):
    @abstractmethod
    def segment(self, vol: Volume) -> np.ndarray:
        """Return a binary lesion mask with the same shape as vol.data."""


def remove_small_lesions(
    mask: np.ndarray, spacing, min_volume_mm3: float
) -> np.ndarray:
    lab, n = ndimage.label(mask, structure=np.ones((3, 3, 3)))
    if n == 0:
        return mask.astype(bool)
    vox = float(np.prod(spacing))
    sizes = ndimage.sum(mask, lab, range(1, n + 1)) * vox
    keep = np.concatenate([[False], sizes >= min_volume_mm3])
    return keep[lab]


class ThresholdSegmenter(Segmenter):
    """Hyperintensity thresholding on a FLAIR volume (z-score > k)."""

    def __init__(
        self, k: float = 1.5, min_volume_mm3: float = 3.0, bias_correct: bool = True
    ):
        self.k, self.min_volume_mm3, self.bias_correct = k, min_volume_mm3, bias_correct

    def segment(self, vol: Volume) -> np.ndarray:
        mask = brain_mask(vol.data)
        d = correct_bias(vol.data, mask) if self.bias_correct else vol.data
        z = normalize(d, mask)
        # erode mask to avoid cortical/CSF-boundary partial-volume false positives
        inner = ndimage.binary_erosion(mask, iterations=2)
        seg = (z > self.k) & inner
        seg = ndimage.binary_opening(seg)
        return remove_small_lesions(seg, vol.spacing, self.min_volume_mm3)


class CallableSegmenter(Segmenter):
    """Wrap any function (e.g. a torch/TF model) mapping a normalised volume to
    a probability map or label volume."""

    def __init__(
        self,
        fn: Callable[[np.ndarray], np.ndarray],
        threshold: float = 0.5,
        min_volume_mm3: float = 0.0,
    ):
        self.fn, self.threshold, self.min_volume_mm3 = fn, threshold, min_volume_mm3

    def segment(self, vol: Volume) -> np.ndarray:
        z = normalize(vol.data)
        out = np.asarray(self.fn(z))
        if out.shape != vol.data.shape:
            raise ValueError(
                f"model output shape {out.shape} != input {vol.data.shape}"
            )
        seg = out > self.threshold
        return (
            remove_small_lesions(seg, vol.spacing, self.min_volume_mm3)
            if self.min_volume_mm3
            else seg
        )


def _starts(dim: int, p: int, stride: int) -> list:
    if dim <= p:
        return [0]
    s = list(range(0, dim - p + 1, stride))
    if s[-1] != dim - p:
        s.append(dim - p)
    return s


def sliding_window_apply(
    fn: Callable[[np.ndarray], np.ndarray],
    image: np.ndarray,
    patch,
    overlap: float = 0.5,
) -> np.ndarray:
    """Apply `fn` (patch -> probability patch, same shape) over overlapping windows
    and average. Matches how the training pipeline's models are evaluated."""
    pad = [max(0, p - s) for p, s in zip(patch, image.shape)]
    img = np.pad(image, [(0, q) for q in pad], mode="edge") if any(pad) else image
    stride = [max(1, int(p * (1 - overlap))) for p in patch]
    acc = np.zeros(img.shape, np.float32)
    cnt = np.zeros(img.shape, np.float32)
    for z in _starts(img.shape[0], patch[0], stride[0]):
        for y in _starts(img.shape[1], patch[1], stride[1]):
            for x in _starts(img.shape[2], patch[2], stride[2]):
                sl = (
                    slice(z, z + patch[0]),
                    slice(y, y + patch[1]),
                    slice(x, x + patch[2]),
                )
                acc[sl] += fn(img[sl].astype(np.float32))
                cnt[sl] += 1
    out = acc / np.maximum(cnt, 1)
    return out[: image.shape[0], : image.shape[1], : image.shape[2]]


class ONNXSegmenter(CallableSegmenter):
    """ONNX model taking (1,1,D,H,W) float32 and returning a lesion probability map.

    Models from the training pipeline use instance norm, so they must be run on
    patches like in training: `patch_size`/`threshold` are read from the
    `<model>.json` sidecar written by the exporter unless given explicitly.
    With no patch size the whole volume is fed in one pass.
    """

    def __init__(
        self,
        model_path: str,
        threshold: Optional[float] = None,
        min_volume_mm3: float = 0.0,
        providers: Optional[list] = None,
        patch_size: Optional[tuple] = None,
        overlap: float = 0.5,
    ):
        try:
            import onnxruntime as ort
        except ImportError as e:  # pragma: no cover
            raise ImportError("onnxruntime is required for ONNXSegmenter") from e
        meta: dict = {}
        if os.path.exists(model_path + ".json"):
            with open(model_path + ".json") as f:
                meta = json.load(f)
        if patch_size is None and meta.get("patch_size"):
            patch_size = tuple(meta["patch_size"])
        if threshold is None:
            threshold = float(meta.get("threshold", 0.5))
        sess = ort.InferenceSession(
            model_path, providers=providers or ["CPUExecutionProvider"]
        )
        name = sess.get_inputs()[0].name

        def run(z: np.ndarray) -> np.ndarray:
            out = sess.run(None, {name: z[None, None].astype(np.float32)})[0]
            return np.squeeze(out)

        def fn(z: np.ndarray) -> np.ndarray:
            if patch_size is None:
                return run(z)
            return sliding_window_apply(run, z, patch_size, overlap)

        super().__init__(fn, threshold, min_volume_mm3)
