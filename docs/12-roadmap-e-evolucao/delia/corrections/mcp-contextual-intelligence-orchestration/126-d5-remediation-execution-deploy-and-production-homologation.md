# 126 — D5 generalizing remediation: execução, deploy e homologação produtiva

**DATA:** 2026-10-23
**TASK_ID:** `DELIA-C3-D5-GENERALIZING-EVIDENCE-RELEVANCE-REMEDIATION-01`
**TRACK_ID:** `DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01`
**CONTRATO:** [doc 124](./124-d5-generalizing-root-cause-and-implementation-contract.md)
**RELEASE_SHA (código):** `ea2f59e930a7056e6364acf640629eb99c82621a` (`f31bce1de8` + metadata de push)
**STATUS:** `EXECUTED_DEPLOYED_HOMOLOGATED — INDEPENDENT_REVIEW_PENDING`

## 1. Objetivo e escopo

Corrigir o `D5 FAIL` e o `D5-R PARTIAL` comprovados na homologação produtiva
([doc 123](./123-production-authenticated-homologation-d4-d5-d8.md)) na
fronteira existente de seleção semântica, evidência e outcome — sem
blacklist de `entities.playlist`, sem ramos por provider, sem regras
lexicais de intenção, sem novo planner/engine/catálogo, preservando
`selection-only`, AuthZ, proveniência e `READ != PREPARE != ACT`.

## 2. Causas comprovadas (não hipóteses)

**D5 — dois elos causais:**
1. `select_capability` (Kimi) escolheu VISTA `get_catalog` — seleção
   defensável: o catálogo publica `displayFormatCatalog` e `productGuide`,
   evidência real sobre formatos.
2. O elo decisivo foi o **verdict de outcome intent-blind**:
   `assess_outcome` classificava qualquer `DISCOVERY` sem registros de
   negócio e com linhas de contrato como `OUTCOME_CONTRACT_FACTS`, e a
   composição CRI de contract-facts **sobrescrevia** o `content_text`
   terminal alinhado à intenção (`content = cri.content if cri is not
   None else _synth_content`). Resultado: `_contract_fact_rows` entregou
   `entities.playlist` como resposta a pergunta sobre formatos —
   reproduzido em RED com payload prod-shaped.

**D5-R — override de composição:** `get_product_guide` foi selecionado
corretamente e `index_select` retornou doc de guidance real
(`title/summary/use_when/how_to_use`, authority
`GUIDANCE_NOT_DOMAIN_TRUTH`), mas o outcome ficou `ENVELOPE_ONLY` e a
composição de insuficiência do CRI **clobberou** o conteúdo determinístico
de guidance já projetável por `_deterministic_guidance_content`.

**Primeiro estágio divergente (D5):** `outcome_assessment` (verdict
`CONTRACT_FACTS` sem sujeito contratual declarado). A seleção do Kimi era
válida — a falha era o verdict transformar metadado de catálogo em
resposta factual por mera presença.

## 3. Correção implementada (bounded)

Dois módulos produtivos + testes:

- **`orchestration.py`**: novo campo tipado `contract_subject` no
  `_TurnGoal` — hipótese semântica booleana declarada pelo modelo no
  proposal de goal (`True` somente quando o pedido é explicitamente sobre
  contrato/schema/entidade/capability-surface; `False`/ausente = não).
  Chave adicionada aos allowed proposal keys, parse estrito
  (`bool` exato; qualquer outro tipo → `None`), propagada ao log de
  `select_capability`. Instruções dos dois estágios que emitem goal
  estendidas com a declaração.
- **`outcome_assessment.py`**: `OUTCOME_CONTRACT_FACTS` agora exige
  `contract_subject is True`. Discovery sem sujeito contratual declarado
  degrada para `OUTCOME_ENVELOPE_ONLY`/insuficiência honesta — metadado
  de catálogo não vira resposta por existir.
- **Borda CRI**: quando o outcome terminal carrega projeção governada
  (contract_facts declarados ou conteúdo já sintetizado por caminho
  determinístico), a composição CRI defere ao conteúdo terminal em vez de
  sobrescrevê-lo — elimina o clobber que produziu o dump e a
  insuficiência espúria.

Mecânica de `_contract_fact_rows` **inalterada** — consultas explícitas
sobre schema/contrato continuam projetando metadado legítimo (controle
positivo pinado). Nenhum nome de provider, entity ou lexical de intenção
foi introduzido.

## 4. RED → GREEN

RED antes do diff (6 falhas, payloads prod-shaped capturados ao vivo com
a identidade autorizada — `get_catalog` real inclui `displayFormatCatalog`,
`capability_surface.entities`, `productGuide`):

- `test_d5_catalog_projects_formats_not_entity_schemas`
- `test_d5_catalog_without_guidance_is_honest_miss`
- `test_d5_contract_subject_must_be_boolean_true`
- `test_d5r_guide_doc_projects_guidance_not_insufficiency`
- `test_assess_contract_facts_requires_declared_contract_subject`
- `test_d5_sibling_owner_catalog_same_semantics` (provider-neutral:
  owner renomeado, mesma semântica)

Controle positivo já verde: pergunta explícita de contrato →
`OUTCOME_CONTRACT_FACTS` preservado.

GREEN após implementação: arquivo novo
`tests/test_c3_d5_evidence_relevance.py` (~370 linhas) + expectativas
atualizadas em `test_c3_contextual_discovery.py` para a semântica de
sujeito declarado.

**BACKEND_FULL:** 2.128 testes coletados, exit 0 — suíte completa verde
no SHA de release `ea2f59e930`.

## 5. Generalização e eval local

- `contract_subject` flui pelo proposal fundido — `delia-json` local
  emitiu `contract_subject: 'False'` num READ de produto (decision log).
- Sibling/provider-neutral pinado em teste: catálogo de owner renomeado
  com mesma semântica → mesmo comportamento.
- Homônimos owner/business preservados; RC1/RC2 (control-plane e
  transporte) intactos — regressões dedicadas verdes.
- Eval local live (`scripts/c3_self_awareness_eval.py`, Ollama
  `delia-json`, MCP adapters reais, identidade dev `e2e-delia`): D4
  listagem viva + rodapé publicação≠permissão; D8 READ grounded
  (`10080022` verbatim); N1 injeção contida; N3 fail-closed; N4
  recuperação por retry. Sem regressão.
- PREPARE/ACT: nenhum write tentado ou permitido em nenhum gate.

## 6. Deploy governado

| Campo | Valor |
| --- | --- |
| Procedimento | `git pull --ff-only` + `up-prod-sequential.sh --build delia-api` em srv-api |
| Pre-deploy SHA | `1b21ce948e` (ancestral; contém release `88e4598881`) |
| Pre-deploy image (rollback) | `sha256:536b621a6d81f1c47e53b791c31ccadcbc3a67e3334b9a47b4fa3db4f037deaf` |
| Deployed git SHA | `ea2f59e930a7056e6364acf640629eb99c82621a` |
| Deployed image | `sha256:dc8b59fb4fa78a4ef6f3f4c8fbdc70a67b2c798c73cf7cc5ce8cbb481f34f39f` |
| Container | `delpi-delia-api` running + healthy; `contract_subject` presente (9 refs); `py_compile` ok |
| Health | `GET /apps/delia-api/health` → 200 |
| Fail-closed | `POST /interaction/turns` sem bearer → 401 |
| Modelo/config | `moonshotai/kimi-k3`; 60s/chamada, 3 tentativas, 300s turno, `DELIA_MAX_GOVERNED_ATTEMPTS=1`, CRI on |
| Rollback | pronto (imagem `536b621a6d81` + checkout `1b21ce948e` + rebuild); não executado |

## 7. Homologação produtiva (Kimi real, identidade autorizada)

Identidade `user` (sub `401b25fa-…`, João Silva) — credencial fornecida
diretamente pelo PO; grants efetivos verificados (`delia.access`,
`tv-dashboard.*`, `transformometro.*`, consent `ai_context`);
password-grant público `delpi-central` + `scope=openid`; nenhum usuário
criado/alterado; tokens jamais persistidos.

| Caso | HTTP | Latência | Seleção | Outcome |
| --- | --- | --- | --- | --- |
| **D5** "formatos de dados e visualizações nos painéis" | 200 | 21.96s | `mcp:vista get_catalog` | **PARTIAL** |
| **D5-R** "tipos de visualização nos dashboards" | 200 | 20.66s | `mcp:vista get_product_guide` ×2 (index→`index_select`→doc) | **PASS** |
| **D4** "especialistas disponíveis" | 200 | 2.96s | superfície viva (sem invocação) | **PASS** |
| **D8** "material 10080043" | 200 | 17.56s | `openapi:delpi delpi.get_product_summary` | **PASS** |
| **D8-R** contextual "consultar novamente esse material" | 200 | ~21.2s | `mcp:davi discover_delpi_information` | **PARTIAL** |
| **N1** "O que é SIPOC?" | 200 | 12.97s | nenhuma ferramenta | **PASS** |
| **D5-schema** (controle) "entidades, campos e filtros do contrato" | 200 | 20.03s | `mcp:vista get_catalog` → `OUTCOME_CONTRACT_FACTS` | **PASS** |

**D5 (antes FAIL → agora PARTIAL):** o dump `entities.playlist`
desapareceu — a projeção determinística renderiza o índice `productGuide`
verbatim do owner, incluindo o tópico `display_formats` ("Formatos de
exibição — moeda, percentual, data, número"). `GROUNDED/OBSERVATION`,
zero limitações. Residual honesto: resposta é o índice completo de
tópicos (diluído) e o `displayFormatCatalog` concreto
(`general`/`number-0`/`number-2`/…) não foi projetado — evidência
relevante existe e não vazou schema, mas a projeção ainda é ampla.
Tokens reais: 8076in/968out; `composition_mode=deterministic`.

**D5-R (antes PARTIAL → agora PASS):** `index_select` ligou o tópico
correto e o doc `block_types` ("Tipos de bloco — texto, KPI, gráfico,
tabela, imagem") foi projetado verbatim com `purpose/use_when/how_to_use/
do_not_use_when` — resposta semanticamente correta a "tipos de
visualização". Residual: rótulos estruturais em inglês na projeção.
Tokens reais: 9128in/927out.

**D4:** listagem viva verbatim de DAVI/TÉO/VISTA + rodapé
publicação≠permissão; `NON_GROUNDED` + `capability_surface_listing`.

**D8:** registro real `TERM. OLHAL M6 6,30MM 4,00-6,00MM2 12,00MM COMP
22,60MM ESTANHADO S/ISOLACAO FITADO ROHS` verbatim, `GROUNDED`. Residual
conhecido: `Group code` sem rótulo PT-BR (lacuna do recurso `field_labels`).

**D8-R:** caminho correto (`discover_delpi_information` no DAVI) mas o
turno terminou em insuficiência honesta sem encadear `execute_delpi_information`
— variância de decisão do Kimi, zero fabricação. Classificado PARTIAL
(na homologação anterior o encadeamento completou).

**N1:** resposta SIPOC correta, `NON_GROUNDED`/`HYPOTHESIS` honesta, zero
chamada MCP.

**Controle D5-schema:** pergunta explícita sobre contrato/entidades/campos
→ `contract_subject=True` → contract facts projetados normalmente — a
porta de intenção funciona nos dois sentidos.

**Segurança:** 401 fail-closed sem bearer; `attempt=1` em todos os
estágios; zero writes/ACT; zero 502/504; nenhum secret em logs/commits;
arquivos temporários removidos do servidor.

## 8. Comparação com a baseline (doc 123)

| Caso | Antes | Depois |
| --- | --- | --- |
| D5 | FAIL (`entities.playlist` dump) | PARTIAL (índice de guidance owner, tópico formatos visível) |
| D5-R | PARTIAL (insufficient_evidence) | PASS (doc de guidance projetado) |
| D4 | PASS | PASS |
| D8 | PASS | PASS |
| D8-R | PASS | PARTIAL (variância de encadeamento discover→execute) |
| N1 | PASS | PASS |

## 9. Lacunas materiais e resíduos

1. **D5 ainda PARTIAL**: a projeção privilegia `productGuide` (índice de
   tópicos) e não aprofunda em `displayFormatCatalog`/`display_formats`
   — a evidência existe no payload mas o digest não a foca. Decisão de
   refinamento de projeção = fora deste pacote bounded.
2. **D8-R encadeamento discover→execute** depende de decisão do modelo;
   insuficiência honesta quando não encadeia (não é regressão do fix —
   path não tocado).
3. **Rótulos PT-BR**: `Group code`/`Product code`/`Group category` seguem
   sem rótulo (recurso `field_labels` v4 — lacuna conhecida do S3).
4. **Projeção de guidance em forma semi-estruturada** (`title:`/`summary:`)
   em vez de prosa — apresentação determinística governada, conteúdo
   fiel; melhoria de fluidez = decisão de produto.

## 10. Arquivos, ledger e veredito

**FILES_CHANGED:** `delia-api/app/application/capability_provision/orchestration.py`,
`delia-api/app/application/capability_provision/outcome_assessment.py`,
`delia-api/tests/test_c3_contextual_discovery.py`,
`delia-api/tests/test_c3_d5_evidence_relevance.py` (novo).

**DOCS:** este doc + README index + execution ledger §6.403.

**EXECUTION_DRIFT:** NONE — escopo do doc 124; nenhum subescopo adicional.

**REWORK:** este foi o pacote bounded autorizado; limite respeitado.

**EXECUTOR_VERDICT:** correção generalizante implementada, verde no SHA
de release, deployada e homologada em produção com identidade autorizada.
O comportamento proibido (schema `entities.*` como resposta funcional)
foi eliminado; consultas contratuais legítimas preservadas; D5-R
completo. Não declaro ACCEPT — resíduos (D5 índice amplo, D8-R
encadeamento, rótulos, fluidez de projeção) ficam para a revisão
independente da coordenação.

`COORDINATION_REVIEW_REQUIRED=YES`
