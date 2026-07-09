import pathlib
p = pathlib.Path("F:/projects/chez-violeta-intelligence/artifacts/review/checklist.md")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("# Review Checklist\n", encoding="utf-8")
print("OK")
