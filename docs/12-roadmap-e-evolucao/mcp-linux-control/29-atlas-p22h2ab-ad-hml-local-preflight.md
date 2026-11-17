# ATLAS | P2.2h.2ab-ad | Preflight local real do coletor HML sem privilégios

**Data:** 16/11/2026 | **Estado:** PR candidata a revisão | **PROD/HML:** sem mudanças

## Avanço em uma entrega, com três partes vinculadas

As PRs #209-#219 criaram os contratos criptográficos, Core humano, leitor OCI/GHCR, journal e diagnóstico HML. Ainda faltam identidade operacional do coletor e uma forma segura de conhecer a condição do próprio Linux. A etapa ab-ad entrega um preflight **realmente executável e somente leitura**, sem criar daemon, servidor, socket, cliente Keycloak ou API. A ferramenta pode ser invocada manualmente num checkout existente, com saída JSON para orientar a futura configuração HML.

1. **AB: inspeção de privilégios OS.** Lê UID/EUID e grupos UNIX do processo e mede se a conta pode alterar o checkout fixado em /home/operador/projetos/delpi-central. Se root/setuid ou grupo root/docker/sudo/wheel/lxd/podman ou checkout gravável, recusa toda leitura Git/Docker. Grupo e UID no relatório não são expostos. A verificação é uma observação momentânea e não comprova MAC, ACL completa, namespaces, capacidades Linux ou identidade de processo remota.
2. **AC: leitura real e restrita.** Reutiliza GitCheckoutReadOnlyObserver, que executa apenas rev-parse/symbolic-ref/status Git, em caminho fixado, sem lock opcional. Se um proxy UNIX GET-only para Docker estiver previamente instalado e independentemente revisado, usa DockerReadOnlyInspect para requisitar APENAS GET /containers/delpi-hml-public-hub/json, validando label do serviço public-hub e projeto delpi-hml e reportando image ID/saúde. O endereço é /run/atlas-hml-readonly/inspect.sock, imutável; não aceita URL ou path do CLI, HTTP, MCP ou variáveis de ambiente. Checa socket real (não symlink), pasta sem world-write, socket sem world-write e rejeita quando o inode equivale a /run/docker.sock ou /var/run/docker.sock. NÃO instala nem confia automaticamente na política do proxy: um socket com nome próprio pode ocultar Docker irrestrito. Essa prova requer revisão independente.
3. **AD: CLI JSON + testes.** Invocação única e explícita, sem flags de bypass, sem tokens/chaves/nonce, execução de deploy, gravação de banco, operação Docker POST ou listener de rede. Em caso de falha, exibe código finito sem rastrear secrets. Testes criam Git local temporário, usam mock de HTTPX e sockets UNIX efêmeros para verificar path, grupos/UID, Git sujo, container parado, falhas e impossibilidade de elevar permissões.

## Comando manual após merge, quando houver autorização do responsável do Linux

Este comando **não é deploy** e não instala serviço ou proxy. Só precisa do código atualizado no checkout e do Python do projeto; executar numa janela de leitura autorizada, sem sudo.

    cd /home/operador/projetos/delpi-central
    PYTHONPATH=linux-ops-mcp python3 -B -m linux_ops_mcp.atlas_hml_local_probe

O argumento -B evita gravação de pycache durante a importação. A ferramenta sempre retorna status=blocked, prepare_eligible=false, can_execute=false; código de saída 0 significa apenas que a execução imprimiu o diagnóstico, e 2 que o próprio diagnóstico falhou. O usuário operador atual pode ter permissão de escrita no checkout: nesse caso a recusa é intencional e não significa falha do servidor.

Sem proxy aprovado, nenhum acesso Docker é tentado, e o relatório inclui HML_PROXY_UNAVAILABLE ou HML_PROXY_NOT_CONFIGURED. A ferramenta pode ainda inspecionar Git se a conta não for privilegiada e não puder escrever no checkout.

## O que NÃO foi construído

- Nenhum Keycloak client/scope/secret/provisionamento de serviço. A etapa S2S da PR #219 continua um contrato inativo.
- Nenhuma API/MCP tool, HTTP/SSH daemon, Docker socket montado, config nova do Compose, migration, grant Core/DB, script de rollout ou escrita em HML/PROD.
- Nenhum coletor operacional certificado: a identidade OS, transporte mútuo, política de proxy Docker, confiabilidade do filesystem e atomicidade do Git permanecem sem atestação, mesmo com Git limpo e container saudável.
- Nenhuma prova de execução de rollback, backup/restauração, reversibilidade de migrations, consumo one-shot do nonce ou direito humano PREPARE/ACT.
- Nenhuma recomendação para usar Docker group ou montar docker.sock no MCP/API. Isso equivaleria a privilégio elevado no host.

## Aceite seguro e plano do próximo pacote

- [ ] 6 checks aplicáveis verdes (GitHub Docker, PG/API, Linux MCP read-only, arquitetura, auditoria).
- [ ] Revisão independente delpi-verifier com outro agente; não confundir com GitHub Actions.
- [ ] Revisão humana das permissões de socket e da hipótese de proxy GET-only.
- [ ] Depois de aprovado, configurar conta OS unprivileged em HML e proxy exclusivo sob change control. Validar que nenhuma requisição POST/exec/listagem é permitida e que acesso à API Docker bruta não foi exposto.
- [ ] Executar manualmente o preflight e conferir relatório, estado Git/contêiner, timestamp, sem gravar dados nem instalar serviços.
- [ ] Só depois desse ensaio, considerar um coletor de receipts + transporte S2S autenticado, com auditoria e channel binding entre JWT, nonce e dados HMAC, ainda read-only e PREPARE/ACT OFF.

**Invariante:** toda saída permanece BLOCKED. Este passo traz observação real de Linux sem transformar o ATLAS em sistema de implantação.
