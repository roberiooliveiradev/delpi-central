# Prompt para o Cursor — UI review, U13 (residuais da U12)

```text
PROMPT CURSOR — UI REVIEW · U13 — residuais da U12: filtro do axe, testes antigos do MFE e
filtro de detalhamento sem apagar a tela

CONTEXTO
Revisão do Claude sobre U12 W2–W8 (track.md §10, «Revisão do Claude sobre U12 W2–W8»):
ACCEPT_WITH_RESIDUAL. Abas sem remontar, ordenação e comparação com o anterior provadas (PROD pela
CLARA). Ficaram três residuais técnicos. Os prints de PROD seguem com o owner (fora desta etapa).

X1 · Média · Filtro do axe pela classe do Portal
   e2e/specs/u12-ui-review.spec.ts ignora contraste em nós que casam com
   /segment-toggle|datatable-layout|cf-action-with-icon|…|avatar/. `cf-action-with-icon` é classe
   do MFE (src/index.css), usada dentro dos botões do hero da análise. Filtrar por ela esconde
   qualquer problema futuro nesses botões.
   Fazer:
   a) O filtro decide pelo componente do kit, não por classe do Portal: o nó só é ignorado se
      estiver dentro de `.delpi-ui-action-btn`, `.delpi-ui-segment-toggle` ou do avatar/TopBar do
      host (checar com element.closest no page.evaluate, por seletor do nó). Lista de exceções num
      único lugar do spec, cada uma com o componente dono e a cor medida (primeiro/segundo plano).
   b) Conferir no Comercial qual variante do ActionButton os heros usam para as ações. Se lá a
      ação principal usa uma variante com contraste correto, alinhar o hero da análise (Exportar
      como principal, as demais como estão) — isso é composição do Portal, não mudança no kit.
      Se o contraste continuar falhando na variante padrão do kit, fica como residual do kit.
   c) Registrar os residuais do kit (ActionButton no hero, SegmentToggle Tabela/Cards) no lugar
      onde a U10 registrou os do plugin-ui, com página, seletor e cores. Não corrigir o kit aqui.

X2 · Alta · Suíte do MFE não fica verde (anterior à U12; mesmo resultado em 0cbe6c3d65)
   5 testes falham e 2 suítes não carregam, todos em src/features/closing/:
   - DocumentDetailPanel «histórico operacional não exibe eventos de download»
     → Found multiple elements with the text /trilha de auditoria/
   - MonthlyDocumentsPanel «exige documento exigido e documento adicional em cartões»
     → Found multiple elements with the text /Exigido/
   - P3CutoffPanel «exibe bloqueios honestos sem cutoff e sem fontes»
     → expected length 3, got 4
   - PackagesPage «rejeição terminal congela ações de revisão no MFE»
     → Found multiple elements with the text /congelada/
   - reportQueryCache «403 substitui o payload da fonte sem tratar como logout»
     → seção ainda renderizada quando devia ser null
   - BillingModBreakdownFlow.realKit e BillingModBreakdownTable.realKit não carregam
     (no ambiente do Claude: «Failed to resolve import "recharts" from
     ../plugin-ui/src/components/charts/ComparativeAreaChart.tsx» — conferir se é dependência
     faltando na resolução do MFE ou só do ambiente).
   Fazer, para CADA um:
   a) Achar o commit em que passou a falhar (git log/bisect no arquivo do componente e do teste).
   b) Classificar: TESTE DESATUALIZADO (a tela mudou de propósito — ex.: texto repetido em ajuda,
      hero ou título) ou DEFEITO DO PRODUTO (a tela faz o que não devia — ex.: 403 deixando dado na
      tela; bloqueio a mais no P3).
   c) Teste desatualizado → ajustar a consulta para o elemento certo (escopo `within`, papel,
      rótulo), sem enfraquecer o que o teste prova. Defeito → corrigir o componente e manter o
      teste. Na dúvida sobre regra de negócio (ex.: quantos bloqueios o P3 deve mostrar) → V1, parar
      e perguntar.
   d) realKit: as suítes precisam carregar e rodar; se faltar dependência na configuração de teste
      do MFE, corrigir a configuração (alias/deps), não pular a suíte.
   Meta: `npm test` do MFE com 0 falhas. Nenhum `skip`/`todo` novo.

X3 · Baixa · Filtro de detalhamento apaga hero, KPIs e gráficos
   EntryAuditAnalysisPage.tsx: o efeito com deps [analysisId, detailFiltersKey] zera analysis,
   summary, breakdowns, daily, rows e page. Ao aplicar um filtro de detalhamento (severidade, tema,
   fornecedor, TES, dia), a página volta a «carregando».
   Fazer: zerar tudo só quando analysisId muda; com filtro novo, manter os dados na tela com o
   estado «atualizando» do kit até a resposta chegar, e descartar respostas atrasadas (abort já
   existe). `analysis` não depende dos filtros — não zerar. Teste: aplicar filtro mantém hero e
   KPIs montados e troca os números quando o resumo chega.

ENTREGA
Um commit por item (X2 pode ter um por teste), push a cada commit, track.md atualizado.
HML: rodar o spec da U12 com o filtro novo (X1) e a página de análise com filtro de detalhamento
(X3). PROD: só o MFE muda; tag rollback-ui-review-u13-controllership-finance; deploy e parar.

REGRAS
As da trilha (main sem branch; git add só com caminhos explícitos; sem mudança de regra, contrato
ou permissão; sem dado real no repositório; paradas V1–V6). Não mexer no plugin-ui.

REPORT
X1: filtro novo, lista de exceções com dono e cores, variante usada no Comercial e decisão.
X2: tabela teste × commit que quebrou × classificação × correção; resultado do `npm test`.
X3: antes/depois e teste. HML/PROD: tag e resultado. Parar ao concluir.
```
