# 🏢 Durham Region Rental Agent & Market Research (GitHub Web Edition)

A web-based agent and market research system for managing and syndicating rental listings for 6 properties across **Durham Region, Ontario** (Oshawa, Whitby, Ajax, Pickering, Clarington/Bowmanville).

---

## 🌐 3 Ways to Run in GitHub

### 1. Free Web Dashboard on GitHub Pages
The web dashboard in `docs/` is preconfigured for **GitHub Pages**.
- Once pushed to GitHub, go to **Settings > Pages > Build and deployment > Source: GitHub Actions** (or Deploy from branch `/docs`).
- Your interactive dashboard will be live at:
  ```text
  https://<your-username>.github.io/<your-repo-name>/
  ```
- **Features in the Web App:**
  - 🏠 **6-Unit Portfolio View**: Visual cards with photos, amenities, video tour player, and $/sqft.
  - 📊 **Durham Market Comps & Pricing Tool**: Real-time comp comparisons against nearby units in Oshawa/Whitby/Ajax with interactive price charts.
  - 📢 **1-Click Multi-Platform Poster**: Formatted listings for Facebook Marketplace, Kijiji, Zumper, and Rentals.ca with one-click copy and direct links to posting pages.
  - 🗺️ **Durham Free Platforms Guide**: Complete rulebook for posting free across the region.

---

### 2. Automated Agent in GitHub Actions (No Local Setup Required)
Two automated workflows are pre-configured in `.github/workflows/`:

1. **`Weekly Durham Market Comps Agent`** (`weekly_market_comps.yml`):
   - Runs automatically **every Monday at 9:00 AM EST**.
   - Scrapes and calculates active comps, generates a fresh analysis report, and uploads it to GitHub.
   - Can also be triggered manually with one click from GitHub's **Actions** tab.
2. **`Generate Rental Listing Dossiers`** (`generate_postings.yml`):
   - Triggerable on demand via GitHub Actions with a dropdown selector for any of the 6 units.
   - Generates and uploads downloadable listing dossiers for your entire portfolio.

---

### 3. 100% In-Browser Execution via GitHub Codespaces
No software needs to be installed on your local computer.
1. Click the green **Code** button on your GitHub repository.
2. Select **Codespaces > Create codespace on main**.
3. Inside the browser-based VS Code environment, run:
   ```bash
   python server.py
   ```
4. GitHub Codespaces will automatically open the interactive web dashboard in your browser.

---

## 🚀 Pushing This Project to Your GitHub

If you haven't pushed this folder to your GitHub yet:

1. Create a new repository on GitHub (e.g. `durham-rental-agent`).
2. Run these commands from this folder:
   ```bash
   git add .
   git commit -m "Initial commit: Durham rental posting agent & web dashboard"
   git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/<YOUR-REPO-NAME>.git
   git push -u origin main
   ```
3. Enable GitHub Pages:
   - On GitHub, navigate to **Settings > Pages**.
   - Under **Build and deployment > Source**, select **GitHub Actions** (or select branch `main` with folder `/docs`).

---

## 🛠 Local CLI Quick Commands

If you prefer to run commands via terminal:
```bash
# List all 6 units
./venv/bin/python agent.py list

# Run market comps research for a unit
./venv/bin/python agent.py comps --unit unit_1

# Package ready-to-post dossiers for Facebook, Kijiji, and Zumper
./venv/bin/python agent.py package

# Run local web dashboard
./venv/bin/python server.py
```
