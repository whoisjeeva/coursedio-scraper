import json
import requests
import sys
from collections import OrderedDict
from time import sleep

from core.scraper import Scraper


def main():
    with open("progress_output.json", "r") as f:
        courses = json.load(f, object_pairs_hook=OrderedDict)

    scraper = Scraper()
    print("[ STATUS ] Logging in...")
    scraper.login("33667870", "1609")
    output = []

    for course in courses:
        course_data = {
            "title": course["title"],
            "slug": course["slug"],
            "date_published": course["date_published"],
            "author_name": course["author_name"],
            "author_url": course["author_url"],
            "description": course["description"],
            "excercise_file_url": course["excercise_file_url"],
            "skills": ",".join(course["skills"]),
            "category": course["category"],
            "image": course["image"],
            "videos": []
        }
        output.append(course_data)
        print(f"[ COURSE ] adding course '{course['title']}'...")

        while True:
            try:
                remote_course, _ = scraper.get_course_details_using_session(course["slug"])
                break
            except:
                sleep(2)
        
        for index, video in enumerate(remote_course["videos"]):
            found_video = get_video(video, course["videos"])
            video_slug = video["url"].split("/")[-1]
            video_data = {
                "title": found_video["title"],
                "duration": found_video["duration"],
                "subtitle": found_video["subtitle"],
                "url": found_video["url"],
                "course_slug": course["slug"],
                "video_slug": video_slug,
                "index": index+1
            }
            output[-1]["videos"].append(video_data)
            print(f"[ VIDEO ] adding video '{found_video['title']}'...")
    
    with open("final.json", "w") as f:
        f.write(json.dumps(output))
    print("Done.")



def get_video(remote_video, local_videos):
    found = None
    for v in local_videos:
        if v["title"] == remote_video["title"] and v["duration"] == remote_video["duration"]:
            found = v
            break
        
    return found


if __name__ == "__main__":
    main()
