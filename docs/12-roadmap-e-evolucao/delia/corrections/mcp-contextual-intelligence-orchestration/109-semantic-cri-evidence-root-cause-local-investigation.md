# 109 — Investigação causal local: semântica, evidência, CRI e business outcome

`DELIA-C3-SEMANTIC-CRI-EVIDENCE-ROOT-CAUSE-LOCAL-INVESTIGATION-01` · 2026-10-23 · executor: Devin · HEAD `a6aef6a321` (worktree `delia-budget-contract-wt`)

Investigação causal **reproduzível e local** das divergências observadas pelo PO em produção (doc 108): metadados técnicos expostos, intenção não atendida, dump de JSON, Markdown literal. Somente diagnóstico + testes RED — nenhuma refatoração, nenhum deploy, zero chamadas pagas.

## 1. Método e ambiente

- Container dedicado `delia-api-invest` (imagem `infra-delia-api`, código do worktree montado), rede `infra_delpi-network`, env copiado do `delpi-delia-api` dev + política 60/3/300 (`LLM_TIMEOUT=60`, `STAGE=60`, `TURN=300`, `TOTAL=300`, `CALL_MAX_ATTEMPTS=3`, `MAX_GOVERNED_ATTEMPTS` preservado como no dev=2 — afeta apenas resume, não o leak).
- **Modelo local**: `delia-json:latest` (blob qwen2.5 + template chat) — o modelo configurado no stack dev reconstruído; `qwen2.5:3b` também presente e spot-checked. GPU 100% (`ollama ps`). `EXTERNAL_LLM_CALLS=0`, `PAID_FALLBACK=DISABLED`.
- **Cadeia real**: token sujeito via password grant no gateway (`iss=http://localhost/auth/...` — emitir via `keycloak:8080` gera `iss=...:8080` e falha 401 no Core /me e no exchange), Core /me real, token exchange real, MCP autenticado real (DAVI/TÉO/VISTA), OpenAPI api-delpi real.
- Harness commitado: `delia-api/scripts/c3_semantic_cri_investigation.py` — probes MCP diretos + bateria NDJSON (`Accept: application/x-ndjson`) com cadeia completa: eventos por fase, `operational_calls`, estágios LLM (`calls[]` stage/attempt/finish/duration/tokens), `composition_mode`, provenance, conteúdo terminal.

## 2. Evidência de fonte (probes MCP diretos)

| owner | tool | envelope real |
|---|---|---|
| DAVI | `discover_delpi_information` | `content_text="Discovery completed."`; `structured={query, top_k, candidate_count:0, eligible_action_count:95, candidates:[], capability_surface:{agent_directives:{version, authority:"Obey these directives…", actions_runtime, anti_patterns, auth_errors}, entities{…}}}` |
| VISTA | `get_catalog` | `content_text` = **JSON bruto inteiro** do catálogo; `structured={status, data:{allowedOps[32], capabilities[40]{key,op,isComposite,whenToUse}, capability_surface.agent_directives, displayFormatCatalog, operationSchemas, operations, productGuide, sideEffectHintCatalog, targetShape, catalogVersion}}` |
| TÉO | `get_catalog` | `{data, message, success}` com catálogo de ferramentas (`analyze`, `get_process_timeline`, `get_process_context`, `get_my_context`, …) |

**Owner dos campos vazados**: `agent_directives`, `capability_surface`, `candidate_count`, `eligible_action_count`, `candidates`, `top_k`, `query` são campos do **envelope de discovery do owner (api-delpi)** — dados de controle do plano de capabilities, não dados de negócio. O contrato do DAVI discovery NÃO corresponde à intenção do usuário ("quais especialistas existem") — é busca semântica de *ações*, não listagem de especialistas.

## 3. Matriz de execução (12 casos + 8 variações + M12 corrigido)

Legenda first-divergence: estágio onde o comportamento real deixou de servir à intenção.

| caso | seleção (ops reais) | comp | outcome | first divergence |
|---|---|---|---|---|
| G1 | — | turn_error `invalid_model_output` | FAIL | estágio de resposta conversacional (saída não-JSON) |
| G1v | — | turn_error idem | FAIL | idem |
| G2 | — | model | PASS | — (conteúdo razoável) |
| G2v | — | model | PASS | — |
| G3 | — | turn_error `invalid_model_output` | FAIL | estágio de resposta (saída não-JSON; 3 tentativas) |
| G3v | — | model | PASS_WITH_RESIDUAL | — (resposta curta mas correta) |
| D4 | `davi.discover_delpi_information` | deterministic | FAIL (intenção) | interpretação de intenção: pergunta meta ("quais especialistas") tratada como busca de ações → `CAPABILITY_NOT_MATCHED`; resposta honesta mas não lista especialistas; `native_assessment=corroboration_requested` espúrio |
| D4v | — (clarification) | deterministic | FAIL | seleção/resolução → ask-back que ecoa a pergunta |
| D5 | `davi.discover_delpi_information` | **cri** | **FAIL + LEAK** | **projeção de evidência → contract_facts** (detalhe §4) |
| D5v | — | model | FAIL | modelo alucinou tipos de gráfico NON_GROUNDED (nunca consultou fonte) |
| D6 | — (nenhuma invocação) | deterministic | FAIL | capability `teo.get_process_timeline` exige identificador ausente → clarify ask-back; `clarification_wording` falhou 3× (saída não-JSON) |
| D6v | — | deterministic | FAIL | idem |
| D7 | — | deterministic | FAIL | `teo.get_process_context` idem → ask-back/eco |
| D7v | — | deterministic | FAIL | idem |
| D8 | `delpi.search_products` (openapi) | cri | **PASS** | — (descrição correta, GROUNDED/OBSERVATION) |
| D8v | `delpi.get_product_summary` | cri | PASS | — |
| M9 | — | deterministic | FAIL | pergunta conceitual → ask-back/eco em vez de responder |
| M10 | `davi.discover_delpi_information` | model | **FAIL** | modelo afirmou "DAVI não está disponível" **enquanto o op log prova invocação** — alegação falsa |
| M11 | — | turn_error `invalid_model_output` | FAIL | saída não-JSON |
| M12 | `vista.get_catalog` | deterministic | FAIL | resposta é miss-render do catálogo VISTA (lista tools de playlist); **nenhuma comparação** com a explicação inicial |

`CASES_EXECUTED=20` (12 obrigatórios + 8 variações; M9–M12 numa única conversa com `context` preservado — 400 numa primeira tentativa de M12 causado por o harness reenviar `DELIA_RESULT` de turno falho sem `epistemic_class`; contrato correto, artefato do harness, re-executado com contexto válido → 200).

### 3.1 Comparação com screenshots do PO (produção, Kimi)

| PO (prod) | local (qwen/delia-json) | leitura |
|---|---|---|
| D4: `agent_directives`, `candidate_count=0`, `eligible=95`, `candidates=[]` expostos | D5 reproduziu **o mesmo leak**: CRI `contract_facts` renderizou `capability_surface:{agent_directives…}` + contadores verbatim | mesma causa (RC1); a pergunta-trilho varia por nondeterminismo do modelo |
| D5: dump JSON playlist/mutações/capability surface | VISTA `capabilities[40]` promovido a `records` → verdict `answered` (prova determinística §5) | mesma causa (RC2) |
| G2/G3: markdown literal `**` | modelo local não emitiu `**`; mecanismo provado: bloco `text` sem `format` renderiza literal; só projeção tipada recebe `markdown_safe` | RC7 (INCONCLUSIVE localmente; mecanismo PROVEN) |

## 4. Causa-raiz PROVEN — RC1: contract_facts apresenta envelope de controle ao usuário

Cadeia provada por logs + teste determinístico:

```text
discover_delpi_information → candidates=[]
→ _invoke_selected: DISCOVERY terminal → _render_zero_candidate_discovery
   (texto honesto "busca não encontrou ação" — CORRETO)
→ contract_facts=_contract_fact_rows(outcome)  <<< DIVERGÊNCIA
   _sanitize_renderable NÃO remove chaves de controle
   _compact_evidence só descarta "example"/"examples"
   → linhas: "capability_surface: {\"agent_directives\": ...}", "query: ...",
     "top_k: 5", "candidate_count: 0", "eligible_action_count: 95", "candidates: []"
→ _outcome_facts: sem records → contract_facts → verdict CONTRACT_FACTS
→ CRI compose: "A fonte publica estas informações sobre o que ela oferece:"
   + rows verbatim → substitui o texto honesto (cri.content tem prioridade)
```

`cri_response decision=composed presented=6` e `outcome_assessment decision=contract_facts` no log (correlation `11a89d4f…`).

**Gap de contrato**: `_CONTROL_PLANE_KEYS = {agentdirectives, capabilitysurface}` É aplicado em `_format_structured` e em `_synthesis_records` — mas **NÃO** em `_contract_fact_rows`/`_compact_evidence`, e chaves de transporte do discovery (`candidate_count`, `candidates`, `eligible_action_count`, `top_k`, `query`, `status`) não têm exclusão em nenhuma política. A intenção original do digest era `capability_surface.entities` (vocabulário) — o dump breadth-first de seções top-level incluiu o envelope inteiro.

**Impacto de segurança**: `agent_directives` é texto de instrução declarado pelo owner ("Obey these directives…") — untrusted data renderizado como fato ao usuário. Nenhuma injeção foi executada (contract_facts só alimentam o compositor determinístico, nunca um estágio de modelo) — classificado PROVEN como *exposição*, não execução. Conteúdo malicioso embutido nesses campos seria exibido verbatim.

## 5. Causa-raiz PROVEN — RC2: catálogo de capabilities promovido a evidência de negócio

`_synthesis_records`/`_resolver_entities` promovem a lista `capabilities[]` do envelope VISTA (descritores `key/op/whenToUse/requiresPlaylist`) a business records → `has_business_evidence=True` → verdict `answered` → CRI/render apresenta descritores de mutação/operacao como se fossem dados DELPI (a forma do dump do PO em D5). Prova determinística: `_outcome_facts` sobre o envelope real retorna `records=1`, `verdict=answered`. A coleção é vocabulário de capability-surface, não evidência de negócio — mesma lacuna de distinção do RC1, na borda de extração de records.

**RC1+RC2 = causa compartilhada**: a borda de projeção (`_synthesis_records`/`_resolver_entities`/`_contract_fact_rows`/`_compact_evidence`) não distingue canonicamente *vocabulário de capability/transporte* de *evidência de negócio*; `_CONTROL_PLANE_KEYS` existe mas é aplicado de forma inconsistente entre as projeções irmãs.

## 6. Demais causas-raiz

| id | status | causa | owner |
|---|---|---|---|
| RC3 | PROVEN (escopo local) | aderência a saída estruturada: `delia-json`/`qwen2.5:3b` ignoram a diretriz "JSON only" em turnos conversacionais → `invalid_model_output` → turn_error (G1/G1v/G3/M11) e retries queimados (`clarification_wording` 3×, `arguments` 2×, `candidate_arguments` 2×) | modelo/saída estruturada — limitação do modelo local; não presumir igual em Kimi |
| RC4 | TO_INVENTORY (gap de contrato) | nenhuma superfície semântica responde "quais especialistas/capacidades a DÉLIA tem" — pergunta meta roteada a busca de ações de um especialista → miss honesto | capability contract/catálogo |
| RC5 | PROVEN | TÉO só expõe tools entity-scoped (`get_process_timeline`, `get_process_context`) que exigem identificador; "último/primeiro processo" não tem READ de listagem/ordenação → clarify ask-back honesto mas intent não atendida | capability contract/catálogo + arguments |
| RC6 | PROVEN | desonestidade de modelo: M10 afirmou "DAVI não disponível" com `discover_delpi_information` invocado no mesmo turno (`operational_calls` prova); marcado NON_GROUNDED corretamente | modelo (instrução não impõe checagem contra fatos do turno) |
| RC7 | INCONCLUSIVE (mecanismo PROVEN) | bloco `text` sem `format` renderiza prosa do modelo literalmente; `markdown_safe` é reservado à projeção tipada — `**` de Kimi em prod aparece literal por design | apresentação/modelo |
| RC8 | PROVEN | testes existentes validavam envelope/bounds (ex.: `test_contract_facts_instruction_shaped_content_stays_bounded_data` aceita texto de injeção contanto que bounded) — nunca a ausência de controle-plane nem utilidade do conteúdo | observabilidade/testes |

## 7. Checklist §10 resumido por caso

| caso | expected → actual | selected | source_relevance | grounding | first_divergence | outcome |
|---|---|---|---|---|---|---|
| G1 | saudação natural → turn_error | — | n/a | — | resposta conversacional (não-JSON) | FAIL/RC3 |
| G2 | explicar SIPOC → explicou | — | n/a | NON_GROUNDED honesto | — | PASS |
| G3 | diferenças c/ exemplos → turn_error | — | n/a | — | resposta (não-JSON) | FAIL/RC3 |
| D4 | lista de especialistas → miss de busca + tools | davi/discover | envelope discovery ≠ intent | GROUNDED | interpretação de intent (RC4) | FAIL |
| D5 | formatos de visualização → **leak agent_directives** | davi/discover (dono errado p/ painéis) | envelope control-plane | GROUNDED | projeção de evidência (RC1) | FAIL |
| D6 | último processo → ask-back | teo/get_process_timeline | sem invocação | NON_GROUNDED | seleção tool entity-scoped (RC5) | FAIL |
| D7 | primeiro processo+desc → ask-back/eco | teo/get_process_context | sem invocação | NON_GROUNDED | idem | FAIL |
| D8 | descrição material → descrição real | delpi/search_products | registro correto | GROUNDED | — | PASS |
| M9 | exemplos conceituais → ask-back/eco | — | n/a | NON_GROUNDED | decisão semântica (RC3-adj.) | FAIL |
| M10 | verificar via DAVI → alegou indisponibilidade | davi/discover | invocou de fato | NON_GROUNDED | honestidade do modelo (RC6) | FAIL |
| M11 | aprofundar consulta → turn_error | — | n/a | — | não-JSON (RC3) | FAIL |
| M12 | comparação → miss render VISTA | vista/get_catalog | catálogo ≠ comparação | NON_GROUNDED | continuidade/intent (RC4-adj.) | FAIL |

`USER_OUTCOME_PASS=3` (G2, G2v, D8, D8v → 4 contando D8v) · `USER_OUTCOME_FAIL≈15` · `INCONCLUSIVE=0` (nenhum caso ficou sem decisão; G3v=M9-adjacent residual counted as PASS_WITH_RESIDUAL separadamente).

## 8. Testes RED adicionados (6)

`delia-api/tests/test_c3_contextual_discovery.py`, Parte 4 — todos **RED** sobre o código atual, mirando o owner canônico (não o sintoma):

1. `test_contract_facts_exclude_control_plane_keys_real_envelope` — envelope DAVI real: `agent_directives`/`actions_runtime`/`anti_patterns`/`auth_errors` ausentes; entidades preservadas (sibling positivo).
2. `test_contract_facts_exclude_transport_counters` — `candidate_count`/`candidates`/`eligible_action_count`/`top_k`/`query`/`status` nunca viram linha.
3. `test_contract_facts_exclude_control_plane_nested_in_wrapper` — controle-plane aninhado em wrapper é removido em qualquer profundidade.
4. `test_contract_facts_malicious_directive_text_never_user_facing` — texto de injeção em `agent_directives` não é renderizado (segurança).
5. `test_capability_catalog_is_not_business_evidence` — coleções `capabilities/allowedOps/operations` não viram records nem verdict `answered` (RC2).
6. `test_cri_contract_facts_content_never_contains_directives` — gate end-to-end do conteúdo CRI.

Resultado: `6 failed, 16 passed` — os 16 preexistentes verdes (nenhuma regressão induzida; os testes novos falham exatamente onde o leak vive).

## 9. Correções mínimas recomendadas (bounded package)

P1 — **borda de projeção canônica (RC1+RC2, um único fix arquitetural)**:
- `_contract_fact_rows`/`_compact_evidence`: aplicar exclusão `_CONTROL_PLANE_KEYS` recursivamente + conjunto provider-neutral de chaves de transporte do envelope de discovery (`candidate*`, `eligible_*`, `top_k`, `query`, `status/success/message` quando envelope); preservar `entities.*`.
- `_synthesis_records`/`_resolver_entities`: coleções sob chaves de vocabulário de capability (`capabilities`, `allowedOps`, `operations`, `operationSchemas`, `productGuide`, `sideEffectHintCatalog`, `targetShape`, `displayFormatCatalog`, `entitySchemas` — chaves canônicas, provider-neutral) não são elegíveis a business records.
- Owner: `capability_provision/orchestration.py` (projeção); consumidores: CRI, síntese, render determinístico. Sem branches por especialista.

P2 — **avaliação/gate**: evals de inteligência devem incluir asserção de conteúdo útil (ausência de controle-plane, presença de resposta) além de envelope — RC8.

P3 — **decisão de produto/arquitetura requerida** (não implementar neste pacote):
- RC4: superfície honesta para perguntas meta ("o que você pode fazer / quais especialistas") — resposta determinística da superfície viva de grupos, não busca de ação.
- RC5: contrato owner para listagem ordinal ("último/primeiro") ou capability de exploração — gap do owner TÉO, não prompt.
- RC7: política para markdown em prosa de modelo (strip bounded ou render decisivo) — decisão de apresentação.
- RC3: aderência JSON do modelo local — candidatos: `response_format`/grammar no adapter (decisão de contrato de provider) ou validação-com-retry já existente (preserva fail-closed). Não confundir com qualidade semântica de Kimi.

Não recomendado: nenhuma branch por especialista, lista de palavras-chave, regex de intent, ou formatter VISTA/DAVI-específico.

## 10. Limitações honestas

- Modelo local `delia-json`/`qwen2.5:3b` ≠ Kimi produção: falhas de seleção semântica e saída não-JSON são **não transferíveis** sem re-execução no modelo alvo; porém RC1/RC2 são falhas determinísticas de projeção — independentes do modelo (a seleção chegar a esses envelopes basta).
- Produção não foi consultada (zero chamadas pagas); screenshots do PO servem como referência de forma.
- Stack dev tem dados distintos de prod (ex.: `candidates=[]` local; prod pode retornar candidatos para a mesma pergunta — o encadeamento candidate→execute fica `INCONCLUSIVE` para prod).
- `qwen2.5:3b` spot-check no estágio conversacional reproduziu a mesma falha não-JSON do `delia-json`.
- Cobertura §9: ausência de candidatos ✓(live), catálogo grande ✓(VISTA real), JSON com metadados ✓(live), instruções maliciosas ✓(RED determinístico), sem dados relevantes ✓(D4/D6/D7), falha de autorização ✓(401 manual), timeout de fonte ✓(suite existente de retries), saída estruturada inválida ✓(live), continuidade multiturno ✓(M9–M12), mudança de especialista ✓(D8↔D8v, M10 DAVI↔M12 VISTA), intenções parecidas distintas ✓(variações), conceitual sem fonte ✓(G2/G3/M9).

## 11. Veredicto

`EXECUTOR_VERDICT=ROOT_CAUSES_PROVEN` — RC1 e RC2 (projeção de evidência/controle-plane) provados live + deterministicamente; RC5/RC6/RC8 provados; RC3 provado no escopo do modelo local; RC4 inventariado como gap de contrato; RC7 mecanismo provado, manifestação prod-only. O leak de `agent_directives` NÃO é do CRI em si — é da projeção que alimenta o CRI; o CRI compõe fielmente o que recebe.

**NEXT_COORDINATION_DECISION**: revisar RC1+RC2 (fix canônico na borda de projeção — P1) → autorizar pacote bounded de implementação com os 6 testes RED como critério de verde; decisões P3 separadas (RC4/RC5/RC7 produto; RC3 provider-contrato).
