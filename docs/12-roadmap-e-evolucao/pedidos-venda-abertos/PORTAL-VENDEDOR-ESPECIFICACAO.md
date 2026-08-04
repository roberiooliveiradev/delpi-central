# Portal do Vendedor — especificação funcional e técnica

> **Arquivo:** `docs/12-roadmap-e-evolucao/pedidos-venda-abertos/PORTAL-VENDEDOR-ESPECIFICACAO.md`  
> **Status:** especificação + implementação parcial (Etapas 3–6 no working tree; sem commit)  
> **Plugin:** `pedidos-venda-abertos` · manifesto **`1.1.0`**  
> **Base:** diagnóstico Etapa 1 + contrato `GET /pedidos-venda-abertos/`  
> **Nome abandonado:** “Portal do Fornecedor” (não usar nesta iniciativa)

---

## 1. Objetivo

Evoluir o plugin `pedidos-venda-abertos` de uma tela isolada de pedidos em aberto para um **pequeno portal comercial orientado ao vendedor**, mantendo o mesmo `plugin-id`, container, autenticação e permissão do MVP.

O produto deve permitir que o vendedor responda em poucos segundos, durante ligação ou acompanhamento diário:

- quais **clientes** possuem pedidos de venda em aberto;
- quais clientes **precisam de atenção**;
- quais pedidos estão **atrasados**;
- qual cliente possui maior **valor em aberto**;
- qual é a **próxima entrega** prevista;
- quais pedidos foram **parcialmente atendidos**;
- quais pedidos ainda possuem **saldo**;
- o que verificar na conversa com o cliente (**check-up comercial**).

Princípio de experiência: **busca, atenção, clareza e detalhe** — não dashboard decorativo.

---

## 2. Decisões confirmadas

| Decisão | Valor |
|---------|--------|
| Domínio | **Clientes e pedidos de venda** |
| Nome funcional da iniciativa | **Portal do Vendedor** |
| Área de lista agregada (UI) | **Clientes** |
| Detalhe do cliente (UI) | **Check-up comercial do cliente** |
| Plugin | `pedidos-venda-abertos` (sem novo plugin) |
| `basePath` | `/apps/pedidos-venda-abertos` |
| Rota inicial | `/apps/pedidos-venda-abertos` (tela atual preservada) |
| Infra | mesmo `remoteEntry`, container Docker, HTTP client, JWT Portal |
| Permissão MVP | `pedidos-venda-abertos.access` |
| Fonte de dados MVP | Contrato atual de pedidos de venda em aberto (+ OPs já usadas na tela) |
| Navegação MVP | Abas / links horizontais internos: **Pedidos em aberto** \| **Clientes** |
| Faturamento / NF no MVP | **Não** |
| Novos contratos API no MVP | **Não** (agregação client-side sobre o dataset já carregado) |

### Identidade do cliente (chave confirmada)

Não agrupar somente por `nome_cliente`.

| Campo | Origem | Papel |
|-------|--------|--------|
| `codigo_cadastro` | `SC5.C5_CLIENTE` (LEFT JOIN no repository) | Código Protheus da contraparte |
| `loja_cadastro` | `SC5.C5_LOJACLI` | Loja Protheus (par obrigatório do cadastro) |

**Chave canônica de agrupamento e de rota:**

```text
clienteKey = codigo_cadastro + "|" + loja_cadastro
```

(ambos trimados; vazios tratados como dado incompleto — ver §14.)

**Evidências:**

- Tipos: `plugins/pedidos-venda-abertos/src/types/pedidosVendaAbertos.ts`
- SQL: `api-delpi/.../pedidos_venda_abertos_query_repository.py`
- Normalização: `list_pedidos_venda_abertos_use_case.py`
- Formatação UI existente: `formatEntityCodeStore(code, store)` → `codigo-loja`

| Campo avaliado | Faz parte da identidade? | Motivo |
|----------------|--------------------------|--------|
| `nome_cliente` | Não (apenas exibição) | Pode variar / não é único |
| `filial` | Não | Mesmo cliente pode ter pedidos em `01` e `02`; filial é contexto/filtro |
| `tipo_entidade` | Não na chave de rota | Classifica CLIENTE/FORNECEDOR na view; domínio do portal é comercial de **clientes**/PV; exibir como atributo se útil |
| `codigo_cliente` | Não | Part number / código do **produto no cliente**, não o cadastro Protheus |

**Formato de rota de detalhe recomendado:**

```text
/apps/pedidos-venda-abertos/clientes/:codigo/:loja
```

- `:codigo` = `codigo_cadastro` (URL-encoded)
- `:loja` = `loja_cadastro` (URL-encoded)
- Se `loja` vier vazia no dataset: usar segmento literal `_` e documentar no decode (edge case de JOIN incompleto)

---

## 3. Fora de escopo

Explicitamente **fora** desta iniciativa (incluindo MVP e nomenclatura):

- fornecedores do cadastro **SA2** (compras);
- pedidos de compra **SC7**;
- notas fiscais de **entrada**;
- inspeções de entrada / pendências de fornecedor;
- vínculo pedido de compra ↔ pedido de venda;
- funcionalidades de **suprimentos** ou compras;
- uso do termo **“Portal do Fornecedor”** na documentação e UI desta iniciativa.

Fora do **MVP** (segunda fase — ver §21): faturamento por cliente, NF de saída por cliente, carteira por vendedor, etc.

---

## 4. Personas e contexto de uso

| Persona | Contexto | Necessidade |
|---------|----------|-------------|
| **Vendedor** | Ligação / WhatsApp / reunião com cliente | Localizar cliente, ver atrasos e valor em aberto em &lt; 30 s |
| **Vendedor** | Acompanhamento diário da carteira em aberto | Fila de atenção + próximos prazos |
| **Supervisão comercial** (secundário) | Visão ampla com a mesma permissão | Mesmo dataset; sem filtro por vendedor no MVP |

**Não-persona no MVP:** comprador interno, PCP (exceto modal OP já existente na tela de linhas), financeiro (inadimplência).

---

## 5. Jornadas principais

### J1 — Abrir o módulo e ver pedidos (atual)

1. Menu Portal → “Pedidos em Aberto”.
2. Rota `/apps/pedidos-venda-abertos`.
3. Comportamento **idêntico** ao atual (KPIs, filtros, tabela, export, modal OP).

### J2 — Ver quais clientes precisam de atenção

1. Aba **Clientes**.
2. Ver fila de atenção no topo + lista completa.
3. Filtrar “somente com atraso” ou buscar por nome/código.

### J3 — Check-up antes/durante a ligação

1. Buscar cliente → abrir check-up.
2. Ler indicadores + pedidos que exigem atenção.
3. Expandir/consultar linhas; abrir previsão OP se necessário.
4. Voltar à lista de clientes.

### J4 — Deep link / refresh

1. Usuário atualiza a página em `/clientes/...` ou compartilha URL.
2. Portal mantém o app pelo `basePath`; MFE lê `pathname` e renderiza a área correta.

---

## 6. Arquitetura de informação

```text
Portal do Vendedor (plugin pedidos-venda-abertos)
├── Pedidos em aberto     ← dataset linha a linha (já existe)
└── Clientes              ← mesma fonte, agregada por codigo_cadastro+loja
    └── Check-up comercial do cliente
        ├── Indicadores
        ├── Pedidos que exigem atenção
        └── Todas as linhas em aberto do cliente
```

Uma única carga de dados de pedidos (e OPs, como hoje) alimenta as duas áreas no MVP. Sem segundo endpoint.

---

## 7. Navegação interna

| Item | Destino | Observação |
|------|---------|------------|
| Pedidos em aberto | `/apps/pedidos-venda-abertos` | Tela atual; **default** |
| Clientes | `/apps/pedidos-venda-abertos/clientes` | Nova |

- Padrão: **abas ou links horizontais** sob o header (sem menu lateral no MVP).
- A aba ativa deve ser evidente (texto + estilo; não só cor).
- Em mobile: navegação com rolagem horizontal se necessário.
- Check-up **não** entra na navegação de abas; acesso via lista + “Voltar para clientes”.

---

## 8. Rotas

| Rota | Tipo | Menu Portal | Conteúdo |
|------|------|-------------|----------|
| `/apps/pedidos-venda-abertos` | inicial | `showInMenu: true` (já existe) | Pedidos em aberto |
| `/apps/pedidos-venda-abertos/clientes` | interna | `showInMenu: false` (ao registrar) | Lista Clientes |
| `/apps/pedidos-venda-abertos/clientes/:codigo/:loja` | detalhe | `showInMenu: false` | Check-up |

### Refresh e deep link (Portal × plugin)

**Evidência Portal** (`portal/src/ui/AppHost.tsx`):

- Resolve o app se `pathname === basePath` ou `pathname.startsWith(basePath + "/")`.
- `resolveMatchingRoute` casa pelo **maior prefixo** das rotas do manifesto.
- Passa `pathname`, `basePath`, `getAccessToken` em `mount` / `updateRoute`.

**Requisitos futuros do MFE:**

1. Consumir `pathname` (hoje ignorado em `App.tsx`).
2. Manter `updateRoute` sincronizando a view interna sem remontar o remote desnecessariamente.
3. Declarar rotas internas no manifesto (`showInMenu: false`) para permissão/deep link explícitos — mesmo que o prefix match já cubra filhos da rota raiz.
4. Navegação interna preferencialmente via API do Portal (history) / `navigate` do shell, ou links absolutos sob `basePath`, para o browser refresh continuar no path correto.

**Cliente inválido / não encontrado:** ver §14.

---

## 9. Visão de clientes

### Agregação

Sobre `items[]` do contrato atual, agrupar por `codigo_cadastro` + `loja_cadastro`.

Para cada grupo, derivar:

| Coluna / informação | Regra |
|---------------------|--------|
| Código | `codigo_cadastro` |
| Loja | `loja_cadastro` (exibir se não vazia) |
| Nome | `nome_cliente` predominante no grupo (primeiro não vazio; se divergir, exibir o mais frequente) |
| Qtd. pedidos em aberto | `COUNT DISTINCT (filial, pedido)` com `saldo > 0` |
| Qtd. linhas em aberto | `COUNT` de linhas do grupo com `saldo > 0` |
| Valor total em aberto | `SUM(valor_aberto)` |
| Qtd. pedidos atrasados | `COUNT DISTINCT (filial, pedido)` com ao menos uma linha `isDeliveryOverdue(data_entrega, saldo)` |
| Maior atraso (dias) | `MAX(getDeliveryOverdueDays(data_entrega))` entre linhas atrasadas; senão “—” |
| Próxima entrega | `MIN(data_entrega)` entre linhas com `data_entrega` não nula e `saldo > 0` e **não** atrasadas; se só houver atrasadas, menor `data_entrega` atrasada ou “—” conforme regra §13 |
| Qtd. pedidos parcialmente atendidos | `COUNT DISTINCT (filial, pedido)` com ao menos uma linha `entregue > 0 AND saldo > 0` |
| Atenção | Indicador visual + texto se houver atraso (e opcionalmente parcial) — ver §11 |

### Resumo (cards)

Avaliação dos quatro candidatos:

| Card | Útil? | Decisão MVP |
|------|-------|-------------|
| Clientes com pedidos em aberto | Sim — tamanho da carteira | **Manter** |
| Clientes com atraso | Sim — urgência | **Manter** |
| Valor total em aberto | Sim — exposição financeira | **Manter** |
| Entregas próximas | Parcial — útil, mas sobrepõe fila/filtro | **Não** como 4º card; usar filtro “entrega nos próximos N dias” (N=7 sugerido) |

Três cards no máximo no MVP.

### Layout

Ver wireframe §24.

---

## 10. Check-up comercial do cliente

### Identificação

- Código (`codigo_cadastro`) e loja (`loja_cadastro`)
- Nome (`nome_cliente`)
- Filiais com pedidos no grupo (lista distinta de `filial`)
- `tipo_entidade` (exibição informativa)
- Data/hora da **última atualização** = momento do último fetch bem-sucedido no cliente (clock local / ISO formatado pt-BR) — não há campo de timestamp no contrato TOTVS

### Indicadores (somente dataset atual)

| Indicador | Incluir | Observação |
|-----------|---------|------------|
| Pedidos em aberto | Sim | distinct `(filial, pedido)` |
| Linhas em aberto | Sim | count linhas |
| Valor total em aberto | Sim | soma BRL |
| Pedidos atrasados | Sim | distinct |
| Maior atraso | Sim | dias |
| Próxima entrega | Sim | data |
| Pedidos parcialmente atendidos | Sim | distinct |
| Saldo total em quantidade | **Não** como KPI agregado | Unidades podem diferir entre produtos; saldo permanece **por linha** na tabela |

### Pedidos que exigem atenção

Lista curta (máx. sugerido: 10), ordenada pela mesma prioridade §11 aplicada às **linhas/pedidos** do cliente:

1. linhas/pedidos atrasados (maior atraso primeiro);
2. parcialmente atendidos;
3. entrega nos próximos 7 dias (não atrasados).

Campos: pedido, filial, produto, saldo, data entrega, valor aberto, badge de status (reuso).

### Todos os pedidos em aberto do cliente

Reutilizar padrões da tabela atual (`PedidosTable` / colunas / sort / badges / modal OP / export filtrado ao cliente), restritos às linhas do `clienteKey`.

Sem gráficos no MVP.

---

## 11. Fila de atenção

### Critérios objetivos (sem score oculto)

Um cliente entra na **fila de atenção** se:

1. possui **pelo menos uma** linha atrasada (`isDeliveryOverdue`), **ou**
2. possui **pelo menos um** pedido parcialmente atendido (`entregue > 0 AND saldo > 0`).

Ordenação **determinística** da fila (e default da lista completa quando “priorizar atenção”):

```text
1. tem_atraso DESC          (boolean 1/0)
2. maior_atraso_dias DESC   (0 se sem atraso)
3. valor_total_aberto DESC
4. tem_parcial DESC
5. proxima_entrega ASC      (nulos por último)
6. nome_cliente ASC         (desempate estável)
7. codigo_cadastro, loja    (desempate final)
```

**Pedidos sem `data_entrega`:** o contrato permite `null` (`_optional_date`). A Fase 0 **não** quantificou nulos de `data_entrega` (só de `data_despacho`). Portanto:

- **não** usar “sem prazo” como critério primário de atenção no MVP;
- se em runtime existirem linhas com `data_entrega == null` e `saldo > 0`, exibir badge “Sem data de entrega” e permitir filtro opcional — sem inventar volume.

Texto explicável ao vendedor (exemplo de ajuda):

> “Clientes com atraso aparecem primeiro; em empate, maior atraso em dias; depois maior valor em aberto.”

---

## 12. Busca e filtros

### Sempre visível

- **Busca principal:** texto livre contra `codigo_cadastro`, `loja_cadastro`, `nome_cliente`, e (nas linhas do grupo) `pedido`, `pedido_cliente` — se qualquer linha do cliente casar, o cliente entra no resultado.

### Filtros essenciais visíveis

- Filial (select; valores distintos do dataset)
- Somente com atraso (toggle)
- Somente parcialmente atendidos (toggle)

### Expansível (se necessário)

- Entrega nos próximos 7 dias
- Somente sem data de entrega (somente se houver ocorrências no dataset)

Evitar barra enorme; não duplicar todos os filtros da tela de linhas.

---

## 13. Matriz de dados e cálculos

Fonte base: item de `GET /apps/api-delpi/pedidos-venda-abertos/` (campos abaixo). OPs: `GET .../ops-abertas` — só para modal/previsão já existente nas linhas.

| Informação exibida | Campo de origem | Transformação | Regra | Limitação |
| ------------------ | --------------- | ------------- | ----- | --------- |
| Código do cliente | `codigo_cadastro` | trim | Chave com loja | Pode vir vazio se JOIN SC5 falhar |
| Loja | `loja_cadastro` | trim | Chave com código | Idem |
| Nome / razão social | `nome_cliente` | trim; modo no grupo | Só exibição | Não usar como chave |
| Tipo entidade | `tipo_entidade` | exibir | Informativo | CLIENTE ou FORNECEDOR na view; domínio = PV |
| Filial (contexto) | `filial` | distinct no grupo | Filtro / lista no check-up | Não é identidade |
| Pedido | `pedido` | — | Com `filial` forma chave do pedido | Números podem repetir entre filiais |
| Linha | `linha` | — | Item do pedido | — |
| Produto | `produto` | — | Exibição | — |
| Cód. produto no cliente | `codigo_cliente` | — | Busca / coluna | ≠ cadastro Protheus |
| Pedido do cliente | `pedido_cliente` | — | Busca | — |
| Qtd. pedida | `quantidade` | number | Por linha | Não agregar no KPI de check-up |
| Entregue | `entregue` | number | Parcial se &gt; 0 e saldo &gt; 0 | — |
| Saldo | `saldo` | number | Aberto se &gt; 0 | Não somar KPI entre UMs distintas |
| Valor em aberto | `valor_aberto` | sum no grupo | BRL | Null → 0 (já no use case) |
| Preço | `preco_venda` | — | Por linha | — |
| Data entrega | `data_entrega` | ISO / dd/MM/yyyy | Atraso / próxima | Pode ser `null` |
| Data despacho | `data_despacho` | — | Coluna linhas (já existe) | ~70% nulo (Fase 0) |
| Estoque view | `no_estoque` | alocação FIFO existente | Badges tela linhas | Client-side |
| Pedidos em aberto (cliente) | `filial`+`pedido` | distinct count | `saldo > 0` | ≠ count de linhas |
| Linhas em aberto | — | count | `saldo > 0` | — |
| Valor total aberto (cliente) | `valor_aberto` | SUM | — | — |
| Pedidos atrasados | `data_entrega`, `saldo` | `isDeliveryOverdue` + distinct pedido | Utilitário **já existe** | Timezone = data local do browser (`getTodayIsoDate`) |
| Maior atraso (dias) | `data_entrega` | `getDeliveryOverdueDays` + MAX | Utilitário **já existe** | — |
| Próxima entrega | `data_entrega` | MIN futura não atrasada | **Novo utilitário** de agregação | Nulos excluídos do MIN |
| Parcialmente atendidos | `entregue`, `saldo` | distinct pedido | **Nova** regra explícita (não confundir com estoque parcial) | ≠ `estoque_parcial` |
| Indicador atenção | derivados | flags | §11 | Texto + cor |
| Atualizado em | — | `Date` do fetch | Client-only | Sem timestamp TOTVS |
| Previsão OP | OPs + alocação | existente | Modal | Falha OP não bloqueia clientes |

### Contagens — pedidos vs linhas

| Conceito | Definição |
|----------|-----------|
| **Linha** | Um item do array `items` (granularidade da view) |
| **Pedido** | Par `(filial, pedido)` distinto |

Risco de **dupla contagem:** somar `valor_aberto` por linha é correto; contar “pedidos” sem `DISTINCT` inflaria números. Nunca usar `nome_cliente` para distinct de cliente.

### Utilitários

| Cálculo | Situação |
|---------|----------|
| `isDeliveryOverdue`, `getDeliveryOverdueDays`, `formatDisplayDate`, `compareDeliveryDates` | **Já existem** (`utils/dates.ts`) |
| `formatEntityCodeStore` | **Já existe** |
| `computeSummaryFromItems` | Existe para **linhas**; não substitui agregação por cliente |
| `getClientKey` atual | Usa **nome** — **não** reutilizar para Portal; criar `getCustomerIdentityKey` |
| Agregação por cliente / fila / filtros clientes | **Novos** em `features/customers/utils` |
| Status parcial de **entrega** | Novo helper; não reusar só `isParcialStatus` (estoque) |

### Monetário e nulos

- Valores: `formatCurrency` existente; null/undefined → 0 na soma.
- Datas nulas: exibir “—”; não entram em atraso (`isDeliveryOverdue` já exige data).
- `codigo_cadastro` vazio: grupo “Cadastro incompleto” ou exclusão da lista navegável + aviso (§14).

---

## 14. Estados da interface

| Estado | Comportamento |
|--------|----------------|
| Carregamento inicial | State-box / loading nas duas áreas até pedidos (e OPs) resolverem; mesma fonte |
| Atualização manual | Botão Atualizar (já na tela de pedidos); na área Clientes, mesmo fetch; preservar filtros se possível |
| Erro da API (pedidos) | Mensagem + “Tentar novamente”; Clientes e Pedidos indisponíveis |
| Sessão expirada (401) | Mensagem clara de sessão; orientar relogin Portal (melhorar vs. “Erro HTTP 401” genérico) |
| Acesso negado (403) | Mensagem de sem permissão; sem dados parciais falsos |
| Dataset vazio | “Nenhum pedido em aberto”; aba Clientes: “Nenhum cliente com pedidos em aberto” |
| Nenhum cliente encontrado (filtro) | Empty state de filtro + limpar filtros |
| Nenhum pedido atrasado | Fila de atenção pode mostrar só parciais, ou mensagem “Nenhum cliente com atraso” se filtro ativo |
| Rota cliente inválida (segments faltando) | Redirect para `/clientes` + aviso |
| Cliente não encontrado (código/loja sem linhas) | Empty check-up + link voltar (dataset pode ter mudado após refresh) |
| Dados parcialmente incompletos | Badge “Cadastro incompleto”; sem deep link estável se chave vazia |
| Falha ao abrir previsão OP | Manter warning de OP já existente na tela de linhas; no check-up, modal exibe vazio/erro sem derrubar a página |
| Falha só em OPs | Pedidos/Clientes seguem; previsão degradada (comportamento atual) |

---

## 15. Responsividade

| Viewport | Comportamento |
|----------|----------------|
| Desktop (&gt; 1100px) | Abas + tabela clientes completa + 3 KPIs em linha |
| Notebook | Idem; colunas secundárias podem ocultar via preferência |
| Tablet (≤ 1100px) | KPIs 2 colunas; filtros empilhados |
| Celular (≤ 768px) | Abas com scroll horizontal; KPIs essenciais (atraso + valor); filtros recolhíveis; lista clientes em **cards** priorizando nome, atraso, valor; detalhes (loja, parcial) em expansão; **sem** ações só no hover |

Padrão visual: manter prefixo/escopo `.dashboard-pedidos-venda-abertos` e tokens existentes.

---

## 16. Acessibilidade

Exigências:

- navegação por teclado nas abas, busca, tabela/cards e botão voltar;
- foco visível (`outline` accent já usado no plugin);
- labels em inputs/toggles (`aria-label` / `FieldLabel` do kit);
- contraste adequado claro/escuro (`data-theme`);
- status **não** só por cor (texto do badge + ícone quando couber);
- hierarquia `h1`/`h2` coerente (título da área / seções);
- tabelas com `<th>` / escopo ou padrão card com `data-label` no mobile (já na tela de pedidos);
- erros com `role="alert"` próximos ao contexto;
- zoom até 200% sem perda de ação crítica;
- modal OP: preferir evolução para diálogo contido no host (dívida atual `PvaModal`); Escape fecha.

---

## 17. Arquitetura frontend recomendada

### Alvo incremental

```text
src/
  app/
    routes/           # parse pathname × basePath; mapear views
    navigation/       # abas Pedidos | Clientes
  shared/
    api/              # httpClient + pedidosVendaAbertosApi (permanecem)
    components/       # PageHeader, KpiCard, Pagination, StatusBadge…
    utils/            # dates, format, entityCodeStore, statusBadges…
    types/            # tipos do contrato
  features/
    open-sales-orders/  # página/tabela/filtros atuais (migração gradual)
    customers/
      pages/            # CustomersPage, CustomerCheckupPage
      components/
      hooks/
      services/         # aggregateCustomers(items) — puro
      types/
      utils/
```

### O que pode permanecer no lugar no início

- `api/httpClient.ts`, `api/pedidosVendaAbertosApi.ts`
- `utils/dates.ts`, `format.ts`, `statusBadges.ts`, `stockAllocation.ts`, `opAllocation.ts`, export Excel
- `pages/PedidosVendaAbertosPage.tsx` como implementação da aba Pedidos (sem reescrita)
- `hooks/usePedidosVendaAbertos.ts` como fonte única de fetch

### Reuso

| Peça | Reuso |
|------|--------|
| Fetch + AbortSignal | `usePedidosVendaAbertos` compartilhado no shell |
| Badges / datas / currency | shared utils |
| Tabela de linhas no check-up | extrair props de `PedidosTable` ou passar `items` filtrados |
| FilterBarShell / KPI / Pagination | `@delpi/plugin-ui` via wrappers atuais |
| Export | opcional no check-up com `exportRows` filtrados |

### Evitar acoplamento

- `features/customers` **não** importa `PedidosVendaAbertosPage`.
- Consome `PedidosVendaAbertosItem[]` + funções puras de agregação.
- Shell (`App`) escolhe feature conforme rota.

### Lazy loading

```text
React.lazy(() => import("./features/customers/pages/CustomersPage"))
```

Aba Pedidos pode permanecer eager (rota default). Check-up lazy junto com Clientes.

### Evitar reescrita geral

1. Introduzir router + abas com a página atual intacta.
2. Adicionar agregação + lista Clientes.
3. Adicionar check-up reutilizando tabela.
4. Só então mover arquivos para `features/open-sales-orders` (opcional).

---

## 18. Permissões

### MVP

```text
pedidos-venda-abertos.access
```

Única permissão; cobre Pedidos, Clientes e Check-up.

### Evolução futura (candidatos — não registrar agora)

```text
pedidos-venda-abertos.clients.view
pedidos-venda-abertos.export
```

Confirmar padrão com RBAC/Core API antes de criar.

---

## 19. Impacto no manifesto (Etapa 6 — registrado)

| Campo | Valor |
|-------|--------|
| `id` | `pedidos-venda-abertos` (preservado) |
| `name` | **Portal do Vendedor** |
| `basePath` | `/apps/pedidos-venda-abertos` (preservado) |
| `entry` | `/apps/pedidos-venda-abertos/assets/remoteEntry.js` |
| `version` | **`1.1.0`** (anterior `1.0.0`; incremento MINOR) |
| `permissions` | somente `pedidos-venda-abertos.access` |
| `routes[0]` | `/apps/pedidos-venda-abertos` — `showInMenu: true`, label **Portal do Vendedor** |
| `routes[1]` | `/apps/pedidos-venda-abertos/clientes` — `showInMenu: false` |

### Rota dinâmica de check-up

**Não declarada no manifesto.** A Core API rejeita paths fora de `PATH_RE` (`^/[-a-z0-9/]*$`); placeholders `:codigo` / `:loja` são inválidos. O Portal monta hosts federados como `` `${basePath}/*` `` e `resolveMatchingRoute` usa o maior prefixo estático — `/clientes/000123/01` casa com `/clientes` (ou com a rota raiz). O MFE resolve o detalhe internamente.

Registro: `plugins/pedidos-venda-abertos/scripts/register-manifest.sh` (nova versão via POST register, não update).

**Operação (Etapa 6):** container `delpi-pedidos-venda-abertos` reconstruído; `remoteEntry.js` HTTP 200. Registro na Core API **pendente** neste ambiente: `get-dev-token.sh` retorna `unauthorized_client` / *Client not allowed for direct access grants* no client `delpi-central`. Comando a executar após habilitar Direct Access Grants (ou obter JWT admin por outro fluxo):

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
bash plugins/pedidos-venda-abertos/scripts/register-manifest.sh
# Confirmar: GET /core-api/admin/apps/pedidos-venda-abertos/versions
# Rollback oficial se necessário: POST /core-api/admin/apps/pedidos-venda-abertos/rollback
```

---

## 20. MVP

1. Navegação interna **Pedidos em aberto** \| **Clientes**.
2. Preservar 100% o comportamento da tela atual na primeira aba.
3. Lista **Clientes** agregada por `codigo_cadastro` + `loja_cadastro`.
4. Fila de atenção com regra §11.
5. Busca + filtros essenciais §12.
6. Três KPIs de resumo §9.
7. **Check-up comercial do cliente** §10 (sem saldo agregado; sem gráficos).
8. Rotas §8 consumindo `pathname` / `updateRoute`.
9. Mesma permissão `.access`; mesmos endpoints atuais.
10. Estados §14, responsividade §15, a11y §16.

**Não incluir no MVP:** NF, faturamento, placeholders de indicadores futuros, novo plugin, nova permissão, menu Portal adicional.

---

## 21. Segunda fase

Registrar para depois (sem UI fictícia no MVP):

| Tema | Referência existente (não é contrato do MVP) | Necessidade provável |
|------|-----------------------------------------------|----------------------|
| Faturamento por cliente | `/products/{code}/sales/billing`, `/commercial/rol/by-customer` | Endpoint **por cliente** (código+loja), período, totais e/ou série |
| NF saída por cliente | `/products/{code}/outbound-invoice-items` (filtro `customer`) | Listagem **por cliente** (não só por produto), paginada |
| Histórico / última NF | — | Campos derivados do contrato por cliente |
| Tendências / comparativos | OTD/ROL comerciais | Definição de período e métricas |
| Carteira por vendedor | ROADMAP Fase 6; sem campo na view atual | Campo TOTVS + filtro server-side |
| Filtros salvos / favoritos / alertas | — | Persistência (Portal ou API) |
| Paginação server-side | ROADMAP Fase 6 | Se volume crescer |
| Export específico da visão clientes | Export Excel linhas já existe | Export da agregação |
| Permissões granulares | candidatos §18 | RBAC |

**Contrato futuro (conceitual, sem SQL):** algo na família `GET /pedidos-venda-abertos/clientes/{codigo}/{loja}/...` ou módulo commercial com `customer_code` + `store` + período — a definir na Etapa de API; **não** inventar campos aqui.

---

## 22. Critérios de aceite

- [ ] Rota inicial continua exibindo a tela atual sem regressão funcional.
- [ ] Abas Pedidos \| Clientes navegáveis; deep link e F5 em `/clientes` e check-up funcionam via Portal.
- [ ] Clientes agrupados por `codigo_cadastro` + `loja_cadastro`, **nunca** só por nome.
- [ ] Contagem de **pedidos** ≠ contagem de **linhas**; distinct `(filial, pedido)`.
- [ ] Atraso usa as mesmas regras de `dates.ts` que a tela de linhas.
- [ ] Parcial = `entregue > 0 AND saldo > 0` (entrega), não confundir com estoque parcial.
- [ ] Fila de atenção ordenada pela regra documentada (sem score oculto).
- [ ] Check-up sem KPIs de faturamento/NF; sem saldo agregado enganoso.
- [ ] Nenhum termo “Portal do Fornecedor” / SA2 / SC7 no escopo entregue.
- [ ] Permissão MVP apenas `pedidos-venda-abertos.access`.
- [ ] Sem novo container / plugin-id / remoteEntry.

---

## 23. Riscos e decisões futuras

| Risco / decisão | Impacto | Mitigação |
|-----------------|---------|-----------|
| `codigo_cadastro`/`loja` vazios | Clientes sem deep link estável | Grupo incompleto + aviso |
| Nome divergente no grupo | Confusão visual | Moda + tooltip se houver variantes |
| Timezone do “hoje” no atraso | Divergência vs SQL Server | Documentar; eventualmente data do servidor |
| Volume do dump completo | Performance com agregação extra | Mesma mitigação Fase 6 (server-side) |
| `getClientKey` legado por nome | Bug se reutilizado | Nova identidade; não reusar |
| Label do menu Portal | “Pedidos em Aberto” vs “Portal do Vendedor” | Decisão de produto |
| `tipo_entidade = FORNECEDOR` na view | Poucas linhas de PV com contraparte “FORNECEDOR” | Exibir no check-up; continua sendo PV, não compras |
| Carteira por vendedor | Todos veem tudo | Segunda fase |
| Modal OP full-viewport | A11y / shell | Migrar para HostContained no kit |
| Branch git ainda `feat/portal-fornecedor` | Nomenclatura legada | Renomear branch/docs operacionais quando conveniente |

---

## 24. Wireframes textuais

### 24.1 Pedidos em aberto (tela atual + navegação)

```text
┌─────────────────────────────────────────────────────────────────┐
│  Pedidos de Venda em Aberto          [Atualizar]  carregado: N  │
│  ┌──────────────────┐ ┌──────────┐                              │
│  │ Pedidos em aberto│ │ Clientes │   ← abas (Pedidos = ativa)   │
│  └──────────────────┘ └──────────┘                              │
├─────────────────────────────────────────────────────────────────┤
│  (conteúdo atual intacto)                                       │
│  KPIs existentes | FilterBar existente | Tabela | Paginação     │
│  Modal previsão OP inalterado                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 24.2 Clientes

```text
┌─────────────────────────────────────────────────────────────────┐
│  Clientes — carteira em aberto       [Atualizar]  Atualizado: … │
│  ┌──────────────────┐ ┌──────────┐                              │
│  │ Pedidos em aberto│ │ Clientes │   ← Clientes ativa           │
│  └──────────────────┘ └──────────┘                              │
├─────────────────────────────────────────────────────────────────┤
│  🔍 Busca: código, nome, pedido…                                │
│  Filial [▼]   [ ] Só atraso   [ ] Só parcial   [Mais filtros]   │
├─────────────────────────────────────────────────────────────────┤
│  ┌ Clientes abertos ┐ ┌ Com atraso ┐ ┌ Valor em aberto ┐       │
│  │       42         │ │     12     │ │  R$ 1.234.567   │       │
│  └──────────────────┘ └────────────┘ └─────────────────┘       │
├─────────────────────────────────────────────────────────────────┤
│  Clientes que exigem atenção                                    │
│  • ACME 01-01 | 3 atr. | máx. 12 d | R$ 80.000 | [Abrir]      │
│  • BETA 02-01 | 1 atr. | máx. 4 d  | R$ 15.000 | [Abrir]      │
├─────────────────────────────────────────────────────────────────┤
│  Todos os clientes                                              │
│  Código | Loja | Nome | Pedidos | Linhas | Valor | Atraso | … │
│  …                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 24.3 Check-up comercial do cliente

```text
┌─────────────────────────────────────────────────────────────────┐
│  ← Voltar para clientes                                         │
│  Check-up comercial do cliente                                  │
│  ACME INDUSTRIA  ·  Código 001234  ·  Loja 01  ·  Filiais 01,02 │
│  Tipo: CLIENTE  ·  Atualizado em 04/08/2026 08:30               │
├─────────────────────────────────────────────────────────────────┤
│  Pedidos 5 │ Linhas 18 │ Valor R$ … │ Atrasados 2 │ Máx. 12 d  │
│  Próxima entrega 10/08/2026 │ Parciais 1                        │
│  (sem KPI de saldo agregado; sem gráficos)                      │
├─────────────────────────────────────────────────────────────────┤
│  Pedidos que exigem atenção                                     │
│  [lista curta atrasados / parciais / próximos 7 dias]           │
├─────────────────────────────────────────────────────────────────┤
│  Todos os pedidos em aberto                                     │
│  [tabela no padrão da tela atual, filtrada ao cliente]          │
│  [export / colunas / modal OP quando aplicável]                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Referências

| Documento / código | Uso |
|--------------------|-----|
| `ESPECIFICACAO-VIEW.md` | Campos da view |
| `FASE0-VALIDACAO-VIEW.md` | Volume e nulos de despacho |
| `ROADMAP.md` | Fases 0–6 do plugin |
| `pedidos_venda_abertos_query_repository.py` | SQL + SC5 |
| `list_pedidos_venda_abertos_use_case.py` | Normalização / null datas |
| `plugins/pedidos-venda-abertos/src/types/pedidosVendaAbertos.ts` | Contrato TS |
| `utils/dates.ts`, `entityCodeStore.ts` | Regras de atraso e código-loja |
| `portal/src/ui/AppHost.tsx` | `pathname` + `updateRoute` |
| Diagnóstico Etapa 1 | Contexto e inventário API |

---

*Fim da especificação — Etapa 2. Nenhuma implementação de código associada a este arquivo.*
