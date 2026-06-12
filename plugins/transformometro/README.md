# Transformômetro (MFE)

Plugin microfrontend do Transformômetro para o portal Minha Delpi.

## Rotas

| Path | Página |
|------|--------|
| `/apps/transformometro/dashboard` | KPIs, 3 visões (consolidado/filial/dept), alertas, export, recalcular |
| `/apps/transformometro/processos` | Lista; create com primeira instância |
| `/apps/transformometro/processos/{id}` | Mestre + painel instâncias + revisões |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}/revisoes/{revisaoId}` | URL canônica da revisão |
| `/apps/transformometro/filiais` | CRUD filiais |
| `/apps/transformometro/setores` | Catálogo de setores |
| `/apps/transformometro/recursos` | Catálogo global (`escopo_recurso`) |
| `/apps/transformometro/dados` | Export/import backup JSON |

**Fonte de dados:** Postgres via `transformometro-api` (não planilha Google).

Cadastro pelas telas do app. Backup/restauração via **Exportar / Importar JSON** (mesclar por ID ou substituir tudo).

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

`transformometro.manifest.json` — registrar na Core API após deploy (rotas dashboard, processos, recursos, `/dados`):

```bash
export TOKEN="<jwt apps.manage>"
export BASE_URL="https://www.minhadelpi.com.br"
chmod +x scripts/register-manifest.sh
./scripts/register-manifest.sh
```

Permissão do catálogo: `transformometro.shared-resources.manage` (atribuir na **Core API** RBAC, não no Keycloak).

Documentação RBAC: [modelo-rbac.md](../../docs/09-banco-de-dados/modelo-rbac.md).

Documentação: [docs/12-roadmap-e-evolucao/transformometro-app/](../../docs/12-roadmap-e-evolucao/transformometro-app/README.md)
