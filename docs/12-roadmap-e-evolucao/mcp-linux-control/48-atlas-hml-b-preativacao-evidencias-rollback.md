# ATLAS | Arquitetura B: pacote consolidado de preativação HML, evidências e rollback

**Data:** 17/11/2026  
**Estado:** CÓDIGO SOURCE-ONLY / REVISÃO DE EVIDÊNCIAS NÃO CONFIÁVEIS / ZERO INSTALAÇÃO  
**Issue canônica:** [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232)  
**Referências:** [decisão SEC-01..10](./43-atlas-hml-independent-security-decision-gate.md), [limites de sistema Linux](./42-atlas-hml-supervisor-blueprint-review.md), [teste real descartável](./47-atlas-hml-disposable-process-fd-boundary.md).

## 1. Estado real após as PRs #245, #251 e #253

O owner escolheu **arquitetura B como direção de desenvolvimento**, não para instalação. As três PRs de código/CI foram mescladas, com revisão separada por Cursor Composer 2.5 e `ACCEPT_WITH_RESIDUAL`; nenhuma OC obrigatória. A PR #253 comprovou em **runner descartável** um subprocesso `nobody` com UID/GID sem privilégio, grupos vazios e **FD UDS permitido em `pass_fds`**, e detectou um FD Docker conectado propositalmente herdado.

Isto **não é** prova de que a unidade `atlas-hml` real no servidor está isolada, nem que existe um produtor root autorizado ou que a origem de snapshots foi autenticada.

```text
Docker Engine compartilhado (alto risco)
                 |
                 v
  produtor curto / root / acesso Docker
      [NÃO INSTALADO; risco host-equivalente]
                 |
        snapshot JSON allowlisted
      [NÃO INSTALADO NO HOST]
                 |
                 v
   presenter sem Docker e sem FDs herdados
   [MÓDULO-FONTE; TESTADO SÓ EM RUNNER]
                 |
                 v
    socket UNIX com SO_PEERCRED
   [SEM SOCKET OPERACIONAL NO HOST]
                 |
                 v
  ATLAS quatro ferramentas MCP READ
      BLOCKED; PREPARE/ACT OFF
```

O próximo passo tecnicamente relevante é **coletar evidências reais em janela separadamente autorizada** e anexar parecer identificado. Mais testes CI não substituem esse gate.

## 2. O que este pacote desenvolve

O novo `atlas_hml_b_preactivation_evidence.py` interpreta **somente um índice JSON offline** de evidências SEC-01..SEC-10. Exige escopo fixo HML/Compose/serviço, dez linhas exatas, validação estrita de tipos, referências opacas, SHA-256 em minúsculas, origem permitida por gate e rejeição de campos não autorizados ou JSON duplicado. Uma referência ou hash **não comprova a autenticidade dos bytes ou a identidade do avaliador**.

- **Nenhuma leitura de arquivos evidenciados ou captura do host**: o módulo não tem comando, entrada de shell, Docker, systemd, rede, socket, filesystem, subprocesso, Keycloak, MCP, PREPARE ou ACT.
- A referência `EVID-...` precisa ser **única por gate**. A associação entre referência opaca e documento original é externa e precisa ser conferida em revisão humana, não presumida pelo parser.
- Os resultados `PENDENTE`, `REPROVADO` e `COMPROVADO` são **declarações enviadas pelo operador**, jamais veredictos do ATLAS. O nome `claimed_complete_items` registra apenas quais linhas foram **marcadas** como comprovadas.
- Para evitar contaminação de evidências, `SEC-03` (isolamento real de host) não aceita a origem `ci_disposable` como prova de host. A matriz de origens permitidas está no código-fonte e serve apenas para **triagem de documentação**.
- **Mesmo com dez declarações COMPROVADO**, a resposta é `status=blocked`; `independent_human_attestation=false`, `host_isolation_attested=false`, `operational_authorization_granted=false`, `prepare_eligible=false`, `can_execute=false`.

### Formato da declaração de evidência

Envelope exato: `schema=atlas.hml.architecture-b.preactivation-evidence.v1`, `source=operator_supplied_untrusted`, `architecture=B`, `environment=hml`, `compose_project=delpi-hml`, `service_id=public-hub`, `container_name=delpi-hml-public-hub`, `host_claim=srv-api`, `checks` com exatamente dez objetos.

Cada linha contém **somente**: `id` (SEC-01..SEC-10), `claimed_result` (`PENDENTE`, `REPROVADO`, `COMPROVADO`), `origin`, `evidence_ref` e `sha256`. Uma linha pendente exige `origin=not_provided`, e referência/digest `null`. Uma linha avaliada exige referência opaca `EVID-XXXXXXXX` e digest com 64 hexadecimais em minúsculas. O código recusa a adição de `can_execute`, `approved`, `operational_authorization_granted`, scripts ou outros campos.

As associações de proveniência para as dez linhas são:

| Gate | Origem documental que pode ser declarada no índice (NÃO atestada) | Evidência operacional ainda exigida |
|---|---|---|
| SEC-01 | `human_independent_claim` ou `governance_exception_claim` | Parecer humano identificável, ou exceção expressa do owner com riscos; uma exceção não é revisão independente |
| SEC-02 | `host_observation_claim` | Origem real do produtor privilegiado, cadeia de execução e limites Docker |
| SEC-03 | `host_observation_claim` | Prova negativa de Docker por path, FD, alias, ACL e rede no presenter REAL |
| SEC-04 | `host_observation_claim` | `systemd` real, UID/GID, grupos, capabilities, seccomp, MAC/LSM, namespaces e `NoNewPrivileges` |
| SEC-05 | `host_observation_claim` | Pais do UDS e snapshot root:grupo, modos/ACL, symlink e FD de socket activation |
| SEC-06 | `host_observation_claim` | Alvo HML exato, snapshot stale/adulterado/replay, falha do produtor, permissão falsa negada |
| SEC-07 | `host_observation_claim` | Ensaio de recuperação e rollback que preserva Docker e `delpi-public-hub` produção |
| SEC-08 | `independent_verifier_claim` | Veredito DELPI Verifier verificável da PR operacional, OCs fechadas e revisão de Segurança separada |
| SEC-09 | `change_authorization_claim` | Janela e autorização operacional explícitas, responsáveis e critérios de abortar |
| SEC-10 | `control_plane_claim` | Quatro tools MCP READ, Core/journal/S2S/backup segregados, PREPARE/ACT OFF |

> **Interpretação obrigatória:** uma linha `COMPROVADO` no JSON é apenas uma **afirmação**. A fonte, assinatura, revisão humana e autorização precisam ser validadas fora deste parser. O status permanece **BLOQUEADO** em todos os casos.

## 3. Checklist de análise Linux real, NÃO executado agora

Os itens a seguir são **plano de observação futura**, não comandos para executar no `srv-api` nesta etapa.

1. **Identidade e processo:** verificar conta dedicada `atlas-hml` sem login, UID/GID efetivos, grupos suplementares, capabilities e FDs do **processo criado pelo systemd**, não de `sudo -u`; validar fonte do executável e revisão implantada.
2. **Propriedades systemd:** comparar `User`, `Group`, `NoNewPrivileges`, `CapabilityBoundingSet`, `AmbientCapabilities`, `RestrictAddressFamilies`, `InaccessiblePaths`, `ReadOnlyPaths`, `ProtectSystem`, sandbox, LSM/MAC, `LoadState` e `ExecMainPID` da unidade **real**, com plano específico de teste negativo. A configuração de unidade não substitui observação do PID.
3. **Docker por múltiplos caminhos:** confirmar ausência de `/var/run/docker.sock`, `/run/docker.sock`, bind mounts/aliases, socket remoto, rota TCP/TLS e de **FD conectado herdado**. Apenas `chmod`, remoção de grupo ou `AF_UNIX` não provam ausência de acesso privilegiado.
4. **UDS e snapshot:** inspecionar todos os pais, UID/GID/modos, ausência de ACL estendida, symlink, hardlink e TOCTOU; confirmar root:`atlas-hml` em pai 0750, socket 0660 e snapshot 0640, e `SO_PEERCRED`.
5. **Target e limitações:** somente `delpi-hml-public-hub` de `delpi-hml`; documento sem credenciais/mounts/env; TTL e replay negados. NÃO tocar `delpi-public-hub` produção.
6. **Governança:** evidências com data e escopo, responsável identificável, hash e caminhos de verificação; remover segredos, tokens, nomes de pessoas e conteúdo indiscriminado de `/proc/*/environ` ou logs antes de anexar; nunca anexar Docker inspect bruto.

Antes de habilitar qualquer unidade, exigir revisão das **cinco** propostas `.review` em `linux-ops-mcp/review-only/`. Elas continuam **não instaláveis**, mantêm `ExecStart=/usr/bin/false`, não possuem `[Install]` e rejeitam ativação manual. **Não renomear ou instalar tais arquivos.**

## 4. Plano de rollback HML e critérios de interrupção

**Somente após aprovação SEC-01..10, change-control separado e janela registrada. Não executar agora.** O responsável deverá registrar previamente uma linha de base confiável e uma sequência testada que:

1. Identifique inequivocamente **somente** os novos processos/timer/socket/diretório ATLAS HML aprovados e o backup da configuração que possa ser revertida. Nunca confundir o serviço HML com Public Hub PROD.
2. Interrompa somente o novo produtor, o apresentador e seu timer/socket quando houver falha de identidade, FD Docker inesperado, snapshot malformado/stale, escalonamento ou falta de rollback confiável.
3. Revogue somente recursos novos e explicitamente inventariados, com revisão de ownership, permissões e mounts. Não removê-los por glob/limpeza automática, nem apagar snapshots sem evidência da necessidade.
4. **Jamais** reinicie o daemon Docker compartilhado, faça `docker rm`, reinicie `delpi-public-hub` produção, altere Compose PROD, Keycloak/DB/grants, habilite PREPARE/ACT ou use script de deploy genérico como medida de rollback.
5. Comprove que o status original dos sistemas e o baseline de produção não foram alterados. O rollback deve ser **ensaiado** em HML, com responsável, horário, resultado e evidência preservados.
6. Caso não seja possível encerrar os novos processos com segurança ou garantir não impacto: **parar a ativação**, preservar evidências mínimas sem segredos e escalar para Infra/Security. Não improvisar ações de root em Docker.

**Critérios de bloqueio imediato:** identidade não comprovada; qualquer FD/alias/caminho Docker inesperado no presenter; inconsistência de ACL/ownership; snapshot publicado com falha pós-rename sem comportamento seguro; perda de proveniência; evidência sem fonte; qualquer risco ao serviço de produção.

## 5. Critérios de aceitação desta PR e próximos gates

- **Agora:** código offline + testes negativos + workflow CI + este runbook + roadmap, em **uma única Draft PR**. Nenhum comando ou instalação no host.
- **Antes do merge:** 5/5 jobs CI e uma revisão DELPI Verifier separada **ao final deste pacote consolidado**, sem rodadas por commit.
- **Depois do merge:** a issue #232 permanece aberta. A próxima dependência real é autorização de uma coleta *somente leitura* específica no host, parecer de Segurança humano independente ou exceção formal de governança, e **nova decisão operacional** do owner.
- **Antes de qualquer piloto:** revisão da PR operacional executável, prova real no `srv-api`, rollback ensaiado e autorização de janela. O código e este documento não substituem SEC-01..10.

**A PR não muda runtime, servidor, usuários, grupos, root, serviços, Docker, Core, Keycloak, DB ou autorizações. PREPARE/ACT continuam desabilitados. Progresso ATLAS permanece 52% até evidência operacional real.**
