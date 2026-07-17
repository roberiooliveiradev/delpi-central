# Fase 7 — Qualidade, profiling e otimização M DELPI

**Status:** implementação concluída em 2026-07-17; piloto funcional ativado em produção
**Baseline:** `b715840eb`

## Resultado

A Fase 7 foi implementada no pipeline canônico do backend. Profiling e explain
não são decisões do browser: a UI somente solicita e apresenta contratos
calculados pelo servidor. O piloto habilita runtime, escrita v2, editor avançado
e telemetria; recursos de maior custo permanecem desligados.

## Contratos entregues

- `POST /data/m/explain`: plano simplificado, diagnostics, hash e tempo/cache de
  compilação; nunca devolve o script no contrato de explain;
- `POST /data/preview-block`: `previewOptions.includeColumnProfile` e
  `deadlineMs`; resposta opcional com `columnProfile`, `stepMetrics` e
  `explainPlan`;
- `GET /data/m/capabilities`: flags finais de profiling, explain, caches e
  telemetria;
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
segundo consumidor.

## Flags do piloto

Estão `true`: `enabled`, `writeV2Enabled`, `advancedEditorEnabled` e
`phase7TelemetryEnabled`. Permanecem `false`: `profilingEnabled`,
`explainPlanEnabled`, `compileCacheEnabled` e `previewCacheEnabled`.

## Rollout recomendado

1. manter tudo desligado e executar testes/carga em ambiente não produtivo;
2. ativar telemetria e cache de compilação para grupo interno;
3. validar taxa de erro, hit ratio, memória e p95 de compile;
4. ativar explain para o piloto;
5. ativar preview cache com TTL curto, verificando isolamento por usuário;
6. ativar profiling apenas no piloto e medir p95/cancelamentos;
7. ampliar gradualmente somente após metas de produto definidas e comprovadas.

Rollback: desligar primeiro `profilingEnabled` e `previewCacheEnabled`; depois
`explainPlanEnabled` e `compileCacheEnabled`. O fluxo M das Fases 0–6 permanece
funcional e os caches locais expiram/reiniciam sem migração.

## Checklist e gaps

- [x] profiling opt-in e amostrado;
- [x] qualidade, distribuição, distinct e min/max seguros;
- [x] explain e métricas por etapa;
- [x] cache TTL/LRU particionado;
- [x] deadline backend e AbortController frontend;
- [x] telemetria sem conteúdo sensível;
- [x] capabilities e UI acessível;
- [x] testes adversariais de chave, isolamento, amostragem e deadline;
- [ ] definir meta oficial de p95 com Produto/SRE;
- [ ] coletar evidência de carga e consumo de memória no ambiente alvo;
- [ ] validar cancelamento por desconexão no proxy ASGI em homologação;
- [ ] validar min/max com datasets reais de datas/durações;
- [ ] decidir TTL e limites finais por telemetria.

## Decisão de ativação

O piloto funcional foi autorizado em produção para validar o fluxo M real. A
ativação de profiling, explain e caches continua condicionada a evidência de
carga, p95, cancelamento e isolamento de memória.

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
