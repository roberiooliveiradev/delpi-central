# ATLAS HML | Ensaio real em CI descartável de UID, DAC e FDs Docker herdados

**Data:** 17/11/2026 (BRT) | **Status:** EXPERIMENTO DE SEGURANÇA EM RUNNER DESCARTÁVEL, NÃO ATESTAÇÃO DE HOST | **Issue:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232)  
**Roadmap:** etapa 53 | **Referências:** [runbook 42](./42-atlas-hml-supervisor-blueprint-review.md), [runbook 43](./43-atlas-hml-independent-security-decision-gate.md).

## Contexto e resultado que queremos comprovar

A questão crítica da arquitetura B é separar o processo que conversa com o Docker Engine (host-equivalente) do processo `atlas-hml` que lê um snapshot e atende o cliente. O `AGENTS.md`, a issue #232 e o runbook 43 exigem parecer independente e autorização operacional separada; nenhuma aprovação foi encontrada na issue ao iniciar esta entrega.

As verificações puramente lexicais da PR #240 ainda não demonstravam um fato importante em um sistema operacional real: **um UID sem permissão DAC no caminho `/var/run/docker.sock` pode continuar conversando com o Engine se herdou um socket já conectado do processo privilegiado**. Também não testavam a separação de permissões reais root/grupo em um diretório temporário.

Este pacote não cria um novo inspector, presenter, serviço ou instalador. Acrescenta uma reprodução negativa do risco usando exclusivamente o **Docker Engine de uma GitHub Actions runner descartável** e o contêiner fixture criado pelo workflow existente.

## O que o teste executa

Arquivo: `linux-ops-mcp/tests/test_atlas_hml_os_boundary_real_ci.py`. Integração: `.github/workflows/atlas-p22e-integration.yml`, job `disposable-docker`.

O job atual já inicializa uma fixture local `delpi-hml-public-hub` em contêiner Alpine temporário. Após os testes existentes, executa o novo teste com `sudo -n` **somente dentro do runner do GitHub**, usando a mesma instalação Python. O teste recusa execução se as três flags de CI descartável não estiverem presentes, se não estiver sob root, se o caminho não for socket UNIX, se a identidade `nobody` for privilegiada ou se o socket estiver acessível por outros.

| ID | Ensaio no runner descartável | Resultado esperado |
|---|---|---|
| **CI-OS-01** | Child root faz drop de grupos suplementares, GID e UID para `nobody`, tenta abrir conexão nova para o socket Docker | **DAC_DENIED** (EACCES/EPERM). Se conectar, FAIL |
| **CI-OS-02** | Parent conecta ao Docker antes de criar child; child derruba grupos/UID/GID e realiza **apenas GET /_ping** pelo mesmo FD já conectado | **INHERITED_FD_STILL_WORKS**. Este PASS é um **alerta de vulnerabilidade de design por herança**, não um sinal verde para usar esse FD no presenter |
| **CI-OS-03** | Em diretório temporário `root:nobody 0750` e arquivo `root:nobody 0640`, child `nobody` usa o leitor candidato por FD, tenta sobrescrever o JSON, criar arquivo no diretório e ler arquivo `root:root 0600` | Leitura da claim HML **BLOCKED** sem atestações; tentativas de escrita/leitura não autorizadas negadas |

Os probes nunca imprimem resposta Docker, dados do snapshot ou informações internas: só retornam códigos finitos. O experimento só utiliza `GET /_ping` e I/O em diretório temporário da runner, sem `POST`, `DELETE`, alterações em contêineres, API/Keycloak, banco, serviços ou infraestrutura DELPI. O workflow remove suas duas fixtures Docker descartáveis mesmo se falhar.

## Controles e limites da prova

- A precondição `GITHUB_ACTIONS=true` + `ATLAS_DISPOSABLE_DOCKER=true` + `ATLAS_REAL_HML_CHAIN_CI=true` **não é uma autorização criptográfica**; apenas restringe o disparo da suíte. O workflow GitHub é a fronteira relevante. Não executar o teste no `srv-api` ou copiar o comando `sudo` para a empresa.
- O child abandona grupos, GID e UID **no runner**, não em `atlas-hml` no host; isso não comprova ACLs, LSM/MAC, file descriptors, namespaces, seccomp ou política systemd real do host.
- O caso CI-OS-02 propositalmente mostra que uma conexão aberta **sobrevive à perda de UID e da permissão DAC de caminho**; um presenter com socket Docker pré-conectado **não estaria isolado**. `RestrictAddressFamilies` ou `NoNewPrivileges` não revogam automaticamente essa conexão.
- O caso CI-OS-03 comprova permissões POSIX do snapshot **no runner**, com `nobody` simulando grupo leitor; não comprova root autêntico, origem do produtor, ausência de replay, troca atômica ou identidade do `atlas-hml`.
- `PASS` em CI-OS-01..03 **não encerra SEC-01..SEC-10**. Parecer humano Linux/Segurança e `delpi-verifier` seguem pendentes, mesmo que CI esteja verde. Falhas indicam drift do runner ou risco a revisar, não autorização para flexibilizar checks.

## Critérios para leitura dos resultados

**Falha CI-OS-01**: o usuário desprivilegiado conseguiu abrir Docker; conferir grupos, socket permissions, mounts, ACLs e runner antes de confiar no modelo.  
**Sucesso CI-OS-02**: indica que a fronteira precisa garantir **zero FDs de Docker herdados**, além de negar o caminho.  
**Falha CI-OS-02**: investigar regressão da reprodução e estado do Engine, **não** concluir que herança de FDs é segura por uma falha incidental.  
**Falha CI-OS-03**: investigar DAC e leitor FD, sem relaxar ownership/mode para obter PASS.

## Próximos passos após CI

1. Enviar link desta evidência e logs dos checks para **revisor Linux/Segurança independente**, registrando os limites na issue #232.
2. Obter decisão nominativa A/B/C com justificativa dos riscos residuais e parecer do `delpi-verifier`; não há delegação de aprovação ao próprio código.
3. Apenas com decisão favorável e revisão do futuro código executável, preparar PR operacional separada do presenter sem Docker e produtor one-shot, sem ativação e sem alteração no `srv-api`.
4. Posteriormente, com autorização operacional específica, testar isolamento real de ACL, FD, aliases e rollback no host HML, não em produção.

**Conclusão:** os testes são uma evidência reproduzível **sobre um runner descartável** e uma demonstração de por que a arquitetura ainda requer revisão independente. O ATLAS mantém **4 ferramentas MCP READ**, `status=blocked`, PREPARE/ACT OFF e avanço global **mantido em 52%** até a dependência operacional ser resolvida.
