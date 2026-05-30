# Auditoria 5S — plugin Minha DELPI

Aplicação operacional de auditoria 5S para a equipe de qualidade: avaliação colaborativa dos 5 sensos, cálculo de percentuais (escala Ruim/Médio/Bom/NA), registro de NCs e, em fase posterior, dashboards analíticos.

**Status (2026-05-28):** piloto em dev — Fases 1–5 + **dashboard gerencial (Fase 6 MVP)** implementados; validação manual pendente.

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ROADMAP.md](./ROADMAP.md) | **Roadmap completo** — fases, arquitetura, API, permissões e critérios de pronto |
| [CRITERIOS-CATALOGO.md](./CRITERIOS-CATALOGO.md) | **48 critérios** por senso (catálogo v1) |
| [REGRAS-NEGOCIO.md](./REGRAS-NEGOCIO.md) | Turnos, áreas, validação, fórmulas e status |

Documentos previstos nas próximas etapas:

| Documento | Conteúdo |
|-----------|----------|
| ESPECIFICACAO-PLUGIN.md | Telas, fluxos e regras de UI (Fase 0) |

---

## Referências no monorepo

| Peça | Caminho |
|------|---------|
| Plugin MFE | `plugins/auditoria-5s/` |
| Rotas operacionais API | `api-delpi/.../audit_5s_operational_router.py` |
| Repositório PG | `api-delpi/.../postgres_audit_5s_repository.py` |
| Rotas Qualidade (legado) | `api-delpi/app/interface/http/routes/quality/quality_router.py` |
| Legado analítico (Sheets) | `api-delpi/.../audit_5s_repository.py` |
| UI analítica legada | `plugins/dashboard-quality/src/pages/Audit5sPage.tsx` |
| Migrations quality | `api-delpi/migrations/plugins/quality/` (`V022`–`V025`) |
| Homologação | `scripts/homologacao/check-auditoria-5s.sh`, `check-audit-5s-api.sh` |
| Registro de plugin | [registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) |

---

## Identificação do plugin

| Campo | Valor |
|-------|--------|
| `id` | `auditoria-5s` |
| `basePath` | `/apps/auditoria-5s` |
| Rotas operacionais | `/apps/auditoria-5s/filial-01`, `/apps/auditoria-5s/filial-02` |
| Container Docker | `delpi-auditoria-5s` |
| Permissões Portal | `auditoria-5s.view.filial-01`, `auditoria-5s.view.filial-02` |
| Fonte de dados (MVP) | `postgres-plugins` — schema `quality`, tabelas `audit_5s_*` |

### Endpoints API (gateway) — operacional

| Método | Caminho | Uso |
|--------|---------|-----|
| `GET` | `/apps/api-delpi/quality/audit-5s/criteria` | Catálogo de critérios |
| `GET` | `/apps/api-delpi/quality/audit-5s/areas` | Áreas por filial |
| `POST` | `/apps/api-delpi/quality/audit-5s/areas` | Cadastrar área |
| `GET` | `/apps/api-delpi/quality/audit-5s/audits` | Listagem por filial |
| `POST` | `/apps/api-delpi/quality/audit-5s/audits` | Nova auditoria |
| `GET` | `/apps/api-delpi/quality/audit-5s/audits/{id}` | Detalhe + scores |
| `PUT` | `/apps/api-delpi/quality/audit-5s/audits/{id}/responses/{criterionId}` | Nota/observação |
| `POST` | `/apps/api-delpi/quality/audit-5s/audits/{id}/complete-evaluation` | Concluir avaliação |
| `GET` | `/apps/api-delpi/quality/audit-5s/audits/{id}/nc-candidates` | Critérios elegíveis NC |
| `POST` | `/apps/api-delpi/quality/audit-5s/audits/{id}/nonconformities` | Registrar NC |
| `PATCH` | `/apps/api-delpi/quality/audit-5s/nonconformities/{id}` | Atualizar plano da NC |
| `POST` | `/apps/api-delpi/quality/audit-5s/nonconformities/{id}/attachments` | Upload evidência (antes/depois) |
| `POST` | `/apps/api-delpi/quality/audit-5s/nonconformities/{id}/complete-action` | Finalizar ação com evidências |
| `POST` | `/apps/api-delpi/quality/audit-5s/nonconformities/{id}/actions` | Ação no histórico |
| `GET` | `/apps/api-delpi/quality/audit-5s/analytics/dashboard` | Dashboard gerencial (PG) |

Ver contrato completo em [ROADMAP.md](./ROADMAP.md#5-api-rest-contratos-alvo).

**Legado (mantido):** `GET /apps/api-delpi/quality/audit-5s/summary` — Google Sheets para dashboard analítico.

---

## Resumo do fluxo (UX atual)

1. **Lista** — hub principal; botões **Dashboard**, **Nova auditoria**, **Avaliar** e **Tratar NC**.
2. **Nova auditoria** — data, área, responsável, turno; código serial gerado (`01-000123`).
3. **Avaliação** — 5 sensos, critérios com Ruim/Médio/Bom/NA, observação; conclusão retorna à lista.
4. **NC** — tela dedicada; plano com auto-save; fotos antes/depois; finalização explícita.
5. **Dashboard gerencial** — filtros (período, área, turno, status); KPIs; gráficos de evolução; tabela de auditorias.
6. **Colaboração** — Socket.IO na avaliação e NC.
7. **Dashboards legado** — `dashboard-quality` ainda usa Google Sheets (migração futura).

Deploy típico após alterações:

```bash
cd infra

# Migrations (se houver novas — aguardar conclusão)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality

# Rebuild serviços (sempre a partir de infra/)
docker compose -f docker-compose.dev.yml up -d --build api-delpi auditoria-5s
docker restart delpi-gateway   # se mudou backend ou gateway desatualizado
```

Build do MFE (quando alterou só frontend):

```bash
cd plugins/auditoria-5s && npm run build
```

Homologação automatizada:

```bash
export TOKEN="<jwt>"
bash ./scripts/homologacao/check-auditoria-5s.sh   # Fase 1
bash ./scripts/homologacao/check-audit-5s-api.sh   # Fase 2
bash ./scripts/homologacao/check-audit-5s-dashboard.sh   # Fase 6
```
