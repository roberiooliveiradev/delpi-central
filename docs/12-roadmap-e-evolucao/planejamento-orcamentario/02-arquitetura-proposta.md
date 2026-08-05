# 02 — Arquitetura proposta

## 1. Visão geral

```text
Portal (Keycloak + AppHost)
  └─ MFE planejamento-orcamentario  (/apps/planejamento-orcamentario)
       └─ JWT + X-Delpi-Caller-App
            └─ Gateway
                 └─ api-delpi  /planejamento-orcamentario/*   (domínio + envelope)
                        ├─ Postgres plugins (schema planejamento_orcamentario)
                        ├─ volumes anexos (carta/docs/export)
                        └─ leituras TOTVS (reuso /financial/rol, view CC, SA1/SA2…)
```

**Recomendação de backend:** módulo de domínio na **api-delpi** + schema em `postgres-plugins`.  
Justificativa completa: `11-adr-backend.md`.

---

## 2. Pacotes e fronteiras

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** | UI, estado local, debounce de autosave, render-only de permissões (UX); **nunca** fonte final de autorização |
| **api-delpi** | Use cases, validação, RBAC + escopo CC, workflow, auditoria, export, SQL TOTVS |
| **core-api** | Registro de app/manifesto, permissões funcionais, `me/apps` |
| **Gateway** | Rota `/apps/api-delpi/` e assets do MFE (padrão existente; entradas novas só na implementação) |
| **Keycloak** | Identidade (sem lista completa de permissões no JWT) |

---

## 3. Organização proposta na api-delpi

```text
api-delpi/app/
  domain/planejamento_orcamentario/
  application/use_cases/planejamento_orcamentario/
  application/security/          # constantes em api_delpi_permissions.py
  infrastructure/persistence/plugins/planejamento_orcamentario/
  infrastructure/persistence/totvs/…
  infrastructure/pdf|excel/…
  interface/http/routes/planejamento_orcamentario/
migrations/plugins/planejamento-orcamentario/V00N__….sql
```

Camadas alinhadas ao código atual (`interface/` singular).

---

## 4. Microfrontend

Seguir `docs/05-plugin-system/novo-plugin-mfe-checklist.md`:

- Scaffold: `controle-retrabalhos` ou `quality-action-plans`
- Federation `@delpi/plugin-ui` + `preparePluginUiRemote`
- `httpClient` com `X-Delpi-Caller-App`
- Estrutura `ui` / `state` / `data` / `features/*` — ver `08-mapa-de-telas.md`

---

## 5. Plugins de referência

| Referência | Padrão a reutilizar | Limitações / não copiar | Aderência |
|------------|---------------------|-------------------------|-----------|
| **quality-action-plans** | Revisões, snapshot, approve/reject, anexos, Excel/PDF | Domínio qualidade; não copiar telas 8D | Alta |
| **lancamento-notas-fiscais** | Workflow + migrations plugins + RBAC filial | Conciliação SF1 específica | Alta |
| **central-agendamento** | Status pending/rejected + `.approve.filial-*` | Domínio agenda; sem grade orçamentária | Média-alta |
| **financeiro-centro-custo** | View CC / conta / fornecedor | Read-only; sem workflow | Média (ERP) |
| **reports** | Schema plugins + exports | Foco e-mail/agenda | Média |
| **cipa / CEC (*-api)** | PDF oficial / assinatura | Custo operacional alto | Baixa no MVP |
| **propostas-comerciais** | ReportLab PDF | Read-only TOTVS | Baixa-média |

**Não copiar:** protótipo PHP Desktop; Bootstrap ad hoc; autorização só no front; `COPY plugin-ui`.

---

## 6. Persistência

| Dado | Onde |
|------|------|
| Exercício, linhas, workflow, auditoria, escopos | Postgres `planejamento_orcamentario` |
| Anexos / exports | Volume `${DELPI_DATA_HOST_DIR}/planejamento-orcamentario` |
| ROL, CC, clientes, fornecedores | TOTVS leitura via api-delpi |
| Permissões funcionais | Core API |
| Usuário↔CC | Tabela de domínio do plugin (proposta) |

---

## 7. Autosave, auditoria, export

Detalhes: seções nos docs `03`–`07` e roadmap. Resumo:

- Autosave com debounce + versão otimista (padrão PAC revisions)
- Auditoria de eventos + snapshot em aprovação
- Excel síncrono para escopos pequenos; assíncrono se volume alto
- PDF executivo síncrono no MVP se payload limitado

---

## 8. Fora do desenho (MVP)

- Escrita no Protheus
- API dedicada (salvo gatilhos do ADR)
- Integração chat como canal principal de preenchimento
