import requests
from bs4 import BeautifulSoup
from googlesearch import search
import re
from urllib.parse import urlparse, urljoin, urlsplit
from pymongo import MongoClient
from rich.console import Console
from rich.markdown import Markdown
import json
from dotenv import load_dotenv
import os
import concurrent.futures

from extract_emails import EmailExtractor
from extract_emails.browsers import ChromeBrowser


load_dotenv()
try:
    mongodb_url = os.environ['mongodb_url']
    user_agent = os.environ['user_agent']
    accept_language = os.environ['accept_language']
except Exception as e:
    print('\nImproperly Configured Environment\nPlease refer the documentation for Email Scraper (IEEE-VIT)\nhttps://github.com/IEEE-VIT/email-scrapper\n')
    print(e)
    exit(0)


email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
page_keywords = ['about', 'contact', 'support', "care", "info"]
headers = {'User-Agent': user_agent, 'Referer': 'https://www.google.com/', 'Accept-Language': accept_language}


connection = MongoClient(mongodb_url)
db = connection.get_database('sponsorship')
companies = db['companies']
skipped = db['skipped']


def startScraping(company_names, source, mode, use_module):

    company_names = [company_name.strip() for company_name in company_names if not (companies.find_one({"name": company_name}) or skipped.find_one({"name": company_name}))]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(findInfo, company_name, mode, use_module): company_name for company_name in company_names}

        for future in concurrent.futures.as_completed(futures):
            company_name = futures[future]
            company_info = future.result()
            
            print(f'\n\n{company_name}')
            if company_info == 0:
                print('skipped :(')
                skipped.insert_one({"name": company_name, "source": source, "mode": mode})
                continue
            else:
                company_info = {"name": company_name, "website": company_info['website'], "emails": company_info['emails'], "source": source}
                print(company_info)
                companies.insert_one(company_info)


def viewSkipped(source, use_module):
    console = Console()
    view = input('\n\nWould you like to view automatically skipped companies\n').lower()
    if not (view == 'y' or view == 'yes'):
        console.print(Markdown('##### Thank You !! for using my Email Scraper command line utility | Harsh Gupta (IEEE-VIT)'))
        print()
        exit(0)

    mode = "manual"
    console.print(Markdown('##### Switching to manual mode'))

    for company in skipped.find({"mode": "auto", "source": source}):
        print(f'\n\n{company["name"]}')
        skipped.delete_one(company)
        info = findInfo(company['name'], mode, use_module)
        if info == 0:
            print('skipped :(')
            skipped.insert_one({"name": company["name"], "source": source, "mode": mode})
            continue
        else:
            info = {"name": company["name"], "website": info['website'], "emails": info['emails'], "source": source}
            print(info)
            companies.insert_one(info)


# def getCompanyNames(url):
#     res = requests.get(url).content
#     soup = BeautifulSoup(res, 'lxml')
#     return [element.get_text() for element in soup.find_all(class_='link_display_like_text')]


def findInfo(company_name, mode, use_module):
    urls = search(company_name, num_results=10, lang='en')
    urls = list(filter(lambda url: url.startswith('http://') or url.startswith('https://'), urls))
    company_words = company_name.lower().split()
    flag = False
    for url in urls:
        if flag:
            break
        domain = urlparse(url).netloc
        for company_word in company_words:
            if company_word in domain:
                if mode == 'auto':
                    return findEmails(url, use_module)
                print(url)
                confirm = input("Do you want to continue with this url\n").lower()
                if confirm == '-1' or confirm == 'exit':
                    exit(0)
                elif confirm == '0' or confirm == 'skip':
                    return 0
                elif confirm == 'y' or confirm == 'yes':
                    return findEmails(url, use_module)
                else:
                    flag = True
                    break
    if mode == 'auto':
        return 0
    print()
    for index, url in enumerate(urls):
        print(f'{index+1}. {url}')
    while True:
        choice = input('\nPlease enter a choice\n').lower()
        if choice == '-1' or choice == 'exit':
            exit(0)
        elif choice == '0' or choice == 'skip':
            return 0
        elif choice.strip('-').isnumeric() and int(choice) in list(range(1, len(urls)+1)):
            choice = int(choice)
            break
    return findEmails(urls[choice-1], use_module)


def filterPages(link):
    for keyword in page_keywords:
        if keyword in link:
            return True
    return False


def logJson(filename, json_obj):
    f = open(filename, 'a+')
    f.seek(0)
    if f.read():
        f.seek(0)
        temp = json.load(f)
        temp.append(json_obj)
        f.truncate(0)
        json.dump(temp, f, indent=2)
        f.close()
    else:
        json.dump([json_obj], f, indent=2)
        f.close()


def findEmails(url, use_module):
    if use_module:
        emails = []
        try:
            with ChromeBrowser() as browser:
                email_extractor = EmailExtractor(url, browser, depth=2)
                emails = email_extractor.get_emails()
                emails = [{"email": email.email, "source_page": email.source_page} for email in emails]
        except Exception as e:
            logJson('errors.json', {"url": url, "exception": str(e)})
        return {"website": url, "emails":emails}
    else:
        info = {"website": url}
        emails = set()
        emails.update(scrapeEmails(url))
        
        res = requests.get(url, headers=headers)
        logJson('response.json', {"url": url, "response": str(res)})
        links = BeautifulSoup(res.content, 'lxml').find_all('a')
        links = [str(link.get('href')) for link in links if 'href' in link.attrs]
        links = list(filter(filterPages, links))

        for link in links:
            try:
                if not (link.startswith('http://') or link.startswith('https://')):
                    link = urljoin(url, link, allow_fragments=True)
                emails.update(scrapeEmails(link))
            except Exception as e:
                logJson('errors.json', {"url": link, "exception": str(e)})
        
        info['emails'] = list(emails)
        return info
    

def scrapeEmails(url):
    temp = headers
    temp['Referer'] = f'{urlsplit(url).scheme}://{urlsplit(url).netloc}'
    res = requests.get(url, headers=temp)
    logJson('response.json', {"url": url, "response": str(res)})   
    soup = BeautifulSoup(res.content, 'lxml').get_text()
    return re.findall(email_regex, soup)


