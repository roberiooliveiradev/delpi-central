# Treinamento Portal Comercial — roadmap 1h

> **Objetivo:** roteiro para ministrar ~60 min sem esquecer funcionalidades **já entregues** no Portal Comercial (`/apps/commercial`).  
> **Público sugerido:** vendedores, orçamentistas, faturamento e gestores (admin em bloco final ou sessão dedicada).  
> **Base da auditoria:** manifesto + README do MFE, `GESTAO-A-VISTA.md`, `WIREFRAMES.md` (matriz rota×WF), `PERFIS-E-PERMISSOES.md`, `HELP-COVERAGE.md`, `ATA-MAPA-NECESSIDADES.md`, código em `plugins/commercial/src/features/*` (set/2026).  
> **Não cobre:** implementação técnica, backlog (confirmação de pedidos, Diretoria, forecast, kanban pipeline), nem plugins irmãos como se fossem o Portal.

**Manual para participantes / usuários:** [MANUAL-USUARIO-PORTAL-COMERCIAL.md](./MANUAL-USUARIO-PORTAL-COMERCIAL.md) (“Quero…” → onde ir + FAQ) — **também na UI** em `/apps/commercial/help`.  
**Termos relacionados (Incoterm, datas):** [GLOSSARIO-TERMOS.md](./GLOSSARIO-TERMOS.md).

---

## 1. Como usar este documento

| Quem | Como |
|------|------|
| Instrutor | Seguir a **agenda cronometrada** (§3); usar §4 como roteiro de demo + FAQ; §5 como checklist pré-sala |
| Homologador | Conferir se cada tópico P0 ainda existe na build (rotas da matriz §2) |
| Produto | Atualizar este arquivo quando uma área nova entrar no top nav ou sair do launcher |

**Princípio didático:** Início = “o que fazer agora”; Visão geral = “como está o comercial”; Pedidos/Carteira = operação; Admin = estruturar carteiras.

---

## 2. Mapa de funcionalidades (auditoria)

### 2.1 Navegação de topo (sempre mostrar)

Fonte: `shellNav.ts` + manifesto.

| Item | Path | Quem vê | Pergunta que responde |
|------|------|---------|------------------------|
| **Início** | `/apps/commercial` | Todos com `commercial.access` | O que fazer agora / para onde ir? |
| **Visão geral** | `/overview` | Capacidade analytics (na prática: quem tem acesso ao produto) | Como está o comercial no período? |
| **Sala de interação** | `/interaction-rooms` | `commercial.access` | Onde conversamos sobre pedido/conta/OV? |
| **Minhas tarefas** | `/my-tasks` (alias `/my-day`) | Worklist | Qual minha fila de follow-ups? |
| **Meus pedidos** | `/open-orders` | `commercial.access` | Quais linhas operar agora? |
| **Minha Carteira** | `/customers` | Membership **ou** `commercial.manage` | Quem são meus clientes? |
| **Administração** | `/administration` | `commercial.manage` | Como gerir carteiras / equipe / grupos? |

Chip **Escopo** no chrome = identidade da sessão (carteira própria / equipe / todas), **não** é o mesmo que filtro de período da Visão geral.

### 2.2 Fora do topo (chegar pelo Início / drills)

| Área | Path | Notas para o treinamento |
|------|------|--------------------------|
| Propostas (documento ADY) | `/proposals` · `/proposals/:id` | ≠ Oportunidades OV |
| Pontualidade OTD | `/analytics/otd` | Drill da Visão geral / launcher |
| Oportunidades (OV AD1010) | `/analytics/opportunities` · `/:n` | Lista global + ficha nativa |
| Ficha linha / OP | `/open-orders/:filial/:pedido/:linha` · `…/op/:op` | Deep link compartilhável |
| Conta 360 | `/customers/:codigo/:loja` | Abas via `?secao=` |
| Perfil usuário | `/users/:userId` | Atalho de menção / equipe |
| Equipe analytics | `/analytics/team` | **Redirect** → Administração (não ensinar como tela própria) |

### 2.3 Permissões (3 codes — falar em 2 minutos)

| Code | Em uma frase |
|------|----------------|
| `commercial.access` | Usa o Portal (pedidos, tarefas, BI, propostas, sala) |
| `commercial.manage` | Administra carteiras e **vê todas** as carteiras |
| `commercial.billing.notify` | Recebe aviso “Pronto para faturar” (não libera admin) |

**Dúvida frequente:** “Tenho acesso mas não vejo Minha Carteira” → falta **membership** na carteira (ou `manage`). Pedidos sem membership mostram consolidado amplo; carteira na topbar some.

### 2.4 Ecossistema (deixar explícito no início)

| É Portal Comercial | Não é Portal (coexiste no menu Minha Delpi) |
|--------------------|-----------------------------------------------|
| MFE `commercial` + `commercial-api` | `dashboard-commercial` (cockpit legado) |
| Páginas nativas; dados TOTVS via **BFF** | `pedidos-venda-abertos` (Portal do Vendedor) |
| GR de Vendas / TV = **tv-dashboard** (sem atalho no Portal) | `propostas-comerciais` (legado ADY) |

### 2.5 Status por área (o que ensinar vs. mencionar)

| Área | Status treinamento | Observação |
|------|--------------------|------------|
| Início, Overview, Pedidos, Carteira, Conta, Tarefas, Admin carteiras, OTD, OV, Propostas ADY, Sala | **Demonstrar** | Entregue na matriz WF |
| Kanban de pedidos (board por etapa) | **Demonstrar se disponível na build** | WF-OPEN-ORDERS-KANBAN |
| Confirmação de pedidos, Diretoria, forecast, pipeline kanban comercial | **Não demonstrar** | Stub / backlog |
| Meta SI proporcional, YoY, bruto×líquido, share, horizonte | **Demonstrar na Overview/Carteira** | Entregue (W0 / Onda A–B) |

---

## 3. Agenda cronometrada (60 min)

Ajuste fino conforme a sala: se **só vendedores**, enxugue Admin (T8) e alongue Pedidos + Conta. Se **só gestores**, alongue Overview + Admin e passe mais rápido na ficha de linha.

| Min | Bloco | Foco | Tempo |
|-----|-------|------|-------|
| 0–5 | **T0** Abertura | O que é o Portal, o que não é, permissões, Escopo | 5 min |
| 5–12 | **T1** Início | Hero, eventos, launcher, favoritos, busca | 7 min |
| 12–22 | **T2** Visão geral | Filtros, KPIs, ROL/meta, YoY, funil, export, drills | 10 min |
| 22–32 | **T3** Meus pedidos | Lista, chips, estoque FIFO, atraso, ficha linha/OP | 10 min |
| 32–42 | **T4** Minha Carteira + Conta | Lista, foco/tendência, Conta 360 abas | 10 min |
| 42–49 | **T5** Minhas tarefas | Buckets, CRUD, responsável usuário/grupo, notif | 7 min |
| 49–54 | **T6** Sala de interação | Inbox, thread, pin, tarefa a partir da msg | 5 min |
| 54–58 | **T7** Launcher rápido | OTD · Oportunidades · Propostas (ADY≠OV) | 4 min |
| 58–60 | **T8** Admin *ou* Q&A | Carteiras multi-membro / overlapping *ou* dúvidas | 2+ min* |

\*Se houver gestores na sala, reserve **+8–10 min** no final (estourar levemente ou cortar T7) para Administração (carteiras, cobertura, bulk, equipe, grupos).

**Buffer sugerido:** marcar 1–2 FAQ espontâneas por bloco; o restante vai para §4 “Possíveis dúvidas”.

---

## 4. Roteiro por tópico (funcionalidades + dúvidas)

### T0 — Abertura e contrato mental (5 min)

#### Subtópicos

1. URL canônica: `/apps/commercial` (“Portal Comercial”).
2. Dados de negócio (TOTVS) vs. estado Delpi (carteira, tarefas, sala, avatars) — sem detalhe técnico.
3. Escopo da sessão (chip): própria / equipe / todas (`manage`).
4. Três permissões e papéis típicos (Operacional, Admin, Faturamento, Orçamentista).

#### Demonstrar

- Abrir o Portal logado como vendedor **com** membership.
- Mostrar top nav completa vs. usuário **sem** carteira (Minha Carteira oculta).

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| É o mesmo que o Dashboard Comercial / Portal do Vendedor? | **Não.** Coexistem no menu; o Portal é a UX nativa a evoluir. |
| Por que não vejo Administração? | Falta `commercial.manage`. |
| Escopo muda o período dos gráficos? | Não. Escopo = **carteira(s)**; período fica na Visão geral / filtros locais. |
| Preciso de VPN / Protheus aberto? | Não na UI; o BFF busca TOTVS no servidor. |

---

### T1 — Início (7 min)

#### Subtópicos

1. Saudação + highlights (follow-ups, valor em aberto, atrasos).
2. Faixa de **eventos** do dia (ou chip “fila em dia”).
3. Busca de caminhos / favoritos / recentes.
4. Launcher por seções: Operação · Gestão à vista · Documentos · Administração.
5. Atalhos comuns: Pode faturar, atrasos, Oportunidades, Propostas, OTD.

#### Demonstrar

- Clicar “Ver atrasos” → Meus pedidos com foco.
- Fixar um favorito e reabrir pelo Início.
- Abrir Visão geral pelo launcher (não só pelo topo).

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| Onde está o ROL do mês? | **Visão geral**, não no Início (de propósito). |
| Posso personalizar o launcher? | Favoritos/recentes sim; seções do catálogo são do produto. |
| “Pode faturar” não aparece para mim | Depende de dados FIFO + permissão/audiência de notificação; o chip operacional é na bancada de pedidos. |

---

### T2 — Visão geral (10 min)

#### Subtópicos

1. Filtros: período (presets MTD/YTD etc.), **unidade** SC/ES, carteira (quando permitido).
2. KPIs: ROL vs meta, ROL WEG, novos negócios, conversão, **carteira aberta (agora)**, gap vs meta, horizonte, OTD, % novos negócios.
3. Série ROL + comparar ano anterior (YoY); série hit rate + YoY.
4. Funil de propostas/conversão.
5. Export (ROL / funil / série) — o que exporta e o que **não** (OTD/Opp ficam nas páginas dedicadas).
6. Drills: OTD, Oportunidades (não ficar preso na Overview).

#### Demonstrar

- Alternar MTD ↔ YTD e apontar chip de meta (Meta / Meta parcial / Meta acumulada — linguagem W0).
- Ligar “Comparar ano anterior” no gráfico de ROL.
- Abrir card OTD → página `/analytics/otd`.
- Deixar claro: **carteira aberta ≠ ROL do período** (não somar).

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| Por que meta “parcial”? | Meta SI **proporcional aos dias** do intervalo; mês incompleto ≠ meta cheia. |
| Filial 01/02 vs consolidado | Unidade no filtro; consolidado ≠ média de meta das duas (comportamento documentado nos KPIs). |
| Cadê o ranking da equipe na Overview? | Ranking/gestão de pessoas → **Administração**; Overview é BI de indicadores. |
| Posso ver GR de Vendas daqui? | GR = **TV Dashboard**, sem atalho no Portal. |
| Share / % da empresa | Card de participação quando disponível no cockpit; não confundir com soma ROL+carteira. |

---

### T3 — Meus pedidos (10 min)

#### Subtópicos

1. Lista operacional com escopo de carteira.
2. Filtros / deep links: busca, filial, cliente, datas, sort, página.
3. Chips: **Atraso**, estoque (`com_estoque` / `parcial` / `sem_estoque`), “Pode faturar” (FIFO no BFF).
4. Badge da nav “Meus pedidos” alinhado ao mesmo critério de pronto para faturar.
5. Board/kanban por etapa (se habilitado na build).
6. **Ficha da linha:** status fabril, OPs, BOM, timeline, OV relacionada. Coluna **Data de entrega** depende do **Incoterm** (EXW/FOB = expedição; CIF = saída da empresa) — ver [GLOSSARIO-TERMOS.md](./GLOSSARIO-TERMOS.md).
7. **Ficha da OP:** apontamentos, prazo OTD, troca de OP na URL.
8. Retorno à lista preservando filtros (URL compartilhável).

#### Demonstrar

- Filtrar atrasos → abrir uma linha → abrir uma OP → voltar com breadcrumb.
- Mostrar que a URL da lista pode ser colada no Teams/e-mail.
- Relacionar linha ↔ OV (CTA só quando houver `proposal_number` / resolução).

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| “Tem estoque no Protheus mas aqui diz sem” | Alocação **FIFO** entre pedidos; estoque pode estar “reservado” por outra linha. |
| Data de entrega = chegada no cliente? | **Não.** Depende do Incoterm: EXW/FOB = expedição (cliente busca); CIF = saída da empresa. |
| Pedido ≠ OV | Pedido = C5/SC6; OV = AD1010; proposta documento = ADY — três conceitos. |
| Por que vejo clientes de outro vendedor? | Sem membership: consolidado; com `manage`: todas as carteiras; com membership: só as suas. |
| Notificação “pronto para faturar” | Só quem tem `commercial.billing.notify` (não todos os membros da carteira). |
| Posso confirmar pedido / mudar prazo aqui? | Confirmação comercial ainda **não** é feature do Portal (backlog). |

---

### T4 — Minha Carteira + Conta 360 (10 min)

#### Subtópicos — lista

1. Universo = clientes **vinculados** à carteira (não só quem tem pedido aberto).
2. Painéis: Clientes / Faturamento / Ranking (`panel=`).
3. Foco operacional + tendência de NF (eixos independentes).
4. Natureza **bruto × líquido** (quando o contrato ofereceita).
5. Série de faturamento + comparar ano anterior.
6. Badge **Compartilhado** (cliente em mais de uma carteira).
7. Auditoria “histórico da carteira” (colapsável).
8. Export Excel da lista.

#### Subtópicos — Conta (`?secao=`)

| Aba | Conteúdo |
|-----|----------|
| Resumo | Identidade, KPIs, pontos para conversa, previews |
| Pedidos | Linhas do cliente → ficha nativa |
| Histórico | Faturamento + NFs (detalhe NF em página) |
| Oportunidades | OVs do cliente |
| Contatos | TOTVS (leitura) + contatos locais (CRUD) |
| Atividades | Timeline / follow-ups |

#### Demonstrar

- Abrir cliente → Resumo → Contatos (criar um contato local de teste, se ambiente permitir).
- “Ver atrasos” da conta → pedidos filtrados.
- Mostrar cliente compartilhado (se houver no ambiente).

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| Cliente sem pedido some da carteira? | Não — membership define a lista; pedido é overlay. |
| Fat. 12m bruto vs líquido | Líquido segue lógica ROL; bruto = NF / gross_revenue conforme painel. |
| “Dado indisponível” | Enrichment parcial; lista base permanece; Excel deixa célula vazia. |
| Contato do Protheus posso editar? | Não; só contatos **locais** Delpi. |
| Onde edito a carteira (vínculos)? | **Administração → Carteiras** (`manage`). |

---

### T5 — Minhas tarefas (7 min)

#### Subtópicos

1. Buckets: atrasadas / hoje / próximas / concluidas (labels da UI).
2. Criar follow-up: prazo, tipo, vínculo a cliente/pedido quando houver.
3. Responsável: **usuários XOR grupos** operacionais.
4. Anexos / observação (conforme disponível na build).
5. Escopo equipe (`manage` / team view).
6. Notificações “Tarefas comerciais” (preferências Minha Delpi) vs. faturar.

#### Demonstrar

- Criar tarefa para hoje → concluir → mostrar bucket.
- Deep link de notificação abrindo `/my-tasks` com bucket.

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| Tarefa some para o outro? | Assignees + membros do grupo; quem fez a ação não recebe notificação dela. |
| Posso atribuir a um grupo? | Sim — modo Grupos (não misturar com usuários na mesma tarefa). |
| É o Outlook / Teams? | Não; worklist nativa Delpi (+ sala para chat). |

---

### T6 — Sala de interação (5 min)

#### Subtópicos

1. Inbox global (todos com `access`) vs. unfurl de entidade limitado por carteira.
2. Workspace lista | conversa; painel Contexto / Localizar.
3. Mensagens: markdown, menções, reply, editar, excluir, reações.
4. Imagens (anexo / colar no texto).
5. Pins e itens compartilhados.
6. Criar **tarefa a partir da mensagem**.
7. Abrir sala embutida a partir de pedido/conta/OV (resolve sob demanda).

#### Demonstrar

- Abrir inbox → entrar numa sala → pin + menção.
- Da ficha de pedido, abrir o painel da sala (se houver no ambiente).

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| Substitui o WhatsApp? | Canal interno Delpi; WhatsApp externo não é feature core desta tela. |
| Quem vê a sala? | Inbox ampla com `access`; conteúdo de entidade respeita carteira. |
| Mensagem some para todos se eu excluir? | Exclusão com confirmação — alinhar política mostrada no confirm. |

---

### T7 — OTD, Oportunidades e Propostas (4 min)

#### Subtópicos

1. **OTD:** % no período, série SC/ES, insights (reincidência / tops), linhas com busca.
2. Help OTD: comparação **data de faturamento × data prometida** (linguagem de negócio).
3. **Oportunidades (OV):** lista global + ficha (itens, estrutura, histórico).
4. **Propostas (ADY):** documento + PDF; contato do PDF a partir de contatos salvos.
5. Diferença visual/mental: OV ≠ ADY ≠ pedido.

#### Demonstrar

- Tabela mental no quadro:

```text
Pedido (SC6)  →  operação / fábrica
OV (AD1)      →  oportunidade comercial
ADY           →  documento / PDF para cliente
```

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| Por que a OV não acha a proposta ADY? | Bases/chaves diferentes; CTA só quando o vínculo existe. |
| Escopo nas Propostas | Chrome pode mostrar identidade; listagem ADY nesta wave **sem** filtro membership rígido como carteira. |
| Export OTD na Overview? | Não — usar a página OTD. |

---

### T8 — Administração (gestores — 8–10 min se priorizar)

#### Subtópicos

1. Painel do hub Administração.
2. **Carteiras:** lista / org; ativo-inativo; overlapping; **sem cobertura**.
3. Detalhe: membros (N:N), responsável, clientes, auditoria, carga (`open_value` / atenção).
4. Bulk transfer + export matriz Excel.
5. Soft delete vs. exclusão permanente.
6. **Equipe:** presença / roster.
7. **Grupos** operacionais (≠ RBAC Keycloak).

#### Demonstrar

- Abrir carteira multi-membro → adicionar/remover membro (homolog).
- Chip “Sem cobertura” e explicar universo = clientes com pedido aberto.
- Aviso soft ao vincular cliente já coberto em outra carteira.

#### Possíveis dúvidas

| Dúvida | Resposta curta |
|--------|----------------|
| Grupo = permissão? | Não. Grupo é assignee operacional; permissão continua `access`/`manage`. |
| Cliente em duas carteiras | Permitido; badge “Compartilhado” / overlapping no admin. |
| Inativei a carteira e o vendedor ainda entra | Soft inativa; conferir membership e `manage`. |

---

## 5. Checklist do instrutor (antes da sala)

### Ambiente

- [ ] Usuário **vendedor** com membership real (carteira com pedidos e clientes).
- [ ] Usuário **admin** (`commercial.manage`) para contraste de Escopo / Admin.
- [ ] Opcional: usuário com `commercial.billing.notify` para falar de notificação.
- [ ] Dados no período da demo (mês corrente com ROL / OV / atrasos).
- [ ] Preferências de notificação Minha Delpi visíveis (`commercial` / `commercial_tasks`).

### Roteiro técnico leve

- [ ] Abrir `/apps/commercial` (não o MFE legado por engano).
- [ ] Confirmar top nav: Início · Visão geral · Sala · Minhas tarefas · Meus pedidos · Minha Carteira · Administração.
- [ ] Helps (`?` / `hint`) ativos — reforçar que o aluno pode ler sozinho depois (`HELP-COVERAGE.md`).

### Materiais de apoio (links)

| Doc | Uso na sala |
|-----|-------------|
| [README do plugin](../../../plugins/commercial/README.md) | Rotas e deep links |
| [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) | Norte Início vs Overview |
| [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) | Quem vê o quê |
| [WIREFRAMES.md](./WIREFRAMES.md) | Matriz rota × status |
| [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md) | “Já temos / falta” se perguntarem roadmap |

---

## 6. Script sugerido (falas-âncora)

1. **“O Portal é o lugar do dia a dia comercial na Minha Delpi.”**
2. **“Início organiza o caminho; Visão geral mostra o placar.”**
3. **“Pedido, OV e proposta documento são três coisas — vamos sempre nomear qual.”**
4. **“Carteira é quem é seu cliente; pedido aberto é o que está em andamento.”**
5. **“Escopo é com quem você trabalha; período é o recorte do indicador.”**
6. **“O que ainda não está no Portal (confirmação, Diretoria, GR TV) a gente nomeia para não gerar expectativa falsa.”**

---

## 7. Pós-treinamento (opcional, 5 min assíncrono)

Enviar aos participantes:

1. Atalho `/apps/commercial` + pedido para fixar favoritos no Início.
2. Tabela OV ≠ ADY ≠ pedido (T7).
3. Quem acionar TI/Admin para membership / `manage` / `billing.notify`.
4. Canal de dúvidas (sala de interação do time ou suporte interno).

---

## 8. Fora do escopo deste treinamento de 1h

- Configurar Keycloak / papéis Minha Delpi do zero (só mencionar os 3 codes).
- Treinar TV Dashboard / Gestão à vista na TV.
- Treinar plugins `dashboard-commercial`, `pedidos-venda-abertos`, `propostas-comerciais` como produto principal.
- Detalhe de APIs, migrations, WebSocket.
- Backlog: confirmação de pedidos, reunião Diretoria, forecast, AI carve, mapa territorial (E7).

---

## 9. Histórico da auditoria (fontes)

| Fonte | O que alimentou este roteiro |
|-------|------------------------------|
| `plugins/commercial/commercial.manifest.json` | Rotas e permission codes |
| `plugins/commercial/src/content/shellNav.ts` | Ordem e labels do top nav |
| `plugins/commercial/README.md` | Deep links pedidos/carteira, Conta, Admin E6, sala |
| `docs/.../GESTAO-A-VISTA.md` | Catálogo de informação por página + métricas Overview |
| `docs/.../WIREFRAMES.md` | Matriz entregue vs stub |
| `docs/.../PERFIS-E-PERMISSOES.md` | Membership × access × manage × billing.notify |
| `docs/.../ATA-MAPA-NECESSIDADES.md` | Expectativa de negócio vs. o que já existe |
| Features em `src/features/{home,overview,open-orders,customers,my-day,interaction-rooms,proposals,analytics,administration,seller-portfolios}` | Confirmação de superfícies reais no código |

*Atualizar este arquivo quando o top nav, o launcher ou o status WF de uma área mudar.*
