# 02 — UX / página inicial — wireframe candidato

**Entrada:** Portal Engenharia → Ferramentas → **Produtos Novos** (não alterar TopBar principal congelada na documentação mestra).  
**Título:** Produtos Novos  
**Subtítulo:** Planejamento e Acompanhamento da Produção.

## Layout proposto
```text
┌ Portal Engenharia / Ferramentas / Produtos Novos ──────────────────────────┐
│ Produtos Novos        [Semana | Mês | Personalizado] [Unidade] [Busca]      │
│ Fonte Carga Máquina: [última atualização / indisponível]                   │
├────────────────────────────────────────────────────────────────────────────┤
│ [OPs previstas] [Solicitados] [Em acompanhamento] [Com pendências]         │
├────────────────────────────────────────────────────────────────────────────┤
│ Visão geral | Programação | Acompanhamentos | Pendências | Histórico       │
│ Próximas OPs de produtos novos                                             │
│ OP | Produto | Unidade | Data prevista | Etapas | Situação | Detalhes     │
│ ...                                                                        │
├────────────────────────────────────────────────────────────────────────────┤
│ Fila de trabalho / ocorrências relevantes     [Solicitar acompanhamento]  │
└────────────────────────────────────────────────────────────────────────────┘
```

## Navegação interna
1. **Visão geral** — consolida programação e trabalho pendente.
2. **Programação** — OPs futuras por semana/mês/intervalo, unidade, produto e estado.
3. **Acompanhamentos** — chamados, checklists e execução por operação.
4. **Pendências** — divergências, reprogramações e verificações incompletas.
5. **Histórico** — eventos, responsáveis, evidências e decisões rastreáveis.

## Componentes
- `PageHeader`, `PeriodFilter`, `UnitFilter`, `OrderSearch`, `SyncHealthStatus`.
- `UpcomingOrdersTable`, `StatusChip`, `WorkQueue`, `SummaryMetrics`.
- `RequestFollowUpDialog` (somente líder autorizado, OP obrigatória), `FollowUpDetail`, `OperationChecklist`, `IssueTimeline`, `CompletionApproval`.
- Adotar `@delpi/plugin-ui` e padrões do Portal existentes; nomes acima são **conceituais**, não componentes de código comprovados.

## Estados
- Previsão de produção **≠** início efetivo / checklist executado.
- Loading, empty, forbidden, unavailable, partial/stale sync, conflict/reprogrammed, retry, success com read-back.
- Números e OPs do protótipo anterior eram **fictícios**; não reaproveitá-los como dados DELPI.
- Ação manual só confirma sucesso após resposta e leitura do owner autorizado; desabilitar/explicar quando acesso faltar.
- Responsividade, claro/escuro, teclado/foco e URL deep link dependem de padrões do Portal.

## Critérios de UX
- A Engenharia filtra lista por semana, mês e período livre e vê fonte/data da última sincronização.
- Busca por produto e OP, unidade e situação respeita escopo do usuário.
- Uma OP reprogramada muda previsão sem virar 'iniciada'; ausência de integração é sinalizada.
- Líder registra solicitação de acompanhamento com vínculo canônico à OP; o sistema não cria duplicidade lógica.
- Toda divergência e pendência têm histórico navegável sob autorização.
