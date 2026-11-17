# ATLAS P2.2h.2au-ax | Revisao local de isolamento do coletor HML

**Data:** 17/11/2026. **Estado:** Draft PR, codigo read-only; **PREPARE/ACT: OFF**. Nenhuma alteracao no `srv-api`.

## Por que este incremento

A PR #227 foi mesclada e comprovou 5/5 checks CI: a cadeia completa UDS/guard Docker funcionou com Docker Engine real somente em runner GitHub descartavel. **Isso nao prova como um processo privilegiado se comporta no Linux da DELPI.** A proxima barreira e medir, com o processo certo e sob controle do operador, se o coletor realmente tem privilegios minimos.

Esta entrega cria `linux-ops-mcp/linux_ops_mcp/atlas_hml_collector_isolation.py`, uma CLI **sem argumentos e somente leitura**, com saida JSON de flags e codigos sanitizados. Foi projetada para ser executada manualmente como `atlas-hml` depois de merge/revisao e autorizacao do operador. Nao ha daemon, provisionamento, socket, subprocesso, HTTP, banco, token, Keycloak, git, grants, chmod/chown ou Docker API.

## Contrato da coleta

| Observacao | Como e observada | O que NAO comprova |
|---|---|---|
| Conta OS | NSS `atlas-hml`, UID/EUID e shell `nologin` | Integridade do binario, processo remoto, setuid futuro |
| Grupo primario e suplementares | `os.getgroups()` + NSS, rejeicao de nomes privilegiados | ACLs, regras LDAP futuras, capacidades por outros processos |
| Permissao de escrita no checkout | `os.access(..., os.W_OK, effective_ids=True)` | Snapshot Git atomico ou ausencias de arquivos ignorados |
| Socket Docker bruto | `stat` e `os.access` somente nos dois caminhos canonicos | FDs herdados, outros aliases, endpoints TCP, namespaces ou Unix fora da lista |
| Capacidades Linux | Leitura limitada a 8192 bytes de `/proc/self/status`: CapEff/CapPrm/CapAmb | Bypass de host ou provas independentes de isolamento |
| NoNewPrivs e Seccomp | Flags do processo corrente em `/proc/self/status` | Que o futuro supervisor execute o mesmo programa/politica ou proteja Docker |
| DOCKER_HOST / DOCKER_CONTEXT / CONTAINER_HOST | Somente presenca/ausencia; nunca imprime valores | Ausencia de endpoints alternativos configurados fora do ambiente |

Se o checkout estiver ausente, a capacidade de escrever nele e DESCONHECIDA, nunca comprovada como negada. Falhas de NSS, leitura/proc e stat geram `null` e bloqueios, nunca PASS. `NoNewPrivs=0` ou `Seccomp!=2` tornam o check insatisfatorio para a postura proposta, **nao** sao evidencia de erro do servidor, ja que a CLI manual nao roda sob o futuro supervisor.

Em qualquer combinacao, inclusive todos os fatos `true`, a resposta mantem:
- `status=blocked`
- `prepare_eligible=false`
- `can_execute=false`
- `host_identity_attested=false`
- `upstream_process_attested=false`
- `proxy_policy_independently_attested=false`

**Importante:** o diagnostico imprime fatos observados, nunca um veredito independente de seguranca. `os.access` mede DAC de um instante, nao prova impossibilidade de abrir Docker por outros meios. O backend nao consome essas flags como evidencia de PREPARE/ACT. Nao substituir a revisao humana por booleans.

## Verificacao e testes nesta PR

- `tests/test_atlas_hml_collector_isolation.py`: matriz negativa de cada campo (false/null), formatos falsificados (string/int/dict), proc com capabilities, dados ausentes ou maiores que 8 KiB, grupos com `docker`, caminho ausente, recusa de acesso Docker bruto e excecoes sanitizadas. Nada abre socket real.
- Workflow Linux MCP: compile, suite inteira, smoke da CLI explicitamente com `status=blocked`; continua inventory das 4 tools read-only.
- Workflow ATLAS: novo arquivo em filtros e conjunto de testes do CI Docker descartavel, sem acesso ao host DELPI.

## Procedimento futuro de operacao (somente depois de revisao e autorizacao)

O operador podera executar manualmente com a conta tecnica existente, **sem alterar sudoers, senha, permissoes, grupo, checkout, venv, Docker nem iniciar daemon**:

```bash
cd /home/operador/projetos/delpi-central
sudo -u atlas-hml env PYTHONPATH=/home/operador/projetos/delpi-central/linux-ops-mcp /opt/atlas-hml/venv/bin/python -B -m linux_ops_mcp.atlas_hml_collector_isolation
```

- Este comando so faz leituras e imprime JSON; exit 0 significa que o diagnostico foi emitido, nao que o sistema esta aprovado.
- Sob execucao manual via `sudo -u`, seccomp e `NoNewPrivs` podem estar ausentes. Isso apenas sinaliza controles que o **supervisor futuro** precisara garantir.
- Nunca usar `sudo` para dar a `atlas-hml` acesso ao Docker. Esse comando executa com credenciais da conta e nao chama `docker`.
- Nao anexar JSON bruto de processos ou caminhos privados; somente codigos e booleans sanitizados podem compor o dossie de revisao.

## Bloqueios que NAO foram removidos

1. Privilegios reais do processo upstream que tera acesso ao Docker Engine; possivel bypass via socket bruto, processo root, FD herdado, TCP e confusao de namespaces.
2. Instalacao/ativacao de proxy e socket `/run/atlas-hml-readonly/inspect.sock`, ainda inexistentes segundo o ultimo teste real informado pelo operador.
3. Revisao de Seguranca independente de OS, ACL, MAC/LSM, capabilities, binaries e systemd.
4. Checkout Git nao confiavel e sem snapshot atomico; HEAD continua dado diagnostico.
5. Consumo one-shot do journal challenge, restore real, rollback/migration e grants Core nominativos.
6. PREPARE e ACT continuam inteiramente desabilitados.

## Proximo marco operacional

Reunir revisao independente de processo com acesso ao Docker Engine, comprovar recusa de acesso bruto para `atlas-hml`, definir quem podera iniciar/parar **apenas** o proxy novo e formular change plan e reversao para HML. Essa revisao nao e substituida pelo CI nem autoriza a instalacao automaticamente. **Nenhum servico de producao deve ser reiniciado.**

## Gates da entrega

- [ ] Cinco checks CI no ultimo HEAD da Draft PR, sem skipped indevidos
- [ ] `delpi-verifier` executado de forma independente; veredito literal registrado
- [ ] Revisao humana do fluxo de socket/supervisor e ameaças do Docker Engine
- [ ] Nenhuma alteracao de servidor ou permissao durante esta PR
- [ ] Nenhum merge automatico nem liberacao de PREPARE/ACT
