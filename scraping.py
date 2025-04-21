import os.path
# import random
import time

import re
from urllib.parse import urljoin
import json

import PyPDF2
import requests
from PyPDF2.errors import PdfReadError
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import urllib3
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'

config = __import__("config")

# https://chromedriver.chromium.org/downloads
service = Service(config.chromePath, service_args=['headless'])
options = Options()
#options.add_extension('uBlock-Origin.crx')
options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
# options.headless = True  # does not work with extension
#driver = webdriver.Chrome(service=service, options=options)

# headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def getPath(currentPath, href):
    return urljoin(currentPath, href)


# scrape text and add all links to pathsOpen
def scrape(website, pathsVisited, pathsOpen, linesKnown, href):
    # scrape
    filenameHtml = config.getFilename(website.name, href, "html", ".html")
    filenamePdf = config.getFilename(website.name, href, "html", ".pdf")

    if os.path.exists(filenamePdf):
        isPdf = True
    elif os.path.exists(filenameHtml):
        isPdf = False
    else:
        data = requests.get(href, verify=False, headers=headers)
        isPdf = data.content.startswith(b"%PDF")

        if isPdf:
            f = open(filenamePdf, 'wb')
            f.truncate()
            f.write(data.content)
            f.close()
        else:
            f = open(filenameHtml, 'w')
            f.truncate()
            f.write(data.text)
            f.close()

    # pdf
    text = ""
    if isPdf:
        # parse saved data
        # https://www.geeksforgeeks.org/extract-text-from-pdf-file-using-python/
        f = open(filenamePdf, 'rb')
        try:
            pdfReader = PyPDF2.PdfFileReader(f)
        except PdfReadError as e:
            print(f"Error reading pdf {e}: link {href}")
            return
        pdfPages = pdfReader.numPages

        text = ""
        for i in range(pdfPages):
            pageObj = pdfReader.getPage(i)
            text += pageObj.extractText()
        f.close()

    # is not a pdf
    else:
        # can just read html from file
        if website.waitFunction is None:
            f = open(filenameHtml, 'r')
            html = f.read()
            soup = BeautifulSoup(html, 'lxml')
            f.close()
        # must get html from website if it needs javascript
        else:
            driver.get(href)
            website.waitFunction(driver)
            # filenamePicture = config.getFilename(website.name, href, "html", ".png")
            # driver.save_screenshot(filenamePicture)
            soup = BeautifulSoup(driver.page_source, 'lxml')

        # find all links
        links = soup.find_all("a", href=True)
        for link in links:
            hrefNew = getPath(href, link['href'])
            # skip link: if it does not fit
            if (len(link['href']) == 0) or ("https://" not in hrefNew) or (
                    link['href'][0] == '#') or ('tel:' in link['href']) or ('mailto:' in link['href']):
                continue

            # get href without query (query is the part after '?')
            hrefWithoutQuery = hrefNew
            if "?" in hrefWithoutQuery:
                queryIndex = hrefWithoutQuery.index("?")
                hrefWithoutQuery = hrefWithoutQuery[0:queryIndex]

            # skip link: must include all of pathMustInclude without query
            skip = False
            for pathMust in website.pathMustInclude:
                if pathMust not in hrefWithoutQuery:
                    skip = True
                    break
            # skip: path includes something
            for doNotTake in website.pathMustNotInclude:
                if doNotTake in hrefNew:
                    skip = True
                    break
            for doNotTake in config.websiteExcludeGlobal:
                if doNotTake in hrefNew:
                    skip = True
                    break
            if skip:
                continue

            # do not visit again
            if (hrefNew in pathsVisited) or (hrefNew in pathsOpen):
                continue
            # if os.path.exists(getFilename(websiteName, href, False)):
            #    continue
            pathsOpen.append(hrefNew)

        # scrape text
        # text = soup.get_text('\n', True)
        body = soup.find("body")
        if not body or not body.text:
            return
        text = body.text
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\t+', '\t', text)

    # check already scraped?
    filename = config.getFilename(website.name, href, "text", ".txt")
    if os.path.exists(filename):
        return

    # open file
    f = open(filename, 'w')
    f.truncate()

    # add lines
    lines = text.splitlines()
    for line in lines:
        l = line.strip() + '\n'
        if l in linesKnown:
            continue
        linesKnown.add(l)
        f.write(l)

    f.close()

# go through all websites
websiteCount = 0
websiteLength = len(config.websites)

# load old state
state = {}
stateLoaded = False
filenameState = os.path.join(config.folder, "scrapingState.txt")
filenameStateBackup = os.path.join(config.folder, "scrapingState-old.txt")
if os.path.exists(filenameState):
    stateFile = open(filenameState, 'r')
    jsonString = stateFile.read()
    state = json.loads(jsonString)
    stateLoaded = True
    stateFile.close()

    # save old scraping state into backup file, then delete scraping state
    stateFile = open(filenameStateBackup, 'w')
    stateFile.write(jsonString)
    os.remove(filenameState)  # delete file (state is not valid anymore)
    stateFile.close()

websiteNameCurrent = ""
pathsVisited = []
pathsOpen = []
linesKnown = set()

# scrape
try:
    for website in config.websites:
        websiteCount += 1
        websiteNameCurrent = website.name
        pathsVisited = []
        pathsOpen = [website.firstPath]
        linesKnown = set()
        count = 0

        # load state
        if stateLoaded:
            # state: stopped at this website
            if website.name == state['websiteName']:
                pathsOpen = state['pathsOpen']
                pathsVisited = state['pathsVisited']
                count = len(pathsVisited)
                stateLoaded = False
            # already scraped this
            else:
                continue

        # already have result - skip
        if os.path.exists(os.path.join(config.folderResult, website.name + '.txt')):
            print(
                f"Skipping {websiteCount}/{websiteLength} website {website.name}: Already have text file in result folder")
            continue

        # create folders for the website
        if not os.path.exists(config.folder + website.name):
            os.mkdir(os.path.join(config.folder, website.name))
        if not os.path.exists(os.path.join(config.folder, website.name, 'html')):
            os.mkdir(os.path.join(config.folder, website.name, 'html'))
        if not os.path.exists(os.path.join(config.folder, website.name, 'text')):
            os.mkdir(os.path.join(config.folder, website.name, 'text'))

        while len(pathsOpen) > 0:
            href = pathsOpen[0]
            pathsVisited.append(href)
            count += 1
            print(f"At {websiteCount}/{websiteLength} website {website.name}: visited {count} sub-websites, {len(pathsOpen)} (or more) still missing. Visiting {href}")
            try:
                scrape(website, pathsVisited, pathsOpen, linesKnown, href)
            except requests.exceptions.TooManyRedirects:
                # ignore redirects
                pathsOpen.pop(0)
                continue
            pathsOpen.pop(0)

# on any error: save scraping current state
except (KeyboardInterrupt, Exception) as e:
    print(f"Error {type(e).__name__}: {e}")

    # save: which website, pathsOpen, pathsVisited
    state = {
        'websiteName': websiteNameCurrent,
        'pathsOpen': pathsOpen,
        'pathsVisited': pathsVisited
    }

    stateFile = open(filenameState, 'w')
    jsonString = json.dumps(state)
    stateFile.write(jsonString)
    stateFile.close()

    print(f"Scraping state saved to {filenameState}.")

#driver.quit()
