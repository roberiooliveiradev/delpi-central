# ATLAS | Etapa 70: baseline do srv-api e endurecimento DAC do signer

**18/11/2026 | issue #232 | SOURCE-ONLY | BLOCKED | referencia de progresso 60%**

O baseline abaixo foi reportado pelo operador do srv-api por comandos exclusivamente de leitura.
Isso nao constitui atestacao independente nem autorizacao para alterar host, Docker, chaves,
systemd, PREPARE ou ACT.

## 1. Evidencias do operador

| Componente | Observado | Limitacao |
| --- | --- | --- |
| Host | srv-api, Ubuntu 24.04, Linux 6.8.0-147-generic | Sem atestacao independente de identidade |
| Docker/containerd | Ambos active | Sem inventario de endpoints alternativos ou FDs herdados |
| Socket Docker | /run/docker.sock = root:docker 0660; /var/run/docker.sock aponta para o mesmo socket; ACL base sem entradas estendidas | Nao confere isolamento real de processos futuros |
| HML | delpi-hml-public-hub running + healthy, compose delpi-hml/public-hub, imagem sha256:f9566946c0e34fc56fc17aebe0936e7045d4c1b5bb545374e0b12415ce39401a | Origem Docker nao verificada por terceiro |
| PROD | delpi-public-hub running, compose infra/public-hub, imagem sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb | Sem healthcheck, portanto NAO declarar healthy |
| Identidades | atlas-hml UID 995, GID 985; grupo docker GID 988 | atlas-hml-bridge e atlas-hml-signer nao existem |
| Artefatos ATLAS | Servicos systemd, diretorios de snapshot, chave, estado e socket ausentes | Esperado no pre-piloto |
| LSM kernel | lockdown, capability, landlock, yama, apparmor | Perfil efetivo do PID real nao observado |
| Revisao local antes desta PR | HEAD e origin/main local bff9f1eee440028cb91c025589050758bd1398c9 | Estavam atras da main remota; nao houve git fetch/pull |
| Worktree | modo 100644 -> 100755 em infra/scripts/up-hml-sequential.sh; uma linha adicionada em shared/delpi_auth.egg-info/SOURCES.txt | Preservar ambos; nao fazer stash, reset, clean ou deploy |

O usuario que realizou o diagnostico pertence ao grupo docker, o que permite acesso privilegiado
ao Engine. Esse usuario NAO deve ser tomado como modelo de grupo para bridge ou signer.
Nenhuma identidade dedicada recebeu acesso Docker nessa etapa.

## 2. Defeito da fronteira DAC encontrado antes da ativacao

O layout candidato de /run/atlas-hml-signer-socket estava em 0750, sem setgid, e a funcao
bind_signer_owned_socket aceitava o grupo primario do signer quando o GID solicitado
nao coincidia. Isso nao garante que a bridge consiga conectar ao socket previsto.

Contrato revisado nesta PR:

- Diretorio do socket: atlas-hml-signer:atlas-hml-bridge, modo **02750** (setgid).
  A bridge atravessa o diretorio, mas nao escreve nele.
- Socket AF_UNIX: UID exclusivamente do signer, GID **exatamente** da bridge,
  modo **0660** herdado do diretorio setgid. Nao usar chown nem fallback para
  o grupo primario do signer.
- Verificacao antes do bind: processo non-root; directory FD O_DIRECTORY,
  O_NOFOLLOW e O_CLOEXEC; inode/UID/GID/modo exatos; ausencia comprovada
  de ACL POSIX estendida e de entradas preexistentes (inclusive symlink quebrado).
- Verificacao posterior: inode do listener, owner, grupo, modo, tipo, parent
  e escuta. Nao apagar arquivos preexistentes se bind falhar.
- O binario signer deve assumir UID nao-root antes de chamar bind/listen.
  Um socket prebound por root nao satisfaz o requisito SO_PEERCRED.

O revisor estatico de candidate-units exige somente as cinco diretivas de
tmpfiles autorizadas. Nega modos, identidades e paths extras, ainda que textos
semelhantes aparecam nos comentarios.

## 3. Testes em runner descartavel

- Suite negativa especifica de Etapa 70: modo sem setgid, diretorio permissivo,
  GID divergente, symlink de parent ou de socket, socket preexistente, ACL nao
  confiavel e alteracao perigosa de tmpfiles.
- Suite Linux elevada do GitHub Actions: signer UID 61021 e bridge UID 61022
  usando agora a **funcao candidata real** de bind; contagem e resultado devem
  ser confirmados no CI do HEAD. O teste de socket prebound por root permanece.
- Suite de cadeia HML E66-69 ajustada para um diretorio disposable 02750.
- Nenhum teste em srv-api; nao atesta os usuarios, grupos, ACL, perfis LSM ou
  descritores reais do servidor.

## 4. Proxima mudanca operacional (AINDA NAO AUTORIZADA)

1. CI 5/5 do HEAD + DELPI Verifier independente + decisao do owner de merge.
2. Reconciliar com seguranca os dois arquivos modificados localmente no
   checkout do srv-api. Nao sobrescrever nem limpar a arvore do servidor.
3. Change-control exclusivo HML, janela e baseline PROD com healthcheck
   funcional ou prova de saude de nivel de aplicacao.
4. Validar Docker endpoints/FDs, perfis AppArmor e grupos reais antes de
   sugerir qualquer criacao de usuario, diretorio ou unidade.
5. Somente sob autorizacao operacional separada: provisionar identidades e
   diretórios, conferir socket 02750/0660, bootstrap com ancora externa,
   chave real + GLPI, packaging e instalacao HML e rollback somente ATLAS.
6. STOP em desvio do Docker Engine, PROD, LSM, autenticação, UID/GID ou
   contador monotônico. Nunca alterar docker.service, containerd.service,
   Public Hub PROD ou realizar restore de geração antiga automaticamente.

**Quatro ferramentas MCP READ, PREPARE/ACT OFF, status BLOCKED, nenhuma chave real
ou unidade instalada. Nao realizar git pull ou deploy nesta etapa.**
