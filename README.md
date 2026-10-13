# 🌌 Cosmic

**AI-powered research paper discovery tool for fast, intelligent literature exploration**

Cosmic is a lightweight, modular system that helps researchers and students quickly discover relevant scientific papers using modern LLM workflows. It ingests a user query, retrieves semantically related papers from arXiv, and summarizes key insights — all through a clean Python pipeline.

This project was developed as part of the **Google 5‑Day GenAI Intensive Capstone**, and is designed to be easy to extend, adapt, and integrate into larger research workflows.

## ✨ Features

- **Semantic search** over arXiv abstracts using embeddings
- **LLM-powered summarization** of retrieved papers via Google Gemini
- **Configurable pipeline** with modular components
- **Simple CLI interface** for quick experimentation
- **Lightweight dependencies** — runs locally with minimal setup
- **Smart date filtering** — automatically retrieves recent papers (skipping weekends)

## 📁 Project Structure

```
cosmic/
├── LICENSE
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
└── src/
    ├── arxiv_retriever.py    # Fetch papers from arXiv API
    ├── llm_handler.py        # Google Gemini integration
    └── processor.py          # Semantic ranking using embeddings
└── tests/
    └── test_arxiv_retriever.py  # Date-window and parsing tests
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- A Google API key (for Gemini LLM)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/anaennis/cosmic.git
   cd cosmic
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key:**
   
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```

   You can obtain a Google API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### Usage

Run the main script with optional CLI flags to customize the search:

```bash
# Basic usage with defaults
python main.py

# Customize your search
python main.py --interests "machine learning for drug discovery" --category "cs.LG" --limit 5
```

**Available CLI flags:**
- `--interests`: Research interests for semantic ranking (default: globular clusters)
- `--category`: arXiv category to search (default: `astro-ph.GA`). See [arXiv categories](https://arxiv.org/category_taxonomy)
- `--limit`: Number of top papers to summarize (default: 3)
- `--max-results`: Maximum number of papers to fetch from arXiv before ranking (default: 100)
- `--model`: Gemini model used for summaries (default: `gemini-2.5-flash`)

**Example output:**
```
INFO: Fetching papers from ArXiv category: astro-ph.GA...
INFO: Ranking 47 papers by relevance to: 'I am interested in globular clusters in an extragalactic context.'...
INFO: Summarizing top 3 matches...
------------------------------
TITLE: Globular Clusters in the Virgo Galaxy Cluster
AUTHORS: A. Author, B. Author, C. Author et al.
LINK: http://arxiv.org/abs/2610.01234v1
RELEVANCE SCORE: 0.7234
SUMMARY: This paper presents a comprehensive study of globular cluster systems...
```

### Running Tests

```bash
python -m unittest discover -s tests -t .
```

The tests cover the arXiv date-window logic and feed parsing, and need no network or API key.

### Customization

Beyond CLI flags, you can also modify:
- **Embedding model**: Change `model_name` in [processor.py](src/processor.py) (default: `all-MiniLM-L6-v2`)

## ⚙️ Configuration Options

| Component | Options | Default |
|-----------|---------|---------|
| Embedding Model | Any Sentence-Transformers model | `all-MiniLM-L6-v2` |
| arXiv Category | Any valid arXiv category | `astro-ph.GA` |
| Max Results (`--max-results`) | 1-2000 | 100 |
| LLM Model (`--model`) | Any Google Gemini model | `gemini-2.5-flash` |
| Top Papers | Any number | 3 |

## 📚 Use Cases

- **Rapid literature review** — Stay up-to-date with recent publications in your field
- **Exploring unfamiliar research areas** — Get quick overviews of new topics
- **Identifying related work** — Find relevant papers for your project or manuscript
- **Teaching and academic outreach** — Help students discover research papers
- **Bootstrapping datasets** — Collect papers for downstream ML tasks

## 🛠️ Technical Details

**Semantic Ranking**: Uses sentence-transformers to encode user interests and paper abstracts, then computes cosine similarity to rank papers by relevance.

**Vectorized Batch Encoding**: Employs efficient batch processing for embedding generation, encoding all paper abstracts in a single model call rather than iteratively. This reduces computational overhead and significantly improves performance for large paper sets.

**LLM Integration**: Leverages the Google Gemini API (default `gemini-2.5-flash`, configurable with `--model`) for generating concise, readable summaries of complex academic abstracts.

**Date Filtering**: Automatically calculates the submission window for the most recently announced arXiv batch (submissions close at 1400 ET, announced at 2000 ET), skipping weekends so Monday's batch covers Friday 1400 → Monday 1400.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs or suggest features via [Issues](https://github.com/anaennis/cosmic/issues)
- Submit pull requests with improvements
- Extend the system with new data sources or LLM providers

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Originally built as part of the **Google 5-Day GenAI Intensive Capstone** program in collaboration with Ashley Bemis. Thanks to the Google team for the excellent learning experience!


