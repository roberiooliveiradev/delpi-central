# Canal de Denúncia — plugin Minha DELPI

Microfrontend (Module Federation) para envio de **denúncias anônimas** à Ouvidoria via **api-delpi**.

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `canal-denuncia` | Formulário de relato (somente descrição) |
| **api-delpi** `POST /canal-denuncia/denuncias` | Persistência + notificação Microsoft Graph |

```text
Portal → /apps/canal-denuncia
           ↓ Module Federation (remoteEntry.js)
         MFE canal-denuncia
           ↓ JWT + X-Delpi-Caller-App: canal-denuncia
Gateway → /apps/api-delpi/canal-denuncia/denuncias
```

## Permissão

| Código | Uso |
|--------|-----|
| `canal-denuncia.access` | Abrir o app e enviar denúncia |

## API

`POST /apps/api-delpi/canal-denuncia/denuncias`

```json
{ "description": "Texto da denúncia" }
```

Body contém **somente** `description` (10–8000 caracteres). Sem nome, e-mail ou identificação no payload.

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
