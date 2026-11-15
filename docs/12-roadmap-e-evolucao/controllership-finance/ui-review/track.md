# Trilha — UI review (U0–U8)

Fonte: [review.md](./review.md). Autoridade: instruções oficiais do arquiteto e `.cursor` > padrão visual dos Portais (`docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md`) > `30-plugin-ui-reuse-map.md` > docs do front-end da auditoria (`entry-audit/frontend/01–04`) > este track > review.md.

## 1. Regras

1. `main`, sem branch; `git add` só com caminhos explícitos (nunca `-A`, `.`, `commit -a`); push a cada etapa.
2. `@delpi/plugin-ui` first: usar o componente do kit pelo adaptador `Cf*`; não recriar tabela, card, hero, badge ou gráfico com CSS local (§22). Mudança no plugin-ui só aditiva, com testes de caracterização e prova dos consumidores (lição da T13R).
3. Sem mudança de regra de negócio, contrato ou permissão. Se uma correção de tela pedir dado que a BFF não entrega, parar (Y-dado) e listar; leitura nova aditiva só com decisão.
4. Vocabulário e formatação num lugar só (`entryAuditPresentation.ts` e utilitários do MFE), com teste.
5. DoD de cada página: desktop 1440, tablet 1024, celular 390; claro e escuro (mesma árvore); teclado e foco; estados do §16; ajuda atualizada no mesmo gate.
6. Evidência por screenshot nos três tamanhos e dois temas (no report, não commitado) + Playwright + verificação de acessibilidade automatizada (axe) sem violação séria nova.
7. Página não aberta = INCONCLUSIVE.

## 2. Paradas

| # | Quando parar |
|---|---|
| V1 | 4º ciclo de correção no mesmo problema |
| V2 | Falha nova em suíte (MFE, plugin-ui, consumidores) |
| V3 | Correção exige mudança não aditiva no plugin-ui |
| V4 | Tela precisa de dado que a BFF não entrega (listar campo, página e motivo) |
| V5 | Escolha de produto fora desta revisão (conteúdo, fluxo, regra) |
| V6 | Falha em PROD → rollback e parar |

## 3. Quadro de status

| Etapa | Status | SHA |
|---|---|---|
| U0 Inventário visual e matriz de conformidade | TODO | |
| U1 Base comum (vocabulário, formatação, badges, ícones, estados) | TODO | |
| U2 Início | TODO | |
| U3 Auditoria — entrada e execução | TODO | |
| U4 Auditoria — resultado da análise | TODO | |
| U5 Auditoria — detalhe da ocorrência | TODO | |
| U6 Demais páginas do Portal (desvios do padrão) | TODO | |
| U7 HML (usuários de teste por perfil, Playwright, axe, screenshots) | TODO | |
| U8 PROD | TODO | |

## 4. Etapas

**U0 — Inventário (somente leitura).** Screenshots de todas as páginas do MFE (Início, fechamento mensal e abas, documentos, relatórios, administração, Meu perfil, DRE, Auditoria: entrada, resultado com cada aba, detalhe) em 1440/1024/390 e claro/escuro. Matriz página × regra do padrão (§8–§24): hero, PagePath, SectionCard, KPIs, filtros, tabela, estados, responsivo, ícones, ajuda, vocabulário. Confirmar ou corrigir cada item do review.md e acrescentar o que faltar. Medir o tempo de abertura da análise de 01/11–15/11 (G9).

**U1 — Base comum.** Vocabulário (temas, tipos, filiais, situações), formatação (R$, datas, números de nota/série), mapa severidade → `StatusBadge` (tom + ícone), mapa de ícones por rota e ação, estados de carregamento/erro/parcial/vazio reutilizáveis, ajuda (`CF_HELP`) das telas. Testes de unidade.

**U2 — Início.** H1–H3 do review.md. H1 usa leituras que já existem (competência, bloqueios, última auditoria, backlog do LNF) e mostra estado explícito quando faltar.

**U3 — Entrada da auditoria.** E1–E3. Execução com progresso real (estágio e contadores da análise).

**U4 — Resultado da análise.** A1–A9 e G7/G9. Layout alvo (desktop):

```
PagePath
PageHero  [eyebrow Notas fiscais] Análise de 01/11 a 15/11/2026  [Concluída]
          Matriz (SC) · Filial ES · NF-e · CT-e · criada em … por …
          [⤓ Exportar] [↻ Executar de novo] [+ Nova análise]
KPIs      Notas | Valor | Pendentes | Alta | Diferença nas Altas | Sem par
Linha 1   [Conformidade: medidor + legenda + strip]   [Severidade: donut]
Linha 2   [Por tema]  [Por fornecedor]  [Por TES]
Linha 3   [Evolução por dia: período × anterior]   (só se > 1 dia)
Escopo    chips de filtro ativos  · Limpar
Abas      Ocorrências 159 · Notas casadas 315 · Sem par 144 · CT-e · TES · Fora do período 400
Tabela    severidade | nota/série | fornecedor | regra | campo | Protheus | XML | diferença | status
CLARA     Pergunte à CLARA + 3 sugestões
```

Tablet: KPIs 3 colunas, gráficos 2; celular: 1 coluna, tabela em cards.

**U5 — Detalhe da ocorrência.** Item O do review.md contra o doc 03.

**U6 — Demais páginas.** Corrigir os desvios de padrão da matriz U0, página a página, um commit por página. O que não for padrão vai para a lista de decisão (V5).

**U7 — HML.** Criar no Keycloak de HML usuários de teste por perfil (só access; access+manage; access+LNF; DRE), autorizado pela regra 9 da trilha da auditoria, com senha só no `.env.hml`. Playwright por perfil nas páginas mexidas, axe, screenshots 1440/1024/390 claro/escuro.

**U8 — PROD.** Tags `rollback-ui-review-controllership-finance` (e `-plugin-ui` se tocado); publicar; abrir o Início, a entrada da auditoria e a análise de 01/11–15/11 logado (página aberta, não remoteEntry); comparar números do resultado com a CLARA (summary).

## 5. Rollback

MFE (e plugin-ui, se tocado) pelas tags. Sem migration nesta trilha.

## 6. Registro

| Data | Etapa | SHA | Status | Nota |
|---|---|---|---|---|
| 2026-11-14 | plano | — | READY | Doc 171. Revisão pedida pelo owner sobre os prints de PROD. |
