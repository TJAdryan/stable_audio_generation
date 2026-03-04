import torch
import torchaudio
import os
import time
import sys
import soundfile as sf
import numpy as np
from stable_audio_tools import get_pretrained_model
from stable_audio_tools.inference.generation import generate_diffusion_cond

def generate_stable_audio(prompt, seconds=30, steps=200, cfg_scale=8.5):
    # 1. Clear Cache
    torch.cuda.empty_cache()

    MAX_SECONDS = 47
    target_seconds = min(seconds, MAX_SECONDS)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- Smooth Gen on {device.upper()} ---")

    # 2. Load Model
    model, model_config = get_pretrained_model("stabilityai/stable-audio-open-1.0")
    model = model.to(device)
    
    sample_rate = model_config["sample_rate"]
    sample_size = model_config["sample_size"]

    # Use a descriptive prompt to help the sampler
    smooth_prompt = f"{prompt}, smooth production, high quality, studio recording"

    conditioning = [{
        "prompt": smooth_prompt,
        "seconds_start": 0,
        "seconds_total": target_seconds
    }]

    print(f"--- Generating {target_seconds}s at {steps} steps (Lower CFG for smoothness) ---")
    
    with torch.no_grad():
        # generate_diffusion_cond uses the model's default sampler
        output = generate_diffusion_cond(
            model,
            steps=steps,
            cfg_scale=cfg_scale,
            conditioning=conditioning,
            sample_size=sample_size,
            device=device
        )

    # 3. Post-Process & Smoothing
    # Convert to float32 and move to CPU
    output = output.to(torch.float32).squeeze(0).cpu().numpy()
    
    # Transpose for soundfile: (Channels, Samples) -> (Samples, Channels)
    if output.ndim == 2:
        output = output.T

    # 4. Normalize to -1dB to prevent digital "choppiness" from clipping
    max_val = np.max(np.abs(output))
    if max_val > 0:
        output = output / max_val * 0.9

    # 5. Trim to requested duration
    target_samples = int(target_seconds * sample_rate)
    output = output[:target_samples, :]

    # 6. Save
    os.makedirs("exports", exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_prompt = prompt.replace(" ", "_")[:30].strip("_")
    out_path = f"exports/smooth_{timestamp}_{clean_prompt}.wav"
    
    sf.write(out_path, output, sample_rate)
    print(f"DONE: {out_path}")

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "Alt rock drums and bass"
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    generate_stable_audio(p, seconds=s)