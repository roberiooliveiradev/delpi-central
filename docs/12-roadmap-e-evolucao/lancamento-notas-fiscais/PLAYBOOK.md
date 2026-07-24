# Playbook — Lançamento de Notas Fiscais (LNF)

> **Arquivo:** `docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/PLAYBOOK.md`  
> **Versão:** 1.0  
> **Data:** 2026-07-24  
> **Status:** MVP operacional entregue (MFE + api-delpi + conciliação sob demanda)  
> **Base:** especificação funcional/técnica + implementação em `plugins/lancamento-notas-fiscais` e `api-delpi`

**Relacionado:**

- [README.md](./README.md) — índice do módulo
- [especificacao-funcional-tecnica.md](./especificacao-funcional-tecnica.md) — contrato de domínio
- [ROADMAP.md](./ROADMAP.md) — etapas e status
- [Plugin README](../../../plugins/lancamento-notas-fiscais/README.md)
- [API](../../../api-delpi/docs/api/lancamento-notas-fiscais.md)
- Regras: `plugins-documentation.mdc`, `new-api-route-checklist.mdc`, `migrations-immutable-checksum.mdc`, `infra-sequential-container-startup.mdc`

---

## 1. North Star

Excelência no LNF **não** é «cadastrar a nota no portal». É garantir que **toda NF de entrada recebida fisicamente**:

1. Gere uma solicitação rastreável (quem, quando, filial, chave fiscal).
2. Entre numa fila **FIFO** justa (`received_at`).
3. Seja atendida com estados claros (pendente → em andamento → bloqueada → lançada).
4. Feche sozinha quando o Protheus (`SF1`) confirmar o lançamento.
5. Possa ser marcada **Já lançada** pelo atendente quando o match automático falhar — sem inventar status paralelo.
6. Preserve auditoria (histórico + comentários) para disputa operacional.

### Métricas de sucesso (orientadoras)

| Métrica | Meta sugerida | Como olhar |
|---------|---------------|------------|
| Tempo médio recebimento → `posted` | Tendência de queda | `reconciled_at` − `received_at` |
| % `posted` via auto vs manual | Auto dominante | `completion_source` |
| Fila aberta (`pending`+`in_progress`+`blocked`) | Estável / sem acúmulo | listagem filtrada |
| Refresh sem travar UI | 100% | timeout/cooldown MFE + API |

---

## 2. Pilares

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  SOLICITANTE    │────▶│  FILA / ATEND.   │────▶│  PROTHEUS SF1   │
│  (create)       │     │  (process/manage)│     │  (somente leitura)│
└─────────────────┘     └────────┬─────────┘     └────────▲────────┘
                                 │                        │
                                 │   Postgres plugins     │
                                 └────────────────────────┘
```

| Pilar | Responsabilidade |
|-------|------------------|
| **Operação** | Cadastro, fila, bloqueio, Já lançada |
| **Conciliação** | Match lote SF1 + refresh com cooldown |
| **Dados** | Schema `lancamento_notas_fiscais`, migrations imutáveis |
| **UX** | Header/brand, status, detalhe denso, valor PT-BR, doc 9 dígitos |
| **RBAC** | Matriz por permissão + `allowed_actions` na API |

---

## 3. Papéis (matriz operacional)

| Ação | Solicitante (`create`) | Atendente (`process`) | Admin (`manage`) |
|------|------------------------|------------------------|------------------|
| Abrir plugin | se tiver `access` | idem | idem |
| Criar solicitação | ✓ | —* | —* |
| Ver próprias | ✓ | ✓ (todas se view/process) | ✓ |
| Ver todas | precisa `view`/`process`/`manage` | ✓ | ✓ |
| Corrigir pending/blocked | próprias | ✓ | ✓ |
| Start / block / resume | — | ✓ | ✓ |
| Já lançada (`post-manual`) | — | ✓ | ✓ |
| Comentar | próprias (e fluxo create) | ✓ | ✓ |
| Cancelar | própria **pending** | — | não terminais |
| `reconciliation/run` | — | — | ✓ |
| `reconciliation/refresh` | se read | ✓ | ✓ |

\* Atendente/admin normalmente também têm `create` no Keycloak se cadastram; a API exige a permissão explícita na rota.

**Regra de ouro:** o MFE só exibe botões presentes em `allowed_actions`.

---

## 4. Fluxo ponta a ponta

```text
Recebimento físico
       │
       ▼
 POST /requests  →  pending
       │
       ├─▶ POST /start     → in_progress
       ├─▶ POST /block     → blocked ──▶ POST /resume → in_progress
       │
       ├─▶ reconciliation (refresh/run) casa SF1 → posted (auto)
       ├─▶ POST /post-manual → posted (manual)
       └─▶ POST /cancel (+ justificativa) → cancelled
```

### Já lançada

- Modal de **confirmação** (sem campo de justificativa obrigatório).
- API: `POST .../post-manual` com body opcional.
- Histórico: `manual_posted`, `completion_source=manual`.

### Conciliação na abertura da fila

1. MFE chama `POST /reconciliation/refresh` (timeout ~45s no cliente).
2. API respeita cooldown **45s** — se ativo, retorna sem reprocessar lote.
3. Em paralelo / em seguida, `GET /requests` lista a fila (UI não fica presa em «Verificando…»).

---

## 5. Contrato fiscal (resumo)

Ver especificação §2 para detalhes. Implementação alinhada:

- Documento: pad **9** dígitos para apresentação e match.
- Valor: vírgula PT-BR aceita no MFE e na API.
- Duplicidade: chave sem valor da nota → **409**.
- Divergência pós-lançamento: alerta, **sem** reabrir `posted`.

---

## 6. Arquitetura no monorepo

| Camada | Path |
|--------|------|
| MFE | `plugins/lancamento-notas-fiscais/` |
| Router | `api-delpi/.../lancamento_notas_fiscais_router.py` |
| Use cases | `api-delpi/.../invoice_posting_use_cases.py` |
| Migrations | `api-delpi/migrations/plugins/lancamento-notas-fiscais/` |
| Manifest | `lancamento-notas-fiscais.manifest.json` |

Não há `*-api` dedicada: tudo na **api-delpi** + Postgres plugins + leitura TOTVS.

---

## 7. Deploy e operação

### Dev

```bash
./infra/scripts/up-dev-sequential.sh --fase api --build api-delpi
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin lancamento-notas-fiscais
./infra/scripts/up-dev-sequential.sh --fase mfe --build lancamento-notas-fiscais
```

### Produção

```bash
./infra/scripts/up-prod-sequential.sh --fase api --build api-delpi
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin lancamento-notas-fiscais
./infra/scripts/up-prod-sequential.sh --fase mfe --build lancamento-notas-fiscais
```

**Migrations:** nunca editar `V00x` já aplicado — criar `V00N` novo (`migrations-immutable-checksum.mdc`).

### Smoke

```bash
curl -sI http://localhost/apps/lancamento-notas-fiscais/assets/remoteEntry.js | head -3
# + GET /apps/api-delpi/lancamento-notas-fiscais/requests com JWT e caller header
```

### Keycloak / Portal

Registrar manifesto (permissões + rota menu Financeiro). Atribuir papéis reais:

- Operação de recebimento → `access` + `create`
- Fiscal / lançamento → `access` + `view` + `process`
- Admin do processo → `manage` (+ demais conforme necessidade)

---

## 8. Ondas (histórico e próximo)

| Onda | Objetivo | Status |
|------|----------|--------|
| 0 | Homologação TOTVS (SF1/SA2/chave) | Feito |
| 1 | Spec + schema Postgres (V001+) | Feito |
| 2 | API + máquina de estados + conciliação | Feito |
| 3 | MFE fila / form / detalhe | Feito |
| 4 | UX (header IE, Já lançada, doc 9, valor BR) | Feito |
| 5 | Job agendado de conciliação (cron) | Backlog |
| 6 | RBAC por filial `.view.filial-*` | Backlog (fora do v1) |
| 7 | Resumo KPI da fila / chat agent | Backlog |

---

## 9. Anti-padrões

| Evitar | Preferir |
|--------|----------|
| `PATCH status` livre | Ações explícitas (`start`, `block`, …) |
| Justificativa obrigatória em Já lançada | Confirmação + histórico opcional |
| Travamento da UI no refresh | Cooldown API + timeout cliente + listagem independente |
| Serviço/rota sem doc | README + `docs/api/lancamento-notas-fiscais.md` + inventário 08 |
| Editar migration aplicada | Nova `V00N` |
| `docker compose up --build` em massa | Scripts sequenciais |

---

## 10. Checklist de excelência (release)

- [ ] Migrations `up` no ambiente
- [ ] Manifesto registrado; papéis Keycloak batem com a matriz §3
- [ ] Smoke `remoteEntry.js` + listagem autenticada
- [ ] Criar → start → (block/resume) → post-manual **ou** auto-match
- [ ] Solicitante só vê próprias; atendente vê fila
- [ ] Documento exibe 9 dígitos; valor com vírgula
- [ ] Índices doc atualizados (06, 10, 08-plugins)
