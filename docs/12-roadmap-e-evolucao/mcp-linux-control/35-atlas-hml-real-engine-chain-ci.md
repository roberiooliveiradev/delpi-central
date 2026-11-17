# ATLAS P2.2h.2ar-at | Teste completo com Docker Engine descartavel no CI

**Data:** 17/11/2026 (BRT). **Estado:** Draft PR e testes CI sujeitos a validacao no SHA da entrega. **Host DELPI:** inalterado. **PREPARE e ACT:** OFF.

## Objetivo e aceleracao

A PR #226 (mesclada) demonstrou a cadeia ATLAS/UDS/proxy/guard com Engine simulado. Este incremento substitui apenas a ultima dependencia simulada por **Docker Engine real do runner descartavel GitHub-hosted**, com um contêiner de teste rotulado como alvo HML. Nenhum socket, agente ou servico e instalado no `srv-api`.

## Mudancas entregues

- `linux-ops-mcp/tests/test_atlas_hml_real_engine_chain_ci.py`: suite **opt-in de CI**, desabilitada por padrao. Exige simultaneamente `GITHUB_ACTIONS=true`, `ATLAS_DISPOSABLE_DOCKER=true`, `ATLAS_REAL_HML_CHAIN_CI=true` e usuario nao-root. Usa socket AF_UNIX temporario, `serve_one_prebound`, `HMLDockerInspectOnly`, `HMLDockerGETTransport`, `DockerReadOnlyInspect` e `httpx.AsyncHTTPTransport` para consultar a API Docker da maquina **descartavel do GitHub**.
- `.github/workflows/atlas-p22e-integration.yml`: mantem o piloto `atlas-ci-pilot-hml` original e adiciona um **segundo contêiner descartavel de CI** com nome `delpi-hml-public-hub` e labels Compose `delpi-hml/public-hub` exigidas pelo guard. Os dois contêineres sao removidos no step `if: always()`, restrito ao runner hospedado pelo GitHub.
- O teste positivo exige que o read-back identifique contêiner real healthy/running e que somente **um GET do container allowlisted** chegue ao Engine.
- Os casos negativos enviam `POST`, `DELETE`, `GET /containers/json`, GET do Public Hub de producao e header Authorization; exigem rejeicao 400/404/405, **zero requests encaminhadas ao Engine**, erros sanitizados e estado BLOCKED. A falsificacao de UID do peer exige 403, sem request upstream.
- Todos os retornos de `SingleRequestProxyResult` permanecem com `prepare_eligible=false`, `can_execute=false`, `proxy_policy_independently_attested=false` e `host_identity_attested=false`.

## Limites de evidencias

A prova de ponta a ponta num runner descartavel **nao equivale** a atestacao independente de isolamento do `srv-api`. O processo de teste tem acesso ao socket Docker do runner GitHub para fazer uma unica inspeção; isso seria alto privilegio em qualquer host. Testes e classes Python nao impedem um processo comprometido com acesso ao socket Docker bruto de fazer outras operacoes. A validacao de host Linux, unidades systemd, policy MAC/LSM, ACLs, substituicao de binario, release OCI real, backup/restauracao, rollback e Core/Keycloak permanece exigida.

**Nao instalar** `delpi-hml-public-hub` em nenhum servidor com base neste teste. O nome de contêiner e somente uma fixture descartavel em um runner GitHub.

## Proxima decisao de arquitetura

Para o primeiro piloto HML operacional falta um **desenho de processo upstream revisado independentemente**: qual usuario detem o acesso ao Engine, como restringir ou isolar o processo de acesso elevado, como fornecer FD de socket UNIX root-owned ao proxy, o mecanismo de supervisao/limpeza e que evidencias de nao-bypass podem ser obtidas. O processo remoto da conta `atlas-hml` nao deve ter acesso direto ao socket Docker. Esta decisao nao deve ser escondida por mais testes unitarios.

## Checklist de aceite por evidencias

- [ ] 5 checks GitHub Actions (Linux MCP, Docker/Engine, PostgreSQL, arquitetura, auditoria) PASS **na HEAD da PR**
- [ ] `delpi-verifier` independente, com veredito anexado; se nao executado, registrar PENDENTE
- [ ] Revisao humana de seguranca de componentes privilegiados e do diferencial de CI
- [ ] Nenhuma alteracao em `srv-api`, HML real, producao, conta `atlas-hml`, grupos, systemd, Docker host, banco ou Keycloak
- [ ] PREPARE/ACT continuam desligados; nenhuma nova ferramenta MCP foi publicada
- [ ] A proxima atividade de host exige mudanca autorizada com plano de reversao

**Sem deploy real, sem habilitacao do proxy, sem promocao de artefatos OCI e sem merge automatico.**
