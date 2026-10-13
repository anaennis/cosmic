import datetime
import pytz
import requests
import xml.etree.ElementTree as ET

def get_arxiv_dates(now=None):
    """Calculates the date range for arXiv submissions.

    `now` is an optional timezone-aware datetime (defaults to the current time).
    """
    eastern = pytz.timezone('US/Eastern')
    now_eastern = (now or datetime.datetime.now(eastern)).astimezone(eastern)
    today = now_eastern.date()

    if now_eastern.hour < 20:
        today -= datetime.timedelta(days=1)

    while today.weekday() >= 5: # Skip weekends
        today -= datetime.timedelta(days=1)

    # The window opens at the previous weekday's cutoff, so Monday's batch
    # covers Friday 1400 -> Monday 1400.
    previous = today - datetime.timedelta(days=1)
    while previous.weekday() >= 5:
        previous -= datetime.timedelta(days=1)

    start_date = previous.strftime("%Y%m%d") + "1400"
    end_date = today.strftime("%Y%m%d") + "1400"
    return start_date, end_date

def _clean(text):
    """Collapses the line breaks and indentation arXiv puts inside titles/abstracts."""
    return " ".join(text.split())

def build_query_url(categories, start_date, end_date, max_results=100):
    """Builds the arXiv API URL for one or more categories within a date window."""
    if isinstance(categories, str):
        categories = [categories]
    # Parentheses are URL-encoded so the OR-group survives the query string
    category_query = "+OR+".join(f"cat:{c}" for c in categories)
    if len(categories) > 1:
        category_query = f"%28{category_query}%29"
    search_query = f"search_query={category_query}+AND+submittedDate:[{start_date}+TO+{end_date}]"
    return (f"https://export.arxiv.org/api/query?{search_query}"
            f"&sortBy=submittedDate&sortOrder=ascending&max_results={max_results}")

def fetch_arxiv_papers(categories="astro-ph.GA", max_results=100, timeout=30):
    """Fetches raw XML data from ArXiv for one category or a list of them."""
    start_date, end_date = get_arxiv_dates()
    url = build_query_url(categories, start_date, end_date, max_results)

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text

def extract_arxiv_metadata(xml_response):
    """Parses the arXiv Atom feed into a structured list of dictionaries."""
    root = ET.fromstring(xml_response)
    ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
    papers = []
    for entry in root.findall('atom:entry', ns):
        papers.append({
            'title': _clean(entry.find('atom:title', ns).text),
            'id': entry.find('atom:id', ns).text.strip(),
            'abstract': _clean(entry.find('atom:summary', ns).text),
            'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
            'published': entry.find('atom:published', ns).text,
            'categories': [c.get('term') for c in entry.findall('atom:category', ns)]
        })
    return papers
