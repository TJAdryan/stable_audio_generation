# Stable Audio Generation

Generated audio files are written to `exports/`.

Git tracks the `exports/` directory via `exports/.gitkeep`, but ignores generated audio files inside it. This keeps local renders on disk without committing large binary outputs.  This is purely speculative but there is room for improvement here, I am looking for other projects that might have gone a little further and to make sure I am not just repeating what others have already provided.adding llm responders



## Generate Audio

General usage:

`uv run python generate_hifi_stable.py "your prompt" 30`

Dedicated single-instrument generation:

`uv run python generate_single_instrument.py piano 30`

Single-instrument with extra style descriptors:

`uv run python generate_single_instrument.py trumpet 25 --style "warm jazz tone, intimate room"`

## Generate Walking Bass MIDI (Loop for REAPER)

Create a loop-ready walking bass MIDI file:

`uv run python generate_walking_bass.py --key C --bpm 120 --bars 12`

Example in a minor key:

`uv run python generate_walking_bass.py --key Amin --bpm 100 --bars 8`

The script writes `.mid` files into `exports/` by default. In REAPER, drag the generated MIDI onto a bass instrument track and enable item looping (or duplicate the item) to repeat it.
