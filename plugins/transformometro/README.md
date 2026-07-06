# Transformômetro (MFE)

Plugin microfrontend do Transformômetro para o portal Minha Delpi.

## Rotas

| Path | Página |
|------|--------|
| `/apps/transformometro/dashboard` | KPIs, 3 visões (consolidado/filial/dept), alertas, export, recalcular |
| `/apps/transformometro/processos` | Lista; create com primeira instância |
| `/apps/transformometro/processos/{id}` | Mestre + painel instâncias + revisões + **diagrama macro** |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}` | Instância + **escopo no diagrama** |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}/revisoes/{revisaoId}` | URL canônica da revisão + **overlay diagrama** |
| `/apps/transformometro/filiais` | CRUD filiais |
| `/apps/transformometro/setores` | Catálogo de departamentos |
| `/apps/transformometro/recursos` | Catálogo global (`escopo_recurso`) |
| `/apps/transformometro/dados` | Export/import backup JSON |

**Fonte de dados:** Postgres via `transformometro-api` (não planilha Google).

Cadastro pelas telas do app. Backup/restauração via **Exportar / Importar JSON** (mesclar por ID ou substituir tudo) — inclui diagramas macro, escopos e overlays (Playbook 19).

## Diagramas (Playbook 19)

| Camada | Onde na UI |
|--------|------------|
| **Macro** | Detalhe do processo → seção «Diagrama macro» |
| **Escopo** | Detalhe da instância → «Escopo no diagrama» (subset de nós) |
| **Overlay** | Cadastro da revisão → «Diagrama da revisão» (as-is / to-be) |

Editor: React Flow (`FlowchartEditor`, lazy) — BPMN-lite, swimlanes, templates, auto-layout, export PNG.

Documentação: [PLAYBOOK-19](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-19-diagramas-processo-revisao-escopo.md) · [status implementação](../../transformometro-api/docs/playbook-19-implementation-status.md).

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
