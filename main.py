import os
import re
import shutil
import subprocess
import pandas as pd
import json
import sys


# === Read CSV with video titles and URLs ===
df = pd.read_csv("topstep.csv")

def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters for Windows/Linux/Mac."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(BASE_DIR, "csv_study")


def download_video(url: str, folder: str, cookies: str = "cookies.txt") -> str:
    """
    Download only video (no audio) using yt-dlp via subprocess.
    Saves the file in the given folder with the folder name as the filename.
    Also copies the template into the folder after download.
    Returns the full path of the downloaded video file.
    """
    # Ensure folder exists
    os.makedirs(folder, exist_ok=True)
    folder_name = os.path.basename(os.path.normpath(folder))
    output_template = os.path.join(folder, f"{folder_name}.%(ext)s")

    # Download video
    cmd = [
        "yt-dlp",
        "-f", "bestvideo",            # video only
        "--cookies", cookies,         # include cookies
        "-o", output_template,        # output file path
        url
    ]
    subprocess.run(cmd, check=True)

    # Find downloaded video file
    video_files = [f for f in os.listdir(folder) if f.endswith((".mp4", ".mkv", ".webm"))]
    if not video_files:
        raise FileNotFoundError(f"No video downloaded in {folder}")
    video_file = os.path.join(folder, video_files[0])

    # Save metadata
    metadata = {"video_name": folder, "video_title": folder, "video_url": url}
    with open(os.path.join(folder, "info.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Copy template into the folder (without overwriting)
    for item in os.listdir(TEMPLATE):
        src = os.path.join(TEMPLATE, item)
        dst = os.path.join(folder, item)
        if os.path.isdir(src):
            if not os.path.exists(dst):
                shutil.copytree(src, dst)
        else:
            if not os.path.exists(dst):
                shutil.copy2(src, dst)

    print(f"[download_video] {folder} ready with template + video")
    return video_file


import sys
import importlib.util
from pathlib import Path

def process_video(folder: str, video_file: str):
    """
    Runs run.py inside the given folder without using subprocess.
    """
    run_path = Path(folder) / "run.py"
    if not run_path.exists():
        raise FileNotFoundError(f"{run_path} not found")

    # Load run.py dynamically
    spec = importlib.util.spec_from_file_location("run_module", run_path)
    run_module = importlib.util.module_from_spec(spec)
    sys.modules["run_module"] = run_module
    spec.loader.exec_module(run_module)

    if not hasattr(run_module, "main"):
        raise AttributeError("run.py must define a function named 'main'")

    # Save old sys.argv so we don’t mess up the caller
    old_argv = sys.argv[:]
    sys.argv = [str(run_path), video_file]

    try:
        run_module.main()
        print("[process_video] Completed successfully")
    except Exception as e:
        print(f"[process_video] Error: {e}")
        raise
    finally:
        # Restore argv
        sys.argv = old_argv




# === Main execution (sequential) ===
finished_file = "finished.txt"

# Load already processed folders into a set
if os.path.exists(finished_file):
    with open(finished_file, "r") as f:
        finished = {line.strip().split()[0] for line in f if line.strip()}
else:
    finished = set()

for _, row in df.iterrows():
    title = row["Title"]
    url = row["URL"]
    folder = sanitize_filename(title).replace(" ", "_")

    if folder in finished:
        print(f"[SKIP] {folder} already processed")
        continue

    print("\n=== Starting:", folder, "===")
    try:
        video_file = download_video(url, folder)
        process_video(folder, video_file)

        with open(finished_file, "a") as f:
            f.write(folder + " done\n")

    except Exception as e:
        print(f"[ERROR] {folder} failed:", e)

# terminate_instance.py

def shutdown_instance():
    try:
        print("Shutting down the instance...")
        # run the shutdown command
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
    except Exception as e:
        print(f"Failed to shutdown: {e}")

shutdown_instance()
