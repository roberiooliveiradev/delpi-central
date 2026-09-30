"""Resolve each persisted field=='value' ref to its operationId via block.dataBinding or dataSourceId."""
import json

FIELD_KEYS = ('valueField', 'selectedValueFields', 'field', 'dataField', 'metricField')


def walk_fields(node, path, out):
    if isinstance(node, dict):
        for k, v in node.items():
            p = path + '.' + k if path else k
            if k in FIELD_KEYS and isinstance(v, str):
                out.append((p, v))
            elif k in FIELD_KEYS and isinstance(v, list):
                for i, it in enumerate(v):
                    if isinstance(it, str):
                        out.append((f'{p}[{i}]', it))
            walk_fields(v, p, out)
    elif isinstance(node, list):
        for i, it in enumerate(node):
            walk_fields(it, f'{path}[{i}]', out)


inv = json.load(open('docs/07-api-delpi/inventory-value-field/value_field_consumer_inventory.json',
                     encoding='utf-8'))
ops98 = {r['operationId'] for r in inv['rows']}
rows_out = []

for line in open('/tmp/tv_dump.jsonl', encoding='utf-8'):
    rec = json.loads(line)
    doc = rec.get('doc')
    if not isinstance(doc, (dict, list)):
        continue
    blocks = []

    def collect(n):
        if isinstance(n, dict):
            if isinstance(n.get('blocks'), list):
                for i, b in enumerate(n['blocks']):
                    blocks.append((i, b))
            for v in n.values():
                collect(v)
        elif isinstance(n, list):
            for it in n:
                collect(it)
    collect(doc)
    bmap = {b.get('id'): b for _, b in blocks if isinstance(b, dict) and b.get('id')}

    for i, b in blocks:
        if not isinstance(b, dict):
            continue
        fs = []
        walk_fields(b, '', fs)
        vrefs = [(p, v) for p, v in fs if v == 'value']
        if not vrefs:
            continue
        op = (b.get('dataBinding') or {}).get('operationId')
        src_b = bmap.get(b.get('dataSourceId'))
        op_src = (src_b.get('dataBinding') or {}).get('operationId') if isinstance(src_b, dict) else None
        resolved = op or op_src
        for p, v in vrefs:
            flag = 'IN98' if resolved in ops98 else ('NO_OPID' if not resolved else 'OTHER')
            rows_out.append({
                'source': rec['src'], 'row_id': rec['id'], 'name': rec.get('name'),
                'playlist_id': rec.get('pl'), 'block_index': i,
                'block_id': b.get('id'), 'field_path': p, 'field': v,
                'block_operationId': op, 'source_block_operationId': op_src,
                'resolved_operationId': resolved, 'scope': flag,
            })

print(json.dumps(rows_out, ensure_ascii=False, indent=1))
