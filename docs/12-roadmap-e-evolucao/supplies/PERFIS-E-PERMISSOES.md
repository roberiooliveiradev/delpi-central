# Perfis e permissões — Portal Suprimentos

> Papéis Minha Delpi **agrupam** codes. O MFE não autoriza por nome de cargo.  
> **Unidades:** eixo próprio — [ADR-006](./adr/ADR-006-unit-permissions.md).  
> Codes de unidade: `filial-01` / `filial-02` (exceção já adotada no repo); futuras = `filial-{codigo_totvs}`.

---

## Princípio — dois eixos (não misturar)

```text
Usuário → Papel(éis) → codes A (o quê) + codes B (onde) → API / MFE
```

| Eixo | Pergunta | Família de codes | Infla quando nasce… |
|------|----------|------------------|---------------------|
| **A — capability** | O que pode fazer no Portal? | `supplies.access`, `*.view`, `*.export`, `manage` | …uma **feature** nova de risco |
| **B — unidade** | Em quais sites TOTVS vê dado? | `supplies.unit.filial-{TOTVS}` | …uma **unidade** nova |

```text
pode_ler_dado = eixo_A AND eixo_B
```

O Comercial condensou capabilities porque carteira resolve o recorte de **cliente**. Suprimentos recorta **unidade TOTVS**: isso **não** se resolve copiando `filial-sc` em cada tela (padrão rejeitado do ESTSEG legado).

Justificativa para fragmentar o eixo A: risco de dado (solicitante ≠ analista ≠ export).  
**Não** fragmentar o eixo A por site.

---

## Eixo B — catálogo de unidades (tipo único)

Uma permission por unidade. Rótulo PT só na UI.

| Código TOTVS | Permission | Label UI | Status |
|--------------|------------|----------|--------|
| `01` | `supplies.unit.filial-01` | Santa Catarina (SC) | canônico |
| `02` | `supplies.unit.filial-02` | Espírito Santo (ES) | canônico |
| `XX` | `supplies.unit.filial-XX` | (nome da unidade) | quando o TOTVS ganhar filial |

**Nova unidade:** 1 linha neste catálogo + 1 permission no manifest `supplies` + atribuição nos papéis. **Nenhuma** capability do eixo A muda.

Fonte de verdade futura (E2): JSON de catálogo na `supplies-api` (código, permission, label). Rotas e o filtro de filial **consomem** o catálogo — sem `if branch == "01"` espalhado.

### Regras do eixo B

| Situação | Comportamento |
|----------|----------------|
| Tem capability, **zero** unit | Fail-closed: sem dado TOTVS (Home/Ajuda com `access` ok) |
| Uma unit | Dado só daquela filial; filtro travado ou único valor |
| Várias units | União; consolidado = só essas unidades (não a empresa toda) |
| `branch` na query fora do conjunto | **403** no BFF (nunca só ocultar no MFE) |
| `supplies.manage` | Não libera unidade. Papel Admin recebe units à parte |
| Superadmin | Bypass de unidade com auditoria |
| `purchase-requests.view-all` | Bypass de **CC**, não de unidade |

---

## Eixo A — catálogo de capabilities (sem coluna de filial)

| Capability | Permission | Comprador | Analista | Gestor | Admin |
|------------|------------|:---------:|:--------:|:------:|:-----:|
| Entrar no Portal (shell, busca, help) | `supplies.access` | ✓ | ✓ | ✓ | ✓ |
| Administração / settings | `supplies.manage` | — | — | opt | ✓ |
| Overview e KPIs | `supplies.analytics.view` | opt | ✓ | ✓ | ✓ |
| Solicitações (escopo CC) | `supplies.purchase-requests.view` | ✓ | opt | opt | ✓ |
| Bypass CC **dentro da unidade** | `supplies.purchase-requests.view-all` | ✓ típico | — | opt | ✓ |
| Exportar SC | `supplies.purchase-requests.export` | opt | opt | opt | ✓ |
| Pedidos / entregas / OTD operacional | `supplies.purchase-orders.view` | ✓ | opt | ✓ | ✓ |
| Fornecedores / 360 | `supplies.suppliers.view` | ✓ | opt | ✓ | ✓ |
| Produtos / 360 / onde-usado | `supplies.products.view` | ✓ | opt | ✓ | ✓ |
| Controle estoque + ESTSEG + consumo | `supplies.inventory.view` | ✓ | opt | ✓ | ✓ |
| Negociações / savings | `supplies.negotiations.view` | opt | ✓ | ✓ | ✓ |
| Worklist / alertas | coberto por `access` + caps de recurso | ✓ | ✓ | ✓ | ✓ |

Unidade **não aparece nesta tabela**. Quem vê SC, ESTSEG ou CPV de qual site é só o eixo B.

Admin de mapping CC: `supplies.manage` (não criar `supplies.purchase-requests.admin`).

---

## Como montar um papel (exemplos)

| Papel | Eixo A | Eixo B |
|-------|--------|--------|
| Suprimentos — Comprador SC | access + PR.view + view-all + PO + suppliers + products + inventory | `unit.filial-01` |
| Suprimentos — Analista SC e ES | access + analytics + negotiations | `unit.filial-01` **e** `unit.filial-02` |
| Suprimentos — Solicitante ES | access + PR.view (sem view-all) | `unit.filial-02` |
| Suprimentos — Gestor multi | Analista + inventory + suppliers + products | todas as units do catálogo vigente |
| Suprimentos — Admin | eixo A completo + manage | units que administra (em geral todas) |

Comprador ES no Core: ainda **HIPOTESE_A_VALIDAR** (E1.S2). O **modelo** já o admite: mesmo eixo A do comprador + só `filial-02`.

---

## Aliases obrigatórios (coexistência)

| Legado (não apagar) | Resolve para |
|---------------------|----------------|
| `dashboard-supplies.view` | eixo A `analytics.view` (**não** concede unidade) |
| `purchase-requests.access` | eixo A `purchase-requests.view` |
| `purchase-requests.view-all` | eixo A `view-all` |
| `purchase-requests.export` | eixo A `export` |
| `purchase-requests.admin` | eixo A `manage` |
| `purchase-requests.unit.filial-01` | eixo B `unit.filial-01` |
| `purchase-requests.unit.filial-02` | eixo B `unit.filial-02` |
| `estoque-seguranca.access` | eixo A `inventory.view` |
| `estoque-seguranca.view.filial-sc` | eixo B `unit.filial-01` |
| `estoque-seguranca.view.filial-es` | eixo B `unit.filial-02` |
| `idd-suprimentos.access` | eixo A `analytics.view` **após** dump Core |

Quem hoje tem só `dashboard-supplies.view` **sem** unit legado: no cutover o papel precisa **ganhar** `supplies.unit.filial-*` explícito (senão fail-closed). Registrar na E3 / cutover de papéis — não “inventar consolidado universal”.

Resolução no BFF: `has(canônico) OR has(alias)` **dentro do mesmo eixo**.

---

## Proibido

- `supplies.inventory.view.filial-01` e qualquer `{feature}.{ação}.filial-*` novo
- Recriar `filial-sc` / `filial-es` como canônico
- `if role == comprador` ou `if unidade == SC` no MFE
- Copiar code PT do PO (`controle-estoque-sc.access`) para contrato novo
- Tratar `manage` como “vê todas as filiais”

---

## Codes do PO (não canônicos)

`importados.access`, `onde-e-usado.access`, `matriz_atraso-fornecedores.access`, `alcada-compras.access`, `controle-estoque-sc.access`, `idd-suprimentos.access`: **CONFIRMADO_POR_EVIDENCIA_DO_PRODUCT_OWNER**. Após dump: mapear para eixo A (e o site da pessoa continua no eixo B). O sufixo `-sc` do BI **não** vira permission nova — unidade já está no eixo B.
