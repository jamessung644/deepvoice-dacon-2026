#!/usr/bin/env python3
"""Independent compact MUSIC_FAKE model for HTDemucs non-vocal 16 kHz stems.

The architecture is a clean version of the 1.24M LogSpecResNet.  This module
contains no checkpoint discovery or pretrained-weight path: every Task 5 run
starts from a newly initialized state and predicts MUSIC_FAKE=1.
"""
from __future__ import annotations

import hashlib
import io
import math
from pathlib import Path
import re

import torch
from torch import nn


MODEL_ID = "music_fake_logspec_resnet_v1"
TASK = "MUSIC_FAKE"
POSITIVE_LABEL = "MUSIC_FAKE=1"
INPUT_DOMAIN = "htdemucs_non_vocals_16k"
SAMPLE_RATE_HZ = 16_000
CLIP_SAMPLES = 64_600
EXPECTED_PARAMETER_COUNT = 1_241_825


def normalization(channels: int) -> nn.Module:
    return nn.GroupNorm(math.gcd(8, channels), channels)


class ResidualBlock(nn.Module):
    def __init__(self, incoming: int, outgoing: int, stride: int = 1):
        super().__init__()
        self.body = nn.Sequential(
            nn.Conv2d(incoming, outgoing, 3, stride, 1, bias=False),
            normalization(outgoing),
            nn.SiLU(),
            nn.Conv2d(outgoing, outgoing, 3, 1, 1, bias=False),
            normalization(outgoing),
        )
        self.shortcut = nn.Identity() if incoming == outgoing and stride == 1 else nn.Sequential(
            nn.Conv2d(incoming, outgoing, 1, stride, bias=False),
            normalization(outgoing),
        )
        self.activation = nn.SiLU()

    def forward(self, tensor: torch.Tensor) -> torch.Tensor:
        return self.activation(self.body(tensor) + self.shortcut(tensor))


class MusicFakeLogSpecResNetV1(nn.Module):
    """Log-power and temporal-delta ResNet producing one MUSIC_FAKE logit."""

    def __init__(self, width: int = 24, dropout: float = 0.15):
        super().__init__()
        if width != 24:
            raise ValueError("v1 width is frozen at 24")
        if not math.isfinite(dropout) or not 0 <= dropout < 1:
            raise ValueError("dropout must be finite and in [0, 1)")
        self.width = width
        self.dropout = float(dropout)
        self.register_buffer("window", torch.hann_window(512))
        channels = [width, width * 2, width * 4, width * 6]
        self.stem = nn.Sequential(
            nn.Conv2d(2, width, 5, 2, 2, bias=False),
            normalization(width),
            nn.SiLU(),
        )
        blocks: list[nn.Module] = []
        incoming = width
        for stage, outgoing in enumerate(channels):
            blocks.extend(
                [
                    ResidualBlock(incoming, outgoing, 1 if stage == 0 else 2),
                    ResidualBlock(outgoing, outgoing),
                ]
            )
            incoming = outgoing
        self.blocks = nn.Sequential(*blocks)
        self.head = nn.Sequential(
            nn.LayerNorm(incoming * 8),
            nn.Dropout(dropout),
            nn.Linear(incoming * 8, 128),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
        )

    def forward(self, waveforms: torch.Tensor) -> torch.Tensor:
        if waveforms.ndim != 2:
            raise ValueError("waveforms must have shape [batch, samples]")
        if waveforms.shape[-1] < 512:
            raise ValueError("waveforms must contain at least one 512-sample FFT window")
        # Spectrum normalization remains FP32 under CUDA AMP.
        with torch.autocast(device_type=waveforms.device.type, enabled=False):
            spectrum = torch.stft(
                waveforms.float(),
                n_fft=512,
                hop_length=256,
                win_length=512,
                window=self.window.float(),
                center=False,
                return_complex=True,
            )
            log_power = spectrum.abs().square().clamp_min(1e-10).log()
            mean = log_power.mean(dim=(-2, -1), keepdim=True)
            std = log_power.std(dim=(-2, -1), keepdim=True, unbiased=False).clamp_min(1e-5)
            normalized = (log_power - mean) / std
            delta = nn.functional.pad(normalized[..., 1:] - normalized[..., :-1], (1, 0))
            image = torch.stack((normalized, delta), dim=1)
        features = self.blocks(self.stem(image))
        temporal_mean = features.float().mean(dim=-1, keepdim=True)
        temporal_std = features.float().var(dim=-1, keepdim=True, unbiased=False).clamp_min(1e-6).sqrt()
        statistics = torch.cat(
            (
                nn.functional.adaptive_avg_pool2d(temporal_mean, (4, 1)),
                nn.functional.adaptive_avg_pool2d(temporal_std, (4, 1)),
            ),
            dim=1,
        )
        return self.head(statistics.flatten(1)).squeeze(1)


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def build_model(width: int = 24, dropout: float = 0.15) -> tuple[MusicFakeLogSpecResNetV1, dict]:
    model = MusicFakeLogSpecResNetV1(width=width, dropout=dropout)
    count = parameter_count(model)
    if count != EXPECTED_PARAMETER_COUNT:
        raise RuntimeError(f"Frozen v1 parameter count changed: {count} != {EXPECTED_PARAMETER_COUNT}")
    config = {
        "model_id": MODEL_ID,
        "class": "MusicFakeLogSpecResNetV1",
        "task": TASK,
        "positive_label": POSITIVE_LABEL,
        "input_domain": INPUT_DOMAIN,
        "pretrained_checkpoint": None,
        "initialization": "fresh PyTorch initialization from recorded run seed; no VOICE_FAKE or FILE_FAKE weights",
        "width": width,
        "channels": [width * factor for factor in (1, 2, 4, 6)],
        "blocks_per_stage": 2,
        "dropout": dropout,
        "parameters": count,
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "clip_samples": CLIP_SAMPLES,
        "n_fft": 512,
        "hop_length": 256,
        "win_length": 512,
        "center": False,
        "window": "periodic Hann",
        "input_features": ["per-example normalized natural log-power", "first temporal difference"],
        "pooling": "time mean/std followed by four frequency bands",
        "output": "one logit; sigmoid is P(MUSIC_FAKE=1)",
    }
    return model, config


def load_selected_checkpoint(path, *, expected_bindings: dict, expected_checkpoint_sha256: str, device="cpu"):
    """Load only a Task 5 checkpoint with the frozen independent model identity."""
    if not isinstance(expected_checkpoint_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_checkpoint_sha256
    ):
        raise ValueError("Caller must supply an independent lowercase checkpoint SHA256")
    # Hash and deserialize the same immutable byte string.  Hashing the path and
    # reopening it for torch.load would leave a substitution race between the
    # two reads.
    payload = Path(path).read_bytes()
    actual_checkpoint_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_checkpoint_sha256 != expected_checkpoint_sha256:
        raise ValueError("Checkpoint bytes do not match the independently supplied SHA256")
    checkpoint = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
    required = {
        "schema_version", "model_state_dict", "model_config", "best_epoch", "best_metrics",
        "config_sha256", "input_manifest_sha256", "used_train_manifest_sha256", "used_dev_manifest_sha256",
        "used_model_selection_dev_manifest_sha256", "used_report_only_dev_manifest_sha256",
        "task2_source_manifest_sha256", "task2_completion_receipt_sha256",
        "task3_stem_manifest_sha256", "task3_completion_receipt_sha256",
        "source_files_sha256", "fresh_initial_state_sha256", "pretrained_checkpoint",
        "task", "positive_label", "input_domain", "seed",
    }
    if not isinstance(checkpoint, dict) or set(checkpoint) != required:
        raise ValueError("Checkpoint top-level schema differs from the strict Task 5 v1 contract")
    if checkpoint["schema_version"] != 1:
        raise ValueError("Checkpoint schema_version must be 1")
    if (checkpoint["task"], checkpoint["positive_label"], checkpoint["input_domain"]) != (
        TASK, POSITIVE_LABEL, INPUT_DOMAIN
    ):
        raise ValueError("Checkpoint target/input-domain identity differs")
    if checkpoint["pretrained_checkpoint"] is not None:
        raise ValueError("Task 5 checkpoint claims forbidden top-level pretrained weights")
    if type(checkpoint["best_epoch"]) is not int or checkpoint["best_epoch"] < 1 or type(checkpoint["seed"]) is not int:
        raise ValueError("Checkpoint epoch/seed metadata is invalid")
    if not isinstance(checkpoint["best_metrics"], dict) or not math.isfinite(
        float(checkpoint["best_metrics"].get("selection_macro_criterion", math.nan))
    ):
        raise ValueError("Checkpoint best_metrics is incomplete")
    digest_keys = (
        "config_sha256", "input_manifest_sha256", "used_train_manifest_sha256", "used_dev_manifest_sha256",
        "used_model_selection_dev_manifest_sha256", "used_report_only_dev_manifest_sha256",
        "task2_source_manifest_sha256", "task2_completion_receipt_sha256",
        "task3_stem_manifest_sha256", "task3_completion_receipt_sha256",
        "fresh_initial_state_sha256",
    )
    if any(not isinstance(checkpoint[key], str) or not re.fullmatch(r"[0-9a-f]{64}", checkpoint[key])
           for key in digest_keys):
        raise ValueError("Checkpoint manifest/initial-state digest metadata is invalid")
    source_hashes = checkpoint["source_files_sha256"]
    required_sources = {
        "scripts/music_fake_model_v1.py", "scripts/component_fake_utils_v1.py",
        "scripts/train_music_fake_v1.py", "scripts/run_music_fake_v1.py",
    }
    if (
        not isinstance(source_hashes, dict)
        or set(source_hashes) != required_sources
        or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
               for value in source_hashes.values())
    ):
        raise ValueError("Checkpoint Task 5 source hash receipt is incomplete")
    binding_keys = {
        "config_sha256", "input_manifest_sha256", "used_train_manifest_sha256", "used_dev_manifest_sha256",
        "used_model_selection_dev_manifest_sha256", "used_report_only_dev_manifest_sha256",
        "task2_source_manifest_sha256", "task2_completion_receipt_sha256",
        "task3_stem_manifest_sha256", "task3_completion_receipt_sha256",
        "source_files_sha256", "fresh_initial_state_sha256",
    }
    if not isinstance(expected_bindings, dict) or set(expected_bindings) != binding_keys:
        raise ValueError("Caller must supply every independent manifest/code/initial-state checkpoint binding")
    stored_bindings = {key: checkpoint[key] for key in binding_keys}
    if stored_bindings != expected_bindings:
        raise ValueError("Checkpoint metadata does not match the caller's independently computed bindings")
    stored_config = checkpoint["model_config"]
    if not isinstance(stored_config, dict):
        raise ValueError("Checkpoint model_config must be an object")
    model, config = build_model(
        width=int(stored_config.get("width", -1)),
        dropout=float(stored_config.get("dropout", math.nan)),
    )
    if stored_config != config:
        raise ValueError("Stored model_config differs from the full frozen Task 5 architecture contract")
    if not isinstance(checkpoint["model_state_dict"], dict):
        raise ValueError("Checkpoint model_state_dict must be an object")
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.to(device).eval()
    return model, {key: value for key, value in checkpoint.items() if key != "model_state_dict"}
