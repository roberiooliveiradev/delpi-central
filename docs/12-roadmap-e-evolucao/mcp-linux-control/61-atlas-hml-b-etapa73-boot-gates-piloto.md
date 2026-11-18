# ATLAS | Etapa 73: boot seguro e gates para o primeiro piloto HML

**18/11/2026 | Issue #232 | SOURCE-ONLY | status=blocked | PREPARE/ACT OFF**

## Entrega de codigo

1. Reusa o candidato tmpfiles com cinco entradas exatas, incluindo /run/atlas-hml-signer-socket com modo 02750 e grupo bridge. A funcao render_stage73_tmpfiles_payload devolve o texto em memoria, mas nao o grava. Instalacao futura exige change-control, validacao da precedencia com outras regras tmpfiles e read-back por FD.
2. As unidades .candidate do bridge e signer continuam nao instalaveis: sentinel impossivel, RefuseManualStart=yes, sem secao Install e ExecStart=/usr/bin/false. Acrescentado isolamento de rede, capabilities vazias, limitacao de descritores, entrada padrao nula, hardening de kernel e namespace. Bridge sem permissao de acesso ao estado, chave e diretorio do signer.
3. O modulo atlas_hml_b_stage73_boot_guard.py valida o layout e unidades, rejeita diretivas perigosas e faz inspeção somente leitura de pastas por openat com O_NOFOLLOW, FD, owner, grupo, modo e ACL. Nao instala servicos nem abre Docker.
4. A suite test_atlas_hml_b_stage73_boot_guard.py inclui fixtures de DAC, ACL, symlink, socket, identidade, heranca de FD, env Docker e diretivas indevidas. Evidencia de fixture e CI nao constitui atestacao do host.

## Janela operacional C futura: STOP ate autorizacao separada

- CI validado no SHA exato, DELPI Verifier independente, SEC-01 a SEC-10 e parecer humano de Seguranca.
- Validar identidades, grupos suplementares, ausencia de docker/sudo, DAC e ACL reais. Provar conexoes Docker negadas ao bridge e ao signer, inclusive alternativas TCP, UDS e FDs herdados.
- Conferir AppArmor efetivo por PID, isolamento em runtime, socket AF_UNIX 0660 criado pelo signer nao-root, nunca por root-prebound ou chown corretivo.
- Inspecionar sobreposicao de regras tmpfiles em /etc/tmpfiles.d e /usr/lib/tmpfiles.d. Garantir recriacao pos-boot, controle de ACL/symlinks e read-back. systemd-tmpfiles --create, instalacao e reboot exigem plano e autorizacao separados.
- Bootstrap gen1 com ancora externa real, chave operacional com recuperacao segregada e vinculacao GLPI, rollback testado e health PROD antes/depois.
- Nenhum deploy, pull, systemctl, Docker, geracao de chaves, alteracao de identidades, ACL ou permissoes nesta entrega.

| Area | Prova da PR | Pendencia |
|---|---|---|
| Persistencia /run | Regras verificadas em codigo | instalacao, reboot e atestacao |
| Units HML | candidatos bloqueados e hardenings | revisao independente e sandbox real |
| Isolamento | testes negativos descartaveis | endpoints, AppArmor e FDs no host |
| Assinatura local | reaproveita etapas 62-70 | gen1, chave real, GLPI e rollback |
| Governanca | handoff e CI | Verifier + SEC-01..10 |

**Invariantes:** quatro MCPs READ, PREPARE/ACT desabilitados, can_execute=false, prepare_eligible=false, status=blocked. Os arquivos .candidate nunca devem ser publicados automaticamente via deploy. Progresso global conservador: 60%.
