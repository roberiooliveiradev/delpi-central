# Playbook de Modelagem — Transformômetro

**Status:** playbook vivo de domínio (atualizado pós–Playbook 18, jun/2026)  
**Escopo:** `transformometro-api`, `plugins/transformometro`, schema `transformometro`

Este playbook define como modelar, calcular e evoluir o Transformômetro sem quebrar a coerência entre cadastro, API, dashboard, exportações e integrações.

Relacionado: [PLAYBOOK-18](./PLAYBOOK-18-instancias-filial-setor-escopo.md) · [PLAYBOOK-19 — diagramas processo/revisão/escopo](./PLAYBOOK-19-diagramas-processo-revisao-escopo.md) · [PLAYBOOK-20 — decomposição árvore/mapeamento](./PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md) · [regras-de-calculo.md](../../../transformometro-api/docs/regras-de-calculo.md) · [playbook-18-implementation-status.md](../../../transformometro-api/docs/playbook-18-implementation-status.md) · [playbook-19-implementation-status.md](../../../transformometro-api/docs/playbook-19-implementation-status.md) · [playbook-20-implementation-status.md](../../../transformometro-api/docs/playbook-20-implementation-status.md)

## 1. Princípios

1. O **processo-mestre** guarda identidade da iniciativa (`codigo_processo`, família, metadados); **não** carrega filial/setor operacional (Playbook 18).
2. A **instância operacional** `(filial × setor)` possui timeline própria de revisões.
3. O cálculo acontece por **revisão** (sempre vinculada a uma `instancia_id`).
4. A baseline é referência comparativa; não representa melhoria implementada.
5. A primeira revisão não-baseline **da instância** define a data de implementação operacional.
6. A vigência da revisão define em quais competências ela pode gerar cálculo.
7. Investimentos e recursos entram no cálculo somente quando pertencem à revisão calculada e estão vigentes na competência.
8. `dashboard_calculos` é derivada; nunca é fonte de cadastro manual.
9. Toda regra de cálculo deve viver no domínio (`DashboardCalculatorService`, `SharedResourceScopeService`) e ser consumida por dashboard, export, alertas e integrações.
10. **PK técnica = UUID** (`filial_id`, `setor_id`, `instancia_id`); **código de negócio** = `codigo_*` (`01`, `engenharia`). Queries e MFE podem usar código; FKs internas usam UUID.

## 2. Entidades e Fonte de Verdade

### 2.1 Cadastro mestre e operacional

| Entidade | Tabela | PK | Papel |
|----------|--------|-----|-------|
| Filial | `filiais` | `filial_id` UUID | Catálogo; `codigo_filial` único (`01`, `02`, …) |
| Setor | `setores` | `setor_id` UUID | Catálogo; `codigo_setor` único (slug de negócio) |
| Setor × filial | `setor_filiais` | — | FKs UUID; define setores elegíveis por filial |
| Processo-mestre | `processos` | `processo_id` UUID | Iniciativa global; `codigo_processo` único |
| Instância operacional | `processo_instancias` | `instancia_id` UUID | Par `(processo_id, filial_id, setor_id)`; unique por processo |
| Revisão | `revisoes` | `revisao_id` UUID | Cenário calculável; FK **`instancia_id`** (+ `processo_id` denormalizado) |
| Medição | `medicoes` | `medicao_id` UUID | Fotografia operacional da revisão |
| Investimento | `investimentos` | `investimento_id` UUID | Custo de implantação ou sustentação da revisão |
| Recurso compartilhado | `recursos_compartilhados` | `recurso_compartilhado_id` UUID | Catálogo + **`escopo_recurso`** (`empresa` \| `filial` \| `setor`) |
| Vínculo recurso/revisão | `revisao_recursos_compartilhados` | `vinculo_id` UUID | Uso e rateio do recurso por revisão |
| Custo de recurso | `recurso_custos` | — | Histórico mensal do custo do recurso |

### 2.2 Derivadas

| Entidade | Tabela | Chave | Papel |
|----------|--------|-------|-------|
| Dashboard (cache) | `dashboard_calculos` | `dashboard_calculo_id` UUID; unique `(revisao_id, competencia)` | Materialização; denorm `instancia_id`, `filial_id`, `setor_id`, `codigo_*` |
| Snapshot agregado | view `processo_competencia_snapshot` | processo × competência | Leitura chat/integrações; expõe `codigo_*` como alias legado |

Fonte de verdade de cadastro:

- `filiais`, `setores`, `setor_filiais`
- `processos`, `processo_instancias`
- `revisoes`, `medicoes`, `investimentos`
- `recursos_compartilhados`, `revisao_recursos_compartilhados`, `recurso_custos`

Fonte derivada:

- `dashboard_calculos`, `processo_competencia_snapshot`

### 2.3 Hierarquia lógica

```text
processo-mestre (codigo_processo) — macroprocesso
  ├── decomposicao (árvore WBS — Playbook 20)
  │     processo_chave → tarefa → sub_tarefa
  ├── diagrama-macro (mapa canônico de fluxo — Playbook 19)
  └── instancia (filial × setor) [instancia_id] — **onde a melhoria acontece**
        ├── contexto operacional extra (`instancia_contexto`, PB20)
        ├── escopo decomposição (processos-chave desta fatia)
        ├── escopo no diagrama (subset nós fluxo)
        └── revisão [revisao_id]
              ├── overlay decomposição (as-is / to-be textual)
              ├── overlay diagrama (as-is / to-be fluxo)
              ├── medição
              ├── investimentos
              └── vínculos → recursos compartilhados (rateio conforme escopo_recurso)
```

Um processo pode ter **N instâncias** (ex.: mesma melhoria em Matriz/Engenharia e Filial 02/Produção). Consolidado do processo = soma KPIs de todas as instâncias; ROI = totais líquidos / totais investimento (não média de percentuais).

## 3. Vocabulário do Domínio

**Baseline**  
Cenário original do processo (`cenario_tipo = baseline`). Serve como referência padrão quando nenhuma revisão de comparação explícita foi informada.

**Revisão de referência (`revisao_referencia_id`)**  
Revisão contra a qual outra revisão calcula economia e diffs visuais. Obrigatória para cenários não-baseline no cadastro (V035). Se NULL (legado), o motor usa a baseline da instância (`DashboardCalculatorService._pick_reference_review`).

**Revisão não-baseline**  
Qualquer revisão com `cenario_tipo` diferente de `baseline`. Hoje os cenários comparáveis oficiais são `melhoria`, `automacao` e `correcao`.

**Data de implementação do processo**  
Data da primeira revisão não-baseline **da instância operacional** (escopo local):

1. usar `data_implantacao`, quando preenchida;
2. usar `data_inicio_vigencia`, como fallback.

No dashboard consolidado por processo-mestre, a data exibida segue a regra acima **por instância**; agregações somam linhas de cada instância.

**Instância operacional**  
Par `(filial × setor)` dentro de um processo-mestre — **onde a melhoria acontece**. Declara escopo (processos-chave / nós de fluxo) e concentra timeline de revisões. Identificador canônico: `instancia_id` (UUID). Opcional: `rotulo_instancia`, `instancia_contexto` (metadados operacionais extras — Playbook 20).

**Processo-mestre**  
Cadastro sem `filial_id`/`setor_id` na tabela `processos` (V015). Create via API ainda aceita filial/setor no body → cria **primeira instância**.

**Escopo de recurso (`escopo_recurso`)**  
Define o pool de vínculos elegíveis ao rateio **antes** de aplicar `criterio_rateio`:

| Valor | Pool |
|-------|------|
| `empresa` | Todos os vínculos vigentes (legado) |
| `filial` | Vínculos cuja instância tem a mesma filial da revisão âncora |
| `setor` | Vínculos cuja instância tem o mesmo par filial × setor |

Módulo: `SharedResourceScopeService`. Detalhe numérico: [regras-de-calculo.md](../../../transformometro-api/docs/regras-de-calculo.md).

**Visão analítica (`view`)**  
Parâmetro de dashboard: `consolidated` (default) \| `filial` \| `department`. Filtra instâncias/revisões nos KPIs; não altera o pool global de recursos `empresa` — apenas a fatia exibida. Módulo: `DashboardViewScopeService`.

**Processo ativo para cálculo**  
Processo que possui pelo menos uma revisão não deletada com `revisao_ativa = true`.

**Revisão vigente na competência**  
Revisão cuja competência calculada cai entre:

- `data_inicio_vigencia` inclusive;
- `data_fim_vigencia` inclusive, quando preenchida.

## 4. Ciclo de Vida do Processo

1. Criar processo-mestre (+ primeira instância operacional com filial/setor).
2. Criar baseline **na instância** com medição.
3. Criar primeira revisão não-baseline **na mesma instância** com `revisao_referencia_id` apontando para a baseline (ou revisão escolhida).
4. Revisões posteriores podem referenciar a **revisão ativa anterior** (incremento entre versões) — campo **Compara com** no MFE.
5. Informar `data_implantacao` ou, no mínimo, `data_inicio_vigencia`.
6. Informar medição da revisão.
7. Registrar investimentos únicos ou recorrentes da revisão.
8. Vincular recursos compartilhados (definir `escopo_recurso` no catálogo quando ≠ `empresa`).
9. Ativar uma revisão operacional da instância.
10. Para replicar a timeline em outro par filial × setor: `POST /instancias/{id}/duplicar` (não duplicar processo-mestre inteiro salvo legado deprecado).
11. Encerrar revisões antigas por `data_fim_vigencia` quando houver troca real de cenário.
12. Recalcular dashboard ou deixar o cálculo em tempo real refletir a alteração.

## 5. Regras de Atividade e Vigência

### Processo ativo

Um processo sem nenhuma revisão ativa é inativo para fins de dashboard.

Consequências:

- não gera linhas em `dashboard_calculos`;
- não entra no ranking "Processos no recorte";
- não entra em resumo por família;
- não entra em alertas;
- não entra em exportação;
- pode continuar aparecendo no CRUD de processos como cadastro histórico.

### Revisão calculável

Uma revisão entra no cálculo mensal quando:

- não está deletada;
- não é baseline;
- pertence a um processo ativo;
- possui medição;
- tem vigência válida na competência;
- o processo possui baseline com medição.

### Baseline

Baseline não deve gerar economia por si só. Ela é a referência para calcular:

- custo de tempo;
- custo de retrabalho;
- custo de erro;
- outros desperdícios;
- custo de recursos compartilhados da baseline.

Se não houver baseline ou medição da baseline, a revisão não deve gerar cálculo financeiro.

## 6. Recorte Temporal

O recorte do dashboard usa competências mensais.

Para a tabela "Processos no recorte":

- incluir processos cuja data de implementação seja menor ou igual ao fim do recorte;
- considerar apenas meses em que a revisão calculável esteja vigente;
- se o processo estiver inativo, não incluir;
- se o recorte estiver antes da primeira implementação, não incluir;
- revisões posteriores não devem alterar a data de implementação do processo.

Exemplo:

```text
Baseline: 2025-01-01
Melhoria 1.1.0: implantação 2025-02-10, vigência 2025-02-01 a 2025-05-31
Automação 2.0.0: implantação 2025-06-05, vigência desde 2025-06-01

Data de implementação do processo: 2025-02-10
Recorte junho/2025: processo pode aparecer, mas o cálculo vem da revisão vigente em junho.
```

## 7. Investimentos

Investimentos são sempre vinculados à revisão (`revisao_id`).

### Campos decisivos

- `recorrencia`
- `valor_total`
- `data_investimento`
- `meses_vigencia`
- `deletado`

### Investimento único

Regra padrão:

- `recorrencia = unico`;
- entra no mês de `data_investimento`;
- se `meses_vigencia > 0`, distribuir o valor igualmente entre os meses da vigência.

Uso:

- compõe investimento do mês;
- compõe investimento acumulado;
- entra no ROI e payback;
- não deve reduzir economia líquida operacional mensal, salvo decisão explícita futura.

### Investimento recorrente

Recorrências aceitas no cálculo:

- `mensal`: valor integral por mês;
- `trimestral`: valor / 3 por mês;
- `semestral`: valor / 6 por mês;
- `anual`: valor / 12 por mês.

Vigência:

- começa no mês de `data_investimento`;
- se `meses_vigencia` vazio ou menor/igual a zero, assume vigência aberta;
- se `meses_vigencia > 0`, termina no último mês da vigência.

Uso:

- reduz `economia_liquida_mes`;
- compõe `investimento_total_mes`;
- compõe custos recorrentes do período.

## 8. Recursos Compartilhados

Recursos compartilhados representam custo operacional ou sustentação rateada.

### Regras de elegibilidade

Um recurso entra na competência da revisão quando:

- o vínculo `revisao_recursos_compartilhados` pertence à revisão;
- o vínculo está `ativo = true`;
- o vínculo não está deletado;
- a competência cai entre `data_inicio_uso` e `data_fim_uso`, quando preenchidas;
- o recurso está com `status_recurso = ativo`;
- o recurso não está deletado;
- a competência cai entre `data_inicio_vigencia` e `data_fim_vigencia`, quando preenchidas.

### Valor mensal

Resolver valor mensal nesta ordem:

1. buscar custo vigente em `recurso_custos`;
2. se não existir histórico vigente, usar `valor_total_recorrente` do recurso.

### Rateio

Critérios atuais (aplicados **dentro do pool** definido por `escopo_recurso`):

- `igualitario`: divide pelo número de vínculos elegíveis no pool;
- `por_revisoes_ativas`: divide pelo número de revisões elegíveis no pool;
- `por_peso`: divide pelo peso relativo do vínculo no pool.

Pool canônico: `SharedResourceScopeService.filter_rateio_pool` · âncora = instância da revisão que recebe o custo.

### Uso no cálculo

O custo compartilhado atual:

- compõe `custo_recursos_compartilhados_mes`;
- compõe `investimento_total_mes` ou custo total mensal apresentado;
- deve reduzir a economia líquida mensal quando tratado como custo de sustentação da revisão.

A economia por recurso compartilhado é o delta:

```text
economia_recursos_compartilhados =
  max(0, custo_recurso_baseline - custo_recurso_revisao)
```

## 9. Fórmulas de Cálculo

### Custo operacional da medição

```text
custo_tempo =
  volume_mensal * (tempo_medio_execucao_min / 60) * custo_hora_mao_obra

custo_retrabalho =
  se custo_unitario_retrabalho > 0:
    volume_mensal * percentual_retrabalho * custo_unitario_retrabalho
  senão:
    volume_mensal * percentual_retrabalho * (tempo_retrabalho_min / 60) * custo_hora_mao_obra

custo_erro =
  quantidade_erros_mes * custo_unitario_erro

custo_operacional =
  custo_tempo + custo_retrabalho + custo_erro + custo_outros_desperdicios + custo_recursos_compartilhados
```

### Economia bruta

```text
economia_bruta =
  max(0, baseline.custo_tempo - atual.custo_tempo)
  + max(0, baseline.custo_retrabalho - atual.custo_retrabalho)
  + max(0, baseline.custo_erro - atual.custo_erro)
  + max(0, baseline.custo_outros - atual.custo_outros)
  + max(0, baseline.recurso_compartilhado - atual.recurso_compartilhado)
```

### Economia líquida mensal

Regra recomendada:

```text
economia_liquida_mes =
  economia_bruta
  - custo_recorrente_mes
  - custo_recursos_compartilhados_mes
```

Observação: se o recurso compartilhado já estiver modelado como custo operacional da medição e também como custo de sustentação, validar para não descontar em duplicidade. A regra operacional deve ser única por tipo de custo.

### Investimento total do mês

```text
investimento_total_mes =
  investimento_unico_mes
  + custo_recorrente_mes
  + custo_recursos_compartilhados_mes
```

### Horas economizadas

```text
minutos_baseline = volume_baseline × tempo_medio_execucao_min_baseline
minutos_melhoria = volume_melhoria × tempo_medio_execucao_min_melhoria
horas_economizadas_mes =
  max(0, minutos_baseline - minutos_melhoria)
  * fração_de_vigencia_no_mês
  / 60
```

## 10. Pipeline Oficial do Dashboard

1. Carregar dados brutos via `DashboardDataRepository.load_raw`.
2. Indexar processos, **instâncias**, revisões, medições, investimentos, recursos, vínculos e custos.
3. Aplicar **`DashboardViewScopeService`** (filtro `view`, `filial_id`, `setor_id`).
4. Determinar timeline mensal.
5. Para cada competência:
   - iterar instâncias/revisões no escopo;
   - descartar processos sem revisão ativa na instância;
   - resolver revisão de referência (`revisao_referencia_id` ou baseline da instância);
   - selecionar revisões não-baseline vigentes;
   - calcular custos operacionais;
   - calcular investimentos únicos e recorrentes da revisão;
   - calcular recursos compartilhados (**pool** via `SharedResourceScopeService`);
   - gerar linha de cálculo por revisão e competência (denorm instância/filial/setor no cache).
6. Consolidar mensalmente em evolução.
7. Derivar resumo, ranking, alertas, família e exportações do mesmo conjunto de linhas.

## 11. Contratos da API

### Dashboard

Rotas principais:

- `GET /dashboard/resumo`
- `GET /dashboard/evolucao`
- `GET /dashboard/processos`
- `GET /dashboard/por-familia`
- `GET /dashboard/alertas`
- `GET /dashboard/export.csv`
- `GET /dashboard/export.xls`
- `POST /dashboard/recalcular`

Parâmetros comuns:

- `view` — `consolidated` \| `filial` \| `department` (Playbook 18)
- `filial_id` — UUID ou `codigo_filial` (`01`)
- `setor_id` — UUID ou `codigo_setor` (exige visão departamento ou filtro explícito)
- `familia_processo`
- `competencia_inicio` / `competencia_fim`

`GET /options` retorna `access_scope` quando RBAC filial está ativo (`FilialAccessScopeService`).

Rotas de instância:

- `GET/POST /processos/{id}/instancias`
- `GET /instancias/{id}`
- `POST /instancias/{id}/duplicar`

### Tabela de processos no recorte

Campos recomendados:

- `processo_id`
- `codigo_processo`
- `nome_processo`
- `filial_id`
- `setor_id`
- `data_implantacao`
- `revisao_implantacao_id`
- `competencia`
- `economia_diaria`
- `economia_liquida_mes`
- `economia_bruta`
- `investimento_total_mes`
- `custo_recorrente_mes`
- `custo_recursos_compartilhados_mes`

## 12. Checklist Antes de Alterar o Cálculo

Antes de mudar qualquer regra:

- atualizar este playbook;
- criar fixture com baseline, revisão ativa, revisão inativa, investimento único, investimento recorrente e recurso compartilhado;
- testar `DashboardCalculatorService`;
- testar `DashboardLiveService`;
- testar exportação, se novos campos forem expostos;
- rodar build do MFE;
- conferir se `dashboard_calculos` materializado e cálculo em tempo real produzem a mesma regra;
- validar que alertas e resumo por família usam as mesmas linhas base.

## 13. Casos de Teste Obrigatórios

1. Processo com baseline e melhoria ativa gera cálculo.
2. Processo sem revisão ativa não gera cálculo.
3. Processo com primeira melhoria antiga e revisão nova mantém data de implementação antiga.
4. Recorte posterior à implementação inclui processo ativo.
5. Recorte anterior à implementação não inclui processo.
6. Revisão com `data_fim_vigencia` não calcula após o fim.
7. Investimento único entra somente no mês ou na distribuição de `meses_vigencia`.
8. Investimento recorrente entra em todos os meses vigentes.
9. Recurso compartilhado respeita vínculo, recurso ativo, vigência, histórico de custo e rateio.
10. Recurso deletado ou vínculo inativo não entra no cálculo.

## 14. Antipadrões

- Calcular regra diferente em rota específica do dashboard.
- Usar `status_processo` como fonte única de atividade operacional.
- Alterar data de implementação quando uma revisão posterior é criada.
- Somar investimento de outra revisão no mês da revisão atual.
- Descontar recurso compartilhado duas vezes sem decisão explícita.
- Editar `dashboard_calculos` manualmente.
- Corrigir apenas a UI quando a regra pertence ao domínio.

## 15. Arquivos de Referência

- `transformometro-api/tm_app/domain/services/dashboard_calculator.py`
- `transformometro-api/tm_app/domain/services/shared_resource_scope_service.py`
- `transformometro-api/tm_app/domain/services/dashboard_cache_denorm_service.py`
- `transformometro-api/tm_app/application/services/dashboard_view_scope_service.py`
- `transformometro-api/tm_app/application/services/filial_access_scope_service.py`
- `transformometro-api/tm_app/application/services/dashboard_live_service.py`
- `transformometro-api/tm_app/application/services/dashboard_recalc_service.py`
- `transformometro-api/docs/regras-de-calculo.md`
- `transformometro-api/migrations/V011__create_filiais.sql` … `V018__revisoes_unique_por_instancia.sql`
- `plugins/transformometro/src/utils/dashboardViewScope.ts`
- `plugins/transformometro/src/ui/processos/ProcessoInstanciasPanel.tsx`
- `plugins/transformometro/src/data/api/transformometroApi.ts`

## 16. Decisões Pendentes

Estas decisões precisam ser explicitadas antes de novas mudanças grandes:

- `custo_recursos_compartilhados_mes` deve sempre reduzir `economia_liquida_mes` ou apenas aparecer como investimento/custo total?
- `status_processo` deve continuar manual ou ser derivado de revisões ativas?
- Deve existir endpoint para desativar todas as revisões de um processo sem excluir revisão?
- Revisões históricas inativas devem calcular em meses passados se eram vigentes no período?
- `meses_vigencia` deve valer para investimento único como amortização contábil ou apenas como rateio de dashboard?

