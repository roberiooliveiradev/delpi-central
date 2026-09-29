# Factory Supply — Abastecimento Fabril

> **Status:** baseline de produto/arquitetura — Documentation 1/5 (set/2026)
> **DOCUMENTATION_CYCLE:** `COMPLETE` — todos os gates C0 (P1/P2/P3, T1–T12) resolvidos; **DOCUMENTATION_COMPLETE = YES / RUNTIME_IMPLEMENTED = NO** (FS-C0.CLOSURE)
> **Nome técnico:** `factory-supply`
> **Nome de produto (PT-BR):** Abastecimento Fabril
> **Natureza:** documentação canônica de evolução. **Não** autoriza implementação, scaffold, migration, manifest ou qualquer mudança de runtime.

---

## 1. Status documental

Este documento usa quatro classificações de evidência. Elas se aplicam a **afirmações**, não a intenções:

| Marca | Significado |
|---|---|
| `PROVEN` | Verificado em código, contrato, migration ou documentação canônica vigente do repositório. |
| `PLANNED` | Direção aprovada pelo Product Master, ainda sem implementação. |
| `TARGET` | Estado-alvo conceitual desejado; não descreve runtime atual. |
| `TO_INVENTORY` | Falta evidência no repositório para afirmar; exige investigação na documentação seguinte. |

Documentação não prova runtime. Nenhuma capacidade descrita como `TARGET`/`PLANNED` existe em produção por estar escrita aqui.

---

## 2. Product vision

O painel atual ("Painel Alimentador Fábrica", Power BI) e a capability **Line Feeder** existente respondem *o que* precisa chegar na bancada. O que falta é o **rastro operacional** entre a necessidade e o destino: quando o material sai oficialmente do almoxarifado para a fábrica, o ERP preserva a transação de estoque, mas o contexto operacional — por que moveu, qual necessidade causou, para onde ia, quem preparou, quem coletou, qual CT recebeu, quando entregou, o que voltou — não fica representado como um fluxo coerente.

**Factory Supply** é o produto que coordena e rastreia esse fluxo interno de abastecimento:

```text
necessidade de material
→ solicitação / decisão de preparo
→ preparo no almoxarifado
→ transação oficial de estoque (quando aplicável)
→ coleta pelo alimentador
→ handoff
→ entrega no CT
→ evidência de consumo / sobra
→ devolução (quando aplicável)
→ encerramento
```

Resultado pretendido: rastreabilidade operacional ponta a ponta, sem virar fonte paralela de estoque.

---

## 3. Product boundary

Factory Supply coordena e rastreia o **fluxo operacional** de abastecimento entre:

```text
Operador de Produção → Almoxarifado → Alimentador de Linha → CT/Produção → Devolução
```

É dono de **fatos operacionais do workflow** (pedidos, preparo, coleta, missão, handoffs, entrega operacional, devolução operacional, correlação com transações oficiais, timestamps e atores). É `TARGET` — cada transição e dono serão detalhados na Documentação 2/5.

Não é dono de fatos de negócio/estoque que pertencem ao ERP (ver § 9).

---

## 4. Non-goals

Factory Supply **não** é:

- um WMS;
- um ERP;
- uma nova fonte de verdade de estoque;
- substituto do TOTVS;
- substituto do PCP;
- substituto do Cockpit do Operador;
- aplicação genérica de almoxarifado;
- aplicação genérica de inventário;
- controlador de segurança industrial;
- sistema de controle industrial autônomo.

Não expande autoridade para PLC/CNC/controle de máquina.

---

## 5. Actors

| Ator | Papel no fluxo | Status |
|---|---|---|
| Production Operator | Solicita material quando operacionalmente apropriado, via Cockpit do Operador | Integração `TARGET` (não implementada) |
| Warehouse Operator | Preparo de material e handoff do lado do almoxarifado | `TARGET` |
| Factory Feeder | Coordena coleta, movimentação, entrega e devolução | `TARGET` (hoje: mesma permissão de leitura do Line Feeder) |
| PCP | Contexto de planejamento/produção onde aplicável | `TARGET` |

**RBAC de usuário — decidido (Product Master, FS-C0.T3):** exatamente 3 permissões — `factory-supply.access` + `factory-supply.view.filial-01` + `factory-supply.view.filial-02`; `.view.filial-*` é escopo de filial (leitura+escrita), não permissão read-only. Atores (almoxarifado, alimentador, operador) são papéis de negócio sobre o mesmo modelo — sem permissão por papel/ação. Referência existente: `production-control.line-feeder.view` + filial (§ 18). Detalhe de contrato em TECHNICAL-CONTRACTS §40.

---

## 6. Current problem

A transferência oficial almoxarifado → fábrica existe no ERP, mas o contexto operacional se perde: o ERP sabe que o material moveu; ninguém sabe, em um só lugar, qual necessidade de produção causou a movimentação, quem preparou, quem coletou, qual bancada recebeu, quando, e o que precisou voltar. O rastro hoje é reconstruído manualmente — ou não é reconstruído.

---

## 7. Current state

A implementação existente relevante é o subplugin **Line Feeder** (`line-feeder`) do Portal PCP:

```text
Portal / Minha DELPI
→ plugins/production-control (MFE federado)
→ production-control-api (/apps/production-control-api)
→ api-delpi (contratos TOTVS)
→ TOTVS (Protheus)
```

`PROVEN`. Detalhamento completo em § 18.

**Classificação arquitetural:** essa implementação é `PROVEN_REFERENCE_IMPLEMENTATION` — evidência de domínio, contratos e UX a aprender. **Não** é a arquitetura-alvo de ownership do Factory Supply (§ 11).

---

## 8. Target operational lifecycle

`TARGET` — o ciclo conceitual desejado é:

```text
material need
→ request / preparation decision
→ warehouse preparation
→ official stock transaction (quando aplicável)
→ feeder collection
→ handoff
→ delivery to CT
→ consumption / remainder evidence
→ return (quando aplicável)
→ closure
```

Distinções obrigatórias que o modelo deve preservar:

```text
PREPARED                ≠ OFFICIALLY TRANSFERRED
COLLECTED               ≠ OFFICIALLY TRANSFERRED
OPERATIONALLY DELIVERED ≠ ERP MOVEMENT
ERP MOVEMENT            ≠ PRODUCTION CONSUMPTION
```

Exemplo: a transferência oficial `almoxarifado → ponto de uso` pode continuar sendo executada **diretamente no TOTVS**. Factory Supply observa e correlaciona a evidência autoritativa desse movimento **se** a api-delpi expuser o contrato de leitura necessário — sem jamais afirmar que executou a transferência. Códigos de armazém (ex.: `01`, `99`) são configuração do contexto/filial, não semântica hardcoded — os valores concretos vigentes vivem hoje em `production-control-api/production_control_app/content/line_feeder.json` (`pointOfUseWarehouse`, `sourceWarehouse`) como referência, e a semântica autoritativa vem dos contratos.

Estados concretos, transições e donos pertencem à Documentação 2/5. Nenhuma máquina de estado está implementada por este documento.

---

## 9. Authority and ownership matrix

Duas verdades coexistem e **não** se fundem:

- **Verdade autoritativa de negócio/estoque:** TOTVS, acessado via api-delpi (fronteira de leitura atual — § 10).
- **Verdade operacional do Factory Supply:** o que o produto registra sobre o workflow.

| Conceito | Owner canônico | Fonte canônica | Consumidor | Status | Notas |
|---|---|---|---|---|---|
| Necessidade de produção (o que a programação exige) | TOTVS | api-delpi — `POST /production/orders/operation-materials/batch` (SD4) + fila alocada `GET /production/machine-load/*` (SH8) | BFF de domínio | `PROVEN` (leitura existe e é usada pelo Line Feeder) | `open_qty` (`D4_QUANT`) já exclui baixa por apontamento |
| Saldo de estoque | TOTVS | api-delpi — `GET /supplies/stock-balances/items` (SB2) | BFF | `PROVEN` | `only_positive=false` distingue zero de negativo |
| Saldo por armazém / ponto de uso | TOTVS | mesmo contrato, parâmetro `warehouse` | BFF | `PROVEN` | Armazém concreto = configuração, não constante do domínio |
| Empenho (commitment) | TOTVS | api-delpi — operation-materials (SD4) | BFF | `PROVEN` | Teto 300 OPs/requisição; fatiamento é responsabilidade do consumidor |
| Local físico de retirada | TOTVS | api-delpi — `POST /products/physical-locations` (SBZ `BZ_MPLOCAL`) | BFF | `PROVEN` | Produto sem SBZ na filial → ausência, nunca local inventado |
| Bloqueio de inventário | TOTVS | api-delpi — `POST /products/inventory-blocks` (SB2 `B2_DTINV`/`B2_DINVFIM`) | BFF | `PROVEN` | |
| Transferência oficial entre armazéns | TOTVS | api-delpi — `GET /products/{code}/internal-movements?kind=warehouse_transfer` (SD3, DE0 sai / RE0 entra) | BFF | `PROVEN` como leitura/correlação | **Execução da transferência: `NOT_AVAILABLE`** — Factory Supply não escreve no TOTVS |
| Consumo oficial de produção | TOTVS | api-delpi — `/production/consumption/*` (apontamento SH6) | BFF | `PROVEN` (leitura existe) | Baixa de MP é fato ERP, não evento Factory Supply |
| Ordem de produção / operação / CT | TOTVS | api-delpi — `/production/pcp-orders/*`, `/production/orders/*`, `/production/machine-load/*` | BFF | `PROVEN` | |
| Solicitação do operador | Factory Supply | próprio backend + Postgres | — | `TARGET` | Sinal distinto da necessidade planejada (§ 14) |
| Decisão/estado de preparo | Factory Supply | próprio backend + Postgres | — | `TARGET` | `prepared` **não** implica reserva no TOTVS (§ 11 do prompt de origem) |
| Lista de coleta / pick workflow | Factory Supply | próprio backend + Postgres | — | `PLANNED` — existe referência PROVEN no Line Feeder | Reuso/migração do modelo `line_feeder_pick_plans` é decisão da Doc 2/5 |
| Handoff operacional | Factory Supply | próprio backend + Postgres | — | `TARGET` | Ator autenticado + timestamp + quantidade + origem/destino |
| Rastro de entrega operacional | Factory Supply | próprio backend + Postgres | — | `TARGET` | Não é movimento ERP |
| Rastro de devolução operacional | Factory Supply | próprio backend + Postgres | — | `TARGET` | ~~Fórmula/fonte da quantidade de devolução: `TO_INVENTORY`~~ — RESOLVIDO FS-C0.P2 (modelo 3-camadas, Doc 4/5 §53.7) |
| Correlação com transação oficial | Factory Supply | referência à evidência api-delpi/TOTVS | — | `TARGET` | Correlação ≠ execução |

Factory Supply **nunca** vira fonte paralela de inventário: não persiste campos locais como versão autoritativa de saldo corrente, saldo de armazém, saldo de empenho, consumo oficial ou resultado de transação de estoque. Onde decisões operacionais exigem fatos do ERP, preserva-se **referência autoritativa** e, quando justificado depois, **snapshot do momento da decisão** como evidência — nunca como verdade de estoque.

---

## 10. Current architecture

`PROVEN` — caminho verificado no repositório:

```text
Browser (Portal)
  → plugins/production-control            MFE federado, render-only
      manifest: production-control.manifest.json
      basePath: /apps/production-control
  → /apps/production-control-api          BFF (FastAPI, production_control_app)
      JWT Keycloak + permissão + filial (BranchAccessService)
      envelope { success, message, data }
      X-Delpi-Caller-App: production-control-api
  → api-delpi                             contratos TOTVS (somente leitura neste fluxo)
      DELPI_API_URL + API_DELPI_INTERNAL_SERVICE_TOKEN
  → TOTVS (SQL Server, tabelas/views SD4/SB2/SB1/SBZ/SH8/SD3…)
  → Postgres (postgres-plugins, schema production_control)
      persistência operacional do BFF (snapshots, pick plans, overrides…)
```

Observações verificadas:

- O MFE **não** chama api-delpi (`mfe-own-api-no-direct-api-delpi.mdc` respeitado; grep sem ocorrências no plugin).
- O BFF propaga o JWT do usuário nas leituras à api-delpi e usa token S2S quando não há usuário (cockpit público). `contextvars` é replicado nos workers paralelos para não perder identidade.
- api-delpi **não** expõe escrita no TOTVS neste domínio: `/data/sql` é SELECT-only; não há rota de transferência/mutuação de estoque no inventário lido.
- Cockpit do operador existe como superfície pública: `public-hub` `/p/production-control/cockpit/{token}` → rotas `/public/machine-load/{token}/*` do mesmo BFF (somente leitura + sessões de bancada/runs do operador).

---

## 11. Target architecture

Decisões de arquitetura **com suporte de evidência ou aprovação do Product Master**:

| Item | Classificação |
|---|---|
| `FACTORY_SUPPLY_PRODUCT_BOUNDARY` — capability de produto distinta, não subdomínio PCP | `PLANNED` — Product Master aprovado |
| `PRODUCTION_CONTROL_LINE_FEEDER` — referência de implementação e inventário | `PROVEN_REFERENCE_IMPLEMENTATION` |
| `PRODUCTION_CONTROL_API` como backend do Factory Supply | `REJECTED_BY_PRODUCT_ARCHITECTURE` |
| `API_DELPI` como fronteira atual de leituras TOTVS do Factory Supply | Product Master aprovado, sujeito às regras canônicas de API/segurança |
| Persistência operacional Factory Supply em Postgres Minha DELPI (schema/boundary dedicado) | `PLANNED` |
| Capability de escrita TOTVS | `NOT_AVAILABLE_CURRENTLY` |
| Topologia HTTP/BFF final | reconciliada com regras canônicas — ver abaixo |

### Topologia HTTP — reconciliação com regras canônicas

`mfe-own-api-no-direct-api-delpi.mdc` + `application-bounded-context-decoupling.mdc` + `platform-frontend-mfe-experience.mdc` exigem: MFE com API própria nunca chama api-delpi direto; regra/escopo/persistência de produto vive na API dona do bounded context; api-delpi só recebe path TOTVS puro, sem regra do consumidor.

Como Factory Supply tem **persistência operacional própria** (§ 9 do prompt: Postgres dedicado) e **writes operacionais** (não-TOTVS), as regras canônicas implicam **backend/BFF dedicado ao produto**:

```text
Portal / Minha DELPI
        │
        ▼
Factory Supply (superfície de usuário)
        │
        ├──► backend dedicado do Factory Supply
        │       ├── estado operacional → Minha DELPI PostgreSQL (schema próprio)
        │       └── leituras ERP ──► API DELPI ──► TOTVS
        │
        └── nunca → api-delpi direto do MFE
```

Este diagrama é conceitual. **Não** congela nome de pacote/serviço: o nome técnico `factory-supply` está aprovado como identidade de produto; se o pacote final será `plugins/factory-supply` + `factory-supply-api` ou equivalente é decisão de implementação futura — **não** autorização de scaffold.

### Evolução futura (contexto, não runtime)

Factory Supply pode vir a integrar um **Portal de Produção** mais amplo. Nesse cenário, contratos hoje na api-delpi podem migrar para uma API de domínio de produção dedicada — razão pela qual o domínio Factory Supply não deve depender de detalhes de implementação da api-delpi nem de ownership PCP. Não criar esse portal agora.

---

## 12. Factory Supply × Line Feeder

| | Line Feeder (hoje) | Factory Supply (alvo) |
|---|---|---|
| Pergunta respondida | "O que precisa estar em cada bancada até o corte?" | "O que aconteceu com o material entre a necessidade e a devolução?" |
| Dono atual | `production-control` / `production-control-api` | produto próprio (boundary § 11) |
| Natureza | cockpit de necessidade + lista de coleta | workflow operacional com rastro |
| Fonte de necessidade | fila congelada (SH8) + empenho (SD4) + saldo (SB2) | mesma fonte planejada + sinais adicionais (§ 14) |
| Escopo | bancada → material → a entregar | necessidade → preparo → coleta → entrega → devolução |
| Persistência | `line_feeder_pick_plans` + `line_feeder_pick_items` (1 item/produto) | agregado operacional a definir (Doc 2/5) |

O Line Feeder permanece capability ativa do Portal PCP. A relação é de **origem e referência**: seu motor de necessidade, rateio FIFO, modelo de lista e padrões de degradação são o inventário probatório do Factory Supply. Nada aqui migra, renomeia ou desliga o Line Feeder — decisões de convivência/migração pertencem às documentações seguintes.

O modelo PickPlan/PickItem existente é `PROVEN_REFERENCE_IMPLEMENTATION`: a Doc 2/5 deve avaliar, via Abstraction Gate, se seus conceitos são generalizáveis, migráveis, substituíveis ou se permanecem específicos do PCP/Line Feeder. O agregado operacional final do Factory Supply **não está congelado**.

---

## 13. Information architecture

Superfícies conceituais-alvo (`TARGET` — não congela telas/componentes; detalhe na Doc 3/5):

| Superfície | Conteúdo conceitual |
|---|---|
| Visão geral | Resumo operacional do fluxo |
| Abastecimento | Workflow do alimentador — subvisões candidatas: Kanban, Necessidades, Minha coleta, Necessidades futuras/próximos períodos |
| Almoxarifado | Workflow de preparo do almoxarifado **específico ao abastecimento fabril** — Factory Supply não é WMS genérico |
| Devoluções | Workflow de retorno produção → almoxarifado |
| Histórico | Rastreabilidade operacional |

**Kanban como decisão de produto:** visualização **operacional**, não alternativa decorativa a tabela. Colunas candidatas (a validar contra o modelo de domínio da Doc 2/5):

```text
Abastecimento:   A separar → Em coleta → Pronto → Entregue
Almoxarifado:    A preparar → Em separação → Pronto para retirada → Handoff
Devoluções:      A recolher → Em retorno → Recebimento → Concluído
```

Drag-and-drop **não** é presumido: transição de Kanban pode representar evento operacional material, exigindo ação explícita, autorização, idempotência e auditoria.

---

## 14. Demand signals

O produto deve distinguir **fontes diferentes** de necessidade de material:

| Sinal | Origem | Status |
|---|---|---|
| Necessidade planejada/calculada | Programação + dados autoritativos de produção (SH8 + SD4 hoje) | `PROVEN` (é o que o Line Feeder já computa) |
| Solicitação do operador | Cockpit do Operador → Factory Supply | `TARGET` |
| Antecipação do alimentador | Alimentador identifica necessidade futura (ex.: próximo turno/dia) | `TARGET` |
| Contexto/intervenção PCP | Onde contratos/autoridade existentes permitirem | `TARGET` |

**Invariante:** os sinais não se sobrescrevem silenciosamente. Necessidade planejada às 10:00 + pedido do operador às 08:30 **não** reescreve a história como "planejado às 08:30". Planejamento e solicitação operacional permanecem fatos distintos no rastro. Regras de reconciliação: Doc 2/5.

---

## 15. Operational traceability

Objetivo: preservar o rastro operacional de ponta a ponta, sem substituir a verdade oficial de estoque.

Dimensões candidatas de rastro (disponibilidade classificada por fonte):

| Dimensão | Disponibilidade hoje |
|---|---|
| necessidade de material, OP, operação, CT, material, quantidade requerida | `PROVEN` (api-delpi SD4 + fila SH8) |
| tempo planejado (início programado da operação) | `PROVEN` (snapshot de carga máquina / `scheduled_start`) |
| fonte da necessidade (planejada vs pedida) | `TARGET` — hoje só existe a planejada |
| preparo, local de retirada | parcial — `PROVEN` local (`BZ_MPLOCAL`); estado de preparo `TARGET` |
| referência da transação oficial | `TARGET` (correlação via SD3 existe como leitura; vínculo causal é a modelar) |
| coleta, handoff, entrega, devolução | `TARGET` |
| timestamps + atores autenticados | parcial — `created_by`/`updated_by` `PROVEN` na referência; ator por transição `TARGET` |
| resultado (outcome) | `TARGET` |

---

## 16. Integration boundaries

| Sistema | Relação | Status |
|---|---|---|
| Portal / Minha DELPI | Host do MFE; manifest, rotas e menu via Core API | `PROVEN` (padrão vigente) |
| Core API | RBAC/permission resolver, manifests, auditoria da plataforma | `PROVEN` (governança transversal) |
| Keycloak | IdP; JWT identifica contexto autenticado | `PROVEN` |
| production-control (MFE) + production-control-api | Referência de implementação; **sem** dependência no alvo | `PROVEN_REFERENCE_IMPLEMENTATION` |
| api-delpi | Fronteira atual de leituras TOTVS | Product Master aprovado |
| TOTVS | Fonte autoritativa de ERP | `PROVEN` |
| production-pulse-api | Telemetria de contagem (contexto do Line Feeder/cockpit) | `PROVEN` no contexto production-control; relevância ao Factory Supply `TO_INVENTORY` |
| public-hub | Hospeda o Cockpit do Operador (superfície pública) | `PROVEN` |
| Cockpit do Operador | Futura entrada de solicitação semântica de material | `TARGET` — fronteira de integração apenas; sem acoplamento a internals de UI do cockpit; contrato na Doc 4/5 |
| Power BI "Painel Alimentador Fábrica" | Origem de requisitos/evidência conceitual | Entrada de requisitos — **não** fonte autoritativa de regra; internals `TO_INVENTORY` |

Integração futura Cockpit → Factory Supply é **semântica** (solicitação de material via contrato), nunca interação de DOM nem acoplamento a internals do cockpit.

---

## 17. Security and authorization principles

Backend-first, fail-closed — conforme `platform-security-identity-authorization.mdc`:

- JWT identifica contexto autenticado; **não** é autorização final.
- Visibilidade no frontend não autoriza ação; writes exigem AuthZ de backend; autoridade de domínio valida regra de negócio final.
- Writes de workflow de material exigem **idempotência** onde replay pode duplicar efeito, e **auditoria** de transições.
- Transações oficiais de estoque exigem execução autoritativa — hoje **fora** do Factory Supply (TOTVS writes indisponíveis).
- Secrets/tokens nunca em prompt, logs comuns, persistência de MFE ou configuração visível além dos mecanismos legítimos de auth.
- Distinções: `read ≠ write`; `recommendation ≠ authorization`; `preparation ≠ official transfer`; `collection ≠ delivery`; `delivery ≠ consumption`; `technical success ≠ verified business outcome`.
- Frontend jamais é autoridade de estoque, quantidade de devolução, empenho, consumo, transferência oficial, permissão ou regra de negócio final — a **quantidade de devolução** virá de regra/contrato de backend autoritativo, nunca de fórmula em React.
- Permissões por ator (operador, almoxarifado, alimentador, PCP): ~~`TO_INVENTORY`~~ — RESOLVIDO FS-C0.T3/T4: 3 permissões usuário (`access`+`view.filial-*`), papéis = contexto, não permission codes (TC §40-A).

---

## 18. Current proven capabilities (Line Feeder — reference implementation)

Inventário `PROVEN` da capability existente:

**Necessidade por bancada** (`GET /line-feeder/requirements`):

- elegibilidade por corte `scheduled_date` + `scheduled_start_time` sobre a **fila congelada** (snapshot `machine_load_snapshots`; conjunto retirado não gera necessidade);
- apenas matéria-prima (`B1_TIPO = MP`); PI/PA fora;
- `required_qty` = Σ `D4_QUANT` em aberto; `point_of_use_qty` (armazém ponto de uso, hoje `99`) e `source_available_qty` (almoxarifado, hoje `01`) rateados **FIFO por horário programado** — o saldo é por produto, não por bancada; recorte de tela (`workCenter`, `status`) vem depois do rateio global;
- situações: `covered` / `to_pick` / `at_risk` / `unknown` (saldo ilegível nunca afirma cobertura);
- detalhe por MP (`GET /line-feeder/products/{code}`): saldo real do almoxarifado, bancadas do corte, transferências recentes pareadas DE0→RE0 (SD3), bloqueio de inventário;
- degradação: empenho falha → `502` (não degrada); saldo/local/bloqueio degradam com `available: false` + mensagem;
- performance: fatiamento de OPs (`commitmentBatchSize` 100, teto 300/lote da api-delpi), fan-out paralelo (`fetchMaxWorkers` 6), cache por `branch + cutoff` (`cacheTtlSeconds` 120 s); identidade do chamador preservada nos workers via `contextvars`.

**Lista de coleta** (`/line-feeder/pick-plans`):

- `POST` congela o que falta entregar (recusa sem saldo medido); um item **por produto** (soma entre bancadas), `pickup_location` fotografado do cadastro; `UNIQUE (plan_id, product_code)`;
- item transiciona `pending ↔ picked ↔ delivered` (`PATCH …/items/{itemId}`); plano fecha (`POST …/close`) e recusa alteração;
- acesso filtrado por `branch` em **toda** leitura/escrita (id de outra filial não é legível nem editável);
- auditoria: `created_by`/`updated_by` (ator) + `created_at`/`updated_at`;
- `created_by`/`updated_by`, envelope e erros seguem padrões do BFF (`{ success, message, data }`, 403/404/422/502).

**Autorização:** uma permissão governa ver necessidade e mexer na lista — `production-control.line-feeder.view` + `production-control.view.filial-{01|02}`; decisão registrada no README do BFF (o papel operacional do alimentador é um só).

**Sem escrita no Protheus:** a lista é controle operacional da plataforma; nenhuma requisição/empenho/transferência é gerada no ERP.

**MFE:** página com KPIs, tabela/cards por viewport, painel de lista de coleta, modal de detalhe de produto, deep links via URL, componentes `@delpi/plugin-ui` (`createDashboardKpiCard`, `createDashboardStatusBadge`, `createDashboardLoadingActivityCard`, `DataTableSection`), textos PT-BR em `content/`.

**Testes:** `test_line_feeder.py`, `test_line_feeder_domain.py`, `test_line_feeder_warehouse_transfers.py` cobrindo rateio FIFO, degradação, permissão, isolamento de filial, ciclo de vida da lista e pareamento de transferências.

---

## 19. Product decisions frozen

| Decisão | Valor |
|---|---|
| Nome técnico | `factory-supply` |
| Nome user-facing | Abastecimento Fabril |
| Identificador técnico `abastecimento-fabril` | Proibido |
| Renomear para `line-feeder` | Proibido — `line-feeder` é a capability existente mais estreita, origem da evolução |
| Boundary | capability de produto **distinta** de production-control/PCP |
| production-control-api como backend-alvo | Rejeitado (arquitetura de produto) |
| api-delpi | fronteira atual de leituras TOTVS |
| Escrita TOTVS | indisponível; fora do runtime atual |
| Persistência operacional | Postgres Minha DELPI, boundary/schema dedicado (PLANNED) |
| Duas verdades | ERP (autoritativo) × operacional (Factory Supply) — nunca fundir |
| Handoff/entrega/devolução | fatos operacionais, não mutação de estoque |
| Documentação raiz | `docs/12-roadmap-e-evolucao/factory-supply/` — convenção do repo (raiz própria por produto: supplies/, commercial/, financial/, helpdesk/…) |

---

## 20. Decisions intentionally NOT frozen

- topologia final de pacote/serviço (nomes concretos de MFE/API);
- superfície final de API (rotas, operationIds, contratos);
- máquina(s) de estado finais (necessidade, preparo, coleta, entrega, devolução);
- schema/migrations finais;
- fórmula/fonte autoritativa da quantidade de devolução;
- ~~catálogo de permissões por ator~~ — decidido FS-C0.T3: 3 permissões `access`+`view.filial-{01|02}` (TECHNICAL-CONTRACTS §40-A);
- colunas Kanban finais e interação (drag-and-drop não presumido);
- `SupplyMission` (Missão de Abastecimento) como entidade: candidato conceitual `TARGET` — pode correlacionar need → request → preparo → transferência oficial → coleta → handoff → entrega → devolução, mas **não** é declarado agregado obrigatório por ter sido nomeado; Doc 2/5 avalia o modelo existente e aplica Abstraction Gate (`PROVEN`/`PLANNED`/`TARGET`/`REJECTED_BY_EXISTING_MODEL`/`TO_INVENTORY`);
- convivência/migração entre o modelo PickPlan do Line Feeder e o agregado operacional do Factory Supply;
- granularidade da lista de coleta (por produto vs por bancada vs por missão);
- relevância de `production-pulse-api` ao fluxo de abastecimento.

---

## 21. Gaps / TO_INVENTORY

| Item | Por quê |
|---|---|
| ~~Fórmula autoritativa da quantidade de devolução~~ — RESOLVIDO FS-C0.P2: baseline Power BI provado (`MAX(0, stock99 − empenho)` = `erp_global_return_capacity`); modelo híbrido 3-camadas congelado (Doc 2/5 §15-B, Doc 4/5 §53.7) |
| Internals do painel Power BI "Painel Alimentador Fábrica" | Não documentado no repositório; conceitos são entrada de requisito, não regra |
| Contrato de leitura para correlacionar transação oficial ↔ missão | `internal-movements` prova o movimento (SD3); vínculo causal com a missão a modelar |
| ~~Catálogo de permissões por ator~~ — RESOLVIDO FS-C0.T3 | Modelo FROZEN: `factory-supply.access` + `view.filial-01` + `view.filial-02`; papéis são contexto de negócio, não permission codes (TC §40-A) |
| Handoff (ator→ator com timestamp/quantidade/origem/destino) | Conceito não existe no modelo atual |
| Solicitação do operador | Sem contrato; cockpit atual é somente leitura + sessões/runs |
| Inventário/gap-analysis formal anterior do Line Feeder | Referenciado pelo programa documental, **não encontrado** no repo — o inventário é reconstruído aqui (§ 18) |
| Critério Abstraction Gate para `SupplyMission` | Depende do modelo de domínio da Doc 2/5 |
| Nome/empacotamento final do backend dedicado | Decisão de implementação; nome `factory-supply` aprovado ≠ autorização de pacote |

---

## 22. Documentation roadmap

Programa documental — exatamente 5 etapas:

| Etapa | Conteúdo | Estado |
|---|---|---|
| 1/5 | Product + Architecture Baseline | este documento |
| 2/5 | Domain + State Machines + Data + Contract Model | [DOMAIN-MODEL.md](./DOMAIN-MODEL.md) |
| 3/5 | Frontend + UX + Screens + Kanban + plugin-ui | [UX-SPEC.md](./UX-SPEC.md) |
| 4/5 | APIs + Routes + RBAC + Persistence + Integrations | [TECHNICAL-CONTRACTS.md](./TECHNICAL-CONTRACTS.md) |
| 5/5 | Implementation Roadmap + Requirements + Tests + Consolidation | [IMPLEMENTATION-ROADMAP.md](./IMPLEMENTATION-ROADMAP.md) |

**SPECIFICATION PROGRAM COMPLETE** — especificação 5/5 encerrada; runtime **não** implementado, produto **não** releaseado. Sem sexta fase.

---

## Referências

- Capability de referência: `plugins/production-control` (README § Alimentador de linha) + `production-control-api` (README § Alimentador de linha)
- Contratos api-delpi: `api-delpi/docs/api/13-producao-operacional.md`, `supplies-stock-balances.md`, `02-produtos.md`, `production-machine-load.md`, `production-pcp-orders.md`
- Regras canônicas: `platform-architecture-boundaries`, `application-bounded-context-decoupling`, `mfe-own-api-no-direct-api-delpi`, `platform-api-contracts-integration`, `platform-data-persistence`, `platform-security-identity-authorization`, `platform-frontend-mfe-experience`, `platform-quality-testing`, `plugins-reusable-components`, `plugins-visual-design-system`, `evidence-driven-execution`, `plan-construction`
- Relação com o módulo de origem: `docs/12-roadmap-e-evolucao/production-control/README.md`
