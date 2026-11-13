# Doc 320 — INT-1 · TÉO Shared Resource Scope Fail-Closed Remediation and Gate R Security Revalidation

**TASK_ID:** `DELIA-C3-T2-INT1-TEO-SHARED-RESOURCE-SCOPE-FAIL-CLOSED-REMEDIATION-01`
**Data:** 2026-11-13
**BASE_HEAD:** `4a47a56c9d0a9773d6105492c3e898ed4c2ce145` (= `origin/main` no fetch; REFERENCE_HEAD `37ee712640` já incorporado por commits remotos docs/WIP concorrente)
**PRIMARY REFERENCE:** Doc 319 · contrato de domínio `transformometro-api/docs/domain/regras-de-calculo.md` § «Recursos compartilhados — `escopo_recurso`»
**STATUS:** `R_GATE=PASS_PROPOSED` · `INT1_CLOSED=NO` · publicado em `main` para revisão independente

---

## 1. Reancoragem

| Campo | Valor |
|---|---|
| HEAD | `4a47a56c9d` — idêntico a `origin/main` (fetch prévio) |
| Branch ativa | `devin/prc-track-prod-01-records-list` apontando para o mesmo SHA de `origin/main` (Regra 7 registrada; publicação via `HEAD:main`, sem troca/criação de branch) |
| WIP concorrente | `engineering-api/.../product_registration*.py` (3 modified) + artifacts untracked — **preservados, fora do stage** |
| PHASE_FROM_16 | C3/T2 — INT-1 pendente de aceite independente |
| NEXT_FROM_LEDGER | `COORDINATION_INT1_GATE_R_PUBLISHED_CODE_INDEPENDENT_REVIEW` |
| OWNER_CONTRACT | `SharedResourceScopeService` (domain, TÉO) — consumidor único `DashboardCalculatorService._get_eligible_links_for_resource` |

`EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=EXTEND` (mesmo módulo/funções, sem nova engine de filtragem).

## 2. Contrato empresarial autoritativo

Fonte: `regras-de-calculo.md` (doc canônico de cálculo) + `playbook-18` + schemas `crud_schemas.py`:

- `empresa` (default): todos os vínculos vigentes.
- `filial`: vínculos cuja instância tem a **mesma filial** da revisão âncora.
- `setor`: vínculos do **mesmo par filial × setor**.
- `todas_filiais_ativas=true`: instância corporativa — autorização legítima de match com qualquer filial (semântica mantida).
- Instância exige `filial_id` **ou** `todas_filiais_ativas` (validação de schema) — âncora de instância sempre tem identidade de filial ou flag corporativa.
- Fallback `processo` (sem instância): identidade legada `filial_id`/`setor_id` do processo — contrato preservado (S8).
- `codigo_filial`/`codigo_setor` são chaves de negócio únicas denormalizadas; `filial_id`/`setor_id` são UUID/FK. Processo legado carrega o **código** em ambos os campos; instância carrega UUID+código — por isso a igualdade deve ser testada **por campo homogêneo, exigindo valor não-vazio**.

## 3. Hipóteses → veredito

| Hipótese | Veredito | Evidência |
|---|---|---|
| **H1** `_share_setor` trata dois recursos sem identidade de setor como «mesmo setor» | **CONFIRMED_DEFECT** | linha 92: quando `setores`/keys ausentes em qualquer lado, caía em `codigo_setor == codigo_setor` → `"" == ""` → `True` |
| **H2** `filter_rateio_pool` retorna todos os vínculos quando a âncora não resolve | **CONFIRMED_DEFECT** | `if not anchor: return links` — liberava o pool inteiro para escopo `filial`/`setor` |
| `_same_filial` análogo | **CONFIRMED_DEFECT** | quando `filial_id` não presente em **ambos**, caía em `codigo_filial == codigo_filial` → `"" == ""` → `True`, inclusive com um lado identificado por `filial_id` e o outro sem nada |

**Impacto empresarial provado (não só lista):** o pool filtrado é o **denominador** do rateio (`igualitario` divide por `len(eligible_links)`; `por_revisoes_ativas` por revisões distintas; `por_peso` pela soma de pesos). Fail-open → vínculos de outras filiais/setores entram no denominador → **custo rateado sub-alocado por revisão** (diluição) e recurso fora-de-escopo agregado ao cálculo. Fail-closed por âncora ausente → pool vazio → `if not eligible_links: continue` → recurso não contribui (graceful, sem erro).

## 4. Reprodução — matriz S1–S12

13 testes novos em `tests/test_shared_resource_scope_service.py` (helpers `_chain`/`_pool`):

| Cenário | Resultado esperado pelo contrato | Antes (RED) | Depois (GREEN) |
|---|---|---|---|
| S1 mesma filial+setor | compartilha | ✅ | ✅ |
| S2 mesma filial, setores diferentes | exclui | ✅ | ✅ |
| S3 mesmo cod. setor, filiais diferentes | exclui | ✅ | ✅ |
| S4 **ambos sem setor** | pool vazio (âncora sem setor não prova «mesmo par») | ❌ devolvia r1+r2 | ✅ `[]` |
| S5 um lado sem setor | exclui o não-identificado | ✅ (assimetria do fallback) | ✅ |
| S6 **ambos sem filial** | pool vazio | ❌ devolvia r1+r2 | ✅ `[]` |
| S6b vínculo sem filial vs âncora identificada | exclui | ✅ | ✅ |
| S7 **âncora inexistente** | `[]` (nenhum vínculo pode casar) | ❌ devolvia todos | ✅ `[]` |
| S8 instância ausente + processo válido | fallback legado preservado | ✅ | ✅ |
| S9 `todas_filiais_ativas` | match com qualquer filial | ✅ | ✅ |
| S10 `SCOPE_EMPRESA` | pool completo | ✅ | ✅ |
| S11 `setores=[]` + top-level válido | identidade top-level preservada | ✅ | ✅ |
| S12 UUID/código divergentes + legado só-código | divergente exclui; código-only legítimo casa por `codigo_filial` | ✅ p/ negativo | ✅ |

**FIRST_DIVERGENCE:** S4 — `_share_setor` `"" == ""` → `True` (a âncora i1 e o link i2, ambos sem setor, foram considerados «mesmo setor»).

## 5. Correção mínima (owner TÉO, `shared_resource_scope_service.py`)

```text
_same_filial  → OR por campo homogêneo (filial_id, codigo_filial),
                exigindo valor NÃO-VAZIO e igualdade; senão False.
                (todas_filiais_ativas short-circuit preservado)
_share_setor  → se qualquer lado não tem keys → False;
                senão interseção (fallback codigo-vaio removido)
filter_rateio_pool → anchor não resolvida → return [] (pool vazio
                contratual; consumidor faz skip graceful)
```

Decisão `[]` vs erro tipado: contrato define pool = vínculos que casam com a âncora; âncora inexistente ⇒ nenhum match possível ⇒ `[]`. Consistente com o tratamento por-link (`continue` quando o vínculo não resolve) e com `if not eligible_links: continue` do calculator. Sem schema/assinatura pública alterada.

**Invariantes preservados:** match por código-only legado (instância UUID×código vs processo código×código casa via `codigo_filial`); `todas_filiais_ativas`; fallback processo; `SCOPE_EMPRESA` intocado.

## 6. Resultados

| Medida | Valor |
|---|---|
| RED | `test_s4` + `test_s6` + `test_s7` FAILED (3 divergências provadas) |
| TARGETED_GREEN | 17/17 `test_shared_resource_scope_service.py` PASS |
| Sibling/consumer | `test_dashboard_calculator_escopo_recurso` + `test_dashboard_calculator` = 49/49 PASS |
| TÉO FULL SUITE | **2140 PASSED / 62 SKIPPED / 0 FAILED** (baseline 2127 + 13 novos; skips inalterados) |
| DELIA integration | N/A — contrato interno de domínio TÉO; **MODEL_VISIBLE_CHANGE=NO** (nenhuma surface MCP/OpenAPI/Actions alterada) |
| VISTA/DAVI suites | Não reexecutadas — escopo restrito ao owner TÉO, sem tocar contratos cruzados (Doc 293 § regressão por escopo) |

## 7. Segurança / Outcome

```text
UNKNOWN_SCOPE_DOES_NOT_GRANT_ACCESS=YES      (âncora ausente → pool vazio)
MISSING_SECTOR_DOES_NOT_PROVE_EQUALITY=YES   (S4/S5)
MISSING_FILIAL_DOES_NOT_PROVE_EQUALITY=YES   (S6/S6b)
LEGITIMATE_SHARED_RESOURCES_PRESERVED=YES    (S1/S8/S9/S10/S11/S12-positivo)
DOMAIN_AUTHORITY_PRESERVED=YES               (fix no domain service owner; DÉLIA intocada)
TECHNICAL_TEST_PASS=YES · DOMAIN_OUTCOME_PROVEN=YES (denominador do rateio agora restrito ao escopo)
```

## 8. Gates

`L=PASS` (reportado) · `A=PASS` (AGENT_COUNT=1, owners intactos, sem RBAC/permission mutation) · `O=PASS` · **`R=PASS_PROPOSED`** — veredito formal é da coordenação; **não autoaprovado**.

## 9. Residuais

- Nenhum residual material novo. Linha `setores[0]`→top-level do `resolve_instancia_anchor` (Gate R anterior) permanece correta: `_setor_keys` agrega todos os `setores[]` + top-level.
- Registrado no residual register como `R-T3-SCOPE-FAIL-CLOSED` **CLOSED**.

## 10. Publicação

Commit identificado pela task em `main` (push `HEAD:main` — branch local `devin/prc-...` não alterada em remote; Regra 7/9 observadas: sem switch, sem branch nova, sem force). WIP concorrente engineering-api preservado fora do stage.

`PRODUCTION_DEPLOY=NOT_AUTHORIZED` · `PRODUCTION_DEPLOY_EXECUTED=NO` · `PHASE_ADVANCEMENT=NO` · `INT1_CLOSED=NO` · `INT2/INT3/T3=NOT_AUTHORIZED`

**NEXT=`COORDINATION_INT1_TEO_SCOPE_AND_GATE_R_INDEPENDENT_ACCEPTANCE_REVIEW`**
