"""Read-only audit: scan tv_dashboard JSONB for 'value' field references.

Reads a JSON dump produced by psql (one JSON doc per line, '||' separated cols).
Usage: _audit_value_bindings.py dump.jsonl
"""
import json
import sys
import re

FIELD_KEYS = {'valueField', 'selectedValueFields', 'field', 'dataField', 'metricField'}
CONTAINER_KEYS = {'dataBinding', 'binding', 'dataRef', 'nativeConfig', 'kpi', 'kpiMetrics'}

def walk(node, path, hits):
    if isinstance(node, dict):
        for k, v in node.items():
            p = f'{path}.{k}' if path else k
            if k == 'operationId' and isinstance(v, str):
                hits.append(('OPID', p, v))
            if k in FIELD_KEYS:
                if isinstance(v, str):
                    hits.append(('FIELD', p, v))
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        hits.append(('FIELD', f'{p}[{i}]', item))
            walk(v, p, hits)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f'{path}[{i}]', hits)

def main():
    ops98 = set(json.load(open('docs/07-api-delpi/inventory-value-field/value_field_consumer_inventory.json',
                              encoding='utf-8'))['rows'][i]['operationId'] for i in range(98))
    out = []
    for line in open(sys.argv[1], encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        src = rec['src']
        rid = rec.get('id')
        name = rec.get('name')
        doc = rec.get('doc')
        if not isinstance(doc, (dict, list)):
            continue
        hits = []
        walk(doc, '', hits)
        fields = [(p, v) for t, p, v in hits if t == 'FIELD']
        opids = [(p, v) for t, p, v in hits if t == 'OPID']
        value_fields = [(p, v) for p, v in fields if str(v) == 'value']
        ops_in_scope = [v for p, v in opids]
        if value_fields or fields or opids:
            out.append({
                'source': src, 'id': rid, 'name': name,
                'operationIds': ops_in_scope,
                'opids_in_scope_98': [o for o in ops_in_scope if o in ops98],
                'field_refs': [{'path': p, 'field': v} for p, v in fields],
                'value_refs': [{'path': p} for p, v in value_fields],
            })
    print(json.dumps(out, ensure_ascii=False, indent=1))

main()
