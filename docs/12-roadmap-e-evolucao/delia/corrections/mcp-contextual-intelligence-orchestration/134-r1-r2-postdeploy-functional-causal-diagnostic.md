# 134 — Diagnóstico causal pós-deploy R1/R2: D5-R, D8-R e D5-schema

**TASK_ID:** `DELIA-ORCH-REFAC-R1R2-POSTDEPLOY-FUNCTIONAL-CAUSAL-DIAGNOSTIC-01`
**PLAN_ID:** `DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01`
**REFERENCE_REVIEW:** `9d7d61205fbf8e0518e2f88325c81fb2d67bb094` (parecer independente — D5-R funcional FAIL, D8-R PARTIAL, D5-schema INCONCLUSIVE)
**Data:** 2026-10-23
**Natureza:** diagnóstico causal read-only. Nenhuma correção implementada. Nenhum deploy.

---

## 1. Reancoragem

| Item | Valor verificado |
|---|---|
| Doc HEAD | `924bbeba9caaf293d42ad9812b929e52c40a826a` (= `origin/main`) |
| Baseline pré-refatoração | `6a896a695d947566cf7a7b730e836585a954e692` |
| Código R2 revisado | `738cc50efab8bf9e1d68a01d331ecbc40561cb80` |
| Release integrado avaliado | `0660f49af0f2abf8228519bca84df410b57fdd0f` |
| Imagem produtiva (reverificada nesta task) | `sha256:ee155bf5a325…` — **inalterada** |
| Rollback image | `1201882fdceb` (retida) |
| Checkout prod srv-api | `924bbeba9caaf293d42ad9812b929e52c40a826a` |
| delia-api em origin/main vs avaliado | idêntico exceto `scripts/r1r2_integrated_eval.py` (script de evidência, fora do runtime) |
| Modelo produtivo | `moonshotai/kimi-k3`, CRI ativo |
| Modelo dev | `delia-json` (qwen2.5:3b), T=0.2 — **não equivalente ao produtivo** |

Working tree principal contém trabalho concorrente (api-delpi supplies) — não tocado. Diagnóstico documentado em worktree isolada sobre `924bbeba9c`.

## 2. Método

Traces redigidos do runtime produtivo (`delpi-delia-api`, correlation_id por turno, sem payload sensível) + reprodução determinística em nível de unidade no stack dev (DAVI `retrieve_eligible_actions`, índice de ações, allowlist v23) + comparação de código baseline vs avaliado (`git show`) + inspeção dos módulos `orchestration.py`, `outcome_assessment.py`, `conversational_response.py` e do owner DAVI (`api-delpi/app/application/external_capabilities/dynamic_information/`).

Cadeia rastreada por cenário: `USER INPUT → CONTEXT → INTENT/GOAL → SELECTION → DISCOVERY → CANDIDATE RESOLUTION → ARGUMENT BINDING → PROVIDER INVOCATION → OWNER RESULT → EVIDENCE PROJECTION → OUTCOME ASSESSMENT → CRI COMPOSITION → PRESENTATION`.

## 3. Cenário D5-R — `entities.playlist` em pergunta funcional de visualização

### 3.1 Trace produtivo (correlation `f74d8044`, imagem `ee155bf5a325`)

```text
goal_understanding  decision=interpreted class=read subject=yes
                    prior_sufficient=no contract_subject=YES
target_selection    group=mcp:vista capability=get_catalog class=DISCOVERY
provider_invoke     ok capability=vista.get_catalog arg_keys= 63ms
discovery_terminal  decision=CAPABILITY_NOT_ENUMERABLE eligible=None
outcome_assessment  decision=contract_facts
cri_response        decision=composed presented=1
```

Três turnos irmãos D5 (`5a677e82`, `c0ecca32`, `305de7e5`), mesma família de pergunta, **mesmo capability/payload**: `contract_subject=NO` → mesmo `discovery_terminal` → renderização guidance-aligned ("Guia do produto" com tópicos de formato, ex. `block_types`) → resposta funcional correta.

### 3.2 Mecanismo comprovado

1. O modelo declarou `contract_subject=yes` para "quais tipos de visualização a DÉLIA suporta?" — leitura legítima mas divergente da intenção funcional.
2. Com `contract_subject=yes`, `assess_outcome` abre o gate `contract_facts` (outcome_assessment.py, `OUTCOME_CONTRACT_FACTS`) — comportamento contratual correto por decisão (doc 124: metadata de contrato só substitui evidência empresarial quando a intenção contratual foi declarada).
3. `_contract_fact_rows` emite **linhas de entidade primeiro** (`entities.<name>: <json>`, breadth-first, bounded `MAX_CONTRACT_FACT_ENTITY_ROWS=4`) antes das seções achatadas. O payload `vista.get_catalog` publica `entities: [{id: playlist, ...}]` via `tv_app/application/gpt_actions/capability_surface.py`.
4. `compose_cri_response` renderiza `leads.contract_facts` + as linhas bounded — precedendo o conteúdo guidance já projetado em `truthful.content_text` (`_deterministic_guidance_content`), que continha o tópico semanticamente relevante (tipos de bloco/formato).

`entities.playlist` é vocabulário contratual **publicado pelo owner** (não control-plane, não secret). O vazamento é de ruído técnico, não de segurança.

**Linha de decisão (doc 124/126):** a correção generalizante anterior criou exatamente o gate `contract_subject` — antes, `OUTCOME_CONTRACT_FACTS` era intent-blind e promovia `entities.*` em qualquer turno. O gate funciona como desenhado; o resíduo migrou para a fronteira: (a) a declaração de intenção em si (variância/modelo numa pergunta ambígua) e (b) o que a branch contract_facts projeta e com que precedência quando o gate abre (rows genéricas `entities.*` deslocam guidance relevante ao assunto).

### 3.3 Classificação

| Campo | Valor |
|---|---|
| SCENARIO | D5-R |
| EXPECTED_OUTCOME | Lista funcional de tipos de visualização suportados |
| OBSERVED_OUTCOME | Lead contract_facts + `entities.playlist` verbatim |
| FIRST_CAUSAL_DIVERGENCE | `goal_understanding` — declaração modelo `contract_subject=yes` para pergunta funcional (irmãos declararam `no`) |
| RESPONSIBILITY | classificação de intenção (modelo) + precedência/orde­namento determinístico de projeção e composição |
| OWNER | estágio de intent (instrução governada R1) / `outcome_assessment.py` (`_contract_fact_rows`) / `conversational_response.py` (branch contract_facts) |
| CANONICAL_CONTRACT | `OUTCOME_CONTRACT_FACTS` gated em `contract_subject` (doc 124); contrato de rows `_contract_fact_rows` |
| BASELINE_COMPARISON | **idêntico** em `6a896a695d` — emissão `entities.<name>:` byte-idêntica, gate `contract_subject` idêntico (residual pré-existente §6.413/§17781) |
| ROOT_CAUSE | `MODEL_VARIANCE` na fronteira de intenção **expondo** fragilidade determinística: rows genéricas `entities.*` precedem conteúdo contratual relevante ao assunto e a branch contract_facts desloca o guidance projetado |
| EVIDENCE_STATUS | PROVEN (trace + código + baseline diff) |
| CORRECTION_CLASS | correção bounded de composição/projeção (p.ex. precedência de guidance quando projetado; ou ordenação subject-aware de contract rows) — mudança de comportamento, requer autorização |
| REUSE_DECISION | EXTEND (mesmas funções owner) — condicionado a autorização |
| RISK | ruído técnico user-facing; zero risco de secret/control-plane |
| NEXT_ACTION | retornar à coordenação com proposta bounded de precedência/ordenação |

## 4. Cenário D8-R — discover executado, consulta contextual não concluída

### 4.1 Trace produtivo

```text
goal_understanding  class=read output_mode=snapshot contract_subject=no
target_selection    group=mcp:davi capability=discover_delpi_information class=DISCOVERY
provider_invoke     ok davi.discover_delpi_information arg_keys=query
provider_invoke     ok davi.discover_delpi_information arg_keys=query   ← retry folded
discovery_terminal  decision=CAPABILITY_NOT_MATCHED eligible=95
outcome_assessment  decision=envelope_only reasons=no_business_data
cri_response        decision=composed presented=0 delivered=0
```

### 4.2 Reprodução determinística (dev api-delpi, índice técnico 769 ações; allowlist prod v23 = 95 elegíveis, `search_products` presente)

| Query | `retrieve_eligible_actions` top-K |
|---|---|
| `use o davi para consultar a descricao do material 10080043` | `[]` |
| `descricao do material 10080043` | `[]` |
| `liste os tipos de visualizacao suportados` | `[]` |
| `descricao do produto 10080043` | `search_products 0.91` |
| `consulta produto por codigo` | `search_products 0.905`, `get_product_stock 0.71`, … |

`search_products.searchable_text` contém `produto/produtos/buscar produto/descricao do produto/codigo do produto` e **zero** tokens `material`. O retrieval DAVI (`discover_service`/`retrieval`) é lexical (alias/filler-tolerant/ordered-subsequence + quarantine) — não semântico. `material`↔`produto` não está no vocabulário indexado do owner.

A DÉLIA comportou-se corretamente: retry bounded com query context-folded (segundo `provider_invoke` no trace), terminal honesto `CAPABILITY_NOT_MATCHED` ("busca sem resultado ≠ capability ausente"), `presented=0`, zero fabricação, zero ACT.

### 4.3 Classificação

| Campo | Valor |
|---|---|
| SCENARIO | D8-R |
| EXPECTED_OUTCOME | discover → candidato → `davi.read_delpi_information` → registro do material |
| OBSERVED_OUTCOME | discover ×2, `CAPABILITY_NOT_MATCHED eligible=95`, terminal honesto |
| FIRST_CAUSAL_DIVERGENCE | **OWNER** — `retrieve_eligible_actions` (DAVI): zero candidatos para vocabulário `material` |
| RESPONSIBILITY | vocabulário de retrieval do owner (searchable_text/aliases) |
| OWNER | DAVI — `api-delpi` `dynamic_information` (retrieval + conteúdo/allowlist v23). **Não** é defect do orquestrador DÉLIA |
| CANONICAL_CONTRACT | contrato discover→candidate→candidate-bound READ do owner; resposta honesta DÉLIA preservada |
| BASELINE_COMPARISON | idêntico — mesmo retrieval owner, mesmo caminho orquestrador em `6a896a695d` (`_context_folded_discovery_query` já existia) |
| ROOT_CAUSE | `OWNER_VARIANCE` / `CONTRACT_LIMITATION` — gap de vocabulário lexical (material↔produto) no índice de retrieval DAVI. Determinístico em nível de unidade |
| EVIDENCE_STATUS | PROVEN |
| CORRECTION_CLASS | owner externo (enriquecer aliases/searchable_text para sinônimos de domínio material↔produto). Fix lexical na DÉLIA seria regra provider-específica → `ARCHITECTURE_DECISION_REQUIRED` se pretendida |
| REUSE_DECISION | REUSE (owner estende vocabulário existente) |
| RISK | nenhum introduzido; fail-closed manteve-se |
| NEXT_ACTION | coordenação: alinhar com owner DAVI extensão de vocabulário de retrieval |

## 5. Cenário D5-schema — pergunta explícita de contrato, resposta honesta sem satisfação

### 5.1 Trace produtivo (`2c787e76`, `58adece2`)

```text
goal_understanding  class=read contract_subject=YES
target_selection    group=mcp:davi capability=discover_delpi_information class=DISCOVERY
provider_invoke     ok davi.discover_delpi_information arg_keys=query
model_propose       ok purpose=...candidate_arguments
interaction_completed                                    ← turno termina aqui:
(sem provider_invoke encadeado, sem outcome_assessment, sem discovery_terminal)
```

### 5.2 Mecanismo comprovado

1. Discover DAVI retornou candidatos (reprodução dev: `search_protheus_columns_in_table`, score 0.897 — match lexical em "campos/colunas").
2. O candidato exige `tableName` (path, required) + `q` (query, required). `tableName` não é derivável de "quais campos o contrato de informações da DELPI expõe" → proposta `candidate_arguments` falha validação → `merged=None`.
3. `candidates_present` → `return None` (NOT_APPLICABLE honesto) — **sem** chegar à projeção `contract_facts`.

Assimetria estrutural: no branch zero-candidatos, o terminal projeta `contract_facts` (`truthful.contract_facts=_contract_fact_rows(outcome)`). No branch candidatos-presentes-mas-inutilizáveis, o outcome é descartado inteiramente — inclusive os `argument_schema`/`required_arguments` publicados pelo owner, que **são** conteúdo contratual legítimo para um turno `contract_subject=yes`.

Nota de semântica owner: o candidato escolhido (`search_protheus_columns_in_table` = introspecção de colunas Protheus/DB) não é o "contrato de informações DELPI" que a pergunta visava — match lexical plausível, semântica divergente.

### 5.3 Classificação

| Campo | Valor |
|---|---|
| SCENARIO | D5-schema |
| EXPECTED_OUTCOME | campos/parâmetros do contrato publicado |
| OBSERVED_OUTCOME | resposta honesta "sem registro" (`presented` implícito 0) |
| FIRST_CAUSAL_DIVERGENCE | terminal `candidates_present → return None` em `orchestration._invoke_for_capability` descarta o envelope — incluindo contract info publicada — antes de qualquer projeção contratual |
| RESPONSIBILITY | tratamento de terminal DISCOVERY no orquestrador (determinístico) + semântica de candidato do owner |
| OWNER | `orchestration.py` (branch DISCOVERY, `candidates_present`) — assimetria vs branch zero-candidato |
| CANONICAL_CONTRACT | `contract_subject` + `contract_facts` (doc 124); candidato owner `argument_schema`/`required_arguments` |
| BASELINE_COMPARISON | idêntico em `6a896a695d` — mesma assimetria de branch |
| ROOT_CAUSE | `ORCHESTRATOR_DEFECT` determinístico (assimetria candidatos-presentes vs zero-candidatos sob `contract_subject`) — com contribuição `CONTRACT_LIMITATION` owner (candidato semânticamente divergente por retrieval lexical) |
| EVIDENCE_STATUS | PROVEN (mecanismo); conteúdo exato das linhas que seriam projetadas = TO_INVENTORY |
| CORRECTION_CLASS | correção bounded: estender terminal candidatos-presentes para projetar `contract_facts` quando `contract_subject=yes` — preservando honestidade "candidato inutilizável". Requer autorização |
| REUSE_DECISION | EXTEND (mesmo terminal, mesma projeção `_contract_fact_rows`) |
| RISK | moderado — não pode promover schema a FACT empresarial nem sugerir execução; manter bound |
| NEXT_ACTION | coordenação: decidir se a correção bounded pertence à DÉLIA e seu contrato de apresentação |

## 6. A/B baseline vs release

| Cenário | Baseline `6a896a695d` | Release `0660f49af0` | Δ |
|---|---|---|---|
| D5-R `entities.*` verbatim | caminho idêntico (byte-idêntico) | idêntico | **sem regressão** |
| D5-R gate `contract_subject` | idêntico | idêntico | sem regressão |
| D8-R folded retry + terminal honesto | idêntico | idêntico | sem regressão |
| D8-R retrieval owner "material"→0 | idêntico (owner inalterado) | idêntico | sem regressão |
| D5-schema `candidates_present → None` | idêntico | idêntico | sem regressão |

**Conclusão A/B:** os três resíduos são **pré-existentes** à R1/R2. A refatoração (extração AST-idêntica) não introduziu regressão em nenhum dos três caminhos causais.

## 7. Generalização e segurança

- **Generalização:** o gap D8-R é estrutural — retrieval lexical owner-side falha para qualquer vocabulário de domínio fora dos aliases indexados (prova: "material"→[] vs "produto"→0.91). Não é sanável por blacklist de termos na DÉLIA sem regra provider-específica (proibida). O gap D5-schema/D5-R é estrutural na precedência/assimetria de projeção — não depende de VISTA/`entities.playlist` específico.
- **Controles de matriz anteriores** (doc `r1-r2-integrated-release-homologation.md` + evals): capabilities renomeadas/reordenadas, provider ausente, resultado vazio, schema legítimo, payload malicioso — executados previamente; reexecução completa nesta task = `TEST_NOT_RUN` (escopo: rastreio causal, não re-homologação).
- **Segurança:** `entities.playlist` é vocabulário contratual publicado pelo owner (sanitizado pela pipeline `_sanitize_renderable`/`_redact_text`), não control-plane nem secret. Zero ACT/write em todos os traces. Unauth 401 e injection fail-closed mantidos (homologação anterior). Invariantes `DISCOVERY != APPROVAL`, `MODEL OUTPUT != FACT`, `READ != WRITE`, `PREPARE != ACT`, `HTTP 200 != BUSINESS OUTCOME` preservadas.
- **Semântica de "contrato":** para "campos do contrato DELPI", o match lexical do owner vai a introspecção de DB — limitação de vocabulário owner, mesma família do gap D8-R.

## 8. Status separados

| Estado | Valor |
|---|---|
| LOCAL_TEST_STATUS | diagnóstico determinístico PASS; reexecução de matriz ampla TEST_NOT_RUN |
| INDEPENDENT_REVIEW_STATUS | pendente — esta task produz evidência para a coordenação |
| DEPLOY_AUTHORIZATION | n/a — deploy não executado nem solicitado |
| DEPLOY_STATUS | NOT_EXECUTED (proibido nesta task) |
| PROD_AUTH_HOMOLOGATION | reutilizada a evidência da task anterior; traces desta task = observação read-only |
| BUSINESS_OUTCOME_STATUS | D5-R FAIL funcional, D8-R PARTIAL, D5-schema INCONCLUSIVE — confirmados pelo diagnóstico (classificações da revisão independente mantidas) |

## 9. Recomendações de correção (não implementadas)

1. **D5-schema / assimetria de terminal (bounded, DÉLIA):** no branch `candidates_present`, quando `contract_subject=yes`, projetar `contract_facts` (mesma `_contract_fact_rows`) em vez de descartar o envelope — mantendo a honestidade "candidato não executável" como limitation. Owner: `orchestration.py` DISCOVERY terminal + testes caracterizados.
2. **D5-R / precedência de composição (bounded, DÉLIA):** quando guidance goal-aligned foi projetado no terminal DISCOVERY, dar-lhe precedência de apresentação sobre rows `entities.*` genéricas (ou ordenar rows por relevância ao assunto declarado). Owner: `conversational_response.py`/`outcome_assessment.py`. Alternativa estrutural: refinar a semântica `contract_subject` na instrução governada (recurso R1).
3. **D8-R / vocabulário owner (externo, DAVI):** enriquecer `searchable_text`/aliases das ações de produto com sinônimos de domínio (`material`, `materiais`, `item`, `código de material`) no índice/allowlist DAVI. Owner: `api-delpi` `dynamic_information`. Alternativa DÉLIA-side (normalização semântica de query) exigiria regra provider-neutra genérica — `ARCHITECTURE_DECISION_REQUIRED` se pretendida.

Nenhuma recomendação contradiz ADR 58, S4/117 ou contrato de Evidence que exija `ARCHITECTURE_DECISION_REQUIRED` imediato — exceto a alternativa 3-DÉLIA, já sinalizada.

## 10. Próximo passo finito

Retornar à coordenação com este diagnóstico: três causas-raiz PROVEN, todas pré-existentes (zero regressão R1/R2), com três propostas de correção bounded (2×DÉLIA, 1×owner DAVI) aguardando autorização. `R3_AUTHORIZED=NO`.


## 11. Parecer independente da coordenação — 2026-10-23

**REVIEWED_DELIVERY_SHA:** `3fa0b17165f3a93c99c8da64c4b92971de47cf10`  
**REVIEW_VERDICT:** `ACCEPT_WITH_RESIDUAL` (diagnóstico causal, não aprovação das propostas de correção nem homologação funcional integral).  
**R3_AUTHORIZED:** `NO`. **DEPLOY_AUTHORIZED_BY_THIS_REVIEW:** `NO`.

**Verificação GitHub:** doc 134, README e ledger constam no commit entregue. O diagnóstico apresenta traces produtivos redigidos, reprodução de retrieval lexical DAVI, comparação de código e diferenças de terminal/discovery. Não houve reexecução independente de unit tests, SSH ou modelo nesta revisão; `PROVEN` descrito pelo executor não é automaticamente prova reproduzida pelo reviewer. A conclusão de zero regressão é limitada aos mecanismos examinados, não equivale a `GLOBAL_BUSINESS_OUTCOME=PASS`.

**D5-R:** aceitar a causalidade `contract_subject` variável + `contract_facts` com prioridade sobre guidance já projetado. Correção bounded DÉLIA elegível apenas se validar contratos, owner, relevância da evidência e consultas contratuais positivas, sem regra lexical/provider-specific e sem transformar guidance em preferência absoluta.

**D8-R:** aceitar o gap lexical `material` versus `produto` no retrieval DAVI como limitação do owner, com prova unitária reportada. Encaminhar ao owner `api-delpi/dynamic_information` para avaliar aliases governados, generalização e testes; nenhuma normalização específica na DÉLIA e nenhuma autoridade de alteração cross-bounded por este parecer.

**D5-schema:** aceitar o descarte de envelope em `candidates_present → return None` como mecanismo candidato ao reparo. **Não autorizar projetar indiscriminadamente** `argument_schema` de candidato semanticamente inadequado (`search_protheus_columns_in_table`) como contrato geral da DELPI. Antes do fix, provar vínculo typed entre a pergunta contratual, o subject/capability owner e a seção contratual que será mostrada, ou retornar insuficiência honesta. Isso é gate de contrato/semântica, não detalhe cosmético.

**NEXT:** duas decisões bounded separadas: (A) autorizar diagnóstico-implementação DÉLIA de precedência e preservação de envelope, condicionado a testes positivos/negativos, owner/contrato, RED→GREEN e generalização; (B) encaminhar gap DAVI a seu owner legítimo. Nenhuma task R3, novo módulo/registry, mudança de auth ou deploy automático decorre deste parecer. Antes de implementação, reancorar HEAD, 16 + ledger e autoridades completas.
