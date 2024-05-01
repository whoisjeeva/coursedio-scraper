import json
import sys
import os
from tqdm import tqdm
import requests

from core.github import Github
from core.npm import Npm
from core.scraper import Scraper
from core.argparse import ArgParse


GLOBAL_DATA = []
GLOBAL_SLUGS = []


def main():
    parser = ArgParse(argument_space_count=20, usage="coursedio [options]")
    parser.add_argument(["--help", "-h"], description="show help", is_flag=True)
    parser.add_argument(["--slug"], description="course slug")
    parser.add_argument(["--category"], description="course category")
    parser.add_argument(["--skills"], description="course skills")
    args = parser.parse()
    
    if args.help:
        parser.print_help()
        sys.exit(0)

    if args.slug:
        data = [{
            "category": args.category,
            "courses": [{
                "slug": args.slug,
                "skills": args.skills.split(",")
            }]
        }]
    else:
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
                print("[ STATUS ] Skipping course details for '" + str(c["slug"]) + "'...")
                continue
            print("[ STATUS ] Getting course details for '" + str(c["slug"]) + "'...")
            try:
                course, _ = scraper.get_course_details_using_session(c["slug"])
            except Exception as e:
                print(f"[ ERROR ] {e}")
                continue
            course_slug = course["slug"]
            print("[ STATUS ] Getting excercise files for '" + str(c["slug"]) + "'...")
            excercise_files = scraper.get_exercise_files(course_slug)
            if len(excercise_files) > 0:
                course["excercise_file_url"] = excercise_files[0]["url"]
            else:
                course["excercise_file_url"] = None
            course["skills"] = c["skills"]
            course["category"] = category
            
            
            print("[ STATUS ] Creating repo for course '" + str(c["slug"]) + "'...")
            # repo = github.create_repo(uuid.uuid4().hex)
            
            # if repo is None:
            #     raise Exception("Repo failed to create")
            
            if course["excercise_file_url"] is not None:
                folder = f"coursedio-{course_slug}-excercise"
                if not os.path.exists(folder):
                    os.mkdir(folder)
                download_file(scraper.session, course["excercise_file_url"], f"{folder}/exercise.zip")
                print("[ STATUS ] Uploading excercise files for '" + str(course["title"]) + "'...")
                # github.upload("ex.zip", f"{repo}.mp4", repo)
                npm.publish(folder, folder)
                course["excercise_file_url"] = f"https://unpkg.com/{folder}@1.0.1/exercise.zip"
            else:
                course["excercise_file_url"] = None

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

                folder = f"coursedio-{course_slug}-{video_slug}"
                if not os.path.exists(folder):
                    os.mkdir(folder)
                download_file(scraper.session, video_url, f"{folder}/video.mp4")
                print("[ STATUS ] Uploading video '" + str(video["title"]) + "' from '" + str(c["slug"]) + "'...")
                # github.upload("v.mp4", f"{filename}.mp4", repo)
                video_url = f"https://unpkg.com/{folder}@1.0.1/video.mp4"
                
                try:
                    download_file(scraper.session, subtitle_url, f"{folder}/subtitle.srt")
                    print("[ STATUS ] Uploading subtitle '" + str(video["title"]) + "' from '" + str(c["slug"]) + "'...")
                    subtitle_url = f"https://unpkg.com/{folder}@1.0.1/subtitle.srt"
                except Exception as e:
                    print(f"[ ERROR ] {e}")
                    subtitle_url = None
                
                video["url"] = video_url
                video["subtitle"] = subtitle_url
                npm.publish(folder, folder)
            
            GLOBAL_DATA.append(course)
            with open("progress_output.json", "w+") as f:
                f.write(json.dumps(GLOBAL_DATA))
                
            # input("The course '" + course["title"] + "' is done, press enter to continue...")
    
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
