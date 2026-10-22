# NEWS FLOW
Japanese auto-rotating headlines for iPhone, hosted on GitHub Pages.

## Setup
1. Create a **public** GitHub repository named `news-flow`.
2. Upload `index.html`, `fetch_news.py`, and `.github/workflows/news.yml` preserving paths. (The ZIP contains them.)
3. In repository **Settings > Actions > General > Workflow permissions**, choose **Read and write permissions** if available. The workflow also declares `contents: write`.
4. Go to **Actions > Update Japanese news > Run workflow** to generate `news.json` for the first time.
5. In **Settings > Pages**, select **Deploy from a branch**, branch **main**, folder **/(root)**, then Save.
6. Visit `https://YOUR_USERNAME.github.io/news-flow/` on iPhone Safari.

The workflow is scheduled every 30 minutes, but GitHub may delay scheduled runs. Google News RSS availability and links can change. GitHub Pages is public. Keep the browser foregrounded for reliable automatic switching.

## Local development

Run `python3 -m http.server 8000` and open the local server in your browser.
Run `python3 fetch_news.py` to refresh `news.json`. The same script runs in
GitHub Actions every 30 minutes (scheduled runs may be delayed).

Each entry in `articles` contains `title`, `link`, `category`, `published`,
`source`, and `summary`. Sources include Yahoo! News (including sports), NHK, and ITmedia.
Summaries use descriptions supplied by RSS feeds or article pages, not
generated text or full articles. Feeds are interleaved so sports and each
publisher appear early in the rotation. If an article has no
available description, the page keeps its headline and offers the original
article link. Headlines and summaries rotate together, with a default interval
of 10 seconds and 5/10/15/20-second controls.

Run fetcher checks with `python3 -m unittest discover -s tests -v`.
