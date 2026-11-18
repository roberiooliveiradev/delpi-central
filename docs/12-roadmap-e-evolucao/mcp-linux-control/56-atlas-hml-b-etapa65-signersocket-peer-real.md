# ATLAS | Etapa 65: fronteira SO_PEERCRED do assinador HML

**17/11/2026 BRT · issue #232 · SOURCE-ONLY / BLOCKED · progresso 58%.**

PR #272 / Etapa 64 integrada na main em b6b93b01d887004977f6b2d95ff1255a291ce248. DELPI Verifier da Etapa 64: ACCEPT_WITH_RESIDUAL, independência OK, zero ordens de correção.

## 1. Lacuna crítica encontrada antes do piloto

O blueprint anterior considerava um socket AF_UNIX em escuta criado por systemd/root e transferido por FD a um processo signer não-root. No Linux, SO_PEERCRED no cliente pode devolver o UID de quem executou listen(2), não o UID atual do processo que herdou o listener. Um ensaio descartável comprovou peer UID 0 quando root chamou listen, mesmo com um processo posterior não-root.

Isso conflita com a regra da ponte da Etapa 63, que exige o UID não-root do signer. NÃO autorizar UID 0, NÃO desligar SO_PEERCRED e NÃO considerar SocketUser ou SocketGroup evidência de peer UID não-root.

## 2. Decisão candidata: signer cria e escuta seu próprio socket

- Preparação futura de diretório exclusivo para socket, owner atlas-hml-signer e grupo atlas-hml-bridge, modo 02750 (setgid), sem ACL estendida. O signer cria o socket e executa bind/listen depois de perder definitivamente qualquer UID root; o socket fica owner signer, group bridge, 0660.
- O signer usa UID/GID próprios, sem grupos suplementares, Docker ou FD herdado de Docker. A ponte não-root possui o grupo bridge e valida SO_PEERCRED do signer, owner/gid/mode/inode e Ed25519 pública.
- Chave privada em diretório separado, signer:signer 0700, arquivo 0600; store do contador em diretório signer:signer isolado. A ponte não recebe chave, Docker ou privilégio de escrita no diretório do socket.
- O blueprint legado atlas-hml-local-signer.socket.review foi aposentado como candidato de socket activation: apenas seção Unit, sem seção Socket ou Install e condição impossível. O blueprint service continua deliberadamente não executável (ExecStart=/usr/bin/false).
- O modelo aceita o risco residual de root malicioso no mesmo host. Isso não converte assinatura local em autenticidade independente nem comprova SEC-01..10.

## 3. Evidência de CI, não de srv-api

Teste elevado de CI exclusivamente descartável, com UID root e as três flags GITHUB_ACTIONS, ATLAS_DISPOSABLE_DOCKER e ATLAS_REAL_HML_CHAIN_CI iguais a true:

1. Demonstração negativa: socket escutado por root reporta peer UID 0.
2. Demonstração positiva: signer UID 61021 e bridge UID 61022 em subprocessos reais, sem criação de usuários; listener bind/listen pelo signer e SO_PEERCRED confere UID 61021.
3. Chave Ed25519 efêmera não legível pela bridge; conexão da bridge aos caminhos Docker UDS locais recusada; sem fd herdado de Docker.
4. Snapshot allowlisted HML, assinatura validada com pública, geração 1 em fixture e geração 2 após reinício; bloqueio PREPARE/ACT e quatro MCP READ preservados.

A prova do CI não abrange aliases Docker TCP, config real systemd, kernel/LSM, UID/GID reais do srv-api, assinaturas operacionais nem autorização. Os testes não alteram o Docker Engine nem contêineres do srv-api.

## 4. Gates e mudança futura

Permanecem pendentes: wrapper operacional com caminhos fixos, revisão de permissões e unidades efetivas, âncora externa de bootstrap da geração 1, geração/custódia de chave real e GLPI com autorização específica, janela de HML, preflight read-only, rollback apenas ATLAS e ratificação formal de SEC-01/exceção quando exigida. Primeiro ensaio em host somente após decisão independente de mudança, mantendo delpi-public-hub de produção intocado.

**Sem pull/deploy, sem instalação, sem chave real, sem autorização de PREPARE/ACT.**
