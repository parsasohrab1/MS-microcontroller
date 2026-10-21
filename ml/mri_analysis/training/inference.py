"""Sliding-window inference and a Segmenter backed by a trained checkpoint."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import torch

from ..io import Volume
from ..preprocessing import brain_mask, normalize
from ..segmentation import Segmenter, remove_small_lesions, sliding_window_apply
from .unet import UNet3D


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

    def run(x: np.ndarray) -> np.ndarray:
        t = torch.from_numpy(x)[None, None].to(device)
        return torch.sigmoid(model(t))[0, 0].cpu().numpy()

    return sliding_window_apply(run, image, patch, overlap)


def load_checkpoint(path: str, device: str = "cpu") -> Tuple[UNet3D, dict]:
    ck = torch.load(path, map_location=device, weights_only=True)
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
