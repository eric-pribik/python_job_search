from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import expected_conditions as EC
import json
import os
import urllib.request
import requests
import time
from zipfile import ZipFile


service = Service(executable_path="chromedriver")
driver = webdriver.Chrome(service=service)

def get_chromedriver():
#If the program cannot find the chromedriver file it will download and unzip the file
    #gets current version of Chrome to download the correct chromedriver version
    print("chromedriver file was not found. Downloading chromedriver-linux64.zip...")
    chrome_version = os.popen("google-chrome --version | awk '{print $3}'").read().rstrip()
    #Generates the URL with the Google Chrome version number above
    chromedriver_dl_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/linux64/chromedriver-linux64.zip"
    response = requests.get(chromedriver_dl_url)
    if response.status_code == 200:
        with open("chromedriver-linux64.zip", "wb") as f:
            f.write(response.content)
        print("chromedriver-linux64.zip downloaded successfully! Extracting zip file...")
    #Extracts chromedriver for the downloaded zip file
#        with ZipFile('chromedriver-linux64.zip') as zObject:
#            zObject.extract(
#                "chromedriver")
#        zObject.close()
        print("chromedriver extracted sucessfully!")

    else:
        print(f"Error downloading file: {response.status_code}")


def main():
    chromedriver_exists = os.path.exists("./chromedriver")
    if chromedriver_exists == False:
        get_chromedriver()



    driver.get("https://google.com")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "gLFyf"))
    )
    input_element = driver.find_element(By.CLASS_NAME, "gLFyf")
    input_element.clear()
    input_element.send_keys("test" + Keys.ENTER)

    link = driver.find


    time.sleep(20)
    driver.quit

if __name__ == "__main__":
    main()
