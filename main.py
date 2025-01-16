import requests
from bs4 import BeautifulSoup
import csv
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to extract URLs from a given XML file
def extract_urls_from_xml(xml_file):
    with open(xml_file, 'r') as file:
        soup = BeautifulSoup(file.read(), 'xml')
        urls = [url.text.strip() for url in soup.find_all('loc')]
    return urls

# Function to crawl a given URL and find links to a specific domain
def crawl_url(url, domain):
    try:
        print(f"Crawling: {url}.")

        # Send a request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Build the regex pattern
        domain_regex = rf"https?://(?:[wW]{3}\.)?.*{re.escape(domain)}.*"

        # Find all <a> tags with href attributes
        links = soup.find_all('a', href=True)

        # Extract links that point to the specified domain using regex and save the full URL
        domain_links = [(link['href'], url) for link in links if re.search(domain_regex, link['href'])]

        return domain_links

    except requests.exceptions.RequestException as e:
        print(f"Error crawling {url}: {e}")
        return []

# Function to save links to a CSV file
def save_links_to_csv(links, csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Referrer'])
        for link, referrer in links:
            writer.writerow([link, referrer])

# Main function
def main():
    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('xml_file', help='Path to the XML file')
    parser.add_argument('domain', help='Target domain (e.g., example.com)')
    parser.add_argument('-t', '--threads', type=int, default=8, help='Number of threads to use (default: 8)')
    args = parser.parse_args()

    # Extract URLs from the XML file
    urls = extract_urls_from_xml(args.xml_file)

    all_domain_links = []
    # Crawl each URL using multiple threads
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(crawl_url, url, args.domain) for url in urls]
        for future in as_completed(futures):
            all_domain_links.extend(future.result())

    # Save the links to a CSV file
    save_links_to_csv(all_domain_links, 'domain_links.csv')

# Call the main function
if __name__ == "__main__":
    main()