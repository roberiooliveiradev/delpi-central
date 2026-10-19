# 18 — Readiness e Handoff para Implementação

> **Estado vigente — 19/10/2026:** **A01–A16 PASS documental** com inventários físicos **por slice**. Quatro freezes de desenho, contrato semântico, modelo de segurança e estratégia de teste estão documentados e fechados **para planejamento da V1**. Isso não é autorização de runtime. A revisão probatória está em [44](./44-a16-revalidacao-final-transversal-2026-10-16.md); índice atual no [README](./README.md).
>
> `DOCUMENTATION_CLOSURE_COMPLETE=PASS` · `IMPLEMENTATION_AUTHORIZED=NO` (até comando explícito no novo chat) · `PORTAL_RUNTIME=NOT_IMPLEMENTED` · `RUNTIME_TESTS=TEST_NOT_RUN`.

## 1. O que está pronto e o que ainda não foi executado

| Área | Status | Evidência |
|---|---|---|
| A01 Página do usuário | **READY_FOR_IMPLEMENTATION_BRIEF** | [31 — contrato](./31-pagina-do-usuario.md), RQ-USER-01..09 no [23](./23-ledger-rq-ac-testes.md), reuso no [30](./30-plugin-ui-reuse-map.md) |
| A02–A07 comuns | **PASS documental** | docs 24–29 e 32, requisitos 23, Help no mesmo gate |
| A08–A13 P1–P6 | **PASS documental** | docs 08–13, 37; contratos de ownership e eventual stop local |
| A14 | **PASS transversal de desenho** | [34](./34-revisao-transversal-gate-v2.md) |
| A15 | **PASS de contratos semânticos/matriz PLANNED** | [35](./35-contratos-regras-scripts-test-matrix-gate-v2.md), [41](./41-estrategia-validacao-e-gates-implementacao-v1.md) |
| A16 | **PASS fechamento documental da V1** | [33](./33-plano-mestre-fechamento-documental.md) e [44](./44-a16-revalidacao-final-transversal-2026-10-16.md) |
| Runtime/CI/smoke do Portal | **NOT_IMPLEMENTED / TEST_NOT_RUN** | não inferir de testes do Core, exports do plugin-ui ou merge de docs |

A documentação diz **o quê** deve ser feito e como testar. OpenAPI físico, migration, deploy, wiring e testes reais são entregas do **slice proprietário** e exigem inventário antes da primeira alteração desse slice. A regra documental [33](./33-plano-mestre-fechamento-documental.md) diferencia vínculo técnico `TO_INVENTORY` de nova escolha material de produto: **não travar A01 por bindings da P3 ou P5 que ela não consome**.

## 2. Condições para a próxima interação

1. **Comando explícito do PO no novo chat:** autorizar começar **somente IMP-01/A01 Página do usuário**, não P1–P6 em lote nem deploy. Se não houver esse comando, executar apenas inventário.
2. **Executor Cursor:** provar `git rev-parse HEAD`, `git status --short --branch`, branch, arquivos preexistentes e regras `.cursor` aplicáveis. GitHub connector não prova working tree limpa.
3. **Inventário vinculado à A01:** comparar padrões atuais de APIs/Portais/MFEs antes de scaffold; ler contratos/Core S2S de effective access, directory, person profile/photo e `plugin-ui` exportado; verificar manifesto schemaVersion `1.0.0`, roteamento/gateway e BFF conforme padrões reais da plataforma. Respeitar [31](./31-pagina-do-usuario.md), [30](./30-plugin-ui-reuse-map.md), [21](./21-boundaries-produtos-e-owners.md) e [14](./14-seguranca-rbac-auditoria-e-ia.md).
4. **Gate por slice:** `READY_TO_EXECUTE` somente se owner, authz, contract produtor/consumidor, RQ/AC e testes positivos/sibling/negativos da A01 estiverem comprovados. Lacuna material exige `DECISION_REQUIRED`; premissa invalidada `EXECUTION_DRIFT`. Sem extrapolar de docs para código.
5. **Entrega mínima:** implementar **uma página/deep route** e BFF estritamente necessários, leitura server-side fail-closed, nenhum write de identidade, reuso `createDashboardPortalUserProfilePage`, Help atualizada na mesma PR, 403/404/503, F5, responsividade, teclado/foco, claro/escuro, testes e prova de resultado.
6. **Review:** Execution Report do [42](./42-playbook-brief-cursor-execution-report-v1.md), diff, CI e smoke reais no SHA. Só avançar para IMP-02 depois de `ACCEPT` ou `ACCEPT_WITH_RESIDUAL` não bloqueante.

**Permission codes congelados:** `controllership-finance.access` / `controllership-finance.manage` apenas. Core controla usuários, grupos, RBAC e permissões. JWT não é permission authority. BFF autoriza capability **AND** resource scope/ownership **AND** business rule. MFE consome apenas BFF; não chamar `api-delpi` diretamente do browser.

## 3. Dependências pendentes são locais, não novos gates globais

| Assunto | Status | Slice em que é stop |
|---|---|---|
| Identidade/permissões A01 e perfis Core | **PROVEN em source para APIs S2S existentes; wiring novo TO_INVENTORY** | IMP-01, validar contrato antes de código |
| T03 ERP/cutoff `STOCK_CLOSED` | **TO_INVENTORY**, owner canônico `api-delpi` | IMP-10 / P3 |
| T05 grupo/função corporativa para área P5 | **TO_INVENTORY**, owner Core API | IMP-12 / P5; **não** A01 |
| Coordenação formal P5 e P6 required-area snapshot / OCC | **TARGET semântico; físico TO_INVENTORY** | IMP-12/13 |
| D-FINAL-02 ausência de revisores | **CLOSED / PO_APPROVED** | P5 deve aguardar aceite humano real, sem trava artificial de submissão |
| Ajuda | **Contrato transversal definido; runtime ainda ausente** | mesma PR de cada slice user-facing |

A ausência de pessoas não configura aprovação automática nem motivo para barrar previamente submissão/publicação. Um aceite humano real válido por pacote e versão é indispensável à conclusão C2, além do quórum das áreas obrigatórias existentes; todos os pacotes aplicáveis submetidos, nenhuma clarification aberta e nenhum terminal rejeitado.

## 4. Ordem executiva e DoD

```text
IMP-01 Página do usuário → IMP-02 Início → IMP-03 Visão geral
→ IMP-04 Minhas tarefas → IMP-05 Sala de interação
→ IMP-06 Administração → IMP-07 Ajuda (sincronizada em cada PR)
→ IMP-08 P1 → IMP-09 P2 → IMP-10 P3 → IMP-11 P4
→ IMP-12 P5 → IMP-13 P6 → integração/regressão/release governado
```

Consultar [39 — roadmap](./39-roadmap-mestre-implementacao-v1.md), [40 — dependencies](./40-matriz-dependencias-e-slices-v1.md), [41 — validação](./41-estrategia-validacao-e-gates-implementacao-v1.md) e [43 — operações](./43-rollout-operacao-e-handoff-v1.md). Dependência P6 estritamente demonstrada pode exigir micro-slice predecessor **no owner**, nunca avanço por preferência.

**Definition of Done do IMP-01:** RQ-USER-01..09 satisfeitos, contrato de Core real, nenhum dado RBAC de outro usuário, efetivas permission/scope no backend, UI padrão, Help, positive/sibling/negative, CI/contract test/smoke material com evidência. `HTTP 200 != outcome`, docs `!=` runtime, `TEST_NOT_RUN != PASS`.

**Próxima conversa:** copie o brief do [42](./42-playbook-brief-cursor-execution-report-v1.md); solicite `Iniciar IMP-01 — Página do usuário`. **Não criar outro plano documental** antes de inspecionar o checkout atual.
