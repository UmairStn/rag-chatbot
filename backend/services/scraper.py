# Website crawling logic
import requests
from bs4 import BeautifulSoup

def scrape_website(WEBSITE_URL):
    headers = {"User-Agent": "Mozilla/5.0"} # Pretend to be a real user browser
    response = requests.get(WEBSITE_URL, headers=headers)
    
    # Parse the HTML code
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove 'Noise' (elements that don't help the AI answer questions)
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose() # Physically delete these from the parsed content
        
    # Extract the clean text, using a space to separate words
    clean_text = soup.get_text(separator=' ', strip=True)
    return clean_text