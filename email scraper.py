import requests
from bs4 import BeautifulSoup
from googlesearch import search
import re
from urllib.parse import urlparse, urljoin
from pymongo import MongoClient
from pyfiglet import figlet_format
from rich.console import Console
from rich.markdown import Markdown
import json
from dotenv import load_dotenv
import os


load_dotenv()
try:
    python_env = os.environ['python_env']
    mongodb_url = os.environ['mongodb_url']
    root_url = os.environ['root_url']
    if not root_url.endswith('/'):
        root_url += '/'
    email_regex = os.environ['email_regex']
    user_agent = os.environ['user_agent']
except Exception as e:
    print('\nImproperly Configured Environment\nRefer the documentation for Email Scraper (IEEE-VIT)\nhttps://github.com/IEEE-VIT/email-scrapper\n')
    print(e)
    exit(0)


page_keywords = ['about', 'contact', 'support']
headers = {'User-Agent': user_agent}


connection = MongoClient(mongodb_url)
db = connection.get_database('sponsorship')
companies = db['companies']
skipped = db['skipped']


print(figlet_format('Email  Scraper'))
print(figlet_format('          Harsh  Gupta'))
print(figlet_format('          IEEE  VIT'))

console = Console()
console.print(Markdown('##### Welcome to my command line utility'))
console.print(Markdown('###### You may enter 0 OR skip to skip any company | -1 OR exit to quit the command line utility'))


mode = ''
while True:
    mode = input('\nPlease select any mode to continue\nauto OR manual\n').lower()
    if mode == 'auto' or mode == 'manual':
        break


def main():
    global mode
    pages = int(BeautifulSoup(requests.get(root_url).content, 'lxml').find(id='total_pages').get_text()) if python_env == 'production' else 1
    for page in range(1, pages+1):
        company_names = getCompanyNames(f'{root_url}page-{page}')
        for company_name in company_names:
            company_name = company_name.strip()
            if companies.find_one({"name": company_name}) or skipped.find_one({"name": company_name}):
                continue
            print(f'\n\n{company_name}')
            info = findInfo(company_name)
            if info == 0:
                print('skipped :(')
                skipped.insert_one({"name": company_name, "source": "Internshala", "mode": mode})
                continue
            else:
                info = {"name": company_name, "website": info['website'], "emails": info['emails'], "source": "Internshala"}
                print(info)
                companies.insert_one(info)

    view = input('\n\nWould you like to view automatically skipped companies\n').lower()
    if not (view == 'y' or view == 'yes'):
        console.print(Markdown('##### Thank You !! for using my Email Scraper command line utility | Harsh Gupta (IEEE-VIT)'))
        print()
        exit(0)

    mode = 'manual'
    console.print(Markdown('##### Switching to manual mode'))

    for company in skipped.find({"mode": "auto"}):
        print(f'\n\n{company["name"]}')
        skipped.delete_one(company)
        info = findInfo(company['name'])
        if info == 0:
            print('skipped :(')
            skipped.insert_one({"name": company_name, "source": "Internshala", "mode": mode})
            continue
        else:
            info = {"name": company_name, "website": info['website'], "emails": info['emails'], "source": "Internshala"}
            print(info)
            companies.insert_one(info)



def getCompanyNames(url):
    res = requests.get(url).content
    soup = BeautifulSoup(res, 'lxml')
    return [element.get_text() for element in soup.find_all(class_='link_display_like_text')]


def findInfo(company_name):
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
                    return findEmails(url)
                print(url)
                confirm = input("Do you want to continue with this url\n").lower()
                if confirm == '-1' or confirm == 'exit':
                    exit(0)
                elif confirm == '0' or confirm == 'skip':
                    return 0
                elif confirm == 'y' or confirm == 'yes':
                    return findEmails(url)
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
    return findEmails(urls[choice-1])


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


def findEmails(url):
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
    res = requests.get(url, headers=headers)
    logJson('response.json', {"url": url, "response": str(res)})   
    soup = BeautifulSoup(res.content, 'lxml').get_text()
    return re.findall(email_regex, soup)


main()