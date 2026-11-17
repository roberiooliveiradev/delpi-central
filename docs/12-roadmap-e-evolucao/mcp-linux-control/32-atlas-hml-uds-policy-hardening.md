# ATLAS P2.2h.2ai-ak | Politica compartilhada de UDS HML (source-only)

**Data:** 16/11/2026 (BRT). **Estado:** PR Draft, CI e revisao independente pendentes. **Servidores:** intocados. **PREPARE/ACT:** desabilitados.

## Objetivo e escopo

Endurecer a integracao local do proxy Docker limitado ao Public Hub de homologacao, preservando o estado BLOCKED e a ausencia de qualquer processo/servico persistente. Esta entrega **nao instala, inicia, liga, configura nem conecta** um proxy no `srv-api`.

Componentes:
- `linux-ops-mcp/linux_ops_mcp/atlas_hml_uds_policy.py`: mesma verificacao de metadata do socket para proxy e preflight. Caminho real fixo `/run/atlas-hml-readonly/inspect.sock`; owner de diretorio e socket: root; grupo do diretorio/socket: grupo nominal `atlas-hml`; modo do socket exatamente `0660`; diretorio sem permissoes para outros e sem escrita por grupo, mas com travessia habilitada para o grupo. Nega symlinks no caminho imediato, aliases de inodes conhecidos de sockets Docker e metadata de socket bruto inacessivel. A identidade nominal `atlas-hml` exige UID nao-root, grupo primario `atlas-hml` e shell de `nologin`.
- `atlas_hml_unix_proxy.py`: valida que FD recebido e um AF_UNIX stream listener em escuta, com pathname esperado. No caminho real, UID admitido por SO_PEERCRED deve coincidir com o UID resolvido da conta `atlas-hml`; um UID indicado por supervisor nao muda a identidade aprovada. O inspector async e limitado por deadline adicional de 4 s. Erros permanecem sanitizados e o retorno sempre declara BLOCKED.
- `atlas_hml_local_probe.py`: reutiliza a politica antes de criar o transporte HTTPX ao socket. Falha de metadata de UDS continua diagnostico bloqueado, nao permissao para ler Docker bruto.
- Testes: fixtures AF_UNIX descartaveis, modes/owner/group, alias, UID, listener sem `listen`, falhas do upstream e ausencia de identidade; sem Engine Docker real, banco, Keycloak ou host Delpi.

## Contrato operacional proposto (nao executar sem autorizacao)

O desenho de provisionamento futuro requer:
1. Owner Linux e Seguranca aprovarem o processo que acessara a API Docker, sua fronteira de isolamento (ex.: politica de proxy Engine de GET unico) e a impossibilidade de uso de metodos alternativos, mesmo quando um usuario local comprometer o processo upstream.
2. Supervisor revisado cria **fora** do MCP o diretorio root-owned e o socket root-owned, com grupo `atlas-hml`, modo do socket `0660`, diretorio root-owned e group-traversable, sem escrita por grupo ou acesso por outros. A conta `atlas-hml` nao recebe acesso ao socket `/var/run/docker.sock`, nem grupos `docker`/`sudo`, nem scripts de deploy.
3. Revisao independente comprova que nao existe acesso direto do coletor a Docker Engine por outro caminho, que supervisor nao aceita binds arbitrarios e que a aplicacao upstream nao pode encaminhar `POST`, `PUT`, `DELETE`, `exec`, listagem ou outra inspeção.
4. Ensaio HML real com cliente `atlas-hml`: GET da allowlist entrega apenas metadados sanitizados; outra conta, outros container/servico, headers indevidos e metodos alternativos retornam erro sem executar consulta upstream.
5. A alteracao tem change ticket, reversao, observabilidade segura (sem payload bruto e sem secrets) e autorizacao explicita antes de instalar qualquer unidade, socket, configuracao ou processo.

## Evidencia e lacunas nao resolvidas

**Evidencia de codigo:** ha verificacoes de identidade, ACL do pathname, metodo/caminho HTTP, sanitizacao e suite de teste negativa. **Evidencia de CI:** verificar checks da PR no commit de head, nao presumir resultado. **Evidencia host:** nenhuma nova coleta, nao ha proxy instalado. Mesmo com GET 200, as flags `host_identity_attested`, `proxy_policy_independently_attested`, `checkout_integrity_attested`, `prepare_eligible` e `can_execute` nao podem ser promovidas.

**Limites materiais:** o modo de arquivo nao prova isolamento do processo Docker/Engine, ACL adicionais, grupos efetivos em NSS/LDAP, capacidades Linux, SELinux/AppArmor, autenticidade do binario nem ausencia de TOCTOU por administrador privilegiado. Em Linux, `fstat(listener)` e `lstat(path)` pertencem a namespaces/inodes distintos (sockfs vs pathname); comparar esses dois inodes seria incorreto. O pathname e um controle preventivo sob diretorio root-owned, mas nao atestacao criptografica do listener. `SO_PEERCRED` informa UID kernel da conexao, nao a identidade ou integridade do codigo cliente. Revisao de seguranca independente e ensaios de host sao obrigatorios.

A revisao Git HEAD da PR #222 continua `filesystem_head_only_untrusted`; `HML_GIT_STATUS_NOT_CHECKED`, `GIT_IGNORED_FILES_NOT_MEASURED` e `GIT_FILESYSTEM_SNAPSHOT_NOT_ATOMIC` permanecem. Nenhum credito adicional e concedido a release, journal, Core, nonce, backup/restore ou rollback.

## Gates de aceite

- [ ] Linux MCP read-only, ATLAS disposable CI, arquitetura e auditoria, todos aplicaveis na PR
- [ ] Verificador `delpi-verifier` independente, conforme `AGENTS.md` (indisponivel neste ambiente; nao declarar PASS)
- [ ] Revisao humana de processo elevado, ACLs efetivas, grupo `atlas-hml` e caminho real de Docker Engine
- [ ] Autorizacao administrativa separada para qualquer provisao e ensaio no servidor
- [ ] PREPARE e ACT continuam desabilitados; nenhuma PR e mesclada automaticamente

**Proximo passo depois da revisao de codigo:** avaliar isoladamente o processo upstream/supervisor e plano de validacao no host, sem ativar o proxy por inferencia.
