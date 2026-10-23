# 123 — Homologação produtiva autenticada: D4/D5/D8 com Kimi
**TRACK_ID:** DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01
**TASK_ID:** DELIA-C3-S5-PRODUCTION-AUTHENTICATED-OUTCOME-HOMOLOGATION-01
**Data:** 2026-10-23
**Status:** EXECUTED — resultados classificados; nenhuma alteração de runtime.
**Executor:** Devin. **Review:** Architecture / Coordination.
**Contrato:** tarefa de homologação autenticada sobre [doc 122](./122-s5-rework-independent-coordination-verdict.md) (`NEXT=PO_PRODUCTION_D4_D5_D8_OBSERVATION`). Escopo: read-only; `CODE_CHANGED=NO`, `DEPLOY_EXECUTED=NO`, `REWORK_S5_USED=1/1` (encerrado).

## 0. Reanchor e ambiente avaliado
- HEAD da avaliação: `bf3db64c8` (superset documental do release `88e4598881`).
- Servidor: `srv-api` (`~/projetos/delpi-central`), `origin/main` verificado.
- Container `delpi-delia-api`: **healthy**, imagem `sha256:f9e2b4cb54c9e1d6126c32d290fd7392777febbc4693761b01a3e41e0643ce4f` — mesma do doc 121.
- Modelo produtivo: `moonshotai/kimi-k3` (OpenRouter), `DELIA_LLM_TIMEOUT_SECONDS=60`, `DELIA_LLM_CALL_MAX_ATTEMPTS=3`, `DELIA_TURN_BUDGET_SECONDS=300`, `DELIA_MAX_GOVERNED_ATTEMPTS=1`, `DELIA_RESPONSE_INTELLIGENCE_ENABLED=true` (CRI ativo, JSON v4 conforme doc 116).
- Wire checks: `GET /apps/delia-api/health` → 200; `POST /apps/delia-api/interaction/turns` sem bearer → 401.
- MCP `DELIA_MCP_{DAVI,TEO,VISTA}_ENABLED=true` com endpoints internos alcançáveis (401 sem bearer = auth exigida, esperado).

## 1. Identidade e autorização
- Identidade: `user` (sub `401b25fa-…`, João Silva) — usuário produtivo real, credenciais fornecidas diretamente pelo Product Owner nesta tarefa.
- Grants efetivos verificados em `delpi_core` (read-only): `delia.access`, `tv-dashboard.read/manage/write`, `transformometro.access/manage`, entre outros; consentimento `ai_context` concedido via Portal real.
- Token: password-grant OIDC público `delpi-central` — mesmo mecanismo do Portal; nenhum usuário criado, senha redefinida, token copiado ou AuthZ contornado.
- **Causa raiz do primeiro round (evidência de processo, não defeito prod):** o grant inicial omitiu `scope=openid`; o token delegado resultante (`email mcp:tools profile`) falhava o gate MCP com `MISSING_REQUIRED_SCOPE missing=openid` (logs `mcp_auth_denied` nos serviços). Com `scope=openid profile email` — como o fluxo real do Portal — os três token-exchanges (`mcp-api-delpi`, `mcp-transformometro`, `mcp-tv-dashboard`) retornaram 200 e a superfície completa respondeu. Round 1 descartado como `STALE_EVIDENCE` de harness.

## 2. Bateria executada (17:53–17:55 UTC-3, runtime acima)
| Caso | http | Grounding | Epistemic | Proveniência | Estágios modelo (tentativas) |
|---|---|---|---|---|---|
| D4 | 200 | NON_GROUNDED | OBSERVATION | — (listagem determinística) | admission(1) |
| D4-R | 200 | NON_GROUNDED | OBSERVATION | — | admission(1) |
| D5 | 200 | GROUNDED | OBSERVATION | mcp:vista `get_catalog` corr `0d661ee1` | admission(1), select_group(1), select_capability(1), native_assessment(1) |
| D5-R | 200 | GROUNDED | OBSERVATION | mcp:vista `get_product_guide` corr `f5895dd5` | admission, select_group, select_capability, native_assessment, index_select (1 cada) |
| D8 | 200 | GROUNDED | OBSERVATION | openapi:delpi `delpi.get_product_summary` corr `165e92e3` | admission→arguments (1 cada) |
| D8-R | 200 | GROUNDED | OBSERVATION | mcp:davi `execute_delpi_information` corr `16e6ab34` | admission→candidate_arguments (1 cada) |
| N1 | 200 | NON_GROUNDED | HYPOTHESIS | — | admission(1), turn(1) |

Tokens reais reportados pelo provider (observability): D4 938in/79out; D5 940+2849+2476+1751 in / 197+374+844+80 out; D8 932+2830+1445+714+923 in / 65+166+168+75+48 out; D8-R 1070+1332+2415+995+805+1185+547 in / 122+256+266+183+168+112+153 out; N1 923+717 in / 68+607 out. Todas as chamadas `attempt=1`, `finish_status=completed`.

## 3. Resultados e classificação

### D4 — PASS (D4-R PASS)
`Quais especialistas estão disponíveis…` → admission `surface_inquiry` → **listagem viva determinística** de DAVI (discover/execute_delpi_information), TÉO (get_my_context, get_workspace_context, get_catalog, get_methodology_guide, get_product_guide, solution_read) e VISTA (list_playlists, get_playlist_context, …), descrições verbatim do owner, rodapé *"uma superfície publicada respondeu… permissão verificada a cada solicitação concreta — esta lista não garante autorização"*. `capability_surface_listing`, OBSERVATION, 1 chamada de modelo, composição determinística. Sem dump técnico, sem especialista inventado, sem claim de autorização. D4-R idêntico sob reformulação.

### D5 — FAIL
`Quais formatos de dados e visualizações…` → admission operational → `select_group=vista` → `select_capability=get_catalog` → invocada → **resposta = dump JSON bruto do payload do catálogo**: `"A fonte publica estas informações sobre o que ela oferece: - entities.playlist: {"id": "playlist", "kind": "ENTITY", "owner": "tv-dashboard-api", …"`. Viola diretamente o critério do contrato: *"Não aceitar: Schema `entities.playlist` como resposta; JSON técnico bruto"*.
**Primeiro estágio divergente:** `select_capability` escolheu `get_catalog` (descoberta técnica) em vez de `get_product_guide` (guia de formatos); segundo ponto divergente: a projeção de evidência tratou a seção `entities.*` do catálogo como conteúdo de resposta (mesma lacuna observada no eval local e prevista pelo review 119 §2/§5). `GROUNDED` + OBSERVATION não convertem em PASS — HTTP 200 com saída técnica.

### D5-R — PARTIAL
Reformulação → `get_product_guide` (capability semanticamente correta) + `index_select` → `lim=['insufficient_evidence']`, conteúdo = declaração honesta de cobertura não comprovada. Comportamento fail-honest correto, mas não respondeu formatos efetivos — evidência do mesmo gap D5 (o guidance sobre formatos não foi projetado como resposta).

### D8 — PASS (com residual de rótulo)
`Qual é a descrição do material de código 10080043?` → `openapi:delpi` → `delpi.get_product_summary` (READ) → argumento `code` → owner real → `GROUNDED`, OBSERVATION, `is_complete=true`. Resposta: `Código: 10080043 · Descrição: TERM. OLHAL M6 6,30MM 4,00-6,00MM2 12,00MM COMP 22,60MM ESTANHADO S/ISOLACAO FITADO ROHS · Group code: 1008 · Tipo: MP`. Rótulos PT-BR governados aplicados (Código/Descrição/Tipo); valores verbatim, sem tradução nem expansão inventada. Residual: `Group code` renderizou sem rótulo PT-BR (cobertura incremental do vocabulário v4 — mesmo residual do S3).

### D8-R — PASS (com residual de rótulo)
Continuidade na mesma conversa → `turn_goal` interpretou "desse material" → `mcp:davi` → `discover_delpi_information` → `execute_delpi_information` com `candidate_token` → **mesmo registro** (`Product code: 10080043 · Descrição: TERM. OLHAL…`). Provider diferente do D8 (DAVI vs OpenAPI) — seleção provider-neutral funcionando; mesma descrição canônica confirmada. Residual: `Product code`/`Group category` sem rótulos PT-BR.

### N1 — PASS
`O que é SIPOC?` → admission `explanation` → `turn` único, zero invocações MCP → resposta conceitual correta com disclaimer explícito ("exemplo ilustrativo — não é um registro DELPI"). Caminho conversacional governado íntegro com Kimi.

## 4. Comparação com AC (doc 120)
| Gate | Veredito |
|---|---|
| AC-S5-B (D4 original+variantes) | **PASS** |
| AC-S5-C (D5 guidance/read end-to-end ou insuficiência específica) | **FAIL** — dump `entities.playlist` em produção real |
| AC-S5-D (D8 READ + PT-BR + valores verbatim) | **PASS** (residual: 3 rótulos não cobertos) |
| AC-S5-E (no-tool/negativas) | **PASS** — N1 conversacional sem MCP |
| AC-S5-H (homologação produtiva) | **EXECUTED** — era TEST_NOT_RUN |

## 5. Gaps, divergências e decisões
1. **D5 functional FAIL (material):** a seleção de capability para cobertura de formatos preferiu `get_catalog`; o payload `entities.*` vazou como conteúdo de resposta. Cadeia causal: `select_capability` (modelo) → payload do catálogo → projeção de evidência sem exclusão da família `entities`. Não há hotfix autorizado nesta tarefa (rework S5 = 1/1); requer decisão do Product Master — possível novo rework bounded ou reclassificação do AC.
2. Residual cosmético: `Group code`/`Product code`/`Group category` sem rótulo PT-BR governado (vocabulário v4 incremental).
3. Sem drift de authority, sem regressão de segurança: AuthZ fail-closed (401), AuthZ owner não exercida em ACT, nenhum write executado.
4. `PROD_AUTHENTICATED_TESTS` agora **EXECUTED** — desbloqueio formal resolvido por credencial fornecida pelo PO.

## 6. Telemetria consolidada
Latências totais: D4 2.5s, D4-R 8.0s, D5 20.5s, D5-R 19.8s, D8 11.1s, D8-R 30.1s, N1 12.4s — todas dentro de 300s; cada estágio de modelo 1 tentativa ≤ ~12s. Correlation IDs por caso registrados acima (seguros para exposição). Nenhum erro HTTP, nenhum 502/504, nenhum retry necessário.

## 7. Encerramento
`CODE_CHANGED=NO`, `DEPLOY_EXECUTED=NO`, `EXECUTION_DRIFT=NONE`. Homologação real concluída com identidade autorizada pelo PO. Resultado funcional: **D4 PASS, D5 FAIL, D5-R PARTIAL, D8 PASS, D8-R PASS, N1 PASS** — retorna à coordenação/Product Master com evidência causal para decisão sobre o gap D5. `COORDINATION_REVIEW_REQUIRED=YES`.
