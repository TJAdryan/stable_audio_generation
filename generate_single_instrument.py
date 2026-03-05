import argparse
import os
import time

import numpy as np
import soundfile as sf
import torch
from stable_audio_tools import get_pretrained_model
from stable_audio_tools.inference.generation import generate_diffusion_cond


def build_single_instrument_prompt(instrument, style=""):
    instrument = instrument.strip()
    parts = [
        f"solo {instrument}",
        "single instrument",
        "no accompaniment",
        "no drums",
        "no bass",
        "no vocals",
        "no crowd noise",
        "clean studio recording",
        "high quality production",
    ]

    if style and style.strip():
        parts.insert(1, style.strip())

    return ", ".join(parts)


def generate_single_instrument_audio(instrument, style="", seconds=30, steps=200, cfg_scale=8.5):
    torch.cuda.empty_cache()

    max_seconds = 47
    target_seconds = min(seconds, max_seconds)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- Single Instrument Gen on {device.upper()} ---")

    model, model_config = get_pretrained_model("stabilityai/stable-audio-open-1.0")
    model = model.to(device)

    sample_rate = model_config["sample_rate"]
    sample_size = model_config["sample_size"]

    prompt = build_single_instrument_prompt(instrument, style)

    conditioning = [{
        "prompt": prompt,
        "seconds_start": 0,
        "seconds_total": target_seconds,
    }]

    print(f"--- Generating {target_seconds}s at {steps} steps: {prompt} ---")

    with torch.no_grad():
        output = generate_diffusion_cond(
            model,
            steps=steps,
            cfg_scale=cfg_scale,
            conditioning=conditioning,
            sample_size=sample_size,
            device=device,
        )

    output = output.to(torch.float32).squeeze(0).cpu().numpy()

    if output.ndim == 2:
        output = output.T

    max_val = np.max(np.abs(output))
    if max_val > 0:
        output = output / max_val * 0.9

    target_samples = int(target_seconds * sample_rate)
    output = output[:target_samples, :]

    os.makedirs("exports", exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_instrument = instrument.replace(" ", "_")[:20].strip("_")
    out_path = f"exports/single_{timestamp}_{clean_instrument}.wav"

    sf.write(out_path, output, sample_rate)
    print(f"DONE: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a single-instrument track with Stable Audio Open")
    parser.add_argument("instrument", type=str, help="Instrument to generate (example: piano)")
    parser.add_argument("seconds", nargs="?", type=int, default=30, help="Target duration in seconds (max 47)")
    parser.add_argument("--style", type=str, default="", help="Optional style descriptors")
    parser.add_argument("--steps", type=int, default=200, help="Diffusion steps")
    parser.add_argument("--cfg-scale", type=float, default=8.5, help="Prompt guidance scale")

    args = parser.parse_args()

    generate_single_instrument_audio(
        instrument=args.instrument,
        style=args.style,
        seconds=args.seconds,
        steps=args.steps,
        cfg_scale=args.cfg_scale,
    )
