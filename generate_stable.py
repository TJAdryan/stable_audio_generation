import torch
import torchaudio
import os
import time
import sys
import subprocess
import soundfile as sf
from stable_audio_tools import get_pretrained_model
from stable_audio_tools.inference.generation import generate_diffusion_cond

def clear_gpu_memory():
    """Finds and kills all python processes currently using the NVIDIA GPU."""
    print("--- Clearing GPU Processes ---")
    try:
        # This command finds PIDs using the GPU and kills them
        # fuser returns non-zero if no processes found, so we catch the error
        subprocess.run("fuser -v /dev/nvidia* 2>/dev/null | awk '{print $2}' | xargs -r kill -9", shell=True)
        torch.cuda.empty_cache()
        time.sleep(1) # Brief pause for hardware to release memory
    except Exception as e:
        print(f"Note: GPU cleanup skipped or no processes found: {e}")

def generate_stable_audio(prompt, seconds=30, steps=100, cfg_scale=7):
    # Standard cleanup before loading the model
    clear_gpu_memory()

    MAX_SECONDS = 47
    target_seconds = min(seconds, MAX_SECONDS)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- Running on {device.upper()} ---")

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

    print(f"--- Generating (Steps: {steps}, Request: {target_seconds}s): {prompt} ---")
    
    with torch.no_grad():
        output = generate_diffusion_cond(
            model,
            steps=steps,
            cfg_scale=cfg_scale,
            conditioning=conditioning,
            sample_size=sample_size,
            device=device
        )

    # Post-process: Normalize and convert to NumPy
    output = output.to(torch.float32).div(torch.max(torch.abs(output))).clamp(-1, 1)
    output = output.squeeze(0).cpu().numpy()
    
    # Transpose for soundfile: (Channels, Samples) -> (Samples, Channels)
    if output.ndim == 2:
        output = output.T

    # Trim to requested duration
    target_samples = int(target_seconds * sample_rate)
    if output.shape[0] > target_samples:
        print(f"--- Trimming output to {target_seconds}s ---")
        output = output[:target_samples, :]

    # Save logic
    os.makedirs("exports", exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_prompt = prompt.replace(" ", "_")[:30].strip("_")
    out_path = f"exports/stable_{timestamp}_{clean_prompt}.wav"
    
    sf.write(out_path, output, sample_rate)
    print(f"DONE: {out_path} ({sample_rate}Hz Stereo)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python generate_stable.py 'Your prompt' [seconds]")
        sys.exit(1)
        
    user_prompt = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    generate_stable_audio(user_prompt, seconds=duration)