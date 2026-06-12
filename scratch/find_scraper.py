import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_path = os.path.join(base_dir, "admin_dashboard", "app.py")
out_path = os.path.join(base_dir, "scratch", "scraper_lines.txt")

terms = ["scraper", "scrapper", "status", "start", "stop", "cooling", "naukri", "indeed", "linkedin"]

matches = []
with open(app_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        line_lower = line.lower()
        matched_terms = [t for t in terms if t in line_lower]
        if matched_terms:
            matches.append(f"Line {i+1} ({', '.join(matched_terms)}): {line.strip()}")

with open(out_path, "w", encoding="utf-8") as out:
    out.write("\n".join(matches))

print(f"Scanned {app_path} and found {len(matches)} lines. Written to {out_path}")
