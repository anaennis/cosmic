import datetime
import pytz
import requests
import feedparser
import xml.etree.ElementTree as ET

def get_arxiv_dates():
    """Calculates the date range for arXiv submissions."""
    eastern = pytz.timezone('US/Eastern')
    now_eastern = datetime.datetime.now(eastern)
    today = now_eastern.date()

    if now_eastern.hour < 20:
        today -= datetime.timedelta(days=1)

    while today.weekday() >= 5: # Skip weekends
        today -= datetime.timedelta(days=1)

    start_date = (today - datetime.timedelta(days=1)).strftime("%Y%m%d") + "1400"
    end_date = today.strftime("%Y%m%d") + "1400"
    return start_date, end_date

def fetch_arxiv_papers(category="astro-ph.GA", max_results=100):
    """Fetches raw XML data from ArXiv."""
    start_date, end_date = get_arxiv_dates()
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=cat:{category}+AND+submittedDate:[{start_date}+TO+{end_date}]"
    url = f"{base_url}{search_query}&sortBy=submittedDate&sortOrder=ascending&max_results={max_results}"
    
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_arxiv_metadata(xml_response):
    """Parses the arXiv Atom feed into a structured list of dictionaries."""
    root = ET.fromstring(xml_response)
    ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
    papers = []
    for entry in root.findall('atom:entry', ns):
        papers.append({
            'title': entry.find('atom:title', ns).text.strip(),
            'id': entry.find('atom:id', ns).text.strip(),
            'abstract': entry.find('atom:summary', ns).text.strip(),
            'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
            'published': entry.find('atom:published', ns).text,
            'categories': [c.get('term') for c in entry.findall('atom:category', ns)]
        })
    return papers
