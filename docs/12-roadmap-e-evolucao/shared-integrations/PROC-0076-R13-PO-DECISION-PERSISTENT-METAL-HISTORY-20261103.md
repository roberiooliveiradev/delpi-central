# PROC-0076.R13 — Decisão do Product Owner: persistência histórica obrigatória (2026-11-03)

**Status:** requisito do produto APPROVED; ativação produtiva MetalCharts PENDING por direitos e conectividade.

## Decisão inequívoca

Em 03/11/2026, o Product Owner reiterou expressamente: **é para persistir sim as cotações coletadas na tabela histórica, não somente manter cache temporário**. Uso interno DELPI, usuários autenticados, sem revenda nem redistribuição. Esta é decisão funcional definitiva, não hipótese.

- PRODUCT_OWNER_AUTHORIZATION = APPROVED
- PURPOSE = INTERNAL_MARKET_INTELLIGENCE
- TARGET_RETENTION = PERMANENT
- TARGET_REFRESH = DAILY, uma consulta lógica diária conforme data real publicada
- REDISTRIBUTION = FORBIDDEN
- CACHE_ONLY_AS_FINAL_PRODUCT_SOLUTION = REJECTED

Não aceitar TTL cache como cumprimento do histórico permanente. Falhas na coleta não podem eliminar observações legitimamente retidas.

## Ownership e contrato

- external-data-api: owner de fonte, direitos, ingestão e persistência no PostgreSQL external_data. Usar metal_quote_observations e migrations vigentes; não criar banco duplicado.
- supplies-api: composição e AuthZ server-side. plugins/supplies: apresentação; nunca escrever série histórica no MFE.
- Observações por fonte, instrumento, basis/tipo de cotação, unidade e data de referência, com valor e proveniência; upsert idempotente, concorrência, revisões auditáveis, sem apagar datas anteriores.
- Não representar spot/intraday last como close/settlement. Scheduler fora do request, lock e budget, sem upstream por refresh de página.

## Estado técnico e evidências

- R10: cache expirou, scheduler anteriormente ausente, bloqueio Sophos api.metalcharts.org; cron operacional foi implementado.
- R11: feed metals-prices-daily, endpoint /v1/prices/ e roteamento permanent/ttl_cache; custo estimado ~31 weight/mês, sujeito a prova real.
- R12: filtro por source_id, roteamento metals-daily por retenção e freshness por tabela; seis testes PG reais descartáveis PASS; nenhuma cotação MetalCharts permanente provada em produção.
- Snapshot R12: 198 registros históricos Pink Sheet, 0 MetalCharts permanentes, 0 cache vigente; egress bloqueado. Revalidar antes de afirmar estado atual.

## Gates independentes — não confundir autorização com licença

**Produto:** APPROVED, alvo obrigatório de retenção permanente e atualização diária.

**Fonte MetalCharts Free:** PROVIDER_PERMANENT_STORAGE_RIGHT = PENDING na matriz de direitos PROC-0076-SOURCE-RIGHTS-EVIDENCE-20261027.md, seções 5 e 7. O escopo registrado tem store_cache_only, não store. Uso interno sem redistribuição não comprova automaticamente direito de arquivamento permanente.

Não alterar scope para store, não transformar ttl_cache em permanent, não copiar cache antigo nem remover rights guard sem evidência contratual de retenção. Solicitar confirmação escrita/licença do provedor ou homologar outra fonte de histórico com direito comprovado. A pendência do fornecedor **não** significa ausência de autorização do PO.

## Plano de ativação, dependências e sequência

1. S0 Rebaseline: HEAD, git status, authorities, .cursor aplicáveis, migrations, contratos, bindings, código de ingestão, runtime e direitos. Registrar drift e owner.
2. S1 Fonte/direitos: evidência escrita/licença de retenção interna permanente ou fonte alternativa autorizada; registrar decisão/versionamento na matriz de direitos. Se não houver, parar a ativação MetalCharts.
3. S2 Rede: TechMaster comprova egress HTTPS e cadeia TLS confiável para a fonte, sem bypass; verificar resposta real e data do provedor.
4. S3 Contrato: validar /v1/prices/, símbolos HG/ALI/NI/ZN/PB, semântica *_last, peso e budget, UTC/timezone, horário de publicação, no-new-reference.
5. S4 Política: quando direito store estiver PROVEN, propor migration aditiva e auditável para observation_retention=permanent e allowed_use_scope com store, somente na fonte autorizada; definir rollback operacional, sem modificar outras fontes.
6. S5 Ingestão: realizar coleta real controlada pelo job existente; comprovar INSERT/UPSERT em metal_quote_observations por source_id, instrumento e data de referência; idempotência, preservação de históricos e ledger.
7. S6 Consumo: verificar external-data-api → supplies-api → plugins/supplies com autenticação e unidade, períodos 30d/90d/12m/24m/36m; validar último dado, cobertura, basis e unidade.
8. S7 Operação: provar ao menos um agendamento automático de produção e tratamento de falha sem perda do histórico. Resolver healthcheck de scheduler não-HTTP e teste legado R2 se ainda inconsistentes.

## Critérios de aceite

- AC-01 Decisão do PO registrada como APPROVED, não PENDING.
- AC-02 Direito store da fonte selecionada comprovado; sem direito, guarda fail-closed.
- AC-03 Cotação real persistida por data do provedor em PostgreSQL histórico.
- AC-04 Repetição idempotente, nova data preserva a anterior; revisões auditáveis.
- AC-05 Sem chamada ao fornecedor por usuário; scheduler diário com lock e budget.
- AC-06 Falha de fonte não apaga histórico licenciado; frescor informado honestamente.
- AC-07 Isolamento de source_id, sem mistura Pink Sheet e MetalCharts.
- AC-08 BFF efetivo e gráficos autenticados retornam dados reais, fonte e unidade.
- AC-09 Logs sem segredos, TLS válido, evidência e rollback documentados.

## Classificação formal

PO_PERSISTENT_HISTORY_REQUIREMENT = APPROVED
R12_PERSISTENCE_CODE_PATH = PROVEN (verificar HEAD atual)
METALCHARTS_STORE_RIGHT = PENDING (até documento comprobatório)
TECHMASTER_EGRESS = PENDING (última evidência; revalidar)
PRODUCTION_METALCHARTS_PERSISTENT_HISTORY = PENDING

Não declarar PASS do produto enquanto a fonte não tiver licença comprovada, a coleta real não estiver gravada e o gráfico autenticado não tiver sido verificado.

## Referências

- [Matriz de direitos](./PROC-0076-SOURCE-RIGHTS-EVIDENCE-20261027.md)
- [R10](./PROC-0076-R10-SCHEDULER-RIGHTS-AND-EGRESS-EVIDENCE-20261029.md)
- [R11](./PROC-0076-R11-DAILY-QUOTES-EVIDENCE.md)
- [R12](./PROC-0076-R12-PERSISTENT-METAL-QUOTES-EVIDENCE.md)

READ → VERIFY → CLASSIFY → DECIDE → IMPLEMENT MINIMAL DIFF → TEST → VERIFY OUTCOME → DOCUMENT → REPORT.