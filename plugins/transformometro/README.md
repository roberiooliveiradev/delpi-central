# Transformômetro (MFE)

Plugin microfrontend do Transformômetro para o portal Minha Delpi.

## Rotas

| Path | Página |
|------|--------|
| `/apps/transformometro` | Início |
| `/apps/transformometro/dashboard` | Dashboard (KPIs, alertas, CSV/Excel, recalcular) |
| `/apps/transformometro/processos` | Processos e cadastro de revisões (abas) |
| `/apps/transformometro/recursos` | Catálogo global de recursos compartilhados |

Barra superior do módulo: **Dashboard · Processos · Recursos**.

Cadastro pelas telas do app. Backup/restauração completa via **Exportar / Importar JSON** (mesclar por ID ou substituir tudo).

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

`transformometro.manifest.json` — registrar na Core API após deploy (inclui rota `/recursos`):

```bash
export TOKEN="<jwt apps.manage>"
export BASE_URL="https://www.minhadelpi.com.br"
chmod +x scripts/register-manifest.sh
./scripts/register-manifest.sh
```

Permissão do catálogo: `transformometro.shared-resources.manage`.

Documentação: [docs/12-roadmap-e-evolucao/transformometro-app/](../../docs/12-roadmap-e-evolucao/transformometro-app/README.md)
