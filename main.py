import os
from dotenv import load_dotenv
from src.arxiv_retriever import fetch_arxiv_papers, extract_arxiv_metadata
from src.processor import PaperProcessor
from src.llm_handler import GeminiHandler

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    interests = "I am interested in globular clusters in an extragalactic context."

    # 1. Fetch and Parse
    print("Fetching papers from ArXiv...")
    raw_xml = fetch_arxiv_papers()
    papers = extract_arxiv_metadata(raw_xml)

    # 2. Process and Rank
    print("Ranking papers by relevance...")
    processor = PaperProcessor()
    ranked_papers = processor.rank_papers(papers, interests)

    # 3. Summarize Top Papers
    print("Summarizing top matches...")
    llm = GeminiHandler(api_key)
    for item in ranked_papers[:3]:
        print(f"\nTitle: {item['metadata']['title']}")
        summary = llm.summarize_paper(item['metadata']['abstract'])
        print(f"Summary: {summary}")

if __name__ == "__main__":
    main()
