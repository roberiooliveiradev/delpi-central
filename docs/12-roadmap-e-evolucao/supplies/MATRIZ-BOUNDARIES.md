# MATRIZ-BOUNDARIES — Portal Suprimentos

Princípio: **dado compartilhado ≠ ownership**. Consumo por HTTP/deep link; sem import de domain/application de outro pacote.

| Capacidade | Owner | Fonte | Portal consome como | Não deve fazer |
|---|---|---|---|---|
| Identidade SSO | Keycloak | JWT | validação AuthN | confiar em permission claims como AuthZ final |
| Effective permissions, users, apps, routes, favoritos | **Core API** | Postgres Core + Keycloak context | `/me`, `/me/apps`, `/me/routes` | colocar regra de Suprimentos na Core |
| Catálogo de permissions do app | Core + manifest `supplies` | RBAC | MFE para UX + supplies-api para segurança | autorizar só no frontend |
| Units do Portal | Core effective permissions + catálogo `supplies.unit.*` | RBAC | supplies-api deriva `allowedUnits` | ler units de claims JWT como fonte final |
| SQL Protheus SC1/SC7/SA2/SA5/SB1/SB2/SBZ/SD1/SD3/SD4 | **api-delpi** | TOTVS | gateway HTTP | espelhar TOTVS no PG do Portal |
| CPV/OTD/ESTSEG/giro e interpretações ERP | **api-delpi** | SQL + domínio TOTVS | BFF | reimplementar fórmula no MFE/BFF |
| Escopo CC/mapping/notificações SC até C2 | **purchase-requests-api** | schema `purchase_requests` | HTTP C1 | duplicar fail-closed na api-delpi |
| Escopo CC/mapping/notificações SC após C2 | **supplies-api** | mesmo schema, novo process owner | interno | executar C3 antes de reconciliação |
| Tasks/follow-ups/notas/settings/auditoria funcional | **supplies-api** | Postgres `supplies` | CRUD próprio com ADR-007 | criar permission por verbo CRUD automaticamente |
| AuthZ do Portal | **supplies-api + Core** | effective permissions + units + ownership | capability + scope | confiar no browser/JWT claims |
| Meta/realizado estratégico | **strategic-indicators-api** | SI | enrich autorizado | segunda fonte de meta no Portal |
| Inspeções de entrada | **Qualidade** | contexto Qualidade | projeção read-only autorizada | tomar workflow de Qualidade |
| Frete/rateio | **Financeiro** | financial-api/TOTVS | deep link/projeção | recalcular rateio |
| PCP/programação | **Produção/PCP** | contexto PCP | somente integrações necessárias | mover regra de PCP |
| Materiais terceiros SB6 | **materiais-terceiros** | SB6 | fora do escopo/deep link | tratar como estoque de compra |
| Chat/tools | **minha-delpi-ai-api** | OpenAPI | mesmos contratos | duplicar tool routing |
| Sheets IDD | operação atual + api-delpi composer | Google Sheets | leitura integrada | copiar planilha para PG |
| Power BI/iframe externos | Core/external owner | externo | manter/deep-link até paridade | iframe arbitrário dentro do MFE |

```text
plugins/supplies
  └─HTTP→ supplies-api (Flask)
            ├─HTTP→ Core /me
            ├─HTTP→ api-delpi → TOTVS
            ├─HTTP→ purchase-requests-api (somente C1)
            ├─HTTP→ strategic-indicators-api
            └─HTTP→ contextos irmãos autorizados
```

## Gates

- MFE: grep zero de acesso direto à api-delpi.
- AuthZ: effective permissions Core-first.
- RBAC: menor catálogo suficiente (ADR-007).
- C2 antes de C3.
- nenhuma regra TOTVS nova só no BFF.
- nenhuma regra de CC na api-delpi.
