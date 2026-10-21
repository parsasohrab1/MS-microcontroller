"""Segmentation losses."""

from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F


class DiceBCELoss(nn.Module):
    """Soft Dice + weighted BCE; robust to the heavy class imbalance of MS lesions."""

    def __init__(
        self,
        dice_weight: float = 1.0,
        bce_weight: float = 1.0,
        pos_weight: float = 1.0,
        eps: float = 1e-5,
    ):
        super().__init__()
        self.dw, self.bw, self.eps = dice_weight, bce_weight, eps
        self.register_buffer("pos_weight", torch.tensor(float(pos_weight)))

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        target = target.float()
        bce = F.binary_cross_entropy_with_logits(
            logits, target, pos_weight=self.pos_weight
        )
        p = torch.sigmoid(logits)
        dims = tuple(range(1, p.ndim))
        inter = (p * target).sum(dims)
        denom = p.sum(dims) + target.sum(dims)
        dice = 1.0 - (2 * inter + self.eps) / (denom + self.eps)
        return self.dw * dice.mean() + self.bw * bce
