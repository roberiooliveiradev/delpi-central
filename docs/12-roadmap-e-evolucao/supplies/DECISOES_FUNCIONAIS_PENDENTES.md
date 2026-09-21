> **Histórico / SUPERSEDED pelo [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md):** o Portal vigente usa só `supplies.access` e `supplies.manage`. Unidade é filtro de dados `01`/`02`. O texto abaixo não é o contrato ativo.

# DECISOES_FUNCIONAIS_PENDENTES — Portal Suprimentos

> Revisado em 2026-09-16. Revalidado em 2026-09-21 (`aa13f1075`): não há neste repositório autorização do Product Owner para WF-07 nem evidência de smoke federado que feche GATE-FEATURE WF-06. P-03 continua bloqueio de paridade/depreciação, não a única trava da página nativa. Este arquivo contém apenas decisões que o repositório ainda não responde. Hipótese não vira receita executável.

| ID | Pergunta | Impacto | Estado atual | Próxima decisão |
|---|---|---|---|---|
| P-01 | URLs, ids e tipo dos 6 apps/BIs do PO | menu, paridade, redirects | **BLOQUEADO_COM_EVIDENCIA** — Core local 0/6; falta dump prod | coletar Core prod antes de cutover |
| P-02 | Comprador ES existe no Core? | papel + unit-02 | **FECHADO_PARA_DESENHO** — sem permission nova; validação operacional fica para HML/prod | smoke com usuário real quando disponível |
| P-03 | Regra do BI Atraso SC = OTD/PO-OTD nativo? | paridade WF-07/11 | **BLOQUEADO_COM_EVIDENCIA** até dump/comparação prod | comparar antes de depreciação do BI; não bloquear automaticamente construção da página nativa se contrato estiver comprovado |
| P-04 | Regra do BI Controle Estoques SC | paridade WF-15 | **BLOQUEADO_COM_EVIDENCIA** | dump prod + comparação na etapa de Estoque |
| P-05 | Existe processo de importação/TOTVS já mapeado? | WF-08 | **BLOQUEADO_COM_EVIDENCIA** | manter Importações fora da linha executável até contrato/jornada comprovados |
| P-06 | Alçada é consulta ou workflow de aprovação? | permission/SoD futura | **BLOQUEADO_COM_EVIDENCIA** | não criar `approvals.manage` até workflow/segregação reais serem comprovados |
| P-07 | Quem edita IDD/Sheets e o app deve permanecer? | manter externo vs integrar | **BLOQUEADO_COM_EVIDENCIA** | dump prod + owner/fluxo de edição |
| P-08 | Cobertura = meses de giro ou cobertura ESTSEG? | KPI | **FECHADO** — fora do Overview P0 | reabrir somente como feature futura com ficha própria |
| P-09 | Threshold aging SC/PC | worklist/alertas | **ABERTO** | homologar antes de nomear buckets/regras |
| P-10 | Qual a janela operacional de transição C2? | migração SC | **PARCIALMENTE_FECHADO** — estratégia técnica single-writer já está definida; faltam volumes HML/prod, janela, responsáveis e rollback operacional | medir ambiente e fechar runbook antes de E25 |
| P-11 | Quais dados de Qualidade podem aparecer no Supplier 360? | boundary/RBAC cruzado | **ABERTO** | **Qualidade fora do P0 Supplier 360 enquanto não houver contrato + autorização claros** |
| P-12 | Owner formal de cada KPI | governança | **FECHADO** — área Suprimentos; aceite nominal pode permanecer assinatura de homologação | manter fichas atualizadas |
| P-13 | Identificador canônico de usuário persistido | data model | **FECHADO** — Core `/me.id` UUID | manter `keycloak_sub` apenas quando contrato exigir |
| P-14 | `/indicators` agrega jornada distinta da Overview/SI? | risco de página redundante | **ABERTO PARA A ETAPA FUTURA** | antes de promover WF-20, provar valor distinto; senão marcar fora do escopo |
| P-15 | Histórico de Preços é página própria ou seção do Product 360? | fila page-by-page | **ABERTO PARA A ETAPA FUTURA** | decidir com evidência antes de promover WF-19 |

## Decisões fechadas pelo PO/arquitetura

- Unidade = `supplies.unit.filial-{TOTVS}`.
- Permission catalog mínimo; sem espelho CRUD.
- Tasks/notas não recebem permissions read/write separadas na P0 sem risco/segregação comprovados.
- `supplies-api` = Flask.
- JWT não é fonte final de permissions; Core resolve effective permissions.
- C1 → C2 → paridade → C3.
- MFE fala somente com `supplies-api`.
- `/me/apps` (`apps[].routes`) é a superfície vigente para apps/rotas autorizadas; não criar dependência em `/me/routes`.
- Páginas generalistas seguem linguagem visual Comercial por `@delpi/plugin-ui`, sem copiar CSS/componentes.
- **Tabelas do Portal Comercial são referência de UX, não contrato automático para Suprimentos.** A paridade tabular será feita por capacidade comprovada, priorizando `@delpi/plugin-ui`; ordenação, colunas, preferências, densidade, paginação, responsividade, tema e teclado/foco são candidatas a padrão compartilhado, enquanto `Cards`, `Board`, alternâncias de unidade de domínio e outras funções específicas permanecem opt-in por jornada. Ver `TABLE-UX-PARITY.md`.
- A frente de paridade de tabela é transversal e **não altera a fila page-by-page nem autoriza página futura**; o inventário `Comercial × plugin-ui × Suprimentos` deve ocorrer quando uma superfície tabular for promovida.
- Help acompanha cada feature user-facing.
- Uma página user-facing por vez até GATE-FEATURE fechado.

## Gates

- P-01/P-03/P-04/P-07 não podem chegar ao cutover como `LEGADO_A_VALIDAR`.
- P-06 não cria capability/permission de aprovação sem workflow comprovado.
- P-10 bloqueia E25 C2 enquanto volumes/janela/runbook operacional não estiverem fechados.
- P-11 mantém o bloco Qualidade fora do Supplier 360 P0 enquanto aberto.
- P-14/P-15 não bloqueiam a fila anterior; são decisões obrigatórias somente quando suas páginas forem promovidas.
