# Supplier model audit — evidence scripts

Read-only SQL queries used by the TOTVS Protheus supplier data model audit.
Canonical report: `api-delpi/docs/api/padroes-totvs/playbooks/playbook-cadastro-fornecedor-sa2.md`
Short section: `api-delpi/docs/api/padroes-totvs/cadastro-fornecedor.md`

## Usage

```bash
./q.sh -Q "SELECT ..."          # ad-hoc read-only query (pipe-separated output)
./q.sh -i q5_sa5.sql            # run a canned audit query
```

`q.sh` reads `TOTVS_DB_*` credentials from `infra/.env` at runtime and runs
`sqlcmd` against the authorized DELPI TOTVS SQL Server. No credentials are
stored here. **Read-only only** — the audit class forbids any write.

## Query inventory

| File | Purpose |
|---|---|
| `q2_discovery.sql` | Global SX3 discovery — columns referencing supplier/code/store/CNPJ across all dictionaries |
| `q3_related.sql` | SA2 relationships from SX9 (dominant/child) + physical table cross-check |
| `q4_material.sql` | Material related tables (SA5, SA6, contacts, fiscal, commercial) — SX2/SIX |
| `q5_sa5.sql` | SA5 (product × supplier) full SX3 schema |
| `q6_profile.sql` | SA2010 read-only profiling — fill rates, domains, duplicates, code patterns |
| `q7_mech.sql` | Physical mechanisms — indexes, triggers, TTAT log structure |
| `q8_material_schemas.sql` | Complete SX3 schemas for material related tables |
| `q9_counts.sql` | Row counts for material/transactional tables |

Outputs (`out/`, `out_utf8/`, `*.md` fragments) are regenerated artifacts —
not versioned. Do not commit raw dumps: they may contain real supplier data.
