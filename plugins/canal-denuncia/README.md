# Canal de Denúncia — plugin Minha DELPI

Microfrontend (Module Federation) para envio de **denúncias anônimas** à Ouvidoria via **api-delpi**.

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `canal-denuncia` | Formulário de relato (somente descrição) |
| **api-delpi** `POST /canal-denuncia/denuncias` | Persistência + notificação Microsoft Graph |

```text
Portal (com conta)
  → /apps/canal-denuncia
      → POST /apps/api-delpi/canal-denuncia/denuncias   (JWT)

Público (sem conta)
  → /p/canal-denuncia/denuncia/aberto
      → POST /apps/api-delpi/public/canal-denuncia/denuncias
```

## Permissão

| Código | Uso |
|--------|-----|
| `canal-denuncia.access` | Abrir o app e enviar denúncia |

## API

Doc: [api-delpi/docs/api/canal-denuncia.md](../../api-delpi/docs/api/canal-denuncia.md)

| Método | Endpoint | Quem |
|--------|----------|------|
| POST | `/canal-denuncia/denuncias` | autenticado (`canal-denuncia.access`) |
| POST | `/public/canal-denuncia/denuncias` | público (sem JWT) |

```json
{ "description": "Texto da denúncia" }
```

Body contém **somente** `description` (10–8000 caracteres). Sem nome, e-mail ou identificação no payload.

Link público: `/p/canal-denuncia/denuncia/aberto` (copiável no próprio plugin).

## Desenvolvimento local

```bash
cd plugins/canal-denuncia
npm install
npm run lint
npm test
npm run build
```

Registrar manifesto (quando autorizado):

```bash
TOKEN=$(bash infra/scripts/get-dev-token.sh) bash plugins/canal-denuncia/scripts/register-manifest.sh
```

## Docker

Container: `delpi-canal-denuncia` (Compose profile `plugins` em dev).
