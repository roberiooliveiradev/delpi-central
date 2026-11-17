# ATLAS P2.2h.2ao-aq | Cadeia HML integrada, sem ativacao no host

**Data:** 17/11/2026 (BRT). **Entrega:** Draft PR. **Runtime HML/PROD:** nao alterado. **PREPARE/ACT:** OFF.

## Objetivo de aceleracao

Em vez de acumular mais contratos isolados, exercitar a fronteira completa
**leitor ATLAS -> UDS -> proxy -> guard Docker -> RuntimeContainer** sob testes
descartaveis. O deploy real e um marco diferente e ainda exige isolamento
independente do processo que pode acessar o Docker Engine.

## Mudancas em codigo

1. **Assembly fail-closed do proxy:** `atlas_hml_unix_proxy.py` reutiliza o
   `HML_TARGET` canonico de `atlas_hml_engine_boundary.py` e, quando o
   `expected_path` coincide com o socket HML fixo, exige que o inspector
   seja **exatamente** `HMLDockerInspectOnly`. A conta `atlas-hml` continua
   sendo resolvida via NSS e autenticada pelo UID local recebido do kernel.
   Inputs de DI para socket temporario preservam os testes, mas nao sao
   superficies publicas de CLI, MCP ou HTTP. Este gate de tipo em Python
   **nao prova isolamento do supervisor** nem impede codigo privilegiado de
   acessar Docker por fora da classe.
2. **Teste de cadeia com AF_UNIX real:** `test_atlas_hml_boundary_chain.py`
   cria somente sockets no `pytest tmp_path`, usa o handler de producao,
   `HMLDockerInspectOnly`, `DockerReadOnlyInspect`, `httpx.AsyncHTTPTransport(uds)`
   e `httpx.MockTransport` com JSON Docker sintetico.
3. **Casos negativos ligados entre si:** UID diferente = 403 sem upstream;
   metodos POST/DELETE, listagem de containers, contêiner PROD, cabecalho
   Authorization = recusados antes do upstream; Compose labels, status Docker
   inesperado e ImageID invalido = 502 sanitizado, sem Env/Mounts/Network.
   A mesma cadeia alimenta `inspect_hml_local` e permanece
   `status=blocked`, `prepare_eligible=false` e `can_execute=false`.
4. **CI:** `atlas-p22e-integration.yml` inclui o novo arquivo em paths e
   nos testes que acompanham o Docker descartavel de CI. A suite completa
   `linux-ops-mcp-readonly.yml` o captura pelo glob da pasta.

## O que esse teste demonstra (e o que nao demonstra)

| Evidencia | Demonstrada neste pacote? |
|---|---|
| Fluxo UDS real efemero com credenciais SO do kernel | Sim, no runner CI nao-root |
| Filtragem upstream para o GET exato e alvo HML | Sim, com Engine simulado |
| Rejeicao de UID, metodo, alvo e Docker JSON indevidos | Sim, nos testes |
| Sanitizacao e estado BLOCKED no diagnostico | Sim, nos testes |
| Instalacao ou ativacao de proxy no srv-api | Nao |
| Confinamento independente de processo privilegiado no Linux | Nao |
| Exposicao exclusiva do socket root-owned 0660 ao atlas-hml real | Nao |
| Prova de checkout, build OCI assinado ou artefato implantado | Nao |
| Aprovacao Core, challenge consumido, backup/restore/rollback | Nao |
| PREPARE ou ACT operacional | Nao |

## Roteiro de aceite HML (somente apos autorizacao formal)

A seguir esta a **lista de evidencias exigidas**, nao comandos de instalacao.

- **Dono do processo upstream:** nome do responsavel e revisao de threat model
  cobrindo Docker daemon, processo privilegiado, namespaces, capabilities,
  sudo, grupos, MAC e quem pode alterar o binario e a configuracao.
- **Isolamento:** demonstrar de forma independente que a conta `atlas-hml`
  nao acessa nenhum socket Docker bruto; que o upstream tem somente a
  capacidade estritamente necessaria e nao um caminho alternativo de
  execucao administrativa.
- **Socket UNIX:** validar caminho fixo, owner root, grupo atlas-hml, modo 0660,
  diretorio root-owned sem escrita de grupo, e grupos suplementares reais.
  Um `stat()` sozinho nao cobre ACLs, LSM, namespaces ou troca de processo.
- **Protocolos:** GET allowlisted deve retornar somente campos de identidade,
  ImageID e Running/Health. Em ensaios negativos separados, tentar POST,
  listagem, `/exec`, query, Host incorreto, UID nao aprovado e contêiner
  `delpi-public-hub`; todos precisam negar sem atingir Docker Engine.
- **Observabilidade:** log somente com codigos finitos, sem variaveis Env,
  credentials, Docker payload, tracebacks, headers de autenticacao, nem
  dados sensiveis do host.
- **Rollback da ativacao:** plano de parar/desabilitar *somente* os componentes
  novos e retirar o socket dedicado, sem parar Docker ou outros containers.
  Definir janela, ownership, verificacao de reversao e resposta a incidentes.
- **MCP:** permanece com 4 ferramentas READ; `get_deployment_revision`
  continua sem inventar revisao do checkout; PREPARE/ACT continuam OFF.

## Proximo pacote apos revisao desta PR

Definir um pacote de revisao e confinamento operacional do upstream, incluindo
prova de acesso minimo e aceite de Seguranca. **Nao** se deve instalar
unit/socket/daemon ou conceder grupo docker ao coletor sem aprovacao separada.
Esse trabalho pode caminhar em paralelo com o desenho do backend de PREPARE,
mas **nao habilitar** propostas ou executores por inferencia de CI.

## Gates

- [ ] CI da HEAD desta PR: Linux MCP, Docker CI, PostgreSQL CI, arquitetura e auditoria
- [ ] `delpi-verifier` externo executado por revisor independente
- [ ] Review humano de seguranca para o diff e para o processo upstream futuro
- [ ] Confirmacao sem alteracao em host, Keycloak, DB, Docker, sockets e infraestrutura
- [ ] Nenhum merge automatico
