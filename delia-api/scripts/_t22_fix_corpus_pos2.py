p = "scripts/local_orchestration_reliability_eval.py"
lines = open(p).read().split("\n")
# V3 block spans lines 973..1115 (0-indexed 972..1114) inside a function.
# Module-level target: right after HELD_OUT_CORPUS_V2's closing ']'
# (line 564 1-indexed).
start = next(
    i for i, l in enumerate(lines) if "# Task 22 acceptance held-out" in l
)
end = next(
    i
    for i, l in enumerate(lines[start:], start)
    if l == "]"
) + 1
block = lines[start:end]
del lines[start:end]
v2_end = next(
    i
    for i, l in enumerate(lines)
    if l == "]" and i > lines.index("HELD_OUT_CORPUS_V2 = [")
)
lines[v2_end + 1:v2_end + 1] = ["", ""] + block
open(p, "w").write("\n".join(lines))
print("moved block to after HELD_OUT_CORPUS_V2")
