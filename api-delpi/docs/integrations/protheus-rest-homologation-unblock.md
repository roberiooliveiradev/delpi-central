# Protheus REST — desbloqueio de homologação live

Documento operacional. Não contém segredos. Não substitui autorização do owner.

## Owners

| Responsabilidade | Owner canônico |
|---|---|
| Integração REST (código/contrato) | `api-delpi` |
| `PARAMETROS_MINHADELPI` / SQL Intranet | Owner ERP/Intranet (não a api-delpi) |
| Conta técnica Protheus (`USR_PROTHEUS`) | Owner ERP / segurança de integração |
| Keycloak identity + Core RBAC | Core / plataforma |
| Deploy / TLS / rede | Infraestrutura |

## Reuse

- `EXISTING_EQUIVALENT`: cliente REST, path resolver, token cache, status/supplier use cases já na `main`.
- `REUSE_DECISION`: não criar segundo client; corrigir parâmetros/transporte/RBAC no ownership correto.

## Checklist de desbloqueio (ordem)

1. **PATH_AUTH** — AMBIENTE 1 corrigido para `/api/oauth2/v1/token` (relativo a `URL_REST=…/rest`). AMBIENTE 2 permanece EMPTY até autorização própria.
2. **HTTP interno** — mantido por decisão do solicitante (risco residual). Não exige HTTPS nesta entrega.
3. **Rotação PSW** — owner rotaciona credencial exposta no PDF; atualiza só na tabela Intranet; **bloqueia** OAuth live até concluir.
4. **Manifest 1.0.1+** — `POST /core-api/admin/apps/register` com `api-delpi.manifest.json`; grant `api-delpi.integrations.protheus.read` ao usuário/grupo de homologação.
5. **Deploy** — `git pull` no SHA da `main` + `./infra/scripts/up-prod-sequential.sh --pull --build` (serviço `api-delpi`).
6. **Live autenticado** — somente após rotação confirmada: `GET /integrations/protheus/status` → supplier existente → inexistente → RBAC negado.

## SQL de referência (AMBIENTE 1 já aplicado)

```sql
UPDATE PARAMETROS_MINHADELPI
SET CONTEUDO = '/api/oauth2/v1/token'
WHERE PARAMETRO = 'PATH_AUTH'
  AND AMBIENTE = 1
  AND (CONTEUDO IS NULL OR LTRIM(RTRIM(CONTEUDO)) = '');
```

AMBIENTE 2: somente com autorização explícita do owner (mesmo valor relativo; não duplicar `/rest`).

## Grant RBAC (procedimento)

```text
1. Token admin com apps.manage + rbac.manage
2. POST /core-api/admin/apps/register  (body = api-delpi.manifest.json versão >= 1.0.1)
3. Associar api-delpi.integrations.protheus.read à role de homologação
4. Associar role ao usuário/grupo autorizado
5. Validar: usuário com grant → 200; usuário sem grant → 403 antes de chamar Protheus
```
