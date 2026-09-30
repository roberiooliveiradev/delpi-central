"""Per-block audit: associate each field=="value" ref with its block's operationId."""
import json
import sys

FIELD_KEYS = {'valueField', 'selectedValueFields', 'field', 'dataField', 'metricField'}

def find_opid(node):
    """Return operationId bound to a block (dataBinding.operationId or any operationId key)."""
    found = []
    def w(n):
        if isinstance(n, dict):
            for k, v in n.items():
                if k == 'operationId' and isinstance(v, str):
                    found.append(v)
                w(v)
        elif isinstance(n, list):
            for i in n:
                w(i)
    w(node)
    return found

def walk_fields(node, path, out):
    if isinstance(node, dict):
        for k, v in node.items():
            p = f'{path}.{k}' if path else k
            if k in FIELD_KEYS and isinstance(v, str):
                out.append((p, v))
            elif k in FIELD_KEYS and isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, str):
                        out.append((f'{p}[{i}]', item))
            walk_fields(v, p, out)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk_fields(item, f'{path}[{i}]', out)

def block_scan(doc, prefix, out):
    """Scan blocks[] arrays: per block, collect field refs + operationIds."""
    if isinstance(doc, dict):
        for k, v in doc.items():
            if k == 'blocks' and isinstance(v, list):
                for i, blk in enumerate(v):
                    fields = []
                    walk_fields(blk, '', fields)
                    ops = find_opid(blk)
                    for p, f in fields:
                        out.append({'block_index': i, 'block_id': blk.get('id') if isinstance(blk, dict) else None,
                                    'field_path': prefix + f'.blocks[{i}].' + p.lstrip('.'),
                                    'field': f, 'block_operationIds': ops})
            else:
                block_scan(v, f'{prefix}.{k}' if prefix else k, out)
    elif isinstance(doc, list):
        for i, item in enumerate(doc):
            block_scan(item, f'{prefix}[{i}]', out)

results = []
for line in open('/tmp/tv_dump.jsonl', encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    rec = json.loads(line)
    doc = rec.get('doc')
    if not isinstance(doc, (dict, list)):
        continue
    out = []
    block_scan(doc, '', out)
    # also non-block field refs
    top_fields = []
    walk_fields(doc, '', top_fields)
    non_block = [(p, v) for p, v in top_fields if 'blocks[' not in p and str(v) == 'value']
    valrefs = [o for o in out if o['field'] == 'value']
    if valrefs or non_block:
        results.append({'source': rec['src'], 'id': rec.get('id'), 'name': rec.get('name'),
                        'playlist_id': rec.get('pl'),
                        'block_value_refs': valrefs, 'other_value_refs': non_block})

print(json.dumps(results, ensure_ascii=False, indent=1))
