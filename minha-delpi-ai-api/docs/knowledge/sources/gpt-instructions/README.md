# Fonte: GPT_instructions (api-delpi-py)

Espelho **verbatim** da pasta `api-delpi-py/GPT_instructions` dentro do repositório minha-delpi-ai-api.

## Para quê

- **Referência** para implementações futuras (intents, policies, skills, RAG) sem depender do checkout de `api-delpi-py`.
- **Entrada** do script `scripts/sync_gpt_instructions_knowledge.py` (padrão quando esta pasta existe).
- **Diff** entre versão original e markdown adaptado em [`../../domains/gpt-instructions/`](../../domains/gpt-instructions/) e [`../../domains/global/`](../../domains/global/).

## Arquivos

| Arquivo | Uso típico |
|---------|------------|
| `GPT_instructions.md` | Regras gerais → global (`company-knowledge`) |
| `O_ARQUITETO_DO_CODIGO.md` | Identidade/plataforma → global |
| `Normas_Tecnicas_DELPI.md` | Descrição técnica matérias-primas → global |
| `data_sql_api_instructions.md` | POST `/data/sql`, SC2010, produção → agente |
| `product_api_instructions.md` | Rotas produtos / Protheus → agente |
| `system_api_instructions.md` | SX2/SX3, dicionário → agente |
| `drawing_analyser_instructions.md` | Analyser PDF/desenhos → agente |
| `drawing_analyser_instructions_full.md` | Versão estendida (referência; não ingerida no agente geral) |
| `drawing_rules_delpi.md` | Regras gráficas → agente |
| `drawing_requirements_delpi.md` | Requisitos de desenho → agente |
| `validation_rules_delpi.md` | Conformidade automática → agente |
| `Understanding DELPI Intermediate Product Codes.md` | Códigos intermediários 50xx → agente; skill `technical-description-delpi` + classificação no desenho (`ChatDrawingProductFamilyClassificationService`) |
| `diretrizes_criacao_de_descricao.md` | Padronização de descrições → agente |
| `instructions.md` | Apontador para `GPT_instructions.md` (omitir na ingestão) |
| `Checklist Revisão de Desenhos DELPI.pdf` | Checklist operacional (referência; backlog Onda 12) |

## Atualizar a partir do api-delpi-py

```bash
cp -a /caminho/api-delpi-py/GPT_instructions/. \
  minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/

# Regenerar adaptados + mapa (+ global):
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
  python scripts/sync_gpt_instructions_knowledge.py --sync-global
```

Mapa documento a documento: [`../../gpt-instructions-coverage-map.md`](../../gpt-instructions-coverage-map.md).
