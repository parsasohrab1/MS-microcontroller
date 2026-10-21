"""Training loop with subject-level validation (Dice via the module's own metrics)."""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np
import torch
from torch.utils.data import DataLoader

from ..metrics import dice
from .data import PatchDataset, load_case, load_manifest, split_cases
from .inference import sliding_window_predict
from .losses import DiceBCELoss
from .unet import UNet3D


@dataclass
class TrainConfig:
    manifest: str
    output_dir: str = "runs/ms_lesion"
    patch_size: tuple = (48, 48, 48)
    base_channels: int = 16
    depth: int = 3
    epochs: int = 50
    batch_size: int = 2
    samples_per_epoch: int = 64
    lr: float = 1e-3
    weight_decay: float = 1e-5
    fg_prob: float = 0.5
    val_fraction: float = 0.2
    val_every: int = 1
    patience: int = 0  # 0 disables early stopping
    seed: int = 0
    num_workers: int = 0
    device: str = "auto"
    resume: Optional[str] = None
    threshold_grid: tuple = (0.3, 0.4, 0.5, 0.6, 0.7)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


@torch.no_grad()
def validate(model, val_cases, patch, thresholds, device):
    """Mean Dice per threshold over validation subjects."""
    per_thr = {t: [] for t in thresholds}
    for c in val_cases:
        img, msk, _ = load_case(c)
        prob = sliding_window_predict(model, img, patch, 0.5, device)
        for t in thresholds:
            per_thr[t].append(dice(prob > t, msk))
    return {t: float(np.mean(v)) for t, v in per_thr.items()}


def train(cfg: TrainConfig) -> dict:
    seed_everything(cfg.seed)
    device = (
        ("cuda" if torch.cuda.is_available() else "cpu")
        if cfg.device == "auto"
        else cfg.device
    )
    os.makedirs(cfg.output_dir, exist_ok=True)

    train_cases, val_cases = split_cases(
        load_manifest(cfg.manifest), cfg.val_fraction, cfg.seed
    )
    with open(os.path.join(cfg.output_dir, "split.json"), "w") as f:
        json.dump(
            {
                "train": [c["id"] for c in train_cases],
                "val": [c["id"] for c in val_cases],
            },
            f,
            indent=2,
        )

    ds = PatchDataset(
        train_cases, cfg.patch_size, cfg.samples_per_epoch, cfg.fg_prob, True, cfg.seed
    )
    loader = DataLoader(
        ds,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=cfg.num_workers,
        drop_last=False,
    )

    model_cfg = {"in_channels": 1, "base": cfg.base_channels, "depth": cfg.depth}
    model = UNet3D(**model_cfg).to(device)
    loss_fn = DiceBCELoss().to(device)
    opt = torch.optim.AdamW(
        model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay
    )
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda e: (1 - e / max(cfg.epochs, 1)) ** 0.9
    )

    start_epoch, best, best_thr, history, bad = 0, -1.0, 0.5, [], 0
    if cfg.resume:
        ck = torch.load(cfg.resume, map_location=device, weights_only=True)
        model.load_state_dict(ck["state_dict"])
        opt.load_state_dict(ck["optimizer"])
        sched.load_state_dict(ck["scheduler"])
        start_epoch, best, best_thr = ck["epoch"] + 1, ck["best_dice"], ck["threshold"]
        history = ck.get("history", [])

    def save(path, epoch):
        torch.save(
            {
                "state_dict": model.state_dict(),
                "optimizer": opt.state_dict(),
                "scheduler": sched.state_dict(),
                "epoch": epoch,
                "best_dice": best,
                "threshold": best_thr,
                "history": history,
                "model_config": model_cfg,
                "patch_size": list(cfg.patch_size),
                "train_config": asdict(cfg),
            },
            path,
        )

    for epoch in range(start_epoch, cfg.epochs):
        model.train()
        t0, losses = time.time(), []
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(model(x), y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 12.0)
            opt.step()
            losses.append(float(loss.item()))
        sched.step()
        rec = {
            "epoch": epoch,
            "train_loss": float(np.mean(losses)),
            "lr": opt.param_groups[0]["lr"],
            "seconds": round(time.time() - t0, 2),
        }
        if (epoch + 1) % cfg.val_every == 0 or epoch == cfg.epochs - 1:
            scores = validate(
                model, val_cases, cfg.patch_size, cfg.threshold_grid, device
            )
            thr = max(scores, key=lambda t: scores[t])
            rec.update(val_dice=scores[thr], val_threshold=thr)
            if scores[thr] > best:
                best, best_thr, bad = scores[thr], thr, 0
                save(os.path.join(cfg.output_dir, "best.pt"), epoch)
            else:
                bad += 1
        history.append(rec)
        save(os.path.join(cfg.output_dir, "last.pt"), epoch)
        with open(os.path.join(cfg.output_dir, "history.json"), "w") as f:
            json.dump(history, f, indent=2)
        print(json.dumps(rec))
        if cfg.patience and bad >= cfg.patience:
            break

    return {
        "best_val_dice": best,
        "threshold": best_thr,
        "epochs_run": len(history),
        "best_checkpoint": os.path.join(cfg.output_dir, "best.pt"),
        "history": history,
    }
