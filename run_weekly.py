"""Run weekly (cron / Windows Task Scheduler):  python run_weekly.py   -> reports/weekly_<date>.md"""
import os, datetime
import data, ai

B = data.build(data.load())
text, _ = ai.weekly_report(B)          # needs ANTHROPIC_API_KEY
os.makedirs("reports", exist_ok=True)
path = f"reports/weekly_{datetime.date.today()}.md"
open(path, "w", encoding="utf-8").write(text); print("saved", path)
