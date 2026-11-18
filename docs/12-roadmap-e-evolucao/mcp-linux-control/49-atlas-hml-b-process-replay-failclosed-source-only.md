# ATLAS | Arquitetura B: integridade de processo, continuidade e falha segura

**17/11/2026 | Issue [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232) | SOURCE-ONLY | NÃO INSTALADO | 52%**

## Entrega técnica

Este pacote agrupa dois controles de revisão em código e testes adversariais:

1. **Processo Linux (offline):** `atlas_hml_b_process_evidence.py` revisa um envelope estrito, de origem declaradamente não confiável, para presenter: UID/GID real e efetivo sem root, grupos suplementares vazios, capabilities efetivas/permitidas/ambient zero, NoNewPrivileges, seccomp, LSM, namespace, somente um FD socket e inventário declarativo de aliases e transportes Docker.
2. **Continuidade de snapshots:** `atlas_hml_b_snapshot_continuity.py` mantém estado imutável em memória por chamador, recusa replay literal, timestamp regressivo, geração com mesmo timestamp e bytes diferentes, troca não autorizada de container/image, TTL vencido e payload PROD. O retorno não altera o estado anterior.

Ambos são **candidatos de revisão offline**, não ferramentas MCP, não APIs, não serviços e não provas de host. Não há acesso a Docker, /proc, systemd, socket, banco, Keycloak, rede ou alterações em arquivos do host.

## Limitações que não podem ser mascaradas

- O envelope do processo é fornecido pelo operador; mesmo evidência declarada totalmente consistente não comprova que o futuro PID `systemd` em `srv-api` corresponde a ele. O digest é referência, não assinatura ou atestação.
- Inventariar um FD por `socket:[inode]` **não identifica o peer**; verificação por origem do FD, identidade do socket e rotas alternativas ainda exige ensaio em processo real.
- O ledger anti-replay é **volátil e não integrado**. Reinicialização, troca de estado, relógio adulterado e produtor root comprometido não são impedidos. Persistência de contador, assinatura/MAC com chaves protegidas e mecanismo de recuperação exigem análise específica.
- O produtor que abre Docker bruto é **host-equivalente** mesmo one-shot; Python não restringe acesso de um processo comprometido.
- SEC-01 a SEC-10, parecer humano independente ou exceção formal, autorização de mudança, rollback ensaiado, origem autêntica do snapshot e isolamento real do presenter estão pendentes. O código sempre mantém `blocked`, PREPARE/ACT OFF e 4 tools MCP READ.

## Falha, parada, recuperação e rollback

Antes de ativação futura, ensaiar em HML: snapshot ausente, truncado, trocado, stale, replay, geração contraditória, produtor falhando antes/depois do rename, indisponibilidade de socket, timeout de cliente, PID de presenter inadequado, FD Docker herdado e interrupção/restart de timer. Sob falha, **negar observação atual e não reutilizar sucesso anterior**. Registrar evidência sem segredos e interromper apenas unidades ATLAS novas. Nenhum fallback para Docker bruto, PROD ou PREPARE/ACT. Proibir reinício/alteração do daemon compartilhado, limpeza por glob e reconfiguração de produção.

Uma execução/rollback operacional só pode ser discutida depois da revisão humana formal de Segurança, ensaios no host, plano de reversão controlado, provas SEC-01..SEC-10 e autorização explícita do owner. **Não converter arquivos `.review` em serviços executáveis.**

## Revisão e validação

O workflow ATLAS Linux/Docker descartável inclui os novos testes; uma única revisão DELPI Verifier independente será solicitada ao fim da PR, sem confundir CI com parecer humano. Conservar progresso geral em **52%** até comprovação operacional real. **Não executar pull/deploy no `srv-api`**.
