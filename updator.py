import json
import requests
from tqdm import tqdm
import os
from moviepy.editor import VideoFileClip

from core.npm import Npm


def main():
    with open("progress_output.json", "r") as f:
        data = json.load(f)

    npm = Npm("1.0.2")

    for d in data:
        for video in d["videos"]:
            folder = video["url"].split("@")[0].split("/")[-1]
            if video["url"].endswith(".mp4"):
                print(folder)
                os.mkdir(folder)
                download_file(video["url"], f"{folder}/video.mp4")
                download_file(video["subtitle"], f"{folder}/subtitle.srt")
                videoClip = VideoFileClip(f"{folder}/video.mp4")
                videoClip.write_videofile(f"{folder}/video.webm", threads = 8, fps=24)
                os.remove(f"{folder}/video.mp4")
                npm.publish(folder, folder)
                video["url"] = f"https://unpkg.com/{folder}@1.0.2/video.webm"
                video["subtitle"] = f"https://unpkg.com/{folder}@1.0.2/subtitle.srt"
                
                with open("updated.json", "w+") as f:
                    f.write(json.dumps(data))

    with open("updated.json", "w+") as f:
        f.write(json.dumps(data))
    print("Done.")


def download_file(url, filepath):
    try:
        response = requests.get(url, stream=True)

        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024

        with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
            with open(filepath, "wb") as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)

        if total_size != 0 and progress_bar.n != total_size:
            raise RuntimeError("Could not download file")
    except requests.exceptions.ChunkedEncodingError:
        download_file(url, filepath)
