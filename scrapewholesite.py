from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import requests
import json
import os
import html2text
from scraping.web_scrape import browse_website

load_dotenv()
brwoserless_api_key = os.getenv("BROWSERLESS_API_KEY")


# 1. Scrape raw HTML

def scrape_website(url: str):

    print("Scraping website...")
    # Define the headers for the request
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
    }

    # Define the data to be sent in the request
    data = {
        "url": url,
        "elements": [{
            "selector": "body"
        }]
    }

    # Convert Python object to JSON string
    data_json = json.dumps(data)

    # Send the POST request
    response = requests.post(
        f"https://chrome.browserless.io/scrape?token={brwoserless_api_key}",
        headers=headers,
        data=data_json
    )

    # Check the response status code
    if response.status_code == 200:
        # Decode & Load the string as a JSON object
        result = response.content
        data_str = result.decode('utf-8')
        data_dict = json.loads(data_str)

        # Extract the HTML content from the dictionary
        html_string = data_dict['data'][0]['results'][0]['html']

        return html_string
    else:
        print(f"HTTP request failed with status code {response.status_code}")
        return


# 2. Convert html to markdown

def convert_html_to_markdown(html):

    # Create an html2text converter
    converter = html2text.HTML2Text()

    # Configure the converter
    converter.ignore_links = False

    # Convert the HTML to Markdown
    markdown = converter.handle(html)

    return markdown


# Turn https://developers.webflow.com/docs/getting-started-with-apps to https://developers.webflow.com

def get_base_url(url):
    parsed_url = urlparse(url)

    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url


# Turn relative url to absolute url in html
def convert_to_absolute_url(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')

    for img_tag in soup.find_all('img'):
        if img_tag.get('src'):
            src = img_tag.get('src')
            if src.startswith(('http://', 'https://')):
                continue
            absolute_url = urljoin(base_url, src)
            img_tag['src'] = absolute_url
        elif img_tag.get('data-src'):
            src = img_tag.get('data-src')
            if src.startswith(('http://', 'https://')):
                continue
            absolute_url = urljoin(base_url, src)
            img_tag['data-src'] = absolute_url

    for link_tag in soup.find_all('a'):
        href = link_tag.get('href')
        if href is not None and href.startswith(('http://', 'https://')):
            continue
        absolute_url = urljoin(base_url, href)
        link_tag['href'] = absolute_url

    updated_html = str(soup)

    return updated_html


def get_markdown_from_url(url):
    base_url = get_base_url(url)
    html = scrape_website(url)
    updated_html = convert_to_absolute_url(html, base_url)
    markdown = convert_html_to_markdown(updated_html)

    return markdown


# Function to crawl a website
# method 1: use expensive but well functional "browserless.io"
def crawl_site(site_url, max_depth=3, max_url=20):
    if site_url is not None and not site_url.startswith(('http://', 'https://')):
        site_url = "https://" + site_url
    
    base_url = get_base_url(site_url)
    print(f"base_url is: {base_url}")

    visited_urls = set()
    site_content = []

    def recursive_crawl(url, depth):
        if depth > max_depth:
            return
        
        if len(visited_urls) > max_url:
            return

        if url in visited_urls:
            return

        visited_urls.add(url)
        print(f"Added URL: {url}")   

        # method 1: use expensive browserless.io
        html = scrape_website(url)
        if html is None:
            return
        
        markdown = convert_html_to_markdown(html)
        site_content.append(markdown + "\n\n")

        soup = BeautifulSoup(html, 'html.parser')
        print(f"Crawled URL: {url}")  
        # Process the page content here or extract data
        # # Find all anchor tags and crawl their href attributes
        for link in soup.find_all('a'):
            next_link = link.get('href')
            if next_link is not None and next_link.startswith('/') or next_link.startswith(base_url):
                next_url = urljoin(base_url, next_link)
                recursive_crawl(next_url, depth + 1)


    recursive_crawl(base_url, 0)

    # Iterate through the list of URLs
    print(f"visited_urls are: {visited_urls}")

    return site_content

# method 2: use free selenium, also works pretty well
def crawl_site_selenium(site_url, max_depth=3, max_url=120):
    if site_url is not None and not site_url.startswith(('http://', 'https://')):
        site_url = "https://" + site_url
    
    base_url = get_base_url(site_url)
    print(f"base_url is: {base_url}")

    visited_urls = set()
    site_content = []

    def recursive_crawl(url, depth):
        if depth > max_depth:
            return
        
        if len(visited_urls) > max_url:
            return

        if url in visited_urls:
            return

        visited_urls.add(url)
        print(f"Added URL: {url}")   

        # method 2: use free selenium
        markdown, links = browse_website(url)
        if markdown:
            site_content.append(markdown)

        print(f"Crawled URL: {url}")  
        # Process the page content here or extract data
        # # Find all anchor tags and crawl their href attributes
        for link in links:
            next_link = link
            if next_link is not None and next_link.startswith('/') or next_link.startswith(base_url):
                next_url = urljoin(base_url, next_link)
                recursive_crawl(next_url, depth + 1)


    recursive_crawl(base_url, 0)

    # Iterate through the list of URLs
    print(f"visited_urls are: {visited_urls}")

    return site_content