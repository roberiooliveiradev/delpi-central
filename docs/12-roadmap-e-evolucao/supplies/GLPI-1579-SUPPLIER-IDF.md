# GLPI #1579 — Índice de Desempenho do Fornecedor

Referência: chamado #1579. Implementação: 16/11/2026.

## Decisões e critérios de aceite

O chamado solicita IDF = (Qualidade × 0,70) + (Entrega × 0,30), na mesma escala.
O solicitante confirmou manter a taxa atual de aprovação de Qualidade, incluindo
liberação urgente e laudo condicional. O chamado não define faixas nem metas:
nenhuma classificação A/B/C, boa/ruim ou meta arbitrária foi criada.

| Requisito | Implementação / aceite | Estado |
|---|---|---|
| RQ-01 — fórmula 70/30 | Índices 0–100; cálculo decimal sem arredondamento intermediário, nota com duas casas | ATENDIDO em testes |
| RQ-02 — fontes existentes | Views de inspeções e pontualidade; nenhuma escrita no ERP | ATENDIDO; consulta real somente leitura |
| RQ-03 — Portal Suprimentos | Análises → IDF dos fornecedores; rota, catálogo, busca e manifesto 0.5.3 | ATENDIDO no código / build |
| RQ-04 — objetividade e UX | Média, pesos, contagens, comparação, busca, cobertura, paginação e composição por fornecedor | ATENDIDO em testes de interação; inspeção visual pendente |
| RQ-05 — segurança | `supplies.access`, filiais 01/02, BFF obrigatória, chamadas diretas negadas | ATENDIDO em testes positivos/negativos |
| RQ-06 — sem nota inventada | Ausência de base ou inconsistência deixa IDF nulo e fora da média | ATENDIDO em testes |
| RQ-07 — publicação main | Commit, push e deploy canônico, preservando alterações concorrentes | Código preparado para main; deploy BLOQUEADO_COM_EVIDENCIA (rede indisponível) |
| RQ-08 — ajuda e evidência | Manual in-app, README, contratos e este documento | ATENDIDO no código |

## Cálculo e granularidade

| Componente | Fonte | Referência temporal | Denominador / numerador |
|---|---|---|---|
| Qualidade, peso 70% | `dbo.vw_minha_delpi_inspecoes_entrada_historico_tela` | `Data_Laudo` | Inspeções concluídas / aprovadas (`Eh_Aprovada=1`, situações 2, 4 e 5) |
| Entrega, peso 30% | `dbo.VW_PONTUALIDADE_FORNECEDORES` | `DT_DIGITACAO` | Linhas de recebimento / linhas no prazo ou antecipadas (`DIAS >= 0`) |

O escopo de produtos acompanha o OTD geral de Suprimentos: matéria-prima
(`B1_TIPO=MP`) **ou** família 3019. Não confundir com o indicador de pedidos
MP-only. A aprovação é por inspeção, não por quantidade de peças ou ensaios.
Recebimentos parciais podem gerar várias linhas e não são pedidos únicos.

Inspeções são deduplicadas por filial e `Id_Inspecao` antes da agregação.
Qualidade e Entrega são agregadas separadamente e unidas por código + loja,
sem join de fatos que multiplique contagens. Consolidar filiais soma contagens
antes das taxas; lojas distintas não são fundidas. As duas bases são eventos
independentes no período e podem ter contagens distintas.

Exemplo sintético: 8/10 inspeções aprovadas e 6/10 recebimentos no prazo geram
80 × 0,70 + 60 × 0,30 = **74,00**. Zero é uma nota válida. Sem uma das bases,
o índice disponível permanece visível, mas IDF fica sem nota. Flags de inspeção
conflitantes ou recebimento sem data válida também impedem uma nota completa.
Condicionais e urgentes aparecem separadamente no detalhe e contam como
aprovação conforme a decisão confirmada.

A média do painel é simples sobre fornecedores/lojas com IDF completo, sem
ponderação por volume. As médias dos componentes usam a mesma população.
Contadores totais de inspeções/recebimentos incluem toda a base selecionada,
inclusive fornecedores incompletos. A busca na tabela não altera os KPIs.

## Contratos, limites e operação

Fluxo: `plugins/supplies` → `supplies-api` → `api-delpi` → SQL Server TOTVS.
Ownership segue `MATRIZ-BOUNDARIES.md`: interpretação ERP na api-delpi; acesso
Core-first na BFF; UI sem recálculo de negócio. Nenhuma migração foi criada.

- UI: `/apps/supplies/analytics/supplier-performance`.
- BFF: `GET /analytics/supplier-performance`, operationId `get_portal_supplier_performance`.
- Interna: `GET /supplies/supplier-performance`, operationId `get_supplies_supplier_performance`.
- Filtros: `branch=01&branch=02`, `date_from=AAAA-MM-DD`, `date_to=AAAA-MM-DD`.
- Datas inclusivas, período crescente de até 367 dias. Sem filial: fail-closed.
- BFF delega token do usuário e headers internos pelo gateway canônico, com timeout existente.
- A rota interna exige autenticação e prova de caller `supplies-api`; token de usuário isolado não basta. O catálogo técnico não concede acesso.
- Sem polling: consulta inicial, alteração de filtros ou Atualizar. Cache canônico, TTL configurável (padrão 300 s), chave por filiais e período, singleflight por processo. Atualizar pode servir o cache ainda válido.
- Uma consulta SQL agregada por cache miss, até 5.000 grupos fonte. Overflow retorna erro pedindo menor recorte, nunca sucesso truncado.
- Erros de dependência/contrato retornam 502 seguro na BFF, nunca um indicador vazio de sucesso. Indicador sem movimento é um estado distinto.
- Telemetria SQL e cache usam owners existentes, operationId estável e request ID do gateway; não registrar tokens nem dados de fornecedores nos logs de erro novos.

## Evidências de validação

- SQL real: duas execuções mensais, duas filiais, **341,550 ms** e **334,232 ms** efetivos medidos em `sys.dm_exec_query_stats`; 41.825 leituras lógicas em cada amostra. A latência do conector foi maior e não foi confundida com tempo SQL. Sem alteração de índices; avaliar carga de períodos longos em produção antes de ampliar os limites.
- API: **37 testes selecionados aprovados**; testes de fórmula, arredondamento, lojas, filiais, zero, ausência, inconsistência, filtros, cache, falha de fonte, SQL parametrizado, overflow, autorização e rota HTTP/schema/meta.
- BFF: **105 testes selecionados aprovados**; acesso negado sem login/sem `supplies.access`/somente manage, todas as filiais validadas, filtros ambíguos, contrato inválido e erros sanitizados; regressões de fornecedores, overview, alçadas e gateway.
- MFE: **573 testes aprovados em 56 arquivos**, suíte existente + testes de navegação, escopo, busca e interação real do componente. Detalhe usa modal canônico contido no host; loading, empty, 403, 422, 502 e recuperação por Atualizar são exercitados.
- Build federado aprovado e lint de 17 arquivos alterados com 0 erros / 1 warning; CSS de domínio escopado, tokens claros/escuros, grid responsivo e tabela do kit. Não houve alteração no kit compartilhado.
- Inspeção visual em navegador: **TEST_NOT_RUN / ambiente**. Chromium abortou antes de renderizar (`socket() failed: Operation not permitted`); não há alegação de screenshot ou aceite visual em produção. Testes DOM não comprovam layout/contraste real.

Falhas externas já presentes no HEAD base `e18ee9a3`, preservadas:

- Lint geral do MFE: cinco erros em SessionContext, OtdAnalyticsPage, deliveries/query e userManual.structural.test; nenhum desses arquivos foi alterado.
- Suíte completa supplies-api: marcador de conflito já versionado em `tests/interface/suri_mcp/test_tool_bridge.py` e dependência local sem `mcp.server.mcpserver`. Não é alegado PASS da suíte completa.
- Gerador TV: baseline original tem 597 rotas armazenadas versus 585 geradas. A nova operação foi adicionada isoladamente com o gerador canônico, preservando entradas anteriores; paridade OpenAPI/TV passa. Não foi feita uma reconciliação destrutiva do catálogo.
- `sync_tv_data_param_catalog.py --check`: 46 enumLabels faltantes e drift anteriores em parâmetros alheios ao IDF. O IDF não adiciona nomes de parâmetros nem enums globais.

Responsabilidades materiais: arquitetura, segurança, contratos, dados, frontend,
qualidade, delivery e confiabilidade. Evidência acima distingue código/testes
de verificação visual, runtime e aprovação funcional ainda pendentes.

## Deploy, validação funcional e rollback

Serviços afetados: `api-delpi`, `supplies-api`, `supplies`. Não subir todos os
serviços do monorepo. Publicar não significa aceite funcional nem chamado solucionado.

```bash
cd ~/projetos/delpi-central
git pull --ff-only
./infra/scripts/up-prod-sequential.sh --build api-delpi supplies-api supplies
```

Registrar/atualizar o manifesto `plugins/supplies/supplies.manifest.json` no Core
pelo fluxo existente em `plugins/supplies/README.md` caso o cadastro não seja
sincronizado pelo procedimento do ambiente. Não há nova permissão a conceder.

Aceite em produção:

1. Abrir Portal Suprimentos → Análises → IDF dos fornecedores com usuário normal `supplies.access`; validar tema claro/escuro e desktop/mobile.
2. Escolher período com movimento e filiais 01/02. Conferir um fornecedor/loja nas telas de Qualidade e OTD com as mesmas datas de referência e mesmo escopo de produtos.
3. Abrir Ver composição, conferir contagens, condicionais/urgentes e fórmula 70/30. Validar fechamento por Escape, foco e sidebar acessível.
4. Comparar consolidado com soma de contagens de cada filial, sem média de percentuais; testar loja distinta e fornecedor sem uma das bases.
5. Testar busca, filtro de disponibilidade, paginação e período vazio. Sem `supplies.access`, o acesso deve ser negado também na API.
6. Em Saúde SQL/Cache, verificar operação e namespace `supplier-idf:v1`; repetir consulta deve atingir cache. Não confundir cache válido com falha do botão Atualizar.

Rollback: reverter somente o commit desta funcionalidade por commit de revert
na main e executar o mesmo deploy sequencial dos três serviços. Sem rollback
de dados/migration. Reverter o registro do manifesto apenas se necessário ao
procedimento do Core. Manter o chamado aberto até confirmação do solicitante.

## EXECUTION REPORT — verificação independente

Resultado do runner canônico, sem edição:

```text
# Relatório do delpi-verifier

motor: none · modelo: n/a

veredito: INCONCLUSIVE

motivo: verificador indisponível

## Saída bruta

Nenhum motor headless disponível (devin/agent).
```

| Rodada | Veredito | OCs / resíduo |
|---|---|---|
| 1 | INCONCLUSIVE | Nenhuma análise independente ocorreu; motor indisponível. OCs não avaliadas. |

A indisponibilidade não equivale a ACCEPT. Não foram alterados runner, limites,
scanners ou testes para obter aprovação. Os testes próprios e limites de evidência
estão descritos acima. Revisão independente, inspeção visual e aceite produtivo
permanecem resíduos explícitos. A publicação solicitada não encerra o chamado.

Conectividade de deploy: SSH sem configuração global (`-F /dev/null`, BatchMode)
falhou com `Network is unreachable`; nenhuma alteração foi aplicada ao servidor.

## Continuidade em 16/11/2026 — auditoria pós-push

- Verificado no GitHub: `dee14a0cd2b65fd6a2c18a0821c4900d07e82595` está na ancestralidade de `main` (HEAD observado: `ead46831787acbb4a3f3ec6ac1c42611dd534d8e`). O código IDF está publicado no repositório, mas **não há evidência de deploy em produção**.
- CI do commit IDF: `Architecture Enforcement` falhou em `FASTAPI_OPERATION_ID_REQUIRED` porque o scanner tratava uma rota Flask `Blueprint.get` como FastAPI. A rota BFF é Flask, não aceita `operation_id`. Correção delimitada na branch `fix/glpi-1579-flask-openapi-guardrail`: identificar apenas construtores Flask explícitos (inclusive imports com alias), excluir seus receivers do scanner FastAPI e manter o gate exigindo `operation_id` nas rotas FastAPI, com testes de regressão.
- `api-delpi console`: build MFE aprovado; job `api-tests` falhou por arquivo de teste DAVI inexistente (`tests/test_davi_enterprise_offline_broker_contract_v1.py`), sem relação evidenciada com o IDF.
- `minha-delpi-ai-api presentation`: falha de instalação `npm ci` por `react`/`react-dom` divergentes entre package e lock, outra frente. Não alterar dependências de DAVI/apresentação neste chamado.
- Antes do deploy: revisão da PR de correção e confirmação do gate de arquitetura. Depois do deploy dos três serviços, validar UI desktop/mobile, RBAC, contagens, dados incompletos e consultas em produção conforme roteiro acima. Não marcar #1579 solucionado sem aceite.

