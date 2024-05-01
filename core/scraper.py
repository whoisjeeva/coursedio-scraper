#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2021 suyambu developers (http://suyambu.net)
See the file 'LICENSE' for copying permission
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date as datetime_date
import urllib.parse as urlparse
from urllib.parse import parse_qs
import json
import re


class Scraper:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.login_url = "https://www.linkedin.com/learning-login/go/loganlibraries"
        self.csrf = None

    def login(self, libraryCardId, pin):
        r = self.session.get(self.login_url, headers={
            "Accept-Language": "en-US,en;q=0.9"
        })
        s = BeautifulSoup(r.content, "html.parser")
        portal_url = s.select("a[class^='library-go']")[0]["href"]
        r = self.session.get(portal_url, headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9"
        })
        # with open("test.html", "wb") as f:
        #     f.write(r.content) 
        s = BeautifulSoup(r.content, "html.parser")

        csrfToken = s.find("form").select("[name='csrfToken']")[0]["value"]
        # libraryCardId = "33667870"
        # pin = "1609"
        account = s.find("form").select("[name='account']")[0]["value"]
        appInstance = s.find("form").select("[name='appInstance']")[0]["value"]
        redirect = s.find("form").select("[name='redirect']")[0]["value"]
        authUUID = s.find("form").select("[name='authUUID']")[0]["value"]


        library_callback_url = "https://www.linkedin.com/learning-login/go/library-callback"
        payload = {
            "csrfToken": csrfToken,
            "libraryCardId": libraryCardId,
            "pin": pin,
            "account": account,
            "appInstance": appInstance,
            "redirect": redirect,
            "authUUID": authUUID
        }

        d = self.session.post(library_callback_url, data=payload).json()
        self.session.post(f"https://www.linkedin.com/checkpoint/enterprise/library/{account}/LEARNING/{appInstance}", data={
            "redirectUrl": d["redirectUrl"],
            "pin": d["pin"],
            "libraryCardId": d["libraryCardId"]
        })

        self.csrf = self.session.cookies.get_dict()["JSESSIONID"]


    def search(self, query, start=0):
        r = self.session.get(
            f"https://www.linkedin.com/learning-api/searchV2?facets=List(entityType%3DCOURSE)&keywords={query}&q=keywords&sortBy=RELEVANCE&start={start}", 
            headers={ 
                "X-Requested-With": "XMLHttpRequest",
                "csrf-token": self.csrf,
                "Accept-Language": "en-US,en;q=0.9"
            }
        )

        data = r.json()

        if "elements" not in data:
            return []

        elements = data["elements"]
        results = []

        for inc in elements:
            if "entityType" not in inc:
                continue

            length = inc["length"]
            if "duration" not in length:
                length["duration"] = length["com.linkedin.common.TimeSpan"]["duration"]

            thumbnail = inc['thumbnails'][0]['source']
            if "rootUrl" not in thumbnail:
                thumbnail = thumbnail["com.linkedin.common.VectorImage"]

            try:
                results.append({
                    "title": inc["headline"]["title"]["text"],
                    "description": inc["description"]["text"],
                    "duration": self.parse_duration(length["duration"]),
                    "thumb": f"{thumbnail['rootUrl']}{thumbnail['artifacts'][0]['fileIdentifyingUrlPathSegment']}",
                    "author": f"{inc['authors'][0]['firstName']} {inc['authors'][0]['lastName']}",
                    "release_date": self.epoch_to_date(inc["releasedOn"]),
                    "url": inc["slug"]
                })
            except:
                pass
        
        expire = 0
        if results:
            parsed_url = urlparse.urlparse(results[0]["thumb"])
            expire = int(parse_qs(parsed_url.query)['e'][0])

        return {"expire": expire, "data": results}

    def epoch_to_date(self, epoch):
        """
        Expecting epoch to be in milliseconds
        """
        return datetime.fromtimestamp(epoch/1000).strftime("%b %d, %Y")

    def parse_duration(self, duration):
        hours = int(duration / 3600)
        minutes = int((duration % 3600) / 60)
        seconds = int(duration % 60)

        if hours == 0 and minutes == 0:
            return f"{seconds}s"
        elif hours == 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{hours}h {minutes}m {seconds}s"


    def get_course_details(self, course_slug):
        """
        This is just a web scraping hack to extract the course details, it's not a real API call
        """
        if course_slug.find("://") == -1:
            course_slug = f"https://www.linkedin.com/learning/{course_slug}"


        r = requests.get(course_slug)
        s = BeautifulSoup(r.content, "html.parser")
        obj = json.loads(s.select("script[type='application/ld+json']")[0].string)
        # return obj
        parsed = urlparse.urlparse(obj["thumbnailUrl"])
        d = obj["datePublished"].split("-")
        date_published = datetime_date(int(d[0]), int(d[1]), int(d[2])).strftime("%b %d, %Y")

        data = {
            "author_name": obj["author"][0]["name"],
            "author_url": obj["author"][0]["url"],
            "date_published": date_published,
            "description": obj["description"],
            "image": obj["thumbnailUrl"],
            "title": obj["name"],
            "videos": [],
            "expire": int(parse_qs(parsed.query)["e"][0]) * 1000,
            "slug": course_slug.split("/")[-1]
        }
        
        items = s.find_all("a", {"class": "toc-item__link"})
        for item in items:
            data["videos"].append({
                "url": item["href"].split("?")[0],
                "duration": item.find("div", {"class": "table-of-contents__item-duration"}).text.strip(),
                "title": item.find("div", {"class": "table-of-contents__item-title"}).text.strip()
            })
        return data

    
    def get_course_details_using_session(self, course_slug):
        """
        This is just a web scraping hack to extract the course details, it's not a real API call
        """
        try:
            if course_slug.find("://") == -1:
                course_slug = f"https://www.linkedin.com/learning/{course_slug}"


            r = self.session.get(course_slug)
            s = BeautifulSoup(r.content, "html.parser")
            code_els = s.find_all("code")
            code = None
            for code_el in code_els:
                if "COURSE" in code_el.text:
                    code = code_el.text
            
            if code is None:
                return self.get_course_details(course_slug)


            videos = []
            course_details = {}



            obj = json.loads(code)["included"]
            tmp = {}
            first = None
            last = None
            for o in obj:
                if "title" in o and "*items" in o:
                    if o["title"].lower() == "introduction":
                        first = o
                    elif o["title"].lower() == "conclusion":
                        last = o
                    else:
                        k = int(o["title"].split(".")[0])
                        tmp[k] = o
                elif "displayName" in o:
                    course_details["author_name"] = o["displayName"]
                elif "updatedAt" in o and "activatedAt" in o:
                    if o.get("updatedAt", None) is not None:
                        course_details["published_date"] = self.epoch_to_date(o["updatedAt"])
                    else:
                        course_details["published_date"] = self.epoch_to_date(o["activatedAt"])
                    
                    course_details["description"] = o["description"]["text"]
                    course_details["title"] = o["title"]
                    course_details["duration"] = self.parse_duration(o["duration"]["duration"])

                    rootUrl = o["primaryThumbnail"]["source"]["rootUrl"]
                    part = o["primaryThumbnail"]["source"]["artifacts"][-2]["fileIdentifyingUrlPathSegment"]
                    course_details["thumbnail"] = rootUrl + part
                    course_details["expire"] = o["primaryThumbnail"]["source"]["artifacts"][-2]["expiresAt"]
                    course_details["difficulty"] = o["difficultyLevel"]
                    course_details["exercise_files"] = o["exerciseFiles"]

            
            keys = list(tmp.keys())
            keys.sort()
            snaps = []
            if first is not None:
                snaps.append(first)
            for k in keys:
                snaps.append(tmp[k])
            if last is not None:
                snaps.append(last)

            video_items = []
            for o in obj:
                if "entityType" in o and o["entityType"] == "VIDEO":
                    video_items.append(o)
            
            for snap in snaps:
                for item in snap["*items"]:
                    urn = item.replace("urn:li:learningApiTocItem:", "")
                    for v in video_items:
                        if v["entityUrn"] == urn:
                            videos.append({
                                "title": v["title"],
                                "url": "https://www.linkedin.com/learning/" + course_slug + "/" + v["slug"],
                                "duration": self.parse_duration(v["duration"]["duration"])
                            })
            

            return {
                "author_name": course_details["author_name"],
                "author_url": "https://www.linkedin.com/learning/",
                "date_published": course_details["published_date"],
                "description": course_details["description"],
                "image": course_details["thumbnail"],
                "title": course_details["title"],
                "videos": videos,
                "expire": course_details["expire"],
                "slug": course_slug.split("/")[-1]
            }, course_details["exercise_files"]
        except:
            return self.get_course_details(course_slug), []

    
    def get_exercise_files(self, course_slug):
        r = self.session.get(f"https://www.linkedin.com/learning-api/courses?q=slug&slug={course_slug}", headers={
            "X-Requested-With": "XMLHttpRequest",
            "csrf-token": self.csrf
        })
        return r.json()["elements"][0]["exerciseFiles"]

    
    def get_course_decoration_id(self, course_slug):
        """
        So far courseDecorationId is not required, in-case if it is required in the future, I can use this method.
        Example: f"https://www.linkedin.com/learning-api/courses?decorationId={courseDecorationId}&q=slug&slug={course_slug}"
        """
        r = self.session.get(f"https://www.linkedin.com/learning/{course_slug}")
        soup = BeautifulSoup(r.content, 'html.parser')
        js = soup.select_one('[data-fastboot-src="/learning/assets/learning-web.js"]')["src"]
        r = self.session.get(js)
        course_decoration_id = re.search(r"DECORATED_COURSE,(.*?)\)", r.text).group(1).replace('"', '')
        return course_decoration_id

    
    def get_video_decoration_id(self, course_slug, video_slug):
        """
        So far videoDecorationId is not required, in-case if it is required in the future, I can use this method.
        Example: f"https://www.linkedin.com/learning-api/videos?decorationId={videoDecorationId}&parentSlug={course_slug}&q=slugs&slug={video_slug}
        """
        r = self.session.get(f"https://www.linkedin.com/learning/{course_slug}/{video_slug}")
        soup = BeautifulSoup(r.content, 'html.parser')
        js = soup.select_one('[data-fastboot-src="/learning/assets/learning-web.js"]')["src"]
        r = self.session.get(js)
        video_decoration_id = re.search(r"DECORATED_VIDEO,(.*?)\)", r.text).group(1).replace('"', '')
        return video_decoration_id


    def get_video_details(self, course_slug, video_slug):
        r = self.session.get(f"https://www.linkedin.com/learning-api/videos?parentSlug={course_slug}&q=slugs&slug={video_slug}", headers={
            "csrf-token": self.csrf,
            "X-Requested-With": "XMLHttpRequest"
        })
        video = r.json()
        streams = []
        element = None

        # with open("streams.json", "w") as f:
        #     json.dump(video, f, indent=4)

        for el in video["elements"]:
            if "entityType" in el:
                if el["entityType"] == "VIDEO":
                    element = el
                    break

        for v in element["presentation"]["videoPlay"]["videoPlayMetadata"]["progressiveStreams"]:
            video_url = v["streamingLocations"][0]["url"]
            if "audio" in video_url:
                continue
            streams.append({
                "height": v["height"],
                "width": v["width"],
                "video_type": v["mediaType"],
                "url": video_url,
                "expire": v["streamingLocations"][0]["expiresAt"],
                "slug": f"{course_slug}/{video_slug}"
            })

        try:
            subtitle = element["presentation"]["videoPlay"]["videoPlayMetadata"]["transcripts"][0]["captionFile"]
        except:
            subtitle = ""
        hls = element["presentation"]["videoPlay"]["videoPlayMetadata"]["adaptiveStreams"]
        hls_url = None
        hls_expire = None
        if len(hls) > 0:
            hls_url = hls[0]["masterPlaylists"][0]["url"]
            hls_expire = hls[0]["masterPlaylists"][0]["expiresAt"]

        return {"subtitle": subtitle, "streams": streams, "hls": hls_url, "hls_expire": hls_expire}


    def get_suggestions(self, query):
        r = self.session.get(
            f"https://www.linkedin.com/learning-api/typeaheadV2?count=10&includeAuthors=false&includeCategories=false&includeLearningPaths=false&numAutoComplete=10&prefix={query}&q=typeahead", 
            headers={ 
                "X-Requested-With": "XMLHttpRequest",
                "csrf-token": self.csrf
            }
        )

        elements = r.json()["elements"]
        suggestions = []
        for inc in elements:
            suggestions.append(inc["primaryText"]["text"])

        return suggestions


if __name__ == "__main__":
    scraper = Scraper()
    scraper.login("33667870", "1609")

    # data = scraper.get_course_details("react-server-side-rendering-2018")
    # print(data)

    s, excercise_files = scraper.get_course_details_using_session("python-essential-training-18764650")
    print(excercise_files)
    print("\n\n")
    course_slug = s["slug"]
    v = scraper.get_video_details(course_slug, s["videos"][0]["url"].split("/")[-1])
    
    print(v)

    # r = scraper.session.get(
    #     "https://www.linkedin.com/learning-api/courses?q=slug&slug=react-server-side-rendering-2018",
    #     headers={ 
    #         "X-Requested-With": "XMLHttpRequest",
    #         "csrf-token": scraper.csrf
    #     }
    # )
    # print(r.text)
    # with open("details.json", "w") as f:
    #     json.dump(r.json(), f, indent=4)
