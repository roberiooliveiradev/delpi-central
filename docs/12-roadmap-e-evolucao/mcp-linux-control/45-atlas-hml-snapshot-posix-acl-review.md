# ATLAS HML | Revisão de ACL POSIX do snapshot por FD (source-only)

**Data:** 17/11/2026 (BRT) | **Estado:** CONTRATO CANDIDATO / NAO OPERACIONAL | **Issue:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232)

## Problema corrigido nesta proposta

O leitor e o publicador do snapshot HML verificavam owner, grupo, modos POSIX (`0750` no diretorio e `0640` no arquivo), inode e freshness. Isso **nao comprova que nao existem entradas POSIX ACL adicionais** no mesmo inode, inclusive ACL default herdada pelo arquivo criado posteriormente. Atributos `system.posix_acl_access` e `system.posix_acl_default` precisam ser inspecionados tambem, ou a garantia de acesso baseada apenas em bits tradicionais fica incompleta.

O modulo `linux_ops_mcp.atlas_hml_posix_acl_review` usa **somente descritores ja abertos** para consultar `os.getxattr(fd, ...)`, sem fazer lookup de ACL por pathname que possa trocar entre `stat` e leitura. Somente `ENODATA` (atributo comprovadamente ausente) permite continuar; qualquer atributo existente, leitura negada, API ausente, filesystem sem suporte ou erro inesperado e **negação por padrão**.

## Escopo e impacto dos arquivos

| Camada | Mudanca concreta | Condicao de recusa |
|---|---|---|
| Leitor `atlas_hml_snapshot_file_reader.py` | ACL access e default do diretorio; ACL access do arquivo; repetir verificacoes apos leitura e verificacao de inode | `HML_SNAPSHOT_DIRECTORY_ACL_UNTRUSTED` ou `HML_SNAPSHOT_FILE_ACL_UNTRUSTED` |
| Publicador `atlas_hml_snapshot_publisher_candidate.py` | ACL do diretorio antes de criar stage, antes do rename e apos a publicacao | `HML_SNAPSHOT_DIRECTORY_ACL_UNTRUSTED` |
| Destino antigo do publicador | Abre arquivo existente com `O_NOFOLLOW`, `O_NONBLOCK` e `O_CLOEXEC`; compara inode/metadados por `fstat` e verifica ACL em FD | `HML_SNAPSHOT_DESTINATION_ACL_UNTRUSTED` / `...DESTINATION_UNSAFE` |
| Stage e arquivo final | Recusa ACL no stage antes e apos `fsync`, verifica novamente no mesmo FD apos rename | `HML_SNAPSHOT_STAGE_ACL_UNTRUSTED` / `HML_SNAPSHOT_PUBLISHED_ACL_UNTRUSTED` |

**Sem enfraquecimento:** permanecem limites de 2048 bytes, alvo HML fixo, `O_NOFOLLOW`, owner/GID/modes exatos, hardlink unico, validacao JSON com 11 campos, timestamp declarado recente, `fsync` + `os.replace`, e `status=blocked` / PREPARE/ACT desligados.

## Cobertura de negacoes (fixtures descartaveis)

- Diretorio com ACL access adicional e ACL default: recusa antes da criacao ou leitura.
- Snapshot anterior com ACL estendida: recusa substituicao antes de escrever, preserva bytes do destino anterior.
- Stage com ACL nao confiavel: nao executa rename, remove arquivo temporario, preserva geracao anterior.
- Falha da leitura `getxattr` (EACCES, EOPNOTSUPP, EIO) e ausencia da API: **falha fechada**, com codigo finito sanitizado.
- ACL introduzida na janela de leitura ou durante `fsync` (simulada por injecao): rechecagem recusa, sem estado aprovado.
- Fixtures POSIX regulares sem ACL estendida: os caminhos positivos antigos continuam validos e terminam somente em diagnostico `BLOCKED`.

## Riscos residuais e limite dos testes

1. **Nao ha autenticidade de origem:** root pode forjar JSON, mtime, ACL, owner e inode. Checar ACL em dois instantes reduz mas nao elimina TOCTOU contra agente privilegiado. Nao e anti-replay, assinatura, prova de imagem nem de rollback.
2. **Nao mede a configuracao real do host:** nenhuma ACL de `/run/atlas-hml-readonly` foi lida ou alterada, nem user/group, socket, Docker Engine, unidade `systemd`, LSM/MAC, mount namespace, posix ACL de ancestrais ou FDs herdados foram atestados.
3. **Sem extensao operacional:** este codigo so faz parte de modulos candidatos nao ligados ao MCP ou a API. Nenhum presenter, produtor real, daemon, CLI, timer, socket, alteracao de conta ou deploy foi criado.
4. **Falhas apos rename:** uma falha de verificacao depois do rename pode deixar um snapshot substituido mas retornar erro. Nao a tratar como transacao revertida; continua exigindo futuro plano de rollback no host.
5. **Revisor independente:** apenas o resultado do CI e evidência de exercicio descartavel; `delpi-verifier` e parecer humano sobre arquitetura A/B/C e isolamento do produtor privilegado continuam obrigatorios na issue #232.

## Antes da homologacao

A arquitetura B permanece **NAO APROVADA**. A decisao da [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232), os gates SEC-01..SEC-10 do [runbook 43](./43-atlas-hml-independent-security-decision-gate.md), o [ensaio CI-OS da etapa 53](./44-atlas-hml-disposable-os-boundary-evidence.md) e uma autorizacao operacional nominativa continuam precedendo qualquer instalacao. Testes em CI sao evidencia apenas sobre runner descartavel e fixture `tmp_path`, **nao prova de segurança no `srv-api`**.

**Publicação:** arquivo e testes source-only, sem pull/deploy necessário mesmo apos merge. **Progresso estimado permanece 52%** ate decisao de Seguranca e homologacao real.
