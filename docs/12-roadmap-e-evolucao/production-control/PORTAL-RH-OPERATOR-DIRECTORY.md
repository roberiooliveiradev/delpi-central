# Diretório de colaboradores — Production Control → Portal RH (C2)

Integração S2S que resolve a **matrícula** do operador na **identidade
oficial do colaborador**, de propriedade do Portal RH
(epi.Collaborator).

## Arquitetura

    ProductionRun / futuros serviços
            │
            ▼
    OperatorDirectoryService        (application)
            │ find_by_registration(registration: str)
            ▼
    OperatorDirectoryPort           (domain/ports — Protocol)
            │
            ▼
    PortalRhOperatorDirectoryGateway (infrastructure — httpx)
            │ GET  /api/v1/integrations/collaborators/{registration}/
            │ X-Delpi-Service-Token: <PORTAL_RH_API_SERVICE_TOKEN>
            │ Accept: application/json
            ▼
    Portal RH  →  epi.Collaborator

## Regras

- `registration` é **texto opaco**: apenas `strip()` externo; nunca
  `int()`, nunca `lstrip("0")`. "001" != "1". Máx. 30 chars.
- `active: false` é identidade válida (`OperatorIdentity(active=False)`).
  A regra "inativo não inicia sessão" pertence à **C3**.
- Campos extras do upstream são ignorados; `registration` retornada deve
  coincidir com a consultada.
- **Sem** acesso ao DB do Portal RH (`PORTAL_RH_DB_*` não é usado aqui),
  **sem** Protheus, **sem** cache, **sem** fallback para nome digitado.

## Erros de domínio

| Resposta Portal RH     | Erro                              |
|------------------------|-----------------------------------|
| 200 válido             | `OperatorIdentity`              |
| 200 fora do contrato   | `OperatorDirectoryContractError`|
| 401 / 403              | `OperatorDirectoryUnauthorized` |
| 404                    | `OperatorNotFound`              |
| timeout/rede/5xx/outro | `OperatorDirectoryUnavailable`  |
| config ausente         | `OperatorDirectoryUnavailable`  |

O token S2S nunca aparece em log nem em mensagem de erro.

## Configuração

| Env                            | Uso                                   |
|--------------------------------|---------------------------------------|
| `PORTAL_RH_API_URL`          | base URL do Portal RH (por ambiente)  |
| `PORTAL_RH_API_SERVICE_TOKEN`| credencial S2S dedicada (sem default) |
| `PORTAL_RH_API_TIMEOUT`      | timeout HTTP (default 5s)             |

Config ausente não impede o startup — a chamada ao diretório falha
explicitamente só quando invocada (integração ainda sem consumidor).

## Escopo C2

Composer expõe `build_operator_directory_service()` e o client é fechado
no shutdown do lifespan. **Cockpit, bench-session, public-hub, api-delpi e
o banco não foram alterados** — a substituição da identificação livre por
matrícula oficial é a C3.

## C3 — bench-session resolve identidade via Portal RH

`POST /public/machine-load/{token}/bench-sessions` agora exige a
**matrícula** e resolve a identidade oficial antes de persistir.

Contrato de entrada:

    {
      "branch": "02",
      "workCenter": "CT-123",
      "registration": "20057",   // canônico
      "website": ""              // honeypot preservado
    }

Compatibilidade temporária até a C4 (redesign do cockpit):

- `operatorCode`: **alias legado** da matrícula — aceito quando
  `registration` ausente; se ambos vierem **divergentes** → 422.
- `operatorName`: **ignorado** — o nome gravado é sempre
  `identity.full_name` do Portal RH. O browser não pode mais falsificar
  `operator_name`.

Persistência (sem migration): `operator_code = registration`,
`operator_name = full_name`. Resposta mantém `operatorCode` /
`operatorName` por compat.

Erros públicos: matrícula ausente/inválida/divergente → 422; inexistente →
404 "Matrícula não encontrada."; inativa → 403; diretório
indisponível/S2S/contrato inválido → 503 genérico (detalhe só em log).
Filial do colaborador ≠ filial do cockpit **não bloqueia** nesta etapa.

Resiliência: o Portal RH é necessário **somente para criar** sessão.
Sessões já válidas operam Play/Pause/Resume/Stop/classificação sem novo
lookup — não há dependência do RH por transição.
