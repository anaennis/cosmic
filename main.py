import os
import argparse
import logging
from dotenv import load_dotenv
from src.arxiv_retriever import fetch_arxiv_papers, extract_arxiv_metadata
from src.processor import PaperProcessor
from src.llm_handler import GeminiHandler

# Setup basic logging for a more professional feel
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # --- CLI Setup ---
    parser = argparse.ArgumentParser(description="ArXiv Paper Ranker and Summarizer")
    
    parser.add_init_subparsers
    parser.add_argument(
        "--interests", 
        type=str, 
        default="I am interested in globular clusters in an extragalactic context.",
        help="The research interests used to rank papers."
    )
    parser.add_argument(
        "--category", 
        type=str, 
        default="astro-ph.GA", 
        help="ArXiv category to search (e.g., astro-ph.SR, cs.LG)."
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=3, 
        help="Number of top papers to summarize."
    )

    args = parser.parse_args()

    # --- Execution ---
    if not api_key:
        logging.error("GOOGLE_API_KEY not found. Please check your .env file.")
        return

    logging.info(f"Fetching papers from ArXiv category: {args.category}...")
    try:
        raw_xml = fetch_arxiv_papers(category=args.category)
        papers = extract_arxiv_metadata(raw_xml)
    except Exception as e:
        logging.error(f"Failed to fetch papers: {e}")
        return

    if not papers:
        logging.warning("No papers found for the specified date range.")
        return

    logging.info(f"Ranking {len(papers)} papers by relevance to: '{args.interests}'...")
    processor = PaperProcessor()
    ranked_papers = processor.rank_papers(papers, args.interests)

    logging.info(f"Summarizing top {args.limit} matches...")
    llm = GeminiHandler(api_key)
    
    for item in ranked_papers[:args.limit]:
        print("-" * 30)
        print(f"TITLE: {item['metadata']['title']}")
        print(f"RELEVANCE SCORE: {item['similarity']:.4f}")
        summary = llm.summarize_paper(item['metadata']['abstract'])
        print(f"SUMMARY: {summary}\n")

if __name__ == "__main__":
    main()