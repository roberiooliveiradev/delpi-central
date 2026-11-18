# ATLAS | Etapa 61: lock transacional de continuidade, pedido de assinatura sem chave e LISTEN_* adversarial

**Data:** 17/11/2026 (BRT)  
**Situação:** source-only, código/testes descartáveis, sem alterações no `srv-api`  
**Issue de governança:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232)  
**Base:** PR #261 integrada, Etapa 60, progresso 55%.

## 1. Avanços técnicos

- **Estado persistente via FD:** o `HMLContinuityStore` passa a validar diretório e arquivo com `O_NOFOLLOW`, proprietário, grupo, modos 0750/0640, `nlink=1`, dispositivo/inode, ACL POSIX, tamanho máximo e metadados antes/depois da leitura. `read_bytes()` por pathname é eliminado. Falha de integridade leva a latch; arquivo removido durante a vida da instância também é negado. Testes de symlink, hardlink, FIFO, modo inseguro, ACL, troca durante leitura, corrupção, fsync falho e perda de estado.
- **Concorrência fail-closed:** transação de leitura→validação→incremento→rename/fsync ocorre sob `flock(LOCK_EX|LOCK_NB)` no mesmo descritor de diretório. Segunda instância cooperante recebe `BUSY` e não sobrescreve geração. Locks são advisory, não protegem contra root nem processos que os ignorem. Diretório mutado por escrita legítima muda mtime; comparação estrutural de identidade não confunde isso com troca de inode.
- **LISTEN_* adversarial:** tuple do `systemd` aceita somente as três chaves esperadas, PID canônico do processo, um único FD3 e nome ASCII restrito. Variáveis extras, pares incompletos, zero/duas FDs, PID errado, zero-padding, whitespace, separador `:`, path e controles são negados. Sem variáveis de activation permanece permitido apenas nos testes prebound.
- **Assinatura desacoplada:** `prepare_signing_intent` produz pedido canônico HML sem parâmetro nem material privado. `review_signing_intent_for_external_signer` examina forma, tempo, escopo, bytes e contador esperado; `seal_externally_signed_intent` verifica assinatura Ed25519 e chave pública antes de montar envelope. O subprocesso signer descartável gera chave internamente e responde apenas com pública e assinatura. `key_id` agora deve corresponder ao fingerprint da chave pública, inclusive para keyring fornecido diretamente.

## 2. O que os testes NÃO comprovam

1. **Fronteira de confiança do assinador:** separar os dados em processos de CI não isola a chave de um produtor root no mesmo host. O assinador externo real exigirá identidade validada, política independente de autorização, armazenamento de chave em outro domínio (por exemplo dispositivo/serviço gerenciado com autenticação mútua), contador monotônico próprio e revisão humana. Nada disso está instalado nem autorizado.
2. **Bootstrap e replay pós-perda do estado:** uma instância já inicializada identifica desaparecimento do arquivo. Um processo novo não diferencia primeiro boot de deleção/rollback malicioso. Exigir checkpoint raiz confiável ou atestação externa antes da operação real. Fsync + flock e assinatura NÃO eliminam esse risco.
3. **Kernel/LSM/FD no srv-api:** validação de `LISTEN_*` no CI só demonstra consistência dos argumentos. Não confirma que o PID real herdou apenas o socket certo, nem ausência de acesso Docker por aliases/namespace/rede/FD.
4. **Advisory lock vs root:** outro processo privilegiado pode ignorar lock, adulterar bytes ou trocar arquivo. Não há atestação SEC-03/04.
5. **Produtor one-shot:** continua host-equivalente enquanto estiver ligado ao Docker Engine. Qualquer afirmação do produtor sobre saúde do contêiner permanece não confiável fora do domínio de execução controlado.

## 3. Gates, rollback e implantação

A arquitetura B está aprovada **somente para desenvolvimento**. SEC-01 a SEC-10, revisão independente **humana** ou exceção formal, plano operacional e ensaio de rollback real, autenticação de origem e change-control seguem pendentes. A revisão DELPI Verifier de código não substitui isso.

As quatro ferramentas MCP existentes permanecem exclusivamente READ. Status sempre `blocked`, PREPARE/ACT desligados. Não criar/instalar `systemd`, não converter `.review`, não alterar Docker, contas, grupos, ACL, Keycloak, Core, banco ou serviços de produção. Não realizar pull ou deploy em nenhuma instância `srv-api`.

Os novos testes são executados em CI Linux/Docker descartável; uma única rodada DELPI Verifier ao final do pacote consolidado conforme contrato do repositório. Não registrar resultado que ainda não foi obtido.

**Progresso conservador:** 55% até atestação técnica operacional real e revisão de segurança.
