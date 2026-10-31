import json
d = json.load(open("/app/.battery/task21/newheldout_run2.runs.json"))
for sid in ["nh_teo_ctx", "nh_ilhos", "nh_tomada"]:
    r = [x for x in d["runs"] if x["scenario"] == sid][0]
    print("===", sid, r["classification"])
    for p in r["proposals"][:8]:
        print(" ", p["purpose"].split(".")[-1], p["block_valid"], str(p["proposal"])[:140])
    print("  invokes:", [(i["capability_id"], i["status"]) for i in r["invokes"]])
    print("  content:", str(r["content"])[:140])
