# Roadmap — Plugin Inspeções de Entrada

> **Arquivo:** `docs/12-roadmap-e-evolucao/inspecoes-entrada/ROADMAP.md`  
> **Status:** MVP implementado em branch `feature/inspecoes-entrada` (documentação 2026-06-18)  
> **Produto:** Minha DELPI  
> **Escopo:** plugin `inspecoes-entrada` + rotas `/inspecoes-entrada/*` em `api-delpi`

---

## 1. Objetivo

Disponibilizar no Portal um **painel operacional por filial** para a equipe de qualidade/recebimento acompanhar:

- **Pendências** de inspeção de materiais recebidos;
- **Indicadores** (taxa de aprovação, tempo médio de laudo);
- **Gargalos por fornecedor** e **rejeições recentes**;
- **Histórico auditável** com detalhe de ensaios e certificado de qualidade.

**Fonte de dados:** views TOTVS `dbo.vw_minha_delpi_inspecoes_entrada_*` e tabelas de ensaio (`QER010`, etc.).

**Especificação do que está implementado:** [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md).

---

## 2. Decisões de arquitetura

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Tipo de plugin | `microfrontend` + `renderMode: federated` | Padrão dashboards operacionais |
| API dedicada (`*-api`) | **Não** | Domínio TOTVS já pertence à **api-delpi** |
| Backend de dados | Rotas dedicadas `/inspecoes-entrada/*` | Módulo qualidade/recebimento isolado |
| Persistência própria | **Não** (MVP) | Leitura direta das views |
| Permissões | Por filial + view ampla | Mesmo padrão `auditoria-5s`, `central-agendamento` |
| Referência de UI | `dashboard-production`, `cadastro-kaizen` | Tokens portal, KPI cards, tabelas |
| Referência de backend | `eficiencia_fabril`, `inspecoes_entrada_repository` | Repository TOTVS + use cases |

Fluxo:

```text
Portal → MFE inspecoes-entrada (/filial-01|02)
  → GET /apps/api-delpi/inspecoes-entrada/*
  → InspecoesEntradaRepository → views TOTVS + QER (detalhe)
```

---

## 3. Permissões

| Camada | Código | Observação |
|--------|--------|------------|
| Manifesto (Core API) | `inspecoes-entrada.view.filial-01` | Menu filial SC |
| Manifesto | `inspecoes-entrada.view.filial-02` | Menu filial ES |
| Manifesto | `inspecoes-entrada.view` | Ambas filiais |
| api-delpi | Mesmos códigos + `api-delpi.access` | Validação filial no router |

Registro: `POST /core-api/admin/apps/register` com `apps.manage` ou superadmin.

---

## 4. Fases de entrega

### Fase 0 — Especificação e validação TOTVS (pré-código) ✅

**Objetivo:** confirmar views e volume antes do repository.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Views documentadas | [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | ✅ |
| Script validação | `api-delpi/scripts/validate_inspecoes_entrada_views.py` | ✅ |
| Procedimento | [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md) | ✅ |
| Execução em dev/homolog | Rodar script no container `delpi-api-delpi` | ⏳ Por ambiente |

**Critério de pronto:** 5 views × 2 filiais retornam amostra sem erro SQL.

---

### Fase 1 — Backend api-delpi (MVP leitura) ✅

**Objetivo:** endpoints prontos para consumo pelo MFE.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Port + repository | `InspecoesEntradaRepositoryPort`, `InspecoesEntradaRepository` | ✅ |
| Use cases (7) | resumo, pendentes, fornecedor, rejeitadas×2, histórico, detalhe | ✅ |
| Router + RBAC filial | `inspecoes_entrada_router.py` | ✅ |
| Contratos meta | `route_contract_registry.py` + OpenAPI agent | ✅ |
| Testes | `tests/test_inspecoes_entrada_*` | ✅ |
| Composer | `inspecoes_entrada_composer.py` | ✅ |
| Registro `main.py` | Router incluído | ✅ |

**Critério de pronto:** pytest verde; smoke `meta.operationId` por rota.

---

### Fase 2 — MFE inspecoes-entrada (MVP UI) ✅

**Objetivo:** painel utilizável no Portal ou standalone dev.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Scaffold Vite + Federation | `remoteEntry.js`, bootstrap Portal | ✅ |
| Manifesto | `inspecoes-entrada.manifest.json` | ✅ |
| Dashboard | KPIs, fornecedor, rejeitadas, pendências | ✅ |
| Histórico | Filtros, paginação, modal detalhe | ✅ |
| Certificado | Impressão HTML via modal | ✅ |
| Docker dev | `delpi-inspecoes-entrada` no compose | ✅ |
| Design system | `dashboard-inspecoes-entrada`, prefixo `ie-` | ✅ |
| `npm run ci` | lint + build | ✅ |

**Critério de pronto:** build passa; smoke manual checklist [TESTING.md](../../../plugins/inspecoes-entrada/docs/TESTING.md).

---

### Fase 3 — Registro portal e homologação ⏳

**Objetivo:** plugin visível e validado em staging.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| `register-manifest.sh` em staging/prod | Core API | ⏳ |
| RBAC perfis qualidade | Filial 01/02 | ⏳ |
| Script homologação | `scripts/homologacao/check-inspecoes-entrada.sh` | ⏳ |
| Script CI build | `scripts/ci/build-inspecoes-entrada.sh` | ⏳ |
| Entrada em `docs/08-plugins/README.md` | Inventário | ✅ |
| Doc API pública | `api-delpi/docs/api/inspecoes-entrada.md` | ✅ |

**Critério de pronto:** menu Portal + smoke HTTP automatizado no CI.

---

### Fase 4 — Completude analítica ⏳

| Entrega | Detalhe | Status |
|---------|---------|--------|
| UI rejeitadas por ensaiador | Consumir `/rejeitadas-ensaiador` | ⏳ |
| Paginação pendências dashboard | Aviso ou paginação se > 200 | ⏳ |
| Export Excel histórico | Download CSV/XLSX | 📋 Backlog |
| Auto-refresh opcional | Intervalo configurável (como eficiencia-fabril) | 📋 Backlog |

---

### Fase 5 — Chat e indicadores estratégicos 📋

| Entrega | Detalhe |
|---------|---------|
| Registry operacional | `operational_route_registry.json` |
| Domínio rota | `api_route_domains.json` |
| Perfil apresentação | `presentation_profiles.json` |
| Casos regressão | `chat_intelligence_regression_cases.py` |
| Exposição SI (se aplicável) | KPIs agregados |

Seguir [new-api-route-checklist.mdc](../../../.cursor/rules/new-api-route-checklist.mdc) quando iniciar integração chat.

---

## 5. Fora de escopo (MVP)

- Cadastro ou alteração de laudos no Protheus
- Workflow de aprovação/rejeição pela plataforma
- NC automática a partir de rejeição
- Notificações push/e-mail de pendências

---

## 6. Referências

- Plugin README: [plugins/inspecoes-entrada/README.md](../../../plugins/inspecoes-entrada/README.md)
- Doc técnica: [plugins/inspecoes-entrada/docs/DOCUMENTACAO.md](../../../plugins/inspecoes-entrada/docs/DOCUMENTACAO.md)
- Guia qualidade DELPI: [documentos/guia_consolidado_de_desenvolvimento_aplicacao_de_qualidade_delpi.md](../../../documentos/guia_consolidado_de_desenvolvimento_aplicacao_de_qualidade_delpi.md)
