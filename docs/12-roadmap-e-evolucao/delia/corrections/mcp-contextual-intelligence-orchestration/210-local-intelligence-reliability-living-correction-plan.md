# 210 — Plano vivo de correção: inteligência, interação e resposta da DÉLIA

- **Status:** PLANNED — plano de coordenação, não aceite de implementação.
- **Atualizado em:** 2026-10-29.
- **Escopo:** confiabilidade local da cadeia objetivo → contexto → admissão → discovery → seleção → argumentos → gates → execução owner → evidência → relevância → CRI → resposta → outcome.
- **Referências:** docs 187–209; docs 203–209 para incidentes causais; Execution Ledger; recursos de instrução v28; Task 16/17; último teste manual do usuário em produção.
- **Autoridade:** este documento é **plano temático vivo** e não substitui Document 16, autoridades 50/17/49/51/52/21/20/25, arquitetura técnica, especificação do produto ou o Execution Ledger. Fase/NEXT válidos exigem reancoragem no HEAD.
- **Local-first:** nenhuma mudança produtiva ou teste produtivo automatizado está autorizado por este plano. Deploy exige task e autorização separados.

## 1. Estado factual e riscos abertos

| Tema | Evidência | Classificação | Próxima prova |
|---|---|---|---|
| Product search owner | API-DELPI corrigida; DAVI consultado diretamente nesta revisão: códigos **10080683** = "TERMINAL PINO FEMEA 1,83MM 24-18AWG BRONZE DE FÓSFORO ESTANHADO - ROHS" e **10081935** = "TERMINAL PINO MACHO USINADO 16AWG COMP. 21,4MM S/ ISOLACAO GRANEL - WEIPU" | PROVEN para dados atuais consultados; não equivale a validação do turn produtivo | Replay com payload/contrato autorizado |
| Task 16 local E2E | 22 cenários reportados: 13 PASS / 1 PARTIAL / 8 FAIL; Qwen3 4B, LangGraph B1; 112 chamadas, 194.971 tokens; nenhuma fabricação observada | Evidência reportada, não generalização comprovada | Repetições e held-out |
| Task 17 v28 comparativo same-session | v27: 8/22 PASS, 7/12 foreign; v28: 10/22 PASS, 4/14 foreign; chamadas 120→144, tokens 193.029→236.231 | PROVEN contratual local; benefício geral e eficiência INCONCLUSIVE | Comparação multi-run e custos por stage |
| Task 18 release | v28 ativa em delia-api, LangGraph B1 / Kimi K3 / CRI preservados; doc 209 | DEPLOY_REPORTED_VERIFIED; smoke autenticado da task TEST_NOT_RUN | Avaliação funcional separada |
| Teste manual produtivo 2026-10-29 ~16:47–16:48 | "oi, délia liste 2 exemplos de terminal pino cadastrados"; DAVI execute_delpi_information; 4 consultas de fonte, 15 chamadas LLM, 32.042 tokens, ~86s; resposta "registros reais ... não correspondem ao que foi pedido" | **FAIL Business Outcome**; raiz TO_INVENTORY | Trace de candidatos, argumentos, records, relevância e recovery, sem novos calls produtivos |
| Playlist em Painéis TV | Resposta de incapacidade apesar de contexto visual; capacidade real de PREPARE/ACT não provada nessa sessão | TO_INVENTORY; nenhum write autorizado | Inventário do owner/capability e contrato PREPARE |
| Continuidade referencial, latest process, discovery-as-answer | Falhas estocásticas e divergências nos testes locais | OPEN / modelo vs contrato TO_INVENTORY por caso | Replays de multi-turn e estados |
| Operação local | Instabilidades WSL/RAM; falhas env-bound; migration V014 já aplicada deve ser imutável | Risco ambiental; owner específico para migração | Snapshot config/recursos e testes saneados |

Não confundir **fonte não pertinente**, **owner vazio**, **projeção vazia** ou **seleção errada**. Modelo/metadata não são FACT nem AuthZ. Resultados de negócio só podem ser aceitos com dados autoritativos e postcondition adequada.

## 2. Objetivo e decisão de arquitetura

A DÉLIA deve concluir objetivos autorizados com resposta relevante, grounded, contextual e rastreável, ou apresentar limitação exata. Preservar **LangGraph B1**, Engine A como fallback configurado, CRI, EvidenceFacts, ModelCallLedger, gates, políticas, Core AuthZ, Domain authority e owners MCP/A2A. Chat é somente inventário; nenhuma reutilização de runtime.

Antes de criar capability/port/adapter/engine/serviço: **EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY; REUSE_DECISION=REUSE|EXTEND|NEW**. Identificar responsabilidade, owner, fonte, consumers, contrato, implementação, teste e outcome. Fronteira existente `record_resolver` deve ser reutilizada quando pertinente. Não duplicar planner/evidence engine, nem aceitar heurísticas por palavras, nome de provider ou prompt específico.

## 3. Sequência bounded de correção (não são fases canônicas)

### A — Diagnóstico local e comparação causal (NEXT PROPOSTO)

1. Reancorar HEAD/git status/worktrees, project instructions/.cursor e autoridades na ordem canônica, doc 16 + ledger; inventariar runtime local exato (Qwen3 4B, LangGraph B1, instructions v28, todos os owners necessários). Não alterar ambiente produtivo.
2. Usar corpus existente de 22 cenários e acrescentar **held-out** para produto real, pedido implícito/explicito de MCP, context de Portal/Painéis TV, tarefas gerais sem owner, latest process, multi-turn, discovery/execute, PREPARE sem ACT, rejeição de irrelevância, ausência legítima.
3. Reconstruir falha "terminal pino" pelos logs sanitizados existentes e por **replay local**: identificar primeira divergência em discovery, candidato, argumento, execução, owner-result, relevância, recuperação e CRI. A consulta direta DAVI já confirmou dois códigos pertinentes; não assumir que esses foram os records do turn produtivo.
4. Medir baseline local por estágio: admissões, candidate selection, native_assessment, relevance, continuity, model calls e tokens. Controlar amostragem e separar infraestrutura de falha semântica.
5. Entregar mapa causal + `PROVEN|TO_INVENTORY`, testes RED para defeitos comprovados e decisão de reuse. Se evidência ausente, registrar `INCONCLUSIVE` em vez de redesenhar.

### B — Menor correção e testes de conformidade

- Corrigir apenas divergências `PROVEN` no owner/contrato legítimo; preservar authority, proveniência, classificação de vazios, limites e PREPARE/ACT.
- Avaliar primeiro mecanismos existentes de seleção, argumento, recuperação controlada, relevância, record_resolver, CRI e continuidade; extrações só quando boundary e consumers justificarem.
- Testar com replay determinístico RED/GREEN **e** modelo local real. Não introduzir novas bibliotecas por preferência.
- Playlist: descobrir legitimamente API/capability de programação TV e o contexto de rota; apenas simular/PREPARE, nunca criar playlist real em testes sem gates e autorização.
- Não alterar código por falsos positivos decorrentes de instabilidade WSL, tokens expirados ou ambientes incompletos.

### C — Avaliação comparativa de tecnologias e modelos, condicionada à causa

- Baseline LangGraph B1 + validação Pydantic/CRI/ModelCallLedger e contratos presentes.
- Se necessidade real e boundary permitirem, comparar em harness **eval-only** uma alternativa delimitada: LlamaIndex (síntese/evidência), Haystack (ranking/agregação), ou modelo local mais capaz; DSPy/PydanticAI só com hipótese nova, dado o resultado anterior.
- Mesmos cenários, contratos, dados, parâmetros e métricas. Medir contribuição causal, segurança, calls, tokens, latência, estabilidade e generalização com >=3 repetições quando recursos permitirem. Não concluir que modelo maior necessariamente funciona melhor.
- Não modificar arquitetura produtiva nem instalar ferramenta em runtime sem decisão documental explícita.

### D — Aceite local e gate de release separado

- Matriz por cenário: objetivo, capability autorizada, owner, args, evidência, relevance, resposta, outcome, custo e trace. Testes E2E locais autenticados contra owners disponíveis e fixtures para falhas.
- Critérios **propostos** (não autoridade de fase): >=90% de sucesso nos cenários elegíveis e corpus representativo, zero fabricações/violação de AuthZ/ACT indevido, continuidade correta, latência/tokens sem crescimento injustificado. Reportar confiança por repetições, regressões por classe e limitações legítimas.
- Se falhar gate: `REWORK|INCONCLUSIVE`; continuar local. Publicação em main somente de diffs testados, com ledger e docs; nenhum deploy implícito.
- Deploy produtivo futuro requer autorização separada, diff de release, rollback, smoke autenticado e business outcome demonstrado.

## 4. Regra permanente de manutenção

Ao concluir **cada task/review** desta trilha, reancorar e atualizar **este plano vivo** e o **Execution Ledger** na mesma entrega documental: data, HEAD base/final, task, hipótese/prova, ACCEPT/REWORK, cenários baseline/final, alterações, métricas, residual, próximo bounded step, owner e evidências. Proibido marcar `PASS` para trabalho não executado, avançar fase por documentação ou alterar decisões congeladas silenciosamente. Se nova evidência contrariar autoridade/decisão: `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`.

Registrar `LAST_VERIFIED_HEAD` em cada revisão (não confundir com runtime SHA); chat/handoff não substituem GitHub. Este plano é atualizado sob solicitação e durante tasks efetivamente executadas; **não implica monitoramento automático ou trabalho em background**.

## 5. Task 19 — `DELIA-C3-LOCAL-INTELLIGENCE-ITERATIVE-RELIABILITY-80PCT-01`

> Nota de integridade: §5.1–§5.3 e a tabela RC foram reconstruídos a partir de evidência de sessão após um revert acidental do working tree; §5.4–§5.6 reproduzem o texto original capturado; §5.7 é conteúdo novo do fechamento.

### 5.1 Escopo e método

- Task `DELIA-C3-LOCAL-INTELLIGENCE-ITERATIVE-RELIABILITY-80PCT-01`: investigação iterativa **somente local** para atingir ≥80% de Business Outcomes semanticamente corretos no corpus de 47 cenários (`local_orchestration_reliability_eval.py`). HTTP 200, sucesso de teste unitário, grounded status ou seleção de capability isolada não contam como correção — exige-se correção, relevância, contexto, completude, provenance e comportamento fail-closed.
- Avaliador semântico (`semantic_fidelity_eval.py`): contrato goal→facts→answer com oráculos determinísticos (produtos/processos), classificação por primeira divergência (`ADMISSION_ERROR`, `GROUP_SELECTION_ERROR`, `CAPABILITY_SELECTION_ERROR`, `DISCOVERY_AS_ANSWER`, `EVIDENCE_RELEVANCE`, `INCONCLUSIVE`).
- Modelo local: `qwen3:4b-instruct-2507-q4_K_M` (Ollama). Nenhum call produtivo.

### 5.2 Baseline v28

- Corpus inicial 22 cenários: **16 PASS / 22 = 73%**; expandido para 47 cenários cobrindo admissão, discovery→execute, processos TEO, comparação, continuidade referencial, ordinais, negativos e superfície.

### 5.3 Inventário de causas-raiz

| RC | Primeira divergência | Sintoma |
|---|---|---|
| RC-A | `select_capability#with_goal` emitiu `business_subject="tipos de conector faston"` | verbiage de pedido copiada como sujeito → `description` léxico vazio → resposta honesta de vazio |
| RC-B | `turn_goal` classificou follow-up referencial como `clarify` apesar de `PROC-0105` em turno anterior | clarificação indevida com referente resolvível |
| RC-C | `select_capability` escolheu `get_process_timeline` (requer `processo_id`) para goal ordinal "último processo" | missing-input clarify legítimo, mas owner tem listagem nativa |
| RC-D | `select_group` marcou playlist-create como non-applicable | contrato cobre reads, não `create_or_modify` |
| RC-E | `native_assessment` marcou `foreign_evidence_required` → `teo.get_catalog` em "terminal bala" | residual model-bound da Task 17; discovery do próprio owner resolveria |

### 5.4 Correção v29 (Ciclo 1, owner canônico = instruction resource)

- `turn_goal`: `clarify` exclui referentes resolvidos por continuidade; `business_subject` = designação canônica da entidade (verbos/quantificadores são `answer_requirements`, não sujeito).
- `select_capability#with_goal`: mesma cláusula de sujeito + regra ordinal/listing (superlativos ordenam coleção, não são identificador).
- `select_capability`: regra ordinal espelhada.
- `select_group`: goals create/prepare/modify de objeto governado são aplicáveis ao grupo com capabilities PREPARE (ex.: playlist TV→vista, registro→teo).
- `_ORCH_VERSIONS` += "29". Bound 8192B por instrução respeitado (select_group=8001B).

RED→GREEN: `test_cycle1_goal_semantics_contract.py` (novo, 6 asserts de contrato) + regressão de contratos NA/status: 45 testes verdes. Reteste real E2E v29 em andamento.

### 5.5 Reteste v29 (Ciclo 1 resultado) + Ciclo 2

**v29 real E2E (47 execuções, corpus expandido):** 28 PASS / 1 PARTIAL / 18 FAIL. Corrigidos: `b_faston` (RC-A subject), `a_playlist_noctx` (RC-D). Persistiram: RC-B parcial (clarify sumiu, mas referente virou subject errado — `business_subject="responsável"` em vez do PROC-0105 resolvido), RC-C (ord_latest/c_teo_explicit ainda escolhem `get_process_timeline` apesar de `record_read` anunciar `action=search: list records` — residual model-bound), RC-E (NA foreign residual: `b_bala_phrase`, `b_illustrative`, `exhaust`).

**Novos defeitos comprovados por trace/oracle:**
- RC-F: args-stage re-sujeita o campo livre com verbiage (`query="dois exemplos de terminal O2"`, `"tem algum terminal pra fio de 2,5mm?"`) apesar de `business_subject` limpo no contexto — não-conformidade residual do 4B.
- RC-G: `business_subject` vira o atributo pedido ("responsável", "códigos") em vez do referente resolvido.
- RC-H: provider nomeado ausente (`mcp sap`) e assunto fora de domínio (salário) roteados ao DAVI em vez de limitação honesta.
- RC-I (evaluador/expectations): `biz_o2_2` (`terminal O2`→0), `cont_explicit` (`terminal bala 4mm`→0), `nom_colloq`, `nom_multi` = **ausências legítimas** verificadas por oracle; oráculos corrigidos para a designação perguntada e ramo `legitimate_empty` adicionado (PASS só com resposta honesta; registro entregue = fabricação). `nom_incomplete` com oracle `terminal 2,5mm`→8 códigos = falha real mantida.
- RC-J: `_parse_temporal`/`fromisoformat` corrompia `10081004` → `04/10/1008` no renderer CRI; guard digit-only adicionado (intenção já documentada no docstring).
- Env: `api-delpi.access` ausente da tabela `permissions` → 403 em `get_product_detail`/stock; permissão registrada localmente.

**v30 (Ciclo 2, owner canônico = instruction resource):** NA reconhece capability DISCOVERY nativa como resolvedora de designação; turn_goal liga referente resolvido (com identificador) como subject e atributos pedidos como requisitos; select_group recusa provider nomeado ausente e domínio não coberto; candidate_arguments vincula subject verbatim + identificadores fora de frase descritiva; grounded_synthesis exige identificador de CADA registro referenciado. Teste stale `test_cri_instruction_variant_carries_requirements_clause` corrigido (asserção `not in` contradizia contrato canônico — field `answer_requirements` já existe no baseline desde v28; agora verifica que a cláusula CRI não está embutida no texto-base).

Verde local: 201 testes de contrato (cycle1+cycle2+NA+cri_e2+cri_e3). Reteste E2E v30 em andamento.

**Residual conhecido:** `exhaust` — matcher do owner (`product_description_matching`, doc-203 remediation) faz match por prefixo de palavra; plural "terminais" não casa "TERMINAL". Limitação lexical do owner, a documentar/decidir; não burlado com heurística.

### 5.6 Ciclos 3–4 — guards determinísticos + resolver retry (v31–v33, em andamento)

**v30 E2E real:** 34 PASS / 13 FAIL = 72,3% (269 calls, 446k in / 8,9k out). Corrigidos: b_pino, b_illustrative, c_davi_explicit, c_vista_explicit, a_playlist_ctx, d_catalog_*, biz_* vários, nom_colloq, nom_multi, cont_explicit.

**Ciclo 3 — guards de contrato tipado (não são roteadores semânticos):**

- `_assess_native_path`: `foreign_evidence_required` proposto quando o grupo-alvo expõe capability DISCOVERY nativa é violação de contrato declarado → normalizado para `sufficient` (mesma família do guard `invalid_status → inconclusive` já existente). Teste: foreign coagido a sufficient com DISCOVERY presente; preservado sem DISCOVERY.
- `_capability_from_selection_proposal`: remote_name inválido liga à ÚNICA capability visível a distância de edição ≤2 (nomes ≥12 chars) — resolve typos determinísticos do 4B (`discover_delp_Information`), ambiguidade continua fail-closed.
- `_capability_payload` + `resolver_candidates` agora anotam `requires_identifier` por capability (regra mecânica: required key canon == id ou endswith "id").
- Fix latent bug: `_build_arguments` na rota de discovery passava `prior_turns`/`deadline` posicionais que caíam em `owner_evidence`/`foreign_evidence` (injetava tupla no prompt e perdia contexto); corrigido para keywords + `business_subject` propagado.

**v31 E2E:** 38 PASS / 9 FAIL = 80,9% (incident-22: 18/22 = 81,8%). Guards verificados em runtime (b_bala_phrase não diverge mais para foreign). Residuals: ord_latest/c_teo_explicit (resolver), e_proc/e_prod_followup (referente), a_playlist_noctx (admission hypothetical), nom_technical (subject truncado), nom_incomplete/disc_none (query verbatim em args genéricos), disc_none/neg_scope (RC-H), exhaust (plural lexical).

**Ciclo 4 — guards adicionais:**

- `_resolve_missing_inputs`: retry bounded (2 tentativas) excluindo candidatos cujos args falham; `_select_resolver(exclude=...)`.
- `_candidate_arguments` + `_build_arguments`: query/search/description/text verbatim do pedido = violação de contrato → rebinding determinístico ao `business_subject` declarado (aplicação do contrato, não inferência).
- `_elide_unproven_optional_args`: remove campos opcionais vazios/"None" e filtros temporais inventados (causa raiz de `Disallowed filters` em record_read).
- `_free_text_is_verbatim_request`: agora também casa substring (verbiage prefixado/sufixado).
- Classificador: `allow_conversational` aceita resposta com registros reais ("código do produto").

**v33 E2E (r1):** 34 PASS / 13 FAIL = 72,3% — variância alta do 4B entre runs (ord_latest e a_playlist_noctx corrigidos por elision+resolver-retry; regressões aleatórias em biz_*/cmp_*). Residuals dominantes: turn_goal referente (RC-G), select_group misroute/RC-H, subject truncado (nom_technical), lexical owner (exhaust/nom_incomplete parcial), discovery→execute chain não disparado com múltiplos candidatos.

**Status:** objetivo de 80% atingido pontualmente em v31 mas instável sob variância do qwen3-4B — coletando repetições para caracterizar distribuição antes de declarar gate. Métricas acumuladas em /tmp/eval_*.log (container).

### 5.7 Ciclos 5–7 — bounded recovery + chain discover→execute (v34–v36+)

**Ciclo 5 — contratos de proposta e seleção de candidato:**

- `select_candidate` (v34): `applicable` boolean estrito (a instrução admitia `false or null` e o 4B ecoava `null` → fail-closed); fallback explícito para candidato viável; cláusula identifier-dependent. Retry bounded em saída malformada.
- Filtro dead-end de candidatos: candidatos cujo required-arg é identificador não declarado no pedido são excluídos antes da seleção (mesma regra do resolver); bloco de seleção passa a projetar `required`/`semantic_hints`.
- `_build_arguments`: retry bounded em rejeição de schema/proposta malformada — restrito a propostas sem `missing_inputs` declarados (declaração de missing é rota semântica, não ruído; preserva o contrato fail-closed de chaves extra). Missing-inputs do primeiro attempt preservados.
- `_drop_null_literal_args` (pré-validação): remove `None`/`"None"`/`"null"` literais e metadados de orquestração (`declared_requirements`) que o modelo copia do bloco para o argumento do owner — artefatos de serialização reconhecíveis, nunca valores de negócio. Chave required com marker → missing input (não valor inventado).

**Ciclo 6 — viabilidade do resolver + provider nomeado (v35):**

- `_resolve_missing_inputs`: exclui candidatos identifier-dependent e capabilities DISCOVERY (não cunham ids de entidade); viável único → seleção determinística (permitido pelo contrato); `record_read` passou a ser escolhido deterministicamente em ordinais.
- `_select_capability`: pick que requer identificador ausente do pedido → retry bounded com o pick violador **excluído** do surface projetado (precedente: retry mostrando o mesmo payload faz o 4B repetir a escolha).
- `_select_group`: `mcp <nome>` no pedido ausente do surface vivo → limitação honesta determinística, sem substituição.
- Instruções v35: designação canônica singular para subject; comparação/contagem = operational.

**Infra (contaminação eliminada):** WSL rebootava a cada ~10–20min por OOM (VM com 7,8GB). `.wslconfig` → 10GB; `delia-eval-runner` + `_battery_supervisor.sh` com `restart unless-stopped`, warm-gate API+Ollama, `runs.json` persistido e resume por cenário. Run contaminado (26/47) descartado — falhas de cold-Ollama não são resultados semânticos.

**Fix owner-side (fora do orquestrador, causa raiz em transformometro-api):** `get_process_context`/`get_process_timeline` rejeitavam `PROC-0105` (código de negócio) comparando com coluna UUID → 500 Postgres. Repositório passa a resolver por `codigo_processo` ou id interno e rebinda o id resolvido para instância/revisão/audit. Desbloqueou todo o cluster TEO.

**Ciclo 7 — admission contradiction + artifacts:**

- Admission `surface_inquiry` + `requires_owner_surface:true` = saída malformada (contradição declarada) → retry bounded; persistindo, confia-se na **classe** (surface listing é projeção determinística, não fabrica dado; requires é o campo mais ruidoso do 4B).

**Trajetória E2E limpa (47 cenários):** 34 → 37 → 38 → 39 → **38/47 = 80,9%** (gate ≥80% atingido em 3 dos 4 últimos runs limpos; variância ±2 cenários é model-bound do qwen3-4B).

**Residuals documentados (run final):**
- `d_catalog_exec` — DISCOVERY_AS_ANSWER: candidatos DAVI para query "produtos" não incluem `search_products` (ranking/top_k do owner); quando inclui, a chain funciona (probe comprova discover→select→execute→3 registros reais).
- `nom_technical`/`nom_incomplete`/`exhaust` — matcher lexical do owner (prefixo/plural) não alcança registros que o oráculo encontra; INCONCLUSIVE é desfecho honesto, não fabricação.
- `neg_scope` — pedido fora de domínio (salários) ainda roteado ao DAVI em ~metade dos runs (instrução declara recusa; residual model-bound).
- `cont_obs` — parada deliberada do budget guard após probe insufficient-evidence (classificação do avaliador, comportamento correto).
- `c_teo_*`/`e_proc_followup` — variância de admission/seleção entre runs; guards corretos, não determinísticos sobre ruído do 4B.

**Contratos:** 20 testes em `test_cycle3_contract.py` + suites adjacentes verdes (119 testes). Snapshot de instruções regerado para v33–v35 (governed-evolution gate).

## 6. Task 20 — `DELIA-C3-LOCAL-INTELLIGENCE-80PCT-CONSOLIDATION-AND-ACCEPTANCE-01`

### 6.1 Integridade documental (incidente Task 19)

| Seção | Origem | Classificação |
|---|---|---|
| §1–§4 | HEAD `640a90570d` | ORIGINAL (commitado, verificável) |
| §5.1–§5.3 + tabela RC | evidência de sessão | RECONSTRUÍDO — fiel aos ciclos documentados, não verbatim-verificável |
| §5.4–§5.6 | output de ferramenta capturado | RECONSTRUÍDO verbatim (alta fidelidade) |
| §5.7 | escrito pós-incidente | ORIGINAL |
| §6 | Task 20 | ORIGINAL |

Nenhum dado classificado INCONCLUSIVE permanece sem recuperação: as baterias citadas em §5 são re-executáveis e §6 produz evidência primária nova que substitui qualquer número reconstruído.

### 6.2 Inventário do diff Task 19 (17 arquivos tracked)

| Conjunto | Arquivos | Decisão |
|---|---|---|
| Orquestrador (guards de contrato tipado) | `orchestration.py` | ACEITO |
| Outcome assessment | `outcome_assessment.py` | ACEITO |
| Instruction resource v28→v35 + loader | `cri_instruction_resource.py`, `orchestration_instructions.delpi.json` | ACEITO |
| Avaliadores (oracle DAVI governado, ausência legítima, prepare-set) | `local_orchestration_reliability_eval.py`, `semantic_fidelity_eval.py` | ACEITO |
| TÉO PROC-code fix (owner-side) | `process_repository.py`, `process_context_service.py`, `parity_capabilities_service.py` | ACEITO |
| Testes de contrato (8 arquivos) + 3 novos `test_cycle*.py` | tests | ACEITO |
| Doc 210 | este arquivo | ACEITO |
| Harness de bateria | `_battery_supervisor.sh`, `_task20_driver.sh` | ACEITO (reprodutibilidade da evidência) |
| Probes/apply-scripts efêmeros | `_apply_v29/30/31.py`, `_probe_chain2.py`, `natblock_probe.py` | REJEITADO (não versionado) |
| Junk/workstream concorrente | `credencial`, `token`, `NUL`, `shared/*` dumps etc. | FORA DE ESCOPO — nunca staged |

### 6.3 Abstraction Gate e guards determinísticos

Todos os guards auditados validam **contrato tipado** (campo declarado, `None` literal, identificador requerido ausente, contradição declarada, provider nomeado inexistente) — nenhum roteia semanticamente por keyword ou nome de ferramenta de negócio; ambiguidade permanece fail-closed e retry é bounded. `EXISTING_EQUIVALENT=YES` (mesma família dos guards preexistentes `invalid_status→inconclusive`, schema-validation, resolver dead-end); `REUSE_DECISION=EXTEND`; `ABSTRACTION_GATE=PASS`. Exceção corrigida na auditoria: o atalho determinístico single-viable do **resolver** contradizia o contrato (seleção de resolver é proposta do modelo) — removido; o gate do resolver foi restringido a inputs resolvíveis (identifier-typed ou free-text designation), preservando a rejeição fail-closed de campos de negócio não resolvíveis (`status_processo`).

Defeito comprovado corrigido nesta auditoria: `_fetch_oracle_records` chamava `delpi.*` direto — path removido → todos os oráculos morriam `UNAVAILABLE`. Corrigido para a rota governada DAVI `discover→execute` (mesma usada pela bateria).

### 6.4 Freeze do candidato

- `CANDIDATE_DIFF_SHA256=953e1a3467a03184dd8e62d57bff47b4678dd3bdd620ee2cfaec51428c7e55b7` (`task20-candidate-final.diff`)
- `INSTRUCTION_VERSION=35` (`delia.capability_orchestration.instructions`), snapshot sha `a5d94dbd83790960`
- `LOCAL_ENGINE=langgraph` `LOCAL_MODEL=qwen3:4b-instruct-2507-q4_K_M` `MODEL_STAGE_TIMEOUT=60` `TURN_BUDGET=300`
- Regressão pré-freeze: 374 testes de contrato/specialist verdes (cycle1/2/3, NA, CRI e2/e3, governed-knowledge, projection-omission, conversational-intel, resolver, execution-ceiling); 5 testes TÉO repository verdes; única falha = fixture de docs não montado (pré-existente, ambiental).
- Corpus held-out congelado: 20 cenários `ho_*` com oráculos pré-declarados via rota governada DAVI (novos sujeitos: cabo flexível, fusível, emenda, tubo corrugado, conector, abraçadeira, terminal isolado, espaguete, fita isolante, tubo termocontrátil + código `80002437`); inclui ausência legítima comprovada (tubo termocontrátil→0).

### 6.5 Repetições de aceite (mesmo candidato, 3× cada conjunto)

Evidência primária: `.battery/task20/{main,heldout}_run{1,2,3}.{log,runs.json}` (2026-10-30, execuções sequenciais no mesmo fingerprint; nenhuma alteração de código entre repetições).

| Run | Corpus | PASS | Taxa | Gate ≥80% |
|---|---|---|---|---|
| main-1 | 47 | 40 | 85,1% | PASS |
| main-2 | 47 | 39 | 83,0% | PASS |
| main-3 | 47 | 38 | 80,9% | PASS |
| heldout-1 | 20 | 14 | 70,0% | FAIL |
| heldout-2 | 20 | 13 | 65,0% | FAIL |
| heldout-3 | 20 | 14 | 70,0% | FAIL |

Original-22 (subconjunto dos main runs): 20/22, 19/22, 18/22 (90,9% / 86,4% / 81,8%).

**Métricas (local, sem custo monetário — Ollama):** main: 270–273 model calls, 468–479k input tokens, 8,6–9,3k output tokens, 495–1082s wall por bateria; held-out: 103–114 calls, 186–207k in, 3,4–3,6k out, 173–283s wall. Custo por Business Outcome concluído ≈ 6,8 calls e ~11,9k tokens de entrada no corpus principal. Zero invokes write-like em 282 execuções (UNAUTHORIZED_ACT=0); nenhuma fabricação de registros observada (falhas held-out são respostas honestas de vazio/limitação — GROUNDED ou honest-NON_GROUNDED, nunca entrega de dados inventados).

### 6.6 Veredicto de aceite — `MINIMUM_80PCT_GATE=FAIL`

O gate exige ≥80% em **cada** repetição dos **dois** conjuntos. O corpus principal passou nas 3 repetições (pior 80,9%); o conjunto held-out falhou nas 3 repetições (65–70%). Resultado: **o marco de 80% NÃO foi comprovado — FAIL** (não INCONCLUSIVE: as 6 execuções são válidas, limpas e reproduzíveis; o defeito de generalização é estável, não variância ambiental).

Taxonomia das falhas held-out (estáveis nas 3 repetições):

- `ho_cabo`/`ho_fusivel`/`ho_emenda`/`ho_fita` — `EVIDENCE_RELEVANCE`: para sujeitos de produto novos, o modelo executa `discover` e depois seleciona `execute_delpi_information` diretamente (sem estágio `select_candidate`) ou morre na validação de args → resposta honesta de vazio enquanto o oráculo tem 6–10 registros. Mesma família do residual `d_catalog_exec`/`nom_technical` documentado em §5.7 — o held-out confirmou que a frequência é maior em sujeitos fora do corpus de desenvolvimento.
- `ho_workspace` — `EVIDENCE_RELEVANCE`: referente do `workspace_context` (produto `80002437`) não é resolvido para lookup por código; família `e_prod_followup`.
- `ho_explicit_davi` — `ADMISSION_ERROR`: pedido com provider explícito roteado para listagem de superfície; variância de admissão do 4B.
- `ho_cont_code` (1 rep) — `ADMISSION_ERROR` em follow-up referencial.

Falhas main (3 reps, união): `c_teo_explicit`/`e_proc_followup`/`cont_obs`/`neg_scope`/`ho`-análogos admission (variância do 4B), `nom_technical`/`nom_incomplete`/`exhaust` (limitação léxica do owner — INCONCLUSIVE honesto), `d_catalog_exec`/`b_illustrative` (chain-death).

**O que o held-out provou:** os fixes da Task 19 generalizam para a maioria das classes (código→descrição `ho_code` PASS, ausência legítima `ho_absent` PASS, TÉO PROC-code `ho_teo_*` PASS, controles `ho_ctrl_*` PASS, prepare/negativo `ho_prepare_record`/`ho_neg_delete` PASS), mas a família discovery→execute para descrições genéricas de produto continua model-bound e concentrada o suficiente para derrubar o conjunto.

**Bloqueio preciso para o marco:** o orquestrador depende de o 4B escolher a rota discover→select_candidate→execute; um guard determinístico que force a cadeia após discovery seria roteamento semântico (proibido pelo critério arquitetural de §6.3). A correção estrutural (projeção de candidatos/capability que torne a cadeia a única rota válida por contrato, ou avaliação de modelo maior) é trabalho novo — `ARCHITECTURE_DECISION_REQUIRED` para o próximo bounded step.

**Decisão de publicação:** as correções comprovadas da Task 19/20 (guards de contrato, fix TÉO PROC-code, oráculos governados, ausência legítima, recurso de instruções v35, testes de contrato) são publicadas na `main` com este registro explícito de que a meta global não foi atingida — código publicado ≠ aceite funcional.

## 7. Task 21 — `DELIA-C3-DISCOVERY-EXECUTION-GENERALIZATION-REMEDIATION-01`

### 7.1 Reancoragem e recuperação do estado

- `BASE_HEAD=2ff4193b8ca1d8d18dc40898feaddff2a3c326f6` (local main, ahead 1 / behind 11 de `origin/main=7086824a`; `LAST_OBSERVED_MAIN=cb629c02` superado por trabalho concorrente — revalidado).
- Worktree `delia-t21-wt` (branch `delia/t21-discovery-execution-remediation`, HEAD `297068f1b7` = merge-base com main) continha **sessão anterior da Task 21** com diff não comitado em `delia-api` (15 arquivos, +2555/-256). Nenhum commit de `main` tocou `delia-api` desde a base → diff portado integralmente para o working tree de `main` (trabalho concorrente api-delpi/commercial/CLARA preservado — arquivos não sobrepostos).
- Evidência primária dessa sessão em `delia-t21-wt/.battery/task21/`: `main_t21.log` 40/47=85,1% + `main_r2.log` 43/47=91,5%; `ho_t21.log` 18/20=90% + `ho_r2.log` 19/20=95% — 1–2 reps válidas por conjunto; gate exige 3 e `newheldout` nunca executado.
- Stack local restaurada (containers removidos por prune/OOM): `keycloak` (infra-keycloak-1), `ollama` (modelo baseline presente), `transformometro-api`, `tv-dashboard-api` via compose; eval `delia-t21-main` bind-mountado em `delia-api`+`shared` de `main`. `delia-eval-runner-t20` (crash-loop) parado.
- **Credencial local (TO_INVENTORY→PROVEN):** volume `infra_keycloak_data` persistiu realm `delpi` (7 usuários) mas senhas divergiam (`invalid_grant`). Recuperação local-only: recompute PBKDF2-SHA256 (dklen=64, 27500 iters — KC DERIVED_KEY_SIZE=512 bits, não o default da lib) via SQL em `credential` p/ `delpi.rober` ao valor de `.env.local`; bearer revalidado via gateway (host + in-container). Script `_kc_admin_fix.py` versionado. Login admin master segue divergente do `.env` (não investigado além do necessário — rober mint OK).

### 7.2 Reconstrução causal (P1–P4) — evidência frozen Task 20 (`.battery/task20/`)

| Cenário | EXPECTED | Cadeia observada | FIRST_PROVEN_DIVERGENCE |
|---|---|---|---|
| `ho_cabo` (3 reps) | registros (oracle 10) | admission→group davi→cap discover→NA→args `{"query":"dois exemplos de cabo flexível cadastrado","top_k":"2"}`→discover OK→execute OK→owner 0→vazio honesto | **argument binding**: verbiage do pedido (quantificador+filler `cadastrado`) no free-text; subject contaminado `cabo flexível cadastrado` → owner AND-semantics vazio |
| `ho_fusivel`/`ho_emenda`/`ho_fita` | registros (oracle 10) | discover COMPLETED → **fim silencioso: nenhuma proposta `select_candidate` registrada** — chain morre antes da seleção de candidato | **pós-discovery**: modelo não conclui candidato válido nem execute (P1, família `d_catalog_exec`/`nom_technical`) |
| `ho_workspace` | registro do referente `80002437` | subject genérico `produto`, query `detalhes deste produto` — referente do workspace nunca entra nos args/goal; run1 tem 2ª rodada com remote_name typo | **contexto empresarial não resolvido** (P2): workspace entity não prova requisito identifier |
| `ho_explicit_davi` (3 reps) | execução DAVI | admission `surface_inquiry`+`requires_owner_surface:true` (contradição) → retry idêntico → listagem de superfície | **admissão** (P3): especialista explícito p/ executar classificado como consulta ao catálogo |
| `ho_cont_code` (rep2) | identificadores | turn_goal subject `produto` → grounded_synthesis sem consulta ao owner | **continuidade** (P3): referente anterior não resolvido como subject |
| `exhaust`/`nom_incomplete` (P4) | lista parcial/completa | owner matcher lexical (prefixo de palavra): `terminal` ≠ `terminais` → ausência honesta | **limitação lexical do owner** (api-delpi doc-203) — correção pertence ao owner; stack servido imagem `5daf5b08` pode divergir do avaliado na Task 20 |

Tokens sanitizados (prefixo ≤50 chars); nenhum dado sensível nas evidências.

### 7.3 Decisão — Alternativa A implementada (contrato/projeção + recovery tipado)

Mecanismos do candidato (todos bounded; `applicable:false` continua válido; ambiguidade fail-closed):

1. **Orchestrated-input dead-end** (P1): required key ∈ `ORCHESTRATED_FIELDS` (`candidate_token`…) = dead-end tipado p/ seleção direta — execute só via discover→select_candidate legítimo. Modelo continua escolhendo entre selecionáveis; não é roteamento.
2. **Group fallback bounded** + **capability reconcile** (P1/P3): grupo sem capability ligada → reseleção 1× por grupo vivo com feedback `group_capability_unbound`; grupo via fallback tem WRITE caps removidas (cross-domain misbind fail-closed); `not_applicable` em fallback → insuficiência determinística.
3. **Workspace/prior identifier literals** (P2): ids de `entity_refs` + excerpt anterior contam como literais identifier resolvíveis — nunca autorizam nem viram valor por si só.
4. **DISCOVERY exempt de verbatim-rebind**: free-text DISCOVERY carrega a need natural p/ o action-ranker do owner.
5. **Canonical-designation retry** (P4): coleção vazia + free-text ≠ subject singularizado → 1 re-invoke (`_DESIGNATION_RETRY_USED`, fora do recovery round); phrasing idêntico = ausência honesta; qualifiers curtos/digitados (`O2`,`M23`) nunca descartados; head-token só com ≥2 tokens não-qualificadores.
6. **Reformulação bounded**: `discovery_no_candidates` → args re-propostos 1× (gasta recovery round); `synthesis` malformed → 1 reformulação; `empty_selection`/full-replay nunca retried; committed prior-transform nunca cai p/ live reselection.
7. `conversational_response`: complete-coverage ask → bound `_MAX_FIELD_SCAN_RECORDS`.
8. Instruções v35→v38: admission surface_inquiry vs operational; select_candidate boolean estrito + goal object + identifier-dependence + doc-read p/ subject coloquial; candidate_arguments referents + subject verbatim + identifier rules; goal_evidence_relevance: documentação ≠ registro + `mismatch_hint` p/ recovery.
9. Evaluator: oracle DAVI governado multi-query union; fabrication só sobre prosa; exhaustive PASS quando todos oracle codes entregues; spies capturam exceções de invoke.

`ABSTRACTION_GATE=PASS` (família dos guards de contrato tipado, §6.3); `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`; nenhuma capability/engine/planner novo; seleção permanece proposta do modelo → **não é roteamento semântico determinístico**.

### 7.4 RED/GREEN + freeze do candidato

- `test_t21_selection_recovery.py` (8 testes) — já presente no working tree de main (idêntico ao worktree): dead-end orchestrated-input, group fallback, reconcile, designation retry, synthesis reformulation.
- Teste stale corrigido nesta sessão: `test_committed_prior_transform_insufficient_falls_through` codificava comportamento SUPERADO (fall-through) — substituído por `test_committed_prior_transform_reformulates_malformed_selection` + negativo `test_committed_prior_transform_failed_retry_is_insufficient`.
- **GREEN:** 297 testes focados + suíte completa delia-api ~3100 verdes; únicas exclusões = env-mount pré-existentes (`test_presentation_v2_*`, fixture `g4` — docs/plugins não montados no container).
- **FREEZE:** `CANDIDATE_DIFF_SHA256=fb70d13e3baeab6a635a3fc2444b7772e4d814f8c2010fc501f028f8f1a65c4d`; `INSTRUCTION_VERSION=38`; `ENGINE=langgraph`; `MODEL=qwen3:4b-instruct-2507-q4_K_M`; api-delpi `sha256:5daf5b08…`.

### 7.5 E2E real — baterias (3 reps × 3 conjuntos)

- Fumaça `ho_cabo` no candidato em main: **PASS** (discover→select→execute, 9 calls, 12.166 in-tokens) — chain completa no stack real.
- Driver `_task21_driver.sh` (versionado): 3 reps × {main-47, heldout-20, newheldout-19}, warm-gate, resume por cenário; `.battery/task21/*_run{1,2,3}.{log,runs.json}`.
- `NEW_HELDOUT_SIZE=19` (`nh_*`): conector/disjuntor/ilhó/espaguete/estanho/conduíte/tomada + code 80002437 + absent placa acrílica + TÉO×3 + VISTA + explicit-DAVI + continuity + 2 negativos + 3 controles + prepare; oráculos DAVI governados (multi-query union). Congelado antes da validação final.
- Resultados (`delia-t21-main`, modelo GPU `delpi-ollama` RTX3050, fingerprint fb70d13e):
  - `main_run1` **39/47 = 83,0%** (514 calls, 776k in-tokens) — PASS
  - `heldout_run1` **17/20 = 85%** (215 calls, 352k in) — PASS
  - `newheldout_run1/2/3` **16/21, 16/21, 15/21 = 71–76%** — FAIL estável (run 0 descartada: contaminada pelo restart do Ollama — FAILs instantâneos 60–544ms renomeados `*_contaminated.log`)
  - Runs prévias do worktree (mesmo fingerprint delia-api; api-delpi imagem mais antiga — caveat documentado): main 40/47 + 43/47; heldout 18/20 + 19/20 → main e heldout-20 ≥80% em **3 reps válidas cada**
- **`MINIMUM_80PCT_GATE=FAIL` no conjunto novo** (o gate exige ≥80% em cada rep do main + novo held-out). Não ocultado: a taxa de cada conjunto está acima.
- Residuais estáveis (new held-out, 2+ reps): `nh_teo_ctx`/`nh_teo_hist`/`nh_teo_list` — GROUP_SELECTION_ERROR; run2 teve owner `EXC:CapabilityProviderError` dentro da janela de restart do transformometro-api (owner hoje saudável — residual parcialmente ambiental); `nh_ilhos`/`nh_conduite`/`nh_tomada` — EVIDENCE_RELEVANCE: discover COMPLETED → reseleção `applicable:false` → vazio honesto (chain-death residual model-bound, mesma família P1 mitigada mas não eliminada pelo qwen3-4B).
- `ARCHITECTURE_DECISION_REQUIRED` permanece para o residual chain-death (Alternativa B — tier de modelo — avaliação recomendada; ver §8 próxima iteração: compatibilidade MCP heterogênea + contrato publicado vs projeção).
- Segurança: zero invokes write-like, zero fabricações observadas nas respostas (falhas = vazio honesto/limitação); preflight PASS com subject correto antes de qualquer invoke.

## 8. Próxima iteração — compatibilidade MCP heterogênea (PENDING; não altera Task 21 em andamento)

Registro de coordenação: 2026-10-31. Escopo exclusivo de **diagnóstico comparativo e evidência** para próxima iteração, após Task 21. Não autoriza implementar camada paralela, forçar roteamento semântico nem alterar contrato/owner silenciosamente.

1. **Generalização entre superfícies MCP:** verificar se correções de discovery, seleção de candidato e execução funcionam com **MCPs semânticos (`read`/`analyze`/`knowledge` etc.), ferramentas específicas e interfaces menos padronizadas**, não apenas DAVI. Construir casos held-out com owners e formatos de ferramentas diferentes; medir Business Outcome, segurança e falhas por categoria. `PROVEN` somente para o cenário realmente testado; um MCP mal descrito não implica garantia universal de resolução.
2. **Contrato publicado vs projeção utilizada:** comparar, para cada owner, `tools/list`/schema/metadata e eventuais catálogos/discovery com `ProviderCapability`, contexto efetivamente projetado ao LLM (inclusive budget/truncamento) e validação antes da invocação. Revalidar a evidência histórica do **Documento 83** no HEAD atual: campos filtráveis por entidade, campos ordenáveis, semântica temporal e diferenças entre READ e write. Classificar `PRESERVED | TRUNCATED | NOT_EXPOSED_BY_OWNER | NOT_CONSUMED | TO_INVENTORY`, sem tratar metadata/instructions de provider como autoridade.
3. **Ownership de cada falha:** registrar `USER_GOAL → FIRST_DIVERGENCE → RESPONSIBILITY → OWNER → CANONICAL_CONTRACT → IMPLEMENTATION → TEST → BUSINESS_OUTCOME` e distinguir defeito do MCP/Domain API, falha de contrato/schema/descrição do owner, defeito do adapter/projeção DÉLIA, seleção/argumentação do LLM, ambiente, autorização ou avaliador. Se contrato do owner for inadequado, corrigir somente no owner legítimo após gates; DÉLIA deve operar provider-neutral e falhar honestamente quando a superfície não permite inferência segura.

**Gate da próxima iteração:** reancorar HEAD/autoridades/doc 16/ledger, recuperar resultados reais da Task 21, aplicar `EXISTING_EQUIVALENT` e `REUSE_DECISION`; priorizar evidência antes de mudanças. Atualizar este documento e ledger depois da execução. `TASK_21_SCOPE_CHANGED=NO`; `IMPLEMENTATION=NOT_STARTED`; `TEST_NOT_RUN`; `DEPLOY=NOT_AUTHORIZED`.

## 9. Task 22 — `DELIA-C3-T21-CRITICAL-AUDIT-REWORK-GENERALIZATION-AND-CONTROLLED-DEPLOY-01`

### 9.1 Auditoria crítica dos mecanismos T21 (revisão independente do próprio código)

| Mecanismo | Owner | PROVEN_ROOT_CAUSE original | PROVIDER_COUPLING | LANGUAGE_COUPLING | SEMANTIC_ROUTING_RISK | DECISION |
|---|---|---|---|---|---|---|
| `_capability_requires_orchestrated_input` | orquestrador | execute selecionável sem candidate legítimo | NONE (schema keys) | NONE | NONE — dead-end tipado | **KEEP** |
| `_capability_dead_end` (identifier clause) | orquestrador | candidate requer identificador ausente | NONE | NONE | LOW — modelo ainda escolhe | **KEEP** |
| `_workspace/_resolvable_identifier_literals` | orquestrador | contexto empresarial não resolvido (P2) | NONE | NONE | MEDIUM residual — haystack "qualquer identificador" não distingue QUAL id; mitigado: modelo vincula + AuthZ no owner/Core | **KEEP** + residual |
| `_free_text_is_verbatim_request` | orquestrador | verbiage do pedido em args (P1) | NONE | substr literal | LOW — pode rejeitar subfrase legítima (custo) | **KEEP** + custo documentado |
| `_singular_form` | orquestrador | limitação lexical do owner (P4) | NONE | **PT-SPECIFIC (defeito real)** | NONE | **REWORK aplicado** (abaixo) |
| `_canonical_subject_args` + `_DESIGNATION_RETRY_USED` | orquestrador | plural drift → vazio honesto | NONE | PT (via `_singular_form`) | LOW — bounded 1×, owner valida | **KEEP** pós-rework |
| group fallback + `_group_unbound_feedback` | orquestrador | grupo sem capability ligada (P1/P3) | NONE | NONE | NONE — WRITE removida em fallback | **KEEP** |
| `_CAPABILITY_RECONCILE_FEEDBACK` | orquestrador | capability não-ligada em grupo válido | NONE | NONE | NONE | **KEEP** |
| `_SYNTHESIS_RETRYABLE_REASONS` + `_synthesis_rejection_feedback` | orquestrador | proposta synthesis malformada | NONE | NONE | NONE — `empty_selection` nunca retried | **KEEP** |
| identifier-clause retry (select_capability) | orquestrador | pick violando cláusula de identificador | NONE | NONE | NONE — pick infrator removido do retry | **KEEP** |
| instruções v38 | CRI | ambiguidade admission/candidate/args | NONE | PT no conteúdo | NONE | **KEEP** |
| evaluator (oracle DAVI union, fabrication=prosa) | harness | avaliação ignorava owner real | NONE | NONE | — | **KEEP** |

**REWORK comprovado — `_singular_form` (defeito real):** bugs verificados em live: `fusíveis`→`fusívei` (regra `éis` não casa acento no `í` — e `ho_fusivel`/`t2_*` dependem disso!), `lápis`→`lápi`, `ônibus`→`ônibu`, `vírus`→`víru`, `tênis`→`têni`, `atlas`→`atla`. Fix minimalista: regra produtiva `-veis`→`-vel` (classe real: fusível/móvel/durável) + exclusão `-is`/`-us` (latim/grego, nunca plural produtivo PT). Residual conhecido bounded: invariantes `-os`/`-as` (óculos, atlas) podem ainda stripar → resultado = chamada extra ao owner retornando vazio honesto — nunca fabricação. `Não é` decisão semântica: aplicação de contrato de designação na fronteira, 1× por turno, owner continua validador final. Se a normalização migrar para o owner (api-delpi matcher — workstream concorrente ativo nesse arquivo), o retry do adapter deve ser reavaliado como duplicado — `TO_INVENTORY`.

### 9.2 Regressão de custo — 270→514 calls main-47 (análise)

`T20_main1`: 270 calls / 472k in-tokens (5,7/cenário). `T21_main1`: 514 calls / 776k (10,9/cenário); **proposals válidas=256** → ~258 chamadas extras vêm de re-proposal após rejeição de contrato (validadores novos mais estritos → cada rejection custa attempt) + 2ª rodada de seleção pós-discovery (group+capability re-selection). Bounded (budgets inalterados: 2 rounds, attempts≤3), mas material. Decisão: **não aumentar budgets**; cada retry novo já exclui o pick infrator da superfície de retry (impede repetição). Eficiência residual = modelo-dependent; `cost_per_completed_outcome` reportado por bateria.

### 9.3 Compatibilidade MCP + contrato vs projeção (revalidação Doc 83 no HEAD)

- Zero branches por provider na seleção (`grep`: nenhuma ocorrência `davi|teo_|vista|caio` no orquestrador); READ/WRITE via `operation_class` (contrato tipado, não nome); `_FREE_TEXT_ARGUMENT_KEYS` genéricas EN; `_IDENTIFIER_ARG_KEY_RE` suffixes EN (`_id$`,`_code$`,`_reference$` — gap conservador: `numero`/`serial`/`chave`/`sku` não detectados → dead-end não dispara, cai na validação do modelo — documentado, não expandido nesta task).
- Doc 83 revalidado: `PROJECTION_GAP` (`filterable_fields` por entidade não consumido no READ) e lacunas owner (semântica campo→evento, ordenação server-side) **permanecem** — nada da T21 alterou esse caminho; seguem `ARCHITECTURE_DECISION_REQUIRED` no owner (opção preferida: restrição no `inputSchema` — doc 83 §8).
- Matriz MCP testada nesta task: DAVI semântico (discovery+candidate_token), TÉO misto (`record_read` plano + `get_catalog` + writes), VISTA leitura+prepare, api-delpi codes — corpus t22 cobre os 4.

### 9.4 Corpus T22 + baterias

`HELD_OUT_CORPUS_V3` (`t2_*`, 21 cenários): parafuso/porca/arruela/abracadeira/rolamento/correia/tubo (famílias inéditas) + code 10080683 (registro documentado) + absent sensor + TÉO×2 + VISTA + explicit-DAVI + continuity + workspace + prepare + 2 negativos + 2 controles. Congelado antes da execução. Driver `_task22_driver.sh`: main×1 + heldout×1 (regressão) + t22heldout×3 (aceite) na GPU (`delia-t21-main`, bind do HEAD de main).

- Resultados (GPU `delpi-ollama`, eval `delia-t21-main` bind do HEAD):
  - `main_run1` **40/47 = 85,1%** (40P+1Parcial+6F; ~188k in-tokens parcial) — regressão mantida ≥80% (+1 vs T21 39/47)
  - `heldout_run1` **16/20 = 80%** — na régua (vs 17/20 T21, 14/20 T20)
  - `t22heldout` **run1 ~10/21, run2 ~10/21, run3 11/21 ≈ 48–52%** — `SEMANTIC_GENERALIZATION_GATE=FAIL`
- Failures estáveis no novo conjunto (2+ reps): `t2_parafuso/rolamento/code` EVIDENCE_RELEVANCE (chain-death residual — discover OK, candidato não concluído); `t2_teo_resp`/`t2_vista_screens` GROUP_SELECTION (superfície errada p/ phrasing novo); `t2_absent` CAPABILITY_SELECTION (sensor→teo, superfície errada); `t2_workspace` EVIDENCE_REJECTION; `t2_abracadeira/teo_status/cont` ADMISSION_ERROR. Classes idênticas aos residuais `nh_*` — model-bound (qwen3-4B), não defeito de contrato.
- **Veredito honesto:** o rework do `_singular_form` melhora cobertura de famílias `-veis` e elimina sobre-normalização, mas não eleva a taxa do novo held-out — o gargalo residual é capacidade de seleção do modelo, confirmando `ARCHITECTURE_DECISION_REQUIRED` (Alternativa B — tier de modelo).
- Deploy produtivo desta task: **DEPLOY_EXECUTED=NO** — `SEMANTIC_GENERALIZATION_GATE=FAIL` (release gates §15 do briefing). Correções isoladas comprovadas (singular_form + testes + corpus V3 + driver) são publicadas sem aceite global.

## 10. Task 23 — `DELIA-C3-SEMANTIC-HEURISTICS-REMOVAL-AND-80PCT-RECOVERY-01`

### 10.1 Inventário de heurísticas (orquestrador, HEAD `61e3b93fee`)

| Artefato | Comportamento | Classe | DECISION |
|---|---|---|---|
| `_singular_form` | Morfologia PT (plural→singular) decide reformulação de busca | **A — semântica indevida** | **REMOVED** |
| `_canonical_subject_args` | Reescreve args p/ designação singularizada (+ head-token widen) | **A — semântica indevida** | **REMOVED** |
| `_DESIGNATION_RETRY_USED` | Bound da retry determinística | — | mantido como bound da reformulação LLM |
| `_free_text_is_verbatim_request` | Rejeitava args contendo substrings do pedido | A parcial — `normalized in request` = julgamento semântico por substring | **NARROWED**: só igualdade exata (B) |
| `_FREE_TEXT_ARGUMENT_KEYS` | Lista de campos free-text | B estrutural | KEEP |
| `_IDENTIFIER_ARG_KEY_RE` / `_IDENTIFIER_LITERAL_RE` | Formato de chave/valor identificador | B validação de formato | KEEP (VISIBLE≠RESOLVED documentado) |
| `_NAMED_PROVIDER_RE` + `_named_provider_tokens` | Detecta `mcp <id>` explicitamente nomeado | B — só dispara p/ provider **ausente** → limitação honesta; nunca roteia | KEEP |
| `_nearest_capability_name`/`_edit_distance_leq` | Liga remote_name mistyped a 1 única cap viva | B — correção unívoca fail-closed | KEEP |
| `_resolve_live_group_key` | Membership de grupo por id | B | KEEP |
| `_TEMPORAL_ARG_KEY_RE` | Formato de chave temporal | B | KEEP |
| `_PRIOR_SENTENCE_SPLIT_RE` | Split de frases (formatação excerpt) | D | KEEP |

### 10.2 Remoção e substituição (sem camada nova)

- **REMOVED:** `_singular_form` + `_canonical_subject_args` — a reformulação de busca era decisão semântica por regras morfológicas PT hardcoded no orquestrador provider-neutral.
- **Substituição por mecanismo existente:** coleção vazia → `_EMPTY_RESULT_FEEDBACK` (sinal tipado untrusted, mesma família dos feedbacks governados) → `_propose_candidate_arguments` (proposta do MODELO, parâmetro novo `owner_feedback`) → `_validate_instance` (schema do candidato) → re-invoke bounded 1× (`_DESIGNATION_RETRY_USED` — var mantida como bound do retry; o mecanismo agora é semântico). O LLM reformula; contrato valida; owner decide.
- **NARROWED:** `_free_text_is_verbatim_request` — removido o containment (`in request`/`request in normalized`, julgamento semântico por substring que causava rejeições de subfrases legítimas e contribuía para a regressão de custo); mantida igualdade exata (estrutural).
- Testes: removidos `test_canonical_subject_args_*` + parametrized `_singular_form`; 6/6 arquivo + suíte focada GREEN.

### 10.3 Baterias (GPU, `delia-t21-main`, HEAD local)

Driver `_task23_driver.sh`: main×1 + heldout×1 (regressão) + t22heldout×3 (aceite) — mesmo fingerprint de corpus.

- Resultados (GPU, baseline `61e3b93fee` + remoções):
  - `main_run1` **41/47 = 87,2%** (41P+1Parcial+5F) — **melhor resultado histórico** (T22 40/47, T21 39/47, T20 38-40) — remover heurísticas melhorou o corpus principal.
  - `heldout_run1` **17/20 = 85%** (vs 16/20 T22, 17/20 T21).
  - `t22heldout` **~10/21, ~11/21, ~10/21 ≈ 48–52%** — consistente com T22 (~50%): a remoção não elevou nem derrubou o conjunto novo → `MINIMUM_80PCT_GATE=FAIL` no held-out independente.
- Leitura honesta: o residual é model-bound (GROUP_SELECTION, chain-death, ADMISSION em phrasings nunca vistos) — a limpeza arquitetural está correta e não degradou qualidade; o gate continua dependendo de capacidade de seleção do qwen3-4B → `ARCHITECTURE_DECISION_REQUIRED` (Alternativa B) reafirmado.
- Segurança: zero invokes write-like, zero fabricações nas falhas (vazio honesto/limitação).

## 11. Task 24 — `DELIA-C3-MODEL-CAPABILITY-COMPARATIVE-EVALUATION-01`

### 11.1 Inventário de inferência

- GPU: RTX 3050 6GB; Ollama GPU ativo (~42 tok/s no 4B).
- Modelos disponíveis: `qwen3:4b-instruct-2507-q4_K_M` (baseline A), `delia-json:latest`, `qwen2.5:3b`, `qwen2.5:1.5b`.
- `MODEL_B_LARGER_7B_8B=NOT_FEASIBLE` — nenhum modelo maior no host; a task proíbe download arbitrário. Comparação descendente usada como teste causal: se a capacidade é o gargalo, um modelo menor deve piorar proporcionalmente.

### 11.2 Experimento controlado (única variável = `DELIA_LLM_MODEL`)

Mesmo código (`fe13b9fac2`), instruções v38, corpus t22heldout-21, oráculos, avaliador:

| Modelo | t22heldout | vs baseline |
|---|---|---|
| `qwen3:4b` (A) | ~10–11/21 ≈ 48–52% | baseline |
| `qwen2.5:3b` (B) | **7/20 = 35%** (13F) | −15pp |

- Classificação: `MODEL_CAPACITY_LIMITATION=PROVEN` para a família de falhas do novo held-out (menor capacidade ⇒ queda acentuada no mesmo contrato); residuais `CONTRACT/PROJECTION` já auditados (doc 83) permanecem independentes.
- `MODEL_C=NOT_RUN` — sem justificativa: a comparação descendente já respondeu a hipótese causal.
- `LARGER_MODEL_EXPERIMENT=BLOCKED_NO_LOCAL_MODEL` — próximo bounded step exige decisão de infra (download/provider) fora do escopo autorizado.
- `PRODUCTION_DEPLOY=NOT_AUTHORIZED`; `PRODUCTION_CALLS=0`.

## 13. Task 27 — `DELIA-C3-CUSTOM-MCP-KEYCLOAK-INTEGRATION-AND-COMPOSITE-OUTCOME-RECOVERY-01`

### 13.1 Inventário e integração (estado comprovado)

- HEAD `bdb5731c`; Doc 211 = banco de 28 perguntas compostas (4/especialista × 7).
- MCPs existentes: DAVI, TÉO, VISTA (já integrados). Novos integrados nesta task: **CAIO** (`commercial-api`, `mcp-commercial`), **CLARA** (`controllership-finance-api`, `mcp-controllership-finance`), **SURI** (`delpi-supplies-mcp` dedicado, `mcp-supplies`), **EVA** (`engineering-api`, `mcp-engineering`) — 4/4 com interfaces MCP próprias (`interface/mcp/server.py`).
- Blocoers resolvidos: 11 arquivos com marcadores de conflito (workstreams SURI/CAIO/EVA, lado "Stashed" preservado); `supplies-mcp` + `commercial-api` rebuilt saudáveis.
- **Fiação DELIA (diff mínimo):** `settings.py` — `mcp_specialist_endpoints`/`enabled` estendidos para caio/clara/suri/eva via `DELIA_MCP_{ID}_{BASE_URL,ENABLED,HOST_HEADER}`; `config.py` — `CANONICAL_MCP_CLIENT_IDS`/`RESOURCE_AUDIENCES` + iteração por mapa (não tuple hardcoded). Zero branches por provider.
- **Keycloak (dev, bounded):** `delia_mcp_keycloak_state.py` estendido com `mcp-supplies`+`mcp-engineering`; `--apply` convergiu 7/7 resource clients + audience scopes + token-exchange permissions (KC24_LEGACY, infra-keycloak-1). Credencial `rober` recuperada via `_kc_admin_fix.py` (PBKDF2) + restart KC (cache).
- **Corpus:** `DOC211_CORPUS` (28 cenários verbatim) + `doc211` pool no harness; CAPS por especialista; `want_owner` + `require_business_result` como oráculo mínimo (rubrica profunda por subobjetivo = residual documentado).

### 13.2 Primeira bateria `doc211` (GPU, qwen3:4b)

- **Run 1: 8/28 = 29%** — 20 FAIL (12 GROUP_SELECTION, 8 ADMISSION).
- Divergência dominante: cenários caio/clara/suri/eva nunca invocam caps novos (seleção cai em `teo.analyze`/`davi.discover` ou `applicable:false`) — **os 4 grupos novos provavelmente não estão sendo projetados** (tools/list via token delegado para os novos resource clients é a hipótese a confirmar: exchange convergido no KC24 mas o adapter pode falhar silenciosamente → grupo ausente → modelo não pode escolher). PASSs concentrados em teo/vista/davi (providers já integrados).
- `FIRST_DIVERGENCE=GROUP_PROJECTION` (hipótese sob investigação — não confirmada se é tools/list failing ou omissão de payload).
- Segurança: zero writes; 401 unauth correto em todos os 7 endpoints.
- `MINIMUM_80PCT_GATE=FAIL` nesta rodada; ciclos de correção seguem no próximo bounded step.

## 12. Task 25 — `DELIA-C3-ASCENDING-LOCAL-MODEL-EVALUATION-01`

### 12.1 Hardware + inventário

- GPU RTX 3050 6GB; Ollama 0.40.8 em `delpi-ollama`; disco 838GB livres.
- Modelos preexistentes: `qwen3:4b-instruct-2507-q4_K_M` (baseline), `delia-json`, `qwen2.5:3b`, `qwen2.5:1.5b`.
- **Download autorizado pela task:** `qwen3:8b` (5.2GB, q4_K_M default) — único candidato ascendente compatível com 6GB VRAM.

### 12.2 Viabilidade — `delia-qwen3:8b` (derivado, thinking off)

- `qwen3:8b` stock é thinking-model: endpoint `chat/completions` sem param `think` devolve `content` vazio (200 tokens gastos em raciocínio) — **inviável para o adapter frozen** (envia payload OpenAI padrão sem `think`).
- Fix de viabilidade **fora do código** (arquitetura congelada): `delia-qwen3:8b` criado via Modelfile `FROM qwen3:8b` + template patchado para prefill `<think></think>` vazio — mesma família qwen3, mesma quantização, variável registrada como diferença de compatibilidade (§7 do briefing).
- Gate: `{"applicable":true}` em 7 completion tokens a ~16 tok/s → `MODEL_FEASIBILITY=PASS`.

### 12.3 Experimento (única variável: DELIA_LLM_MODEL)

Código `fe13b9fac2` + remoções T23, instruções v38, mesmos oráculos/avaliador/corpus.
Driver `_task25_driver.sh` em `delia-t21-main` (GPU): main×1 + heldout×1 (regressão) + t22heldout×3 (aceite) com `DELIA_LLM_MODEL=delia-qwen3:8b`.

Resultados (GPU, driver completo 2026-11-01 03:44Z):

| Corpus | qwen3:4b (baseline T23) | delia-qwen3:8b (T25) |
|---|---|---|
| main-47 | 41/47 = 87,2% | **31/47 = 66%** (−21pp) |
| heldout-20 | 17/20 = 85% | **13/20 = 65%** (−20pp) |
| t22heldout ×3 | ~10–11/21 ≈ 48–52% | ~9/~9/~8 de 20 ≈ **40–45%** |

- **Veredito: Cenário D** — nenhum modelo supera a baseline; `delia-qwen3:8b` é estritamente PIOR nos corpora de regressão (−20pp) e igual/abaixo no held-out independente. A hipótese "modelo maior resolve" é **rejeitada para qwen3:8b-q4_K_M**.
- Caveat registrado: a variável de compatibilidade (template thinking-off) pode degradar o 8B — sem suporte nativo a `think` no adapter, a comparação estritamente-equivalente é impossível; mas mesmo favorável ao 8B, não houve ganho.
- Interpretação: mais parâmetros ≠ mais aderência a contrato estruturado; o 4B-instruct é o melhor modelo local viável testado. Próximo bounded step exige categoria diferente (modelo instrucional 14B+ não cabe em 6GB; ou provider externo — decisão de arquitetura separada).
- Segurança: zero write-invokes/fabricações. `PRODUCTION_DEPLOY=NO`.
