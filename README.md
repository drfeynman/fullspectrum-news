# FullSpectrum.News

**"See every shade of the story"**

A news visualization website that displays top stories on a **spectrum matrix** — a 3×3 grid showing how different sources cover the same story based on political leaning (left/center/right) and tone (optimistic/neutral/pessimistic).

---

## Features

- 🎯 **Spectrum Matrix** — See all coverage at a glance on a 2D grid
- 🌍 **Four Regions** — Switch between Global, US, Singapore, and India
- 📰 **9 Stories per Region** — Featured story with large matrix, 8 smaller cards below
- 🔍 **Hover for Headlines** — Quick preview without leaving the page
- 🔄 **Click to Swap** — Any story can become the featured story
- 🌙 **Dark Mode** — Easy on the eyes
- 📱 **Responsive Design** — Works on desktop, tablet, and mobile
- ⚡ **Static Site** — Fast loading, no server required

---

## Project Structure

```
fullspectrum-news/
├── index.html              # Main website (self-contained HTML/CSS/JS)
├── news_data.json          # Generated news data (created by build script)
├── data/
│   └── sources.json        # Source bias mappings
├── scripts/
│   └── build_news.py       # News fetching and processing script
└── README.md
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install feedparser requests beautifulsoup4 python-dateutil

# Optional: For enhanced AI analysis
pip install anthropic
```

### 2. Run the Build Script

The script fetches news from Google News RSS and other regional sources (no API key required):

```bash
cd fullspectrum-news
python scripts/build_news.py
```

This generates `news_data.json` with news for all four regions (Global, US, Singapore, India).

> **Optional:** Set `ANTHROPIC_API_KEY` for enhanced AI-powered tone analysis.

> **Note:** If no API keys are set, the script falls back to RSS feeds from major news outlets (BBC, NPR, Guardian, NYT, etc.). This works but may not rank stories by global importance as effectively.

### 3. Run the Build Script

```bash
cd fullspectrum-news
python scripts/build_news.py
```

This generates `news_data.json` with the latest news.

### 3. Serve Locally

```bash
# Python 3
python -m http.server 8000

# Then open http://localhost:8000
```

---

## Deployment Options

### Option A: GitHub Pages + GitHub Actions (Recommended)

This is the simplest way to host a static site with scheduled updates.

#### 1. Create a GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/fullspectrum-news.git
git push -u origin main
```

#### 2. Create GitHub Actions Workflow

Create `.github/workflows/build.yml`:

```yaml
name: Build News

on:
  schedule:
    # Run at 2:00 UTC (10:00 SGT) and 13:00 UTC (21:00 SGT)
    - cron: '0 2 * * *'
    - cron: '0 13 * * *'
  workflow_dispatch:  # Allow manual triggers

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install feedparser requests beautifulsoup4 python-dateutil anthropic
      
      - name: Build news data
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python scripts/build_news.py
      
      - name: Commit and push changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add news_data.json
          git diff --staged --quiet || git commit -m "Update news data"
          git push

  deploy:
    needs: build
    runs-on: ubuntu-latest
    
    permissions:
      pages: write
      id-token: write
    
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    
    steps:
      - uses: actions/checkout@v4
        with:
          ref: main  # Get latest after build job
      
      - name: Pull latest changes
        run: git pull
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

#### 3. Configure Repository Settings

1. Go to **Settings** → **Pages**
2. Set Source to **GitHub Actions**
3. (Optional) Go to **Settings** → **Secrets and variables** → **Actions**
4. Add `ANTHROPIC_API_KEY` if you want enhanced AI analysis

#### 4. Enable GitHub Pages

Your site will be live at `https://YOUR_USERNAME.github.io/fullspectrum-news`

---

### Option B: Netlify + GitHub Actions

#### 1. Set Up Netlify

1. Create a Netlify account
2. Create a new site from Git
3. Connect your GitHub repository
4. Set publish directory to `.` (root)

#### 2. Configure Build Hook

1. In Netlify, go to **Site settings** → **Build & deploy** → **Build hooks**
2. Create a new build hook
3. Add the hook URL to GitHub secrets as `NETLIFY_BUILD_HOOK`

#### 3. Update GitHub Actions

Modify the workflow to trigger Netlify:

```yaml
- name: Trigger Netlify deploy
  run: curl -X POST ${{ secrets.NETLIFY_BUILD_HOOK }}
```

---

### Option C: Vercel

#### 1. Install Vercel CLI

```bash
npm i -g vercel
```

#### 2. Deploy

```bash
cd fullspectrum-news
vercel
```

#### 3. Set Up Scheduled Builds

Use Vercel Cron Jobs or GitHub Actions to trigger rebuilds:

```yaml
- name: Trigger Vercel deploy
  run: |
    curl -X POST "https://api.vercel.com/v1/integrations/deploy/${{ secrets.VERCEL_DEPLOY_HOOK }}"
```

---

### Option D: Self-Hosted (VPS/Server)

#### 1. Set Up Server

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip nginx

pip3 install feedparser requests beautifulsoup4 python-dateutil anthropic
```

#### 2. Configure Nginx

```nginx
server {
    listen 80;
    server_name fullspectrum.news;
    root /var/www/fullspectrum-news;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
```

#### 3. Set Up Cron Jobs

```bash
crontab -e
```

Add:
```
0 2 * * * cd /var/www/fullspectrum-news && python3 scripts/build_news.py
0 13 * * * cd /var/www/fullspectrum-news && python3 scripts/build_news.py
```

---

## Configuration

### Modifying Sources

Edit `data/sources.json` to add or modify news sources:

```json
{
  "name": "Source Name",
  "domain": "example.com",
  "bias": 0,       // -4 (extreme left) to 4 (extreme right)
  "reliability": "green"  // green, yellow, orange, red
}
```

### Adjusting Build Settings

Edit the `CONFIG` object in `scripts/build_news.py`:

```python
CONFIG = {
    "num_stories": 5,          # Number of top stories
    "request_timeout": 15,     # HTTP timeout
    "request_delay": 1,        # Delay between requests
}
```

### Using Claude API for Better Analysis

Set the `ANTHROPIC_API_KEY` environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key"
python scripts/build_news.py
```

This enables:
- More accurate tone analysis
- Better neutral headline/summary generation
- Improved story clustering

---

## Customization

### Changing Colors

Edit the CSS variables in `index.html`:

```css
:root {
    --left-color: #3B82F6;      /* Blue for left */
    --right-color: #EF4444;     /* Red for right */
    --optimistic-color: #10B981; /* Green for optimistic */
    --pessimistic-color: #6B7280; /* Gray for pessimistic */
}
```

### Changing Update Times

Modify the cron schedule in your GitHub Actions workflow:

```yaml
schedule:
  - cron: '0 2 * * *'   # 10 AM SGT (UTC+8)
  - cron: '0 13 * * *'  # 9 PM SGT (UTC+8)
```

---

## Troubleshooting

### No News Appearing

1. Check if `news_data.json` was generated
2. Verify sources in `data/sources.json` match actual domains
3. Check browser console for JavaScript errors

### Build Script Failing

1. Ensure all dependencies are installed
2. Check network connectivity
3. Verify RSS feed URLs are accessible

### Stale Data

1. Confirm cron job/scheduled action is running
2. Check GitHub Actions logs for errors
3. Try running build script manually

---

## License

MIT License — feel free to modify and use for your own projects.

---

## Contributing

Contributions welcome! Please open an issue or pull request.

---

## Credits

- News bias ratings based on [Ad Fontes Media Bias Chart](https://adfontesmedia.com/)
- Built with ❤️ for balanced news consumption
