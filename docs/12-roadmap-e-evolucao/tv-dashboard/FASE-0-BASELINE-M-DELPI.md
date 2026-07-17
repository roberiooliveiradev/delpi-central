# Fase 0 — baseline M DELPI

> **Concluída em:** 2026-07-16  
> **Escopo:** documentação, fixtures, corpus, testes de caracterização e flags desligadas  
> **Produção:** comportamento preservado; parser/runtime M não implementado

## Inventário do fluxo e das rotas

### Rotas HTTP usadas hoje

| Método | Rota | Permissão | Uso |
|---|---|---|---|
| `GET` | `/data/routes` | `TV_READ` | catálogo allowlisted do editor |
| `GET` | `/data/routes/{operationId}` | `TV_READ` | detalhe da fonte |
| `GET` | `/data/openapi/candidates` | `TV_MANAGE` | curadoria de GETs |
| `POST` | `/data/preview-block` | `TV_READ` + acesso à playlist quando informado | preview server-side e por prefixo de etapas |
| `POST` | `/data/validate-config` | `TV_READ` | validação atual da configuração |

Não existem rotas `/data/m/*` na Fase 0.

### Fontes operacionais

- `tv_data_routes.json` contém **232 operationIds GET únicos**.
- O editor escolhe dinamicamente qualquer item desse catálogo; não há lista menor de “rotas M”.
- Exemplos exercitados no baseline: OEE geral/série, OTD série, PPM externo, valor de estoque, LMP summary, lacunas de alocação e appointments de eficiência.
- A allowlist é verificada antes do gateway. Fonte desconhecida retorna erro no bloco.

## Componentes e consumidores

| Área | Componente/módulo atual | Decisão |
|---|---|---|
| workbench | `DataPrepareModal.tsx` | futuramente compositor fino; Fase 0 não refatora |
| comandos | `DataPrepareRibbon.tsx` | local, pois contém domínio |
| fórmula | `DataPrepareFormulaBar.tsx` | parser pseudo-M é legado; não ampliar |
| preview | `previewTransformTableOnServer.ts` | servidor é autoridade; prefixo de `steps` representa etapa |
| tipos/espelho | `tv-dashboard-presentation/src/dataTransform.ts` | apenas paridade/compatibilidade, não novo runtime |
| execução | `tv_data_transform_service.py` | executor tabular canônico |
| tabela compartilhada | `plugin-ui` `DataTable` | opção preferida para evolução futura |

Segundo consumidor exigido antes de evoluir o kit: uma tabela administrativa real do `minha-delpi-chat` ou tabela de manutenção/qualidade deve ser migrada no mesmo ciclo. O catálogo visual não conta. Nenhum componente/CSS do `plugin-ui` foi alterado nesta fase.

## Métricas baseline observáveis

| Métrica/limite | Baseline |
|---|---|
| catálogo | 232 GETs únicos |
| debounce do preview | 280 ms no cliente |
| cache de dados | TTL 120 s |
| chave de cache | `operationId + params + authScope(user/service)` |
| linhas renderizadas no grid de preparação | 40 |
| tabela padrão/série | 90 / 366 linhas |
| dedupe no request | por `operationId + params + authScope` |
| transformação | depois do fetch, antes das projeções de View |
| preview por etapa | cliente envia `steps.slice(0, index + 1)` ao endpoint atual |

Não há hoje `executionMs`, `cacheHit`, métricas por etapa, p50/p95 ou contagem de erro de célula. Portanto não é tecnicamente correto declarar latência de produção sem telemetria. A Fase 7 deverá medir, sem registrar linhas ou script completo:

`m_compile_duration_ms`, `m_execution_duration_ms`, `m_preview_duration_ms`, linhas retornadas, rejeições de limite e cache hit.

## Baselines de risco intencionalmente preservados

1. **Cancelar/Aplicar:** `persistSteps()` chama `updateBlock()` durante a edição. “Cancelar” só fecha; “Fechar e aplicar” força refresh. O teste de caracterização deve mudar na Fase 4, junto do draft transacional.
2. **Cache entre usuários:** qualquer Authorization não vazio vira `authScope="user"`. JWTs distintos podem compartilhar resultado por 120 s quando operação e parâmetros coincidem.
3. **Filial:** `branchPolicy.allowedBranches=[]` não restringe estaticamente. Usuários sem escopo granular explícito seguem a política permissiva atual; usuários com permissões de filial são restringidos pelo `BranchAccessScopeService`.
4. **Catálogo:** 232 GETs ampliam a superfície disponível ao editor, embora ainda sob allowlist/JWT/RBAC.
5. **Drift:** Python e TypeScript possuem executores/normalizadores espelho. Fixtures compartilhadas agora detectam divergência, mas a remoção da autoridade TS depende das fases posteriores.
6. **Semântica legada:** merge mantém um match por chave; headers são sanitizados; erro de expressão pode virar `null`; tipos são `number|string`.

Drift concreto congelado: em `firstRowAsHeader`, Python preserva `Código_produto`; o regex TypeScript atual produz `C_digo_produto`. O fixture possui `expected` e `expectedTs` explícitos para tornar o risco visível sem “corrigir” produção na Fase 0.

## Fixtures e corpus

- `fixtures/tv-dashboard/m-query/v1-operations.json`: golden reutilizado por pytest e Vitest; cobre as 15 famílias nomeadas, incluindo `keepRows` e `removeRows` separadamente.
- `previewByStep`: demonstra os três resultados intermediários do mesmo pipeline legado.
- `fixtures/tv-dashboard/m-query/corpus.json`: M válido/inválido com Unicode, comentários, funções proibidas e casos adversariais. É dado de projeto; não é executado nesta fase.

## Gaps para as próximas fases

- contratos `dataTransform.version=2` e adapter legado;
- AST e `SourceRange`;
- gramática LALR, semântica e registry;
- diagnósticos estruturados;
- draft transacional e seleção por nome;
- RBAC de consultas irmãs e DAG;
- chave de cache com escopo efetivo;
- limites/deadline aplicados, não apenas configurados;
- telemetria de latência e cardinalidade;
- erro de célula explícito e join 1:N;
- decisão final `DataTable` versus `DataGrid` com segundo consumidor.

## Validação executada

Resultados em 2026-07-16:

- pytest de baseline, transformador, fórmula, catálogo e filial: **29 passed**;
- Vitest completo de `tv-dashboard-presentation`: **326 passed**;
- teste focal Cancelar/Aplicar do plugin: **2 passed**;
- allowlist versus OpenAPI: **232 rotas alinhadas**;
- gate de bibliotecas Docker: aprovado;
- JSON e `git diff --check`: aprovados.

Gates gerais já vermelhos fora do escopo:

- `generate_tv_data_routes_from_openapi.py --check`: acusa drift mesmo com `stored=232` e `generated=232`;
- `build-tv-dashboard.sh`: para na auditoria global legada de integração `plugin-ui`;
- `npm test` do `tv-dashboard`: 4 falhas preexistentes de smoke/contratos CSS e ribbon; o novo teste passa;
- `npm run build` do `tv-dashboard`: 67 erros de tipos preexistentes em `plugin-ui`, `tv-dashboard-presentation` e plugin;
- lint isolado não é executável porque o pacote `tv-dashboard` declara script ESLint, mas não possui `eslint.config.*`.

Esses itens foram apenas medidos; corrigi-los nesta fase violaria o escopo “não corrigir produção”.

## Arquivos de decisão

- [ADR-M-DELPI-V1.md](./ADR-M-DELPI-V1.md)
- [PLAYBOOK-POWER-QUERY-M.md](./PLAYBOOK-POWER-QUERY-M.md)
