# HOMOLOGACAO-PARIDADE — Portal vs legado

Depreciação somente com checklist assinada (owner Suprimentos + QA) e evidência mensurável.

Não marcar paridade por aparência. Comparar funcionalidade, filtros, dados, permissions, URLs, performance e Ajuda.

---

## 1. Método de comparação

Para KPI:

| Campo | Obrigatório |
|---|---|
| filial/units | sim |
| período/competência | sim |
| filtros | sim |
| valor legado | sim |
| valor Portal | sim |
| delta | sim |
| tolerância | definida antes do teste |
| evidência | link/arquivo/screenshot/JSON |

Para listas/tabelas:

- mesma quantidade total quando contratos forem equivalentes;
- mesmo conjunto de chaves de negócio;
- mesmos filtros/ordenação quando fizer parte do contrato;
- paginação equivalente;
- casos positivo, negativo e filial irmã.

Para performance:

- p50/p95 ou outra métrica acordada;
- timeout/error rate;
- quantidade de downstream calls para composições críticas.

---

## 2. `dashboard-supplies`

| Item | Critério Portal | Status |
|---|---|---|
| Home/Overview | WF-01 + WF-02 sem misturar Hub e BI | pendente |
| CPV | mesmo recorte/fórmula + contexto temporal | pendente |
| OTD + ranking | mesmo universo/regra ou diferença explicitamente homologada | pendente |
| estoque | mesmo recorte por branch/location | pendente |
| giro | mesmo indicador oficial em vezes | pendente |
| savings | mesma origem/recorte | pendente |
| filtros | branch/datas/location/competência equivalentes | pendente |
| export | equivalente se realmente utilizado | pendente |
| metas SI | mesma fonte canônica e escopo autorizado | pendente |
| permission legado | migração para capability canônica + RBAC Core validado | pendente |
| URL legada | redirect decidido/testado somente após GO | pendente |
| Ajuda | conceitos cobertos | pendente |
| performance | baseline legado × Portal | pendente |

---

## 3. `purchase-requests`

| Item | Critério | Status |
|---|---|---|
| lista grão item | mesmo contrato 0.2 | pendente |
| filtros | branch, datas, SC, solicitante, CC, produto, fornecedor, pedido, estágio | pendente |
| fail-closed CC | equivalente | pendente |
| view-all | bypass CC, não unidade | pendente |
| units 01/02 | equivalente após migração | pendente |
| admin mapping/scopes | paridade | pendente |
| export | comportamento + permission | pendente |
| notificações | jobs migrados e reconciliados na C2 | pendente |
| deep links | filtros preservados | pendente |
| C2 | ownership/jobs supplies-api concluídos | pendente |
| reconciliação | contagens/eventos equivalentes antes de C3 | pendente |
| 403 filial | testes positivos/negativos/irmão | pendente |

**C3/cutover é proibido antes de C2 + reconciliação + paridade final.**

---

## 4. `estoque-seguranca`

| Item | Critério | Status |
|---|---|---|
| saldo × ESTSEG | equivalência de dados | pendente |
| filtros | filial/grupo/situação/busca | pendente |
| detalhe | SC7/SD4 + SC1 conforme contrato | pendente |
| fornecedores/preços | equivalência | pendente |
| análise de consumo | mesma memória de cálculo | pendente |
| read-only | preservado | pendente |
| export | equivalente se requisito vigente | pendente |
| unit aliases | migração para eixo B | pendente |
| performance | baseline × Portal | pendente |

---

## 5. BIs/apps externos do Product Owner

Antes do `GATE-CUTOVER`, **nenhum** pode permanecer em `LEGADO_A_VALIDAR`.

Estados finais permitidos:

```text
PARIDADE_HOMOLOGADA
MANTER_EXTERNO
DEEP_LINK
FORA_DO_ESCOPO_COM_ACEITE
```

Tabela após E1.S1 (dump Core **local** 2026-09-08; produção ainda pendente):

| App/BI | id/path real | Regra/fonte confirmada? | Destino | Evidência | Owner aceite | Status |
|---|---|---:|---|---|---|---|
| Análise - Importações | não encontrado (Core local) | não | — | ADR-005 E1.S1 SQL 0 rows | pendente dump prod | LEGADO_A_VALIDAR |
| Onde o item é usado - BI | não encontrado (Core local) | não | — | ADR-005 E1.S1; API nativa `get_product_parents` não prova paridade | pendente dump prod | LEGADO_A_VALIDAR |
| Atraso de Fornecedores - SC - BI | não encontrado (Core local) | não | — | ADR-005 E1.S1; OTD nativo ainda não comparado | pendente dump prod | LEGADO_A_VALIDAR |
| Alçada de Compras - BI | não encontrado (Core local) | não | — | ADR-005 E1.S1; workflow vs consulta aberto (P-06) | pendente dump prod | LEGADO_A_VALIDAR |
| Controle de Estoques - SC - BI | não encontrado (Core local) | não | — | ADR-005 E1.S1 | pendente dump prod | LEGADO_A_VALIDAR |
| Indicadores de Suprimentos - Sheets | não encontrado (Core local) | não | — | ADR-005 E1.S1; savings API ≠ prova de remoção do app | pendente dump prod | LEGADO_A_VALIDAR |

---

## 6. Authz/RBAC de paridade

Além de dados, homologar:

- permissions efetivas vêm do Core;
- `/me/apps` retorna o Portal para papéis provisionados;
- `/me/routes` respeita capabilities;
- usuário sem `supplies.portal.access` não abre o Portal;
- unit scope respeitado no backend;
- aliases legados não viram única fonte de acesso ao novo app;
- tasks/notas respeitam resource scope/ownership sem permissions CRUD redundantes.

---

## 7. Assinatura

| Ativo | Data | Owner Suprimentos | QA | Evidência | Notas |
|---|---|---|---|---|---|
| dashboard-supplies | | | | | |
| purchase-requests | | | | | |
| estoque-seguranca | | | | | |
| BIs externos | | | | | |
