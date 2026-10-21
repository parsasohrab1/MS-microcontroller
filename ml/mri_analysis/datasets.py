"""Loaders for public MS lesion datasets -> training manifests.

The datasets themselves are NOT bundled or downloaded: they require registration
and/or acceptance of their own licence terms. Obtain them from the official
challenge pages, then point these functions at the extracted folder.

Supported layouts (verify against your copy; use `discover_pattern` otherwise):
  ISBI 2015 longitudinal challenge (training set, has masks):
    <root>/training/training01/preprocessed/training01_01_flair_pp.nii[.gz]
    <root>/training/training01/masks/training01_01_mask1.nii[.gz]  (+ mask2)
  MSSEG-2016 (MICCAI 2016):
    <root>/{Training,Testing}/Center_01/Patient_01/Preprocessed_Data/FLAIR_preprocessed.nii.gz
    <root>/{Training,Testing}/Center_01/Patient_01/Masks/Consensus.nii.gz

Every case carries `subject` (for subject-level splits: ISBI has several
timepoints per patient) and `site` (for per-centre evaluation).
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
from typing import Dict, List, Optional

import numpy as np

from .io import Volume, load_volume, save_volume

Case = Dict[str, str]
MANIFEST_FIELDS = ["id", "image", "mask", "subject", "site"]


def _one(patterns: List[str]) -> Optional[str]:
    for p in patterns:
        hits = sorted(glob.glob(p))
        if hits:
            return hits[0]
    return None


def _need(cases: List[Case], root: str, name: str) -> List[Case]:
    if not cases:
        raise FileNotFoundError(
            f"no {name} cases found under {root!r}; check the folder layout "
            "(see module docstring) or use discover_pattern()"
        )
    return cases


def discover_isbi2015(
    root: str, rater: str = "1", cache_dir: Optional[str] = None
) -> List[Case]:
    """ISBI 2015 training set. rater: '1', '2', 'union' or 'intersection'.

    Combined masks ('union'/'intersection') are written to `cache_dir`
    (default `<root>/_combined_masks`).
    """
    if rater not in ("1", "2", "union", "intersection"):
        raise ValueError("rater must be '1', '2', 'union' or 'intersection'")
    cases: List[Case] = []
    flairs = glob.glob(
        os.path.join(root, "training", "training*", "preprocessed", "*_flair_pp.nii*")
    )
    for img in sorted(flairs):
        m = re.match(r"(training\d+)_(\d+)_flair_pp\.nii", os.path.basename(img))
        if not m:
            continue
        subj, tp = m.group(1), m.group(2)
        mdir = os.path.join(root, "training", subj, "masks")

        def mask(r: str) -> Optional[str]:
            return _one([os.path.join(mdir, f"{subj}_{tp}_mask{r}.nii*")])

        if rater in ("1", "2"):
            mpath = mask(rater)
        else:
            m1, m2 = mask("1"), mask("2")
            mpath = None
            if m1 and m2:
                out_dir = cache_dir or os.path.join(root, "_combined_masks")
                os.makedirs(out_dir, exist_ok=True)
                mpath = os.path.join(out_dir, f"{subj}_{tp}_{rater}.npz")
                if not os.path.exists(mpath):
                    a, b = load_volume(m1), load_volume(m2)
                    a_, b_ = a.data > 0.5, b.data > 0.5
                    comb = (a_ | b_) if rater == "union" else (a_ & b_)
                    save_volume(
                        Volume(comb.astype(np.float32), a.spacing, a.affine), mpath
                    )
        if mpath is None:
            continue
        cases.append(
            {
                "id": f"{subj}_{tp}",
                "image": img,
                "mask": mpath,
                "subject": subj,
                "site": "isbi2015",
            }
        )
    return _need(cases, root, "ISBI 2015")


def discover_msseg2016(root: str, splits=("Training", "Testing")) -> List[Case]:
    """MSSEG-2016 cases that have a Consensus mask (site = centre)."""
    cases: List[Case] = []
    for split in splits:
        for img in sorted(
            glob.glob(
                os.path.join(
                    root,
                    split,
                    "Center_*",
                    "Patient_*",
                    "Preprocessed_Data",
                    "FLAIR_preprocessed.nii*",
                )
            )
        ):
            pdir = os.path.dirname(os.path.dirname(img))
            mask = _one([os.path.join(pdir, "Masks", "Consensus.nii*")])
            if not mask:
                continue
            patient = os.path.basename(pdir)
            center = os.path.basename(os.path.dirname(pdir))
            cases.append(
                {
                    "id": f"{center}_{patient}",
                    "image": img,
                    "mask": mask,
                    "subject": f"{center}_{patient}",
                    "site": center,
                }
            )
    return _need(cases, root, "MSSEG-2016")


def discover_pattern(
    root: str,
    image_glob: str,
    mask_glob: str,
    subject_regex: Optional[str] = None,
    site: str = "",
) -> List[Case]:
    """Generic loader. Globs are relative to `root`; use `{id}`-free pairing:
    images and masks are matched by the first regex group of `subject_regex`
    (default: the parent folder name)."""
    rx = re.compile(subject_regex) if subject_regex else None

    def key(path: str) -> str:
        if rx:
            m = rx.search(path)
            if not m:
                raise ValueError(f"subject_regex did not match {path}")
            return m.group(1)
        return os.path.basename(os.path.dirname(path))

    imgs = {key(p): p for p in sorted(glob.glob(os.path.join(root, image_glob)))}
    masks = {key(p): p for p in sorted(glob.glob(os.path.join(root, mask_glob)))}
    cases = [
        {"id": k, "image": imgs[k], "mask": masks[k], "subject": k, "site": site}
        for k in sorted(imgs.keys() & masks.keys())
    ]
    return _need(cases, root, "pattern")


def write_manifest(cases: List[Case], path: str) -> str:
    """CSV manifest readable by `training.data.load_manifest` (absolute paths)."""
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        for c in cases:
            w.writerow(
                {
                    k: (
                        os.path.abspath(c[k])
                        if k in ("image", "mask")
                        else c.get(k, "")
                    )
                    for k in MANIFEST_FIELDS
                }
            )
    return path


def verify_cases(cases: List[Case]) -> Dict[str, object]:
    """Load every case and report problems (shape mismatch, non-binary or empty masks)."""
    problems: List[str] = []
    lesion_vox: List[int] = []
    for c in cases:
        try:
            img, msk = load_volume(c["image"]), load_volume(c["mask"])
        except Exception as e:  # unreadable file
            problems.append(f"{c['id']}: cannot load ({e})")
            continue
        if img.data.shape != msk.data.shape:
            problems.append(f"{c['id']}: image {img.shape} != mask {msk.shape}")
            continue
        vals = np.unique(msk.data)
        if not np.isin(vals, [0, 1]).all():
            problems.append(f"{c['id']}: mask not binary (values {vals[:5]})")
        n = int((msk.data > 0.5).sum())
        lesion_vox.append(n)
        if n == 0:
            problems.append(f"{c['id']}: empty mask")
    return {
        "n_cases": len(cases),
        "n_subjects": len({c.get("subject", c["id"]) for c in cases}),
        "sites": sorted({c.get("site", "") for c in cases}),
        "median_lesion_voxels": float(np.median(lesion_vox)) if lesion_vox else 0.0,
        "problems": problems,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build a training manifest from a public MS dataset"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("isbi2015")
    a1.add_argument("root")
    a1.add_argument("--rater", default="1", choices=["1", "2", "union", "intersection"])
    a2 = sub.add_parser("msseg2016")
    a2.add_argument("root")
    a3 = sub.add_parser("pattern")
    a3.add_argument("root")
    a3.add_argument("--image-glob", required=True)
    a3.add_argument("--mask-glob", required=True)
    a3.add_argument("--subject-regex")
    for p in (a1, a2, a3):
        p.add_argument("--out", required=True, help="manifest CSV to write")
        p.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "isbi2015":
        cases = discover_isbi2015(a.root, a.rater)
    elif a.cmd == "msseg2016":
        cases = discover_msseg2016(a.root)
    else:
        cases = discover_pattern(a.root, a.image_glob, a.mask_glob, a.subject_regex)
    write_manifest(cases, a.out)
    summary: Dict[str, object] = {"manifest": a.out, "n_cases": len(cases)}
    if a.verify:
        summary = {**summary, **verify_cases(cases)}
    print(json.dumps(summary, indent=2))
    return 1 if summary.get("problems") else 0


if __name__ == "__main__":
    raise SystemExit(main())
