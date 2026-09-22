# Fase 7 — Qualidade, profiling e otimização M DELPI

**Status produto (2026-09):** fluxo M **DESATIVADO** no produto (`mQuery.enabled`,
`writeV2Enabled`, `advancedEditorEnabled` = `false`). Código M e testes unitários
permanecem retidos (dormant). Authoring canônico = `dataTransform.steps` (modal
Preparar dados / Combinar) + VISTA `set_data_transform`.

**Status histórico:** implementação concluída em 2026-07-17; piloto funcional
esteve ativo e foi desligado em favor do SoT tipado (steps).

**Baseline:** `b715840eb`

## Resultado

A Fase 7 foi implementada no pipeline canônico do backend. Profiling e explain
não são decisões do browser: a UI somente solicita e apresenta contratos
calculados pelo servidor. Com o produto em modo steps-only, compile/mutate HTTP
respondem 404; dual-read de scripts v2 legados no enrichment permanece para
compatibilidade de playlists já salvas.

## Contratos entregues

- `POST /data/m/explain`: plano simplificado, diagnostics, hash e tempo/cache de
  compilação; nunca devolve o script no contrato de explain;
- `POST /data/preview-block`: `previewOptions.includeColumnProfile` e
  `deadlineMs`; resposta opcional com `columnProfile`, `stepMetrics` e
  `explainPlan`;
- `GET /data/m/capabilities`: flags finais de profiling, explain, caches e
  telemetria (workbench só se `enabled` ∧ `writeV2Enabled`);
- profiling amostrado e opt-in com válida/vazia/erro, distinct/repeated,
  distinct ratio e min/max somente para tipos ordenáveis homogêneos;
- explain classifica operações potencialmente caras e marca todas as etapas
  como canceláveis por AbortController no cliente e deadline cooperativo no
  executor.

## Cache e isolamento

A chave de compilação inclui `profile`, `registryVersion`, `scriptHash`,
`sourceSchema`, bindings, `targetStepName` e `culture`.

A chave de preview inclui também fingerprint opaco de identidade, permissões,
superadmin, filial/filtros/parâmetros, fontes e revisões. JWT, script bruto e
linhas não entram nas chaves. O preview só usa o cache de Fase 7 para requests
autenticadas, impedindo compartilhamento entre usuários. Ambos os caches são
TTL + LRU e possuem limite de entradas.

Os valores de preview em memória contêm a resposta necessária para servir a
prévia; não são persistidos. Desligar a flag ou reiniciar o processo elimina
seu uso.

## Observabilidade

Eventos estruturados usam somente código, hash, duração, hit/miss, contagens de
linhas/colunas e erros. Não registram valores, scripts, JWT ou credenciais.
As métricas por etapa expõem somente cardinalidade e tempo.

## UI

O painel local `DataPrepareQualityPanel` oferece **Analisar perfil** sob demanda,
estado `aria-pressed`, status anunciável, qualidade/distribuição por coluna e
`details` para o plano. Não foi criado componente no `plugin-ui`: não existe
segundo consumidor. Com flags off, o compositor `DataPrepareModal` usa só o
fluxo legado de etapas tipadas (ribbon Combinar / steps).

## Flags canônicas (produto)

Estão `false`: `enabled`, `writeV2Enabled`, `advancedEditorEnabled`,
`profilingEnabled`, `explainPlanEnabled`, `compileCacheEnabled` e
`previewCacheEnabled`. `phase7TelemetryEnabled` pode permanecer `true` sem
expor o workbench.

## Rollout / reativação (somente se produto decidir)

1. backfill ou inventário de transforms v2 → steps;
2. ligar `enabled` + `writeV2Enabled` em ambiente controlado;
3. só então `advancedEditorEnabled` e recursos caros (profiling/explain/caches).

Rollback do produto M: manter as três flags de authoring em `false`. Código
`m_query` e rotas `/data/m/*` ficam dormant sem remoção.

## Checklist e gaps

- [x] profiling opt-in e amostrado;
- [x] qualidade, distribuição, distinct e min/max seguros;
- [x] explain e métricas por etapa;
- [x] caches TTL/LRU particionados;
- [x] deadline backend e AbortController frontend;
- [x] telemetria sem PII/script;
- [x] capabilities e UI acessível (workbench gated);
- [x] produto desativado; SoT = steps tipados;
- [ ] backfill opcional v2→steps (fora deste cutover);
- [ ] meta oficial de p95 se M for reativado.

## Decisão de produto

Fluxo M **desligado** no produto. Novos transforms = `{ steps }`. Scripts v2
existentes: dual-read no enrichment. Reativar M exige decisão explícita +
inventário/backfill.

## Validação local

- Vitest focal da qualidade, ribbon e concorrência: aprovado;
- gate de escopo CSS: aprovado;
- Vite build direto: aprovado;
- sintaxe Python por AST e JSON: aprovados;
- `pytest`: indisponível no ambiente, sem instalação ou criação de venv;
- typecheck amplo: bloqueado por erros preexistentes fora da Fase 7 em
  `plugin-ui`, `tv-dashboard-presentation` e componentes legados do dashboard;
- ESLint amplo/focal: CLI v9 sem `eslint.config.*` no pacote (preexistente).

Esses erros globais não foram corrigidos por estarem fora do escopo. Nenhum
Docker/container/serviço foi usado e nenhuma dependência foi instalada.
