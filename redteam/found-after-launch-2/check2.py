import ast, re
from pathlib import Path

VP = Path("/private/var/folders/fc/53j7mrrs40j5jvl09zqzrcqw0000gn/T/redteam-e8nrm0yq/verify_paper_tables.py")
PP = Path("/private/var/folders/fc/53j7mrrs40j5jvl09zqzrcqw0000gn/T/redteam-e8nrm0yq/polar-projector-paper.md")

src = VP.read_text()
tree = ast.parse(src)
fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_artifact_checks")
lits = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
required = sorted(set(s for s in lits if re.fullmatch(r"[+-]?\d+(\.\d+)?", s) and len(s) > 1))

raw = PP.read_text(encoding="utf-8")
lines = raw.splitlines()

EDITS = [
    (62, "0.925", "0.955"),
    (743, "16.4", "164"),
    (452, "4.3×", "6.3×"),
    (1181, "1.39×", "2.39×"),
    (721, "50 query chunks", "500 query chunks"),
]

def presence(text):
    t = text.replace("\u2212", "-")
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)
    t = re.sub(r"^#+ .*$", "", t, flags=re.M)
    t = re.sub(r"\u00a7+\s?[A-D\d]+(?:\.\d+)*(?:\s?[\u2013-]\s?\u00a7?[A-D\d]+(?:\.\d+)*)?", "", t)
    return {s: bool(re.search(rf"(?<![\d.]){re.escape(s)}(?!\d|\.\d)", t)) for s in required}

base = presence(raw)
print("baseline missing:", [s for s, ok in base.items() if not ok])

for ln, old, new in EDITS:
    idx = ln - 1
    line = lines[idx]
    n = line.count(old)
    print(f"\nline {ln}: occurrences of {old!r} on line = {n}")
    print("   line:", line[:160])
    assert n == 1, (ln, old, n)
    newlines = list(lines)
    newlines[idx] = line.replace(old, new)
    after = presence("\n".join(newlines))
    missing = [s for s, ok in after.items() if not ok]
    print("   after edit, missing required strings:", missing)
    print("   changed line:", newlines[idx][:160])
