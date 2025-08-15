# 📊 Artworks Report Generator

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Build](https://github.com/git-challenge/script-challenge/actions/workflows/python-app.yml/badge.svg)

> 🛠 Python script that generates a **report in JSON and PDF formats** based on a YAML configuration file.  
> Data is retrieved from the [Art Institute of Chicago API](https://api.artic.edu/docs/).

---

## ✨ Features
- 📄 Produces **two output files**: `report.json` and `report.pdf`.
- ⚙️ Fully configurable report through a `.yml` file.
- 🖋️ PDF output is rendered from an HTML template using **Jinja2** and **WeasyPrint**.
- 🔄 Integrated with **GitHub Actions** for automated validation and CI workflows.
- 🌐 Fetches data directly from the **Art Institute of Chicago's public API**.

---

## 📂 How It Works
1. **Configuration-driven** – The script reads a YAML file specifying the query parameters (filters, limits, sorting, etc.).
2. **Data retrieval** – Makes HTTP requests to the Art Institute of Chicago API to fetch artwork metadata.
3. **Report generation** – Creates:
   - A **JSON file** with the raw fetched data.
   - A **PDF file** formatted via HTML templates and styled with CSS.
4. **Automation ready** – Can be run locally or in CI/CD environments like GitHub Actions.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/git-challenge/script-challenge.git
cd script-challenge
```
### 2. Create a virtual environment (recommended)
```bash
python -m venv .venv
source .venv/bin/activate
```
### 3. Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
### 4. Run the script
```bash
python -m artworks-report.py \
        --config config/queries.yml \
        --out out --dry-run
```
Tip: Remove --dry-run to actually generate the files.

---

## 🛠 Tech Stack
- Python 3.11
- Jinja2 – HTML templating engine for PDF generation.
- WeasyPrint – HTML/CSS to PDF rendering.
- PyYAML – YAML configuration parsing.
- Requests – HTTP client for fetching API data.

--- 

## 📜 License

This project is licensed under the MIT License.