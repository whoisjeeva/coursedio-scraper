from core.scraper import Scraper



scraper = Scraper()
scraper.login("33667870", "1609")
results = scraper.search("python")
results = scraper.get_course_details(results["data"][0].url)

print(results)
