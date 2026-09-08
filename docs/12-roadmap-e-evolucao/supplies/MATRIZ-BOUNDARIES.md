# MATRIZ-BOUNDARIES — Portal Suprimentos

Princípio: **dado compartilhado ≠ ownership**. Consumo HTTP ou deep link. Sem import de `domain`/`application` de outro pacote.

| Capacidade | Owner | Fonte | Portal consome como | Não deve fazer |
|------------|-------|-------|---------------------|----------------|
| Usuário, papéis, apps, favoritos, JWT identity | **Core API** | Postgres Core + Keycloak | `GET /core-api/me` / apps / routes | Colocar regra de SC/estoque na Core |
| Permissões de produto + aliases | Core (cadastro) + manifest `supplies` | RBAC | Checagem no MFE (navegação) **e** na supplies-api | Autorizar só no frontend |
| SQL Protheus SC1 SC7 SA2 SA5 SB1 SB2 SBZ SD1 SD3 SD4 | **api-delpi** | TOTVS | Gateway HTTP | Espelhar tabelas no PG do Portal |
| Interpretação canônica CPV OTD ESTSEG giro | **api-delpi** | SQL + domain totvs | BFF | Reimplementar fórmula no MFE ou na supplies-api |
| Envelope `/supplies/*` `/products/*` | **api-delpi** | OpenAPI | Reuso; rota nova só com gap | Copiar OpenAPI para assistant JSON |
| Escopo CC, mapping Protheus, notif SC (hoje) | **purchase-requests-api** | schema `purchase_requests` | HTTP C1; depois C2 migra owner para supplies-api | Duplicar fail-closed na api-delpi |
| Workflows, tarefas, follow-ups, notas, alertas, settings | **supplies-api** | Postgres `supplies` | CRUD próprio | Gravar isso na api-delpi |
| Composição BFF / membership filial do Portal | **supplies-api** | JWT + unit perms | — | Mandar «filial pronta» do browser para api-delpi |
| Meta vs realizado CPV/OTD/giro/estoque/savings | **strategic-indicators-api** | snapshots + gateway supplies | HTTP enrich Overview | Segunda tabela de metas no Portal |
| Telas TV estoque | **tv-dashboard-api** | native screens | INTEGRAR feed se preciso; deep link | Hostear TV no MFE supplies |
| Inspeção entrada, rejeição, pendência qualidade | **Qualidade** (`inspecoes-entrada` + api-delpi QE*) | views inspeção | Projeção read-only no Fornecedor 360 | Tomar o processo de inspeção |
| Frete das compras / rateio NF | **Financeiro** (`financial-api`) | SF8/SF1 | DEEP_LINK + opcional card «ver no Financeiro» | Recalcular rateio |
| Open-coverage para PCP, programação, OP | **Produção/PCP** | api-delpi + production-control | Portal lê cobertura de **compra** (SC7/SD4/SC1) já no ESTSEG; não lê programa PCP | Mover regra de PCP |
| Beneficiamento SB6 (material de **cliente**) | **materiais-terceiros** | SB6 | FORA_DO_ESCOPO / deep link | Tratar como estoque de MP |
| Chat / RAG / tools | **minha-delpi-ai-api** | OpenAPI importado | Mesmos operationIds; sem markers manuais | Duplicar tool routing por endpoint |
| Planilha IDD (lançamento economia) | Operações + **api-delpi** composer | Google Sheets | INTEGRAR leitura já existente | Copiar aba para Postgres |
| Power BI / iframe Core | Core (URL app) | externo | MANTER_EXTERNO até paridade | Iframe dentro do MFE sem ADR |

```text
plugins/supplies  ──HTTP──► supplies-api ──HTTP──► api-delpi ──► TOTVS
                              │
                              ├──HTTP──► purchase-requests-api   (até C3)
                              ├──HTTP──► strategic-indicators-api
                              ├──HTTP──► Core
                              └──HTTP──► inspecoes / financial   (projeção, opcional)
```

Gate de PR futuro:

- [ ] Grep zero no MFE: `apiDelpiUrl|API_DELPI_BASE|/apps/api-delpi`
- [ ] Nenhuma regra TOTVS nova só no BFF
- [ ] Nenhuma membership de CC na api-delpi
