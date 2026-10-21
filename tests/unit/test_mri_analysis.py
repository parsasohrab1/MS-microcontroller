"""Unit tests for the MRI analysis module."""

import numpy as np
import pytest

from ml.mri_analysis import (
    ThresholdSegmenter, CallableSegmenter, analyze_case, dice, evaluate_dataset,
    lesion_wise_metrics, load_volume, run_qc, save_volume, surface_distances,
    compute_all_metrics,
)
from ml.mri_analysis.synthetic import make_phantom


def test_dice_basic():
    a = np.zeros((10, 10, 10), bool); a[2:6, 2:6, 2:6] = True
    assert dice(a, a) == 1.0
    assert dice(a, np.zeros_like(a)) == 0.0
    assert dice(np.zeros_like(a), np.zeros_like(a)) == 1.0
    b = np.zeros_like(a); b[2:6, 2:6, 2:4] = True
    assert dice(a, b) == pytest.approx(2 * 32 / (64 + 32))


def test_surface_distance_shift():
    a = np.zeros((20, 20, 20), bool); a[5:10, 5:10, 5:10] = True
    b = np.roll(a, 2, axis=0)
    sd = surface_distances(a, b)
    assert 0 < sd["assd_mm"] < 3 and sd["hd_mm"] >= 2
    assert np.isnan(surface_distances(a, np.zeros_like(a))["hd95_mm"])


def test_lesion_wise():
    ref = np.zeros((20, 20, 20), bool); ref[2:4, 2:4, 2:4] = True; ref[10:12, 10:12, 10:12] = True
    pred = np.zeros_like(ref); pred[2:4, 2:4, 2:4] = True; pred[16:18, 16:18, 16:18] = True
    m = lesion_wise_metrics(pred, ref)
    assert (m["lesion_tp"], m["lesion_fn"], m["lesion_fp"]) == (1, 1, 1)
    assert m["lesion_f1"] == pytest.approx(0.5)


def test_shape_mismatch():
    with pytest.raises(ValueError):
        compute_all_metrics(np.zeros((4, 4, 4)), np.zeros((5, 5, 5)))


def test_qc_pass_and_fail():
    vol, _ = make_phantom()
    assert run_qc(vol).passed
    bad = vol.__class__(np.full(vol.shape, 1.0, np.float32), vol.spacing)
    assert not run_qc(bad).passed
    nan = vol.__class__(vol.data.copy(), vol.spacing); nan.data[0, 0, 0] = np.nan
    assert not run_qc(nan).passed
    noisy, _ = make_phantom(noise=0.5)
    assert not run_qc(noisy).passed


def test_threshold_segmentation_on_phantom():
    vol, ref = make_phantom()
    pred = ThresholdSegmenter().segment(vol)
    assert dice(pred, ref) > 0.6
    assert lesion_wise_metrics(pred, ref)["lesion_recall"] >= 0.8


def test_callable_segmenter_shape_check():
    vol, _ = make_phantom()
    with pytest.raises(ValueError):
        CallableSegmenter(lambda z: z[:5]).segment(vol)


def test_pipeline_and_dataset(tmp_path):
    vol, ref = make_phantom(seed=1)
    img_p, ref_p, out_p = (str(tmp_path / n) for n in ("img.npz", "ref.npz", "out.npz"))
    save_volume(vol, img_p)
    save_volume(vol.__class__(ref.astype(np.float32), vol.spacing), ref_p)
    res = analyze_case(img_p, ref_p, output_mask_path=out_p)
    assert res["segmented"] and res["metrics"]["dice"] > 0.6
    assert load_volume(out_p).data.shape == vol.shape

    out = evaluate_dataset([{"id": "a", "image": img_p, "reference": ref_p}],
                           ThresholdSegmenter(), str(tmp_path / "m.csv"), str(tmp_path / "m.json"))
    assert out["n_cases"] == 1 and out["summary"]["dice"]["mean"] > 0.6
    assert (tmp_path / "m.csv").exists()


def test_fail_on_qc(tmp_path):
    p = str(tmp_path / "bad.npy")
    np.save(p, np.ones((32, 32, 32), np.float32))
    assert analyze_case(p, fail_on_qc=True)["segmented"] is False
