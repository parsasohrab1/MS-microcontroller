# MRI Analysis Module (ISMRM 2027 readiness)

Standalone module at `ml/mri_analysis/` for MS lesion MRI analysis, independent of the firmware/cloud stack.

## Pipeline
1. **Load** (`io.py`) – NIfTI (`.nii/.nii.gz`, via nibabel), `.npy`, `.npz`; voxel spacing/affine retained.
2. **QC** (`qc.py`) – NaN/Inf, constant image, dimensions, anisotropy, SNR (Rician background estimate), saturation, ghosting proxy, sharpness; returns `QCReport` with issues (fail) and warnings.
3. **Preprocess** (`preprocessing.py`) – brain mask, homomorphic bias correction (lightweight N4 stand-in), z-score normalisation, isotropic resampling.
4. **Segment** (`segmentation.py`) – `ThresholdSegmenter` (FLAIR hyperintensity baseline); `CallableSegmenter` / `ONNXSegmenter` for trained models (e.g. nnU-Net exported to ONNX) behind the same `Segmenter` interface.
5. **Evaluate** (`metrics.py`, `evaluation.py`) – Dice, IoU, sensitivity, precision, volume difference, HD/HD95/ASSD (mm), lesion-wise recall/precision/F1; dataset aggregation to CSV/JSON.

## Usage
```bash
python -m ml.mri_analysis.cli flair.nii.gz --reference lesion_mask.nii.gz --output pred.nii.gz
python -m ml.mri_analysis.cli flair.nii.gz --onnx-model model.onnx --fail-on-qc
```
```python
from ml.mri_analysis import ThresholdSegmenter, evaluate_dataset
res = evaluate_dataset([{"id": "s01", "image": "s01_flair.nii.gz", "reference": "s01_mask.nii.gz"}],
                       ThresholdSegmenter(), output_csv="metrics.csv", output_json="metrics.json")
```

## Status and limitations (honest scope)
- Verified only on a **synthetic phantom** (`synthetic.py`) via `tests/unit/test_mri_analysis.py`; **no real-patient validation has been done**.
- The threshold segmenter is a baseline, not a publishable model. For ISMRM, train/validate a model (e.g. nnU-Net) on public data (MSSEG-2016/2, ISBI 2015, WMH) and plug it in via `ONNXSegmenter`.
- Single-channel (FLAIR) only; multi-contrast input, N4 correction (SimpleITK), skull stripping (HD-BET/SynthStrip) and longitudinal new-lesion analysis are next steps.
- Research use only; not a medical device.
