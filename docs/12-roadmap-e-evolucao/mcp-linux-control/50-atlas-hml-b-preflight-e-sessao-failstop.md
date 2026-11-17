# ATLAS | Etapa 59: preflight do presenter e sessão de snapshots (Arquitetura B)

**17/11/2026 | SOURCE-ONLY | Issue [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232) | Sem instalação, deploy ou operação no srv-api**

## Resultado técnico verificável

Este pacote aproxima os controles já existentes de um comportamento real, **sem publicar serviço**:

1. `atlas_hml_b_presenter_process_guard.py` executa uma inspeção **do próprio processo**: /proc/self/status, lista real de descritores, UID/GID real/efetivo/salvo/filesystem, grupos suplementares, capabilities, NoNewPrivileges, seccomp, listener AF_UNIX e **nomes** de variáveis Docker. Recusa descritores inesperados, incluindo Docker pré-conectado, antes de o processo de teste chamar o apresentador. Não lê /proc/self/environ, não enumera outros PIDs, não conecta ao Docker e não imprime dados sensíveis.
2. O teste de subprocesso Linux `nobody` em runner **descartável** passa a chamar a guarda reutilizável, em vez de repetir a lógica de detecção de FD apenas no harness. O teste negativo injeta intencionalmente um FD conectado ao Docker da runner e exige recusa antes do atendimento. O teste positivo ainda atende somente o GET HML com `status=blocked`; PROD e métodos de escrita negados.
3. O leitor via FD ganhou um **registro interno** de bytes e identidade do inode (`HMLSnapshotFileRecord`), sem alterar o resultado público `read_fixed_hml_snapshot`. Checagens O_NOFOLLOW, owner/GID, modo, ACL, nlink, TOCTOU e TTL permanecem.
4. `atlas_hml_b_snapshot_file_session.py` implementa sessão **volátil, fail-stop** que aceita leituras repetidas do mesmo inode imutável enquanto fresco e recusa substituição in-place, regressão temporal, republicação do mesmo instante em outro inode, alteração não revisada de container/image, falha do produtor, falha de publicação e shutdown. Uma falha fica travada; sem fallback ao Docker, PROD ou execução automática.
5. Testes positivos e adversariais verificam módulos, limites e encadeamento entre leitor e sessão. Os workflows Linux e Docker descartáveis incluem esses casos.

## Diferentes garantias, diferentes responsáveis

| Propriedade | O que esta PR demonstra | O que ainda falta |
|---|---|---|
| Herança de FDs | Guarda é executada no subprocesso real em GitHub Actions; FD extra detectado | Evidência do PID real systemd em srv-api, alias/namespace/rede e MAC/LSM |
| NoNewPrivileges/seccomp/cap bounding | Inspeção de campos, resposta bloqueada se não observados | Configuração efetiva de kernel e qualidade das políticas; CI não atesta srv-api |
| Integridade do snapshot | Leitura via FD + comparação de inode, ctime, mtime, digest e geração em sessão | Assinatura/origem independente, contador persistente, resistência após restart/comprometimento root |
| Falha/recuperação | Falha travada, sem continuar com snapshot suspeito; simulada por teste | Rollback operacional ensaiado, inventário das unidades novas e aprovação explícita |

**Atenção:** `identity_fd_preflight_passed` é verificação parcial dentro do processo, **não prova de isolamento completo**. `sandbox_basics_observed` valida valores, não qualidade do seccomp nem MAC. Não são permissões de instalação. A sessão é **single-process em memória, não thread-safe nem persistente**. Nenhum pacote prova origem do produtor root: acesso ao socket Docker bruto continua equivalente ao poder sobre o host.

## Contrato de segurança preservado

- Quatro ferramentas MCP permanecem **READ**; `PREPARE/ACT` desligados; todos os resultados diagnósticos `blocked`.
- Sem chamada HTTP Docker fora do Docker descartável já permitido no CI; sem leitura de variáveis secretas; sem comando shell; nenhuma configuração systemd/Docker/contas/ACL alterada.
- Os cinco arquivos `.review` continuam **não instaláveis** e sem `ExecStart` operacional; nenhum novo entrypoint ou wiring de MCP.
- Não usar este CI como atestação do host nem parecer humano SEC-01. SEC-01..SEC-10, revisão humana independente ou exceção formal, change-control, rollback real e autorização específica ainda pendentes.
- O `srv-api` e produção não receberam mudanças: **NÃO realizar pull/deploy** por esta PR.

## Próximo gate

Revisar CI da Draft PR e solicitar **uma única** execução independente de DELPI Verifier no HEAD final (conforme contrato). Depois da revisão de código e merge pelo owner, planejar observação operacional **somente sob autorização específica**, com desenho de assinaturas e contador persistente isolado do produtor, sem comprometer o Docker compartilhado.

**Progresso geral conservador: 52%.** Arquitetura B segue autorizada apenas para desenvolvimento source-only.
