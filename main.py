import os
import argparse
import sys
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from src.arxiv_retriever import fetch_arxiv_papers, extract_arxiv_metadata
from src.processor import PaperProcessor
from src.llm_handler import GeminiHandler, DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS, DEFAULT_THINKING_LEVEL, THINKING_LEVELS
from src.seen_store import SeenStore
from src.digest import format_authors, render_html, render_markdown, write_digest
from src.emailer import email_settings_from_env, send_digest_email

# Setup basic logging for a more professional feel
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# Hide per-request HTTP and SDK chatter
for noisy_logger in ("httpx", "google_genai"):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

def main():
    """Runs the pipeline; returns a process exit code (non-zero on failure)."""
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
        nargs="+",
        default=["astro-ph.GA"],
        help="One or more ArXiv categories to search (e.g., astro-ph.GA astro-ph.CO)."
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=3, 
        help="Number of top papers to summarize."
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Only summarize papers with at least this relevance score (0-1, e.g. 0.35)."
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
        "--thinking",
        choices=THINKING_LEVELS,
        default=DEFAULT_THINKING_LEVEL,
        help="How much the model reasons before answering; lower is faster."
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
    parser.add_argument(
        "--output",
        type=str,
        help="Also save results to this file: HTML if it ends in .html, Markdown otherwise."
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Email the digest (settings come from EMAIL_USER, EMAIL_APP_PASSWORD and EMAIL_TO)."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Don't print papers in the terminal (requires --output or --email)."
    )

    args = parser.parse_args()
    if args.quiet and not (args.output or args.email):
        parser.error("--quiet needs --output or --email, otherwise the results would go nowhere.")

    # --- Execution ---
    if not api_key:
        logging.error("GOOGLE_API_KEY not found. Please check your .env file.")
        return 1

    email_settings = None
    if args.email:
        try:
            email_settings = email_settings_from_env()
        except ValueError as e:
            logging.error(f"{e}. Add them to your .env file (or GitHub secrets).")
            return 1

    logging.info(f"Fetching papers from ArXiv categories: {', '.join(args.category)}...")
    try:
        raw_xml = fetch_arxiv_papers(categories=args.category, max_results=args.max_results)
        papers = extract_arxiv_metadata(raw_xml)
    except Exception as e:
        logging.error(f"Failed to fetch papers: {e}")
        return 1

    if len(papers) >= args.max_results:
        logging.warning(f"Got the maximum of {args.max_results} papers; some may be missing. "
                        "Raise --max-results to fetch more.")

    if not papers:
        logging.warning("No papers found for the specified date range.")
        return 0

    seen_store = SeenStore(args.seen_file)
    if not args.show_seen:
        unseen = [p for p in papers if not seen_store.is_seen(p)]
        skipped = len(papers) - len(unseen)
        if skipped:
            logging.info(f"Skipping {skipped} papers already shown (use --show-seen to include them).")
        papers = unseen
        if not papers:
            logging.info("No new papers since your last run.")
            return 0

    logging.info(f"Ranking {len(papers)} papers by relevance to: '{args.interests}'...")
    processor = PaperProcessor()
    ranked_papers = processor.rank_papers(papers, args.interests)

    relevant = [p for p in ranked_papers if p['similarity'] >= args.min_score]
    if not relevant:
        logging.info(f"No papers scored at least {args.min_score} "
                     f"(best was {ranked_papers[0]['similarity']:.2f}).")
        return 0
    if len(relevant) < len(ranked_papers):
        logging.info(f"{len(relevant)} of {len(ranked_papers)} papers scored at least {args.min_score}.")
    top_papers = relevant[:args.limit]

    logging.info(f"Summarizing top {len(top_papers)} matches in parallel (this can take a minute)...")
    llm = GeminiHandler(api_key, model_id=args.model, timeout=args.timeout,
                        thinking_level=args.thinking)

    summarized = []
    results = []
    # Request all summaries at once; results print in rank order as they arrive
    with ThreadPoolExecutor(max_workers=max(len(top_papers), 1)) as pool:
        futures = [pool.submit(llm.summarize_paper, item['metadata']['abstract'])
                   for item in top_papers]
        for i, (item, future) in enumerate(zip(top_papers, futures), start=1):
            try:
                summary = future.result()
                summarized.append(item['metadata'])
            except Exception as e:
                logging.error(f"Failed to summarize paper {i}: {e}")
                summary = item['metadata']['abstract']
            results.append({**item, 'summary': summary})
            if args.quiet:
                continue
            print("-" * 30)
            print(f"TITLE: {item['metadata']['title']}")
            print(f"AUTHORS: {format_authors(item['metadata']['authors'])}")
            print(f"LINK: {item['metadata']['id']}")
            print(f"RELEVANCE SCORE: {item['similarity']:.4f}")
            print(f"SUMMARY: {summary}\n")

    header = {
        'date': datetime.date.today().isoformat(),
        'categories': args.category,
        'interests': args.interests,
    }
    exit_code = 0
    if args.output:
        try:
            write_digest(args.output, results, header)
            logging.info(f"Saved digest to {args.output}")
        except OSError as e:
            logging.error(f"Could not write digest: {e}")
            exit_code = 1

    if email_settings:
        subject = f"Cosmic digest — {header['date']}: {len(results)} paper{'s' if len(results) != 1 else ''}"
        try:
            send_digest_email(subject, render_html(results, header),
                              render_markdown(results, header), email_settings)
            logging.info(f"Emailed digest to {email_settings['to']}")
        except Exception as e:
            logging.error(f"Could not send email: {e}")
            exit_code = 1

    # Papers whose summary failed stay unseen so they show up again next run,
    # and nothing is marked if the digest couldn't be saved or sent
    if exit_code == 0:
        seen_store.mark_seen(summarized)
        seen_store.save()
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
