# Prompt para o Cursor — Entry audit, T13R (consumidores do plugin-ui e higiene de commit)

```text
PROMPT CURSOR — ENTRY AUDIT · T13R — provar que os portais que usam o plugin-ui não regrediram

CONTEXTO
Revisão do Claude sobre T10–T13 (14/11/2026): ACCEPT_WITH_RESIDUAL, com um item INCONCLUSIVE de
risco em PROD e uma falha de higiene.

1) Consumidores do plugin-ui em PROD — INCONCLUSIVE
   Os portais carregam o plugin-ui como remote de federação em tempo de execução
   (ex.: plugins/commercial/vite.config.ts → pluginUiRemote()). A publicação da T13 trocou, para
   todos eles ao mesmo tempo, os 4 componentes evoluídos (ScopeChipBar, SemicircleProgressGauge,
   HorizontalValueBars, ComparativeAreaChart). Consumidores no repo (arquivos que importam):
   commercial 13, supplies 7, engineering 5, helpdesk 4, controllership-finance 3, delpi-mes 3,
   production-pulse 2, transformometro 2, it-portal 1, kaizometro 1, scrap-monitoring 1.
   O registro da T10 mostra só os testes do plugin-ui (120 focados); a T13 mostra remoteEntry 200 e
   a API. remoteEntry 200 não prova que a página abre (rota ≠ implementação).

2) Higiene — o commit 1cbe0945 («docs(entry-audit): T10.0») levou 10 arquivos de outra frente
   (delia-api: root_composer.py, cri_instruction_resource.py, settings.py,
   pydantic_ai_investigation.py, comprehension_instructions.delpi.json, scripts int1_openrouter…,
   test_engine_production_selection.py, test_g1_native_structured_output.py,
   test_two_agent_experiment.py; docs delia 16/17/20, engineering-closure-residual-register,
   delia/evidence/execution-ledger.md). Era trabalho não commitado de outro agente na árvore.

MISSÃO
A. Para cada consumidor da lista: `tsc --noEmit` e build contra o plugin-ui do HEAD; suíte de testes
   do consumidor comparada ao commit pai do d7ffdd6e. Falha nova → corrigir no plugin-ui (evolução
   continua aditiva), nunca no consumidor sem decisão.
B. Smoke em HML (Playwright headless, usuário de teste de HML): uma página de cada consumidor que usa
   um dos 4 componentes — a página abre, o componente renderiza, console sem erro. Lista de páginas
   no report. Se algum portal não estiver no HML, dizer qual e por quê (INCONCLUSIVE, não PASS).
C. PROD: conferir que o plugin-ui publicado é o mesmo build testado em B (hash do remoteEntry) e que
   não há erro de carregamento do remote nos logs do gateway nas últimas horas.
D. MFE controllership-finance: suíte inteira (não só as 46 focadas) contra o commit pai.
E. Higiene: NÃO reverter o commit 1cbe0945 (reverter apagaria o trabalho do outro agente da árvore).
   Registrar no track.md o ocorrido com a lista de arquivos e avisar no report para o owner
   encaminhar à frente delia. Daqui em diante: `git add` só com caminhos explícitos da etapa; nunca
   `git add -A`, `git add .` ou `commit -a`.
F. Falha em B ou C que afete PROD → rollback do plugin-ui pela tag
   rollback-entry-audit-frontend-plugin-ui e BLOCKED.

REGRAS
As da trilha (main sem branch; commits só da etapa; sem dado real no repo; sem permission nova).

REPORT
Tabela por consumidor: tsc, build, testes (pai × HEAD), página do smoke, resultado. Hash do
remoteEntry HML × PROD. Suíte do MFE. Registro da higiene. Parar ao concluir.
```
