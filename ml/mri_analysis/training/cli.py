"""CLI: python -m ml.mri_analysis.training.cli {make-synthetic,train,evaluate,export}"""

from __future__ import annotations

import argparse
import json

from ..evaluation import evaluate_dataset
from .data import load_manifest, make_synthetic_dataset, split_cases
from .export import export_onnx
from .inference import TorchSegmenter
from .trainer import TrainConfig, train


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="MS lesion segmentation training")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("make-synthetic", help="write a synthetic smoke-test dataset")
    s.add_argument("out_dir")
    s.add_argument("--n-cases", type=int, default=6)

    t = sub.add_parser("train")
    t.add_argument("manifest", help="CSV/JSON with columns id,image,mask")
    t.add_argument("--output-dir", default="runs/ms_lesion")
    t.add_argument("--epochs", type=int, default=50)
    t.add_argument("--batch-size", type=int, default=2)
    t.add_argument("--patch", type=int, nargs=3, default=[48, 48, 48])
    t.add_argument("--base-channels", type=int, default=16)
    t.add_argument("--lr", type=float, default=1e-3)
    t.add_argument("--samples-per-epoch", type=int, default=64)
    t.add_argument("--val-fraction", type=float, default=0.2)
    t.add_argument("--patience", type=int, default=0)
    t.add_argument("--seed", type=int, default=0)
    t.add_argument("--device", default="auto")
    t.add_argument("--resume")

    e = sub.add_parser("evaluate", help="evaluate a checkpoint on the held-out split")
    e.add_argument("manifest")
    e.add_argument("checkpoint")
    e.add_argument("--val-fraction", type=float, default=0.2)
    e.add_argument("--seed", type=int, default=0)
    e.add_argument(
        "--all", action="store_true", help="evaluate all cases, not only the val split"
    )
    e.add_argument("--csv")
    e.add_argument("--json")

    x = sub.add_parser("export", help="export checkpoint to ONNX (for ONNXSegmenter)")
    x.add_argument("checkpoint")
    x.add_argument("out")

    a = ap.parse_args(argv)
    if a.cmd == "make-synthetic":
        print(make_synthetic_dataset(a.out_dir, a.n_cases))
    elif a.cmd == "train":
        cfg = TrainConfig(
            manifest=a.manifest,
            output_dir=a.output_dir,
            epochs=a.epochs,
            batch_size=a.batch_size,
            patch_size=tuple(a.patch),
            base_channels=a.base_channels,
            lr=a.lr,
            samples_per_epoch=a.samples_per_epoch,
            val_fraction=a.val_fraction,
            patience=a.patience,
            seed=a.seed,
            device=a.device,
            resume=a.resume,
        )
        res = train(cfg)
        res.pop("history")
        print(json.dumps(res, indent=2))
    elif a.cmd == "evaluate":
        cases = load_manifest(a.manifest)
        if not a.all:
            cases = split_cases(cases, a.val_fraction, a.seed)[1]
        res = evaluate_dataset(
            [
                {"id": c["id"], "image": c["image"], "reference": c["mask"]}
                for c in cases
            ],
            TorchSegmenter(a.checkpoint),
            a.csv,
            a.json,
        )
        print(json.dumps(res["summary"], indent=2))
    elif a.cmd == "export":
        print(json.dumps(export_onnx(a.checkpoint, a.out), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
