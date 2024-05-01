import json
import uuid
import os
from tqdm import tqdm
import requests

from core.github import Github
from core.npm import Npm
from core.scraper import Scraper


GLOBAL_DATA = []
GLOBAL_SLUGS = []


def main():
    with open("data.json", "r") as f:
        data = json.load(f)
    
    progress_data = []
    if os.path.exists("progress_output.json"):
        with open("progress_output.json", "r") as f:
            progress_data = json.loads(f.read())
    
    for d in progress_data:
        is_downloaded = True
        for v in d["videos"]:
            if "linkedin" in v["url"]:
                is_downloaded = False
                break
        if is_downloaded:
            GLOBAL_SLUGS.append(d["slug"])
            GLOBAL_DATA.append(d)
    
    # github = Github()
    npm = Npm()
    scraper = Scraper()
    print("[ STATUS ] Logging in...")
    scraper.login("33667870", "1609")

    for d in data:
        category = d["category"]
        for c in d["courses"]:
            if c["slug"] in GLOBAL_SLUGS:
                print("[ STATUS ] Skipping course details for '" + str(c["title"]) + "'...")
                continue
            print("[ STATUS ] Getting course details for '" + str(c["title"]) + "'...")
            try:
                course, _ = scraper.get_course_details_using_session(c["slug"])
            except Exception as e:
                print(f"[ ERROR ] {e}")
                continue
            course_slug = course["slug"]
            print("[ STATUS ] Getting excercise files for '" + str(c["title"]) + "'...")
            excercise_files = scraper.get_exercise_files(course_slug)
            if len(excercise_files) > 0:
                course["excercise_file_url"] = excercise_files[0]["url"]
            else:
                course["excercise_file_url"] = None
            course["skills"] = c["skills"]
            course["category"] = category
            
            
            print("[ STATUS ] Creating repo for course '" + str(c["title"]) + "'...")
            # repo = github.create_repo(uuid.uuid4().hex)
            if not os.path.exists(course_slug):
                os.mkdir(course_slug)
            
            # if repo is None:
            #     raise Exception("Repo failed to create")
            
            if course["excercise_file_url"] is not None:
                download_file(scraper.session, course["excercise_file_url"], f"{course_slug}/exercise.zip")
                print("[ STATUS ] Uploading excercise files for '" + str(course["title"]) + "'...")
                # github.upload("ex.zip", f"{repo}.mp4", repo)
                course["excercise_file_url"] = f"https://unpkg.com/coursedio-{course_slug}@1.0.1/exercise.zip"

            for i, video in enumerate(course["videos"]):
                # if os.path.exists("v.mp4"):
                #     os.remove("v.mp4")
                    
                # if os.path.exists("subtitle.srt"):
                #     os.remove("subtitle.srt")
                
                url = video["url"]
                video_slug = url.split("/")[-1]
                video_details = scraper.get_video_details(course_slug, video_slug)
                
                subtitle_url = video_details["subtitle"]
                video_url = get_high_quality_video(video_details["streams"])["url"]
                # upload video and subtitle and replace url

                
                download_file(scraper.session, video_url, f"{course_slug}/{i}.mp4")
                print("[ STATUS ] Uploading video '" + str(video["title"]) + "' from '" + str(c["title"]) + "'...")
                # github.upload("v.mp4", f"{filename}.mp4", repo)
                video_url = f"https://unpkg.com/coursedio-{course_slug}@1.0.1/{i}.mp4"
                
                try:
                    download_file(scraper.session, subtitle_url, f"{course_slug}/{i}.srt")
                    print("[ STATUS ] Uploading subtitle '" + str(video["title"]) + "' from '" + str(c["title"]) + "'...")
                    # github.upload("subtitle.srt", f"{filename}.srt", repo)
                    subtitle_url = f"https://unpkg.com/coursedio-{course_slug}@1.0.1/{i}.srt"
                except Exception as e:
                    print(f"[ ERROR ] {e}")
                    subtitle_url = None
                
                video["url"] = video_url
                video["subtitle"] = subtitle_url
            
            npm.publish(course_slug, course_slug)
            GLOBAL_DATA.append(course)
            with open("progress_output.json", "w+") as f:
                f.write(json.dumps(GLOBAL_DATA))
    
    with open("final_data.json", "w+") as f:
        f.write(json.dumps(GLOBAL_DATA))


def download_file(session, url, filepath):
    try:
        response = session.get(url, stream=True)

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
        download_file(session, url, filepath)


def get_high_quality_video(streams):
    stream = streams[0]
    height = stream["height"]
    
    for s in streams:
        if height == 720:
            break
        if s["height"] > height:
            stream = s
            height = s["height"]
    
    return stream


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("progress_output.json", "w+") as f:
            f.write(json.dumps(GLOBAL_DATA))
        raise e
