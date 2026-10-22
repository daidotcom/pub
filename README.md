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
