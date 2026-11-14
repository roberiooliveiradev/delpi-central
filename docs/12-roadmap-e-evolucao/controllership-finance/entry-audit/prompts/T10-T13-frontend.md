# Prompt para o Cursor — Entry audit, T10 a T13 (front-end, HML e PROD)

```text
PROMPT CURSOR — ENTRY AUDIT · Trilha T10 → T13 (plugin-ui, MFE, HML e PROD), execução contínua

CONTEXTO
Back-end e CLARA da auditoria de entradas estão em PROD e verificados pela CLARA (T9, T9R, T9R2 —
14/11/2026). Agora o dashboard no Portal Controladoria & Finanças: página de entrada e execução,
dashboard da análise e detalhe da ocorrência, com os componentes do @delpi/plugin-ui.

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/
  track.md (Parte 6, T10–T13; protocolo P1–P9; paradas X1–X8; rollback)
  frontend/README.md, 01, 02, 03 (páginas), 04 (componentes novos e evoluções), wireframes
  backend/README.md §6 (contrato ACCEPTED) — o contrato PUBLICADO é a referência dos dados
Autoridade: instruções oficiais do arquiteto e .cursor > ADR-003 > track.md > padrão visual dos
Portais (docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md) > 30-plugin-ui-reuse-map.md
> docs do front-end.

MISSÃO
Executar T10.0 → T13 sem parar entre etapas, corrigindo de forma autônoma, documentando cada etapa no
mesmo commit, publicando em HML e testando, e por fim publicando em PROD. Parar SOMENTE numa regra
X1–X8, num DECISION_REQUIRED de T10.0, ou ao concluir a T13.

T10.0 · Reconciliação dos docs do front com o contrato publicado (antes de qualquer código)
  Os docs 01–03 são de 13/11; o back-end mudou depois (T9R/T9R2). Conferir, campo a campo, cada dado
  que as páginas usam contra as respostas reais das rotas /entry-audit/* (HML ou fixtures geradas do
  contrato) e atualizar os docs. Pontos já conhecidos:
  a) summary.conformity ganhou posted_outside_period {count, received_dates}. Na Conformidade e na aba
     «Notas sem par», tratar «Lançadas fora do período» como informação (tom neutral), fora de «a
     resolver». received_dates vem como lista crua (uma data por nota): a BFF passa a devolver também
     agrupado [{date, count}] (ajuste aditivo e mínimo no contrato, com teste) — a UI não agrega 250 linhas.
  b) Situações do sem par como estão no motor: «Em lançamento (LNF)» (Info, com id da solicitação →
     link para o app LNF), «em trânsito» (Info), «saída da própria filial» (Info), formulário próprio
     sem SF1 (Alta), XML indisponível. «Explicada» = Info; as demais = «a resolver».
  c) Andamento da execução (doc 01 §4.3): o doc espera etapas protheus/tes_book/xml/rules/result e
     percent. A BFF expõe stage (reading_protheus, reading_xml, auditing, saving, done), contagens e,
     por id, read de uma análise. Mapear as etapas para o que existe; se faltar percent, usar o
     ProgressTracker por etapa sem barra percentual, ou acrescentar percent na BFF se for derivável
     sem estimativa falsa. Não inventar progresso.
  d) Campos que o doc usa e o contrato não tem → acrescentar na BFF só se for leitura do que já é
     persistido; caso contrário, ajustar o doc. Escolha de produto (o que mostrar, nova métrica) →
     DECISION_REQUIRED, parar e listar opções.
  Atualizar frontend/README.md (status READY) e os docs 01–03 no mesmo commit.

T10 · plugin-ui (doc 04)
  Testes de caracterização dos 4 componentes evoluídos no código atual → evoluções aditivas
  (§3 ScopeChipBar, §4 SemicircleProgressGauge, §5 HorizontalValueBars, §6 ComparativeAreaChart) →
  primitivos novos genéricos (§1 DistributionDonut sobre ChartSeriesPie, §2 ResolutionStatusCell) com
  demo no catálogo → exports. Nenhum nome ou prop com «auditoria». Regressão: suíte do plugin-ui +
  build/typecheck de TODOS os consumidores dos componentes evoluídos (inventariar por grep no monorepo).

T11 · MFE plugins/controllership-finance
  Adapters Cf* (frontend README, regra 3); rotas do MFE dentro de /apps/controllership-finance;
  páginas 01, 02, 03 exatamente como especificadas (componentes, props, dimensionamento, URL, estados:
  primeiro acesso, em andamento, falha parcial, vazio por filtro); atalho no Fechamento mensal;
  «Pergunte à CLARA» com as sugestões do doc; Ajuda no mesmo gate. MFE consome só a BFF. A UI
  esconde/desabilita, o backend autoriza (403 sem access tratado com o estado padrão do Portal).
  Exportar = rota de export da BFF. Testes de unidade/render, build, typecheck; desktop e mobile
  (cards na tabela), teclado e foco, claro e escuro (mesma árvore), textos em PT-BR.

T12 · Front-end em HML
  Publicar plugin-ui (consumidores afetados) e MFE em HML. Ensaio automatizado (Playwright headless,
  sem verificação manual): entrada → executar um dia real por filial → acompanhar → dashboard → cada
  filtro cruzado (dia, tema, fornecedor, TES, severidade, legenda da conformidade) muda a URL e a
  tabela → detalhe da ocorrência → resolver e reabrir → export; mobile (viewport de celular); usuário
  sem access → estado de sem acesso; os números da tela batem com as rotas da BFF da mesma análise.
  Screenshots claro/escuro, desktop/mobile, das três páginas no report (sem dado real em commit).

T13 · PROD — front-end
  Linha de base; tags rollback-entry-audit-frontend-<artefato>; publicar um artefato por vez (OK do
  owner dado para esta trilha); verificação: as três páginas abrem; a análise de 12/11/2026 filial 01
  mostra 5 ocorrências, 1 Alta e os mesmos totais que a CLARA lê (summary); consumidores do plugin-ui
  sem regressão (abrir as páginas que usam os 4 componentes evoluídos); logs sem token. Falha →
  rollback do artefato e BLOCKED X7. Plano e trilha → DONE.

REGRAS INEGOCIÁVEIS
1. main, sem branch, sem stash/reset/clean; commits só com arquivos da etapa (há outros agentes no
   repo); push a cada etapa (recusa: fetch --depth=80 + rebase em origin/main + push).
2. Protocolo P1–P9 em cada etapa; quadro de status e registro atualizados a cada etapa.
3. Até 3 ciclos de correção por problema; no 4º, BLOCKED X1.
4. @delpi/plugin-ui first: não duplicar componente nem chrome existente; componente novo nasce no
   plugin-ui, genérico. Evolução só aditiva, padrões atuais preservados.
5. Permissão única controllership-finance.access (manage herda). Nenhuma permission nova.
6. Sem mudança nas seis tools da CLARA. Mudança de back-end só a mínima de T10.0, com teste.
7. Repositório público: nenhum dado real (CNPJ, fornecedor, valores, chaves) em código, fixture,
   snapshot de teste, screenshot commitado ou doc.
8. Suíte de cada pacote tocado comparada ao commit pai; só falhas pré-existentes aceitas (X2).
9. Somente leitura no Protheus, no Questor e no LNF; resolver/reabrir só em ocorrência de teste ou
   resolvida e reaberta no mesmo ensaio (estado final igual ao inicial).
10. Evidência PROVEN | TO_INVENTORY | INCONCLUSIVE com arquivo:linha; PASS | FAIL | TEST_NOT_RUN.
    Ensaio não executado = INCONCLUSIVE.

NÃO MUDAR (decisão do owner pendente)
A janela de 30 dias e a regra da skill «Valor das mercadorias diverge» + «Desconto classificado diferente».

REPORT (ao parar)
Formato da track.md Parte 9, um bloco por etapa; tabela de reconciliação de T10.0 (campo do doc ×
campo do contrato × decisão); lista de consumidores do plugin-ui verificados; resultado do ensaio da
T12 por passo; SHAs, imagens/artefatos e tags; quadro de status final.
```
