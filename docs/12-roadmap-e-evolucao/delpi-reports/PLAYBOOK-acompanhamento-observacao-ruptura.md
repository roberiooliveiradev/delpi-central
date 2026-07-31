# Playbook — Acompanhamento na Observação (ruptura 30d)

> **Branch:** `feat/reports-ruptura-30d-interacao`  
> **Status:** Fases 0–4 **e 4b (link e-mail)** **concluídas** · Fase 5 planejada  
> **Provider:** `safety_stock_shortage_30d`

---

## Problema

Os destinatários do e-mail diário de rupturas reanalisam os mesmos itens todos os dias, mesmo quando já há previsão de recebimento ou resposta operacional. Isso gera retrabalho.

## Escopo Fase 1 (desta entrega parcial)

| Inclui | Não inclui |
|--------|------------|
| Persistência de nota por item (`definition` + filial + produto) | Ocultar / suspender item do e-mail |
| Texto de acompanhamento + nome do autor | Histórico versionado de notas |
| Documento e migration | API HTTP / MFE / enrich no e-mail (Fases 2–4) |
| Data opcional de previsão (campo informativo) | Reply / parse de Outlook |
| | Deep link no corpo do e-mail |

## Formato da Observação (quando enrich estiver ligado — Fase 3)

- **Sem** acompanhamento: observação de sistema (terceiro / amostra), se houver.
- **Com** acompanhamento: **somente** o trecho humano (a observação padrão é desconsiderada):

```text
Acompanhamento (Nome do Usuário): {texto}
```

Se existir `expected_receipt_date`, inclui a data formatada `DD/MM/AAAA` no início do trecho:

```text
Acompanhamento (Nome): Previsão DD/MM/AAAA — {texto}
```

Itens **continuam** no e-mail; só a coluna Observação muda.

## Modelo de dados

Tabela `reports.shortage_item_notes` — ver [SCHEMA.md](./SCHEMA.md).

- Chave natural: `(definition_id, branch, product_code)` — **upsert** substitui a nota anterior.
- `author_user_id` + `author_display_name` obrigatórios na gravação.

## Permissões

| Código | Uso |
|--------|-----|
| `reports.view` / `view.filial-*` | Abrir app, listar, preview, GET notes |
| `reports.manage` / `manage.filial-*` | Configuração da definição + notes |
| **`reports.notes.manage`** | Só acompanhamentos (com view da filial) — operacional |

## Fases de entrega

| Fase | Entrega | Status |
|------|---------|--------|
| **0** | Este playbook + ROADMAP/SCHEMA | **Concluída** |
| **1** | Migration `V004` + métodos no `PostgresReportsRepository` | **Concluída** |
| **2** | Rotas GET/PUT/DELETE `item-notes` + OpenAPI/docs | **Concluída** |
| **3** | Enrich da `observation` no run/preview | **Concluída** |
| **4** | UI Acompanhamentos (definição + tela operacional) | **Concluída** |
| **4b** | Link rodapé e-mail + `reports.notes.manage` | **Concluída** |
| **5** | Testes de regressão + deploy `api-delpi` + `reports` | Pendente |

**Como testar (UI + API + e-mail):**  
[PLAYBOOK-testes-acompanhamento-observacao.md](./PLAYBOOK-testes-acompanhamento-observacao.md)

## Deploy (quando Fases 2–4 fecharem)

```bash
./infra/scripts/up-*-sequential.sh --fase core --build api-delpi
./infra/scripts/up-*-sequential.sh --fase mfe --build reports
```

Migration em produção: **somente** `up --plugin reports` (nunca `reset`).

## Critérios de pronto (Fase 1)

- [x] `V004__shortage_item_notes.sql` versionada e aplicável
- [x] Repository: list / upsert / delete / map por produto
- [x] SCHEMA.md e ROADMAP.md atualizados

## Critérios de pronto (Fase 2)

- [x] GET/PUT/DELETE `/definitions/{id}/item-notes`
- [x] RBAC: read + filial view; write + filial manage
- [x] Contratos OpenAPI + `route_contract_registry`
- [x] Doc `delpi-reports.md` + smoke/unit tests

## Critérios de pronto (Fase 3)

- [x] `build_follow_up_observation` + `compose_observation_parts`
- [x] Enrich pós-collect no run agendado / «Enviar agora»
- [x] Preview com `definitionId` opcional aplica as mesmas notas
- [x] Itens **não** são ocultados do e-mail

## Critérios de pronto (Fase 4)

- [x] Seção Acompanhamentos em `DefinitionDetailPage`
- [x] Listar / upsert / remover via API `item-notes`
- [x] Autor pré-preenchido de `/core-api/me`; códigos opcionais do preview
