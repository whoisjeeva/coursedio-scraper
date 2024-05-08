import json
import requests



def main():
    with open("progress_output.json", "r") as f:
        data = json.load(f)


    for d in data:
        for video in d["videos"]:
            if video["url"].endswith(".mp4"):
                print(video["url"])
                r = requests.get(video["url"] + "?meta")
                print(r.text)
                
    print("Done.")



if __name__ == "__main__":
    main()
