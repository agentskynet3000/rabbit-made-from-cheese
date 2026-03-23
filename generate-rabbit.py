#!/usr/bin/env python3
"""Generate a new rabbit-made-from-cheese image using Stable Diffusion WebUI API."""

import base64
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────

API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
IMAGES_DIR = Path(__file__).parent / "images"
REPO_DIR = Path(__file__).parent
GITHUB_REMOTE = "origin"  # remote is configured locally with credentials

MODEL = "juggernautXL_version6Rundiffusion.safetensors"

SETTINGS = [
    "in the jungle",
    "on the Empire State Building",
    "in the desert",
    "in outer space",
    "underwater",
    "in a medieval castle",
    "at a rave",
    "in a sauna",
    "on the moon",
    "during a thunderstorm",
    "in a library",
    "at a disco",
    "in the Louvre museum",
    "surfing a wave",
    "driving a tractor",
    "at a sushi restaurant",
    "in Times Square",
    "in ancient Rome",
    "in a volcano",
    "at a wedding",
    "on top of the Eiffel Tower",
    "in a washing machine",
    "at a heavy metal concert",
    "inside a fridge",
    "at a yoga class",
    "in the Matrix",
    "on a pirate ship",
    "at a drive-through",
    "inside a pinball machine",
    "at the North Pole",
    "in a bouncy castle",
    "at a black tie gala",
    "inside a giant cake",
    "in a haunted house",
    "at a rodeo",
    "on the International Space Station",
    "in ancient Egypt",
    "at a kebab stand at 3am",
    "in a hedge maze",
    "at a hot dog eating contest",
    "inside a snow globe",
    "at a laundromat",
    "in Jurassic Park",
    "at a game show",
    "on a giant chess board",
    "at Burning Man",
    "in a submarine",
    "at a taxidermy shop",
    "inside a clock tower",
    "at a karaoke bar",
    "on the Great Wall of China",
    "in a zero-gravity chamber",
    "at a demolition derby",
    "inside a supercomputer",
    "in the Vatican",
    "at an IKEA",
    "on a melting iceberg",
    "in a car wash",
    "at a flea market",
    "inside a tornado",
    "at a renaissance fair",
    "in a skatepark",
    "at a silent disco",
    "in a ball pit",
    "at the bottom of the Mariana Trench",
    "inside a lava lamp",
    "at a bingo night",
    "in Chernobyl",
    "on a magic carpet",
    "at a construction site",
    "inside a kaleidoscope",
    "at a retirement home disco",
    "in the Sahara at night",
    "inside a snow avalanche",
    "at a political debate",
    "in a cemetery at midnight",
    "on a rainbow",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def next_counter() -> int:
    existing = list(IMAGES_DIR.glob("rabbit-*.jpg"))
    return len(existing) + 1


def setting_to_slug(setting: str) -> str:
    slug = setting.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def build_filename(counter: int, setting: str) -> str:
    return f"rabbit-{counter:03d}-{setting_to_slug(setting)}.jpg"


def generate_image(setting: str) -> bytes:
    prompt = (
        f"rabbit made from cheese, {setting}, "
        "photorealistic, detailed, high quality, product photography style"
    )
    payload = {
        "prompt": prompt,
        "negative_prompt": "cartoon, sketch, low quality, blurry",
        "steps": 25,
        "cfg_scale": 7,
        "width": 1024,
        "height": 1024,
        "sampler_name": "Euler a",
        "save_images": True,
        "override_settings": {
            "sd_model_checkpoint": MODEL,
        },
    }
    print(f"Generating: {prompt}")
    resp = requests.post(API_URL, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    img_b64 = data["images"][0]
    return base64.b64decode(img_b64)


def save_image(img_bytes: bytes, filename: str) -> Path:
    IMAGES_DIR.mkdir(exist_ok=True)
    dest = IMAGES_DIR / filename
    dest.write_bytes(img_bytes)
    print(f"Saved: {dest}")
    return dest


def update_index_html(filename: str):
    """Insert the new image path into the images array in index.html."""
    index_path = REPO_DIR / "index.html"
    content = index_path.read_text()
    img_path = f"images/{filename}"
    # Insert before the closing bracket of the images array
    new_entry = f'      "{img_path}"'
    content = content.replace(
        '    ];',
        f'{new_entry},\n    ];'
    )
    index_path.write_text(content)
    print(f"Updated index.html with {img_path}")


def git_push(filename: str, setting: str):
    cmds = [
        ["git", "-C", str(REPO_DIR), "add", f"images/{filename}", "index.html"],
        ["git", "-C", str(REPO_DIR), "commit", "-m", f"Add rabbit: {setting}"],
        ["git", "-C", str(REPO_DIR), "push", GITHUB_REMOTE, "main"],
    ]
    for cmd in cmds:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            # Don't hard-fail on push errors (e.g. branch name issues)
            if "commit" in cmd or "push" in cmd:
                print("Warning: command failed, continuing...")
            else:
                raise RuntimeError(f"git command failed: {' '.join(cmd)}")
        else:
            print(result.stdout.strip())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    setting = random.choice(SETTINGS)
    print(f"Setting: {setting}")

    counter = next_counter()
    filename = build_filename(counter, setting)
    print(f"Filename: {filename}")

    img_bytes = generate_image(setting)
    save_image(img_bytes, filename)
    update_index_html(filename)
    git_push(filename, setting)

    print(f"\nDone! rabbit #{counter:03d} — {setting}")


if __name__ == "__main__":
    main()
