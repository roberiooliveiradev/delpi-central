# E6 — Decisão de produto: duas leituras do histórico monetário MOD

> **Data:** 2026-10-23 · **Processo:** PROC-0072 — Gestão do Fechamento Mensal da Controladoria · **Produto:** Portal Controladoria & Finanças · **Natureza:** registro documental de decisão, sem autorização de implementação.

## 1. Decisão expressa

**E6 = OPÇÃO C — AMBOS.** O responsável escolheu apresentar **duas leituras distintas** dos indicadores monetários da mão de obra direta (MOD):

1. **Histórico homologado da competência:** valor e evidências preservados conforme o fechamento aprovado, com identidade da competência, filial, versão, rate aplicado, origem, momento e responsável pelo aceite.
2. **Resultado recalculado corrente:** valor derivado dos dados operacionais sob o custo-hora cadastral vigente na consulta, identificado explicitamente como recalculado e potencialmente variável.

**Classificação:** `APPROVED / PRODUCT_DIRECTION_ONLY` e `TARGET / REQUIRES_DETAILING_AND_OWNER_VALIDATION`.

A escolha **não é GO de implementação**, não autoriza novos contratos, tabelas, migrations, APIs, UI, jobs, alteração na view ou runtime e **não promove gates** do documento 47. A aprovação dos critérios concretos, do responsável pela homologação e das fontes históricas permanece pendente. Não declarar uma política de congelamento existente por este registro.

## 2. Evidências que motivam a decisão

- Documento 80 §§22–25: `vw_Apontamentos_Eficiencia` apresenta `VALOR_MOD_HORA` consistentemente associado a `SBZ010.BZ_CUSTD` por produto MOD e filial; quatro produtos da filial 02 não tinham rate nem cadastro SBZ no recorte.
- Paridade matemática observada em 85.904 linhas de 2026 com rate não nulo: `TEMPO_GANHO_PERDIDO_HORAS = TEMPO_PREVISTO_HORAS - TEMPO_REAL_HORAS`; `RESULTADO_MOD = TEMPO_GANHO_PERDIDO_HORAS * VALOR_MOD_HORA`; `LUCRO_MOD = MAX(RESULTADO_MOD, 0)`; `PREJUIZO_MOD = MAX(-RESULTADO_MOD, 0)`.
- Auditoria `SBZ010_TTAT_LOG`: alterações cadastrais de `BZ_CUSTD` por `MATA019` em outubro de 2026, posteriores à competência de setembro de 2026. A view observada apresenta custo corrente inclusive em apontamentos antigos, evidência de revalorização retrospectiva na consulta.
- Demonstração de impacto em **subconjunto** de produtos MOD alterados em outubro, competência setembro/2026: filial 01 `+R$489,72` (resultado atual `+R$5.918,90` vs estimativa por rate anterior `+R$5.429,18`); filial 02 `-R$2.465,53` (atual `-R$32.694,32` vs anterior `-R$30.228,79`). **Não generalizar** ~8–9% para toda a filial, todos os meses ou todo o histórico.
- O log observado inicia em **27/04/2026**; DDL da view permanece indisponível/criptografada. Esses limites impedem declarar histórico completo ou implementação produtora integralmente comprovada.

**Proveniência de investigação:** [Documento 80 — §§23–25](./80-ciclo2-registro-vivo-investigacao-devin.md), commits `f7c899fffef6193b0accb8834e7a80a8aa7d08fd`, `f95c7213eb74c84d7cc91ffd8363d02eec545450` e `4577c8c5e4fbe3c5b7e474652335fb056d8c0680`. Evidência do Ciclo 2, não homologação G6.

## 3. Semântica e proveniência obrigatórias — TARGET

| Campo lógico | Histórico homologado | Recalculado corrente |
|---|---|---|
| Competência e escopo | Competência, empresa/filial, produto MOD, fonte, unidade e filtros congelados | Mesma competência/escopo explicitados; identificar filtros que diferirem |
| Horas e resultado | Horas previstas/reais, delta e resultado utilizados no aceite; valores e granularidade homologados | Horas e delta obtidos na consulta; resultado pela regra demonstrada, sujeito a mudanças da fonte |
| Rate | Valor-hora **efetivamente utilizado no fechamento**, sua data de vigência, origem e evidência | `BZ_CUSTD` corrente ou rate retornado pela view, com instante da consulta |
| Identidade temporal | `closed_at`, `approved_at`, versão da evidência e `as_of` do rate, quando disponíveis | `calculated_at`/`queried_at` e versão de fonte quando disponíveis |
| Aprovação | Owner e evento humano real, evidência preservada e rastreável | Nunca rotular como aprovado apenas por cálculo/HTTP 200 |
| Status visível | Homologado, pendente, indisponível ou parcial, conforme evidência | Recalculado e data/hora de referência |
| Diferença | Comparável apenas com mesmo escopo, granularidade, moeda, versão das horas e período | Variação absoluta e relativa com denominadores definidos; sinal conservado |

Esse quadro define **informações que o detalhamento deve resolver**, não novos campos aprovados de DTO ou esquema físico.

## 4. Critérios de aceite propostos (AC-E6) — pendentes de homologação

- **AC-E6-01 — Duas leituras distintas:** quando ambas as fontes estiverem comprovadas, exibir histórico homologado e recalculado com rótulos inequívocos; não substituir um pelo outro.
- **AC-E6-02 — Imutabilidade e trilha humana:** um valor só pode receber o rótulo *homologado* após evento de aprovação humana real, com owner, competência, escopo, data, artefato/versão e trilha auditável; alterações posteriores ao rate não reescrevem a evidência homologada.
- **AC-E6-03 — Recalculo identificável:** resultado corrente deve registrar `as_of` da consulta e rate aplicado; não pode ser apresentado como número originalmente homologado.
- **AC-E6-04 — Paridade e precisão:** validar a fórmula e agregação pelo grão do relatório oficial (filial, competência, produto/OP conforme artefato), preservando sinais, nulos, moeda, tolerância de arredondamento e valores de lucro/prejuízo; exigir amostra oficial homologada antes de PASS.
- **AC-E6-05 — Comparação justa:** diferença histórica × atual apenas quando período, escopo, horas e filtros forem comparáveis; caso contrário, estado `INCONCLUSIVE` e razão visível, sem percentual artificial.
- **AC-E6-06 — Rate ausente:** produto sem `BZ_CUSTD` ou com rate NULL não é igual a rate zero; diferenciar explicitamente *ausente*, *zero cadastrado*, *não aplicável* e *não comprovado*; não inventar custo.
- **AC-E6-07 — Histórico incompleto:** antes de 27/04/2026 ou para lacunas sem cadeia de mudanças auditável, não inferir rate vigente com base apenas no cadastro atual. Exibir *histórico não comprovado* e permitir evidência histórica externa validada pelo owner, sem backfill fictício.
- **AC-E6-08 — Cutoff e republicação:** definir quem fecha, quando congela, como tratar reabertura/correção e se versões homologadas coexistem. Cada versão deve permanecer rastreável; não sobrescrever ou reclassificar automaticamente um fechamento humano.
- **AC-E6-09 — Segurança e boundary:** acesso somente segundo `controllership-finance.access`/`manage` mais resource scope/ownership/regra de negócio na BFF; browser não acessa `api-delpi` nem tabelas TOTVS diretamente. Nenhuma nova permission.
- **AC-E6-10 — Proveniência e testes:** evidência de producer e consumer, contrato validado, testes de paridade e de regressão de revalorização pós-`MATA019`, nulos, histórico truncado, cancelamento/reabertura e isolamento por filial; ausência de teste = `TEST_NOT_RUN`, nunca PASS.

Todos os AC acima são **TARGET / DRAFT**, não `PASS` e não alteram o ledger 23 nem os critérios G1–G6 do tracker 47.

## 5. Tratamento do histórico incompleto

1. **Até 26/04/2026:** nenhuma garantia de rate por competência baseada no TTAT disponível. Uma linha antiga exibida hoje com `BZ_CUSTD` corrente deve ser classificada como *recalculada corrente*, não *valor homologado histórico*.
2. **A partir de 27/04/2026:** reconstrução por auditoria é **condicional**, por filial/produto, ao estado inicial conhecido, sequência completa de alterações, eventos de inclusão/exclusão e cobertura auditada. Data inicial do log não é prova automática de completude.
3. **Valor homologado sem rate histórico recuperável:** se existir evidência original assinada/aprovada do fechamento, preservar seu valor e registrar a proveniência e o rate desconhecido sem recalcular silenciosamente. Se não existir, mostrar **indisponível / não homologado**, nunca converter a estimativa em homologação.
4. **Rate corrente ausente ou nulo:** o recalculado deve indicar indisponibilidade ou cálculo parcial conforme contrato a decidir; não usar `0` como fallback.
5. **Mudanças retroativas:** preservar snapshots homologados e versões/correções humanas; calcular a leitura corrente em separado. Comparação pode ser desabilitada quando faltarem dados comparáveis.
6. **Backfill:** somente com fonte oficial identificada, validação e decisão do owner; o registro não autoriza tabelas, dados artificiais ou escrita retroativa.

## 6. Decisões de detalhamento ainda necessárias

| ID | Responsável candidato | Escolha pendente |
|---|---|---|
| E6-D1 | Controladoria | O que constitui o **valor homologado**: relatório oficial, pacote do fechamento ou outro artefato; grão e moeda |
| E6-D2 | Controladoria + TI/ERP | Definição do cutoff, versões, correções, reaberturas e momento de congelamento |
| E6-D3 | TI/ERP + DBA | Fonte e confiabilidade de rate por competência, logs, DDL da view e eventuais artefatos históricos |
| E6-D4 | Product owner + arquitetura | Owner da persistência de evidências, retenção, contratos, DTOs e integrações; **nenhum definido por este documento** |
| E6-D5 | Controladoria | Tolerâncias monetárias, rótulos, comparação de variação e aceites por competência e filial |
| E6-D6 | Segurança/owner | Escopo e propriedade da competência, acesso às evidências e auditabilidade conforme normas canônicas |

**Handoff:** E6 conforme [Documento 80 §25.D](./80-ciclo2-registro-vivo-investigacao-devin.md), acompanhado por E3 (DDL das views). TÉO permanece authority AS-IS e o repositório authority TARGET. Revisar requisitos canônicos e contratos vigentes antes de detalhar ou implementar.

## 7. Gate e efeitos

- `E6_OPTION = C` — **APPROVED / PRODUCT_DIRECTION_ONLY**.
- `E6_ACCEPTANCE_CRITERIA = TARGET_DRAFT / PENDING_OWNER_VALIDATION`.
- `E6_PROVENANCE = PARTIAL`; `HISTORICAL_COMPLETENESS = INCONCLUSIVE`.
- `DECISION_REQUIRED` para E6-D1..D6.
- `IMPLEMENTATION_AUTHORIZED = NO` para esta decisão.
- `DOCUMENT_47 = NO_GATE_CHANGE`; `TESTS = TEST_NOT_RUN`.
- Nenhuma alteração em código, contratos, jobs, runtime, permissões, migrações ou governança da plataforma.

> **Registro da escolha solicitado pelo usuário:** opção C. O detalhamento e a homologação permanecem a cargo dos owners competentes.
