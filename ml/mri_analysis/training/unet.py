"""Compact 3D U-Net (instance norm, transposed-conv upsampling; ONNX friendly)."""

from __future__ import annotations

from typing import List

import torch
from torch import nn
import torch.nn.functional as F


def _block(cin: int, cout: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv3d(cin, cout, 3, padding=1, bias=False),
        nn.InstanceNorm3d(cout, affine=True),
        nn.LeakyReLU(0.01, inplace=True),
        nn.Conv3d(cout, cout, 3, padding=1, bias=False),
        nn.InstanceNorm3d(cout, affine=True),
        nn.LeakyReLU(0.01, inplace=True),
    )


class UNet3D(nn.Module):
    """Input (B, in_ch, D, H, W) -> logits (B, 1, D, H, W).

    Spatial dims are padded internally to a multiple of 2**depth and cropped
    back, so arbitrary volume sizes are accepted.
    """

    def __init__(self, in_channels: int = 1, base: int = 16, depth: int = 3):
        super().__init__()
        self.depth = depth
        chans = [base * 2**i for i in range(depth + 1)]
        self.enc = nn.ModuleList()
        cin = in_channels
        for c in chans[:-1]:
            self.enc.append(_block(cin, c))
            cin = c
        self.bottleneck = _block(chans[-2], chans[-1])
        self.up = nn.ModuleList()
        self.dec = nn.ModuleList()
        for i in range(depth, 0, -1):
            self.up.append(nn.ConvTranspose3d(chans[i], chans[i - 1], 2, stride=2))
            self.dec.append(_block(chans[i - 1] * 2, chans[i - 1]))
        self.head = nn.Conv3d(chans[0], 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        m = 2**self.depth
        d, h, w = x.shape[-3:]
        pd, ph, pw = (-d) % m, (-h) % m, (-w) % m
        x = F.pad(x, (0, pw, 0, ph, 0, pd), mode="replicate")
        skips: List[torch.Tensor] = []
        for enc in self.enc:
            x = enc(x)
            skips.append(x)
            x = F.max_pool3d(x, 2)
        x = self.bottleneck(x)
        for up, dec in zip(self.up, self.dec):
            x = up(x)
            x = dec(torch.cat([x, skips.pop()], dim=1))
        x = self.head(x)
        return x[..., :d, :h, :w]
