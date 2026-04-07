import torch
import os
import time
import sys
import soundfile as sf
import numpy as np
from stable_audio_tools import get_pretrained_model
from stable_audio_tools.inference.generation import generate_diffusion_cond

JAZZ_PROMPT = (
    "slow jazz beat, brushed snare drums, upright double bass, jazz piano comping, "
    "warm Rhodes, mellow trumpet, swing feel, 60 BPM, late night jazz club, "
    "smooth and relaxed, high quality studio recording"
)

def generate_jazz_beat(prompt=JAZZ_PROMPT, seconds=45, steps=200, cfg_scale=8.0):
    torch.cuda.empty_cache()

    MAX_SECONDS = 47
    target_seconds = min(seconds, MAX_SECONDS)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- Jazz Beat Gen on {device.upper()} ---")
    print(f"--- Prompt: {prompt} ---")

    # Load model
    model, model_config = get_pretrained_model("stabilityai/stable-audio-open-1.0")
    model = model.to(device)

    sample_rate = model_config["sample_rate"]
    sample_size = model_config["sample_size"]

    conditioning = [{
        "prompt": prompt,
        "seconds_start": 0,
        "seconds_total": target_seconds
    }]

    print(f"--- Generating {target_seconds}s at {steps} steps, CFG {cfg_scale} ---")

    with torch.no_grad():
        output = generate_diffusion_cond(
            model,
            steps=steps,
            cfg_scale=cfg_scale,
            conditioning=conditioning,
            sample_size=sample_size,
            device=device
        )

    # Post-process
    output = output.to(torch.float32).squeeze(0).cpu().numpy()

    if output.ndim == 2:
        output = output.T  # (Channels, Samples) -> (Samples, Channels)

    # Normalize to -1 dB
    max_val = np.max(np.abs(output))
    if max_val > 0:
        output = output / max_val * 0.9

    # Trim to target duration
    target_samples = int(target_seconds * sample_rate)
    output = output[:target_samples]

    # Save
    os.makedirs("exports", exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = f"exports/jazz_beat_{timestamp}.wav"

    sf.write(out_path, output, sample_rate)
    print(f"DONE: {out_path}")

if __name__ == "__main__":
    custom_prompt = sys.argv[1] if len(sys.argv) > 1 else JAZZ_PROMPT
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    generate_jazz_beat(prompt=custom_prompt, seconds=duration)
