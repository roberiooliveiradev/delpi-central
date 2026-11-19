# ATLAS — Monitoramento multisservidor (READ-ONLY)

**Atualizado:** 2026-11-19  
**Escopo:** somente leitura, analise e diagnostico. Sem PREPARE/ACT, SSH, shell, Docker socket ou escrita.

## Arquitetura

```text
ChatGPT / MCP OAuth (humano)
  → linux-ops-mcp (projecao sanitizada + diagnostico conservador)
    → it-portal-api (inventario + observacoes + host-services)
      → coletores linux_host_collector / windows_host_collector
```

O Portal de TI continua sendo a unica fonte de inventario e observacoes. Novos servidores cadastrados passam a aparecer automaticamente em `list_servers` / `get_infrastructure_health` sem alterar configuracao do MCP, desde que o usuario autenticado tenha `it-portal.access` + `it-portal.servers.view` e a coleta esteja operacional para aquele host.

## Tools

| Tool | Entrada principal | Fonte |
|---|---|---|
| `list_servers` | filtros + paginacao | `GET /servers`. Filtros client-side (`os_family`, `administrative_status`) varrem o inventario completo em paginas upstream menores (25) para caber em `MAX_UPSTREAM_BYTES` mesmo com `description` de ate 4000 chars, e devolvem `total` real; nao aplicam o teto `LINUX_OPS_INFRA_MAX_SERVERS`. |
| `get_server_health` | `server_id` ou `hostname` | inventario + `GET /servers/{id}/observations/latest` |
| `get_infrastructure_health` | filtros de escopo + paginacao | inventario + latest por servidor (concorrente). Aqui o teto `LINUX_OPS_INFRA_MAX_SERVERS` (default 500) limita o consolidado. |
| `get_server_services` | servidor + filtros | Windows: `/host-services` (+ opcional dashboard); Linux: systemd allowlist da observacao. Com `critical_only`, a filtragem ocorre sobre o inventario varrido (limite seguro) **antes** da paginacao local. Identificadores Windows seguem o contrato IT Portal (key/name 200, display_name/`service_name` 240). |

As quatro tools legadas (`get_host_health`, `list_managed_services`, `get_service_health`, `get_deployment_revision`) permanecem e continuam ancoradas em `LINUX_OPS_SERVER_ID` com contrato Linux-only.

## Diagnostico

Separacao obrigatoria:

- `collection_status`: `available` | `partial` | `stale` | `unavailable` | `failed_read`
- `health_status`: `healthy` | `attention` | `critical` | `unknown`
- `overall_status`: sintetiza coleta + saude sem confundir ausencia de coleta com host offline

Regras conservadoras (defaults):

- memoria/disco/CPU: atencao >= 85%, critico >= 95% (CPU so quando a metrica existe)
- metrica ausente **nunca** e tratada como 0%
- observacao parcial saudavel nos indicadores presentes => `overall_status=partial`
- observacao stale nao prova host online
- servico Linux inativo/failed na allowlist => atencao/critico
- servico Windows favorito/critico parado => atencao via inventario oficial

## Exemplos

```text
ATLAS, liste todos os servidores cadastrados no Portal de TI.
ATLAS, analise a saude do SRV-PROTHEUS02 e identifique possiveis problemas.
ATLAS, faca uma analise geral da saude de todos os servidores da Delpi.
ATLAS, quais servicos estao parados no SRV-DB01?
```

## Autenticacao e autorizacao

1. OAuth/Keycloak humano no transporte MCP.
2. Revalidacao Core `force_refresh=True` a cada chamada.
3. Permissoes obrigatorias: `it-portal.access`, `it-portal.servers.view`.
4. IT Portal revalida RBAC independentemente.
5. Fail-closed; erros sem body/token/stack.

## Testes

- `tests/test_reader.py` — regressao das projecoes legadas
- `tests/test_multiserver.py` — inventario, paginacao >25, Linux/Windows, hostname ambiguo, stale/partial, falha isolada, auth negada, ausencia de write/shell
- `tests/test_authz.py` / `tests/test_oauth_contract.py` — RBAC e discovery OAuth
- CI: `.github/workflows/linux-ops-mcp-readonly.yml` (inventario de 8 tools)

## Limitacoes conhecidas

- Sem endpoint agregado no IT Portal nesta entrega: o consolidado faz N leituras `latest` com concorrencia limitada e limita o escopo a `LINUX_OPS_INFRA_MAX_SERVERS`.
- `list_servers` com filtros client-side pode varrer varias paginas upstream para calcular o total; a paginacao devolvida permanece correta.
- Linux services continuam limitados a allowlist da observacao (nao e inventorio SCM completo).
- `get_deployment_revision` permanece `not_available` sem fonte atestada.
- Tools legadas ainda exigem `LINUX_OPS_SERVER_ID` e rejeitam observacao Windows.

## Implantacao / rollback (apos merge; nao executar nesta PR)

1. Rebuild/restart apenas do servico `linux-ops-mcp` (profile `linux-ops`) apos merge.
2. Nenhuma migration.
3. Nenhuma mudanca de Keycloak/Core permissions alem das ja exigidas pelo Portal de TI.
4. Rollback: reverter o deploy da imagem MCP para o SHA anterior; inventario/API do Portal nao sao alterados por esta evolucao.

## Proximas evolucoes recomendadas

- Endpoint de leitura agregada no IT Portal (quando o inventario crescer).
- Filtro nativo `operating_system` / `administrative_status` no `GET /servers`.
- Expansao controlada da allowlist systemd via contrato do coletor (nao via shell).
- Surface ChatGPT smoke multisservidor com evidencia sanitizada.
