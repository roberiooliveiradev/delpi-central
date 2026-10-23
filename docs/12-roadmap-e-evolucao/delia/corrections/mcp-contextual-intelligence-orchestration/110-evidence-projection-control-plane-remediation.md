# 110 — Remediação bounded RC1+RC2: fronteira canônica de projeção de evidência

`DELIA-C3-EVIDENCE-PROJECTION-CONTROL-PLANE-REMEDIATION-01` · 2026-10-23 · executor: Devin · HEAD `691ba48864` (worktree `delia-budget-contract-wt`)

Implementação do pacote P1 autorizado pelo parecer de coordenação no doc 109 (`IMPLEMENTATION_SCOPE_AUTHORIZED`): filtros estruturais recursivos de campos control-plane/transport **no contexto correto**, sem filtrar campos de negócio homônimos; promoção de records somente para evidência de negócio válida. `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND` — ajuste único na fronteira de projeção existente em `capability_provision/orchestration.py`. Nenhum formatter por especialista, nenhum keyword de pergunta, nenhum planner novo, nenhuma alteração de produção.

## 1. Causa-raiz corrigida (recapitulação doc 109)

- **RC1**: `_contract_fact_rows`/`_compact_evidence` projetavam todo o envelope de discovery como "fatos de contrato" — `capability_surface.agent_directives` (instrução untrusted do owner), contadores de transporte (`candidate_count`, `eligible_action_count`, `top_k`, `candidates`, `query`) e catálogos de operações vazavam para a composição CRI e para o usuário (leak do doc 108 reproduzido em D5).
- **RC2**: `_resolver_entities`/`_synthesis_records` promoviam listas de descritores de capabilities (`capabilities`, `allowedOps`, catálogos de tools) a business records → verdict `answered` → dump de operações internas como se fossem dados empresariais (leak de D5 do PO).

## 2. A correção (owner canônico, context-aware)

`delia-api/app/application/capability_provision/orchestration.py` — três conjuntos canônicos + dois predicados, todos provider-neutral:

| Peça | Semântica | Onde atua |
|---|---|---|
| `_CAPABILITY_VOCABULARY_KEYS` | coleções de vocabulário de catálogo de capabilities (`capabilities`, `allowedops`, `operationschemas`, `productguide`, `sideeffecthintcatalog`, `targetshape`, `displayformatcatalog`, `catalogversion`, …) — apenas nomes inequívocos | exclusão por chave em `_resolver_entities` (scan), `_synthesis_records` (containers) e linhas do digest |
| `_DISCOVERY_ENVELOPE_KEYS` | campos de transporte/execução no **nível do envelope de discovery** (`query`, `topk`, `candidatecount`, `eligibleactioncount`, `candidates`, `status`, `success`, `message`, `operations`, `tools`) | apenas linhas do digest de contract facts — campos homônimos dentro de schemas/registros preservados |
| `_CAPABILITY_DESCRIPTOR_STRONG/WEAK_KEYS` | assinatura estrutural de descritor de capability (`operationid`, `whentouse`, `inputschema`, `requiresplaylist`, `sideeffect`, `toolname` fortes; `op`, `operation`, `capability` fracos) | `_is_capability_descriptor` — filtro por forma, não por posição |
| `_is_capability_descriptor` | descritor = campo forte + (fraco ou mapeamento esparso ≤4 chaves), ou ≥2 fracos — registro de negócio denso com `operationId`/`op` homônimos **permanece** business record | `_resolver_entities._mappings` |
| `_without_control_plane` | remove `agent_directives`/`capability_surface` recursivamente (qualquer profundidade) | schemas de entidades e payload compactado do digest |
| texto→JSON | `content_text` que é um objeto JSON serializado segue o caminho estruturado — mesmas exclusões em vez de dump por linhas | `_contract_fact_rows` |

Invariante preservada: campos de negócio homônimos (`status`, `operations`, `op`, `operationId`) dentro de registros/schemas de entidade **não** são removidos — testado explicitamente (`test_entity_schema_homonymous_fields_preserved`, `test_business_record_with_operation_homonym_fields_preserved`).

## 3. Baseline RED → GREEN

- **Antes**: `6 failed, 16 passed` em `test_c3_contextual_discovery.py` (os 6 testes RED do doc 109 falhando no código vigente).
- **Depois**: `30 passed` — os 6 RED verdes, 8 novos testes positivos/irmãos (records legítimos, homônimos, catálogo grande, texto-JSON, CRI sem dump, transporte-só ⇒ insuficiência honesta), 1 teste legado atualizado para o contrato de segurança autorizado (instrução nunca é renderizada — `envelope_only` honesto em vez de row bounded com o texto da injeção).
- **Regressão backend completa**: `pytest tests/` — suíte inteira verde (0 falhas) no container com o worktree montado.

## 4. Avaliação local Ollama GPU (re-execução da bateria doc 109)

Container de investigação `delia-api-invest` com o código corrigido, cadeia real (Keycloak→Core→orquestração→MCP→CRI→NDJSON), modelo `delia-json`/`qwen2.5:3b` 100% GPU, `EXTERNAL_LLM_CALLS=0`. 20 turnos executados; scan de todo o output (content+provenance+observability): **zero ocorrências** de `agent_directives`, `candidate_count`, `eligible_action_count`, `capability_surface`, `Obey these directives`, `top_k`, `allowedOps`, `upsert_data_source`, `whenToUse`, `operationSchemas`, `productGuide`, `sideEffectHint`.

| caso | doc 109 (antes) | agora |
|---|---|---|
| D4 | miss honesto | igual — `turn_result`, miss de busca atribuído à fonte (95 capacidades declaradas), sem metadados |
| D4v | ask-back/eco | `turn_result` CRI contract_facts limpo: `entities.playlist: {id, kind...}` — vocabulário do owner sem directives |
| **D5** | **CRI renderizou `agent_directives`+contadores verbatim (leak)** | **honest insufficiency**: "a busca não retornou correspondência e o contrato do owner não enumerou o catálogo de ações" — zero dump |
| D5v | alucinação de gráficos non-grounded | contract_facts limpo com entities da playlist |
| D6/D6v/D7v | clarification | idem (RC5 gap de contrato TÉO — fora de escopo) |
| D7 | clarification | resposta honesta de fonte indisponível |
| **D8** | resposta correta | **regressão OK** — descrição real do material 10080043 |
| D8v | resposta correta | clarification (variação semântica do modelo local — RC3, fora de escopo) |
| G1/G3 | `invalid_model_output` | idem (RC3 qualidade do modelo local — fora de escopo) |
| M9–M12 | M10 desonestidade/erro, M11 erro | M10 turn_error (modelo), M11/M12 = artefato do harness (replay de contexto de turno falho → 400 inadmissível, contrato correto) |

Aceite da task atendido: **nenhum dado de controle vira evidência de negócio** e a DÉLIA encerra honestamente quando o contrato não oferece dados suficientes (D5 = insuficiência honesta atribuída; D4v/D5v = vocabulário de contrato limpo atribuído à fonte).

## 5. Segurança

- `agent_directives`/instruções owner não aparecem mais em contract_facts, conteúdo CRI ou resposta determinística — prova determinística + live scan (§4).
- Conteúdo malicioso em campos control-plane nunca chega a estágio de modelo (contract_facts alimentam apenas o compositor determinístico) e agora nem a projeção user-facing.
- Segredos/tokens: pipeline `_sanitize_renderable`/`_redact_text` inalterado; nenhum header/authorization em saídas.
- `agent_directives` e metadados MCP nunca são autoridade — invariante inalterado.

## 6. Contratos preservados

- CRI existente intocado (`conversational_response.py` sem alteração).
- Seleção semântica LLM, planner, contratos MCP/Domain, governança, READ!=PREPARE!=ACT inalterados.
- Regime produtivo 60/3/300 inalterado; zero deploy; zero chamadas pagas.
- Projeção de evidência para o **modelo** (`_compact_evidence`, `_evidence_rows`, argument stage) intencionalmente não filtrada — o modelo precisa do vocabulário completo; a filtragem é só da fronteira user-facing.

## 7. Resíduos honestos

- RC3 (aderência JSON do modelo local 3B) persiste: G1/G3/M10 `invalid_model_output` — fora de escopo, não reivindicado.
- RC4/RC5 (superfície meta "quais especialistas", contrato ordinal TÉO) permanecem gaps de contrato — D6/D7 seguem em clarification honesto, sem invenção de capability.
- M11/M12 não concluídos por artefato do harness (replay de `DELIA_RESULT` de turno falho sem `epistemic_class` → 400 correto) — mesma limitação do doc 109.
- Resolver interno: `candidates` de discovery filtrados como descritores também para preenchimento de argumentos — semanticamente correto (tokens de capability nunca são inputs de negócio), coberto pela suíte completa verde.
- Modelo local ≠ Kimi produção: melhorias de leak são determinísticas (independentes do modelo); resultados semânticos finais não são transferíveis.

## 8. Arquivos alterados

- `delia-api/app/application/capability_provision/orchestration.py` (+151/−15) — a correção.
- `delia-api/tests/test_c3_contextual_discovery.py` (+207/−15) — 8 novos positivos + 1 legado alinhado ao contrato de segurança.
- `docs/.../110-*.md`, README, ledger §6.392 — documentação.

## 9. Rollback

`git revert <commit>` — alteração contida em um módulo + testes; zero migrations, zero config, zero deploy. Imagens/runtime de produção não tocadas.

## 10. Veredicto

`EXECUTOR_VERDICT=P1_REMEDIATED_READY_FOR_COORDINATION_REVIEW` — RC1 e RC2 corrigidos na fronteira canônica com prova determinística (6 RED → green + 8 positivos) e live Ollama (zero leak em 20 turnos, honest insufficiency onde o contrato não sustenta resposta). RC3–RC7 permanecem itens separados conforme autorização.
