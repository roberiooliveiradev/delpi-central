# 11 — ADR: Backend do Planejamento Orçamentário

**Status:** Proposto (Fase 0)  
**Data:** 2026-08-04  
**Decisores:** Arquitetura Minha DELPI (pendente ratificação do time)

---

## Contexto

O Planejamento Orçamentário 2027 precisa de:

- CRUD colaborativo com workflow e auditoria;
- anexos e exportações;
- leituras TOTVS (ROL, CC, clientes, fornecedores);
- autorização funcional + escopo CC;
- MFE no portal com JWT Keycloak já existente;
- prazo de lançamento 01/10/2026.

Duas alternativas viáveis no monorepo:

1. **Domínio próprio na `api-delpi`** (módulos + rotas + migrations `postgres-plugins`).
2. **Serviço backend independente** `planejamento-orcamentario-api`.

---

## Alternativas

### A — Módulo na api-delpi + schema plugins

**Vantagens**

- Padrão dominante para CRUD+workflow+TOTVS (LNF, PAC, 5S, reports).
- Envelope OpenAPI, registry, permissões, SQL TOTVS e Postgres no **mesmo** processo — menos hops.
- Export openpyxl/reportlab já no pacote.
- Sem novo container Compose/Gateway/JWKS wiring.
- Runner de migrations de plugins já operacional (`run_plugins_migrations.py`).
- Observabilidade e Saúde SQL centralizadas.

**Desvantagens**

- api-delpi cresce em superfície de rotas.
- Ciclo de deploy acoplado a outros módulos api-delpi.
- Isolamento de falha menor (bug no módulo compartilha processo).

**Impactos**

| Área | Impacto |
|------|---------|
| Compose | Volume de upload + serviço já existente |
| Gateway | Nenhuma rota nova de host (só paths internos api-delpi) |
| JWT | Mesmo middleware `delpi_auth` |
| Banco | Schema novo em `postgres-plugins` |
| Deploy | Rebuild `api-delpi` + MFE sequencial |
| Testes | `api-delpi/tests` + gates OpenAPI |

### B — API dedicada

**Vantagens**

- Isolamento de lifecycle (como CIPA/CEC/TM/maintenance).
- Deploy independente se o domínio explodir (PDFs oficiais, assinaturas, jobs longos).
- Fronteira explícita: MFE → dedicada → api-delpi (TOTVS), padrão maintenance PLAYBOOK-01.

**Desvantagens**

- Duplicar bootstrap FastAPI, auth, CI, Compose, Gateway, health, logs.
- Todo acesso TOTVS vira **HTTP interno** extra (latência + contrato duplo).
- Mais tempo até MVP (conflita com 01/10/2026).
- Time precisa operar mais um serviço.

**Impactos**

| Área | Impacto |
|------|---------|
| Compose | Novo serviço + DB schema próprio ou Postgres compartilhado |
| Gateway | Novo `location /apps/planejamento-orcamentario-api/` |
| JWT | Replicar validação JWKS |
| Banco | Runner migrations próprio (checksum) |
| Deploy | Fase `api` adicional nos scripts sequenciais |
| Testes | Pacote de testes separado + contrato client api-delpi |

---

## Riscos

| Risco | A | B |
|-------|---|---|
| Estouro de prazo | Menor | Maior |
| Vazamento SQL TOTVS duplicado | Baixo (código local) | Médio se client frouxo |
| Monólito api-delpi | Médio longo prazo | Baixo |
| Operação (on-call) | Neutro | +1 serviço |

---

## Decisão recomendada

**Adotar Alternativa A:** domínio **Planejamento Orçamentário dentro da `api-delpi`**, com schema `planejamento_orcamentario` em `migrations/plugins/planejamento-orcamentario/`, MFE consumindo `/apps/api-delpi/planejamento-orcamentario/*`.

**Motivo decisivo:** aderência aos padrões reais do monorepo para processos colaborativos com ERP + menor custo operacional no prazo de 01/10/2026. Isolamento de processo **não** compensa a duplicação agora.

Organização de camadas: ver `02-arquitetura-proposta.md`.

---

## Condições que alterariam a decisão (para B)

1. Lifecycle de documentos oficiais com assinatura/PDF comparável a CIPA/CEC.
2. Jobs pesados contínuos (motor de consolidação/simulação) que degradem SLOs da api-delpi.
3. Time dedicado e mandato explícito de bounded context separado.
4. Proibição formal de novos módulos grandes na api-delpi (política futura).

Se migrar para B depois: extrair use cases mantendo SQL TOTVS **apenas** na api-delpi (client HTTP), nunca copiar queries.

---

## Consequências

- Implementação Fase 1 segue checklist `new-api-route-checklist` + `novo-plugin-mfe-checklist`.
- Chat/TV: opcional pós-MVP.
- Prod: migrations só `up` — nunca `reset`.
