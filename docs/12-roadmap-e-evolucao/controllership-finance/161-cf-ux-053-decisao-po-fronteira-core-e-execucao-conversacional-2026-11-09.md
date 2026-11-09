# Doc 161 — CF-UX-053: decisão PO sobre fronteira Core/CLARA e execução conversacional

**Data:** 09/11/2026 · **Processo:** PROC-0072 · **Tipo:** decisão PO de produto/arquitetura alvo + handoff executável · **Estado:** `PO_DECISION_PROVEN / TARGET / SECURITY_POLICY_PENDING / NO_RUNTIME`.

## 1. Declaração do PO (autoridade de produto)

O PO determinou expressamente: **"a CLARA não deve acumular responsabilidade da Core API; se a Core permite uma ação, a CLARA não deve ter outra responsabilidade [de RBAC]; funciona assim para todos os MCPs; não deve haver outro diferente"**. O PO reiterou que a confirmação da CLARA deve seguir o **mesmo padrão conversacional do TÉO**, dentro do ChatGPT, sem redirecionar para `/closing/clara-consent` e sem entregas parciais apresentadas como conclusão.

**Leitura de fronteira arquitetural:** Core é authority de identidade da plataforma, catálogo/effective permissions e RBAC. BFF CLARA deve consumir a Core e **não reproduzir política de RBAC**. O backend da CLARA deve **ainda** validar por operação `capability AND resource_scope/ownership AND business_rule`, com escopo de competência/filial, estado da evidência, transições, invariantes transacionais, auditoria e read-back. Consentimento humano de uma operação específica e AuthZ da Core são conceitos distintos; não afirmar que a Core fornece prova de consentimento do plano sem contrato correspondente.

## 2. Fatos de implementação já levantados

- Código `2444de3378`: proposta conversacional selada + `confirmation` no MCP, `CLARA_CONSENT_CHANNEL=portal` como default, flag de gate, V014 ainda obrigatório.
- Código `23d51e7af5`: schema dinâmico `phase_policy_for_capability()`, confirmação em lote e migration V020 reportada aplicada em produção; inventário [doc 160](./160-cf-ux-053-capability-channel-inventory-2026-11-09.md).
- Produção reportada pelo Cursor: `channel=portal`, `armed=false`, `portal_req=true`; ChatGPT pós-cutover `TEST_NOT_RUN`.
- Benchmark TÉO: `transformometro-api/tm_app/interface/mcp/server.py` e `tool_bridge_v3.py` usam `proposal_pending_confirmation` e `proposal_id + confirmation=true`. **Essa flag é um sinal do cliente MCP, não atestação independente de consentimento humano autenticado.**
- Consentimento adicional da CLARA foi desenhado em R-CLARA-01/V014; não é um RBAC Core paralelo. A discussão sobre sua retirada ou substituição deve ser documentada como **política de consentimento**, não como uma correção de permission codes.

## 3. Ordem de trabalho única para o Cursor

**Objetivo de ponta a ponta:** o operador autenticado pede a ação, recebe a descrição exata da proposta, confirma na conversa, o MCP executa somente a proposta válida sob AuthZ efetiva Core + regras de recurso/negócio, o backend audita e verifica o outcome, e o ChatGPT apresenta o resultado **sem visita à página externa**.

1. Revalidar HEAD, `git status`, Project Instructions, regras .cursor aplicáveis, README, doc 124, doc 150 §20.10, doc 160 e código/testes efetivos do TÉO/CLARA. Inventariar current producer/consumer e políticas de consentimento não-Core.
2. Gerar diff arquitetural **Core RBAC vs BFF resource/business vs consentimento** por capability; localizar qualquer RBAC duplicado e eliminar só após prova do contrato da Core.
3. Resolver no próprio fluxo de trabalho os gates de política: identificar owners reais, apresentar decisão de adoção do padrão TÉO e riscos; obter evidência escrita de Segurança/Plataforma e Controladoria para aceitar o nível de garantia residual ou exigir host-attestation. **PO decidiu a UX; não pedir novamente escolha de UX.** Se a evidência de aprovação não existir, **não simular assinatura nem habilitar ack**, registrar bloqueio concreto e entregar código isolado/relatório sem afirmar conclusão.
4. Com política aprovada: ajustar `consent_channel`, schemas MCP e catálogo `get_context(schema)`, semântica de propostas singles/batch, documentação, branding e distribuição do plugin, garantir ausência de `confirmation_url` obrigatória em todos os casos cobertos; preservar fallback de rollback até cutover.
5. Preservar prova de ator e vínculo à proposta selada, TTL/OCC/claim single-use, idempotência, Core AuthZ, resource scopes, regras canônicas, auditoria, read-back, compatibilidade; migrations forward-only.
6. Executar suites unitárias/integração/contrato/negativos, depois deploy versionado BFF + MCP + catálogo/plugin conforme padrão atual da plataforma; verificar configuração em runtime e schema `get_context` do host efetivo.
7. **Smoke real no ChatGPT com operação isolada de baixo impacto e dados de teste autorizados**: PREPARE → confirmação → ACT → read-back, sem Portal. Para publicação V2 real ou inativação V1, exigir requisição específica da operação, confirmação concreta e gate; teste não deve mutar dados produtivos de fechamento.
8. Registrar relatório completo com SHAs, config sanitizada, evidências de testes/prod, rollback verificado, matriz 48 capabilities, status `PASS/FAIL/INCONCLUSIVE/TEST_NOT_RUN`. **Não declarar `ACCEPT` por deploy ou teste verde isolado.**

## 4. Critérios de aceite não negociáveis

- Zero RBAC duplicado na CLARA; Core resolve effective permissions; BFF mantém resource/business gates.
- 13 `DIRECT_ALLOWED` sem regressão e 35 sensíveis inventariadas e sob política formalmente decidida.
- Nenhum consentimento expresso apenas por flag `confirmation=true` autoriza execução na ausência de proposta selada e política de confirmação aprovada.
- Produção/host mostram canal conversacional ativo, `portal_consent_required=false` no cenário homologado, schema e tool descriptions atualizadas; não exigir `clara-consent`.
- ChatGPT real `PASS` + auditoria/read-back; rollback demonstrado.
- `REWORK` ou `DECISION_REQUIRED` quando faltar decisão de Segurança/Controladoria; não implementar bypass por pressão de prazo.

## 5. Relação com documentos canônicos

Esta decisão **fixa a fronteira Core/CLARA e a UX TARGET**, mas **não altera sozinha a política runtime de consentimento descrita no doc 124 e em V014**. As autoridades de segurança permanecem aplicáveis até aprovação formal. Fonte principal: doc 150 §20.10; matriz de capabilities doc 160.

**Nenhum runtime foi alterado por este registro documental.**

## 6. Evidência de execução Cursor — 09/11/2026 (pós-integração desta branch)

**HEAD de execução:** `ebd0a3533d` (main) + integração documental desta branch.  
**Veredito desta fatia:** `DECISION_REQUIRED` — cutover conversacional **não** ativado.

### 6.1 Fronteira Core × CLARA (PROVEN no código)

| Camada | Owner | Evidência |
|---|---|---|
| Effective permissions / RBAC | Core via `delpi_auth.authz_core.has_permission` | `authz.py`, `tool_bridge._mcp_identity` / `_is_manage` — permission codes `controllership-finance.access\|manage\|access.dre` |
| Resource scope / ownership / business_rule | BFF CLARA | repositórios canônicos + `governed_writes` gates + OCC/read-back |
| Consentimento de operação sensível | BFF (`clara_consent_challenge` V014) | distinto de AuthZ Core; **não** é RBAC duplicado |

Nenhum catálogo local de roles/permissions substitui a Core. V014 permanece prova de **consentimento do plano**, não de permissão de produto.

### 6.2 Gate §20.10 — busca de aprovação formal

| Campo | Resultado |
|---|---|
| `SECURITY_PLATFORM_DECISION` | **AUSENTE** em Git (docs 124/150/161 e branch PO) |
| `CONTROLLADORIA_DECISION` (risco operacional residual TÉO) | **AUSENTE** |
| `CLARA_CONVERSATIONAL_SECURITY_ACK` em produção | `''` (vazio) |
| `CLARA_CONSENT_CHANNEL` em produção | `portal` (default) |
| `portal_consent_required` | `true` |
| `conversational_act_armed` | `false` |
| `CLARA_HOST_ATTESTATION_SECRET` | não configurado (`HOST_ATTESTED` = NOT_CONFIGURED) |
| Tabela V014 `clara_consent_challenge` | presente |

**STOP aplicado:** ack/conversational **não** habilitados; página `clara-consent` permanece obrigatória no CURRENT_RUNTIME. UX PO e fronteira Core ficam registradas; substituição de V014 aguarda texto mínimo do §20.10.

### 6.3 O que já está pronto (código) vs o que falta

| Item | Estado |
|---|---|
| Contrato TÉO (`proposal_pending_confirmation` + `confirmation`) | `IMPLEMENTED` (`2444de3378`, `23d51e7af5`) |
| Schema `get_context` alinhado ao canal | `IMPLEMENTED` |
| Migration V020 (`MCP_CONFIRMATION` em lote) | `DEPLOYED` |
| Inventário 48 capabilities | [doc 160](./160-cf-ux-053-capability-channel-inventory-2026-11-09.md) |
| Cutover produtivo sem Portal | `BLOCKED` — §20.10 |
| Smoke ChatGPT sem `confirmation_url` | `TEST_NOT_RUN` |

### 6.4 Próxima ação exclusiva dos owners

Colar e assinar em doc 150 §20.10 + doc 124 §8:

```text
SECURITY_PLATFORM_DECISION: ACCEPT_TEO_RESIDUAL | REQUIRE_HOST_ATTESTED | KEEP_V014
CONTROLLADORIA_DECISION: ACCEPT_OPERATIONAL_RISK | REJECT
ACK_VALUE_IF_ACCEPT: R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED
DATE / ACTOR / EVIDENCE_REF: …
```

Somente após `ACCEPT_*` o Cursor pode armar o canal, republicar schema e executar smoke ChatGPT com `portal_consent_required=false`.

## 7. Atualização da autoridade operacional — decisão expressa do PO / responsável pela área (09/11/2026)

A informação de §6.2 sobre `CONTROLLADORIA_DECISION = AUSENTE` é **histórica e foi superada**: o solicitante identificou-se como **PO, desenvolvedor/coordenador único e responsável pela área** e autorizou expressamente substituir o fluxo obrigatório V014 pelo padrão TÉO da CLARA, com aceite do risco operacional da Controladoria. Registro canônico em [doc 150 §20.16](./150-plano-unico-correcao-integral-portal-ux-funcional-2026-11-02.md) e política doc 124 §10.

**Não reabrir UX ou risco operacional com esse PO.** A competência separada de Segurança/Plataforma não foi demonstrada pela autodeclaração de responsabilidade da área; não forjar sua aprovação. A documentação é decisão de TARGET, não prova de cutover: no último smoke `portal_consent_required=true`, canal `portal`, `conversational_act_armed=false`.


## 8. Implementação técnica da decisão PO — R-CLARA-01 V2 (09/11/2026)

**Atualização sobre §6.4:** o requisito anterior de `CLARA_CONVERSATIONAL_SECURITY_ACK=R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED` foi **removido no código do produto**. A implementação não grava `security_ack=true` e não declara assinatura inexistente de Segurança/Plataforma. O aceite de risco operacional está no doc 150 §20.16. Política atual detalhada no [doc 124 §11](./124-clara-write-execution-risk-policy.md). §§1–7 preservam inventário e histórico, não devem ser confundidos com o contrato atual.

**Contrato de canal:** servidor em `portal` (default), `dual` ou valor inválido exige step-up V014; seleção explícita `CLARA_CONSENT_CHANNEL=conversational` habilita confirmação TÉO em `phase=commit` (single) ou `batch.phase=confirm` (lote), vinculada a ator, proposta/plan_hash e confirmação explícita. Core continua resolvendo permissions; BFF revalida scope/ownership/business_rule, OCC, TTL, idempotência, auditoria e read-back. Esta alteração altera a garantia de consentimento: o sinal MCP não é atestação independente do usuário, risco conhecido e aceito pelo owner operacional.

**Código:** `consent_channel.py`, `config.py`, `governed_writes.py`, `batch_orchestrator.py`, documentação em `semantic_bridge.py`; testes `test_clara_consent_channel.py`, `test_clara_consent_channel_integration.py`, `test_clara_semantic_operations_consent_channel.py`, `test_clara_mcp_surface.py`; runbook de consentimento atualizado. Portal do PR #148 consulta política efetiva da BFF. Nenhuma alteração de Core RBAC ou migrations históricas.

**Gate de entrega:** `TEST_NOT_RUN` e `NOT_DEPLOYED` nesta sessão de GitHub connector. Cursor deve executar testes, migrador/check de banco V020 já aplicado, deploy com `CLARA_CONSENT_CHANNEL=conversational` (não usar ack legado), restart MCP, consulta autenticada a policy, atualização de plugin se cache, e smoke PREPARE → confirmação explícita → ACT → audit/read-back em recurso de teste. Se testes falharem, rework antes de ativar; se o ambiente não puder ser alterado, reportar falha concreta, não reabrir o aceite de Controladoria. Não publicar V2 real nem inativar V1 como smoke.
