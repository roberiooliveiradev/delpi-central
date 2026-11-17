# ATLAS HML | Arquitetura B: processo isolado e FDs controlados no CI descartável

**Data:** 17/11/2026 (BRT)  
**Situação:** EXPERIMENTO DE PROCESSO LINUX EM CI DESCARTÁVEL, SEM INSTALAÇÃO OU HOMOLOGAÇÃO NO HOST  
**Issue:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232) | **Roadmap:** etapa 56  
**Referências:** [runbook 42](./42-atlas-hml-supervisor-blueprint-review.md), [runbook 43](./43-atlas-hml-independent-security-decision-gate.md), [runbook 44](./44-atlas-hml-disposable-os-boundary-evidence.md), [runbook 46](./46-atlas-hml-architecture-b-presenter-candidate.md).

## 1. Decisão e limite desta entrega

A [PR #251](https://github.com/roberiooliveiradev/delpi-central/pull/251) foi integrada à `main` em `2998b25c7b26287aec13958c1689b1210936ce2d`, após Cursor `composer-2.5` emitir `ACCEPT_WITH_RESIDUAL` (zero ordens de correção). O owner aprovou **arquitetura B como direção de desenvolvimento**, não o acesso operacional ao Docker nem a instalação de serviços.

Já existem: produtor com transporte injetado, JSON restrito, publicação atômica, leitor FD com ACL, presenter com socket prebound, parser GET estrito e blueprints systemd deliberadamente **não instaláveis**. Ainda faltava reproduzir a **separação entre processos** com UID/GID de kernel e verificar que somente o FD de UDS permitido atravessa o `exec`.

Este pacote é **somente um teste Linux em GitHub Actions descartável**, com 4 cenários: três protocolos (GET HML autorizado, GET PROD negado, POST negado) e um ensaio negativo **proposital** com FD Docker herdado. O teste não inclui código de supervisor operacional, serviço `systemd`, usuário Linux no servidor, bind permanente, coleta no `srv-api`, IAM, banco ou API nova.

## 2. Fronteira de processos exercitada

```text
     Runner descartável GitHub Actions (CI_DOCKER=true)
                         |
                  processo root do TESTE
                    /             \
         Docker socket (somente    cria fixture /tmp:
         conexão local sem GET)    root:nobody 0750
                    |              JSON  root:nobody 0640
         [root mantém FD]          UDS   root:nobody 0660
                    |                   |
                    X  FD Docker         v
               NÃO É PASSADO     exec subprocess `nobody`
                                  ├─ UID/GID efetivos > 0
                                  ├─ grupos suplementares vazios
                                  ├─ SOMENTE FD do UDS prebound
                                  ├─ conexão nova ao Docker negada por DAC
                                  ├─ leitor snapshot FD e ACL
                                  └─ GET /v1/hml/public-hub/snapshot
                                            ^
                                   outro processo `nobody`
                                   via SO_PEERCRED
                                         |
                         status=blocked, PREPARE/ACT false
```

A chamada `subprocess.Popen` usa `user=<nobody_uid>`, `group=<nobody_gid>`, `extra_groups=[]`, `close_fds=True` e `pass_fds=(fd_do_listener,)`. O root do runner abre uma conexão Docker apenas para obter um FD real que **não pode** ser herdado no caso positivo. O filho confere por `/proc/self/fd` que o **único socket** recebido é o listener esperado, que a conexão direta ao Docker é negada por DAC e que UID/GID/grupos efetivos estão restritos. Um cliente separado, também `nobody`, prova `SO_PEERCRED` e protocolo real no presenter.

**Controle negativo deliberado:** se `pass_fds` for alterado no teste para incluir o FD Docker, o filho deve identificar o inode privilegiado e encerrar com código de teste 47 **antes de atender solicitações**. Esta é uma propriedade **do harness de teste**, não uma detecção de FDs automaticamente instalada no futuro serviço operacional.

Todos os caminhos de teste são temporários e pertencem ao runner; a rotina só conecta ao Engine local CI. Não envia qualquer método HTTP ao Docker; não executa `docker run`, `docker stop`, `docker exec` nem altera recursos. A criação e remoção dos contêineres Alpine da fixture permanecem responsabilidades do workflow CI já existente.

## 3. Evidências e critérios de falha

| ID | Evidência em runner efêmero | Falha que interrompe CI |
|---|---|---|
| **B-OS-01** | `nobody` após `exec` tem UID/GID não root, grupos vazios, snapshot root:grupo legível, GET HML atendido por presenter de verdade | UID errado, grupo extra, payload diferente ou resposta que promova poder |
| **B-OS-02** | Conexão nova ao Docker pelo child é negada pelo kernel, sem reutilizar root FD | Docker socket aberto ou erro não reconhecido |
| **B-OS-03** | Descritores de socket pós-`exec` contêm **somente o UDS prebound**, sem FD Docker da conexão aberta pelo root do teste | Qualquer outro socket encontrado, inclusive o Docker |
| **B-OS-04** | GET PROD e POST são recusados por protocolo antes da leitura, mantendo `BLOCKED` | HTTP aceito ou payload não sanitizado |
| **B-OS-05** | Passagem intencional do FD Docker ao `exec` causa recusa antes do atendimento | Processo não identifica a presença de inode Docker |

A suíte encontra-se em `linux-ops-mcp/tests/test_atlas_hml_presenter_process_boundary_real_ci.py` e roda junto com `test_atlas_hml_os_boundary_real_ci.py`, exclusivamente sob `GITHUB_ACTIONS=true`, `ATLAS_DISPOSABLE_DOCKER=true`, `ATLAS_REAL_HML_CHAIN_CI=true`, como root **na runner**. Em execuções locais fora dessas flags ela é ignorada, **não** utilizada como prova de host.

**NÃO concluir** que uma conexão Docker fica segura apenas por negar `/var/run/docker.sock`. A [etapa 53](./44-atlas-hml-disposable-os-boundary-evidence.md) já demonstrou o risco de uma conexão preaberta sobreviver ao drop de UID. Este teste acrescenta a capacidade de detectar uma herança inadequada **no cenário descartável controlado**.

## 4. Evidências ainda ausentes para o supervisor HML real

A proposta de unidades em `linux-ops-mcp/review-only/` continua **intencionalmente não executável** (`.review`, `ExecStart=/usr/bin/false`, sem `[Install]`). Nenhum `systemd-analyze security` ou unidade do servidor foi validado.

- **SEC-01**: revisão humana independente/decisão formal de exceção documentada pela governança, ainda pendente. O owner é o único profissional disponível; usar IA diferente para código **não transforma** a revisão em parecer humano independente.
- **SEC-02**: origem e risco host-equivalente do produtor root, cadeia de execução, credenciais, limites reais de acesso Docker e superfície por aliases/TCP ainda não comprovados.
- **SEC-03/04**: processo `atlas-hml` real, `/proc/<PID>/fd`, capabilities, `NoNewPrivileges`, grupos, ACLs, seccomp, LSM e namespace do serviço verdadeiro ainda não verificados. `nobody` **não** representa a identidade real `atlas-hml` de produção.
- **SEC-05/06**: UDS parent real, symlinks, ACL, replay, geração do snapshot e rollback pós-`rename` pendentes. O teste não prova autenticidade da origem root.
- **SEC-07/09**: plano de reversão e autorização de mudança devem proibir qualquer impacto em `delpi-public-hub` de produção e no daemon Docker compartilhado.
- **SEC-08/10**: `delpi-verifier` específico da PR de processo ainda deve ser executado por outro modelo; Core, journal, S2S, backup/restore, PREPARE/ACT continuam sujeitos a gates próprios.

## 5. Plano de homologação, ainda não autorizado

Esta seção é **checklist de projeto**, NÃO uma ordem para executar no `srv-api`.

1. Registrar decisão de exceção de governança **se não houver revisor humano independente**, deixando riscos, responsável e limites claros. A exceção não atesta isolamento ou elimina testes.
2. Entregar proposta operacional **separada** com inventário de caminhos Docker (UDS e rede), binários assinados/imutáveis, usuários, FDs, `systemd` real, contas e permissões; revisar arquitetura conforme SEC-02..05 antes de habilitar qualquer unidade.
3. Autorizar mudança específica e restrita a HML (janela, critério de interrupção, ponto de recuperação e limite absoluto de não mexer no Docker daemon compartilhado / `delpi-public-hub` PROD).
4. Na janela autorizada, registrar linha de base de serviços, processos, mounts e containers sem modificações; ensaiar negações de UID, FDs, ACLs, aliases e rede, replay, stale, rollback e desligamento limpo.
5. **Se qualquer prova falhar:** não ativar nem promover acesso; interromper os novos componentes e confirmar que o ambiente original continua íntegro, sem reiniciar o Docker compartilhado ou a aplicação de produção.
6. Adicionar evidência e decisão nominativa do owner à issue #232 e ao roadmap antes de passar para a próxima fase.

**Situação resultante após merge desta PR:** nenhuma instalação; produção intocada; quatro ferramentas MCP existentes somente READ; `status=blocked`, `prepare_eligible=false`, `can_execute=false`; progresso global conservador **52%** até validação real e autorização independente de operação.

**Ação do responsável agora:** executar `delpi-verifier` pelo Cursor no clone de desenvolvimento *após* os checks desta PR, informar veredito e decidir merge. Nenhum comando de pull/deploy no `srv-api` é exigido por este pacote.
