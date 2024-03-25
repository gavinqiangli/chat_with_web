"""Selenium web scraping module."""
from __future__ import annotations


from pathlib import Path
from sys import platform

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from scraping import scrape_skills, processing as summary
from scraping.processing.html import extract_hyperlinks


FILE_DIR = Path(__file__).parent


def browse_website(url: str) -> tuple[str, list[str]]:
    """Browse a website and return the answer and links to the user

    Args:
        url (str): The url of the website to browse
        question (str): The question asked by the user

    Returns:
        Tuple[str, WebDriver]: The answer and links to the user and the webdriver
    """

    if not url:
        return "A URL was not specified, cancelling request to browse website.", None

    selenium_web_browser = "chrome"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"

    driver, text = scrape_text_with_selenium(selenium_web_browser, user_agent, url)
    add_header(driver)

    links = scrape_links_with_selenium(driver, url)
    print(f"scraped links with selenium: {links}")

    # Limit links to 30
    if len(links) > 30:
        links = links[:30]

    # write_to_file('research-{0}.txt'.format(url), summary_text + "\nSource Links: {0}\n\n".format(links))

    close_browser(driver)
    return text, links

    

def scrape_text_with_selenium(selenium_web_browser: str, user_agent: str, url: str) -> tuple[WebDriver, str]:
    """Scrape text from a website using selenium

    Args:
        url (str): The url of the website to scrape
        selenium_web_browser (str): The web browser used to scrape
        user_agent (str): The user agent used when scraping

    Returns:
        Tuple[WebDriver, str]: The webdriver and the text scraped from the website
    """

    options_available = {
        "chrome": ChromeOptions,
        "safari": SafariOptions,
        "firefox": FirefoxOptions,
    }

    options = options_available[selenium_web_browser]()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--headless")
    options.add_argument("--enable-javascript")

    if selenium_web_browser == "firefox":
        driver = webdriver.Firefox(options=options)
    elif selenium_web_browser == "safari":
        # Requires a bit more setup on the users end
        # See https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari
        driver = webdriver.Safari(options=options)
    else:
        if platform == "linux" or platform == "linux2":
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("prefs", {"download_restrictions": 3})
        
        # run Selenium with local brower for local test
        # driver = webdriver.Chrome(options=options)
        # run Selenium on streamlit cloud, refer to https://selenium.streamlit.app/
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)

    print(f"scraping url {url}...")
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # check if url is a pdf or arxiv link
    if url.endswith(".pdf"):
        text = scrape_skills.scrape_pdf_with_pymupdf(url)
    elif "arxiv" in url:
        # parse the document number from the url
        doc_num = url.split("/")[-1]
        text = scrape_skills.scrape_pdf_with_arxiv(doc_num)
    else:
        # Get the HTML content directly from the browser's DOM
        page_source = driver.execute_script("return document.body.outerHTML;")
        soup = BeautifulSoup(page_source, "html.parser")

        for script in soup(["script", "style"]):
            script.extract()

        # text = soup.get_text()
        text = get_text(soup)

    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return driver, text


def get_text(soup):
    """Get the text from the soup

    Args:
        soup (BeautifulSoup): The soup to get the text from

    Returns:
        str: The text from the soup
    """
    text = ""
    tags = ["h1", "h2", "h3", "h4", "h5", "p"]
    for element in soup.find_all(tags):  # Find all the <p> elements
        text += element.text + "\n\n"
    return text


def scrape_links_with_selenium(driver: WebDriver, url: str) -> list[str]:
    """Scrape links from a website using selenium

    Args:
        driver (WebDriver): The webdriver to use to scrape the links

    Returns:
        List[str]: The links scraped from the website
    """
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    hyperlinks = extract_hyperlinks(soup, url)

    return hyperlinks


def close_browser(driver: WebDriver) -> None:
    """Close the browser

    Args:
        driver (WebDriver): The webdriver to close

    Returns:
        None
    """
    driver.quit()


def add_header(driver: WebDriver) -> None:
    """Add a header to the website

    Args:
        driver (WebDriver): The webdriver to use to add the header

    Returns:
        None
    """
    driver.execute_script(open(f"{FILE_DIR}/js/overlay.js", "r").read())
