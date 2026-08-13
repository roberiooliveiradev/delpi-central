# Ata → Portal Comercial — mapa de necessidades

> **Status:** inventário ata-cêntrico (ago/2026) — leitura gerencial primeiro  
> **Produto:** Portal Comercial · `/apps/commercial` · `commercial-api`  
> **Não substitui:** [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) · [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) · [KPI-FICHAS.md](./KPI-FICHAS.md)  
> **Origem:** ata de reunião de desenvolvimento da área comercial (visão integrada na Minha DELPI)

Este documento responde, para cada ponto da ata: **já temos?** · **onde acessar?** · **o que falta?** · **próximo passo**.

---

## 0. Resumo executivo

| Dimensão | Cobertura aproximada no Portal |
|----------|--------------------------------|
| Área comercial central + navegação | **Existe** |
| Visão gerencial (ROL, funil/hit rate, OTD, OV) | **Parcial forte** — cockpit nativo; sem ROL+carteira / MTD-YTD formais / projeção |
| Visão do vendedor (Conta 360 pré-reunião) | **Parcial** — faturamento, pedidos, opp, contatos, tarefas; sem forecast/ofertas SLA |
| Ofertas (produtividade, etapas, SLA) | **Parcial** — listagens OV/ADY + hit rate; sem tempo/etapa/área |
| Clientes (ativo, recuperado, ticket, família, WEG) | **Parcial / bloqueado** — lista operacional; fichas KPI em rascunho |
| Pedidos / entrega / rastreabilidade | **Parcial** — abertos + fábrica por linha; sem FNE, confirmação, causas OTD |
| Manual do Líder (GAV TV + GR) | **Parcial** — BI Overview ≠ TV/GR completo |
| Expedição barcode / inventário / devoluções | **Fora do Portal** (outros chamados/domínios) |
| Rentabilidade / boletos | **Falta / bloqueado** (política ou contrato) |

**Acordo da ata (prioridade):** começar pela **visão gerencial**, centralizando o que já existe (carteira e indicadores principais), sem MVP fechado nesta reunião. Ver § 4 (ondas).

---

## 1. Como ler

| Status | Significado |
|--------|-------------|
| **Existe** | Disponível no Portal Comercial (rota + permissão) |
| **Parcial** | Há dado/UI, mas incompleto vs. o pedido da ata |
| **Falta** | Não há superfície no Portal; backlog Comercial |
| **Bloqueado** | Previsto, mas exige ficha KPI / política antes de UI |
| **Fora** | Não é dono o bounded context Comercial |

Paths relativos à base `/apps/commercial`. Permissões típicas: `commercial.accounts.view`, `commercial.analytics.view`, `commercial.worklist.view`, `commercial.proposals.view`, `commercial.seller-portfolios.manage`.

Fonte de verdade de rotas: [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md).

---

## 2. Matriz por seção da ata (§3–§22)

### §3 — Contexto e diagnóstico (visão integrada)

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Visão integrada (não só cópia de telas) | **Parcial** | Início `/` + Visão geral `/overview` + launcher | MFE nativo | Consolidar lacunas gerenciais (Onda B); evitar iframes de MFEs irmãos |
| Situação do faturamento | **Existe** | `/overview` (ROL) · Conta `?secao=historico` | api-delpi ROL / billing-series via BFF | Formalizar ficha `KPI-ROL` |
| Carteira atual | **Parcial** | `/open-orders` · `/customers` | open-orders + membership | Carteira consolidada valor/itens (`KPI-CARTEIRA`) |
| Carteira futura / projeções | **Falta** | — | — | Onda B após ficha; dor playbook #4 |
| Andamento das ofertas | **Parcial** | `/analytics/opportunities` · `/proposals` | OV + ADY | Etapas/SLA (Onda C) |
| Desempenho dos vendedores | **Parcial** | Escopo carteira · Admin `/administration` | membership / roster | Ranking produtividade BI (não só presença) |
| Situação dos clientes | **Parcial** | `/customers` + Conta 360 | BFF customers | Definições ativo/recuperado |
| Prazos / problemas entrega / gargalos interdept. | **Parcial** | OTD `/analytics/otd` · ficha linha pedido | sales-order-otd + factory-status | Causas, FNE, confirmação, SLA ofertas |

### §4 — Direcionamento Minha DELPI

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Área Departamento Comercial | **Existe** | `/apps/commercial` | Portal + commercial-api | Continuar como UX canônica |
| Alimentar visão gerencial / vendedor / GAV / GR / relatórios / IA | **Parcial** | Overview, Conta, pedidos; docs DESIGN-IA | — | GAV TV + GR + IA assistida = ondas posteriores |
| Incremental: mapear e centralizar o compreendido | **Existe** (este doc) | — | — | Manter inventário atualizado |
| Prioridade carteira + projeção (sem MVP fechado) | **Parcial** | Carteira ops existe; projeção não | — | Onda A (fórmulas) → Onda B |

### §5 — Públicos

#### §5.1 Visão gerencial

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| ROL | **Existe** | `/overview` | `/commercial/*rol*` via BFF analytics | Documentar fórmula (`KPI-ROL`) |
| Carteira | **Parcial** | `/open-orders`, métricas Conta | open-orders | KPI consolidado |
| Carteira + ROL | **Bloqueado** | — | — | `KPI-ROL-CARTEIRA` |
| MTD / YTD | **Parcial** | Filtro de período no Overview | séries ROL | Presets MTD/YTD + labels |
| Projeção de fechamento | **Falta** | — | — | Onda B / FCT-\* |
| Comparação anos anteriores | **Parcial** | Séries históricas limitadas | rol/series | UX explícita 2 anos |
| Produtividade comercial | **Parcial** | Opp/Proposals counts; Admin | — | Ofertas/colaborador (Onda C) |
| Ofertas em aberto | **Existe** | `/analytics/opportunities` | proposals list | — |
| Clientes ativos | **Parcial** | `/customers` (= com pedido aberto no escopo) | — | Formalizar `KPI-CLIENTE-ATIVO` |
| Ticket médio | **Bloqueado** | — | — | `KPI-TICKET` |
| Prazo de amostras | **Falta** | — | — | Onda E / SMP-\* (F7) |
| Confirmação de pedidos | **Falta** | — | — | Onda D / ORD-004–007 |
| OTD | **Existe** | `/analytics/otd` | sales-order-otd | Ampliar variantes (Onda D) |
| Faturado e não embarcado | **Falta** | — | — | Onda D; dor #11 |
| Problemas de entrega | **Falta** | — | — | Onda D/E; dor #13 |
| Ocupação da fábrica | **Parcial** | Capacidade MP na ficha da linha | factory-status | Cockpit PCP (Fora/Produção) |
| Rupturas de estoque | **Falta** | — | — | GR / outro domínio |
| Rentabilidade | **Bloqueado** | — | — | FIN-004 + Onda E |

#### §5.2 Visão do vendedor

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Faturamento ano anterior / atual / evolução mensal | **Existe** | Conta `?secao=historico` · série na lista | billing-series | — |
| Carteira disponível / pedidos em aberto | **Existe** | Conta `?secao=pedidos` · `/open-orders` | open-orders | — |
| Ofertas em aberto | **Existe** | Conta `?secao=oportunidades` · Opp global | proposals | — |
| Follow-ups / atividades | **Parcial** | Conta `?secao=atividades` · `/my-tasks` | worklist | Follow-up de oferta (OV) dedicado |
| Oportunidades em andamento | **Existe** | Opp Conta + `/analytics/opportunities` | — | Pipeline CRM F5+ se necessário |
| Informações para forecast | **Falta** | — | — | Onda B/E forecast |
| Histórico para negociação | **Parcial** | Conta 360 (resumo/hist/pedidos/contatos) | — | Enriquecer com ticket/rentabilidade quando liberados |

### §6 — Indicadores de produtividade e ofertas

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Ofertas por colaborador / totais / emitidas / em aberto | **Parcial** | Listas Opp + ADY | proposals / ADY | Agregações por vendedor/analista |
| Emitidas não finalizadas / idade / situação | **Parcial** | Filtros e colunas existentes | — | Idade e status canônicos |
| Tempo médio elaboração / tempo por etapa | **Falta** | — | — | Onda C; OFF-\* SLA |
| Hit rate | **Existe** | `/overview` (funil/taxa) | `closing-rate` | Documentar numerador/denominador (`KPI-HIT-RATE`); **não mudar regra** |
| Follow-up sim/não / data último | **Falta** | — | — | Onda C + CRM |
| Capital / valor total ofertado | **Falta** | — | — | Confirmar negócio (ata ambígua) |
| Filtros: cliente, segmento, vendedor, analista, período, situação, etapa, família, grupo | **Parcial** | Analytics: período, unidade, segmento WEG/NB, carteira | AnalyticsFilters | Analista, etapa, família, grupo cliente |
| Etapa atual / permanência / área / prazo / gargalo | **Falta** | — | — | Onda C; SLAs ainda não acordados |
| Hit rate — documentar metodologia | **Parcial** | Rota existe | Doc conversão api-delpi | Completar ficha sem alterar regra |

### §7 — ROL, carteira e projeções

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| ROL + série + metas % | **Existe** | `/overview` | rol targets + series | Ficha `KPI-ROL` |
| Carteira + ROL / itens e valores / MTD YTD / 2 anos | **Parcial / bloqueado** | ROL sim; consolidado não | — | Onda A → B |
| Visão temporal (realizado, carteira mês/futuro, gap meta, antecipação) | **Falta** | — | — | Onda B |
| Atualização automática da carteira (postergações) | **Parcial** | Pedidos refletem TOTVS | open-orders | UX «postergado vs disponível» |
| Bruto vs líquido explícito | **Parcial** | ROL líquido; pedidos podem ser brutos | — | Política por indicador (Onda A) |
| Distinguir carteira comercial × programação PCP | **Parcial** | Pedidos = comercial; factory-status ≠ PCP completo | — | Nunca rotular PCP como carteira (dor #4) |

### §8 — Indicadores de clientes

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Clientes com pedido / faturamento / evolução / carteira / ofertas | **Parcial** | `/customers` + Conta | enrich + billing + opp | — |
| Ativos / novos / recuperados / frequência / tempo desde compra / ticket | **Bloqueado / parcial** | `new-clients-*` na api-delpi (pouca UI) | — | Fichas KPI-CLIENTE-\* / TICKET |
| Filtros vendedor, segmento, período | **Parcial** | Escopo + analytics | — | Família / grupo cliente |
| Segmentação estruturada | **Parcial** | WEG × Novos negócios | — | Fonte TOTVS/CRM/cadastro (dor #6) |
| Subgrupos WEG (Motores, WAU, Drives, WDC…) | **Falta** | — | — | Confirmar regra Comercial; Onda A/E |

### §9 — Família de produtos

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Faturamento/carteira por família (automação, drives, motores…) | **Falta** | — | — | Validar fonte item/grupo TOTVS; sem classificação automática sem regra |

### §10 — Ticket médio

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Ticket médio (unidade, bruto/líquido, devoluções) | **Bloqueado** | — | — | Definir unidade → `KPI-TICKET` → UI |

### §11 — Rentabilidade

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Relatório margem/rentabilidade + RBAC + auditoria | **Bloqueado** | — | Spec `API-ROUTES` §3.20 | Política diretoria (FIN-004); Onda E |

### §12 — Prazo de desenvolvimento de amostras

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Ciclo amostra (etapas, atraso, área, 1ª peça teste) | **Falta** | — | Playbook SMP-\* / DATA-MODEL M4 | Onda E (F7); sem prazo médio consolidado hoje |

### §13 — Programa de confirmação de pedidos

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Prazo confirmação, áreas, motivo atraso | **Falta** | — | ORD-004–007 | Onda D; owner negócio: Junior Cesar Pedersetti |
| Fluxo mensagem cliente / status divergente na ata | **Falta** | — | — | Esclarecer status do levantamento antes de modelar |

### §14 — OTD e cumprimento de prazos

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| OTD pedido (painel/série/linha) | **Existe** | `/analytics/otd` | sales-order-otd | Completar `KPI-OTD` |
| OTD colocação / solicitado vs confirmado vs atendido / prometido vs executado | **Parcial** | Um OTD comercial hoje | — | Onda D — variantes + causas |
| Classificação de desvios (interno, cliente, material, capacidade…) | **Falta** | — | — | Onda D |

### §15 — Rastreabilidade completa do pedido

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Marcos pedido → fábrica → fatura | **Parcial** | Ficha linha `/open-orders/...` (OP, factory, BOM) | production BFF | Embarque/trânsito/redespacho progressivo |
| Data/hora, responsável, desvios, justificativas unificados | **Falta** | — | — | Onda D; fontes múltiplas |

### §16 — Manual do Líder

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Nível 01 Gestão à Vista (ROL, carteira, ticket, ofertas, amostras, FNE) | **Parcial** | `/overview` + Opp + OTD (não TV) | — | Pacote GAV TV; itens faltantes Ondas B–D |
| Nível 02 GR (rupturas 30d, FNE+justificativa, problemas entrega SC/ES, amostras, confirmação, ocupação) | **Falta / parcial** | — | — | Onda D/E + domínios externos; justificativa persistente |

### §17 — Faturado e não embarcado

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Lista FNE (cliente, doc, item, tempos, justificativa, responsável) | **Falta** | — | Sem operationId | Onda D; SLA 24h só após formalizar |
| «Pode faturar» (estoque) | **Parcial** | Chip em Meus pedidos / Início | open-orders | **Não** substitui FNE |

### §18 — Divergência de expedição (barcode/QR)

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Conferência entrada/saída, divergências | **Fora** | — | Ops Expedição | Consultar Junior/Vanusa/Fabiano; Comercial só consome status se houver contrato |

### §19 — Inventário rotativo Expedição (#000697)

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Inventário rotativo tipo Almox | **Fora** | Chamado 000697 | — | Consultar chamado / melhoria contínua |

### §20 — Formulário eletrônico de devoluções (#000688)

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| App devoluções Minha DELPI | **Fora** | Chamado 000688 | — | Verificar status; treinamento Laércio após release |

### §21 — Boletos emitidos por Vendas

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Visão gerencial boletos + alçadas | **Falta** | — | Spec FIN-007–008 | Onda E; contrato TOTVS + controles sensíveis |

### §22 — Ocupação e capacidade da fábrica

| Necessidade | Status | Onde acessar | Fonte | Gap / próximo passo |
|-------------|--------|--------------|-------|---------------------|
| Capacidade instalada/disponível, ocupação, gargalos, impacto carteira | **Parcial / Fora** | MP na ficha da linha | factory-status / Produção | Cockpit = dono PCP/Produção; Comercial consome read model (P2–P3) |

---

## 3. Mapa de navegação (gerencial × vendedor)

### Visão gerencial — caminho sugerido hoje

```text
/apps/commercial
  ├─ /overview              → ROL, metas, funil/hit rate, filtros unidade/segmento/carteira
  ├─ /analytics/otd         → pontualidade (launcher Início)
  ├─ /analytics/opportunities → OV em aberto (launcher)
  ├─ /proposals             → documentos ADY (launcher)
  ├─ /open-orders           → carteira operacional / atraso / pode faturar
  └─ /administration        → carteiras, equipe, grupos
```

### Visão do vendedor — caminho sugerido hoje

```text
/apps/commercial
  ├─ /                      → Início: fila, KPIs carteira, launcher
  ├─ /my-tasks              → follow-ups / tarefas
  ├─ /customers             → Minha Carteira
  │    └─ /customers/:c/:loja
  │         ?secao=resumo|pedidos|historico|oportunidades|contatos|atividades
  └─ /open-orders           → linhas da carteira + ficha fabril
```

### Top nav (produto)

| Item | Path | Capacidade |
|------|------|------------|
| Início | `/` | `accounts.view` |
| Visão geral | `/overview` | `analytics.view` |
| Minhas tarefas | `/my-tasks` | `worklist.view` |
| Meus pedidos | `/open-orders` | `accounts.view` |
| Minha Carteira | `/customers` | membership / team / manage |
| Administração | `/administration` | `seller-portfolios.manage` |

---

## 4. Plano de implementação das lacunas

Prioridade da ata: **visão gerencial primeiro**. Ondas **não** reinventam fases do playbook — amarram lacunas da matriz a donos e dependências. Implementação de código só após aprovação de ficha/política quando o item estiver **bloqueado**.

Legenda de dono: **CA** = `commercial-api` · **AD** = `api-delpi` · **MFE** = `plugins/commercial` · **NEG** = Comercial/negócio · **OUT** = outro domínio.

### Onda A — Formalizar (sem UI nova)

Objetivo: destravar P0 sem código de produto.

| Item | Dependência | Dono | Ref. playbook / ficha |
|------|-------------|------|------------------------|
| Definir e publicar fórmula ROL (líquido, devoluções, competência) | Homologação Comercial | NEG + AD | `KPI-ROL` · dor #2 |
| Definir carteira comercial (fonte SC5/SC6, bruto/líquido, exclusões) | Homologação | NEG + AD | `KPI-CARTEIRA` · dor #4 |
| Regra de soma ROL + carteira (bases compatíveis) | KPI-ROL + KPI-CARTEIRA | NEG | `KPI-ROL-CARTEIRA` |
| Documentar hit rate (num/den, abertas, canceladas, revisões, data conversão) **sem mudar regra** | Doc existente conversão | NEG + AD | `KPI-HIT-RATE` · dor #3 |
| Critérios cliente ativo / inativo / novo / recuperado / evento de atividade | Homologação | NEG | `KPI-CLIENTE-*` · dor #7 |
| Unidade do ticket médio (NF/pedido/cliente…) + bruto/líquido | Homologação | NEG | `KPI-TICKET` |
| Confirmar se acompanha **valor** total ofertado além de quantidade | Ata §6.1 ambígua | NEG | OFF-\* |
| Fonte de família de produto e subgrupos WEG (lista oficial) | Cadastro TOTVS/CRM/Delpi | NEG · dor #6 | ADM-\* / M5 |
| Política de rentabilidade (quem vê, export, auditoria) | Diretoria | NEG · FIN-004 | dor #15 |
| Esclarecer status confirmação de pedidos (levantamento vs não iniciado) | Junior Cesar Pedersetti | NEG | dor #9 |

**Critério de saída A:** fichas críticas em `em_validacao` ou `aprovada` (ou bloqueio explícito documentado).

### Onda B — Cockpit gerencial

Objetivo: Visão geral como painel de decisão (carteira + ROL + tempo).

| Item | Dependência | Dono | Notas |
|------|-------------|------|-------|
| Presets MTD / YTD + comparação 2 anos na UI Overview | Onda A (ROL) | MFE + CA BFF | Período já existe; labels/presets |
| KPI consolidado carteira (valor + itens) no Overview | `KPI-CARTEIRA` | AD rota se faltar + CA BFF + MFE | Dor #4 |
| Card ROL + carteira (bases alinhadas) | `KPI-ROL-CARTEIRA` | AD + CA + MFE | Bloqueado até A |
| Carteira prevista mês / meses seguintes / gap vs meta | Fórmulas + fonte postergação | AD + CA + MFE | Projeção; FCT-\* |
| UX bruto vs líquido por indicador | Política Onda A | MFE | Evitar misturar bases |
| Expor `new-clients-*` / novos negócios no cockpit quando fichas ok | KPI-CLIENTE-\* | CA analytics BFF + MFE | Dor #7 |
| Distinção visual carteira comercial ≠ PCP | Conteúdo CM_HELP + copy | MFE | Sem passar programação PCP como carteira |

**Critério de saída B:** gerente responde «como está o mês/ano?» sem planilha auxiliar para ROL+carteira (quando fichas aprovadas).

### Onda C — Ofertas: produtividade e SLA

Objetivo: medir processo de ofertas além da listagem.

| Item | Dependência | Dono | Notas |
|------|-------------|------|-------|
| Contagens por colaborador / emitidas / em aberto / idade | Dados OV/ADY | AD agregações + CA + MFE | OFF-001–003 |
| Follow-up (com/sem, última data) | Modelo CRM ou evento | CA (+ AD se TOTVS) | Dor #3 |
| Valor total ofertado (se confirmado em A) | Negócio | AD + MFE | — |
| Filtros analista, situação, etapa, família, grupo | Cadastros Onda A | MFE + BFF | Estender AnalyticsFilters / Opp |
| Stage history multiárea (entrada, permanência, área, prazo, gargalo) | SLAs acordados entre áreas | CA settings + AD eventos | OFF-004–009; SLAs ainda não firmados |
| Preservar hit rate na UI (documentação visível) | Onda A doc | MFE Overview | Sem mudança de fórmula |

**Critério de saída C:** liderança vê gargalo de oferta por etapa/área sem export manual.

### Onda D — Pedidos, entrega e prazos

Objetivo: fechar Manual do Líder N1/N2 no que for Comercial.

| Item | Dependência | Dono | Notas |
|------|-------------|------|-------|
| Faturado e não embarcado (lista + tempos + justificativa persistente) | Contrato TOTVS + marcos expedição | AD nova rota + CA BFF + MFE | Dor #11; SLA 24h só após formalizar |
| Programa confirmação de pedidos (prazo, área, atraso) | Esclarecimento §13 + adesão áreas | CA workflow + MFE | ORD-004–007 · F7 |
| Variantes OTD (colocação; solicitado×confirmado×atendido; prometido×executado) | `KPI-OTD` ampliada | AD + CA + MFE | Dor #10 |
| Taxonomia de causas de atraso | Negócio | CA + MFE | — |
| Timeline progressiva embarque/trânsito/redespacho | Fontes disponíveis | AD + CA | Construir por marco |
| Problemas de entrega (SC + Rio Bananal) + indicador GR | Modelo exceção | CA + TV se GAV | Dor #13 |
| Pacote Manual do Líder N1 (o que faltar após B/C) | Itens acima | MFE (+ TV Dashboard se layout TV) | GAV-\* |

**Critério de saída D:** FNE e confirmação mensuráveis; OTD com causa mínima.

### Onda E — Sensíveis, amostras e externos

Objetivo: evoluções posteriores à centralização gerencial.

| Item | Dependência | Dono | Notas |
|------|-------------|------|-------|
| Amostras (ciclo, atraso, 1ª peça) | Modelo M4 / fonte | CA + MFE | SMP-\* · F7 · dor #8 |
| Ticket médio no cockpit | `KPI-TICKET` aprovada | AD + CA + MFE | — |
| Rentabilidade (filtros cliente/família/período) | FIN-004 + RBAC + audit log | AD + CA + MFE | Dor #15 · P2 |
| Boletos Vendas + alçadas | Contrato TOTVS + controles | AD + CA + MFE | FIN-007–008 · dor #16 |
| Família produto / subgrupos WEG como filtro canônico | Cadastro Onda A | AD + CA + MFE | Dor #6 |
| Read model ocupação/capacidade para Comercial | Contrato Produção/PCP | OUT → CA consume | Dor #14 · P2–P3 |
| Rupturas estoque 30d (Jaraguá) no GR | Domínio Supplies/PCP | OUT · Comercial consome | Manual Líder N2 |
| Acompanhar §18–§20 sem implementar no Portal | Chamados | OUT | § 5 deste doc |

**Critério de saída E:** itens sensíveis só após política; amostras e capacidade com dono claro.

### Ordem recomendada e o que *não* fazer

```text
A (fichas) → B (cockpit) → C (ofertas) → D (pedidos/entrega) → E (sensíveis/externos)
```

- Não implementar rentabilidade ou boletos antes da política/alçada.  
- Não classificar família/WEG automaticamente sem regra validada.  
- Não tratar programação PCP como carteira comercial.  
- Não hospedar MFEs irmãos como entrega da consolidação.  
- Não expandir Expedição WMS dentro de `plugins/commercial`.

---

## 5. Itens fora do Portal (chamados / outros domínios)

| Ata | Item | Ação |
|-----|------|------|
| §18 | Divergência expedição barcode/QR | Acompanhar ops (Junior, Vanusa, Fabiano); não implementar no `plugins/commercial` |
| §19 | Inventário rotativo `#000697` | Consultar chamado e cronograma |
| §20 | Devoluções `#000688` | Verificar status pós-27/jul; treinar após liberação |
| §22 | Capacidade fábrica plena | Dono Produção/PCP; Portal só consome contrato futuro |
| — | MFEs irmãos (`dashboard-commercial`, PVA, `propostas-comerciais`) | Coexistem; **não** são a UX canônica a evoluir |

---

## 6. Referências cruzadas

| Documento | Uso |
|-----------|-----|
| [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) | Rotas e catálogo de informação por página |
| [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) | Baseline técnico de rotas/plugins |
| [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) | Dores #1–#18 e fases |
| [KPI-FICHAS.md](./KPI-FICHAS.md) | Fórmulas bloqueantes |
| [API-ROUTES.md](./API-ROUTES.md) | Catálogo + gaps (FNE, boletos, rentabilidade) |
| [SCOPE-OWNERSHIP.md](./SCOPE-OWNERSHIP.md) | commercial-api × api-delpi |
| [plugins/commercial/README.md](../../../plugins/commercial/README.md) | README do MFE |
