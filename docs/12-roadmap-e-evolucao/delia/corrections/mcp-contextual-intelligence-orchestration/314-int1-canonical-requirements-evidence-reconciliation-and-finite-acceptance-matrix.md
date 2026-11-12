# 314 — INT-1 | Requisitos canônicos, reconciliação de evidências e matriz finita de aceitação

**Data:** 2026-11-12  
**Tipo:** REVIEW + CORREÇÃO BOUNDED (defeito comprovado)  
**TASK_ID:** DELIA-C3-T2-INT1-REQUIREMENTS-EVIDENCE-MATRIX-AND-FINITE-ACCEPTANCE-DECISION-01  
**BASE_HEAD:** `d0ab08a8ea76f02b4efc3111ad7a1673352decf3`  
**AUTORIDADE:** Documentos 16/293/313, execution ledger, residual register e decisões congeladas. Este documento não autoaprova a INT-1; entrega recomendação fundamentada para decisão independente de coordenação.

## 1. Reancoragem

```text
HEAD=d0ab08a8ea76f02b4efc3111ad7a1673352decf3 (no início da revisão)
branch=main · worktree com WIP concorrente preservado (plugins/engineering,
plugin-ui, tv-dashboard, dados de tasks alheias — não tocados)
PHASE_FROM_16=C3/T2 · INT-1 pendente de revisão de coordenação
NEXT_FROM_LEDGER=COORDINATION_INT1_REQUIREMENTS_EVIDENCE_MATRIX_AND_FINITE_ACCEPTANCE_DECISION
FROZEN_DECISIONS: AGENT_COUNT=1 · NATIVE_PYDANTIC_AI=YES · NEW_ROUTER=NO
NEW_PLANNER=NO · NEW_RESOLVER_ENGINE=NO · instrução v2-2 fp 3692299dac74c26e
```

Nenhuma divergência `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED` encontrada entre autoridades canônicas.

## 2. Perguntas originais do PO (objetivos canônicos)

| ID | Pergunta | Owner esperado | Classe de evidência |
|---|---|---|---|
| P1 | "Qual é a estrutura do produto 90260921?" | DAVI | composição/árvore de produto |
| P2 | "Quais processos de transformação estão cadastrados?" | TÉO | listagem de processos (`process.search` sem filtro enumera todos; `q`/filtros opcionais; `page`/`page_size` suportados) |
| P3 | "Quais formatos de visualização de dados estão disponíveis?" | VISTA (knowledge/read) + TÉO (views de dashboard) | catálogo/guia de formatos |

## 3. Nova divergência causal comprovada nesta revisão (defeito corrigido)

**Classe:** rejeição tipada do owner mal classificada — segunda ocorrência da família "feedback de rejeição não chega ao modelo" (Doc 312 §B1/B4).

Cadeia comprovada com logging instrumentado + probe direto:

```text
model → vista.read {entity, action} 
  → owner VISTA responde envelope tipado isError:true 
    {"status":"error","error_kind":"validation","code":"INVALID_CHANGE"|"QUERY_REQUIRED"|...,"recoverable":true,"message":"…"}
  → _normalize_outcome: code ∉ _OWNER_ARG_VALIDATION_CODES (ARGUMENT_VALIDATION|UNKNOWN_ENTITY|UNKNOWN_ACTION|UNKNOWN_OPERATION)
  → SpecialistInteropError("mcp_protocol_error")
  → GovernedCapabilityAttempt status=SOURCE_UNAVAILABLE
  → modelo vê "fonte indisponível" e abandona o owner correto
```

- O owner VISTA **estava saudável** (probe direto `call_remote_tool`: 10/10 OK; endpoints `initialize` em <200ms; `playlist.list` retorna dados reais). Não era flake de transporte — era envelope de rejeição tipada mal classificado.
- `recoverable:true` é owner-declarado **somente** para `error_kind=="validation"` (contrato `delpi_mcp`: "argument validation rejections are repairable by the caller" — `tv-dashboard-api/tv_app/interface/mcp/tool_bridge.py:176-181`).
- Correção bounded (reuso do mecanismo existente `OWNER_ARGUMENT_REJECTED` + `owner_hint` → `owner_validation_hint` → `ModelRetry`): a gate de reparabilidade passa a admitir também `error_kind=="validation"` com `recoverable is True`; `recoverable` continua obrigatório — casos sem kind/recoverable seguem terminais.
- RED→GREEN: 3 testes novos em `test_specialist_interop_usecase.py` (positivo + sem `recoverable` + `error_kind` não-validation) + suíte completa delia-api verde (2 falhas pré-existentes deselecionadas — mesmas do baseline).
- Verificação real: `provider_invoke error=owner_argument_rejected` em Qwen real; modelo recebeu a dica e recuperou para `vista.knowledge`/`teo.analyze` com sucesso.

## 4. Matriz de aceitação por requisito

| Requisito | Fonte canônica | Baseline | Correção | Evidência atual (SHA / eval / teste) | Classificação | Bloqueia INT-1 |
|---|---|---|---|---|---|---|
| P1 estrutura de produto | Doc 16, Doc 310 | FAIL PO 11-10 | descrições owner (Doc 310) | `or-qwen14b-985d439b1653` DAVI-first GROUNDED | **SATISFIED_PROVEN** (in sample) | NÃO |
| P2 processos cadastrados | Doc 16, Doc 299/313 | FAIL PO 11-10; parcial pré-correções | — | `or-qwen14b-123ff3f94c37` (HEAD): `teo.read` ×2 SUCCESS (busca com filtro restritivo → 0 linhas) + `davi.get_context` discovery → clarificação honesta, sem fabricação | **PARTIALLY_SATISFIED** — owner/capability corretos; gap model-caused de estratégia de argumentos (não retentou busca sem filtro; contrato suporta listagem completa — `q` opcional no owner) | RESIDUAL (não é defeito de código comprovado; satisfação do objetivo parcial) |
| P3 formatos de visualização | Doc 16, Doc 299/313 | FAIL PO 11-10; VISTA-first já corrigido (Doc 299) | **fix error_kind=validation (§3)** | pré-fix: `123ff3f94c37`/`3eac383d5237`/`b51e9ecf9f5d` — vista.* `SOURCE_UNAVAILABLE` (na verdade rejeições tipadas). pós-fix: `or-qwen14b-5ad8d570cfdc` GROUNDED/**partial** com formatos reais (`dashboard_summary_live`, `dashboard_process_ranking`, `data_model_preview`, `data_block_preview` via `teo.analyze` + `vista.knowledge` SUCCESS); `or-qwen14b-7c97bac72237` GROUNDED/**insufficient** honesto (catálogo de guias vazio p/ o tópico) | **PARTIALLY_SATISFIED** — cadeia rejeição→feedback→recuperação comprovada; enumeração completa limitada pelo contrato owner (VISTA não publica "catálogo de formatos"; TÉO analyze provê nomes reais de dashboards) | RESIDUAL (ver §5) |
| Seleção semântica | Docs 310/311 | — | — | G1/P1/M1 DAVI-first; IG1–IG4 4/4 | **SATISFIED_PROVEN_IN_SAMPLE** | NÃO |
| Continuidade de investigação | Doc 293/299 | — | — | P2: clarificação honesta em vez de retry sem filtro; R4/R5 pós-fix: recuperação após rejeição tipada | **PARTIALLY_SATISFIED** | RESIDUAL |
| Resolução de identificadores | Doc 312 | — | `ProcessoRepository.get` reuse + echo `codigo_processo` | R1/R2 real + testes determinísticos | **SATISFIED_PROVEN_IN_SAMPLE** | NÃO |
| Integridade de argumentos MCP | Doc 312 | self-injeção `query` | `declared_properties` gate + `explain_arguments` | determinístico + real | **SATISFIED_PROVEN** | NÃO |
| Rejeição tipada do owner → feedback | **Novo (esta revisão)** | `mcp_protocol_error`→`SOURCE_UNAVAILABLE` | gate `error_kind=="validation"` + `recoverable` (§3) | 3 testes novos + real `error=owner_argument_rejected` | **CORRIGIDO_PROVEN** | NÃO (após fix) |
| Authorization denied | Docs 310/312 | — | — | `or-qwen14b-525ed88ac205`, R4 real | **SATISFIED_PROVEN_IN_SAMPLE** | NÃO |
| Autorização parcial | Doc 312 | — | — | R4: TÉO SUCCESS + DAVI AUTHZ_DENIED, resposta parcial, sem bypass/leak | **SATISFIED_PROVEN_IN_SAMPLE** | NÃO |
| Evidence grounding / outcome | Docs 310–312 | — | — | GROUNDED com honestidade (partial/insufficient declarado; `result_truncated`; sem falso `OBJECTIVE_SATISFIED`) | **SATISFIED_PROVEN_IN_SAMPLE** | NÃO |
| Satisfação do objetivo (P1/P2/P3) | Doc 16/313 | FAIL | — | P1 satisfeita; P2/P3 parciais honestas | **PARTIALLY_SATISFIED** | RESIDUAL — ver §5 |
| Generalização | Doc 313 | — | — | samples pequenos independentes | **PROVEN_IN_SAMPLE** — sem claim universal | NÃO (limitação declarada) |
| Gates L/A/O/R (Doc 293) | Doc 293 | — | — | L/A: evidência consistente; O: parcial (P2/P3); R: **TEST_NOT_RUN** (bateria completa não autorizada nesta task) | **PENDING** — gate explícito com condição | CONDICIONAL (§6) |

## 5. Bloqueadores, residuais e dependências

### 5.1 Bloqueadores materiais (critério violado, owner/ação conhecida)

| ID | Defeito | Owner | Evidência | Critério | Correção mínima | Estado |
|---|---|---|---|---|---|---|
| BLK-1 | Rejeição tipada owner (`error_kind=validation`+`recoverable`, códigos fora do set canônico) → `mcp_protocol_error`→`SOURCE_UNAVAILABLE` | DÉLIA `specialist_interop._normalize_outcome` | logs `provider_invoke error` + probe + trace | feedback de rejeição deve chegar ao modelo | gate por `error_kind`+`recoverable` (implementado) | **CORRIGIDO** neste commit |
| BLK-2 | P2: busca filtrada vazia → clarificação em vez de listagem sem filtro | modelo/contrato (instrução) | `or-qwen14b-123ff3f94c37` | P2 satisfação | não é defeito de código comprovado; candidato: iteração bounded de instrução/contrato OU aceitar residual | **REWORK_OPCIONAL** — decisão de coordenação |
| BLK-3 | Enumeração completa de formatos (P3) sem capability owner equivalente | VISTA (owner externo) | `or-qwen14b-7c97bac72237`: `product_guide` 0 tópicos; `read` vocabulário fechado sem "formats catalog" | P3 satisfação total | extensão de contrato VISTA (`get_context action=catalog` já publica catálogo; avaliar read dedicado) | **EXTERNAL_OWNER_DEPENDENCY** |

### 5.2 Residuais não bloqueantes

| ID | Residual | Nota |
|---|---|---|
| RES-1 | `INT1-PROJECTION-BUDGET` | árvores TÉO grandes > 20k → `result_truncated` honesto (Doc 312) |
| RES-2 | `attempt.status=SOURCE_UNAVAILABLE` também para `owner_argument_rejected` | `error_code`+`owner_hint` carregam a semântica correta; label do status é conflated — dívida de observabilidade, não funcional |
| RES-3 | `mcp_timeout` real em `teo.analyze` pesado (15s, 1 ocorrência) | latência de view analítica; confiabilidade, não INT-1 |
| RES-4 | 2 falhas de teste pré-existentes (`test_runtime_profiles_share_execution_policy`, `test_module_exposes_native_first_tools`) | baseline pré-INT-1; owner: dívida de testes DÉLIA |
| RES-5 | `INT1-DAVI-NONEXECUTABLE-CAPS` (`NEEDS_*_PROJECTION`) | herdado Doc 310; owner DAVI |
| RES-6 | `coverage_unknown`/`declared_status_overridden` em respostas honestas | finalização conservadora — comportamento correto |

### 5.3 Dependências externas / gates pendentes

| ID | Dependência | Condição objetiva |
|---|---|---|
| EXT-1 | VISTA: capability de enumeração de formatos (BLK-3) | contrato owner decide; fora do escopo INT-1 |
| EXT-2 | Gate R (regressão completa) | bateria completa conforme DoD canônico — **TEST_NOT_RUN**; executar somente se critério de aceite exigir, com owner e condição registrados |
| EXT-3 | Runtime/produção paridade | implementação avaliada em DEV isolado; `PRODUCTION_DEPLOY=NOT_AUTHORIZED` |

## 6. Pacote de revisão independente

```text
INT1_ACCEPTANCE_MATRIX: §4 (14 requisitos)
INT1_SATISFIED_REQUIREMENTS: P1, seleção semântica, identificadores,
  integridade de argumentos, rejeição→feedback (fix), authz denied,
  autorização parcial, grounding/outcome — todos *_IN_SAMPLE
INT1_MATERIAL_BLOCKERS: BLK-1 (corrigido) · BLK-2 (residual model-caused)
  · BLK-3 (dependência owner VISTA)
INT1_EXTERNAL_DEPENDENCIES: EXT-1/2/3
INT1_ACCEPTED_RESIDUALS: RES-1..RES-6
INT1_MISSING_EVIDENCE: gate R (bateria completa); P2/P3 satisfação total
INT1_MINIMAL_REWORK: (a) opcional — iteração bounded instrução/contrato p/
  retry sem filtro após busca vazia; (b) owner VISTA — capability de
  enumeração de formatos; (c) gate R se exigido pelo DoD canônico
INT1_FINAL_REVIEW_RECOMMENDATION: ACCEPT_WITH_RESIDUAL
```

**Justificativa da recomendação:** todos os requisitos de inteligência investigativa têm evidência real em sample (seleção, identificadores, argumentos, authz, grounding); os três bloqueadores identificados nesta revisão se resolvem em: correção implementada (BLK-1), residual de capacidade do modelo com comportamento honesto (BLK-2) e lacuna de contrato do owner externo (BLK-3) — nenhum é defeito de código aberto na DÉLIA. As respostas P2/P3 não-satisfeitas são insuficientes **honestas** (sem fabricação, sem bypass), não violações de contrato. A decisão final de aceite cabe à coordenação independente.

## 7. Diferenças baseline → atual

- Baseline PO (11-10): P1/P2/P3 FAIL — owner errado/respostas sem fundamento.
- Doc 310–312: P1 resolvido; identificadores/argumentos/authz parcial comprovados.
- Esta revisão (HEAD `d0ab08a` + fix): 
  - Novo defeito comprovado e corrigido (rejeições tipadas → `SOURCE_UNAVAILABLE`).
  - P2: evidência atual de insuficiência honesta (não regressão — falha de estratégia de argumentos do modelo).
  - P3: de "fonte indisponível" fantasma para recuperação real com dados de owner (GROUNDED partial / insufficient honesto conforme caminho do modelo).

## 8. Condição objetiva de fechamento

Para `INT1_CLOSED=YES` (decisão de coordenação, não deste documento):

1. Aceitar classificações da matriz §4 (incl. PARTIALLY_SATISFIED para P2/P3) ou exigir evidência adicional específica por requisito.
2. Decidir BLK-2: iteração bounded de instrução/contrato (re-run P2 apenas) **ou** residual aceito com dono.
3. Decidir BLK-3/EXT-1: abrir demanda ao owner VISTA **ou** aceitar enumeração parcial via TÉO+limitações declaradas.
4. Gate R: definir se DoD canônico exige bateria completa antes do aceite formal.

**NEXT=COORDINATION_INT1_FINITE_ACCEPTANCE_DECISION** · `INT1_STAGE_ACCEPTANCE=PENDING_COORDINATION_REVIEW` · `INT1_CLOSED=NO` · `INT2/INT3/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED`.
