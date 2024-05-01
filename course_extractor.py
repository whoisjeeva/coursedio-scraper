from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from time import sleep
import json


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
TMP_SLUGS = []

def main():
    driver.get("https://www.linkedin.com/learning-login/go/loganlibraries")
    driver.find_element(By.CSS_SELECTOR, "a[class*='library-go']").click()
    
    driver.find_element(By.CSS_SELECTOR, "#library-card-number-input").send_keys("33667870")
    driver.find_element(By.CSS_SELECTOR, "#library-card-pin-input").send_keys("1609")
    driver.find_element(By.CSS_SELECTOR, "#library-validate-button").click()
    
    wait_for_text("in progress")
    
    categories = [
        "business",
        "technology",
        "creative"
    ]
    data = []
    for category in categories:
        courses = fetch_courses(category)
        data.append({
            "category": category,
            "courses": courses
        })
    
    with open("data.json", "w+") as f:
        f.write(json.dumps(data))

    driver.quit()


def fetch_courses(category):
    all_courses = []

    driver.get(f"https://www.linkedin.com/learning/topics/{category}")
    wait_for_text("Best Match")
    
    topics_els = driver.find_elements(By.CSS_SELECTOR, ".topics-body__topic-pills a")
    base_topics = []
    for topic_el in topics_els:
        base_topics.append({
            "text": topic_el.text,
            "url": topic_el.get_attribute("href")
        })
    
    topics = []
    for base_topic in base_topics:
        driver.get(base_topic["url"])
        wait_for_text("Best Match")
        topics_els = driver.find_elements(By.CSS_SELECTOR, ".topics-body__topic-pills a")
        for topic_el in topics_els:
            topics.append({
                "text": topic_el.text,
                "url": topic_el.get_attribute("href")
            })
        
    
    for topic in topics:
        driver.get(topic["url"])
        wait_for_text("Best Match")
        while True:
            courses = extract_course_details()
            for c in courses:
                if c["slug"] in TMP_SLUGS:
                    continue
                TMP_SLUGS.append(c["slug"])
                all_courses.append(c)

            print(f"{len(all_courses)} courses for '{category}' added.", end="\r", flush=True)
            show_more_button = driver.find_elements(By.CSS_SELECTOR, ".finite-scroll__load-button")
            if len(courses) == 0 and len(show_more_button) > 0:
                show_more_button[0].click()
            elif len(courses) == 0:
                break
            # sleep(5)
            while True:
                if is_no_more_courses():
                    break
                sleep(1)
    print(f"{len(all_courses)} courses for '{category}' added.")
    return all_courses


def is_no_more_courses():
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, ".finite-scroll__load-button")
        if len(btns) == 0:
            return True
        if len(btns) > 0 and btns[0].get_attribute("aria-disabled") == "false":
            return True
    except StaleElementReferenceException:
        return is_no_more_courses()
    return False


def extract_course_details():
    output = []
    els = driver.find_elements(By.CSS_SELECTOR, ".topics-body__result-card")
    for i, el in enumerate(els):
        slug = el.find_element(By.CSS_SELECTOR, "a").get_attribute("href").split("?")[0].split("/")[-1]
        skills = []
        for a in el.find_elements(By.CSS_SELECTOR, ".lls-card-skills a"):
            skills.append(a.text)
        output.append({
            "slug": slug,
            "title": el.find_element(By.CSS_SELECTOR, ".lls-card-headline").text,
            "skills": skills
        })
        driver.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
        """, el)
    return output


def wait_for_text(text):
    text = text.lower()
    
    while True:
        page = driver.execute_script("return document.body.textContent;")
        if text in page.lower():
            break
        sleep(1)


if __name__ == "__main__":
    main()
    