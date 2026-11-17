# ATLAS P2.2h.2bg-bj | Revisao de arquivo snapshot HML por descriptor (source-only)

**Data:** 17/11/2026. **Estado:** PR Draft candidata, sem instalacao/deploy. **Escopo:** somente codigo, testes e documentacao. **PREPARE/ACT:** OFF. **Issue de decisao:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232).

## Contexto

PR #234 (mesclada) entregou somente o parser puro de snapshots HML para a **alternativa B candidata**, que ainda nao foi aprovada. A proposta e separar um produtor one-shot elevado e um apresentador sem Docker bruto. Este incremento prepara a **leitura local por file descriptor** com validacao de metadados, mas **nao** cria produtor, gravador, timer, socket, supervisor, atendente UDS ou tool MCP.

O diagnostico real enviado pelo operador mostrou `atlas-hml` com grupo/conta apropriados, sem escrita no checkout/sockets Docker conhecidos e capabilities zeradas. `NoNewPrivileges=false` e `Seccomp=false` caracterizam aquela sessao manual; nao ha supervisor instalado. `HML_PROXY_UNAVAILABLE` permanece esperado.

## Arquivo desenvolvido

`linux-ops-mcp/linux_ops_mcp/atlas_hml_snapshot_file_reader.py`

A entrada publica candidata `read_fixed_hml_snapshot(now=...)` permite **somente** o caminho fixo:

- diretorio: `/run/atlas-hml-readonly`, root-owned, grupo nominal `atlas-hml`, modo exato `0750`
- arquivo: `inspect-snapshot.json`, root-owned, grupo nominal `atlas-hml`, modo exato `0640`, arquivo regular, unico hardlink, mesmo filesystem do diretorio, tamanho entre 1 e 2048 bytes.

`os.open` utiliza `O_DIRECTORY`, `O_NOFOLLOW`, `O_CLOEXEC` no diretório e `O_NOFOLLOW`, `O_NONBLOCK`, `O_CLOEXEC` no arquivo aberto com `dir_fd`. O leitor confirma owner/grupo/mode, inode, device, tamanho e timestamps antes e depois da leitura e compara o descriptor com o pathname. Em caso de ausencia, symlink, hardlink, modo inseguro, alteracao durante leitura, mtime fora da janela ou payload nao HML, apenas retorna excecao com **codigo finito sanitizado**. Nao fornece paths/JSON/segredos de erro ao consumidor.

O parser anterior `review_untrusted_snapshot` continua a exigir HML exato, ID de contêiner, image ID, schema estrito, chaves unicas e timestamp JSON de 60s com margem de 5s. `mtime` tambem e checado (declaracao do filesystem, nao assinatura).

**Importantissimo:** metadados root-owned e comparacao de inodes sao apenas filtros locais de risco e de corrida. Eles **NAO provam autoria, integridade criptografica, escrita realmente atomica, seccomp aplicado, processo produtor isolado nem ausencia de paths/FDs alternativos**. Um root comprometido pode forjar arquivo e tempo. Todo retorno valido permanece `status=blocked`, `prepare_eligible=false` e `can_execute=false`.

## Testes e evidencias

- `tests/test_atlas_hml_snapshot_file_reader.py`: fixtures descartaveis `tmp_path`; cobre leitura valida com BLOCKED, ausencia do arquivo, diretorio e arquivo com modos errados, owner/group errados, symlink de arquivo/diretorio, hardlink, FIFO, vazio, payload >2KiB, mtime stale/future, JSON stale, PROD, arquivo substituido entre leitura e revalidacao de inode e entrada invalida.
- Workflow `linux-ops-mcp-readonly.yml` ja inclui `linux-ops-mcp/tests/**` e todo o pacote; workflow ATLAS tambem deve incluir os novos paths e seu teste no job Docker descartavel.
- Nao roda a API Docker do srv-api, nao chama systemd, Keycloak, DB ou Git, nao altera o usuario/grupo e nao requer execucao manual no host.
- Checks no HEAD da PR e `delpi-verifier` independente precisam ser verificados, jamais presumidos.

## Revisao de seguranca necessaria antes de ativacao

1. Owner Linux/Seguranca deve decidir explicitamente o modelo A/B/C da [ADR 38](./38-atlas-hml-supervisor-architecture-proposal.md); preferencia por B ainda e recomendacao em debate.
2. Projetar e revisar **produtor one-shot**, fronteira de acesso ao Docker Engine e ausencia de Docker bruto/Fds privilegiados no apresentador, com evidencia de isolamento OS real, limites de unidade/timer e autenticidade de artefatos.
3. Projetar escrita atomica `temp + fsync + rename` sob diretorio root-only e limpeza/rollback sem afetar Docker/containers existentes. A escrita **nao esta implementada** aqui.
4. Definir quais evidencias o apresentador pode exibir e como recusar snapshot duplicado/stale quando produtor parar, sem permitir replay. Prova de frescor autentico exige controle de ciclo/nonce externo, nao confiar em timestamp/mtime.
5. Verificar ACLs, mounts, FDs, hardening systemd (`NoNewPrivileges`, Seccomp, capabilities, namespaces, MAC/LSM), secrets, log redaction, detecao de falhas e mudanca autorizada antes de instalar.
6. Alteracao da politica `serve_one_prebound` para aceitar snapshot exige ADR aprovada, revisao independente e testes adicionais; **nao alterada nesta PR**.

## Proibicoes e estado final

- Nao instalar/criar `/run/atlas-hml-readonly`, socket ou servico por conta desta PR.
- Nao executar deploy em HML/PROD, nao reiniciar Docker/containers, nao conceder permissao ao socket bruto.
- Nao criar MCP tool, workflow administrativo, Core PREPARE/ACT ou prova falsa de Git/revisao implantada.
- Sem merge automatico. `delpi-verifier` externo e parecer humano independente pendentes.
