import json
from dataclasses import dataclass, asdict
from evilkode import Observation
from utils import observations, passcode_generator, ShuffleTypes
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Iterable

# Project root = parent of *this* file's directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "example" / "obs_json"
PNG_DIR = PROJECT_ROOT / "example" / "obs_png"

@dataclass
class ObservationSequence:
    target_passcode: list[int]
    observations: list[Observation]

def new_observation_sequence(
        number_of_keys: int,
        properties_per_key: int,
        passcode_len: int,
        complexity: int,
        disparity: int,
        numb_runs: int,
) -> ObservationSequence:
    passcode = passcode_generator(number_of_keys, properties_per_key, passcode_len, complexity, disparity)
    obs_seq = ObservationSequence(target_passcode=passcode, observations=[])
    obs_gen = observations(
        target_passcode=passcode,
        number_of_keys=number_of_keys,
        properties_per_key=properties_per_key,
        min_complexity=complexity,
        min_disparity=disparity,
        shuffle_type=ShuffleTypes.FULL_SHUFFLE,
        number_of_observations=numb_runs,
    )
    for obs in obs_gen:
        obs.keypad = obs.keypad.tolist()
        obs_seq.observations.append(obs)

    return obs_seq

def _next_json_filename(base_dir: Path) -> Path:
    """Find the next available observation_X.json file in base_dir."""
    counter = 1
    while True:
        candidate = base_dir / f"observation_{counter}.json"
        if not candidate.exists():
            return candidate
        counter += 1

def save_observation_sequence_to_json(seq: ObservationSequence, filename: Path | None = None) -> None:
    """
    Save ObservationSequence to JSON.
    - If filename is None, put it under PROJECT_ROOT/output/obs_json/ as observation_{n}.json
    - Creates directory if needed
    """
    if filename is None:
        base_dir =  OUTPUT_DIR
        base_dir.mkdir(parents=True, exist_ok=True)
        filename = _next_json_filename(base_dir)
    else:
        filename.parent.mkdir(parents=True, exist_ok=True)

    with filename.open("w", encoding="utf-8") as f:
        json.dump(asdict(seq), f, indent=4)

# ---------- Helpers ----------
def _load_font(preferred: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try a preferred TTF, fall back to common monospace, then PIL default."""
    candidates = [
        preferred,
        "DejaVuSansMono.ttf",       # common on Linux
        "Consolas.ttf",             # Windows
        "Menlo.ttc", "Menlo.ttf",   # macOS
        "Courier New.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    """Get (w, h) using font bbox for accurate layout."""
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top

def _join_nums(nums: Iterable[int]) -> str:
    return " ".join(str(n) for n in nums)

def _next_available_path(path: Path) -> Path:
    """If path exists, append _1, _2, ..."""
    if not path.exists():
        return path
    base, suffix = path.stem, path.suffix or ".png"
    i = 1
    while True:
        candidate = path.with_name(f"{base}_{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1

# ---------- Core rendering ----------
def render_observation_to_png(
    target_passcode: list[int],
    obs: Observation,
    out_path: Path,
    *,
    header_font_name: str = "DejaVuSans.ttf",
    body_font_name: str = "DejaVuSans.ttf",
    header_size: int = 28,
    body_size: int = 24,
    margin: int = 32,
    row_padding_xy: tuple[int, int] = (16, 12),   # (x, y) padding inside row box
    row_spacing: int = 14,
    header_spacing: int = 10,
    section_spacing: int = 18,
    bg_color: str = "white",
    fg_color: str = "black",
    row_fill: str = "#f7f7f7",
    row_outline: str = "#222222",
):
    """
    Render a single observation:
    - Top lines:
        Target Passcode: {target}
        Selected Keys:   {selected keys}
    - Then a stack of row boxes representing the keypad rows.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path = _next_available_path(out_path)

    # Fonts
    header_font = _load_font(header_font_name, header_size)
    body_font = _load_font(body_font_name, body_size)

    # Prepare strings
    header1 = f"Target Passcode: {_join_nums(target_passcode)}"
    header2 = f"Selected Keys:  {_join_nums(obs.key_selection)}"
    row_texts = [_join_nums(row) for row in obs.keypad]

    # Measure to compute canvas size
    # Provisional image for measurement
    temp_img = Image.new("RGB", (1, 1), bg_color)
    d = ImageDraw.Draw(temp_img)

    h1_w, h1_h = _text_size(d, header1, header_font)
    h2_w, h2_h = _text_size(d, header2, header_font)

    row_text_sizes = [_text_size(d, t, body_font) for t in row_texts]
    row_box_widths = [tw + 2 * row_padding_xy[0] for (tw, th) in row_text_sizes]
    row_box_heights = [th + 2 * row_padding_xy[1] for (tw, th) in row_text_sizes]

    content_width = max([h1_w, h2_w] + (row_box_widths or [0]))
    total_rows_height = sum(row_box_heights) + row_spacing * max(0, len(row_box_heights) - 1)

    width = content_width + 2 * margin
    height = (
        margin
        + h1_h
        + header_spacing
        + h2_h
        + section_spacing
        + total_rows_height
        + margin
    )

    # Create final image
    img = Image.new("RGB", (max(width, 300), max(height, 200)), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw headers
    x = margin
    y = margin
    draw.text((x, y), header1, font=header_font, fill=fg_color)
    y += h1_h + header_spacing
    draw.text((x, y), header2, font=header_font, fill=fg_color)
    y += h2_h + section_spacing

    # Draw row boxes with evenly spaced numbers
    max_box_width = max(row_box_widths) if row_box_widths else 0
    for row, box_h in zip(obs.keypad, row_box_heights):
        box_left = x
        box_top = y
        box_right = x + max_box_width
        box_bottom = y + box_h

        # draw row rectangle
        draw.rectangle(
            [box_left, box_top, box_right, box_bottom],
            fill=row_fill,
            outline=row_outline,
            width=2
        )

        # evenly spaced numbers
        n = len(row)
        if n > 0:
            available_width = max_box_width - 2 * row_padding_xy[0]
            spacing = available_width / (n + 1)

            for idx, num in enumerate(row, start=1):
                num_text = str(num)
                num_w, num_h = _text_size(draw, num_text, body_font)
                num_x = box_left + row_padding_xy[0] + spacing * idx - num_w / 2
                num_y = box_top + (box_h - num_h) // 2
                draw.text((num_x, num_y), num_text, font=body_font, fill=fg_color)

        y = box_bottom + row_spacing

    img.save(out_path, format="PNG")

def _next_run_dir(base_dir: Path) -> Path:
    """Find the next available run directory under base_dir (run_001, run_002, ...)."""
    counter = 1
    while True:
        run_dir = base_dir / f"run_{counter:03d}"
        if not run_dir.exists():
            run_dir.mkdir(parents=True)
            return run_dir
        counter += 1

def render_sequence_to_pngs(seq: ObservationSequence, out_dir: Path | None = None) -> None:
    """
    Render each observation to its own PNG inside a fresh run directory.
    Default: PROJECT_ROOT/output/obs_png/run_XXX/observation_001.png
    """
    base_dir = PNG_DIR if out_dir is None else out_dir
    base_dir.mkdir(parents=True, exist_ok=True)

    # Create a fresh run dir
    run_dir = _next_run_dir(base_dir)

    for i, obs in enumerate(seq.observations, start=1):
        filename = run_dir / f"observation_{i:03d}.png"
        render_observation_to_png(seq.target_passcode, obs, filename)
if __name__ == "__main__":
    obs_seq = new_observation_sequence(6, 9,4,0,0,numb_runs=50)
    save_observation_sequence_to_json(obs_seq)
    render_sequence_to_pngs(obs_seq)