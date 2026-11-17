# ATLAS P2.2h.2bs-bv | Blueprint de supervisor HML para revisao independente

**Data:** 17/11/2026 (BRT) | **Status:** PROPOSTA, nao aprovada/instalada | **PREPARE/ACT:** OFF | **Issue de seguranca:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232)

## Objetivo

A PR #239 foi mesclada em `a37e1400e24cfaf7560ab81139a825122e5c5f70` com 5/5 checks verdes. A cadeia `Docker HML GET -> RuntimeContainer -> JSON reduzido -> publicador atomico -> leitor FD` ja funciona no **runner descartavel**. O proximo bloqueio real e uma decisao verificavel sobre **privilegios do produtor e isolamento do apresentador**, nao mais a codificacao de um novo GET.

Esta PR entrega somente um conjunto de `systemd` **blueprints nao executaveis** e um teste estatico de drift. Nenhuma unidade `systemd`, socket, diretorio, grupo, permissao ou timer e instalado no `srv-api`. O modelo B de produtor one-shot privilegiado + apresentador sem Docker continua **NAO APROVADO**.

## Arquivos de design, nao instalaveis

| Arquivo dentro de `linux-ops-mcp/review-only/` | Papel em revisao |
|---|---|
| `atlas-hml-snapshot-producer.service.review` | Processo one-shot root com Docker de alto privilegio e controles de defesa em profundidade |
| `atlas-hml-snapshot-producer.timer.review` | Cadencia candidata 30s, sem ativacao |
| `atlas-hml-snapshot-presenter.service.review` | Leitor dedicado `atlas-hml`, sem Docker bruto, sem capabilities e protegido por sandbox |
| `atlas-hml-snapshot-presenter.socket.review` | UDS fixo `/run/atlas-hml-readonly/inspect.sock`, root:`atlas-hml`, modo 0660 |
| `atlas-hml-runtime-dir.tmpfiles.review` | Pai /run/atlas-hml-readonly root:`atlas-hml`, modo 0750 |

**Incapazes de iniciar a operacao:** todos os arquivos terminam em `.review`, nao em `.service`, `.socket`, `.timer` ou `.conf`; nao possuem `[Install]`; os dois services incluem `ExecStart=/usr/bin/false`. As unidades contêm `RefuseManualStart=yes` e uma condicao de arquivo artificial `REVIEW-ONLY-NEVER-CREATE`. Nao renomear, instalar ou habilitar esses exemplos. A implementacao real de presenter com socket activation **nao existe**. A rotina one-shot atual so recebe um transporte injetado e diretorio de fixture.

## Separacao pretendida, ainda nao comprovada

```text
[PRODUTOR curto, privilegiado, NAO INSTALADO]
  acesso Docker bruto por um periodo limitado | risco host-equivalente
        |
        +-- GET container HML allowlisted em codigo (NAO sandbox de Docker)
        +-- snapshot reduzido, root-owned, com fsync + rename
        |
[ARQUIVO 0640 root:atlas-hml]
        |
        v
[APRESENTADOR atlas-hml, sem Docker e sem FD privilegiado herdado]
        |
        v
[SOCKET UDS 0660 root:atlas-hml, SO_PEERCRED, politica de protocolo]
        |
        v
[ATLAS READ | status=BLOCKED | PREPARE/ACT OFF]
```

### Limites tecnicos que nao podem ser disfarçados

- **Docker Engine:** um processo que pode abrir `docker.sock` tem poder equivalente a administrador do host. `NoNewPrivileges=yes`, `CapabilityBoundingSet=`, `ProtectSystem=strict`, filtros de syscalls e um GET allowlisted em Python **nao** limitam os poderes concedidos pela propria API Docker. A origem/assinatura e isolamento do produtor exigem avaliacao humana independente.
- **Pai do UDS:** `SocketGroup=atlas-hml` muda o grupo do inode do socket, **nao o grupo do diretorio pai**. O pai precisa existir com root:`atlas-hml` 0750 e ser conferido via stat, ACL, mounts e politica de namespaces, separadamente. `DirectoryMode=0750` sozinho nao garante o grupo correto.
- **RestrictAddressFamilies:** limitar a `AF_UNIX` restringe a criacao de sockets, mas **nao** revoga descritores recebidos por socket activation ou herdados. E necessario confirmar explicitamente quais FDs o presenter recebe, e verificar falta de acesso ao Docker bruto por aliases, ACL, rede ou FDs.
- **Execucao manual:** os valores `NoNewPrivileges=false` e `Seccomp=false` observados sob `sudo -u atlas-hml` **nao** atestam como sera um processo sob `systemd`.
- **Autenticidade do snapshot:** modo POSIX, owner root, `fsync`, `rename` e TTL detectam varias falhas, mas nao comprovam autoria, previnem replay por root ou atestam imagem/revisao Git realmente implantada.
- **Supervisao real:** esses blueprints nao recebem FDs, nao fazem bind real, nao invocam Docker e nao produzem snapshots. Nao existe equivalente de `systemd-analyze security` observado no host.
- **Risco de rollback:** retorno do helper apos rename e antes do fsync pode ser incerto. A reversao operacional deve ser testada em HML e atingir somente os novos componentes ATLAS.

## Testes desta PR

O modulo `linux_ops_mcp/atlas_hml_supervisor_blueprint_review.py` valida de maneira **lexical** (nao um parser completo de `systemd`) o conjunto exato de arquivos de design. Rejeita qualquer mudanca de `ExecStart=/usr/bin/false`, guardas de ativacao, usuario/group, capabilities, `NoNewPrivileges`, `ProtectSystem`, visibilidade de `docker.sock`, caminhos, modo UDS ou policy de tmpfiles. Rejeita `[Install]`, propriedades adicionais, arquivos faltantes ou novos e valores falsificados. A saida do revisor de texto permanece `status=blocked`, `architecture_approved=false`, `can_execute=false`, `prepare_eligible=false` mesmo para o conjunto nominal. Nenhum teste e politica de host ou prova independente; e apenas um gate de integridade do design.

Arquivos: `tests/test_atlas_hml_supervisor_blueprint_review.py` e dois workflows existentes do ATLAS/Linux MCP. Os testes executam exclusivamente no CI e leem apenas os arquivos `.review` do repositório.

## Matriz de evidencias para decisao da issue #232

| Gate | Responsavel sugerido | Situacao |
|---|---|---|
| Revisao de privilegio real do produtor Docker e de caminhos alternativos | Especialista Linux/Seguranca independente | PENDENTE |
| Decisao formal A/B/C e threat model aceito | Owner do ATLAS + Seguranca | PENDENTE |
| Checagem de capacidade, NoNewPrivileges, seccomp, namespaces e MAC/LSM da unidade real | Linux/Seguranca | PENDENTE |
| Teste de ausencia de Docker bruto e FDs elevados no presenter, no host real | Linux/Seguranca | PENDENTE |
| Owner root, grupo atlas-hml, UDS 0660, pai 0750, ACL e symlinks | Linux/Seguranca | PENDENTE |
| Teste operacional HML com parada do produtor, stale/replay e rollback | Owner HML/Infra | PENDENTE |
| `delpi-verifier`, CI, evidencias de commit assinado/release e change ticket | Reviewer/release/owner | PENDENTE |
| Aprovacao Core, journal challenge one-shot, backup/restore, PREPARE/ACT | Control plane/owner | BLOQUEADO |

## Condicoes antes de qualquer instalacao futura

1. Parecer de Seguranca independente anexado a issue #232, incluindo avaliacao de `docker.sock` equivalente a root, FDs, aliases, ACLs, sistemas de arquivos e MAC/LSM.
2. Implementacao real do presenter sem Docker, startup/socket activation testados sem privilegios de Engine, e prova de runtime no `srv-api`; **nao basta copiar os blueprints `.review`**.
3. Mudanca planejada e autorizada com janela, rollback, logs sanitizados, limpeza de recursos novos e verificacao de nao impacto na aplicacao Public Hub de producao.
4. PREPARE e ACT continuam OFF ate seus gates independentes.

**Proxima prioridade:** obter a decisao da issue #232 antes de gerar unidades reais ou ativar o processo upstream. Se a arquitetura B for rejeitada, descartar as alternativas candidatas source-only sem colocar o host em risco.

## Documentacao de referencia

- [Docker Engine security](https://docs.docker.com/engine/security/)
- [systemd.socket](https://www.freedesktop.org/software/systemd/man/latest/systemd.socket.html)
- [systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)
