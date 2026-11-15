import ast, re
from pathlib import Path

VP = Path("/private/var/folders/fc/53j7mrrs40j5jvl09zqzrcqw0000gn/T/redteam-e8nrm0yq/verify_paper_tables.py")
PP = Path("/private/var/folders/fc/53j7mrrs40j5jvl09zqzrcqw0000gn/T/redteam-e8nrm0yq/polar-projector-paper.md")

src = VP.read_text()
tree = ast.parse(src)

fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_artifact_checks")
lits = []
for node in ast.walk(fn):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        lits.append(node.value)

numish = [s for s in lits if re.fullmatch(r"[+-]?\d+(\.\d+)?", s)]
required = sorted(set(s for s in numish if len(s) > 1))
print("required presence strings:", len(required))

text = PP.read_text(encoding="utf-8").replace("\u2212", "-")
text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
text = re.sub(r"^#+ .*$", "", text, flags=re.M)
text = re.sub(r"\u00a7+\s?[A-D\d]+(?:\.\d+)*(?:\s?[\u2013-]\s?\u00a7?[A-D\d]+(?:\.\d+)*)?", "", text)

def present(s):
    return bool(re.search(rf"(?<![\d.]){re.escape(s)}(?!\d|\.\d)", text))

missing = [s for s in required if not present(s)]
print("missing from manuscript (would fail presence):", missing)
print()

cands = ["0.543","0.925","0.981","16.4","4.3","1.39","4.64","2.62","50","500","29","0.02","0.003",
         "1.37","0.467","0.485","0.933","0.567","1.000","6.38","12.20","4.71","2.05","3.54","10.1",
         "1.91","7.0","1.71","1.54","1.56","4.68","0.056","0.023","0.019","0.697","0.6811","0.6639",
         "0.6666","1.57","1.17","1.47","2.47","2.41","11.39","0.68","1.18","1.7","2.0","15","0.0068"]
for s in cands:
    hits = [m.start() for m in re.finditer(rf"(?<![\d.]){re.escape(s)}(?!\d|\.\d)", text)]
    line_no = sorted({text[:h].count("\n") + 1 for h in hits})
    print(f"{s:8} count={len(hits):3} lines={line_no[:14]}")
