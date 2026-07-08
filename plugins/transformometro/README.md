# Transformômetro (MFE)

Plugin microfrontend do Transformômetro para o portal Minha Delpi.

## Rotas

| Path | Página |
|------|--------|
| `/apps/transformometro/dashboard` | KPIs, 3 visões (consolidado/filial/dept), alertas, export, recalcular |
| `/apps/transformometro/processos` | Lista; create com primeira instância |
| `/apps/transformometro/processos/{id}` | **Workspace** do processo-mestre (árvore lateral) |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}` | Melhoria no workspace |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}/revisoes/{revisaoId}` | URL canônica da revisão + subpastas na árvore |
| `/apps/transformometro/configuracoes/unidades` | **Workspace Configurações** — catálogo de unidades |
| `/apps/transformometro/configuracoes/departamentos` | Departamentos no workspace |
| `/apps/transformometro/configuracoes/recursos` | Recursos compartilhados no workspace |
| `/apps/transformometro/dados` | Export/import backup JSON |

**Legado (ainda parseado):** `/filiais`, `/setores`, `/recursos`, `/cadastros/*` — redirecionam para o mesmo conteúdo em `/configuracoes/*`.

**Fonte de dados:** Postgres via `transformometro-api` (não planilha Google).

Cadastro pelas telas do app. Backup/restauração via **Exportar / Importar JSON** (mesclar por ID ou substituir tudo) — inclui diagramas macro, escopos e overlays (Playbook 19).

## Workspaces (jul/2026)

Dois ambientes com **árvore lateral** colapsável e redimensionável (persistência no `localStorage`):

| Aba | Árvore | Conteúdo principal |
|-----|--------|-------------------|
| **Processos** | Processo → seções (visão geral, mapeamento, diagrama, melhorias…) → melhoria → revisão → **subpastas** (matriz, vigência, medição…) | Detalhe embutido à direita |
| **Configurações** | Unidades / Departamentos / Recursos → itens do catálogo → subpastas do recurso (dados, custos, vínculos) | Listas e formulários embutidos |

Na revisão, cada subpasta corresponde a uma seção do cadastro (hash `#matriz`, `#vigencia`, etc.). Badge de quadrante (matriz impacto × esforço) aparece no nó da revisão na árvore de Processos.

## Diagramas (Playbook 19)

| Camada | Onde na UI |
|--------|------------|
| **Macro** | Workspace processo → **Diagrama macro** |
| **Escopo** | Workspace melhoria → **Escopo no diagrama** |
| **Overlay** | Workspace revisão → **Diagrama da revisão** (as-is / to-be) |

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

`transformometro.manifest.json` — registrar na Core API após deploy (rotas dashboard, processos, configurações, `/dados`):

```bash
export TOKEN="<jwt apps.manage>"
export BASE_URL="https://www.minhadelpi.com.br"
chmod +x scripts/register-manifest.sh
./scripts/register-manifest.sh
```

Permissão do catálogo: `transformometro.shared-resources.manage` (atribuir na **Core API** RBAC, não no Keycloak).

Documentação RBAC: [modelo-rbac.md](../../docs/09-banco-de-dados/modelo-rbac.md).

Documentação: [docs/12-roadmap-e-evolucao/transformometro-app/](../../docs/12-roadmap-e-evolucao/transformometro-app/README.md)
