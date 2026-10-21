"""Lesion segmentation back-ends.

ThresholdSegmenter is a dependency-light classical baseline (FLAIR hyperintensity).
CallableSegmenter / ONNXSegmenter plug in trained models (e.g. nnU-Net exported
to ONNX) behind the same interface.
"""

from __future__ import annotations

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


class ONNXSegmenter(CallableSegmenter):
    """ONNX model taking (1,1,D,H,W) float32 and returning a lesion probability map."""

    def __init__(
        self,
        model_path: str,
        threshold: float = 0.5,
        min_volume_mm3: float = 0.0,
        providers: Optional[list] = None,
    ):
        try:
            import onnxruntime as ort
        except ImportError as e:  # pragma: no cover
            raise ImportError("onnxruntime is required for ONNXSegmenter") from e
        sess = ort.InferenceSession(
            model_path, providers=providers or ["CPUExecutionProvider"]
        )
        name = sess.get_inputs()[0].name

        def fn(z: np.ndarray) -> np.ndarray:
            out = sess.run(None, {name: z[None, None].astype(np.float32)})[0]
            return np.squeeze(out)

        super().__init__(fn, threshold, min_volume_mm3)
