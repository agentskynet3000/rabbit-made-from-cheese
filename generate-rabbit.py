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


# Stupid/absurd LucasArts-style situations. The rabbit is always the protagonist of something dumb.
SITUATIONS = [
    "trying to use a pay phone with no hands",
    "applying for a job at a cheese shop",
    "waiting for a bus that will never come",
    "attending a seminar about cheese management",
    "getting stuck in a revolving door",
    "filling out a very long form",
    "arguing with a vending machine",
    "reading the terms and conditions",
    "attending his own birthday party alone",
    "stuck in an elevator with a fax machine",
    "trying to return a broken toaster",
    "looking for his keys for the third time",
    "at the DMV for six hours",
    "asking for directions in a foreign country",
    "trying to assemble furniture without instructions",
    "waiting on hold for customer support",
    "pretending to understand a map",
    "caught in a speed trap doing 3mph",
    "accidentally joining a yoga class",
    "trying to fit a sofa through a doorway",
    "standing in the wrong queue at the airport",
    "on a first date that is clearly going badly",
    "explaining himself to a customs officer",
    "attending a mandatory fire safety training",
    "buying milk at 2am from a confused cashier",
    "watching TV in a motel room he can't check out of",
    "at a garage sale trying to sell himself",
    "asking a librarian for a book that doesn't exist",
    "trapped under a pile of junk mail",
    "being towed away while still inside the car",
    "running for a train he clearly won't catch",
    "presenting quarterly results to an empty room",
    "on a broken escalator just standing there",
    "trying to plug in a three-pronged plug in Europe",
    "getting a very bad haircut",
    "at a dog show competing in the wrong category",
    "losing at tic-tac-toe to a child",
    "inside a claw machine looking confused",
    "reading the instructions for a microwave",
    "trying to parallel park a horse",
    "winning an award no one cares about",
    "signing a lease he didn't read",
    "at a museum standing in front of a fire exit",
    "trying to use a coupon that expired in 1987",
    "attending a town hall about a pothole",
    "reporting a noise complaint to an empty desk",
    "taking a personality test online",
    "learning about blockchain at a community center",
    "getting a loyalty card stamped for the first time",
    "in a waiting room where the magazine is from 2004",
]

# Each context is just a name: director/movie, artist/style, or famous person.
# Prompt format: (rabbit made from cheese:1.2), [CONTEXT]
CONTEXTS = [
    # Directors / Films
    "Tarkovsky",
    "Stalker",
    "Ingmar Bergman",
    "Persona",
    "Stanley Kubrick",
    "2001 A Space Odyssey",
    "Werner Herzog",
    "Fitzcarraldo",
    "David Lynch",
    "Mulholland Drive",
    "Wes Anderson",
    "The Grand Budapest Hotel",
    "Wong Kar-wai",
    "In the Mood for Love",
    "Akira Kurosawa",
    "Rashomon",
    "Federico Fellini",
    "8 1/2",
    "Jean-Luc Godard",
    "Breathless",
    "Lars von Trier",
    "Melancholia",
    "Agnès Varda",
    "Cleo from 5 to 7",
    "Pier Paolo Pasolini",
    "Apocalypse Now",
    "Blade Runner",
    "Nosferatu",
    "The Seventh Seal",
    "Metropolis",
    # Artists / Art Styles
    "Caravaggio",
    "Rembrandt",
    "Vermeer",
    "Klimt",
    "Egon Schiele",
    "Francis Bacon",
    "Jean-Michel Basquiat",
    "Andy Warhol",
    "Roy Lichtenstein",
    "Salvador Dali",
    "René Magritte",
    "Giorgio de Chirico",
    "Edward Hopper",
    "Caspar David Friedrich",
    "William Turner",
    "Claude Monet",
    "Paul Cézanne",
    "Henri Matisse",
    "Hieronymus Bosch",
    "Hokusai",
    "ukiyo-e style",
    "bauhaus style",
    "constructivism",
    "Soviet propaganda poster",
    "art nouveau",
    "brutalism",
    "Memphis design",
    "kawaii style",
    "vaporwave",
    "glitch art",
    # Famous People
    "Arnold Schwarzenegger",
    "David Bowie",
    "Freddie Mercury",
    "Keith Richards",
    "Grace Jones",
    "Karl Lagerfeld",
    "Anna Wintour",
    "Marlon Brando",
    "James Dean",
    "Marilyn Monroe",
    "Elvis Presley",
    "Muhammad Ali",
    "Mick Jagger",
    "Iggy Pop",
    "Klaus Kinski",
    "Werner Herzog",
    "Cate Blanchett",
    "Tilda Swinton",
    "Prince",
    "Nina Simone",
    "Miles Davis",
    "Sun Ra",
    "Yoko Ono",
    "Joseph Beuys",
    "Marina Abramović",
    "Elon Musk",
    "Steve Jobs",
    "Pope Francis",
    "Genghis Khan",
    "Napoleon Bonaparte",
    "Cleopatra",
    "Nikola Tesla",
    "Albert Einstein",
    "Karl Marx",
    "Friedrich Nietzsche",
    "Sigmund Freud",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def next_counter() -> int:
    existing = list(IMAGES_DIR.glob("rabbit-*.jpg"))
    return len(existing) + 1


def context_to_slug(context: str) -> str:
    slug = context.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def build_filename(counter: int, context: str) -> str:
    return f"rabbit-{counter:03d}-{context_to_slug(context)}.jpg"


def generate_image(context: str) -> bytes:
    return generate_image_with_context(context)


def generate_image_with_context(context: str, situation: str = None) -> bytes:
    prompt = "(rabbit made from cheese:1.5)"
    payload = {
        "prompt": prompt,
        "negative_prompt": "",
        "steps": 25,
        "cfg_scale": 3,
        "width": 1024,
        "height": 1024,
        "sampler_name": "DPM++ 3M SDE",
        "scheduler": "Normal",
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
    """Insert the new image path into the images array and update OG tags."""
    index_path = REPO_DIR / "index.html"
    content = index_path.read_text()
    img_path = f"images/{filename}"

    # Insert into gallery array (uses unique marker to avoid hitting other arrays)
    new_entry = f'      "{img_path}"'
    content = content.replace(
        '    ]; // END_GALLERY_ARRAY',
        f'{new_entry},\n    ]; // END_GALLERY_ARRAY'
    )

    # Update OG image tags to newest rabbit
    img_url = f"https://rabbit-made-from-cheese.pages.dev/{img_path}"
    content = re.sub(
        r'(<meta property="og:image" content=")[^"]*(")',
        rf'\g<1>{img_url}\g<2>',
        content
    )
    content = re.sub(
        r'(<meta name="twitter:image" content=")[^"]*(")',
        rf'\g<1>{img_url}\g<2>',
        content
    )

    index_path.write_text(content)
    print(f"Updated index.html with {img_path} (OG tags updated)")


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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", help="Force a specific context (e.g. 'Tarkovsky' or 'kawaii style')")
    args = parser.parse_args()

    context = args.context or random.choice(CONTEXTS)
    situation = random.choice(SITUATIONS)
    print(f"Context: {context}")
    print(f"Situation: {situation}")

    counter = next_counter()
    filename = build_filename(counter, context)
    print(f"Filename: {filename}")

    img_bytes = generate_image_with_context(context, situation)
    save_image(img_bytes, filename)
    update_index_html(filename)
    git_push(filename, f"{context} / {situation}")

    print(f"\nDone! rabbit #{counter:03d} — {context} / {situation}")


if __name__ == "__main__":
    main()
