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

1. **PATH_AUTH** — owner aprova UPDATE por `AMBIENTE` para `/rest/api/oauth2/v1/token` (evidência: POST sem username → 400 `invalid_grant`).
2. **SECURE_TRANSPORT** — owner de infra publica HTTPS válido até o REST (ou VPN/proxy com decisão explícita). Sem isso: não enviar password grant real.
3. **Rotação PSW** — owner rotaciona credencial exposta no PDF; atualiza só na tabela Intranet; valida sem logar senha.
4. **Manifest 1.0.1+** — `POST /core-api/admin/apps/register` com `api-delpi.manifest.json`; grant `api-delpi.integrations.protheus.read` ao usuário/grupo de homologação.
5. **Deploy** — `git pull` no SHA da `main` + `./infra/scripts/up-prod-sequential.sh --pull --build` (serviço `api-delpi`).
6. **Live** — `GET /integrations/protheus/status` → supplier existente → inexistente → RBAC negado.

## SQL preparado (não executar sem aprovação)

Ver `protheus-rest-read.md` seção Homologação. Um `AMBIENTE` por vez; backup SELECT antes; releitura depois.

## Grant RBAC (procedimento)

```text
1. Token admin com apps.manage + rbac.manage
2. POST /core-api/admin/apps/register  (body = api-delpi.manifest.json versão >= 1.0.1)
3. Associar api-delpi.integrations.protheus.read à role de homologação
4. Associar role ao usuário/grupo autorizado
5. Validar: usuário com grant → 200; usuário sem grant → 403 antes de chamar Protheus
```
