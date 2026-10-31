p = "scripts/local_orchestration_reliability_eval.py"
src = open(p).read()
# Extract the inserted V3 block (it landed inside the pools dict).
start = src.index("\n\n# Task 22 acceptance held-out")
end = src.index(']\n\n        "heldout": list(HELD_OUT_CORPUS),')
block = src[start:end] + "]"
src = src[:start] + src[end + 1:]
# Re-insert the definition at module level before the pool comment.
anchor = "    # CORPUS_SET selects the evaluation pool"
assert anchor in src
src = src.replace(anchor, block + "\n\n\n" + anchor, 1)
open(p, "w").write(src)
print("repositioned")
