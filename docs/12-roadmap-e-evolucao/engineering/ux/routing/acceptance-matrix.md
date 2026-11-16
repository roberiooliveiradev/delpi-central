# EVA / Routing — Visual Acceptance Matrix V1

**Estado:** `TARGET / EXECUTION_NOT_RUN` — plano de evidência, não resultados.  
**Owner do aceite visual:** Product Owner do Portal Engenharia. **Executor:** agente de implementação. **Verificação:** independente, conforme governança canônica.  
**Escopo:** componentes reais, UX, fidelidade composicional, estados e acessibilidade; preservar leitura oficial e motor determinístico.

**Atualização de referência 2026-11-16:** o Product Owner aprovou um único painel PNG com **3 abas × 2 temas** (Operações, Balanceamento, Análise visual; dark e light). O SVG anterior está `SUPERSEDED`. O PNG original foi anexado no chat como `Painel DELPI em modos escuro e claro(1).png` e está publicado em `references/routing-all-tabs-dark-light-approved.png` (sha256 `89cea3e9…89fa`). Gate 0 de referência visual: atendido. As métricas da arte são ilustrativas: não usar como valores oficiais nem expected outputs de negócio.\n\n## 1. Matriz de aceite objetiva

| AC | Estado / viewport | Critério de aceite bloqueante | Evidência exigida |
|---|---|---|---|
| UX-01 | Operações desktop dark | Cabeçalho compacto com título/subtítulo/filial/estágio + navegação próxima; **sem área vazia grande** | Imagem lado a lado com referência SVG/mock, viewport |
| UX-02 | Operações desktop | Quatro KPIs compactos no mesmo nível hierárquico e sem cards brancos no dark | Screenshot + inspeção do componente/tema |
| UX-03 | Operações fechadas | **Cards verticais expansíveis**, não `DataTable` principal; número, descrição, CT, tempo/peça e chevron visíveis | Screenshot + árvore JSX/exports |
| UX-04 | Operação expandida | Recurso/setup/componentes e atributos válidos em grade curta; valores ausentes discretos e honestos | Screenshot expandido + fixture com/sem componentes |
| UX-05 | Filtros | Filial e estágio são controles acessíveis, não badges estáticos; troca atualiza dados sem mistura | E2E teclado/mouse + evidência de troca |
| UX-06 | Balanceamento vazio | Condições 3 campos, opcionais 2, resumo 2 indicadores, CTA principal; sem form 5 colunas comprimido | Screenshot desktop/mobile |
| UX-07 | Balanceamento calculado | Origem de dados e métricas claras; takt em destaque; cenários diferenciados, sem lógica de domínio duplicada | Screenshot + contrato/response + tests |
| UX-08 | Análise visual 1 operação | Não exigir gráfico solitário: card de tempo legível e contexto; não criar três placeholders enormes | Screenshot product single-operation |
| UX-09 | Análise visual multi-op | Renderer comprovado dos dashboards; plot/título/ticks/tooltip/legenda corretos dark/light | Screenshot dos dois temas + path/export usado |
| UX-10 | Escala | `0,0012 min` e `0,06 min` visíveis com unidade explícita; ticks não viram todos zero | Teste valores extremos + screenshots e tooltip |
| UX-11 | Mobile 390/320 | Cards e formulário reorganizados, sem scroll horizontal global, touch/foco/teclado | Capturas 390×844 e 320×640, interação |
| UX-12 | Light mode | Paridade real de contraste, fundos, inputs, badges, chart, sem CSS dark fixo | Screenshots light das 3 seções |
| UX-13 | Estados | Loading/empty/403/404/502/PARTIAL distintos, com informação honesta | Evidência de harness controlado + testes |
| UX-14 | Fonte e domínio | GET roteiro/POST cálculo mantidos; agrupamento de estágios, dedup, provenance e AuthZ preservados | Testes de contrato/regressão |
| UX-15 | Plugin UI | Mapa C01-C20 preenchido; componentes e tema efetivamente renderizados; nenhuma primitiva visual paralela | Audit JSX/CSS, componente export e trecho de uso |
| UX-16 | Verificação | Revisor independente recebe imagens/contratos e emite resultado reproduzível | Veredicto oficial; fallback apenas complementar |
| UX-17 | Produção | Só após gates: SHA, remoteEntry, smoke autenticado e visual no Portal | Evidência de produção em dois temas e rollback |

## 2. Fixture de validação

- **Referência composicional:** código `90260145`, uma operação `01 EMBALAR`, CT-99, tempo `0,06 min/peça`, conforme captura fornecida; **não usar como expected output ERP imutável**.
- **Multi-op:** escolher produto real com várias operações (90264135 usado historicamente), confirmar dados/filial ao executar, não usar contagem de linhas como operações.
- **Tempos muito pequenos:** fixture etiquetada com `0,0012 min`; interpretar `0,072 s` apenas como exibição.
- **Cálculo demonstrativo:** demanda 500, turno 480, pausas 60, disponibilidade 420, takt 0,84 min/peça; parâmetros de teste `PROVIDED`, nunca meta de produção.
- **Falhas controladas:** 403, 404, 502, partial, empty separados. Não simular chamadas live inexistentes.

## 3. Cobertura mínima de capturas

```text
operations/{dark,light}/desktop-1440.png
operations/dark/expanded-desktop-1440.png
operations/dark/mobile-390.png
operations/dark/mobile-320.png
balance/{dark,light}/empty-desktop.png
balance/dark/filled-preview-desktop.png
balance/dark/calculated-desktop.png
balance/dark/scenario-comparison-desktop.png
balance/dark/mobile-390.png
visual/{dark,light}/single-operation.png
visual/{dark,light}/multi-operation.png
visual/dark/time-vs-takt.png
visual/dark/simulation.png
states/{empty,forbidden,unavailable,partial}.png
```

Cada captura exige `SHA`, viewport, tema, estado, fonte dos dados (`REAL` ou `FIXTURE`) e screenshot de referência. Screenshots sem metadados não autorizam PASS.

## 4. Gate de execução

**Gate 0 — Contract Freeze:** contrato visual, referência visual e componente map sem ambiguidade material. Se houver lacunas C07/C08/C16, resolver inventário/decisão antes de codificar esses blocos.

**Gate 1 — Visual Skeleton:** renderizar composição com dados de demonstração explicitamente rotulados; reviewer compara com visual de referência; não implementar cálculo de novo.

**Gate 2 — UI Integration:** ligar dados oficiais mantendo APIs, permission boundaries, dedup e cálculos; verificação de contrato.

**Gate 3 — Browser Matrix:** testar dark/light, desktop/mobile, expansão, cálculo, gráfico e estados; corrigir as divergências.

**Gate 4 — Independent Verification:** `delpi-verifier` oficial nos termos do repositório; `INCONCLUSIVE` não equivale a PASS. Revisão alternativa explicitamente residual.

**Gate 5 — Prod Readiness:** executar release/deploy somente quando gates materiais cumpridos e regras operacionais permitirem. Este documento não autoriza deploy por si.

## 5. Veredicto e critérios de reprovação

Vocabulário por AC: `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`.

**Bloqueadores automáticos:** tabela como listagem primária de operações; tema com superfície plot/cartão incompatível; erros de escala e unidades; controles estáticos fingindo filtros; overflow horizontal global; regressão/AuthZ; ausência de screenshots comparáveis; componente visual inventado apesar de kit equivalente; gráfico selecionado sem inventário real.

**Não compensar blocker por média de score.** Preferir revisão humana do owner e checklist de congruência estrutural; diff pixel-a-pixel é auxiliar, não substituto da qualidade UX.

**Template de resultado:**

```text
SHA:
AC:
Expected / Actual:
Status:
Reference screenshot:
Actual screenshot:
Plugin UI export/consumer path:
Browser/viewport/theme:
REAL or FIXTURE:
Residual:
Owner decision:
```

**Métrica de processo proposta:** aprovação visual na primeira tentativa; número de reworks por tela; percentual de AC com evidência; defeitos achados antes vs após deploy. Nenhuma dessas métricas tem baseline real estabelecida até coleta.
