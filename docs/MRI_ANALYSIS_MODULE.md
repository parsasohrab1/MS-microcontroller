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

## Training pipeline (`ml/mri_analysis/training/`)
PyTorch pipeline for training a 3D U-Net lesion segmenter (`pip install -r ml/mri_analysis/requirements-training.txt`).

| Piece | File |
|---|---|
| 3D U-Net (instance norm, any input size) | `unet.py` |
| Dice + BCE loss | `losses.py` |
| Manifest loading, subject-level split, foreground-biased patch sampling, flip/intensity/noise augmentation | `data.py` |
| Training loop: AdamW, poly LR, grad clipping, per-epoch sliding-window validation Dice, validation-tuned threshold, best/last checkpoints, resume, early stopping | `trainer.py` |
| Sliding-window inference and `TorchSegmenter` | `inference.py` |
| ONNX export with PyTorch-vs-ONNX parity check; writes `<model>.onnx.json` (patch size, threshold) that `ONNXSegmenter` reads to run the same sliding-window inference as training | `export.py` |

Data: a manifest (CSV/JSON) with columns `id,image,mask` (FLAIR + binary lesion mask, NIfTI/npz/npy; relative paths resolve against the manifest). Splits are per subject and written to `split.json`.

```bash
python -m ml.mri_analysis.training.cli train manifest.csv --output-dir runs/v1 --epochs 200 --patch 64 64 64 --base-channels 16
python -m ml.mri_analysis.training.cli evaluate manifest.csv runs/v1/best.pt --csv val_metrics.csv
python -m ml.mri_analysis.training.cli export runs/v1/best.pt model.onnx
python -m ml.mri_analysis.cli flair.nii.gz --onnx-model model.onnx --reference mask.nii.gz
# smoke test without real data:
python -m ml.mri_analysis.training.cli make-synthetic /tmp/syn && python -m ml.mri_analysis.training.cli train /tmp/syn/manifest.csv --epochs 5 --patch 16 16 16 --base-channels 4 --device cpu
```

**Caveats.** No real MS dataset is bundled and none was used: tests train on the synthetic phantom only, so they verify the pipeline (loss decreases, resume, ONNX parity), not clinical accuracy. Datasets such as MSSEG-2016, ISBI 2015 and MSLesSeg have their own licences and must be obtained and cited separately. The validation threshold is tuned on the same split used for checkpoint selection, so report final numbers on a separate held-out test set (the `evaluate` command takes any manifest). Single-channel FLAIR only; for a publishable result expect to need multi-site data, larger patches/GPU training, and comparison against nnU-Net.

## Public dataset loaders (`ml/mri_analysis/datasets.py`)
Builds a training manifest (`id,image,mask,subject,site`) from a downloaded public dataset. **Nothing is downloaded for you**: these datasets need registration and have their own licences/citation requirements, so get them from the official challenge pages and point the loader at the extracted folder.

| Dataset | Loader | Expected layout |
|---|---|---|
| ISBI 2015 longitudinal (training set) | `discover_isbi2015(root, rater="1"\|"2"\|"union"\|"intersection")` | `training/trainingNN/preprocessed/trainingNN_TT_flair_pp.nii[.gz]`, `training/trainingNN/masks/trainingNN_TT_mask{1,2}.nii[.gz]` |
| MSSEG-2016 | `discover_msseg2016(root)` | `{Training,Testing}/Center_XX/Patient_YY/Preprocessed_Data/FLAIR_preprocessed.nii.gz` + `Masks/Consensus.nii.gz` |
| anything else | `discover_pattern(root, image_glob, mask_glob, subject_regex=None)` | any layout where image and mask pair by a regex group (default: parent folder) |

```bash
python -m ml.mri_analysis.datasets isbi2015 /data/isbi2015 --rater union --out isbi_manifest.csv --verify
python -m ml.mri_analysis.datasets msseg2016 /data/msseg2016 --out msseg_manifest.csv --verify
python -m ml.mri_analysis.training.cli train isbi_manifest.csv --output-dir runs/isbi --epochs 200 --patch 64 64 64
```
- `--verify` loads every case and reports shape mismatches, non-binary masks, empty masks and unreadable files (exit code 1 if any).
- `subject` drives the split: `split_cases` keeps all rows of a subject together, which matters for ISBI (several timepoints per patient) - splitting by row would leak patients between train and validation. `site` is kept for per-centre evaluation.
- The layouts above are written from the datasets' published structure and exercised in tests only with **synthetic folders built to that layout**; they have not been run against the real downloads. If your copy differs, `discover_*` raises a clear "check the folder layout" error, and `discover_pattern` covers the rest.
- ISBI 2015 test-set masks are not public, so only the training set is usable for supervised training/validation. ISBI `union`/`intersection` masks are written to `<root>/_combined_masks`.
