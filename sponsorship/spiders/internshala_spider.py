import scrapy
from scrapy import item

from ..items import CompanyItem
from pymongo import MongoClient
from googlesearch import search
from urllib.parse import urlparse

class InternshalaSpider(scrapy.Spider):

    name = 'internshala'    
    start_urls = [
        'https://internshala.com/internships'
    ]

    def __init__(self):
        connection = MongoClient('mongodb://localhost:27017')
        db = connection.get_database('sponsorship')
        self.collection = db["test_collection"]

    def parse(self, response):

        company_names = response.css(".link_display_like_text::text").extract()
        company_names = [company_name.strip() for company_name in company_names]

        for company_name in company_names:

            if not self.collection.find_one({"name": company_name}):
                print('\n')
                print(company_name)
                urls = list(filter(lambda url: url.startswith("http://") or url.startswith("https://"), search(company_name, num_results=10, lang='en')))
                found = False
                flag = False
                exit_flag = False
                words = company_name.lower().split()
                for url in urls:
                    if flag:
                        break
                    domain = urlparse(url).netloc # maybe fine
                    for word in words:
                        if word in domain:
                            flag = True
                            print()
                            print(url)
                            confirm = input("Do you want to continue with this url\n")
                            if confirm == "-1":
                                exit_flag = True
                            if confirm.lower() == 'y' or confirm.lower() == 'yes':
                                found = True
                                website = url
                            break
                if exit_flag:
                    break
                if not found:
                    print()
                    for index, url in enumerate(urls):
                        print(f"{index+1}.", url)
                    while True:
                        choice = input('Please enter your choice\nYou may enter 0 to skip the company\n')
                        if choice.strip('-').isnumeric() and int(choice) in list(range(-1, 10)):
                            choice = int(choice)
                            break
                    if choice == -1:
                        break
                    if choice == 0:
                        continue
                    website = urls[choice-1]

                yield scrapy.Request(website, callback=self.scrapeEmails, cb_kwargs={"company_name": company_name, "website": website, "start": True})


    def scrapeEmails(self, response, company_name, website, start=False, links=[]):

        item = CompanyItem()
        item["name"] = company_name
        item["website"] = website # we may use urlparse(website).netloc
        item["source"] = "Internshala"
        
        emails = response.css("::text").re(r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+")
        if not emails:
            if start:
                links = response.css("a::attr(href)").extract()
                links = list(filter(lambda link: "about" in link or "contact" in link or "support" in link, links))
            if not links:
                item["emails"] = list(set(emails))
                yield item
                return item
            
            temp = links[1:] if len(links) > 1 else []
            yield response.follow(links[0], callback=self.scrapeEmails, cb_kwargs={"company_name": company_name, "website": website, "links": temp})
        else:
            item["emails"] = list(set(emails))
            yield item
            return item
