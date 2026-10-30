# Doc 57 — EVA.MCP.FULL.PROD.ACTIVATION: Runtime & Governed ACT Evidence

Status: `READY_FOR_ACTIVATION` — superfície semântica em produção com ACT
por classe de risco + confirmação humana verificável (MCP elicitation)
implementados, testados e deployados. **Ativação de escrita permanece
PENDING_AUTHORIZATION** — a aprovação operacional específica (Gate 5 da
missão) ainda não foi apresentada; o prompt genérico não a substitui.
Owner: `engineering-api`. Data: 2026-10-30.

## 1. Deploy

| Item | Valor |
|---|---|
| SHA anterior prod | `70e93be21f` |
| DEPLOYED_SHA | `d709338dc8` |
| Procedimento | canônico: `git pull --ff-only` + `up-prod-sequential.sh --build engineering-api` em `operador@192.168.1.237` |
| Serviços tocados | somente `delpi-engineering-api` |
| Dados | zero mudança DB/schema/grants/writer; NC baseline = 53 |
| Flags prod | `ENG_EVA_ACT_ENABLED=` (vazio), `ENG_EVA_ACT_DELETE_ENABLED` ausente, `ENG_EVA_ACT_IMPORT_ENABLED` ausente, `ENG_NC_IMPORT_REPLACE_ENABLED=false` → **todos os tiers fail-closed** |

## 2. O que mudou (correção exigida pelo Gate 8/9 da missão)

A missão proíbe tratar um booleano global como autorização para todas as
classes de operação e exige confirmação humana **verificável** para
DELETE. Implementado:

1. **Gates por classe de risco** (`tool_bridge._require_eva_act(act_class)`):
   - `write` — create/update → `ENG_EVA_ACT_ENABLED`;
   - `delete` — exclusão → master + `ENG_EVA_ACT_DELETE_ENABLED`;
   - `import` — replace-all commit → master + `ENG_EVA_ACT_IMPORT_ENABLED`
     (o gate do owner `ENG_NC_IMPORT_REPLACE_ENABLED` continua valendo);
   - dry-run de import permanece no tier write (sem efeitos colaterais);
   - tools legadas `delete_nonconformity`/`import_nonconformities`
     roteadas aos mesmos tiers — nenhum caminho contorna o tier.
2. **Confirmação humana verificável** (`semantic_bridge._require_human_confirmation`):
   - commit de delete/import exige MCP **elicitation** (form mode): o
     servidor pergunta ao humano via cliente MCP durante a requisição;
     schema exige `confirm=true` **e** `target_echo` idêntico ao alvo
     (`record_id` para delete, `import_replace_all` para import);
   - `ctx` injetado pelo MCP SDK (`context_kwarg`, fora do inputSchema);
   - consumidor sem elicitation → `confirmation_unavailable` (403)
     honesto — **a proposta NÃO é consumida** e pode ser retentada;
   - decline/cancel/echo errado → `confirmation_declined` (403), nada
     alterado, proposta intacta;
   - posse do `proposal_ref` isoladamente nunca é prova.
3. `get_context` expõe `act_tiers` + `act_flags` por classe.

## 3. Evidência de testes (DEV)

491 passed, 10 skipped no SHA deployado. Cobertura nova:
- tier flags: delete/import negados com só o master (semantic + legacy);
- elicitation: accept+echo correto executa; decline/cancel/echo errado/
  confirm=false → `confirmation_declined` (4 parametrizados, 0 deletes);
- elicitation ausente/quebrada → `confirmation_unavailable`, proposta
  preservada e retry bem-sucedido com canal válido;
- import: dry-run no tier write, commit exige tier + elicitação;
- `get_context` reporta `act_tiers`/`act_flags`.

## 4. Evidência runtime em produção (SHA `d709338dc8`)

OAuth real: usuário smoke temporário (`act57.smoke`, role `Analista de
Engenharia - SC` → `engineering.access`), auth-code+PKCE completo com
`mcp-engineering` — token `azp=mcp-engineering`, `aud` inclui a resource
MCP, `scope` inclui `mcp:tools`. Identidade removida após a coleta
(0 remanescentes KC + Core).

| Check | Resultado |
|---|---|
| tools/list | 29 tools (6 semânticas + 23 deprecated) |
| get_context | `act_enabled:false`, `act_tiers` write/delete/import = false, `act_flags` expostos |
| read nonconformity.search | success, total 53 |
| execute nonconformity.create | 403 `act_disabled` |
| delete prepare | 403 `act_disabled` |
| execute import commit | 403 `act_disabled` |
| sem token | 401 |
| Portal `/`, `/apps/engineering` | 200 |
| REST NC sem auth | 401 |
| logs pós-deploy | zero erros/tracebacks |

## 5. Ledger de capacidades

| Capacidade | Estado |
|---|---|
| READ (home/overview/LMPs/produtos/NCs/histórico/indicadores/contexto/export) | `PROVEN_PROD` |
| ANALYZE (nc.recurrence, lmp.performance) | `PROVEN_PROD` |
| KNOWLEDGE (nc.guide, lmp.guide, eva.usage) | `PROVEN_PROD` |
| CREATE/UPDATE NC | `PROVEN_DEV` — código, contrato, idempotência, ETag e postcondition prontos; bloqueados por flag até Gate 5 |
| DELETE NC | `PROVEN_DEV` — proposta selada + elicitation implementados e testados; requer aprovação de segurança + consumer com suporte a elicitation |
| IMPORT dry-run | `PROVEN_DEV` (tier write) |
| IMPORT replace-all | `BLOCKED` — tier import + `ENG_NC_IMPORT_REPLACE_ENABLED=false` + aprovação específica; nunca como smoke |
| Operações compostas (READ→VALIDATE→EXECUTE→VERIFY→READ) | `PENDING` — depende de ACT habilitado para evidência |
| Drawings/roteiros/matérias-primas/inspeções/docs | `NOT_IMPLEMENTED` (planned, honesto) |

## 6. Pacote de ativação (para o owner de Engenharia + segurança)

Para aprovação de cada tier, especificar: ambiente, escopo, identidade,
política de confirmação, limites, janela, rollback, critérios de sucesso
e responsável pelo acompanhamento. Passos operacionais quando aprovado:

- **Tier write** (CREATE/UPDATE de NC): `ENG_EVA_ACT_ENABLED=true` em
  `infra/.env` → restart de `delpi-engineering-api`. Rollback: esvaziar
  a flag e reiniciar (dados gravados permanecem — reconciliar, nunca
  apagar). Pré-requisitos: todos já comprovados.
- **Tier delete**: `ENG_EVA_ACT_DELETE_ENABLED=true` **só após**
  confirmar que o consumidor MCP suporta elicitation (caso contrário
  delete responde `confirmation_unavailable` — comportamento correto).
  Aprovação de segurança específica exigida.
- **Tier import**: `ENG_EVA_ACT_IMPORT_ENABLED=true` +
  `ENG_NC_IMPORT_REPLACE_ENABLED=true` somente com aprovação separada,
  backup, janela autorizada e dataset conhecido. Não recomendado sem
  necessidade real.
- Testes mutáveis em prod: apenas registro sintético com isolamento e
  limpeza auditável (padrão já usado nesta missão).

## 7. Rollback

- Preferencial: esvaziar flags + restart (instantâneo, dados preservados).
- Código: `git checkout 70e93be21f` + rebuild engineering-api.
- Não executado — estado atual é fail-closed estável.

## 8. Residuais

- DELETE depende de elicitation do consumer (ChatGPT MCP client): se o
  consumidor não suportar, DELETE permanece bloqueado por design —
  validar suporte antes da aprovação do tier.
- Usuários smoke são criados/removidos por missão; padronizar smoke
  identity descartável documentada seria melhoria futura.
- Row Core órfã `b069ead1` (Smoke T7) segue registrada — cleanup opcional.

## 9. Critérios de aceite

PASS: EVA-PROD-01..06, 13 (AuthZ live), 14 (identidade humana), 15-18
(provadas em DEV), 19-25 (negativos, Portal, legado, monitoramento via
logs, rollback, doc, SHA).
PENDING_AUTHORIZATION: EVA-PROD-07 (aprovações), 08-10 (CREATE/UPDATE/
DELETE em prod), 11 (import permanece protegido por design), 12
(compostas dependem de ACT).
Nenhum critério dependente de ACT foi marcado PASS — conforme §17 da
missão.

Generated by Devin — EVA.MCP.FULL.PROD.ACTIVATION.
