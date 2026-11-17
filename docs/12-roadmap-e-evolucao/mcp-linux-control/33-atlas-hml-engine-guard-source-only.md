# ATLAS P2.2h.2al-an | Guard de transporte Docker Engine exclusivo HML

**Data:** 17/11/2026 (BRT). **Estado:** codigo candidato em PR Draft, sem deploy. **PREPARE/ACT:** OFF.

## Motivacao

PR #223 fortaleceu as permissoes e a identidade do socket de entrada, mas isso nao prova que o processo com acesso ao Docker Engine aceita somente a leitura pretendida. A API bruta do Docker equivale a controle elevado do host, inclusive quando a aplicacao que a chama contem apenas operacoes GET. O proximo passo seguro e acrescentar um guard executavel **dentro do cliente** do futuro processo upstream e comprovar recusas em CI, **sem instalar o upstream no servidor**.

## Entrega source-only

- `linux-ops-mcp/linux_ops_mcp/atlas_hml_engine_boundary.py`: `HMLDockerGETTransport` aceita somente request HTTP `GET http://docker.local/containers/delpi-hml-public-hub/json`; rejeita metodo, URL, porta, query, body, cabecalho nao allowlisted e request excessiva. Nao permite seguir redirects, upgrade ou content-encoding inesperado e verifica Content-Length declarado. A camada tipada `HMLDockerInspectOnly` aceita somente o `RuntimeTarget` exato de HML e reutiliza `DockerReadOnlyInspect` para limitar resposta a 256 KiB e validar IDs, labels Compose, estado e health.
- `linux-ops-mcp/tests/test_atlas_hml_engine_boundary.py`: usa apenas MockTransport HTTPX e metadados sinteticos; positivos, negativos de metodos e destinos, labels, redirecionamentos, compressao e corpo grande. Nenhum socket Docker real, rede externa ou operacao host.
- Workflow `atlas-p22e-integration.yml`: monitora novos arquivos nos gatilhos de PR/push. `linux-ops-mcp-readonly.yml` cobre toda pasta por glob existente.

## Limites e bloqueios importantes

Este componente **nao** intercepta o acesso ao Docker fora dele. Se o processo supervisor privilegiado puder abrir `docker.sock` ou executar outro binario, bibliotecas internas nao representam barreira de privilegio. A implementacao nao define usuario efetivo, namespaces, seccomp, MAC, systemd, cgroups, ACL, socket Docker do upstream, bridge, sidecar nem daemon. Tambem nao inicia automaticamente o proxy da PR #221.

A revisao humana de Seguranca deve estabelecer o processo que fara a leitura e a politica de confinamento fora do Python. Em especial, um processo que detenha o socket bruto Docker e privilegiado mesmo que passe todas as verificacoes do guard em CI. As afirmacoes `proxy_policy_independently_attested`, `collector_identity_attested`, `host_identity_attested`, `checkout_integrity_attested`, `prepare_eligible`, `can_execute` continuam falsas. PREPARE/ACT OFF.

## Plano de validacao futura do host (requer autorizacao separada)

1. Inventariar e aprovar, com o owner Linux e revisor independente, como um processo upstream isolado obteria **somente** a consulta do contêiner HML; demonstrar que o processo nao tem caminho alternativo de API Docker, sudo, shell ou containers de producao.
2. Revisar o modelo de ameacas: codigo comprometido no proprio upstream, dependencias, processo root, socket activation, substituicao de pathname, credenciais, uso de ACLs adicionais, isolamento MAC, restart, logs e rollback do servico.
3. Validar fora do ambiente produtivo que requests de escrita/listagem/exec nunca alcancam Docker Engine e nao ha headers ou respostas confidenciais expostas. Verificar que somente o UID `atlas-hml` acessa a projecao root-owned 0660 e que `atlas-hml` continua fora do grupo docker.
4. Preparar runbook de instalacao e remocao com ownership, revisao de seguranca, backup/recuperacao, janela e plano de reversao. Nenhum comando deste documento autoriza instalar servico, socket ou alterar permissoes.
5. Mesmo com teste HML aprovado, uma etapa de governanca separada exige Core humano fresco, journal, challenge one-shot, identidades atestadas, Git/OCI assinados, restauracao e rollback antes de cogitar PREPARE. ACT permanece fase posterior.

## Evidencias e gates

- [ ] CI Linux MCP, ATLAS Docker/PostgreSQL, auditoria e arquitetura, **no HEAD da PR**, aprovados
- [ ] `delpi-verifier` independente executado e veredito anexado
- [ ] Code review humano de Seguranca e Linux
- [ ] Execucao real de Docker Engine GET-only sob isolamento aprovada e testada separadamente
- [ ] Nenhum deploy, merge automatico, nova ferramenta MCP, API de escrita, credencial, socket ou servico foi instalado

**Proximo passo:** revisar isolamento externo ao guard antes de propor qualquer piloto HML. O resultado deste incremento e controle de transporte em codigo, nao atestacao do servidor.
