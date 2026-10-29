# Cottonil Compass
1. `pip install -r requirements.txt`
2. Put your tables in `./02_TABLES/` (and `./01_CATALOG/`) or set `COTTONIL_TABLES` / `COTTONIL_CATALOG`.
3. `streamlit run app.py`
4. AI page: set `ANTHROPIC_API_KEY` or paste it in the sidebar. Weekly report on a schedule: `python run_weekly.py`.

Files: `config.py` settings · `data.py` load+clean · `analysis.py` calculations · `qa.py` questions with charts · `ai.py` Arabic Q&A with tools, weekly report, data alerts · `theme.py` colours · `app.py` pages.
