from pathlib import Path
import ast
p=Path("source/SS_OIL_SMJENE.py")
s=Path("SS_OIL_SMJENE_FIXED.py").read_text(encoding="utf-8")
ast.parse(s)
p.write_text(s,encoding="utf-8")
print("V1 verified send-only source installed")
