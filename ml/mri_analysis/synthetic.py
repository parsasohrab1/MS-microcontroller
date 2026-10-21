"""Synthetic FLAIR-like phantom with known lesions (for tests and demos)."""

from __future__ import annotations

import numpy as np

from .io import Volume


def make_phantom(shape=(64, 64, 48), n_lesions=6, noise=0.03, seed=0, spacing=(1.0, 1.0, 1.0)):
    rng = np.random.default_rng(seed)
    zz, yy, xx = np.meshgrid(*[np.linspace(-1, 1, s) for s in shape], indexing="ij")
    brain = (xx**2 / 0.8**2 + yy**2 / 0.85**2 + zz**2 / 0.8**2) < 1.0
    img = np.where(brain, 0.5, 0.0).astype(np.float32)
    ref = np.zeros(shape, dtype=bool)
    inner = (xx**2 / 0.5**2 + yy**2 / 0.55**2 + zz**2 / 0.5**2) < 1.0
    idx = np.argwhere(inner)
    gz, gy, gx = np.indices(shape)
    for _ in range(n_lesions):
        c = idx[rng.integers(len(idx))]
        r = rng.integers(2, 4)
        ref |= ((gz - c[0])**2 + (gy - c[1])**2 + (gx - c[2])**2) <= r * r
    ref &= brain
    img[ref] = 0.95
    bias = 1.0 + 0.15 * xx
    img = img * bias + rng.normal(0, noise, shape)
    img = np.abs(img).astype(np.float32)
    return Volume(img, spacing), ref
