"""Tests for public-dataset manifest builders (synthetic folder layouts, no real data)."""

import csv
import os

import numpy as np
import pytest

nib = pytest.importorskip("nibabel")

from ml.mri_analysis.datasets import (  # noqa: E402
    discover_isbi2015,
    discover_msseg2016,
    discover_pattern,
    main,
    verify_cases,
    write_manifest,
)


def _nii(path, arr):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    nib.save(nib.Nifti1Image(arr.astype(np.float32), np.eye(4)), path)


def _vol(seed, shape=(12, 12, 12)):
    return np.random.default_rng(seed).random(shape)


def _mask(box):
    m = np.zeros((12, 12, 12))
    m[box] = 1
    return m


@pytest.fixture
def isbi(tmp_path):
    root = tmp_path / "isbi"
    for subj in ("training01", "training02"):
        for tp in ("01", "02"):
            _nii(
                str(
                    root
                    / "training"
                    / subj
                    / "preprocessed"
                    / f"{subj}_{tp}_flair_pp.nii.gz"
                ),
                _vol(1),
            )
            _nii(
                str(root / "training" / subj / "masks" / f"{subj}_{tp}_mask1.nii.gz"),
                _mask(np.s_[2:5, 2:5, 2:5]),
            )
            _nii(
                str(root / "training" / subj / "masks" / f"{subj}_{tp}_mask2.nii.gz"),
                _mask(np.s_[3:7, 3:7, 3:7]),
            )
    return str(root)


def test_isbi_discovery_and_subjects(isbi):
    cases = discover_isbi2015(isbi)
    assert [c["id"] for c in cases] == [
        "training01_01",
        "training01_02",
        "training02_01",
        "training02_02",
    ]
    assert {c["subject"] for c in cases} == {"training01", "training02"}
    assert all("mask1" in c["mask"] for c in cases)


def test_isbi_raters(isbi):
    from ml.mri_analysis import load_volume

    m1 = (load_volume(discover_isbi2015(isbi, "1")[0]["mask"]).data > 0.5).sum()
    un = (load_volume(discover_isbi2015(isbi, "union")[0]["mask"]).data > 0.5).sum()
    it = (
        load_volume(discover_isbi2015(isbi, "intersection")[0]["mask"]).data > 0.5
    ).sum()
    assert it <= m1 <= un and it < un
    with pytest.raises(ValueError):
        discover_isbi2015(isbi, "3")


def test_msseg_discovery_skips_cases_without_consensus(tmp_path):
    root = tmp_path / "msseg"
    for centre, patient, with_mask in [
        ("Center_01", "Patient_01", True),
        ("Center_03", "Patient_02", False),
    ]:
        p = root / "Training" / centre / patient
        _nii(str(p / "Preprocessed_Data" / "FLAIR_preprocessed.nii.gz"), _vol(2))
        if with_mask:
            _nii(str(p / "Masks" / "Consensus.nii.gz"), _mask(np.s_[1:4, 1:4, 1:4]))
    cases = discover_msseg2016(str(root))
    assert len(cases) == 1 and cases[0]["site"] == "Center_01"


def test_missing_layout_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="check the folder layout"):
        discover_isbi2015(str(tmp_path))


def test_pattern_pairs_by_folder(tmp_path):
    for s in ("a", "b"):
        _nii(str(tmp_path / s / "flair.nii.gz"), _vol(3))
        _nii(str(tmp_path / s / "lesion.nii.gz"), _mask(np.s_[2:4, 2:4, 2:4]))
    cases = discover_pattern(
        str(tmp_path), "*/flair.nii.gz", "*/lesion.nii.gz", site="x"
    )
    assert [c["id"] for c in cases] == ["a", "b"] and cases[0]["site"] == "x"


def test_manifest_roundtrip_and_verify(isbi, tmp_path):
    cases = discover_isbi2015(isbi)
    path = write_manifest(cases, str(tmp_path / "m.csv"))
    rows = list(csv.DictReader(open(path)))
    assert rows[0]["subject"] == "training01" and os.path.isabs(rows[0]["image"])
    rep = verify_cases(cases)
    assert rep["n_cases"] == 4 and rep["n_subjects"] == 2 and rep["problems"] == []


def test_verify_flags_problems(tmp_path):
    _nii(str(tmp_path / "i.nii.gz"), _vol(4))
    _nii(str(tmp_path / "m_small.nii.gz"), np.zeros((6, 6, 6)))
    _nii(str(tmp_path / "m_soft.nii.gz"), _vol(5) * 0.5)
    cases = [
        {
            "id": "shape",
            "image": str(tmp_path / "i.nii.gz"),
            "mask": str(tmp_path / "m_small.nii.gz"),
        },
        {
            "id": "soft",
            "image": str(tmp_path / "i.nii.gz"),
            "mask": str(tmp_path / "m_soft.nii.gz"),
        },
        {
            "id": "gone",
            "image": str(tmp_path / "nope.nii.gz"),
            "mask": str(tmp_path / "i.nii.gz"),
        },
    ]
    probs = " | ".join(verify_cases(cases)["problems"])
    assert (
        "shape: image" in probs
        and "soft: mask not binary" in probs
        and "gone: cannot load" in probs
    )


def test_cli_isbi(isbi, tmp_path, capsys):
    rc = main(["isbi2015", isbi, "--out", str(tmp_path / "m.csv"), "--verify"])
    assert rc == 0 and (tmp_path / "m.csv").exists()
    assert '"n_subjects": 2' in capsys.readouterr().out
