"""ONNX export compatible with `segmentation.ONNXSegmenter` and a parity check."""

from __future__ import annotations

import numpy as np
import torch

from .inference import load_checkpoint


class _ProbModel(torch.nn.Module):
    def __init__(self, net):
        super().__init__()
        self.net = net

    def forward(self, x):
        return torch.sigmoid(self.net(x))


def export_onnx(checkpoint: str, out_path: str, verify: bool = True) -> dict:
    """Export a sigmoid-probability model with dynamic spatial axes (1,1,D,H,W)."""
    model, ck = load_checkpoint(checkpoint)
    wrapped = _ProbModel(model).eval()
    p = ck["patch_size"]
    dummy = torch.randn(1, 1, *p)
    kwargs = dict(
        input_names=["image"],
        output_names=["prob"],
        opset_version=17,
        dynamic_axes={
            "image": {2: "d", 3: "h", 4: "w"},
            "prob": {2: "d", 3: "h", 4: "w"},
        },
    )
    try:
        torch.onnx.export(wrapped, dummy, out_path, dynamo=False, **kwargs)
    except TypeError:  # older torch without the dynamo kwarg
        torch.onnx.export(wrapped, dummy, out_path, **kwargs)
    info = {"path": out_path, "threshold": ck.get("threshold", 0.5), "patch_size": p}
    if verify:
        import onnxruntime as ort

        sess = ort.InferenceSession(out_path, providers=["CPUExecutionProvider"])
        test = torch.randn(
            1, 1, p[0] + 5, p[1] + 3, p[2] + 7
        )  # non-multiple, different size
        with torch.no_grad():
            ref = wrapped(test).numpy()
        out = sess.run(None, {"image": test.numpy()})[0]
        info["max_abs_diff"] = float(np.abs(ref - out).max())
        if info["max_abs_diff"] > 1e-3:
            raise RuntimeError(
                f"ONNX output differs from PyTorch: {info['max_abs_diff']}"
            )
    return info
