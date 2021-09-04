from dotenv import load_dotenv
import os
import time
from emailscraper import startScraping
import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures
from itertools import repeat
from pymongo import MongoClient

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

from pyvirtualdisplay import Display


load_dotenv()
try:
    user_agent = os.environ["user_agent"]
    accept_language = os.environ["accept_language"]
    python_env = os.environ["python_env"]
    mongodb_url = os.environ["mongodb_url"]
except Exception as e:
    print('\nImproperly Configured Environment\nPlease refer to the documentation for Email Scraper (IEEE-VIT)\nhttps://github.com/IEEE-VIT/email-scrapper\n')
    print(e)
    exit(0)


headers = {
    'User-Agent': user_agent,
    'Referer': 'https://www.google.com/',
    'Accept-Language': accept_language
}
connection = MongoClient(mongodb_url)
db = connection.get_database('sponsorship')
companies = db['companies']
skipped = db['skipped']


def cleanCompanies(company_names):
    company_names = [company_name.strip() for company_name in company_names]
    company_names = filter(lambda company_name: not (companies.find_one({"name": company_name}) or skipped.find_one({"name": company_name})), company_names)
    company_names = list(company_names)
    return company_names


def scheduler(company_names, source, mode, use_module):
    parts = os.cpu_count()
    each = int(len(company_names)/parts)

    fcompany_names = []
    start = 0
    for i in range(parts):
        if i == parts-1:    fcompany_names.append(company_names[start:])
        else:               fcompany_names.append(company_names[start:start+each])
        start += each

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(startScraping, fcompany_names, repeat(source), repeat(mode), repeat(use_module))


def initializeDriver():
    # display = Display(visible=0, size=(1920, 1080))
    # display.start()

    chrome_options = Options()
    if python_env == "production":
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("window-size=1920x1080")
        chrome_options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    driver.implicitly_wait(20)
    return driver
    

def internshala(mode, use_module):
    driver = initializeDriver()
    driver.get("https://internshala.com/internships")

    try:
        no_thanks = driver.find_element_by_id("no_thanks")
        no_thanks.click()
    except:
        print("We did not encounter any popup")

    input_xpath = "//div[@id='select_category_chosen']/ul[@class='chosen-choices']/li[@class='search-field']/input[contains(@class, 'chosen-search-input')]"
    driver.find_element_by_xpath(input_xpath).click()

    options_xpath = "//div[@id='select_category_chosen']/div[@class='chosen-drop']/ul[@class='chosen-results']//li[@class='active-result']"
    category_options = driver.find_elements_by_xpath(options_xpath)

    print("\n"*3)
    for index, category_option in enumerate(category_options):
        print(f"{index+1}. {category_option.text}")
    print("\n"*2)

    while True:
        choices = input("Please choose some categories\nYou may enter 0 for all\n")
        if choices == "0":
            break
        choices = [int(choice) for choice in choices.split() if choice.isnumeric() and int(choice) in range(1, len(category_options)+1)]
        print(f"\n\nYour choices | {choices}\n\n")
        if choices:
            wait = WebDriverWait(driver, timeout=10, ignored_exceptions=[exceptions.StaleElementReferenceException])
            c = 0
            choices.sort()
            choices = list(set(choices))
            for choice in choices:
                driver.find_elements_by_xpath(options_xpath)[choice-1-c].click()
                c += 1
                time.sleep(3)
                element = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, input_xpath)))
                element.click()
            break

    # company_names = set()
    # while True:
    #     temp = driver.find_elements_by_class_name("link_display_like_text")
    #     temp = [company_name.text for company_name in temp]
    #     company_names = company_names.union(set(temp))
    #     if driver.find_element_by_id("navigation-forward").get_attribute("class") == "disabled":
    #         break
    #     wait = WebDriverWait(driver, timeout=10, ignored_exceptions=[exceptions.StaleElementReferenceException, exceptions.ElementClickInterceptedException])
    #     element = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, "//i[@id='navigation-forward']//parent::a")))
    #     element.click()
    #     time.sleep(3)

    url = driver.current_url
    pages = int(driver.find_element_by_id("total_pages").text)
    driver.quit()

    fcompany_names = set()
    for page in range(1, pages+1):
        company_names = BeautifulSoup(requests.get(f"{url}/page-{page}", headers).content, "lxml").find_all("a", class_="link_display_like_text")
        company_names = [company_name.get_text() for company_name in company_names]
        fcompany_names = fcompany_names.union(set(company_names))
    
    fcompany_names = cleanCompanies(fcompany_names)    
    
    startScraping(list(fcompany_names), "Internshala", mode, use_module)
    # scheduler(fcompany_names, "Internshala", mode, use_module)


def theManifest(mode, use_module):
    url = input("\nPlease enter your start URL\n")
    soup = BeautifulSoup(requests.get(url, headers).content, "lxml")
    pages = int(re.findall(r"\d+", soup.find("li", class_="pager__item pager__item--last").find_next("a")["href"])[0])

    fcompany_names = set()
    for page in range(1, pages+1):
        soup = BeautifulSoup(requests.get(f"{url}?page={page}", headers).content, "lxml")
        company_names = soup.find_all("h3", class_="title")
        company_names = [company_name.find_next("a").get_text() for company_name in company_names]
        fcompany_names = fcompany_names.union(set(company_names))

    fcompany_names = cleanCompanies(fcompany_names)

    startScraping(list(fcompany_names), "The Manifest", mode, use_module)
    # scheduler(company_names, "The Manifest", mode, use_module)


sources = {
    "internshala": "Internshala",
    "theManifest": "The Manifest"
}
