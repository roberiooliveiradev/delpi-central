# Playbook de testes — Acompanhamento na Observação (ruptura 30d)

> **Objetivo:** validar o fluxo completo (API + MFE + e-mail) das Fases 0–4 e do **Plano B** (link no rodapé + tela operacional).  
> **Produto:** [PLAYBOOK-acompanhamento-observacao-ruptura.md](./PLAYBOOK-acompanhamento-observacao-ruptura.md)  
> **Provider:** `safety_stock_shortage_30d`  
> **Apps:** `api-delpi` + MFE `reports` (`/apps/reports`)

---

## 1. O que se testa

| Capacidade | Resultado esperado |
|------------|-------------------|
| Gravar acompanhamento por produto | Nota persistida em `reports.shortage_item_notes` |
| Tela operacional `/acompanhamentos/{id}` | Form/tabela **sem** config da definição |
| Listar / editar / remover (admin) | Também na definição (atalho) |
| Preview com `definitionId` | Coluna Observação já traz o acompanhamento |
| Enviar agora / agenda | Observação enriquecida; item **continua** na lista |
| Rodapé do e-mail | Link «Abrir acompanhamentos…» → portal |
| Formato do texto | Com nota: só `Acompanhamento (Nome): …` (sem obs. de sistema) |

**Fora deste playbook:** ocultar item do e-mail, reply Outlook, link por linha de produto.

---

## 2. Pré-requisitos

### 2.1 Permissões do usuário de teste

| Perfil | Permissões | Pode |
|--------|------------|------|
| **Operacional** | **`reports.notes.manage`** + `reports.view.filial-*` (**sem** `reports.view`) | Só aba/menu Acompanhamentos; gravar/remover notas |
| **Leitura admin** | `reports.view` (+ filial se escopo) | Visão geral, Relatórios, Acompanhamentos (sem gravar definição) |
| **Admin** | `reports.manage` (+ `manage.filial-*`) | Tudo acima + params/agenda/destinatários/enviar |

Sem `notes.manage` (nem manage), o `PUT`/`DELETE` de `item-notes` retorna **403**.  
Com `reports.view`, o usuário vê as abas administrativas — **não** atribua `view` no perfil operacional.

Após deploy: **re-registrar o manifest** do plugin `reports` e atribuir `reports.notes.manage` no portal.

### 2.2 Deploy (dev)

Na raiz do monorepo:

```bash
./infra/scripts/up-dev-sequential.sh --fase core --build api-delpi
./infra/scripts/up-dev-sequential.sh --fase mfe --build reports
```

Confirmar `PUBLIC_BASE_URL` em `infra/.env` (ex.: `http://localhost` ou URL do portal) — sem isso o e-mail **não** traz o link.

### 2.3 Migration (obrigatória)

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin reports
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin reports
```

Checklist:

1. `status` — `V001`…`V003` = **APLICADA**; `V004` pendente ou já aplicada.
2. **Nunca** `reset --plugin reports` em ambiente com dados.
3. Conferir: `V004__shortage_item_notes.sql` aplicada.

### 2.4 Definição de relatório

Ter (ou criar) uma definição ativa:

- Provider: **Rupturas 30 dias** (`safety_stock_shortage_30d`)
- Unidade: `01` (SC) ou `02` (ES)
- Pelo menos **1 destinatário** com e-mail real (para «Enviar agora»)
- Agenda opcional (não necessária para o teste manual)

Anotar o **UUID** da definição (URL `/apps/reports/{id}`).

---

## 3. Testes automatizados (regressão)

Rodar no container da API:

```bash
docker exec delpi-api-delpi python -m pytest \
  tests/test_reports_routes_smoke.py \
  tests/test_report_schedule_and_run.py \
  tests/test_reports_branch_access.py \
  tests/test_safety_stock_shortage_30d_provider.py \
  tests/test_shortage_item_notes_repository.py \
  tests/test_shortage_item_notes_use_cases.py \
  tests/test_shortage_item_note_observation_enrichment.py \
  -q
```

**Critério:** todos verdes.

Cobertura principal:

- smoke `list` / `upsert` / `delete` `item-notes`
- `build_follow_up_observation` + enrich no run/preview
- branch manage 403

Build do MFE (local, se tiver Node):

```bash
cd plugins/reports && npm run build
```

---

## 4. Fluxo manual — operacional via e-mail (Plano B)

### Passo A — Enviar / receber o e-mail

1. Admin: definição com destinatário = usuário operacional de teste
2. **Enviar agora** (ou aguardar agenda)
3. No Outlook, abrir o e-mail de rupturas
4. No **rodapé**, clicar **Abrir acompanhamentos no Delpi Reports**
5. Esperado: portal em `/apps/reports/acompanhamentos/{definitionId}` (login se necessário)

### Passo B — Gravar na tela operacional

1. Confirmar que **não** há params/agenda/destinatários/«Enviar agora»
2. Preencher código, texto, previsão opcional, autor
3. **Salvar acompanhamento**
4. Esperado: linha na tabela; próximo e-mail/preview com Observação enriquecida

### Passo C — Menu do portal

1. Com **só** `reports.notes.manage` (+ filial), o menu do portal e a sidebar do MFE exibem **apenas** Acompanhamentos (sem Visão geral / Relatórios)
2. Lista de definições ativas de ruptura → abrir a mesma tela
3. Acesso direto a `/apps/reports` redireciona para `/apps/reports/acompanhamentos`

---

## 4b. Fluxo manual na UI admin (definição)

### Passo A — Abrir a definição

1. Portal → **Delpi Reports** → `/apps/reports`
2. Abrir a definição de ruptura da unidade desejada
3. Confirmar seções: Parâmetros, Agenda, Destinatários, **Acompanhamentos**, Histórico

### Passo B — Descobrir um código de produto

Opção 1 (recomendada):

1. Na seção **Acompanhamentos**, clicar **Códigos do preview**
2. Aguardar mensagem de sucesso com a quantidade de códigos
3. No campo **Código do produto**, começar a digitar — a lista (datalist) sugere códigos do preview

Opção 2:

1. Usar um código que você já sabe que aparece no e-mail diário
2. Digitar manualmente no formulário

### Passo C — Gravar acompanhamento

1. Preencher:
   - **Código do produto** (obrigatório)
   - **Texto do acompanhamento** (obrigatório), ex.: `Confirmado com fornecedor — chega na próxima semana`
   - **Previsão de recebimento** (opcional), ex.: data daqui a 5 dias
   - **Autor** (pré-preenchido com seu nome do portal; pode editar)
2. Clicar **Salvar acompanhamento**
3. Esperado:
   - Banner verde de sucesso
   - Linha na tabela (código, texto, previsão, autor, atualizado)

### Passo D — Editar

1. Na tabela, **Editar** na linha desejada
2. Formulário preenche com os dados
3. Alterar o texto e **Salvar acompanhamento** de novo (upsert — substitui a nota anterior)
4. Esperado: mesma linha atualizada (sem duplicar o produto)

### Passo E — Conferir no preview (antes do e-mail)

Chamada implícita ao clicar **Códigos do preview** já usa `definitionId`. Para inspeção explícita, use a API (§ 5) ou:

1. Anote o `productCode` e a observação esperada
2. Após o enrich, a observação deve conter `Acompanhamento (Seu Nome): …`

### Passo F — Enviar agora

1. Garantir destinatários salvos (você pode incluir o próprio e-mail)
2. Clicar **Enviar agora**
3. Esperado:
   - Banner de sucesso
   - Nova linha no **Histórico de execuções** (`Sucesso`)
4. Abrir o e-mail no Outlook / webmail
5. Na tabela, localizar o produto:
   - Item **ainda aparece** (não some)
   - Coluna **Observação** contém o trecho de acompanhamento
6. No **rodapé** do e-mail:
   - Link «Abrir acompanhamentos no Delpi Reports»
   - URL = `{PUBLIC_BASE_URL}/apps/reports/acompanhamentos/{definitionId}`

### Passo G — Remover acompanhamento

1. Na tabela, **Remover** → confirmar
2. Esperado: linha some; banner de removido
3. **Enviar agora** de novo (ou só preview via API): observação **sem** o trecho de acompanhamento

---

## 5. Ações via API (opcional / debug)

Substitua `TOKEN`, `DEFINITION_ID` e `PRODUCT`.

Base: `/apps/api-delpi/reports` (via gateway) ou direto no container conforme o ambiente.

### 5.1 Listar

```bash
curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://<host>/apps/api-delpi/reports/definitions/$DEFINITION_ID/item-notes" | jq .
```

### 5.2 Upsert

```bash
curl -sS -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "noteText": "Confirmado com fornecedor",
    "authorDisplayName": "Maria Silva",
    "expectedReceiptDate": "2026-08-05"
  }' \
  "https://<host>/apps/api-delpi/reports/definitions/$DEFINITION_ID/item-notes/$PRODUCT" | jq .
```

### 5.3 Preview com enrich

```bash
curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://<host>/apps/api-delpi/reports/providers/safety_stock_shortage_30d/preview?branch=01&horizonDays=30&definitionId=$DEFINITION_ID" \
  | jq '.data.items[] | {product_code, observation}'
```

Filtrar um produto:

```bash
… | jq --arg p "$PRODUCT" '.data.items[] | select(.product_code == $p) | .observation'
```

### 5.4 Delete

```bash
curl -sS -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "https://<host>/apps/api-delpi/reports/definitions/$DEFINITION_ID/item-notes/$PRODUCT"
```

### 5.5 Run (e-mail)

```bash
curl -sS -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "https://<host>/apps/api-delpi/reports/definitions/$DEFINITION_ID/run" | jq .
```

Artefato HTML (se volume montado): path em `summary.artifactHtmlPath` no run — ver [OPS.md](./OPS.md) / volume `reports-runs`.

---

## 6. Matriz de verificação (checklist)

Marque ao concluir:

### Ambiente

- [ ] Migration `V004` aplicada (`status` sem pendência crítica)
- [ ] `api-delpi` + MFE `reports` rebuildados
- [ ] Manifest re-registrado; `reports.notes.manage` atribuída
- [ ] `PUBLIC_BASE_URL` correto no `.env` da api-delpi

### UI operacional (Plano B)

- [ ] Link do rodapé abre `/apps/reports/acompanhamentos/{id}`
- [ ] Tela **sem** params/agenda/destinatários
- [ ] Operacional com `notes.manage` grava nota
- [ ] Só `view` (sem notes/manage) → 403 ao gravar

### UI admin / Observação / e-mail

- [ ] Seção Acompanhamentos visível na definição
- [ ] Gravar nota cria linha na tabela
- [ ] Editar atualiza (não duplica)
- [ ] Remover exclui a linha
- [ ] Autor vem pré-preenchido
- [ ] Códigos do preview populam sugestões

### Observação / e-mail

- [ ] Preview com `definitionId` mostra `Acompanhamento (…)`
- [ ] Enviar agora: item permanece na lista
- [ ] Observação no e-mail inclui nome + texto
- [ ] Com data: aparece `Previsão DD/MM/AAAA —`
- [ ] Após delete: observação sem o trecho humano
- [ ] Observação de sistema (terceiro/amostra), se houver, permanece e fica **antes** do acompanhamento, separada por ` | `

### Automático

- [ ] Suite pytest da § 3 verde

---

## 7. Problemas comuns

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| E-mail sem link no rodapé | `PUBLIC_BASE_URL` vazio | Ajustar `.env` e rebuild/restart `api-delpi` |
| 403 ao salvar nota (operacional) | Sem `reports.notes.manage` ou sem view da filial | Atribuir permissões no portal |
| 403 ao salvar nota | Sem `reports.manage.filial-*` (admin) / notes | Ajustar permissões / filial da definição |
| Seção não aparece / UI antiga | MFE sem rebuild | `--fase mfe --build reports` |
| E-mail sem acompanhamento | API antiga ou nota em outro `definition_id` / filial | Confirmar UUID; rebuild `api-delpi`; listar `item-notes` |
| Preview sem texto | Falta `definitionId` na query | Usar preview da UI (já manda) ou curl com `definitionId=` |
| Migration / boot | Checksum ou `reset` indevido | Só `up`; nunca `reset` em prod |
| «Enviar agora» falha | Sem destinatário / Graph | Ver [OPS.md](./OPS.md); salvar destinatários antes |

---

## 8. Ordem sugerida de uma sessão de teste (30–40 min)

```text
1. Deploy api-delpi + reports + migration V004
2. pytest (§ 3)          → ~2 min
3. UI: gravar nota (§ 4B–C)
4. curl preview (§ 5.3)  → conferir observation
5. Enviar agora (§ 4F)   → conferir Outlook
6. Remover + reenviar (§ 4G) → observation limpa
7. Preencher checklist (§ 6)
```

---

## 9. Critério de pronto da Fase 5 (testes)

- [ ] Checklist § 6 completa em **dev** (e em **prod** após deploy)
- [ ] Pytest verde no `api-delpi` deployado
- [ ] Pelo menos um e-mail real validado por um responsável de suprimentos
- [ ] Nenhuma regressão: itens sem nota continuam iguais ao comportamento anterior

Deploy prod (quando liberado):

```bash
./infra/scripts/up-prod-sequential.sh --fase core --build api-delpi
./infra/scripts/up-prod-sequential.sh --fase mfe --build reports
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin reports
```
