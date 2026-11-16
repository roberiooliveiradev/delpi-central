# ATLAS | P2.2h.2l: observador Git somente leitura, sem promoção a PREPARE

**Data:** 16/11/2026. **Estado:** candidato em Pull Request. **PREPARE_DISABLED / ACT_DISABLED.**

## Objetivo

Depois da PR #213, o pré-check do host e da imagem OCI continua corretamente bloqueado, porque o Docker não comprova que o checkout Git no servidor está limpo. Esta etapa fornece uma inspeção local de Git sem criar uma autoridade de deploy. Arquivo: linux-ops-mcp/linux_ops_mcp/deploy_git_checkout_readonly.py.

## Funcionamento

- GitCheckoutReadOnlyObserver aceita somente o alvo public-hub e os pares exatos de contêiner/projeto Compose para hml/prod. RuntimeTarget e caminho pertencem ao processo confiável e jamais a entradas HTTP/MCP.
- O caminho operacional padrão é /home/operador/projetos/delpi-central. Exige caminho absoluto e canônico, sem symlinks, e diretório .git real. Não confia em um .git externo ou checkout por worktree. A troca de checkout_root existe somente para testes isolados.
- Comandos permitidos: rev-parse --show-toplevel, symbolic-ref --quiet --short HEAD, rev-parse --verify HEAD^{commit}, status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none. Depois do status, relê HEAD, branch e raiz para detectar algumas mudanças concorrentes.
- Processa em subprocess.run sem shell, com git --no-optional-locks, fsmonitor desabilitado, hooksPath=/dev/null, untrackedCache desabilitado, ambiente sem configurações Git global/system herdadas, timeout de cinco segundos e limite de saída validado.
- Retorna branch, SHA, indicação de arquivos rastreados e não rastreados alterados, timestamp e motivos de bloqueio. Não expõe conteúdo ou nomes de arquivos, tokens, stderr nem caminhos intermediários.
- GitCheckoutObservation sempre possui status inspection_only_blocked, checkout_attested=False, challenge_bound=False, rollback_ready=False, prepare_eligible=False, inclusive quando branch main e git status vazio.

## Limites de segurança

Uma leitura Git local NÃO é uma atestação assinada do estado do host. Não autentica o processo executor, não vincula a medição ao nonce do banco e não prova a procedência da imagem OCI. Arquivos ignorados pelo Git não são medidos, e o filesystem não oferece um snapshot atômico; a releitura de HEAD só detecta algumas corridas. Git status também pode carregar configurações/atributos do repositório: a futura execução deve ser por identidade OS não privilegiada, contra checkout confiável, sem chaves de deploy, acesso Docker ou poderes sobre o banco.

O limite de output é conferido após captura pelo subprocesso, logo não é limite rígido de memória contra um repositório hostil. Não expor essa rotina a repositórios arbitrários. A medição não deve preencher automaticamente HostProof.checkout_clean=True; isso exigirá comprovante host autenticado por chave separada, vínculo a challenge e controles de concorrência.

## Testes de regressão

- linux-ops-mcp/tests/test_deploy_git_checkout_readonly.py testa alvo permitido/proibido, symlinks e gitdir externo, git status limpo/sujo, branch inesperada, HEAD alterado durante a leitura, comando inexistente, erro e timeout sanitizados, resposta gigante, clock inválido e argumentos/ambiente dos subprocessos.
- Teste com Git real cria exclusivamente um repo temporário do pytest e realiza commit de teste, edição de arquivo, criação de arquivo untracked e troca de branch. O observador apenas lê; toda escrita é setup do teste em tmp_path, nunca em produção.
- O workflow atlas-p22e-integration.yml passa a executar o teste no job Docker descartável do GitHub Actions junto aos testes de host existentes.

## Gates restantes

- [ ] Todos os cinco checks da Pull Request concluídos com sucesso.
- [ ] Revisão humana e revisão independente delpi-verifier por outro agente.
- [ ] Ensaio HML sob identidade OS somente leitura, diretório fixado no backend e sem Docker socket.
- [ ] Comprovante autenticado da medição associado ao challenge one-shot do journal; controle de race e proteção de status.
- [ ] CI/GHCR real, backups/rollback, migrações e Core grants nominativos ainda pendentes.
- [ ] PREPARE e ACT continuam desabilitados.

**Próxima evolução:** desenhar host signer separado para o checkout, que assine bytes observados com identidade host e challenge, sem atribuir prontidão de migração/rollback.
