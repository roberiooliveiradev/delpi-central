# ATLAS HML | Supervisor e isolamento Docker: arquitetura candidata

**Data:** 17/11/2026. **Estado:** PROPOSTA PARA REVISAO, sem aprovacao nem implantacao. **Branch:** `feat/atlas-hml-snapshot-supervisor-review`; entregar em Draft PR separada. **Issue:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232). **Base revisada:** `372b69d118b1b1e7c4c59e02c221cd5856d9340f`.

## Objetivo e evidencias disponiveis

Observar exclusivamente `delpi-hml-public-hub` no `srv-api`, sem conceder o Docker socket bruto a `atlas-hml` nem interferir no Public Hub de producao.

A coleta real do operador em 17/11/2026 confirmou conta/grupo dedicados, shell `nologin`, checkout sem escrita, grupos nao privilegiados, capacidades Eff/Prm/Amb zeradas e DAC de escrita negada nos caminhos Docker conhecidos. Na execucao manual, `NoNewPrivileges=false` e `Seccomp=false`, que **nao** refletem a futura unidade supervisionada. `proxy_socket_metadata=unavailable`. O Git HEAD observado e metadata-only untrusted; nao atesta checkout ou imagem implantada. Suites de CI usam runner descartavel, nao atestam o `srv-api`.

## Risco principal

Qualquer processo com acesso ao `/var/run/docker.sock` bruto possui capacidade efetiva elevada sobre o host. Restringir metodos GET apenas no codigo Python nao restringe um processo comprometido que ainda consegue abrir a API Docker por outro caminho. Opcoes systemd como `NoNewPrivileges`, `Seccomp`, `CapabilityBoundingSet` e `ProtectSystem` sao defesa em profundidade e **nao substituem isolamento real da API Engine**.

## Alternativas em revisao

| Modelo | Beneficio | Limite / risco | Estado |
|---|---|---|---|
| A. Proxy Python persistente com Docker bruto | Reutiliza GET guard e UDS ja testados | Processo com privilegio permanente pode contornar filtros internos | NAO APROVADO |
| B. Produtor one-shot + snapshot + atendente UDS sem Docker | Separa consulta elevada de exposicao do coletor; reduz duracao do privilegio | Produtor ainda detem poder sobre Engine; autenticidade/atomicidade/frescor do snapshot nao comprovados | CANDIDATO PREFERIDO, nao autorizado |
| C. Plugin de autorizacao no Engine | Politica imposta pelo Engine | Altera daemon e pode afetar outros containers | FORA DO ESCOPO HML atual |

## Fluxo B candidato

```text
[timer root-owned ainda nao instalado]
       -> [produtor one-shot auditado com acesso temporal ao Engine]
       -> [snapshot reduzido, root-owned, atomico, com TTL]
       -> [atendente UDS sem acesso ao Docker, com SO_PEERCRED]
       -> [atlas-hml read-only]
       -> [status BLOCKED; PREPARE e ACT OFF]
```

**Nenhum desses processos, sockets ou timers sera criado nesta PR.**

## Contratos para proxima decisao

1. **Produtor:** alvo fixo HML; sem parametros do cliente para URL, metodo ou contêiner. Owner, codigo, configuracao e scheduler revisados por Seguranca; documentar protecao contra compromisso do produtor, FDs herdados e endpoints Docker alternativos.
2. **Snapshot:** permitir apenas `schema`, `source` (autodeclarado e nao confiavel), `environment`, `compose_project`, `service_id`, `container_name`, `container_id`, `image_id`, `running`, `healthy`, `observed_at`. Implementacao futura precisa validar arquivo por fd seguro, owner root, ACL, tipo, symlinks, diretorio protegido, escrita atomica, integridade e freshness com prova independente. Timestamp JSON nao e atestado.
3. **Atendente:** sem permissao direta ao socket bruto Docker nem FDs privilegiados herdados. Socket HML root-owned/grupo `atlas-hml` modo `0660`; diretório root-owned, nao gravavel pelo grupo. UDS request/response estritamente limitado e peer UID do kernel.
4. **Mudanca de integracao:** `serve_one_prebound` atualmente exige `HMLDockerInspectOnly` no caminho real. Um eventual `HMLSnapshotInspector` **nao** deve ser registrado como opcao operacional ate ADR aprovada, interface tipada e testes negativos de autenticidade e seguranca. Nunca aceitar inspector arbitrario via MCP.
5. **Hardening futuro:** validar `NoNewPrivileges=yes`, `CapabilityBoundingSet=`, `AmbientCapabilities=`, `RestrictAddressFamilies=AF_UNIX`, `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateTmp=yes`, `RestrictSUIDSGID=yes`, `SystemCallFilter` revisado e UMask. Nao assumir que bloqueiam um produtor comprometido que detem Docker socket.
6. **Falhas e rollback:** snapshot ausente, velho, de PROD, duplicado ou alterado deve gerar erro sanitizado e estado bloqueado. Rollback remove apenas novos componentes e jamais reinicia Docker ou containers existentes.
7. **Governanca:** PREPARE/ACT, journal one-shot, atestacao do checkout, backup/restore/rollback e Core permanecem gates separados.

## Pacote source-only desta PR

- `linux-ops-mcp/linux_ops_mcp/atlas_hml_snapshot_candidate.py`: validador puro de bytes JSON, sem filesystem, Docker, HTTP, network, subprocess ou IPC. Tamanho maximo 2048 bytes; IDs validos; HML estrito; chaves duplicadas/extra proibidas; carimbo de hora de no maximo 60s e 5s no futuro, **apenas como declaracao nao confiavel**. Toda saida aceita permanece `status=blocked`, `prepare_eligible=false`, `can_execute=false`.
- `linux-ops-mcp/tests/test_atlas_hml_snapshot_candidate.py`: 11 testes `unittest` sinteticos, positivos e negativos (PROD, schema, extras, IDs, booleanos, timestamp, oversized, erros sanitizados).
- CI deve executar o teste na suite Linux MCP e no workflow ATLAS; cobertura de CI nao comprova supervisor nem host.

## Gates obrigatorios

- [ ] CI Linux MCP, ATLAS Docker/PG descartaveis, arquitetura e audit verdes no ultimo SHA da PR.
- [ ] `delpi-verifier` independente com parecer sem edicao anexado; se indisponivel, declarar PENDENTE.
- [ ] Parecer humano Linux/Seguranca sobre B x A x C, MAC, FDs, Engine, user/group, permissoes e logs.
- [ ] Plano de homologacao HML, reversao e change control assinados, em outra etapa com autorizacao explicita.
- [ ] Nenhuma instalacao, unidade systemd, socket, daemon, Keycloak, DB, grupo, permissao, deploy nem merge automatico nesta PR.
- [ ] Apenas quatro ferramentas MCP read-only; PREPARE/ACT continuam OFF.

## Referencias

- [Docker Engine security](https://docs.docker.com/engine/security/)
- [systemd.socket](https://www.freedesktop.org/software/systemd/man/latest/systemd.socket.html)
- [systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)
