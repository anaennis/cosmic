import html


def format_authors(authors, max_shown=3):
    """Shows the first few authors, then 'et al.'."""
    shown = ', '.join(authors[:max_shown])
    return shown + (' et al.' if len(authors) > max_shown else '')


def render_markdown(results, header):
    """Renders results as a Markdown digest.

    `results` is a list of {'metadata', 'similarity', 'summary'} dicts and
    `header` a dict with 'date', 'categories' and 'interests'.
    """
    lines = [
        f"# Cosmic digest — {header['date']}",
        "",
        f"**Categories:** {', '.join(header['categories'])}  ",
        f"**Interests:** {header['interests']}",
        "",
    ]
    for item in results:
        paper = item['metadata']
        lines += [
            f"## [{paper['title']}]({paper['id']})",
            "",
            f"*{format_authors(paper['authors'])}* · relevance {item['similarity']:.2f}",
            "",
            item['summary'],
            "",
        ]
    return "\n".join(lines)


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cosmic digest — {date}</title>
<script>window.MathJax = {{ tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] }} }};</script>
<script async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.js"></script>
<style>
  :root {{ --bg: #fbfaf7; --text: #1f1f1f; --muted: #6b6b6b; --accent: #3a5bbf; --rule: #e4e1da; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #16171a; --text: #e8e6e1; --muted: #9a978f; --accent: #8fa8f0; --rule: #2c2d31; }}
  }}
  body {{ background: var(--bg); color: var(--text); font: 17px/1.6 Georgia, serif;
         max-width: 44rem; margin: 0 auto; padding: 2rem 16px; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
  .meta {{ color: var(--muted); font-size: 0.95rem; }}
  article {{ border-top: 1px solid var(--rule); padding: 1.25rem 0; }}
  h2 {{ font-size: 1.15rem; line-height: 1.35; margin: 0 0 0.35rem; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>Cosmic digest — {date}</h1>
<p class="meta">{categories}<br>{interests}</p>
{articles}
</body>
</html>
"""

ARTICLE_TEMPLATE = """<article>
  <h2><a href="{link}">{title}</a></h2>
  <p class="meta">{authors} · relevance {score:.2f}</p>
  <p>{summary}</p>
</article>"""


def render_html(results, header):
    """Renders results as a standalone HTML page (same inputs as render_markdown)."""
    esc = html.escape
    articles = "\n".join(
        ARTICLE_TEMPLATE.format(
            link=esc(item['metadata']['id']),
            title=esc(item['metadata']['title']),
            authors=esc(format_authors(item['metadata']['authors'])),
            score=item['similarity'],
            summary=esc(item['summary']),
        )
        for item in results
    )
    return HTML_TEMPLATE.format(
        date=esc(header['date']),
        categories=esc(', '.join(header['categories'])),
        interests=esc(header['interests']),
        articles=articles,
    )


def write_digest(path, results, header):
    """Writes an HTML digest for .html/.htm paths and Markdown otherwise."""
    render = render_html if path.lower().endswith(('.html', '.htm')) else render_markdown
    with open(path, 'w', encoding='utf-8') as f:
        f.write(render(results, header))
