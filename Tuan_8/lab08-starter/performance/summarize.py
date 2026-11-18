import csv
from pathlib import Path

SCENARIOS = {
    "A": ("10", "2", "30s"),
    "B": ("50", "5", "60s"),
    "C": ("200", "50", "30s"),
}

print("| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |")
print("|---|---:|---:|---:|---:|---:|---:|")
for name, (users, rate, duration) in SCENARIOS.items():
    path = Path("reports") / f"{name}_stats.csv"
    if not path.exists():
        print(f"| {name} | {users} | {rate} | {duration} | chưa chạy | | |")
        continue
    with path.open(encoding="utf-8") as handle:
        row = next(r for r in csv.DictReader(handle) if r["Name"] == "Aggregated")
    total = int(row["Request Count"])
    failures = int(row["Failure Count"])
    print(
        f"| {name} | {users} | {rate} | {duration} | {row['95%']} | "
        f"{failures / total * 100:.2f}% ({failures}/{total}) | {float(row['Requests/s']):.1f} |"
    )
