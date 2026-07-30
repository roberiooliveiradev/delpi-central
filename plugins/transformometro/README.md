# Transformômetro (MFE)

Plugin microfrontend do Transformômetro para o portal Minha Delpi.

## Rotas

| Path | Página |
|------|--------|
| `/apps/transformometro/dashboard` | KPIs, 3 visões (consolidado/filial/dept), alertas, export, recalcular |
| `/apps/transformometro/processos` | Lista; create com primeira instância |
| `/apps/transformometro/processos/{id}` | **Workspace** do processo-mestre (árvore lateral) |
| `/apps/transformometro/processos/{id}/diagrama/edit` | Editor full-page do diagrama macro (lock colaborativo) |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}` | Melhoria no workspace |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}/diagrama/edit` | Editor full-page do escopo no diagrama |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}/revisoes/{revisaoId}` | URL canônica da revisão + subpastas na árvore |
| `/apps/transformometro/processos/{id}/instancias/{instanciaId}/revisoes/{revisaoId}/diagrama/edit` | Editor full-page do overlay da revisão |
| `/apps/transformometro/configuracoes/unidades` | **Workspace Configurações** — catálogo de unidades |
| `/apps/transformometro/configuracoes/departamentos` | Departamentos no workspace |
| `/apps/transformometro/configuracoes/recursos` | Recursos compartilhados no workspace |
| `/apps/transformometro/dados` | Export/import backup JSON |
| `/apps/transformometro/atas` | Atas Transforma+ (lista por filial) |
| `/apps/transformometro/atas/new` · `…/{id}/edit` | Editor: preencher ou importar DOCX + **Gerar ata com IA** (Kimi) + signatários |
| `/apps/transformometro/atas/{id}` | Detalhe (`DocumentReader` + logo Transforma+ + faixa de marca) |
| `/apps/transformometro/atas/{id}/sign` | Assinatura (perfil salvo ou pad) |
| `/apps/transformometro/atas/pending` | Pendências de assinatura do usuário |
| `/apps/transformometro/minha-assinatura` | Perfil de assinatura pessoal |

**Legado (ainda parseado):** `/filiais`, `/setores`, `/recursos`, `/cadastros/*` — redirecionam para o mesmo conteúdo em `/configuracoes/*`.

**Fonte de dados:** Postgres via `transformometro-api` (não planilha Google).

Cadastro pelas telas do app. Backup/restauração via **Exportar / Importar JSON** (mesclar por ID ou substituir tudo) — inclui diagramas macro, escopos e overlays (Playbook 19).

## Atas Transforma+

Módulo de atas oficiais (CRUD, assinatura eletrônica manuscrita, PDF, geração assistida por Kimi).

| Doc | Conteúdo |
|-----|----------|
| [docs/atas.md](./docs/atas.md) | Implementação MFE (rotas, port de IA, marca visual) |
| [ATAS-TRANSFORMA-MAIS.md](../../docs/12-roadmap-e-evolucao/transformometro-app/ATAS-TRANSFORMA-MAIS.md) | Visão de produto e fluxo |
| [atas-kimi.md](../../transformometro-api/docs/atas-kimi.md) | API + configuração `KIMI_*` |

**API base:** `/apps/transformometro-api/transformometro/atas` (JWT).  
**Permissões:** `transformometro.atas.view` / `.manage` / `.sign`.  
**Rebuild MFE:** `./infra/scripts/up-dev-sequential.sh --fase mfe --build transformometro`

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
| **Macro** | Workspace processo → preview em **#diagrama** → **Editar diagrama** (página `/diagrama/edit`) |
| **Escopo** | Workspace melhoria → preview → **Editar diagrama** (página `/diagrama/edit`) |
| **Overlay** | Workspace revisão → preview → **Editar diagrama** (página `/diagrama/edit`) |

Preview na seção `#diagrama` é somente leitura (com «Tela cheia» ampliada). A edição abre página dedicada full-page (mesmo padrão das atas), com lock colaborativo nas chaves `diagrama_macro` / `diagrama_escopo` / `diagrama_revisao`.

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
