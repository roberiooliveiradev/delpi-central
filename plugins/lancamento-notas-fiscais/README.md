# Lançamento de Notas Fiscais — plugin Minha DELPI

Microfrontend federado para **solicitar, acompanhar e concluir** o lançamento de notas fiscais de entrada no Protheus, com fila operacional, conciliação automática (SF1) e confirmação manual quando o match automático falha.

Documentação de roadmap: [docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/](../../docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/) · API: [lancamento-notas-fiscais.md](../../api-delpi/docs/api/lancamento-notas-fiscais.md).

---

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `lancamento-notas-fiscais` | Fila, cadastro/correção, detalhe (ações + histórico) |
| **api-delpi** `/lancamento-notas-fiscais/*` | CRUD operacional + conciliação + RBAC por papel |
| **postgres-plugins** | Solicitações, histórico, comentários, controle de refresh |
| **TOTVS** | Fornecedores `SA2`; matching de NF em `SF1` (confirmação opcional `SD1`) |

```text
Portal → /apps/lancamento-notas-fiscais
           ↓ Module Federation (remoteEntry.js)
         MFE lancamento-notas-fiscais
           ↓ JWT + X-Delpi-Caller-App: lancamento-notas-fiscais
Gateway → /apps/api-delpi/lancamento-notas-fiscais/*
           ↓
         api-delpi → Postgres (plugins) + SQL Server (SA2/SF1)
```

---

## Funcionalidades

- Cadastro de solicitação após recebimento físico (filial, nota, série, fornecedor, valor, data/hora)
- Fila FIFO por `received_at` (mais antigas primeiro), filtros e cards no mobile
- Refresh de conciliação ao abrir a fila (cooldown 45s) — não bloqueia a listagem
- Atendimento: iniciar, bloquear, retomar, comentar, **Já lançada** (confirmação sem justificativa)
- Detalhe em layout denso (resumo + dados fiscais/situação + histórico sticky)
- Documento com **9 dígitos** (zeros à esquerda); valor aceita **vírgula** (formato BR)

---

## Rotas da UI

Navegação interna (estado React; base do portal `/apps/lancamento-notas-fiscais`):

| View | Conteúdo |
|------|----------|
| Fila | Lista + filtros + sync Protheus |
| Nova / Corrigir | Formulário de solicitação |
| Detalhe | Resumo, dados fiscais, situação, ações, histórico |

Menu Portal: grupo **Financeiro** · permissão `lancamento-notas-fiscais.access`.

---

## API (gateway)

Base HTTP: **`/apps/api-delpi/lancamento-notas-fiscais`**

| Método | Rota | Uso no MFE |
|--------|------|------------|
| GET | `/suppliers?query=&limit=` | Autocomplete fornecedor |
| POST | `/requests` | Criar |
| GET | `/requests` | Fila paginada |
| GET | `/requests/{id}` | Detalhe + timeline + `allowed_actions` |
| PATCH | `/requests/{id}` | Corrigir dados |
| POST | `/requests/{id}/start` | Iniciar atendimento |
| POST | `/requests/{id}/block` | Bloquear |
| POST | `/requests/{id}/resume` | Retomar |
| POST | `/requests/{id}/comments` | Comentar |
| POST | `/requests/{id}/cancel` | Cancelar |
| POST | `/requests/{id}/post-manual` | Marcar **Já lançada** |
| POST | `/reconciliation/refresh` | Sync ao abrir fila |
| POST | `/reconciliation/run` | Lote admin (`manage`) |

Envelope padrão api-delpi (`success`, `data`, `meta`, `message`).

Documentação completa: [api-delpi/docs/api/lancamento-notas-fiscais.md](../../api-delpi/docs/api/lancamento-notas-fiscais.md).

### Exemplo — listar fila

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: lancamento-notas-fiscais" \
     "http://localhost/apps/api-delpi/lancamento-notas-fiscais/requests?page=1&page_size=20" \
  | jq '.success, .meta.operationId, .data.total'
```

---

## Permissões (Portal / Keycloak)

| Código | Papel |
|--------|--------|
| `lancamento-notas-fiscais.access` | Abrir o plugin |
| `lancamento-notas-fiscais.create` | **Solicitante** — cadastrar / corrigir / cancelar próprias |
| `lancamento-notas-fiscais.view` | Consultar fila (todas as solicitações autorizadas) |
| `lancamento-notas-fiscais.process` | **Atendente** — start/block/resume/Já lançada/comentar |
| `lancamento-notas-fiscais.manage` | Admin — cancelar não terminais + conciliação em lote |

Escopo de fila: `create` sem `view`/`process`/`manage` vê **somente as próprias**.  
v1 **sem** `.view.filial-*` (filiais `01`/`02` no formulário; consulta ampla para quem tem view/process/manage).

Detalhe solicitante × atendente: [PLAYBOOK.md](../../docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/PLAYBOOK.md) § papéis.

---

## Estrutura do código (MFE)

```text
src/
  App.tsx                         # Views: fila / form / detalhe
  application/                    # Permissões (contexto)
  data/api/                       # httpClient + invoicePostingApi
  domain/                         # types, status, fiscal (doc/valor)
  ui/pages/                       # Queue, Form, Detail
  ui/components/                  # Header, filtros, modais, badges
  index.css                       # Tokens LNF + header estilo IE
```

---

## Desenvolvimento local

### Standalone (Vite)

```bash
cd plugins/lancamento-notas-fiscais
npm install
export TOKEN="$(bash ../../infra/scripts/get-dev-token.sh)"
echo "VITE_DEV_ACCESS_TOKEN=$TOKEN" > .env.local
npm run dev
```

### Docker (compose sequencial — preferido)

```bash
# Na raiz do repo
./infra/scripts/up-dev-sequential.sh --fase api --build api-delpi
./infra/scripts/up-dev-sequential.sh --fase mfe --build lancamento-notas-fiscais
```

Migrations do plugin (startup da api-delpi ou manual):

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin lancamento-notas-fiscais
```

Assets: `http://localhost/apps/lancamento-notas-fiscais/assets/remoteEntry.js`

---

## Build e registro no portal

```bash
cd plugins/lancamento-notas-fiscais
npm run ci   # ou: npm run build

export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
./scripts/register-manifest.sh   # a partir da raiz, se o script existir no pacote
```

Manifesto: `lancamento-notas-fiscais.manifest.json`.

---

## Smoke

```bash
curl -sI "http://localhost/apps/lancamento-notas-fiscais/assets/remoteEntry.js" | head -5

export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: lancamento-notas-fiscais" \
     "http://localhost/apps/api-delpi/lancamento-notas-fiscais/requests?page=1&page_size=5" \
  | jq '.success, .data.total'
```

---

## Produção

```bash
git pull
./infra/scripts/up-prod-sequential.sh --fase api --build api-delpi
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin lancamento-notas-fiscais
./infra/scripts/up-prod-sequential.sh --fase mfe --build lancamento-notas-fiscais
```

---

## Referências

| Documento | Conteúdo |
|-----------|----------|
| [PLAYBOOK.md](../../docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/PLAYBOOK.md) | Operação, papéis, conciliação, deploy |
| [especificacao-funcional-tecnica.md](../../docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/especificacao-funcional-tecnica.md) | Contrato de domínio |
| [ROADMAP.md](../../docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/ROADMAP.md) | Etapas e status |
| [API](../../api-delpi/docs/api/lancamento-notas-fiscais.md) | Contrato HTTP |
| [Inventário plugins](../../docs/08-plugins/README.md) | Registro no monorepo |
