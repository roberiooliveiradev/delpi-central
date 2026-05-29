# Mapa GPT_instructions × agente minha-delpi-chat

Gerado a partir de `GptInstructionsCoverageService`. Reindexe com `scripts/sync_gpt_instructions_knowledge.py`.

| Fonte (api-delpi-py) | Cobertura | Indexado como | Ação |
|----------------------|-----------|---------------|------|
| `api-delpi-rotas-agente.md` | ✅ agente | api-delpi-rotas-agente.md | — |
| `Analista SQL DELPI — Produção, Suprimentos e Perdas.txt` | ⚠️ parcial | Analista SQL DELPI — Produção, Suprimentos e Perdas.txt | — |
| `Analista SQL DELPI — Oportunidades, Processos e Estágios LMP.txt` | ⚠️ parcial | Analista SQL DELPI — Oportunidades, Processos e Estágios LMP.txt | — |
| `data_sql_api_instructions.md` | ✅ agente | data_sql_api_instructions.md | ingerir no agente |
| `product_api_instructions.md` | ✅ agente | product_api_instructions.md | ingerir no agente |
| `system_api_instructions.md` | ✅ agente | system_api_instructions.md | ingerir no agente |
| `GPT_instructions.md` | ✅ global | GPT_instructions.md | — |
| `O_ARQUITETO_DO_CODIGO.md` | ✅ global | O_ARQUITETO_DO_CODIGO.md | — |
| `Normas_Tecnicas_DELPI.md` | ✅ global | normas-tecnicas-delpi.md | — |
| `drawing_analyser_instructions.md` | ✅ agente | drawing_analyser_instructions.md | ingerir no agente |
| `drawing_analyser_instructions_full.md` | ⏭️ omitir | — | — |
| `drawing_rules_delpi.md` | ✅ agente | drawing_rules_delpi.md | ingerir no agente |
| `drawing_requirements_delpi.md` | ✅ agente | drawing_requirements_delpi.md | ingerir no agente |
| `validation_rules_delpi.md` | ✅ agente | validation_rules_delpi.md | ingerir no agente |
| `Understanding DELPI Intermediate Product Codes.md` | ✅ agente | Understanding DELPI Intermediate Product Codes.md | ingerir no agente |
| `diretrizes_criacao_de_descricao.md` | ✅ agente | diretrizes_criacao_de_descricao.md | ingerir no agente |
| `instructions.md` | ⏭️ omitir | — | — |

## Notas por documento

### `api-delpi-rotas-agente.md`
- **Cobertura:** indexed_agent
- **Indexado:** `api-delpi-rotas-agente.md`
- **Notas:** Guia curado minha-delpi (não vem da pasta GPT_instructions); 5 chunks no agente.
- **Tags:** rotas, operacional

### `Analista SQL DELPI — Produção, Suprimentos e Perdas.txt`
- **Cobertura:** partial
- **Indexado:** `Analista SQL DELPI — Produção, Suprimentos e Perdas.txt`
- **Notas:** Playbook SQL customizado no agente; complementa mas não substitui data_sql_api_instructions.md.
- **Tags:** sql, producao

### `Analista SQL DELPI — Oportunidades, Processos e Estágios LMP.txt`
- **Cobertura:** partial
- **Indexado:** `Analista SQL DELPI — Oportunidades, Processos e Estágios LMP.txt`
- **Notas:** Playbook SQL LMP/engenharia no agente.
- **Tags:** sql, lmp

### `data_sql_api_instructions.md`
- **Cobertura:** indexed_agent
- **Indexado:** `data_sql_api_instructions.md`
- **Notas:** Guia completo POST /data/sql, SC2010, exemplos de produção — ingerido via sync_gpt_instructions_knowledge.py.
- **Tags:** sql, data, producao

### `product_api_instructions.md`
- **Cobertura:** indexed_agent
- **Indexado:** `product_api_instructions.md`
- **Notas:** Detalhe por rota/tabela Protheus; paths adaptados para api-delpi atual.
- **Tags:** produtos, operacional

### `system_api_instructions.md`
- **Cobertura:** indexed_agent
- **Indexado:** `system_api_instructions.md`
- **Notas:** Metadados SX2/SX3; descoberta de tabelas antes de SQL.
- **Tags:** sistema, sql

### `GPT_instructions.md`
- **Cobertura:** indexed_global
- **Indexado:** `GPT_instructions.md`
- **Notas:** Regras gerais do agente GPT; escopo global (company-knowledge), 9 chunks.
- **Tags:** comportamento

### `O_ARQUITETO_DO_CODIGO.md`
- **Cobertura:** indexed_global
- **Indexado:** `O_ARQUITETO_DO_CODIGO.md`
- **Notas:** Identidade/plataforma; escopo global.
- **Tags:** plataforma

### `Normas_Tecnicas_DELPI.md`
- **Cobertura:** indexed_global
- **Indexado:** `normas-tecnicas-delpi.md`
- **Notas:** Normas técnicas DELPI; base global (company-knowledge), não agent_source.
- **Tags:** normas, produtos, engenharia

### `drawing_analyser_instructions.md`
- **Cobertura:** indexed_agent
- **Indexado:** `drawing_analyser_instructions.md`
- **Notas:** Analyser / desenhos técnicos; rotas /products/{code}/analyser. Runtime PDF: backlog Onda 12 (skill drawing-analyser herdável).
- **Tags:** engenharia, analyser

### `drawing_analyser_instructions_full.md`
- **Cobertura:** skip
- **Notas:** Versão estendida; preferir drawing_analyser_instructions.md no agente geral.
- **Tags:** engenharia

### `drawing_rules_delpi.md`
- **Cobertura:** indexed_agent
- **Indexado:** `drawing_rules_delpi.md`
- **Notas:** Regras gráficas de desenho.
- **Tags:** engenharia, desenho

### `drawing_requirements_delpi.md`
- **Cobertura:** indexed_agent
- **Indexado:** `drawing_requirements_delpi.md`
- **Notas:** Requisitos obrigatórios em desenhos.
- **Tags:** engenharia, desenho

### `validation_rules_delpi.md`
- **Cobertura:** indexed_agent
- **Indexado:** `validation_rules_delpi.md`
- **Notas:** Critérios de conformidade automática.
- **Tags:** engenharia, qualidade

### `Understanding DELPI Intermediate Product Codes.md`
- **Cobertura:** indexed_agent
- **Indexado:** `Understanding DELPI Intermediate Product Codes.md`
- **Notas:** Codificação intermediários 50xx.
- **Tags:** produtos, engenharia

### `diretrizes_criacao_de_descricao.md`
- **Cobertura:** indexed_agent
- **Indexado:** `diretrizes_criacao_de_descricao.md`
- **Notas:** Padronização de descrições de produto.
- **Tags:** produtos, normas

### `instructions.md`
- **Cobertura:** skip
- **Notas:** Aponta para GPT_instructions.md; sem conteúdo próprio.
