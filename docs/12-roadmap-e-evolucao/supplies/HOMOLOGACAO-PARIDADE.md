# HOMOLOGACAO-PARIDADE — Portal vs legado

> Revisado em 2026-09-10. Paridade é evidência de dados, comportamento, segurança e experiência; não aparência.

Depreciação somente com checklist assinada (owner Suprimentos + QA) e evidência mensurável.

## 1. Método

Para KPIs: filial/units, período/competência, filtros, valor legado, valor Portal, delta, tolerância definida antes do teste e evidência.

Para listas/tabelas: total quando comparável, chaves de negócio, filtros/ordenação, paginação, positive + sibling + negative e filial irmã.

Para performance: baseline e candidato com p50/p95 ou métrica acordada, timeout/error rate e downstream calls quando composição for crítica.

Para UI/UX: Help, loading/empty/partial/error/403/404, URL/F5, tema, responsividade e acessibilidade quando material.

---

## 2. `dashboard-supplies`

| Item | Critério Portal | Status |
|---|---|---|
| Home/Overview | WF-01 + WF-02 preservam separação Hub × BI | implementação fechada; paridade legado pendente |
| CPV | mesmo recorte/fórmula + contexto temporal | pendente |
| OTD | mesmo universo/regra ou diferença homologada | pendente |
| estoque | mesmo recorte aplicável | pendente |
| giro | mesmo indicador oficial | pendente |
| savings | mesma origem/recorte | pendente |
| metas SI | mesma fonte canônica; tríade e escopo preservados | pendente |
| permissions | migração para capabilities canônicas + Core | pendente final |
| URL legada | redirect somente após GO | pendente |
| Ajuda | conceitos equivalentes/cobertos | parcial — Portal implementado |
| performance | baseline legado × Portal | pendente |

Filtros de domínio como `location`/`stock_method` só entram na comparação da superfície que realmente os suporta; não são globais da Overview por conveniência.

---

## 3. `purchase-requests`

C1 funcional existe no Portal, mas o WF-04 ainda está em revalidação de GATE-FEATURE e C2 continua futuro.

| Item | Critério | Status |
|---|---|---|
| lista/detalhe/export C1 | fluxo BFF-only presente | implementado; revalidar DoD |
| grão item | contrato equivalente | pendente de homologação quantitativa |
| filtros | equivalência conforme contrato vigente | pendente |
| fail-closed CC | equivalente | implementado/testes; homologação final pendente |
| view-all | amplia CC, não unidade | implementado/testes; homologação final pendente |
| units | somente `allowedUnits` | implementado/testes; HML/prod pendente |
| admin mapping/scopes | paridade | pendente |
| notificações/jobs | migrados para supplies-api | **não** — C2 futuro |
| deep links/URL | filtros preservados | revalidar WF-04 |
| C2 | ownership/jobs supplies-api | pendente |
| reconciliação | counts/cursors/events | pendente |
| 403 filial | positive/negative/sibling | revalidar |

**C3 é proibido antes de C2 + reconciliação + paridade final.**

---

## 4. `estoque-seguranca`

| Item | Critério | Status |
|---|---|---|
| saldo × ESTSEG | equivalência | pendente |
| filtros | filial/grupo/situação/busca conforme contrato | pendente |
| detalhe | fontes conforme contrato canônico | pendente |
| fornecedores/preços | equivalência | pendente |
| análise de consumo | mesma memória de cálculo | pendente |
| read-only | preservado | pendente |
| export | somente se requisito vigente | pendente |
| unit aliases | eixo `supplies.unit.*` | pendente |
| performance | baseline × Portal | pendente |

---

## 5. BIs/apps externos do Product Owner

Antes do GATE-CUTOVER, nenhum pode permanecer `LEGADO_A_VALIDAR`.

Estados finais permitidos:

`PARIDADE_HOMOLOGADA` · `MANTER_EXTERNO` · `DEEP_LINK` · `FORA_DO_ESCOPO_COM_ACEITE`.

O dump Core local 2026-09-08 encontrou 0/6; o dump produção continua obrigatório para fechar P-01/P-03/P-04/P-07 e decisões de redirect/depreciação.

---

## 6. AuthZ/RBAC de paridade

Homologar:

- effective permissions vêm do Core;
- `/me/apps` retorna o Portal e suas rotas autorizadas em `apps[].routes`;
- **não usar `/me/routes` como critério**, pois não é contrato canônico atual;
- usuário sem `supplies.portal.access` não abre o Portal;
- unit scope é validado no backend;
- aliases legados não viram fonte única de autorização;
- tasks/notas respeitam resource scope/ownership sem CRUD permissions redundantes.

---

## 7. Gates e assinatura

Paridade só fecha quando dados + filtros + segurança + UX + performance aplicável estiverem evidenciados. Falha de ambiente deve ser marcada `INCONCLUSIVE`, não PASS.

| Ativo | Data | Owner Suprimentos | QA | Evidência | Notas |
|---|---|---|---|---|---|
| dashboard-supplies | | | | | |
| purchase-requests | | | | | |
| estoque-seguranca | | | | | |
| BIs externos | | | | | |
