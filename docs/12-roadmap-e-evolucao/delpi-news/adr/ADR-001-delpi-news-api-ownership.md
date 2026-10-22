# ADR-001 — Ownership do motor DELPI News (`delpi-news-api`)

| Campo | Valor |
|---|---|
| Status | **PROPOSTO — aguarda aprovação formal** |
| Data | 2026-10-22 |
| Contexto | DELPI News — Etapa 2 (motor RSS / Atom) |
| Autoridade necessária | Product Master / Arquiteto da plataforma (processo vigente do monorepo) |
| Relacionados | [README](../README.md), [CONTRACTS](../CONTRACTS.md), [STAGE-02](../STAGE-02.md) |
| Estado factual | `ARCHITECTURE_DECISION_REQUIRED` — **este documento não é aprovação** |

---

## 1. Problema

A Etapa 2 exige um componente que:

- colete feeds RSS/Atom de forma segura (HTTPS, timeouts, anti-SSRF);
- normalize e deduplique itens;
- persista fontes, notícias e histórico de coleta;
- preserve estados editoriais (`collected` ≠ `published`);
- **não** publique automaticamente na TV / `public-hub`.

Não existe implementação de coleta RSS/Atom no monorepo (`EXISTING_EQUIVALENT = NO` — CONFIRMADO_NO_CODIGO no HEAD `f8e688bbc`).

A Etapa 1 propôs `delpi-news-api` como BC novo, mas registrou o estado como **PLANNED / TARGET**, não aprovado.

---

## 2. Evidências atuais

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION | Evidência |
|---|---|---|---|
| Coleta RSS/Atom | NO | NEW (se BC aprovado) | Sem `feedparser` / Atom syndication |
| HTTP externo resiliente | PARTIAL | EXTEND padrão no BC | `http-integration-resilience.mdc`, clients por domínio |
| SSRF / safe fetch | PARTIAL | NEW política no BC | Chat/TV/TM guards locais; sem safe-fetch universal |
| XML seguro | PARTIAL (BPMN/fiscal) | NEW parser de feed | `shared/bpmn_validation` (lxml hardenido) ≠ RSS |
| Scheduler | PARTIAL (poll in-process) | ADAPT no BC | Core notifications; pollers FastAPI |
| Persistência plugins PG | YES | REUSE | `postgres-plugins` + SQL `V00N__*.sql` |
| `external-data-api` | NO (para RSS) | **NÃO ESTENDER** | Mandato CNPJ/S2S cadastral; sem PG |
| TV Dashboard | NO (para RSS) | NÃO ESTENDER domínio | Owner de playlist/slides, não editorial de feed |

---

## 3. Alternativas

### Alternativa A — Novo BC `delpi-news-api` (recomendada se aprovada)

| Critério | Avaliação |
|---|---|
| Owner | Domínio editorial + ingestão RSS |
| Consumidores | Admin MFE (E3), `public-hub` board (E4+), opcional slide TV |
| Persistência | Schema `delpi_news` em `postgres-plugins` |
| Custo operacional | +1 container/API; alinhado a `supplies-api` / APIs departamentais |
| Acoplamento | Baixo — contrato HTTP explícito |
| Segurança | SSRF/XML no owner; RBAC Core; coleta não pública |
| Escalabilidade | Adequada a volume de feeds corporativos |

**REUSE_DECISION:** `NEW` (serviço) + `REUSE` (padrões PG/auth/compose).

### Alternativa B — Estender contexto existente

| Candidato | Por que descartar (alta confiança) |
|---|---|
| `external-data-api` | Mandato cadastral S2S/CNPJ; stateless; sem AuthZ de usuário; freeze X0 — mudança de mandato exigiria ADR próprio e revisão LGPD |
| `tv-dashboard-api` | Owner de apresentações/slides; misturar RSS editorial viola SRP e boundaries |
| `api-delpi` | SQL/TOTVS e módulos departamentais; não é owner natural de CMS de notícias externas |
| Core API | Governança de apps/RBAC — não domínio editorial |

**REUSE_DECISION:** `PENDING` rejeitado como caminho padrão → **não EXTEND** sem ADR de mudança de mandato.

### Alternativa C — Capacidade transversal + editorial “em outro lugar”

Um “fetcher genérico” em `shared/` ou worker central sem owner editorial:

- viola `platform-architecture-boundaries` (`shared/` sem regra de produto);
- deixa sem dono claro estados editoriais, auditoria e publicação;
- ainda exigiria um BC para persistência e RBAC.

**REUSE_DECISION:** `PENDING` descartada como owner; no máximo padrões técnicos reutilizáveis **dentro** do BC aprovado.

---

## 4. Decisão proposta (não vigente até aprovação)

1. Criar **`delpi-news-api/`** como bounded context dono de fontes RSS, itens normalizados, histórico de coleta e estados editoriais.
2. Stack alinhada às instruções oficiais: **Python + Flask**, Clean Architecture, envelope de resposta da plataforma.
3. Persistência: PostgreSQL `postgres-plugins`, schema dedicado (ex.: `delpi_news`), migrations SQL versionadas imutáveis.
4. Autorização: JWT → Core `/me` → permissions efetivas (`delpi-news.*`); coleta operacional **não** exposta publicamente.
5. `external-data-api` e `tv-dashboard-api` **não** absorvem RSS.
6. Contratos conceituais de `CONTRACTS.md` tornam-se schemas OpenAPI do BC após aprovação.
7. Agendamento: padrão in-process configurável; **não** ativar multi-réplica em produção sem lock/lease comprovado.
8. Etapa 2 **não** publica no `public-hub` nem altera a demo gated da Etapa 1.

### Framework

Precedência: instruções oficiais → Flask. APIs FastAPI irmãs são referência de composição, não de framework, salvo ADR superior futuro (mesmo racional de `supplies/adr/ADR-001`).

---

## 5. Consequências

### Se aprovado

- E2.S2+ podem iniciar scaffold, migrations e motor de coleta.
- Custo: novo serviço no compose, gateway path `/apps/delpi-news-api`, health/readiness, observabilidade.

### Se rejeitado / alternativa B autorizada

- Reescrever ownership no README e STAGE-02.
- Não criar `delpi-news-api/`.
- Documentar ADR de mandato do contexto escolhido.

### Se pendente (estado atual)

- **STOP** E2.S2/S3/S4.
- Nenhuma migration, gateway, Core register ou código de serviço.

---

## 6. Critérios de aceite da decisão

A autoridade competente deve registrar explicitamente:

```text
STATUS: APPROVED | REJECTED | DEFERRED
OWNER: <serviço/contexto>
DATE: <ISO>
AUTHORITY: <papel/pessoa>
NOTES: <restrições>
```

Sem esse registro em documento canônico no GitHub, o status permanece **PROPOSTO**.

---

## 7. O que este ADR NÃO autoriza

- Scaffold de `delpi-news-api`
- Migrations
- Alteração de gateway/Core/compose
- Cadastro de fontes em produção
- Publicação automática na TV
- Ampliação do mandato do `external-data-api`
