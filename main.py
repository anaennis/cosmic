import os
import argparse
import logging
from dotenv import load_dotenv
from src.arxiv_retriever import fetch_arxiv_papers, extract_arxiv_metadata
from src.processor import PaperProcessor
from src.llm_handler import GeminiHandler, DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS
from src.seen_store import SeenStore

# Setup basic logging for a more professional feel
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# Hide per-request HTTP and SDK chatter
for noisy_logger in ("httpx", "google_genai"):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # --- CLI Setup ---
    parser = argparse.ArgumentParser(description="ArXiv Paper Ranker and Summarizer")
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
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of papers to fetch from ArXiv before ranking."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Gemini model used for summaries."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Seconds to wait for each summary before falling back to the abstract."
    )
    parser.add_argument(
        "--show-seen",
        action="store_true",
        help="Include papers already shown in previous runs."
    )
    parser.add_argument(
        "--seen-file",
        type=str,
        default=".cosmic_seen.json",
        help="File that records which papers have already been shown."
    )

    args = parser.parse_args()

    # --- Execution ---
    if not api_key:
        logging.error("GOOGLE_API_KEY not found. Please check your .env file.")
        return

    logging.info(f"Fetching papers from ArXiv category: {args.category}...")
    try:
        raw_xml = fetch_arxiv_papers(category=args.category, max_results=args.max_results)
        papers = extract_arxiv_metadata(raw_xml)
    except Exception as e:
        logging.error(f"Failed to fetch papers: {e}")
        return

    if not papers:
        logging.warning("No papers found for the specified date range.")
        return

    seen_store = SeenStore(args.seen_file)
    if not args.show_seen:
        unseen = [p for p in papers if not seen_store.is_seen(p)]
        skipped = len(papers) - len(unseen)
        if skipped:
            logging.info(f"Skipping {skipped} papers already shown (use --show-seen to include them).")
        papers = unseen
        if not papers:
            logging.info("No new papers since your last run.")
            return

    logging.info(f"Ranking {len(papers)} papers by relevance to: '{args.interests}'...")
    processor = PaperProcessor()
    ranked_papers = processor.rank_papers(papers, args.interests)

    logging.info(f"Summarizing top {args.limit} matches...")
    llm = GeminiHandler(api_key, model_id=args.model, timeout=args.timeout)
    
    summarized = []
    top_papers = ranked_papers[:args.limit]
    for i, item in enumerate(top_papers, start=1):
        print("-" * 30)
        print(f"TITLE: {item['metadata']['title']}")
        authors = item['metadata']['authors']
        print(f"AUTHORS: {', '.join(authors[:3])}{' et al.' if len(authors) > 3 else ''}")
        print(f"LINK: {item['metadata']['id']}")
        print(f"RELEVANCE SCORE: {item['similarity']:.4f}")
        logging.info(f"Waiting for summary {i}/{len(top_papers)} from {args.model}...")
        try:
            summary = llm.summarize_paper(item['metadata']['abstract'])
            summarized.append(item['metadata'])
        except Exception as e:
            logging.error(f"Failed to summarize paper: {e}")
            summary = item['metadata']['abstract']
        print(f"SUMMARY: {summary}\n")

    # Papers whose summary failed stay unseen so they show up again next run
    seen_store.mark_seen(summarized)
    seen_store.save()

if __name__ == "__main__":
    main()
