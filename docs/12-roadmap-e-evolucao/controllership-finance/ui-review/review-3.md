# UI review — revisão 3: refinamento visual e defeitos da seleção (15/11/2026)

Origem: inspeção do Claude em **PROD** (`minhadelpi.com.br`, navegador do owner), depois da U13, na entrada da Auditoria de Entradas e na análise 07/11–13/11 (filiais 01 e 02). Medição no DOM em 1440×900 e em ≈800 px. O owner aprovou todos os apontamentos, achou o defeito da seleção (S1) e decidiu tirar a CLARA de dentro do Portal (C1).

Execução: [track.md §11](./track.md) · prompt [prompts/U14-acabamento-visual.md](./prompts/U14-acabamento-visual.md).

Cada requisito tem critérios de aceite (AC) verificáveis; são eles que vão no pedido ao verificador (`delpi-verifier`).

---

## RQ-U14-SEL — Seleção nos gráficos (defeito, prioridade alta)

**Reprodução (PROD, 15/11):** análise 07–13/11 → clicar «Alta» na rosca de Severidade → a URL ganha `severity=high` e KPIs/gráficos filtram → clicar «Limpar seleção» abaixo da rosca → **nada acontece** (history instrumentado: nenhuma navegação; `severity=high` continua).

**Causa (código):** `EntryAuditAnalysisPage.tsx`

```ts
onSelect={(item) => { if (item) navigateWith({ severity: severityToUrl(item.id) }); }}
```

O kit chama `onSelect(null)` em «Limpar seleção» e ao clicar de novo na fatia selecionada; o `if (item)` descarta o `null`. O chip «Severidade: Alta» em «Filtros aplicados» funciona.

**Também visto com a seleção ativa:** a rosca vira uma fatia só («Alta 100%»), porque o gráfico que seleciona é filtrado pela própria seleção — o usuário perde o contexto e não troca de severidade sem limpar antes. Nas barras (tema, fornecedor, TES), clicar de novo na barra selecionada reaplica o mesmo filtro em vez de limpar.

| AC | Critério |
|---|---|
| AC-SEL-1 | «Limpar seleção» remove `severity` da URL e os números voltam ao total da análise |
| AC-SEL-2 | Clicar de novo na fatia ou na barra selecionada limpa aquele filtro (rosca e barras com o mesmo comportamento) |
| AC-SEL-3 | Com uma seleção ativa, o gráfico que seleciona mostra todas as categorias: a selecionada destacada, as outras esmaecidas (o kit faz isso com `selectedId`). Cada gráfico de seleção é calculado com todos os filtros de detalhamento **menos o da própria dimensão**; KPIs, Conformidade, Evolução e tabela seguem com todos |
| AC-SEL-4 | «Filtros aplicados» tem «Limpar filtros», que remove todos os filtros de detalhamento de uma vez |
| AC-SEL-5 | Teste de componente para AC-SEL-1..4 e Playwright em HML com a reprodução acima |

## RQ-U14-BFF — Ajustes aditivos na BFF

| AC | Critério |
|---|---|
| AC-BFF-1 | Lista de análises ordena por `branches` e `document_types` (lista branca aditiva) |
| AC-BFF-2 | `breakdowns.tes` traz `label` com a descrição da TES (SF4), sem consulta nova ao Protheus se o dado já está na análise; senão V4 |
| AC-BFF-3 | `breakdowns` calcula cada dimensão de seleção sem o filtro da própria dimensão (AC-SEL-3) |
| AC-BFF-4 | Contrato `entry-audit/backend/README.md §6` atualizado; testes; nenhuma resposta existente muda de forma (só campos novos e semântica documentada) |

## RQ-U14-ENT — Entrada da Auditoria

| # | Problema medido | AC |
|---|---|---|
| E1 | Cabeçalhos misturados: «Período/Situação/Criada em» em caixa normal (botão de ordenar), «FILIAIS/TIPOS» em maiúsculas (sem ordenação); seta de ordenar encostada na coluna seguinte | AC-ENT-1: todas as colunas ordenáveis; um padrão de cabeçalho em todas as tabelas do MFE (o do Comercial — `sentenceHeadersWrap` ou equivalente, conferir); seta junto do nome |
| E2 | Filtros numa segunda caixa com borda dentro do hero (moldura dupla); «Executar auditoria» numa linha só para ele | AC-ENT-2: uma moldura (§14); botão na linha dos campos a partir de 1024 px; abaixo disso, largura total |
| E3 | Barra da tabela em duas linhas (Tabela/Cards, Itens por página, Fonte, Colunas) acima de 8 registros; Tabela/Cards desalinhado | AC-ENT-3: barra em uma linha, alinhada como no Comercial |

## RQ-U14-KPI — Indicadores e hero do resultado

| # | Problema medido | AC |
|---|---|---|
| K1 | «R$ 1.060.126,08» quebra em «R$ 1.060.126,» + «08» (cartão ≈210 px em 1440) | AC-KPI-1: valor do KPI nunca quebra; se não couber, formato compacto («R$ 1,06 mi») com o valor completo no title |
| K2 | «Ocorrências pendentes» quebra em duas linhas | AC-KPI-2: títulos dos KPIs em uma linha em 1440 e 1024 |
| K3 | «Sem análise do período anterior para comparar» repetido em 3 cartões, que ficam altos | AC-KPI-3: o aviso aparece uma vez, logo abaixo da faixa de KPIs; cartões da mesma altura |
| K4 | Escopo «Filial 01 · SC · Filial 02 · ES · CT-e · NF-e» | AC-KPI-4: «Filiais 01 (SC) e 02 (ES) · NF-e e CT-e» |
| K5 | Três botões com três estilos; o cinza de «Executar de novo» parece desabilitado | AC-KPI-5: Exportar principal; Executar de novo e Nova análise com a mesma variante secundária do kit |

## RQ-U14-GRA — Gráficos do resultado

| # | Problema medido | AC |
|---|---|---|
| G1 | Quadrinhos «SEM PAR EM ABERTO / EXPLICADAS» no Panorama: texto quebra palavra a palavra e é cortado; «Sem par em aberto» repete o KPI | AC-GRA-1: quadrinhos saem; «Explicadas» vira linha da legenda da Conformidade |
| G2 | Rosca bem maior que a meia-lua | AC-GRA-2: os dois com a mesma altura de área de gráfico |
| G3 | Evolução por dia: eixo começa em 09/11 numa análise 07–13/11; curva suavizada inventa valores entre os dias; eixo sem título | AC-GRA-3: todos os dias do período no eixo (dia sem ocorrência = 0, conferido na regra); barras por dia; anterior como referência alinhada por dia; eixo «Ocorrências» |
| G4 | TES só com código («148», «031») | AC-GRA-4: «148 · <descrição>» (AC-BFF-2) |
| G5 | Temas «Itens», «Cabeçalho» sem sentido para quem lê | AC-GRA-5: «Itens da nota», «Cabeçalho da nota» (catálogo de temas, sem mudar regra) |

## RQ-U14-TAB — Abas e tabela de ocorrências

| # | Problema medido | AC |
|---|---|---|
| T1 | CT-e e «TES utilizadas» sem contador; as outras com | AC-TAB-1: contador em todas as abas |
| T2 | Coluna «Status» em inglês | AC-TAB-2: «Situação»; nenhum cabeçalho em inglês no MFE |
| T3 | Tabela com 1.856 px para 1.341 px de espaço em 1440 (Fornecedor 393, Regra 372, XML 336 px) | AC-TAB-3: sem rolagem horizontal em 1440 com as colunas padrão (`defaultColumnVisibility`; Fornecedor e Regra com largura máxima e reticências, texto completo no title; numéricos à direita) |
| T4 | 50 linhas por página → página com ≈4.400 px | AC-TAB-4: padrão de 25 linhas nas tabelas da análise |

## RQ-U14-CLARA — A CLARA sai de dentro do Portal (decisão do owner)

A CLARA é um MCP usado no ChatGPT e no Claude, não um assistente dentro do Portal.

| AC | Critério |
|---|---|
| AC-CLARA-1 | Sai o card «Pergunte à CLARA» da análise e o texto de ajuda correspondente |
| AC-CLARA-2 | Sai do detalhe da ocorrência o botão «Copiar pergunta para a CLARA» e o bloco «Sugestão da CLARA» (`clara_suggestion` não é produzido pela BFF — sai do tipo do MFE) |
| AC-CLARA-3 | Nenhum texto do Portal convida a usar a CLARA de dentro da tela. **Ficam** a página de consentimento (`ClaraConsentPage`) e o MCP |
| AC-CLARA-4 | Teste: análise e detalhe não renderizam «CLARA» |

## RQ-U14-DOD — Definição de pronto (vale para todos)

| AC | Critério |
|---|---|
| AC-DOD-1 | 1440/1024/390, claro e escuro, teclado e foco; screenshots antes/depois no report (fora do git) |
| AC-DOD-2 | axe sem violação nova (exceções da U13 inalteradas) |
| AC-DOD-3 | Suíte do MFE e da BFF verdes; ajuda atualizada no mesmo commit |
| AC-DOD-4 | Verificação independente (`delpi-verifier`) em cada fase, veredito sem edição no report |
| AC-DOD-5 | README do MFE diz que as suítes `realKit` precisam das dependências do plugin-ui instaladas (observação da U13) |
