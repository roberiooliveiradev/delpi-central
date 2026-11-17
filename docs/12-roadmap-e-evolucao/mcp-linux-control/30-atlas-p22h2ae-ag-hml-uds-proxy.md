# ATLAS P2.2h.2ae-ag | Proxy UNIX local limitado ao Docker GET do Public Hub HML

**Data:** 16/11/2026 (BRT). **Estado:** PR candidata. **HML/PROD:** nenhuma mudanca. **PREPARE/ACT:** OFF.

## Entrega agrupada de tres capacidades

A PR #220 criou uma CLI de inspecao segura, mas sem fonte Docker restrita. Nao e seguro expor docker.sock a MCP ou Portal TI: o socket bruto equivale a privilegio elevado no host. Esta etapa implementa um contrato executavel e uma prova de interoperabilidade, **sem instalar um servico**.

### AE. Identidade local e listener pre-provisionado

Arquivo linux-ops-mcp/linux_ops_mcp/atlas_hml_unix_proxy.py. Funcao serve_one_prebound recebe um socket UNIX ja vinculado por supervisor aprovado, no caminho fixo /run/atlas-hml-readonly/inspect.sock. NAO cria, escuta, remove, chmod ou chown sockets. Verifica que o FD e UNIX/SOCK_STREAM, o path bate com o bind, o diretorio e socket tem owner aprovado (root no desenho real), o diretorio nao permite group/world-write, socket nao e symlink/world-writable e nao e alias detectavel de docker.sock. Em seguida obtem UID real da conexao pelo SO_PEERCRED do kernel e exige o UID nao-root dedicado do futuro coletor HML.

**Limite:** kernel UID local nao atesta identidade do binario/processo, isolamento Docker, validade de canal mTLS nem confiabilidade do upstream. Credenciais SO e configuracao de host exigem aprovacao separada.

### AF. API GET unica, curta e sem dados sensiveis

Aceita somente HTTP/1.1, Host docker.local e GET /containers/delpi-hml-public-hub/json, sem corpo e com header total limitado a 2048 bytes. Rejeita caminhos diferentes, query, POST/DELETE/PUT/HEAD/OPTIONS, Host duplicado, Authorization, Content-Length, Transfer-Encoding, Expect, Upgrade e pipelining detectado. Cada chamada atende **uma conexao** e faz no maximo uma leitura upstream por um inspector injetado, que futuramente deve ser DockerReadOnlyInspect ja existente e allowlisted.

Nao encaminha o corpo Docker bruto: retorna SOMENTE Id, Image, Name, labels Compose service/project e status Running/Health. Docker Config.Env, mounts, volumes, network settings e outros metadados nunca atravessam a fronteira. Erros de request, peer e upstream recebem resposta fixa sem stack trace ou log de secrets. O SingleRequestProxyResult permanece status=blocked, prepare_eligible=False, can_execute=False, mesmo em HTTP 200.

### AG. E2E sobre UNIX socket real em CI

Arquivo linux-ops-mcp/tests/test_atlas_hml_unix_proxy.py: usa socket AF_UNIX criado somente dentro de pytest tmp_path, httpx.AsyncHTTPTransport UDS real entre cliente e proxy, e DockerReadOnlyInspect com httpx.MockTransport upstream. Confere conteudo filtrado, nega usuario sem UID allowlisted, path ou metodo mutante, header indevido, payload grande, request duplicada, arquivo/diretorio inseguro, symlink, alias raw e upstream malformado. O workflow ATLAS inclui o teste, o workflow Linux MCP executa todos os testes por padrao.

Nao utiliza nenhum docker.sock real, identidade de maquina Keycloak, credenciais, host DELPI, migration, role, Core grant, journal write ou Docker POST no CI.

## Desenho operacional, ainda nao implementado

Futuro coletor HML (UID exclusivo, sem grupo docker/sudo, checkout nao gravavel) comunica localmente ao proxy UNIX por SO_PEERCRED. O proxy, isolado do MCP e Portal TI, consultara um upstream Docker restringido ao GET do container HML e devolvera apenas dados minimos. O processo upstream tem poder elevado sobre o host e deve ser protegido por supervisor, isolamento e threat model aprovados: o codigo fonte sozinho **nao prova que o backend e GET-only**.

Etapas futuras, somente com owner approval:
1. Owner Linux e Seguranca aprovam isolamento de processo, supervisor e acesso Docker estritamente limitado.
2. A conta coletora e o socket de entrada root-owned sao provisionados em HML por mudanca separada, nunca por este merge; sem sudo, grupo docker, token de deploy ou Docker raw socket no coletor.
3. Testes reais negativos sob HML devem impedir POST/exec/listagem e qualquer consulta a outro container; conferir ausencia de Env e secrets na resposta e logs.
4. Integrar a CLI de preflight da PR #220 ao emissor de receipts assinado e ao canal autentico S2S, com Core humano e journal reais autorizados. Backup/restauracao, rollback e migrations exigem prova independente.
5. PREPARE e ACT so podem ser considerados mediante change control, writer nonce one-shot e autorizacao humana fresca separada.

## Gates

- [ ] CI Linux MCP + ATLAS + auditoria + arquitetura aprovado
- [ ] Veredito independente delpi-verifier e code review humano de seguranca
- [ ] Confirmacao de que nenhum daemon/socket/supervisor/proxy foi instalado ou ligado
- [ ] Aprovacao de ownership, isolamento, least privilege e teste HML antes de operar

**Resultado:** modulo source-only testavel em socket UNIX efemero, NAO instalado em HML/PROD e NAO elegivel para deploy.


## Complemento de hardening P2.2h.2ai-ak (PR Draft, 16/11/2026)

A politica de owner/group/mode do socket e do diretorio foi centralizada para o proxy e o preflight; o listener deve estar em escuta, e o UID admitido pela conta nominal `atlas-hml`. O socket real exige owner root, group `atlas-hml` e modo exato 0660; o diretorio nao admite escrita por grupo nem acesso de outros e precisa permitir travessia pelo grupo. O projeto inclui deadline de upstream e testes negativos. Estes requisitos **nao** significam instalacao no host nem atestacao independente. Conferir [runbook atualizado](./32-atlas-hml-uds-policy-hardening.md) antes de qualquer proposta de ativacao.
