import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pymongo import MongoClient
import queue

# Initialize MongoDB client
client = MongoClient('localhost', 27017)
db = client['web_crawler_db']
pages_collection = db['pages']

# Set the starting URL and target URL
starting_url = "https://www.cpp.edu/sci/computer-science/"
target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"

visited = set()  # Set to track visited URLs
frontier = queue.Queue()  # Queue for frontier (URLs to visit)
frontier.put(starting_url)  # Add starting URL to the frontier


# Function to save page data to MongoDB
def save_page_to_mongo(url, html):
    page_data = {
        'url': url,
        'html': html
    }
    pages_collection.insert_one(page_data)  # Insert into MongoDB


# Function to check if the target page is found
def target_page_found(html):
    soup = BeautifulSoup(html, 'html.parser')
    heading = soup.find('h1', class_='cpp-h1')
    return heading and 'Permanent Faculty' in heading.text


# Function to process a single page
def process_page(url):
    if url in visited:
        return False  # Skip if already visited

    visited.add(url)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return False

    html = response.text
    save_page_to_mongo(url, html)  # Save the page to MongoDB

    if target_page_found(html):  # Stop if the target page is found
        print(f"Target page found: {url}")
        while not frontier.empty():
            frontier.get()  # Clear the frontier
        return True

    # Otherwise, collect all links and add them to the frontier
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=True)
    for link in links:
        link_url = link['href']
        full_url = urljoin(url, link_url)  # Resolve relative URL to absolute URL
        parsed_url = urlparse(full_url)

        # Check if the link is an HTML page (ignoring other resources like images, PDFs)
        if parsed_url.scheme in ['http', 'https'] and (full_url.endswith('.html') or full_url.endswith('.shtml')):
            if full_url not in visited and full_url not in list(frontier.queue):
                frontier.put(full_url)

    return False


# Crawler
def crawler():
    while not frontier.empty():
        url = frontier.get()  # Get the next URL from the frontier
        if process_page(url):  # If target page is found, stop the crawler
            break

    print("Crawling finished.")


# Start the crawler
if __name__ == "__main__":
    crawler()
