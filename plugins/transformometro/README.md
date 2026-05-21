# Transformômetro (MFE)

Plugin microfrontend do Transformômetro para o portal Minha Delpi.

## Desenvolvimento

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Manifesto

`transformometro.manifest.json` — registrar na Core API após deploy:

```bash
export TOKEN="<jwt apps.manage>"
export BASE_URL="https://www.minhadelpi.com.br"
chmod +x scripts/register-manifest.sh
./scripts/register-manifest.sh
```

Documentação: [docs/12-roadmap-e-evolucao/transformometro-app/](../../docs/12-roadmap-e-evolucao/transformometro-app/README.md)
