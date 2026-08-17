# Canal de Denúncia

Envio anônimo de relatos à Ouvidoria. Quem tem conta usa o plugin no portal; quem não tem usa o formulário público.

**Plugin:** [plugins/canal-denuncia/README.md](../../../plugins/canal-denuncia/README.md)  
**Página pública:** `/p/canal-denuncia/denuncia/aberto` (public-hub, token estático `aberto`)

## Contrato

Envelope `{ success, message, data, meta }` via `api_delpi_success`.  
Schema Postgres: `canal_denuncia` (plugins). Sem identidade e sem anexos.

| operationId | entity | shape |
|-------------|--------|-------|
| `create_canal_denuncia` | `canal_denuncia` | scalar |
| `create_public_canal_denuncia` | `canal_denuncia` | scalar |

## Admin (JWT)

Prefixo: `/canal-denuncia`

| Método | Path | operationId | Perm. |
|--------|------|-------------|-------|
| POST | `/denuncias` | `create_canal_denuncia` | `canal-denuncia.access` |

Body: `{ "description": "..." }` (10–8000 caracteres). Sem nome, e-mail ou identificação.

## Público (sem JWT)

Liberado em `auth_middleware` pelo prefixo `/public/canal-denuncia/`.

| Método | Path | operationId |
|--------|------|-------------|
| POST | `/public/canal-denuncia/denuncias` | `create_public_canal_denuncia` |

Mesmo `description`. Honeypot `website`: se preenchido, a API devolve sucesso e **não** grava o relato.

```bash
curl -fsS -X POST http://localhost/apps/api-delpi/public/canal-denuncia/denuncias \
  -H 'Content-Type: application/json' \
  -d '{"description":"Relato anônimo com detalhes suficientes."}'
```

O use case é o mesmo do POST autenticado (persistência + e-mail à Ouvidoria).
