from dotenv import dotenv_values
import time
from emailscraper import startScraping, viewSkipped
from pyfiglet import figlet_format
import multiprocessing

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By


config = dotenv_values(".env")
try:
    user_agent = config["user_agent"]
    python_env = config["python_env"]
except Exception as e:
    print('\nImproperly Configured Environment\nPlease refer the documentation for Email Scraper (IEEE-VIT)\nhttps://github.com/IEEE-VIT/email-scrapper\n')
    print(e)
    exit(0)


def initializeDriver():
    chrome_options = Options()
    if python_env == "production":
        chrome_options.add_argument("--headless")
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
        if len(choices) <= 0:
            continue

        wait = WebDriverWait(driver, timeout=10, ignored_exceptions=[
            exceptions.StaleElementReferenceException
        ])

        c = 0
        choices.sort()
        choices = list(set(choices))
        for choice in choices:
            driver.find_elements_by_xpath(options_xpath)[choice-1-c].click()
            c += 1
            time.sleep(3)
            element = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, input_xpath)))
            element.click()

    processes = []
    while True:
        company_names = driver.find_elements_by_class_name("link_display_like_text")
        company_names = [company_name.text for company_name in company_names]
        process = multiprocessing.Process(target=startScraping, args=[company_names, "Internshala", mode, use_module])
        processes.append(process)
        process.start()
        # startScraping(company_names, "Internshala")
        if driver.find_element_by_id("navigation-forward").get_attribute("class") == "disabled":
            break
        driver.find_element_by_id("navigation-forward").click()
        time.sleep(5)
    
    for process in processes:
        process.join()
        print(figlet_format("process complete"))

    time.sleep(10)
    driver.quit()


sources = ["internshala"]
