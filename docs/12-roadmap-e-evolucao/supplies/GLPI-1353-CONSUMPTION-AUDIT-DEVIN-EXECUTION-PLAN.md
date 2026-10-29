# GLPI #1353 — Plano Devin: rotas api-delpi → supplies-api

> Estado: PLANNED / NOT_AUTHORIZED_FOR_IMPLEMENTATION — 2026-10-29.
> Baseline remoto verificado: main = 925e4cbd40e44600183f2bef693d4fec118258bb. Workspace/local git status do Devin NÃO verificado.
> Plano de execução condicional, não substitui contrato freeze nem autoriza criar rotas, commits funcionais ou deploy.

## 1. Authorities e referências

- Instruções oficiais GPT, regras .cursor globais e especializadas por responsabilidade, ADR-009, código no HEAD, testes atuais; planos e docs abaixo são subordinados.
- [D1 fluxo e dados](./GLPI-1353-PRODUCTION-CONSUMPTION-AUDIT-FLOW-20261029.md).
- [D2.1 regras propostas](./GLPI-1353-CONSUMPTION-AUDIT-BUSINESS-RULES-D2.md).
- [D2.2 contratos propostos](./GLPI-1353-CONSUMPTION-AUDIT-CONTRACTS-D2.md).
- [Matriz de boundaries](./MATRIZ-BOUNDARIES.md), [roadmap](./README.md), [plano geral](./IMPLEMENTATION-PLAN.md), [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md).
- Ler development-standards-index, evidence-driven-execution, centralized-rules-first, clean-code-architecture-guardrails, english-code-identifiers, plan-construction, plan-execution, test-and-commit e regras de API, segurança, Protheus/SQL relevantes. Não carregar todo o catálogo .cursor.

## 2. TASK / GOAL / owners

**TASK:** preparar e, após gates/autorização explícita, implementar/testar o producer de evidências na api-delpi e as rotas BFF Flask na supplies-api; a primeira execução do Devin é P0 READ-ONLY.

**GOAL:** prover conciliação auditável por filial × OP × operação × componente, sem afirmar furo físico, sem confundir empenho SD4 com movimento líquido SD3 e sem somar transferência ou MO como consumo MP.

**OWNER:** api-delpi = SQL TOTVS, BOM histórica, apontamentos, empenhos, classificação e cálculo canônico. supplies-api = Core-first AuthZ, escopo, gateway HTTP, composição e eventuais estados próprios. MFE = UX, não neste plano. Core = effective permissions. Não criar microsserviço, import entre domain/application ou mirror TOTVS.

## 3. Estado verificado e riscos

- D0 ACCEPT_WITH_RESIDUAL; D1 INCONCLUSIVE para vínculo evento operação → baixa automática; D2.1/D2.2 DRAFT e NOT FROZEN. GLPI #1353 não é E12 (E12 = consumo produto × período), portanto não mudar sua rota.
- D0 encontrou /production/* e /products/* sem trusted-BFF apropriado; a opção preferida, ainda PROPOSED, é producer dedicado /supplies/consumption-audit/* com S2S seguro, sem ampliar acesso genérico.
- README recente registra residual de smoke federado E11. A fila e autorização de nova página devem ser revalidadas antes de qualquer UI; UI/manifest/deploy estão fora deste plano.
- Exemplo real 01/24884201006: SC2 0,125 planejado e C2_QUJE=0; SH6 H6_QTDPROD=0,125 tipo P (sem reconciliar ambos silenciosamente). SH8 ops 01 CT-23 e 02 CT-35 (cadastro não prova execução).
- Op 01 cabo 10010030: SG1 teórico preliminar 80,75 MT; SD4 80,75 original/0 em aberto/80,75 derivado; SD3 80,75 consumo elegível. Movimento adicional 0,64 MT é TRANSFERÊNCIA inbound, NÃO consumo; não usar 81,39 como consumo.
- Op 02 terminal 10080329: SG1 preliminar 250 PC; SD4 250 original/250 em aberto/0 derivado; sem baixa na consulta. NÃO declarar falha sem execução comprovada.
- MOD216 = MO em HR, 0,233 HR, não matéria-prima. Documento 220039841 possui movimentos de outra OP; nunca correlacionar por documento sozinho. OP 24884201002 vinculada por D4_OPORIG; prevenir dupla contagem.

## 4. Blockers para o GATE-D2

| ID | Evidência/decisão exigida | Owner |
|---|---|---|
| G2-01 | Execução real por operação (SH6/HZA) e nexo causal com baixa automática | PCP/Protheus + api-delpi |
| G2-02 | SH6 0,125 versus SC2 C2_QUJE 0; quantidade e data de referência | PCP/Protheus |
| G2-03 | Retornos, estornos, reclassificação, TM/CF e cálculo SD3 líquido versus SD4 derivado | PCP + api-delpi |
| G2-04 | BOM vigente na OP, substituições e conversões de UM/arredondamento | PCP + api-delpi |
| G2-05 | D4_OPORIG, OPs relacionadas, documentos de múltiplas OPs, C2_PRIOR=500 | PCP + api-delpi |
| G2-06 | Tolerâncias, severidade, momento dos alertas e aceites A–F; inventário G futuro | Joici/Michael |
| G2-07 | Schemas/OpenAPI finais, policy de recurso, S2S trusted caller e compatibilidade | api-delpi/supplies-api/Security |
| G2-08 | Prioridade do #1353 distinta da E12 e gate de página E11 | Product Owner |

**STOP CONDITION:** se falta dado que determine cálculo/alerta/status ou se existir conflito de owner/contrato, registrar EXECUTION_DRIFT ou INCONCLUSIVE e pedir decisão. Não inventar defaults ou implementar classificação especulativa.

## 5. RQ / AC e critérios de verificação

| RQ | Aceite |
|---|---|
| RQ-01 | Identidade filial 01/02 + OP com zeros à esquerda + operação + componente + unidade |
| RQ-02 | Três medidas separadas: teórico SG1, SD4 original/saldo/derivado e SD3 classificado |
| RQ-03 | SH8 não é prova de execução; ausência de status real gera unknown/inconclusive, não erro |
| RQ-04 | Transferência 0,64, MO, retorno, estorno e docs compartilhados não contaminam consumo |
| RQ-05 | Core effective permissions; supplies.access leitura, manage não implica access; fail-closed; nenhuma permission nova |
| RQ-06 | Producer e BFF têm contrato compartilhado verificável, sem regra TOTVS duplicada no BFF |
| RQ-07 | Paginação/limites e erros 400/401/403/404/422/502/503/504 conforme freeze; sem N+1 |
| RQ-08 | Zero write ERP, zero mirror PG, E12 intacta, sem UI/manifest/D6/deploy |
| RQ-09 | Testes positive + sibling + negative + contrato + runtime quando disponível |

## 6. Etapas atômicas (NÃO avançar automaticamente)

### P0 — READ-ONLY rebaseline e inventário (PRIMEIRO COMANDO)

Registrar HEAD, origin/main, branch e git status sem fazer pull/fast-forward/checkout/reset. Inspecionar autoridades, regras .cursor, código, teste, schemas/OpenAPI e consumer/producer atuais. Verificar as capacidades /production, /products, /supplies, SuppliesDelpiReads, DelpiApiGateway e policies. Confrontar D2 proposto versus código HEAD, identificar schema real de operação, segurança e gaps de dados. Devolver matriz G2-01..08 com PROVEN/TO_INVENTORY/EXECUTION_DRIFT e menor plano corrigido. GATE-P0: GPT revisa; sem escrita ou commit.

### P1 — Homologação e contract freeze (DOCUMENTAL)

Com decisões PCP/Joici/Michael, Security e PO, escolher recorte MVP mínimo: priorizar C2 detalhe OP se compatível; C1 lista e C3 consulta inversa ficam independentes. Definir filtros, paginação, data de referência, status de execução, conversões, estornos, completude, identidade de evidência, esquema/decimal, erros e noção de reanálise. Criar contract freeze versionado/OpenAPI no owner, com testes planejados. GATE-D2: ainda PENDING até aprovações explícitas. Não implementar rotas durante freeze.

### S1 — Producer api-delpi (somente após D2 aprovado e GO explícito)

Implementar C2 PROPOSED GET /supplies/consumption-audit/orders/{op} com adapters e use case de leitura; preservar classificador SD3 canônico, SG1 histórica, SD4 por operação e evidência; status unknown em inconsistência. Validar trusted-S2S via caminho já aprovado em /supplies sem expor amplamente /production e /products. TDD positivo OP referência; negativo spoof de caller, falta de token, falta de scope, estornos, UM, D4_OPORIG, documentos com OP diferente e dados incompletos. Provar OpenAPI e compatibilidade; GATE-S1.

### S2 — BFF supplies-api (somente após S1 aprovado)

Implementar gateway explícito para C2, adapter/serviço, policy Core-first e Blueprint Flask GET /consumption-audit/orders/{op} (prefixo final sujeito ao padrão atual). Validar filial 01/02, OP e escopo de recurso, permission supplies.access efetiva, manage-only sem access, Core indisponível fail-closed. Preservar erro/status, timeouts, resposta parcial, logs sem tokens e dados sensíveis. Testes unit/mock de producer, contrato producer-BFF e integração HTTP real em ambiente autorizado. GATE-S2.

### S3 — Lista paginada C1 (depois S2; GO específico)

Adicionar GET /supplies/consumption-audit/orders no producer e GET /consumption-audit/orders no BFF com data-base de período homologada, paginação bounded, sorting estável, sem fan-out por OP×componentes. Testar 01/02, bordas de período, filtros, latência e sem regressão E12. GATE-S3.

### S4 — Consulta inversa C3 (opcional; GO específico)

Implementar apenas se caso de uso demonstrado e performance/contrato aprovados: /supplies/consumption-audit/components e projeção BFF; testar cardinalidade e acesso. GATE-S4.

### S5 — Verify final de producer↔BFF (somente escopos executados)

Pytest, lint/typecheck/format aplicáveis, OpenAPI/DTO-diff, contrato e testes de HTTP autenticado; 01/02, deny de manage-only/no-access, spoofed S2S, Core outage, downstream 502/504, retorno/estorno, docs multi-OP, BOM histórica. Residual search por SQL BFF, uso direto /production, permissions novas, dados TOTVS no PG, chamadas MFE diretas, E12 alterada. Sem runtime, reportar INCONCLUSIVE, jamais PASS inferido. Não confundir gate backend com smoke federado de futura UI.

## 7. Matriz de teste mínima

| Tipo | Cenário | Prova |
|---|---|---|
| Positive | 24884201006/01; cabo 80,75 e transferência 0,64 | Consumo = 80,75, transferência excluída |
| Positive | Operação 02 com SD4 saldo 250 | não gerar acusação automática |
| Positive | MOD216 em HR | não soma com MP |
| Sibling | 24884201002 vinculada por D4_OPORIG | sem duplicidade |
| Sibling | mesmo documento, outra OP | separação por filial+OP+item |
| Sibling | outra vigência SG1/UM | versão e conversão explícitas |
| Negative | estorno/retorno parcial ou classe desconhecida | resultado conservador/unknown |
| Negative | SH6 apontada com SC2 0 | conflito comunicado, não fecha OP artificialmente |
| Negative | 01/02, OP de filial diversa, branch inválida | rejeitar sem vazamento |
| Negative | sem access, manage-only, Core offline, caller spoof | fail-closed |
| Integration | BFF + api-delpi reais (ambiente autorizado) | schema/códigos/latência/S2S; senão INCONCLUSIVE |

## 8. Forbidden scope e governança de commits

Não: nova página/manifest/MFE/Help; no deploy; migration/investigações D6; writes ERP; service novo; autorização por JWT claim; permissões por CRUD/unidade; SQL/cálculo TOTVS no BFF; alterar E12; usar /me/routes; tokens em docs/logs; ajustar teste para esconder erro. Um estágio por vez, com evidências no GitHub e commits apenas quando a etapa de implementação for explicitamente autorizada. O próprio plano não autoriza S1–S5.

## 9. Relatório obrigatório para Devin

BASE HEAD / FINAL HEAD / ORIGIN MAIN / BRANCH / GIT STATUS; STATUS; FACTS PROVEN; TO_INVENTORY; EXECUTION_DRIFT; FILES INSPECTED/CHANGED; CONTRACT IMPACT; SECURITY CHECKS; TESTS com comandos/resultados; RQ/AC COVERAGE; POSITIVE/SIBLING/NEGATIVE; RESIDUAL SEARCH; POSTCONDITION/OUTCOME; UNRESOLVED; NEXT STEP. Resultado de revisão GPT somente ACCEPT / ACCEPT_WITH_RESIDUAL / REWORK / EXECUTION_DRIFT / INCONCLUSIVE.

## 10. Brief pronto para Devin: executar apenas P0

**TASK:** P0 READ-ONLY para o GLPI #1353 neste plano.
**GOAL:** comparar D1/D2 com HEAD e provar readiness técnica de producer api-delpi + consumer supplies-api.
**AUTHORITIES:** instruções oficiais, .cursor, ADR-009, fontes D1/D2, implementação real e testes.
**OWNER:** api-delpi dados/regras; supplies-api AuthZ/BFF; Core permissões.
**CURRENT_STATE:** D2 DRAFT, D1 parcial, nenhuma rota consumption-audit autorizada.
**EVIDENCE_REQUIRED:** HEAD/status, contratos realmente existentes, trust chain, dados e riscos, G2-01..08, testes existentes, proposta de menor dif.
**ALLOWED_SCOPE:** leitura de código/contrato/testes e consultas de dados somente quando previamente autorizadas e governadas.
**FORBIDDEN_SCOPE:** commit, mudança de branch/ref, code, schema, docs, SQL write, deploy, feature.
**ACCEPTANCE:** relatório com PROVEN/TO_INVENTORY/EXECUTION_DRIFT, cobertura e dependências.
**TESTS:** inventariar testes; não alterar nem simular execução.
**STOP_CONDITION:** autoridade divergente, mudança de ownership, dependência não homologada; interromper e reportar.
**RETURN:** relatório da seção 9; não executar P1/S1–S5 automaticamente.