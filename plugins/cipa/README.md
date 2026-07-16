# Plugin CIPA

Gestão de atas da CIPA com assinatura manuscrita, versionamento e isolamento por filial (`01` / `02`).

## Fluxo

```text
Portal → plugins/cipa (MFE) → /apps/cipa-api → schema cipa (postgres-plugins)
```

## Rotas UI

| Path | Descrição |
|------|-----------|
| `/apps/cipa/filial-01` | Lista de atas SC |
| `/apps/cipa/filial-02` | Lista de atas ES |
| `/apps/cipa/filial-{xx}/minutes/new` | Nova ata |
| `/apps/cipa/filial-{xx}/minutes/{id}` | Detalhe |
| `/apps/cipa/filial-{xx}/minutes/{id}/edit` | Edição |
| `/apps/cipa/filial-{xx}/minutes/{id}/sign` | Assinatura |
| `/apps/cipa/pending` | Pendências do usuário |

## API

Base: `/apps/cipa-api` — ver [cipa-api/README.md](../../cipa-api/README.md).

## Permissões

Códigos `cipa.minutes.{ação}.filial-{01|02}` e `cipa.admin.filial-{01|02}` — ver `cipa.manifest.json`.

## Dev

```bash
cd plugins/cipa && npm install && npm run build
TOKEN=… bash scripts/register-manifest.sh
./infra/scripts/up-dev-sequential.sh --fase api --build cipa-api
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build cipa
```

## Smoke

```bash
curl -fsS http://localhost/apps/cipa/assets/remoteEntry.js | head -c 80
curl -fsS http://localhost/apps/cipa-api/health
```
