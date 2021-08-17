import scrapy

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
                urls = search(company_name, num_results=10, lang='en')
                found = False
                words = company_name.lower().split()
                for url in urls:
                    domain = urlparse(url).netloc
                    for word in words:
                        if word in domain:
                            print()
                            print(url)
                            confirm = input("Do you want to continue with this url\n")
                            if confirm == 'y' or confirm.lower() == 'yes':
                                found = True
                                website = url
                                break
                    break
                if not found:
                    print()
                    for index, url in enumerate(urls):
                        print(f"{index+1}.", url)
                    choice = int(input('\nPlease enter your choice\nYou may enter 0 to skip the company\n'))
                    if choice == 0:
                        continue
                    website = urls[choice-1]

                yield scrapy.Request(website, callback=self.scrapeEmails, cb_kwargs={"company_name": company_name, "website": website})


    def scrapeEmails(self, response, company_name, website):
        print(response)
        emails = response.css("::text").re(r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+")
        item = CompanyItem()
        item["name"] = company_name
        item["website"] = website
        item["emails"] = list(set(emails))
        item["source"] = "Internshala"
        yield item