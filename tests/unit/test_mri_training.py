"""Tests for the MS lesion training pipeline (skipped when torch is unavailable)."""

import json

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from ml.mri_analysis import dice  # noqa: E402
from ml.mri_analysis.training.data import (  # noqa: E402
    PatchDataset,
    load_manifest,
    make_synthetic_dataset,
    split_cases,
)
from ml.mri_analysis.training.export import export_onnx  # noqa: E402
from ml.mri_analysis.training.inference import (  # noqa: E402
    TorchSegmenter,
    sliding_window_predict,
)
from ml.mri_analysis.training.losses import DiceBCELoss  # noqa: E402
from ml.mri_analysis.training.trainer import TrainConfig, train  # noqa: E402
from ml.mri_analysis.training.unet import UNet3D  # noqa: E402


def test_unet_handles_non_multiple_shapes():
    net = UNet3D(base=4, depth=2)
    out = net(torch.randn(1, 1, 13, 10, 17))
    assert out.shape == (1, 1, 13, 10, 17)


def test_loss_perfect_vs_wrong():
    loss = DiceBCELoss()
    y = torch.zeros(1, 1, 8, 8, 8)
    y[..., 2:5, 2:5, 2:5] = 1
    good = loss((y * 20 - 10), y)
    bad = loss(((1 - y) * 20 - 10), y)
    assert good < 0.01 < bad


def test_split_is_subject_level_and_deterministic():
    cases = [{"id": str(i)} for i in range(10)]
    tr1, va1 = split_cases(cases, 0.2, seed=3)
    tr2, va2 = split_cases(cases, 0.2, seed=3)
    assert va1 == va2 and len(va1) == 2
    assert not {c["id"] for c in tr1} & {c["id"] for c in va1}
    with pytest.raises(ValueError):
        split_cases(cases[:1])


def test_patch_dataset_shapes_and_foreground(tmp_path):
    cases = load_manifest(make_synthetic_dataset(str(tmp_path), 2, shape=(32, 32, 32)))
    ds = PatchDataset(cases, (16, 16, 16), samples_per_epoch=20, fg_prob=1.0)
    xs = [ds[i] for i in range(20)]
    assert all(x.shape == (1, 16, 16, 16) and y.shape == x.shape for x, y in xs)
    assert sum(float(y.sum()) > 0 for _, y in xs) >= 15


def test_manifest_validation(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"id": "a", "image": "x.npz"}]))
    with pytest.raises(ValueError):
        load_manifest(str(p))


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    d = tmp_path_factory.mktemp("train")
    manifest = make_synthetic_dataset(str(d / "data"), 6, shape=(32, 32, 32))
    cfg = TrainConfig(
        manifest=manifest,
        output_dir=str(d / "run"),
        patch_size=(16, 16, 16),
        base_channels=4,
        depth=2,
        epochs=6,
        batch_size=4,
        samples_per_epoch=32,
        lr=3e-3,
        val_fraction=0.34,
        device="cpu",
    )
    return cfg, train(cfg), d


def test_training_learns_and_writes_artifacts(trained):
    cfg, res, d = trained
    losses = [h["train_loss"] for h in res["history"]]
    assert losses[-1] < losses[0]
    assert res["best_val_dice"] > 0.0
    for f in ("best.pt", "last.pt", "history.json", "split.json"):
        assert (d / "run" / f).exists()


def test_resume(trained):
    cfg, _, d = trained
    cfg2 = TrainConfig(
        **{
            **cfg.__dict__,
            "epochs": 8,
            "resume": str(d / "run" / "last.pt"),
            "output_dir": str(d / "run2"),
        }
    )
    res = train(cfg2)
    assert [h["epoch"] for h in res["history"]][-1] == 7 and res["epochs_run"] == 8


def test_torch_segmenter_and_onnx_parity(trained):
    from ml.mri_analysis import ONNXSegmenter, load_volume

    cfg, _, d = trained
    ck = str(d / "run" / "best.pt")
    case = load_manifest(cfg.manifest)[0]
    vol = load_volume(case["image"])
    seg = TorchSegmenter(ck).segment(vol)
    assert seg.shape == vol.data.shape and seg.dtype == bool

    info = export_onnx(ck, str(d / "m.onnx"))
    assert info["max_abs_diff"] < 1e-3
    onnx_seg = ONNXSegmenter(str(d / "m.onnx")).segment(vol)
    assert seg.any() and dice(onnx_seg, seg) > 0.95


def test_sliding_window_matches_full_forward():
    torch.manual_seed(0)
    net = UNet3D(base=4, depth=2).eval()
    img = np.random.default_rng(0).normal(size=(20, 20, 20)).astype(np.float32)
    prob = sliding_window_predict(net, img, (20, 20, 20), overlap=0.5)
    with torch.no_grad():
        ref = torch.sigmoid(net(torch.from_numpy(img)[None, None]))[0, 0].numpy()
    assert np.allclose(prob, ref, atol=1e-5)
