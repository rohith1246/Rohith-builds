with open("d:/RohithBuilds/admin_dashboard/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "@app.route" in line or "INSERT INTO" in line or "update_job" in line or "create_job" in line or "target_batch" in line:
        print(f"Line {idx+1}: {line.strip()}")
