"""Sliding-window inference and a Segmenter backed by a trained checkpoint."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import torch

from ..io import Volume
from ..preprocessing import brain_mask, normalize
from ..segmentation import Segmenter, remove_small_lesions
from .unet import UNet3D


def _starts(dim: int, p: int, stride: int):
    if dim <= p:
        return [0]
    s = list(range(0, dim - p + 1, stride))
    if s[-1] != dim - p:
        s.append(dim - p)
    return s


@torch.no_grad()
def sliding_window_predict(
    model: torch.nn.Module,
    image: np.ndarray,
    patch=(64, 64, 64),
    overlap: float = 0.5,
    device: str = "cpu",
) -> np.ndarray:
    """Probability map for a normalised 3D image (overlapping windows averaged)."""
    model.eval()
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
                t = torch.from_numpy(img[sl].astype(np.float32))[None, None].to(device)
                acc[sl] += torch.sigmoid(model(t))[0, 0].cpu().numpy()
                cnt[sl] += 1
    out = acc / np.maximum(cnt, 1)
    return out[: image.shape[0], : image.shape[1], : image.shape[2]]


def load_checkpoint(path: str, device: str = "cpu") -> Tuple[UNet3D, dict]:
    ck = torch.load(path, map_location=device, weights_only=False)
    cfg = ck["model_config"]
    model = UNet3D(**cfg).to(device)
    model.load_state_dict(ck["state_dict"])
    model.eval()
    return model, ck


class TorchSegmenter(Segmenter):
    """Segmenter using a checkpoint written by `trainer.train`."""

    def __init__(
        self,
        checkpoint: str,
        threshold: Optional[float] = None,
        overlap: float = 0.5,
        min_volume_mm3: float = 0.0,
        device: str = "cpu",
    ):
        self.model, ck = load_checkpoint(checkpoint, device)
        self.patch = tuple(ck["patch_size"])
        self.threshold = ck.get("threshold", 0.5) if threshold is None else threshold
        self.overlap, self.min_volume_mm3, self.device = overlap, min_volume_mm3, device

    def probability(self, vol: Volume) -> np.ndarray:
        z = normalize(vol.data, brain_mask(vol.data))
        return sliding_window_predict(
            self.model, z, self.patch, self.overlap, self.device
        )

    def segment(self, vol: Volume) -> np.ndarray:
        seg = self.probability(vol) > self.threshold
        if self.min_volume_mm3:
            seg = remove_small_lesions(seg, vol.spacing, self.min_volume_mm3)
        return seg
