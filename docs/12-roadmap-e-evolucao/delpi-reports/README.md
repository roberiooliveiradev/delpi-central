# Delpi Reports — índice

App plugin para **cadastrar, agendar e enviar relatórios por e-mail** aos colaboradores, consumindo dados de outros módulos via **providers** na `api-delpi`.

**Status (2026-07-21):** Fases 0–**4** concluídas (fundação + MFE/API + provider + e-mail + robustez). Fase 5 (multi-provider) pendente. Ops: [OPS.md](./OPS.md).

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ROADMAP.md](./ROADMAP.md) | **Plano de implementação por fases** (0–5), checklists e critérios de pronto |
| [OPS.md](./OPS.md) | Runbook Graph, cron, claim, troubleshooting |
| [ADR-001-fundacao.md](./ADR-001-fundacao.md) | ADR Fase 0 — decisões de fundação |
| [SCHEMA.md](./SCHEMA.md) | Modelo Postgres `reports` |

---

## Decisões travadas

| Tema | Escolha |
|------|---------|
| Nome exibido | **Delpi Reports** |
| Plugin `id` | `reports` |
| Container Docker | `delpi-reports` |
| `basePath` / entry | `/apps/reports` → `/apps/reports/assets/remoteEntry.js` |
| Backend | Módulo na **api-delpi** (Postgres + rotas + registry de providers) |
| Entrega | **E-mail** via Microsoft Graph |
| Remetente | `minhadelpi@delpi.com.br` (`GRAPH_REPORTS_MAIL_SENDER`, fallback `GRAPH_MAIL_SENDER`) |
| Destinatários | Diretório Core (`UserDirectoryPicker` + e-mails resolvidos) |
| 1º relatório | **Rupturas nos próximos 30 dias** (extrato projetado do estoque de segurança) |

---

## Visão de produto

Colaboradores de suprimentos (e, depois, outros times) recebem periodicamente um relatório objetivo — por exemplo, lista de materiais com ruptura projetada nos próximos 30 dias — sem precisar abrir o dashboard de Estoque de Segurança.

O app deve ser **robusto e escalável**:

1. Cadastro de **definições** de relatório (tipo + parâmetros).
2. Seleção de **destinatários** (usuários do portal).
3. **Agendamento** (cron) e disparo manual.
4. **Providers** desacoplados que coletam dados de outros domínios da api-delpi.
5. Histórico de **runs** e entregas (sucesso/falha).

---

## Arquitetura-alvo

```text
Portal → MFE reports
           ├─ Core API directory (UserDirectoryPicker)
           └─ api-delpi /reports/*
                 ├─ Postgres (definitions, schedules, runs, deliveries)
                 ├─ ReportProvider registry
                 │    └─ SafetyStockShortage30dProvider
                 │         └─ build_stock_projection (+ agregação)
                 └─ Microsoft Graph sendMail
                      └─ minhadelpi@delpi.com.br → destinatários
```

### Princípios

| Princípio | Implicação |
|-----------|------------|
| Fonte de verdade = API | Não acoplar ao MFE `estoque-seguranca` via Module Federation |
| Provider por tipo | Motor genérico; cada relatório implementa `collect` + `render_email` |
| Sem N+1 de details | Agregação backend; não chamar `GET …/items/{code}/details` por item |
| UI kit | `@delpi/plugin-ui` via MF; zero CSS de componentes no MFE |
| Artefatos | PDF/XLSX (se houver) em volume persistente (`persistent-upload-storage`) |

---

## Glossário

| Termo | Significado |
|-------|-------------|
| **Definição** | Configuração persistida: `provider_key`, parâmetros, destinatários, ativo/inativo |
| **Provider** | Implementação de domínio que coleta dados e monta corpo/anexo do e-mail |
| **Agendamento** | Regra de recorrência (ex.: diário 07:00) ligada a uma definição |
| **Run** | Execução pontual (manual ou agendada): collect → render → send |
| **Entrega** | Tentativa de envio Graph a um destinatário (ou lote), com status |

---

## Identificação do plugin (alvo)

| Campo | Valor |
|-------|--------|
| `id` | `reports` |
| Nome | Delpi Reports |
| `basePath` | `/apps/reports` |
| Container | `delpi-reports` |
| Caller header | `X-Delpi-Caller-App: reports` |
| Permissões (MVP) | `reports.view`, `reports.manage`, `reports.*.filial-sc/es` |

---

## Primeiro relatório — rupturas 30 dias

Base canônica: **extrato projetado** do estoque de segurança (mesma lógica do modal “Extrato projetado de saldo”).

| Conceito | Regra |
|----------|--------|
| Saldo inicial | SB2 armazéns **01 + 98 + 99** |
| Entradas | Pedidos SC7 elegíveis (data prevista) |
| Saídas | Empenhos SD4 elegíveis (data do empenho) |
| Ruptura | Primeiro evento com `running_balance < 0` → `first_shortage_date` |
| Janela | `as_of_date` … `as_of_date + 30 dias` |
| Não é | Déficit vs ESTSEG (`deficit_quantity`) — outro conceito |

Código de referência:

- `api-delpi/app/domain/services/supplies/safety_stock_stock_projection_service.py` — `build_stock_projection`
- `api-delpi` — `GET /supplies/safety-stock/items/{code}/details` (`get_supplies_safety_stock_item_details`)
- Plugin UI de referência: `plugins/estoque-seguranca/` (seção Extrato projetado)

`provider_key` sugerido: `safety_stock_shortage_30d`

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Scaffold MFE | [novo-plugin-mfe-checklist.md](../../05-plugin-system/novo-plugin-mfe-checklist.md) |
| Registrar plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |
| Inventário plugins | [08-plugins/README.md](../../08-plugins/README.md) |
| Graph mail (hoje) | `api-delpi/app/infrastructure/providers/microsoft_graph/microsoft_graph_mail_client.py` |
| Estoque segurança (API) | `api-delpi/docs/api/estoque-seguranca.md` |
| Roadmap estoque | [estoque-seguranca/README.md](../estoque-seguranca/README.md) |
| Diretório / picker | `plugins/plugin-ui/src/components/directory/UserDirectoryPicker.tsx` |
| Notificações (canal futuro) | [notificacoes.md](../../04-core-api/notificacoes.md) |

---

## Ordem de trabalho

1. **Fase 0** — contratos, schema, RBAC, extensão Graph  
2. **Fase 1** — scaffold MFE + CRUD skeleton api-delpi  
3. **Fase 2** — provider rupturas 30 dias — **concluída**  
4. **Fase 3** — UI + agendamento + e-mail end-to-end — **concluída**  
5. **Fases 4–5** — robustez, escala e novos providers  

Detalhe e checklists: [ROADMAP.md](./ROADMAP.md).

---

## Fora de escopo do MVP

- Canal portal/sino como entrega principal (e-mail primeiro)
- API dedicada `delpi-reports-api`
- Acoplamento MFE↔MFE com `estoque-seguranca`
- Apresentação schema-driven / chat do relatório
- Consumo N+1 de details por produto
