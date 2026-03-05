# Stable Audio Generation

Generated audio files are written to `exports/`.

Git tracks the `exports/` directory via `exports/.gitkeep`, but ignores generated audio files inside it. This keeps local renders on disk without committing large binary outputs.

## Generate Audio

General usage:

`uv run python generate_hifi_stable.py "your prompt" 30`

Dedicated single-instrument generation:

`uv run python generate_single_instrument.py piano 30`

Single-instrument with extra style descriptors:

`uv run python generate_single_instrument.py trumpet 25 --style "warm jazz tone, intimate room"`
