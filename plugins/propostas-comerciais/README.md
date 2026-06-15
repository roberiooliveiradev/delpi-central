# Propostas Comerciais — plugin Minha DELPI

Microfrontend (Module Federation) para consulta **read-only** de propostas comerciais **ativas** no Protheus/TOTVS, com detalhe operacional e emissão de PDF (incluindo revisão editável antes da exportação).

Documentação completa: [docs/12-roadmap-e-evolucao/propostas-comerciais/](../../docs/12-roadmap-e-evolucao/propostas-comerciais/) — em especial [ESPECIFICACAO-PLUGIN.md](../../docs/12-roadmap-e-evolucao/propostas-comerciais/ESPECIFICACAO-PLUGIN.md) e [ESPECIFICACAO-DADOS-TOTVS.md](../../docs/12-roadmap-e-evolucao/propostas-comerciais/ESPECIFICACAO-DADOS-TOTVS.md).

---

## Funcionalidades (resumo)

- Listagem das propostas ativas recentes (`ADY_STATUS = 'A'`)
- Busca local por OV, oportunidade, proposta interna ou cliente
- Detalhe: empresa DELPI, cliente **ou prospect**, contato, condições, vendedor, observações e itens
- Emissão de PDF com modal de revisão (observações, contato, condições e vendedor editáveis antes de exportar)
- Fallback automático para cadastro de **prospect** (`SUS010`) quando a proposta não possui cliente em `SA1010`

---

## Rotas

| Rota | Finalidade | Permissão |
|------|------------|-----------|
| `/apps/propostas-comerciais` | Listagem | `propostas-comerciais.view` |
| `/apps/propostas-comerciais/{proposta_interna}` | Detalhe + PDF | `propostas-comerciais.view` |

---

## API

Base: `/apps/api-delpi/propostas-comerciais`

```http
GET  /apps/api-delpi/propostas-comerciais?limit=100
GET  /apps/api-delpi/propostas-comerciais/{proposta_interna}
GET  /apps/api-delpi/propostas-comerciais/{proposta_interna}/pdf
POST /apps/api-delpi/propostas-comerciais/{proposta_interna}/pdf
```

Permissões aceitas na API: `propostas-comerciais.view`, `api-delpi.access`, `dashboard-commercial.view`.

Envelope JSON: `{ success, message, data, meta }`.

---

## Desenvolvimento local

```bash
cd plugins/propostas-comerciais
npm install
npm run dev
```

Standalone: `http://localhost:5173/apps/propostas-comerciais/` (sem auth — apenas layout).

Integrado ao portal: subir o stack `infra/` e registrar o manifesto (abaixo).

Build:

```bash
npm run build
```

Docker (a partir de `infra/`):

```bash
docker compose -f docker-compose.dev.yml build propostas-comerciais --no-cache
docker compose -f docker-compose.dev.yml up -d propostas-comerciais gateway api-delpi
```

Após mudanças só no **backend**:

```bash
docker compose -f docker-compose.dev.yml restart api-delpi
```

---

## Registro no Portal

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
bash plugins/propostas-comerciais/scripts/register-manifest.sh
```

Atribua `propostas-comerciais.view` ao perfil desejado no RBAC.

---

## Smoke

```bash
curl -sI http://localhost/apps/propostas-comerciais/assets/remoteEntry.js | head -5

# Health da API (via container)
docker exec delpi-api-delpi curl -sf http://localhost:8000/health
```

Validação funcional (prospect):

```bash
docker exec delpi-api-delpi python -c "
from app.composition.propostas_comerciais_composer import build_get_proposta_comercial_use_case
d = build_get_proposta_comercial_use_case().execute('004836')
print(d['cliente']['nome'], d['cliente']['tipo_cadastro'])
"
```

---

## Estrutura do código

```text
src/
  api/              # HTTP + envelope api-delpi
  components/       # tabela, modal PDF, cards, busca
  hooks/            # listagem, detalhe, PDF, roteamento
  pages/            # list + detail
  types/            # contratos espelhando a API
  utils/            # rotas, navegação, filtro local
```

Backend: `api-delpi/app/infrastructure/totvs/propostas_comerciais/` + `domain/propostas_comerciais/`.

Testes: `api-delpi/tests/test_propostas_comerciais.py`.

---

## Variáveis de ambiente (api-delpi)

| Variável | Default | Uso |
|----------|---------|-----|
| `PROPOSTAS_COMERCIAIS_EMPRESA_SITE` | `www.delpi.com.br` | Site exibido no bloco empresa |
| `PROPOSTAS_COMERCIAIS_PDF_LOGO_PATH` | — | Logo opcional no PDF |
