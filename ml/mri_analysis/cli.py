"""CLI: python -m ml.mri_analysis.cli <image> [--reference ref] [--output mask]"""

from __future__ import annotations

import argparse
import json

from .pipeline import analyze_case
from .segmentation import ONNXSegmenter, ThresholdSegmenter


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="MS lesion MRI analysis")
    ap.add_argument("image")
    ap.add_argument("--reference")
    ap.add_argument("--output", help="path for predicted mask (.nii.gz/.npz/.npy)")
    ap.add_argument("--onnx-model", help="use ONNX model instead of threshold baseline")
    ap.add_argument("--fail-on-qc", action="store_true")
    a = ap.parse_args(argv)
    seg = ONNXSegmenter(a.onnx_model) if a.onnx_model else ThresholdSegmenter()
    res = analyze_case(a.image, a.reference, seg, a.output, fail_on_qc=a.fail_on_qc)
    print(json.dumps(res, indent=2))
    return 0 if res["qc"]["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
