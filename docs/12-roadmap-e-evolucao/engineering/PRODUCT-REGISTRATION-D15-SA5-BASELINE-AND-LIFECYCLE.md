# D15 — Baseline SA5, ciclo de vida e homologação

> **TASK_ID:** `ENG-PRC-D15-SA5-BASELINE-LIFECYCLE-AND-FULL-HML`  
> **Estado:** `IMPLEMENTED_DEV` (parcial em HML TOTVS / REMOVE owner)  
> **Precedência:** complementa D12–D14 e REF-012; não autoriza escrita ERP nem deploy produtivo.

## 1. Owner / consumers / fonte oficial

| Papel | Componente |
|---|---|
| Owner do domínio operacional | Engineering API (`product_registration`) |
| Consumers | Portal Engenharia, EVA (mesmos use cases) |
| Fonte oficial de produto/vínculos | TOTVS via api-delpi (READ-ONLY) |
| Identidade / AuthZ | Keycloak + Core (`engineering.access`) |

Fluxo: `Portal / EVA → Engineering API → api-delpi → TOTVS`.

## 2. Identidade da amarração

Chave oficial confirmada no contrato PRC vigente:

```text
(supplierCode, store)  # zeros à esquerda preservados
```

Filial/escopo de leitura é implícito na fonte oficial contratada do reader; não reduzir a chave. Part Number e Catálogo são atributos, não chave.

Identidade local de UI (D14-FIX-02): `rowId` + `origin: official|draft` — nunca confundir com a chave SA5.

## 3. Baseline oficial persistido

### Captura

No `POST /intake/requests` com `requestType=update`, a Engineering API:

1. Reconsulta `OfficialProductReaderPort` (mesmo pipeline de `edit-context`).
2. Exige `status=available` e, quando há `supplierLinkChanges`, `linksComplete=true`.
3. Monta snapshot canônico (`SOURCE_CONTRACT_VERSION = prc-sa5-baseline.v1`).
4. Valida pré-condições das ops contra o snapshot.
5. Persiste `official_baseline` JSONB imutável na solicitação (coluna dedicada; não sobrescrito por draft).

Campos conceituais:

```text
baselineVersion, sourceContractVersion, officialProductCode,
officialSource, readAt/capturedAt, capturedBy, correlationId,
linksComplete, fields[], links[], fingerprint
```

**Proibido:** aceitar snapshot do browser como prova oficial.

### Concorrência

- Cliente pode enviar `baselineFingerprint` (e opcionalmente `editContextReadAt`) obtido do `edit-context`.
- No intake, o servidor recalcula o fingerprint do estado relevante (campos + links + completude) — **não** usa timestamp isolado.
- Divergência → `409` com `code=official_context_stale` (sem rebase silencioso; edições do usuário permanecem no payload rejeitado para o cliente reconciliar).
- Ausência de fingerprint no cliente: ainda captura baseline server-side.

### Imutabilidade / retenção

- Baseline da solicitação não é alterado por `PATCH draft`.
- Nova captura versionada exige nova solicitação (ou mecanismo explícito futuro).
- Retenção: acompanha a solicitação e o ledger de eventos/verificações (append-only).

## 4. Operações SA5

### ADD

| Fase | Regra |
|---|---|
| Pré | Produto identificado; baseline completo; chave ausente no baseline; sem ops conflitantes |
| Pós (`verify-and-complete`) | Presença única; atributos informados batem; consulta completa |

### UPDATE seletivo

| Fase | Regra |
|---|---|
| Pré | Vínculo presente único; atributo conhecido; valor proposto ≠ anterior; sem `remove` na mesma chave |
| Pós | Compara **somente** atributos do change set (`partNumber` / `catalogNumber`) |

### REMOVE

| Variante | Comportamento |
|---|---|
| Descartar linha `draft` | Só estado local; sem op SA5 |
| Proposta sobre `official` | Op `remove` reversível no intake; presença no baseline |
| Conclusão | **`PENDING_OWNER`** — `verify-and-complete` **não** publica revisão se houver `remove`, mesmo com ausência comprovada |

Política candidata documentada; aprovação formal do owner Engenharia pendente. Esta task **não** constitui autorização de publicação REMOVE.

## 5. Request/response (extensões compatíveis)

Reutiliza rotas existentes. Extensões aditivas:

- `IntakeBody.baselineFingerprint?`, `editContextReadAt?`
- `edit-context` passa a incluir `fingerprint`, `baselineVersion`, `sourceContractVersion`
- `GET requests/{id}` inclui `officialBaseline` (read-only) e `removeCompletionPolicy`

Erros novos/estruturados:

| Código | HTTP | Quando |
|---|---|---|
| `official_context_stale` | 409 | Fingerprint cliente ≠ estado oficial atual |
| `validation_error` | 422 | Pré-condição ADD/UPDATE/REMOVE falhou |
| `state_conflict` | 409 | Conclusão com REMOVE sob `PENDING_OWNER` |
| herdados D13 | 409/422/5xx | mismatch / incomplete / unavailable |

## 6. Auditoria e revisões

Eventos preservam solicitação, chave, tipo de op, before/after (via ops + baseline), verificação, ator, canal, razões opcionais ≤250. Revisões imutáveis somente após `matched` e sem REMOVE pendente de owner. Atomicidade: verification + revision + request na mesma transação (já existente).

## 7. EVA

Mesmos use cases; sem regras SA5 duplicadas no layer semântico. Seis tools MCP preservadas. PREPARE/ACT + confirmação humana.

## 8. Classificação de fatos

| Item | Estado |
|---|---|
| Baseline server-side UPDATE | `PROVEN` (código + testes) |
| Pré-condições ADD/UPDATE/REMOVE | `PROVEN` |
| Pós-condições ADD/UPDATE seletivo | `PROVEN` (herdado D13 + gates D15) |
| Conclusão REMOVE | `PENDING_OWNER` |
| HML TOTVS operador manual | `PENDING_TOTVS_OPERATOR` |
| Deploy produção | `NOT_AUTHORIZED` |

## 9. Evidências (execução)

| Superfície | Resultado |
|---|---|
| Domínio `baseline.py` + pré-condições | PASS (pytest unit) |
| Intake UPDATE captura/persiste baseline | PASS |
| Fingerprint stale → 409 `official_context_stale` | PASS |
| ADD duplicado / incomplete SA5 | PASS |
| UPDATE PN seletivo + verify | PASS |
| REMOVE conclusão `PENDING_OWNER` | PASS (409, sem revisão) |
| edit-context fingerprint | PASS (pytest + Playwright) |
| EVA parity (submit async) | PASS |
| Vitest fingerprint no intake body | PASS |
| Playwright (prc-suppliers + D15) | PASS 12/12 desktop/tablet/mobile |
| PostgreSQL `official_baseline` | PASS (`ENG_PRC_TEST_DSN` → plugins_hub DEV) |
| Bundle DEV | `__federation_expose_App-CyhunCwe.js` |
| Screenshots | `assets/d15-baseline/prc-d15-baseline-loaded-{desktop,tablet,mobile}.png` |
| HML TOTVS ADD/UPDATE operador | `PENDING_TOTVS_OPERATOR` |
| REMOVE HML aceite | `PENDING_OWNER` |
| Produção | `NOT_PERFORMED` |

### Ledger de classificação

```text
BASE_SHA: 4b75436e97593d30f50a4f2f42f4faf465f9e36e
FINAL_SHA: 0f8d20d3eb0f504f4114ebe0001f899b5ba2bbab
BASELINE_SERVER_PERSISTENCE: PROVEN
ADD_PRE_POST: PROVEN (código/teste; HML TOTVS PENDING_TOTVS_OPERATOR)
UPDATE_SELECTIVE: PROVEN
REMOVE_PROPOSAL: PROVEN
REMOVE_COMPLETION: PENDING_OWNER
AUDIT_EVENTS: PROVEN
REVISION_IMMUTABILITY: PROVEN (herdado + gate REMOVE)
BUNDLE_FINGERPRINT: __federation_expose_App-CyhunCwe.js
```


## 10. Evolução aditiva D16 — bandeiras não alteram baseline SA5

**Novo plano:** [D16 — bandeiras operacionais do atendimento](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md). Bandeira é observação de acompanhamento dentro da Engineering API, com CRUD/audit independente. Não pertence ao snapshot oficial SB1/SA5, não muda fingerprint de baseline, compare ou `verify-and-complete`. Exemplo de PN a confirmar é anotação, **nunca** preenchimento técnico automático com zero. Bandeira aberta não bloqueia conclusão por padrão; mantém consulta após conclusão conforme AuthZ, para acompanhar cobrança posterior. Sujeito a contrato owner sobre edição pós-terminal. Integração EVA deve usar os mesmos casos de uso. **PLANNED.**


## D16-REF-01 — Bandeiras de acompanhamento vinculadas a atributos SA5

[Contrato D16-REF-01](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md#d16-ref-01--decisão-po-superveniente-bandeiras-por-campo-experiência-contextual-e-consultas-transversais). Bandeiras de acompanhamento são anotações da Engenharia em caso PRC, persistem mesmo quando o PN/Catálogo muda, o vínculo deixa de existir ou o caso é concluído. Identidade de marca no SA5 = requestId + supplierKey canônica + targetAttribute (partNumber ≠ catalogNumber), nunca rowId visual ou texto do PN. A flag **não** altera official_baseline, fingerprint, verify, revisão ou ERP, nem permite burlar PENDING_OWNER de remoção. A pesquisa transversal por produto e campo usa requests autorizados da Engineering API; sem SoT de produto novo. **TARGET não implementado por esta nota.**


## D15-REF-017 — Prova de resultado CREATE/UPDATE antes da conclusão

Conforme [PRC-REF-017 consolidado](./MFE-PRODUCT-REGISTRATION-POST-REDESIGN-REFINEMENT-PLAN.md), D15 estende seu gate de leitura oficial para as jornadas de conclusão CREATE e UPDATE. No **CREATE**, código oficial é inserido manualmente pelo analista **na etapa de conclusão**, após cadastro realizado por operador autorizado; caso não exista/não corresponda/incompleto/não verificável, bloquear \`completed\`. Guardar código e evidência oficial na revisão, histórico e retorno ao solicitante. Não presumir criação apenas pela existência do código: a prova de identidade/proveniência do novo produto exige contrato do owner quando a fonte oficial não fornecer o dado. No **UPDATE**, verificação por **cada campo alterado** SB1 e atributo SA5, com baseline/esperado/observado/resultado, sem exigir attributes untouched. Divergência de um item impede o commit inteiro; \`verify-and-complete\` continua live/fail-closed, sem SQL ERP no owner Engenharia. SA5 REMOVE permanece \`PENDING_OWNER\`. Critérios e testes bloqueantes detalhados no REF-017. **Status:** PLANNED_REFINEMENT, sem alteração de código por esta nota.

