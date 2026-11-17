# ATLAS P2.2h.2ay-bb | Dossie unificado de pre-ativacao HML, somente leitura

**Data:** 17/11/2026 (BRT). **Estado:** Draft PR, source-only. **Servidor DELPI:** sem alteracoes. **PREPARE e ACT:** desabilitados.

## Objetivo operacional

As PRs #220-#229 entregaram preflight de leitura, politica de socket UDS, guard de Docker GET unico, testes com Docker Engine em runner descartavel e diagnostico OS do coletor. Para acelerar a primeira homologacao, este pacote reduz as observacoes manuais a **um JSON sanitizado**, unindo:
- Postura local da conta tecnica via `atlas_hml_collector_isolation.observe_current_process` e `review_facts`
- Metadados de `.git/HEAD` de checkout compartilhado via `GitHeadMetadataPeek`, quando seguro observar, **sem executar Git**
- Politica de metadados do socket HML fixado via `verify_socket_metadata`, quando seguro observar, **sem criar, abrir ou conectar a socket Docker**

Arquivo: `linux-ops-mcp/linux_ops_mcp/atlas_hml_host_review_bundle.py`.

**Este dossie nao atesta o host, o processo upstream, o checkout, o binario implantado, o proxy Docker ou autorizacao.** Metadados e resultados de CI nao comprovam ausencia de bypass ao Docker Engine. Nao introduz cliente Keycloak, HTTP/MCP tool, listener, daemon, CI/CD de HML, escrita em banco ou deploy.

## Comportamento fail-closed

1. O processo precisa coincidir com `atlas-hml`, ter grupo primario correspondente, nao ter grupos privilegiados, nao escrever no checkout nem nos dois caminhos Docker canonicos e nao carregar capacidades efetivas, permitidas ou ambientais.
2. Se qualquer uma dessas verificacoes essenciais for `false` ou `null`, o diagnostico nao le sequer os metadados Git nem os do socket HML. Mantem `status=blocked`.
3. Se for seguro fazer apenas essas leituras, o HEAD so sai como `git_head_metadata_only_untrusted`. Nunca fornece Git clean, atestacao OCI/CI ou SHA implantado.
4. O proxy so recebe estados `unavailable`, `unsafe_or_unverifiable`, `metadata_only_untrusted` ou `skipped_unsafe_account`. Mesmo quando o arquivo de socket obedece a owner/grupo/mode, **isso nao valida o processo que o atende**.
5. Seccomp e NoNewPrivs tambem sao observados, mas os resultados da execucao manual podem diferir dos de um supervisor futuro. Nao se promove PASS a partir deles.
6. A saida nunca e `READY`: `host_identity_attested=false`, `proxy_policy_independently_attested=false`, `checkout_integrity_attested=false`, `challenge_consumed=false`, `prepare_eligible=false`, `can_execute=false`.

## Testes e limites da evidencia

- `test_atlas_hml_host_review_bundle.py`: cobre flags todas positivas, recusa de contas inseguras, payloads Git falsificados, HEAD sem validade, ausencia/unsafe de UDS, excecoes com texto sensivel, timestamps invalidos e invariancia dos flags de autorizacao.
- Workflows Linux MCP e ATLAS incluem teste da CLI e testes negativos. O Docker Engine real permanece exclusivo do GitHub Actions, nunca do `srv-api`.
- **CI_PASS nao equivale a HOST_ATTESTED**. Verificador `delpi-verifier` independente e revisor de Seguranca continuam exigidos.
- `status=blocked` com codigo de saida 0 significa **relatorio gerado**, nao aceite da ativacao.

## Etapa operacional futura, manual, somente com decisao do operador

Apos o merge e um `git pull --ff-only` escolhido pelo operador para atualizar o checkout, pode-se executar o dossie pela conta existente, sem alterar seus grupos, permissoes, Docker, Keycloak, infra ou serviços:

```bash
cd /home/operador/projetos/delpi-central
sudo -u atlas-hml env PYTHONPATH=/home/operador/projetos/delpi-central/linux-ops-mcp /opt/atlas-hml/venv/bin/python -B -m linux_ops_mcp.atlas_hml_host_review_bundle
```

Este comando faz leituras locais, nao tenta GET ao proxy, nao abre a API Docker e nao cria arquivos persistentes. Nao executar como root nem ajustar privilegios para "obter PASS". Na revisao, nunca publicar credenciais, stacktraces, raw `/proc`, dumps Docker ou acesso ao socket bruto.

## Dossie para revisao humana independente

| Evidencia exigida | Owner proposto | Situacao apos a PR |
|---|---|---|
| Conta `atlas-hml`, capabilities e DAC do checkout/socket bruto | Linux/Seguranca | CLI read-only pronta; execucao real nao comprovada |
| Fluxo de privilegios do futuro upstream Docker, uid/gid, MAC, systemd, fds herdados | Linux/Seguranca | Design/revisao independente pendentes |
| Filtro GET Docker com alvo HML, conteudo reduzido e negativas | Desenvolvimento/Seguranca | CI descartavel comprovado, host real pendente |
| Canal UDS root-owned/atlas-hml e supervisor/ciclo de vida | Linux/Seguranca | Codigo fonte pronto, sem socket/servico instalado |
| Checkout e imagem OCI imutaveis, SHA efetivamente implantado | Release/Seguranca | HEAD somente diagnostico, nao atestado |
| Restore, rollback, migrations e recusas de producao | Infra/Owner | Teste real e aprovacao pendentes |
| Journal nonce one-shot, Core/Keycloak e aprovador nominativo | Backend/Core | Gates persistentes inativos |
| Verificador `delpi-verifier`, revisao humana e change ticket | Reviewer independente/Owner | Pendentes |

## Proximo desenvolvimento de maior retorno

**Nao multiplicar testes locais sem decidir a fronteira privilegiada upstream.** A proxima acao de seguranca e revisar, com um segundo especialista, o desenho de como um processo independente tera acesso ao Docker Engine e de como o cliente `atlas-hml` ficara sem esse acesso, incluindo protecao de `systemd`/socket e rollback dos novos componentes. Somente com revisao e autorizacao administrativas separadas pode ocorrer instalacao em HML. **PROD intocada.**

## Gates desta PR

- [ ] Cinco verificacoes do GitHub Actions verdes no HEAD final
- [ ] `delpi-verifier` executado e parecer nao editado anexado
- [ ] Parecer humano de Seguranca sobre plano de privilegios de Docker
- [ ] Nenhum merge/deploy automatico
- [ ] PREPARE/ACT continuam OFF
