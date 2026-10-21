"""Datasets: manifest loading, subject-level splits, patch sampling, augmentation."""

from __future__ import annotations

import csv
import json
import os
from typing import Dict, List, Sequence, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

from ..io import Volume, load_volume, save_volume
from ..preprocessing import brain_mask, normalize


def load_manifest(path: str) -> List[Dict[str, str]]:
    """Manifest rows need `id`, `image`, `mask`; relative paths resolve against the manifest."""
    base = os.path.dirname(os.path.abspath(path))
    if path.endswith(".json"):
        with open(path) as f:
            rows = json.load(f)
    else:
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        for k in ("id", "image", "mask"):
            if k not in r:
                raise ValueError(f"manifest row missing '{k}': {r}")
        out.append(
            {
                "id": str(r["id"]),
                "image": (
                    r["image"]
                    if os.path.isabs(r["image"])
                    else os.path.join(base, r["image"])
                ),
                "mask": (
                    r["mask"]
                    if os.path.isabs(r["mask"])
                    else os.path.join(base, r["mask"])
                ),
            }
        )
    return out


def split_cases(cases: Sequence[dict], val_fraction: float = 0.2, seed: int = 0):
    """Subject-level split (one row == one subject; never split patches of a subject)."""
    if len(cases) < 2:
        raise ValueError("need at least 2 cases for a train/val split")
    idx = np.random.default_rng(seed).permutation(len(cases))
    n_val = max(1, int(round(len(cases) * val_fraction)))
    val = [cases[i] for i in idx[:n_val]]
    train = [cases[i] for i in idx[n_val:]]
    return train, val


def load_case(case: dict) -> Tuple[np.ndarray, np.ndarray, Volume]:
    """Return (normalised image, binary mask, source volume)."""
    vol = load_volume(case["image"])
    mask = load_volume(case["mask"]).data > 0.5
    if mask.shape != vol.data.shape:
        raise ValueError(f"{case['id']}: image {vol.data.shape} != mask {mask.shape}")
    return normalize(vol.data, brain_mask(vol.data)), mask, vol


class PatchDataset(Dataset):
    """Random 3D patches; `fg_prob` of them are centred on a lesion voxel."""

    def __init__(
        self,
        cases: Sequence[dict],
        patch_size=(48, 48, 48),
        samples_per_epoch: int = 64,
        fg_prob: float = 0.5,
        augment: bool = True,
        seed: int = 0,
    ):
        self.items = [load_case(c)[:2] for c in cases]
        self.fg_idx = [np.argwhere(m) for _, m in self.items]
        self.patch, self.n, self.fg_prob, self.augment = (
            tuple(patch_size),
            samples_per_epoch,
            fg_prob,
            augment,
        )
        self.seed = seed

    def __len__(self) -> int:
        return self.n

    def _start(self, rng, shape, center=None):
        s = []
        for ax, (dim, p) in enumerate(zip(shape, self.patch)):
            if dim <= p:
                s.append(0)
                continue
            lo = 0 if center is None else int(center[ax]) - p + 1
            hi = dim - p if center is None else int(center[ax])
            lo, hi = max(0, lo), min(dim - p, hi)
            s.append(int(rng.integers(lo, hi + 1)))
        return s

    def __getitem__(self, i: int):
        rng = np.random.default_rng((self.seed, i, torch.initial_seed() % (2**31)))
        k = int(rng.integers(len(self.items)))
        img, msk = self.items[k]
        center = None
        if self.fg_idx[k].size and rng.random() < self.fg_prob:
            center = self.fg_idx[k][rng.integers(len(self.fg_idx[k]))]
        z, y, x = self._start(rng, img.shape, center)
        pz, py, px = self.patch
        im, mk = (
            img[z : z + pz, y : y + py, x : x + px],
            msk[z : z + pz, y : y + py, x : x + px],
        )
        pad = [(0, p - s) for p, s in zip(self.patch, im.shape)]
        if any(b for _, b in pad):
            im, mk = np.pad(im, pad), np.pad(mk, pad)
        if self.augment:
            im, mk = _augment(im, mk, rng)
        return (
            torch.from_numpy(np.ascontiguousarray(im, dtype=np.float32))[None],
            torch.from_numpy(np.ascontiguousarray(mk, dtype=np.float32))[None],
        )


def _augment(im: np.ndarray, mk: np.ndarray, rng) -> Tuple[np.ndarray, np.ndarray]:
    for ax in range(3):
        if rng.random() < 0.5:
            im, mk = np.flip(im, ax), np.flip(mk, ax)
    im = im * rng.uniform(0.9, 1.1) + rng.uniform(-0.1, 0.1)
    if rng.random() < 0.3:
        im = im + rng.normal(0, 0.05, im.shape)
    return im, mk


def make_synthetic_dataset(
    out_dir: str, n_cases: int = 6, shape=(48, 48, 40), seed: int = 0
) -> str:
    """Write a synthetic phantom dataset + manifest.csv (smoke tests/demos only)."""
    from ..synthetic import make_phantom

    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for i in range(n_cases):
        vol, ref = make_phantom(shape=shape, n_lesions=4 + i % 3, seed=seed + i)
        ip, mp = f"case{i:03d}_flair.npz", f"case{i:03d}_mask.npz"
        save_volume(vol, os.path.join(out_dir, ip))
        save_volume(
            Volume(ref.astype(np.float32), vol.spacing), os.path.join(out_dir, mp)
        )
        rows.append({"id": f"case{i:03d}", "image": ip, "mask": mp})
    path = os.path.join(out_dir, "manifest.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "image", "mask"])
        w.writeheader()
        w.writerows(rows)
    return path
