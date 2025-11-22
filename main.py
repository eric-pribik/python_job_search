from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Remote, ChromeOptions as Options
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection as Connection
from os import environ
import my_secrets
import pandas as pd
import json
import os
import sys
import requests
import time
import pickle
from zipfile import ZipFile


GOOGLE_SEARCH_PAGE_LIMIT = 30
USE_API_BROWSER = False
TARGET_URL = environ.get('TARGET_URL', default='https://Google.com')
BRIGHTHOUSE_AUTH = my_secrets.BRIGHTHOUSE_AUTH
BRIGHTHOUSE_USERNAME = my_secrets.BRIGHTHOUSE_USERNAME
BRIGHTHOUSE_PASSWORD = my_secrets.BRIGHTHOUSE_PASSWORD
BRIGHTDATA_HOST = my_secrets.BRIGHTDATA_HOST
BRIGHTHOUSE_PORT = my_secrets.BRIGHTHOUSE_PORT

#Might have to be moved into main() after chromedriver check
service = Service(executable_path="chromedriver")
driver = webdriver.Chrome(service=service)

def load_ats_json():
    '''
    Loads in the ats-search-queries.json file as a dictionary
    '''
    try:
        with open('ats-search-queries.json', 'r') as file:
            ats_search_queries = json.load(file)
            return ats_search_queries
        print("JSON data loaded successfully into a dictionary:")
    except FileNotFoundError:
        print(f"Error: The file 'your_file.json' was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from 'your_file.json'. Check for valid JSON format.")

def get_chromedriver():
    '''
    If the program cannot find the chromedriver file in the program's directory it will check 
    to see if Google Chrome is installed, get the version number and download the correct 
    chromedriver for this program to use and extract it into the working directory.
    '''
    #gets current version of Chrome to download the correct chromedriver version
    print("chromedriver file was not found. Downloading chromedriver-linux64.zip...")
    chrome_version = os.popen("google-chrome --version | awk '{print $3}'").read().rstrip()
    if chrome_version == "":
        print("Chrome is not installed or cannot get its version number, please install Google Chrome or " \
        "manually download the chromedriver and place it inside the program's working directory.")
        sys.exit(1)
    #Generates the URL with the Google Chrome version number above
    chromedriver_dl_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/linux64/chromedriver-linux64.zip"
    response = requests.get(chromedriver_dl_url)
    if response.status_code == 200:
        with open("chromedriver-linux64.zip", "wb") as f:
            f.write(response.content)
        print("chromedriver-linux64.zip downloaded successfully! Extracting zip file...")
    #Extracts chromedriver for the downloaded zip file
        with ZipFile('chromedriver-linux64.zip') as zObject:
            zObject.extract("chromedriver-linux64/chromedriver")
        zObject.close()
        print("chromedriver extracted sucessfully!")
    else:
        print(f"Error downloading file: {response.status_code}\nPlease try again.")

def initiate_local_google_search(ats_url, job_keyword, location):
    '''
    Starts a new web session, imports any browser cookies you wish to import, and 
    initiates a google search with the keywords you selected.
    '''
    #I NEED LOGGING IN THIS FUNCTION!!!
    #imports any cookies saved at cookies.plk
    cookies_exists = os.path.exists("./cookies.plk")
    if cookies_exists == True:
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
    #opens the google webpage and waits 5 seconds for the search box to appear
    driver.get("https://Google.com")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "gLFyf"))
    )
    input_element = driver.find_element(By.CLASS_NAME, "gLFyf")
    input_element.clear()
    time.sleep(1)
    #Types in the search query and hits enter, waits 60 seconds in case of CAPTCHA
    input_element.send_keys(f"site:{ats_url} {job_keyword} {location} {Keys.ENTER}")
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CLASS_NAME, "zReHs"))
    )

def initiate_api_google_search(url=TARGET_URL):
    if BRIGHTHOUSE_AUTH == f'{BRIGHTHOUSE_USERNAME}:{BRIGHTHOUSE_PASSWORD}':
        raise Exception('Provide Scraping Browsers credentials in AUTH '
                        'environment variable or update the script.')
    print('Connecting to Browser...')
    server_addr = f'https://{BRIGHTHOUSE_USERNAME}:{BRIGHTHOUSE_PASSWORD}@{BRIGHTDATA_HOST}:{BRIGHTHOUSE_PORT}'
    connection = Connection(server_addr, 'goog', 'chrome')
    driver = Remote(connection, options=Options())
    try:
        print(f'Connected! Navigating to {url}...')
        driver.get(url)
        print('Navigated! Waiting captcha to detect and solve...')
        result = driver.execute('executeCdpCommand', {
            'cmd': 'Captcha.waitForSolve',
            'params': {'detectTimeout': 10 * 1000},
        })
        status = result['value']['status']
        print(f'Captcha status: {status}')
    finally:
        driver.quit()

def scrape_webpage():
    '''
    Scrapes the webpage for all search result's titles and urls, then returns a 
    dictionary with these results.
    '''
    results = {}
    #Scrapes the url of each result
    search_url_element = driver.find_elements(By.CSS_SELECTOR, "a[href]")
    urls = []
    for i in search_url_element:
        href = i.get_attribute("href")
        if href and "google.com/" not in href: # Filter out internal Google links
            urls.append(href)
    #scrapes the hyperlink title of each result
    titles = []
    search_title_element = driver.find_elements(By.CLASS_NAME, "LC20lb.MBeuO.DKV0Md")
    for i in search_title_element:
        titles.append(i.text)
    #Combines the title and url into a dictationary and returns it
    results = dict(zip(titles, urls))
    time.sleep(60)
    driver.quit
    return results

def select_next_page(page_limit):
    '''
    This will check to see if there is another page of results, and if so select the next
    page. This WILL NOT start any scraping. You can also set a custom page limit but the 
    default is 30. 
    '''
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.CLASS_NAME, "LLNLxf"))
        )
    except TimeoutException:
        #No more pages
        print(f"Reached the end of the Google results at page: {current_page_element}.")
        return "END"
    
    current_page_element =driver.find_element(
        By.CLASS_NAME, "YyVfkd.NKTSme"
    ).text
    int(current_page_element)
    if current_page_element <= page_limit:
        driver.find_element(By.CLASS_NAME, "LLNLxf").click()
        return current_page_element
    else:
        print(f"Reached maximum Google result's set at page: {current_page_element}.")
        return "END"

def start_next_search(ats_url, job_keyword, location):
    input_element = driver.find_element(By.CLASS_NAME, "gLFyf")
    input_element.clear()
    time.sleep(1)
    #Types in the search query and hits enter, waits 60 seconds in case of CAPTCHA
    input_element.send_keys(f"site:{ats_url} {job_keyword} {location} {Keys.ENTER}")

def main():
    #Checks if chromedriver exists and if not downloads file
    chromedriver_exists = os.path.exists("./chromedriver")
    if chromedriver_exists == False:
        get_chromedriver()
    ats_search_queries = load_ats_json()
    current_page = 1
    search_results = {}
    
    for x in ats_search_queries["search"]["ats_urls"][x]["domain"]:
        for y in ats_search_queries["search"]["job_keywords"]["job_titles"][y]["roles"]:
            for z in ats_search_queries["search"]["location_keywords"][z]["remote"]:
                initiate_local_google_search(x, y, z)
                while current_page != "END":
                    a = scrape_webpage()
                    search_results.update(a)
                    select_next_page(GOOGLE_SEARCH_PAGE_LIMIT)

    #exports all cookies and quits the session
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    time.sleep(100)
    driver.quit

if __name__ == "__main__":
    main()



#    site:indeed.com ("linux engineer" OR "linux administrator" OR "Linux Automation" OR "linux * engineer" OR "linux * administrator") (michigan OR detroit OR "ann arbor")