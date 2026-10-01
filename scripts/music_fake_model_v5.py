#!/usr/bin/env python3
"""Compact raw-audio log-spectrogram model for MUSIC_FAKE v5."""
from __future__ import annotations

import math

import torch
from torch import nn


MODEL_ID = "music_fake_logspec_resnet_v5_raw"
TASK = "MUSIC_FAKE"
POSITIVE_LABEL = "MUSIC_FAKE=1"
INPUT_DOMAIN = "raw_mono_audio_16k"
SAMPLE_RATE_HZ = 16_000
CLIP_SAMPLES = 64_600
EXPECTED_PARAMETER_COUNT = 1_241_825


def normalization(channels: int) -> nn.Module:
    return nn.GroupNorm(math.gcd(8, channels), channels)


def deterministic_frequency_pool(tensor: torch.Tensor, bins: int = 4) -> torch.Tensor:
    """Match adaptive average pooling bins without its nondeterministic CUDA backward."""
    length = tensor.shape[-2]
    pieces = []
    for index in range(bins):
        start = (index * length) // bins
        end = ((index + 1) * length + bins - 1) // bins
        pieces.append(tensor[..., start:end, :].mean(dim=-2, keepdim=True))
    return torch.cat(pieces, dim=-2)


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


class MusicFakeLogSpecResNetV5(nn.Module):
    def __init__(self, width: int = 24, dropout: float = 0.15):
        super().__init__()
        if width != 24:
            raise ValueError("v5 width is frozen at 24")
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
            blocks.extend([
                ResidualBlock(incoming, outgoing, 1 if stage == 0 else 2),
                ResidualBlock(outgoing, outgoing),
            ])
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
        if waveforms.ndim != 2 or waveforms.shape[-1] < 512:
            raise ValueError("waveforms must have shape [batch, samples>=512]")
        with torch.autocast(device_type=waveforms.device.type, enabled=False):
            spectrum = torch.stft(
                waveforms.float(), n_fft=512, hop_length=256, win_length=512,
                window=self.window.float(), center=False, return_complex=True,
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

        statistics = torch.cat((
            deterministic_frequency_pool(temporal_mean),
            deterministic_frequency_pool(temporal_std),
        ), dim=1)
        return self.head(statistics.flatten(1)).squeeze(1)


def build_model(width: int = 24, dropout: float = 0.15) -> tuple[MusicFakeLogSpecResNetV5, dict]:
    model = MusicFakeLogSpecResNetV5(width=width, dropout=dropout)
    count = sum(parameter.numel() for parameter in model.parameters())
    if count != EXPECTED_PARAMETER_COUNT:
        raise RuntimeError(f"Frozen v5 parameter count changed: {count} != {EXPECTED_PARAMETER_COUNT}")
    config = {
        "model_id": MODEL_ID,
        "class": "MusicFakeLogSpecResNetV5",
        "task": TASK,
        "positive_label": POSITIVE_LABEL,
        "input_domain": INPUT_DOMAIN,
        "pretrained_checkpoint": None,
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
