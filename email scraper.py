import requests
from bs4 import BeautifulSoup
from googlesearch import search
import re
from urllib.parse import urlparse, urljoin
from pymongo import MongoClient
from pyfiglet import figlet_format
from rich.console import Console
from rich.markdown import Markdown


email_regex = r'[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+'
page_keywords = ['about', 'contact', 'support']

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
headers = {'User-Agent': user_agent}


connection = MongoClient('mongodb://localhost:27017/')
db = connection.get_database('sponsorship')
companies = db['companies']
companies_skip = db['companies_skip']


print(figlet_format('Email  Scraper'))
print(figlet_format('          Harsh  Gupta'))
print(figlet_format('          IEEE  VIT'))

console = Console()
console.print(Markdown('##### Welcome to my command line utility'))
console.print(Markdown('###### You may enter 0 OR skip to skip any company | -1 OR exit to quit the command line utility'))

while True:
    mode = input('\nPlease select any mode to continue\nauto OR manual\n').lower()
    if mode == 'auto' or mode == 'manual':
        break


def main():
    internshala = 'https://internshala.com/internships/'
    pages = int(BeautifulSoup(requests.get(internshala).content, 'lxml').find(id='total_pages').get_text())
    # for page in range(1, pages+1):
    for page in range(1, 2):
        company_names = getCompanyNames(f'{internshala}page-{page}')
        for company_name in company_names:
            company_name = company_name.strip()
            if companies.find_one({"name": company_name}) or companies_skip.find_one({"name": company_name}):
                continue
            print(f'\n\n{company_name}')
            info = findInfo(company_name)
            if info == 0:
                companies_skip.insert_one({"name": company_name, "source": "Internshala"})
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


def findEmails(url):
    info = {"website": url}
    emails = scrapeEmails(url)
    if emails:
        info['emails'] = list(set(emails))
        return info
    links = BeautifulSoup(requests.get(url, headers=headers).content, 'lxml').find_all('a')
    links = [str(link.get('href')) for link in links]
    links = list(filter(filterPages, links))
    emails = []
    for link in links:
        if not (link.startswith('http://') or link.startswith('https://')):
            link = urljoin(url, link, allow_fragments=True)
        emails.extend(scrapeEmails(link))
    info['emails'] = list(set(emails))
    return info
    

def scrapeEmails(url):
    res = requests.get(url, headers=headers).content
    soup = BeautifulSoup(res, 'lxml').get_text()
    return re.findall(email_regex, soup)


main()