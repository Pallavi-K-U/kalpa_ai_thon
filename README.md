# Mindful Mentor

A privacy-first companion for students. Write a journal entry, get on-the-fly insights (stress score, sentiment, keywords) and gentle recommendations.

## Quickstart

```bash
# 1) Create and activate a venv (Windows PowerShell)
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1

# 2) Install deps
pip install -r requirements.txt

# 3) Run
python app.py
# Visit http://localhost:5000
```

## Structure

- `app.py` – Flask routes
- `nlp/analyze.py` – local text analysis
- `recommendations.py` – tailored suggestions
- `templates/` – UI pages (Jinja2)
- `static/` – CSS and JS

## Notes

- No data is stored. This is a wellness companion, not medical advice.
