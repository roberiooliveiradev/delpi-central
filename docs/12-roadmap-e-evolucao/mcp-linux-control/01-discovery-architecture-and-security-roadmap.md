# Delpi MCP Linux Control — arquitetura, segurança e roadmap

> **Data da avaliação:** 2026-11-14  
> **Status:** `PROPOSED / DISCOVERY`. Este documento não instala, conecta, autoriza ou publica um MCP e não comprova estado operacional do `srv-api`.  
> **Ambiente-alvo:** Linux `srv-api`, checkout de produção `/home/operador/projetos/delpi-central`.  
> **Escopo da entrega inicial:** levantamento de código e documentação, desenho de segurança, inventário somente leitura e critérios de evolução. **Nenhuma mudança em Docker/Keycloak/host/CI neste PR.**

## 1. Objetivo e fronteiras

Criar um servidor MCP de operações de infraestrutura para o Delpi Central, capaz de fornecer diagnóstico de produção e, *após gates explícitos e verificados*, preparar/executar deploys **restritos e auditáveis**, sem transformar o modelo em administrador geral do servidor.

- **MCP:** interface conversacional e transport protocol, não autoridade operacional, não RBAC e não shell genérico.
- **Backend:** valida identidade, escopo, alvo, política e aprovação humana. A aprovação na interface do ChatGPT, isoladamente, não substitui a autorização da DELPI.
- **Executor:** componente local separado, com operações tipadas e whitelist. O servidor MCP nunca recebe acesso ao `docker.sock`, ao grupo `docker`, ao shell root ou a comandos arbitrários.
- **Código em produção:** nunca editar em SSH/container; alteração de código/infra versionada percorre branch → PR → CI → merge/push → deploy de revisão imutável, seguindo `.cursor/rules/local-first-deploy.mdc`.
- **Integração futura:** ChatGPT pode orquestrar MCPs em uma conversa. Para MCPs chamarem outros MCPs autonomamente, haverá necessidade de um **cliente/orquestrador** (candidato natural: DÉLIA) com revalidação das autorizações de cada destino. Nenhuma permissão transita automaticamente entre plugins.

## 2. Evidências verificadas no repositório (não equivalem a runtime)

| Componente | Evidência do repositório | Consequência |
|---|---|---|
| MCP reutilizável | `shared/delpi_mcp`, `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md` | Reutilizar auth, transport, identity, redaction, erros, metadata e contrato OAuth, sem copiar mecanismos |
| Keycloak e Core RBAC | `core-api/docs/mcp-providers.md`, `tv-dashboard-api/docs/integrations/openai-plugin-mcp.md` | Client/entidade de recurso dedicado, `mcp:tools` ≠ permissão para deploy |
| DÉLIA MCP registry e interop | `delia-api/scripts/real_mcp_interop_eval.py`, Core `/integrations/mcp-providers/eligible` | Cadastro de provider exige revisão; elegibilidade ≠ autorização de chamada |
| Docker produção | `infra/docker-compose.yml` | Não criar quarto compose; preservar normas de env, gateway e profile |
| Script de deploy | `infra/scripts/up-prod-sequential.sh` | Ordem sequencial, `--dry-run`, filtro por serviço e espera de PG existem; **não comprovam** health integral/rollback automático |
| Homologação | `infra/docker-compose.hml.yml`, `infra/scripts/hml-compose.sh` | Stack isolada existe como configuração; habilitação/saúde real precisam ser constatadas |
| Normas de segurança | `.cursor/rules/platform-delivery-runtime-operations.mdc`, `.cursor/rules/secret-handling-diagnostics-safety.mdc` | Não imprimir secrets, `docker inspect` com env ou configs integrais; não fazer hotfix direto no servidor |

### Riscos identificados para o agente

1. **`git pull` sem referência imutável:** o script `up-prod-sequential.sh` chama `git pull`; o fluxo do agente não pode usar HEAD flutuante ou deploy automático de alterações não aprovadas. Exigir SHA exato, checkout limpo, fast-forward, consistência com PR/CI e garantia de que a versão implantada é a aprovada.
2. **Ausência de gate genérico de saúde/rollback no script inspecionado:** o script espera PostgreSQL e verifica upstreams estáticos do gateway em alguns casos, mas uma saída zero não comprova saúde funcional de cada API. Criar verificação por serviço e política de reversão/roll-forward.
3. **Repo público:** metadados do GitHub indicam `visibility=public`. Proibir segredos, IPs internos sensíveis, token, credencial, inventário detalhado, dumps e diagnósticos crus no Git. Revisar segregação de repositório público para código e componentes operacionais privilegiados; considerar repositório privado separado para executor e artefatos sensíveis. Uma mudança de visibilidade é decisão administrativa, não parte deste PR.
4. **Docker implica alto privilégio:** acesso ao socket ou grupo `docker` costuma equivaler a acesso administrativo ao host. Nunca expor isso como ferramenta do MCP.
5. **Prompt injection/tool output:** logs, issues, PRs, respostas do terminal e arquivos do repositório são dados não confiáveis; não podem alterar a política do executor ou autorizar operações.

## 3. Opções de conexão investigadas

| Alternativa | Uso | Decisão inicial |
|---|---|---|
| **OpenAI Secure MCP Tunnel** (`tunnel-client`) | Conexão de saída HTTPS do host/rede à OpenAI, encaminhamento privado sem abrir porta de entrada | **Preferência para piloto privado**, condicionada a permissões Platform/ChatGPT, associação ao workspace, runtime key segura e disponibilidade |
| Gateway HTTPS do portal + Keycloak OAuth | Publicação estável de `/apps/<servico>/mcp`, equivalente à família TÉO/VISTA | **Fallback / opção de publicação estável**, com autenticação OAuth, audience exata, mTLS do cliente quando aplicável e hardening do gateway |
| Tailscale Serve | Acesso entre pares autorizados da tailnet | Útil para administração ou cliente MCP na tailnet, **não** presumir acessibilidade do ChatGPT cloud |
| SSH exposto, Tailscale Funnel sem controle, MCP com `shell(cmd)`, executor com `docker.sock` | Caminhos de privilégios amplos | **Rejeitados** para o agente de produção |

Fontes oficiais consultadas em 2026-11-14:
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://help.openai.com/pt-br/articles/12584461-connecting-custom-mcp-servers-in-chatgpt
- https://developers.openai.com/plugins/build/mcp-server
- https://developers.openai.com/plugins/build/auth
- https://blog.modelcontextprotocol.io/posts/2026-07-28/
- https://docs.github.com/en/actions/reference/security/secure-use
- https://tailscale.com/docs/features/tailscale-serve

**Túnel não elimina OAuth/RBAC.** O `tunnel-client` autentica o canal e permite descoberta/autenticação do MCP, mas a identidade do operador, autorização de negócio e gates de deploy ainda pertencem ao backend DELPI. O authorization server (Keycloak) precisa ser acessível para os fluxos OAuth; não é automaticamente exposto pelo túnel.

## 4. Topologia lógica proposta

```text
ChatGPT + MCPs de desenvolvimento
         |
         | chamadas tipadas (sem shell(cmd))
         v
Secure MCP Tunnel (piloto) OU HTTPS gateway protegido
         |
         v
delpi-linux-mcp (ASGI / Streamable HTTP)
  - valida user token Keycloak: iss, aud dedicada, scope, exp e subject
  - revalida Core /me e permissão do usuário a cada operação sensível
  - valida schemas, rate limits, timeout, alvo e classificação
  - logs estruturados e saída sanitizada; sem Docker socket
         |
         v
Policy/approval service + journal transacional
  - PENDING / PREPARED / APPROVED / EXECUTING / VERIFIED / FAILED
  - proposal hash, target SHA, service allowlist, TTL, idempotency key
  - aprovação nominativa (e segunda aprovação para serviço crítico)
         |
         v
Executor local separado (systemd / socket Unix restrito)
  - interface estritamente enumerada
  - código e scripts imutáveis, não graváveis pelo chamador
  - mínimo privilégio e exclusão mútua por serviço
  - único componente habilitado a operar Docker via boundary controlada
         |
         v
GitHub commit pinado → CI verde → rollout sequencial isolado
         → health verificável → evidência → rollback/roll-forward
```

**Escolha de implantação:** no piloto, preferir MCP unprivileged separado, como processo/contêiner sem acesso ao socket Docker nem montagens de `infra/.env`; executor **não** habilitado. Ao evoluir, usar um broker de host com validação rigorosa e não exportar o executor na rede. O tipo concreto (serviço host / contêiner / VM de administração) depende do inventário de host e controles disponíveis.

## 5. Catálogo de ferramentas por nível

| Ferramenta MCP candidata | Nível | Comportamento e limites |
|---|---|---|
| `get_host_health` | READ | CPU, memória, disco e tempo de atividade sanitizados, sem IP público/segredo |
| `list_managed_services` | READ | Estado e health apenas de serviços cadastrados, nenhuma exploração de Docker |
| `get_deployment_revision` | READ | SHA de Git aprovado, revisão em execução, desvio detectado, sem conteúdo de env |
| `get_service_health` | READ | Health HTTP interno previamente cadastrado, timeouts e limites |
| `get_service_diagnostics` | READ restrito | Catálogo limitado de erros agregados sanitizados; logs brutos ficam fora do escopo inicial |
| `preview_deployment` | PREPARE | Alvo `service_id` e `commit_sha` imutável; diff/CI/impacto/migrações/rollback; zero mudança |
| `request_deployment_approval` | PREPARE | Proposta selada, ator, revisão, serviços, janela, expiração e riscos, auditáveis |
| `deploy_approved_revision` | ACT | Apenas `proposal_id` aprovado; server-side approval, Core RBAC, estado esperado e SHA revalidados |
| `get_deployment_status` | READ | Progresso, health, evidências e resultado sem informações sensíveis |
| `request_rollback` / `execute_rollback` | PREPARE / ACT | Contrato específico, com veto se migração/schema impedir rollback binário seguro |

**Proibidos:** `execute_shell`, `run_command`, `docker_exec`, `sudo_any`, `write_file`, SQL livre, `git reset --hard` remoto, edição manual no host e chamadas arbitrárias a URLs internas.

## 6. Política e máquina de estados

```text
DISCOVER → PLAN → PREPARED → HUMAN_APPROVED → EXECUTING
                                     ├→ VERIFIED (smoke, métricas, SHA)
                                     ├→ ROLLED_BACK (apenas se seguro)
                                     └→ FAILED_NEEDS_OPERATOR
```

Gates executados **no backend**, não só pelo modelo:

1. Identidade do Keycloak com MFA quando exigida, audience MCP exata e `mcp:tools`; permissão `linux_ops.view` para leitura e `linux_ops.deploy.prepare`/ `linux_ops.deploy.execute` separadas no Core (nomes candidatos, não cadastrados).
2. Integridade do Git: workspace limpo, SHA de commit publicado e aprovado, HEAD esperado, imagens/artefatos com identidade verificável; rejeitar mudança de SHA entre PREPARE e ACT.
3. CI e revisão: PR aceito, testes pertinentes, aprovações/branch protection e verificação de artefato. **Não instalar self-hosted GitHub Actions runner com privilégios de deploy no repositório público**.
4. Política operacional: alvo cadastrado, aprovação explícita com ator autorizado, tempo de expiração curto (p.ex. 10 min), idempotência, lock, janela de manutenção quando cabível, quotas.
5. Preflight: memória/disco livres, saúde das dependências, snapshot/backup conforme risco, avaliação de migrations e plano de rollback/roll-forward.
6. Deploy: um serviço por vez, limite de recursos, timeout; idealmente imagem testada e identificada por digest (etapa futura), sem build indiscriminado em produção.
7. Postflight: readiness + smoke autenticado quando necessário, versão/commit em execução, erro/latência e smoke de rota; registrar prova. Se falhar, rollback só quando comprovadamente seguro, caso contrário bloquear e escalar.
8. Auditoria independente e imutável no sentido de não editável pelo MCP: `request_id`, subject, tool, arguments sanitizados, proposal hash, SHA, serviço, timestamps, decisão, executor, exit code, health, outcome.

## 7. Ordem de implementação e critérios de saída

| Fase | Entregável | Gate |
|---|---|---|
| **P0 — Discovery** | Este documento + inventário real do Linux sem secrets + ADR transporte/permissões | Inventário validado; desenho aceito |
| **P1 — READ-ONLY** | `delpi-linux-mcp` isolado + OAuth e 4 ferramentas READ + testes negativos + conexão tunnel em ambiente piloto | Chamada autenticada ChatGPT comprovada, sem writes |
| **P2 — GOVERNANCE** | Core permissions, propostas seladas, journal, aprovação nominativa, bloqueios e testes de concorrência | PREPARE não altera produção; ACT sem autorização retorna deny |
| **P3 — HOMOLOGAÇÃO** | Executor allowlisted + deploy de serviço não crítico no `delpi-hml`, smoke e reversão ensaiada | CI/health/rollback evidenciados |
| **P4 — PROD PILOT** | Deploy opcional de um serviço não crítico após change approval e backup | Operador confirma saúde; fail-close real em falhas |
| **P5 — INTEROP** | Conectar ao DÉLIA/ChatGPT com outros MCPs mediante delegação e políticas por ferramenta | Uma permissão em outro MCP nunca autoriza deploy por si só |

### Matriz mínima de testes negativos

- Token ausente/inválido/expirado, issuer errado, aud de outro MCP, role revogada → negar.
- Tentativa de `service_id` desconhecido, caminho arbitrário, shell metacaracter, alteração de Docker socket, exfiltração via logs → negar/sanitizar.
- Commit SHA mudou após aprovação, PR não aprovado, build CI falhou, branch divergente, repo sujo → negar.
- Duas chamadas de deploy idênticas simultâneas → executar no máximo uma vez; sem duplicar.
- Saúde degradada, dependência falha, migração incompatível, sem capacidade de rollback → bloquear ou exigir aprovação adicional, nunca marcar VERIFIED sem prova.
- Executor, Core, túnel ou Keycloak indisponíveis → fail closed.
- Revogação do usuário **entre** PREPARE e ACT → negar.
- Evidências sensíveis nunca aparecem em tool results, GitHub, prompts ou trace.

## 8. Inventário inicial solicitado ao operador (SOMENTE LEITURA)

Execute no `srv-api`. **Não enviar .env, tokens, senhas, chaves privadas, `docker inspect` integral, `docker compose config` integral, `printenv` ou conteúdo de logs brutos.** A coleta abaixo não altera serviços.

```bash
hostnamectl --no-pager | head -n 12
uname -r
whoami
id
docker --version
docker compose version
python3 --version
free -h
df -h / /var/lib/docker
systemctl is-active docker ssh tailscaled 2>/dev/null || true
cd /home/operador/projetos/delpi-central
git status --short --branch
git rev-parse HEAD
git branch --show-current
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

**Sanitização antes de compartilhar:** substituir nomes de usuários sensíveis, paths não relacionados e identificadores de acesso. `id` mostra grupos: usá-lo para avaliar risco; não conceder `docker` ao MCP. **Estado operacional de homologação, tipo de autenticação SSH e disponibilidade do Secure MCP Tunnel ainda são `TO_VERIFY`.**

## 9. Dependências e decisões abertas

- [ ] Confirmar CPU/RAM, SO, Docker/Compose, Git, systemd, Tailscale e identidade/privilégios no `srv-api` (sem secrets).
- [ ] Confirmar onde rodará o MCP unprivileged e a fronteira real do executor.
- [ ] Confirmar disponibilidade do Secure MCP Tunnel no Platform e associação ao workspace ChatGPT; `tunnel-client` exige runtime API key armazenada **somente** no host/secret manager. Não registrar valor em chat/git.
- [ ] Escolher a identidade humana/serviço para Core permissions; definir segundo aprovador para produção crítica.
- [ ] Inventariar saúde da homologação; não assumir que serviços críticos estão disponíveis.
- [ ] Identificar serviço não crítico piloto, checks de saúde por serviço e estratégia de rollback de cada classe de migration.
- [ ] Decidir política para código público vs executor/artefatos sensíveis privados.
- [ ] Avaliar resposta a incidentes: revogação imediata de token/túnel, parada do executor e trilha de auditoria.
- [ ] Definir onde o orquestrador entre MCPs executará e como delegará tokens por audience.

## 10. Registro de execução

| Data | Ação | Estado | Evidência |
|---|---|---|---|
| 2026-11-14 | Leitura da infraestrutura MCP, Core, DÉLIA, script de deploy e regras de operação | `SOURCE_REVIEWED` | Caminhos vinculados acima |
| 2026-11-14 | Pesquisa de Secure MCP Tunnel, OAuth, GitHub Actions e Tailscale | `OFFICIAL_DOC_REVIEWED` | URLs na seção 3 |
| 2026-11-14 | Publicação deste documento em branch de documentação | `DOC_PROPOSED` | PR de documentação |
| 2026-11-14 | Execução de comandos no `srv-api` | `NOT_DONE` | Aguardando inventário autorizado |
| 2026-11-14 | MCP, conexão ChatGPT, alteração de produção, autorização Keycloak, CI e deploy | `NOT_DONE` | Não afirmar implementação |

**Regra de manutenção:** cada etapa futura deve atualizar este documento (ou registro de evidências ligado) com versão, arquivos, testes executados/não executados, decisão, riscos residuais e read-back real. Não confundir `DOC_PROPOSED`, `CODE_IMPLEMENTED`, `TEST_PASSED` e `PRODUCTION_VERIFIED`.


## 11. Inventário operacional recebido do operador (2026-11-14)

> **Proveniência:** saída de comandos fornecida pelo operador humano no terminal do `srv-api`. **Não houve conexão SSH/MCP do assistente nem execução remota.** Este registro evita dados identificadores e não expõe credenciais no GitHub público.

| Categoria | Evidência sanitizada | Interpretação |
|---|---|---|
| Kernel / runtime | Linux `6.8.0-147-generic`, Docker `29.2.1`, Compose `v5.0.2`, Python `3.12.3` | Base apta a um pequeno processo MCP; distribuição Linux exata ainda `TO_VERIFY` |
| Capacidade | RAM total ~47 GiB, disponível ~25 GiB; espaço livre ~210 GiB (ocupação ~45%) | Não indica necessidade imediata de novo host; considerar concorrência com os serviços em produção |
| Serviços | Docker, SSH e Tailscale `active` | Canal de manutenção existente; não presumir que o canal MCP já está disponível |
| Infra existente | Vários contêineres de produção e `delpi-hml-*` em execução no **mesmo host** | Homologação não possui isolamento físico. Limitar CPU/RAM/IO de testes; não executar builds massivos |
| Saúde dos contêineres | Diversos contêineres reportaram `healthy`; outros `Up` sem indicação de healthcheck | Ausência de `unhealthy` na listagem não prova saúde funcional de todos os serviços |
| Identidade atual | Operador humano membro dos grupos `sudo` e `docker` | **Bloqueio de privilégio:** não executar MCP nem túnel como usuário humano; criar identidade restrita sem `sudo`/`docker` |
| Repositório local | `main`, SHA `aeba1d71314747a05cc13f11e95ec9054f7ebe5b`; arquivo `shared/delpi_auth.egg-info/SOURCES.txt` modificado | **Checkout não limpo.** Não executar pull/checkout/reset/restore/deploy; investigar origem da alteração e comparar remoto |
| Comando de SO | `hostnamectl --no-pager` não aceito pela versão instalada | Usar `grep '^PRETTY_NAME=' /etc/os-release` para identificar distribuição, sem elevar privilégios |

### Diagnóstico complementar permitido, somente leitura

```bash
grep '^PRETTY_NAME=' /etc/os-release
nproc
docker ps -q | wc -l
docker ps --filter 'health=unhealthy' --format '{{.Names}}:{{.Status}}'
docker ps --filter 'health=starting' --format '{{.Names}}:{{.Status}}'
cd /home/operador/projetos/delpi-central
git diff --numstat -- shared/delpi_auth.egg-info/SOURCES.txt
git status --porcelain=v1 -uno
git rev-parse HEAD
git rev-parse origin/main
command -v tunnel-client || true
```

**Importante:** `origin/main` é uma *referência local* e pode estar desatualizada. Comparar com GitHub remoto usando ferramenta GitHub autorizada antes de promover qualquer revisão. Os comandos acima não incluem `git fetch`, pull, stop, restart, build ou alterações em arquivos.

### Decisões confirmadas depois do inventário

1. `P0-HOST-CAPACITY`: **PASS parcial** para hospedagem de MCP leve, sem benchmark de latência ou cgroup e sem reserva formal de recursos.
2. `P0-HOST-IDENTITY`: **REQUIRES_SEPARATE_UNPRIVILEGED_SERVICE_ACCOUNT**.
3. `P0-PRODUCTION-GIT`: **BLOCKED_DIRTY_WORKTREE** para qualquer procedimento que presuma checkout limpo e commit fixo.
4. `P0-HML`: **RUNTIME_PRESENT / ISOLATION_PARTIAL**. Testes limitados e agendados, com no-op na produção.
5. `P0-TUNNEL`: **NOT_CONFIGURED / TO_VERIFY**. Nenhuma API key, tunnel ID ou cliente foi instalado; verificar permissões e vínculo de workspace antes de habilitar.
6. `P1-READ_ONLY`: **NOT_STARTED**; só prosseguir com identidade, autenticação, isolamento e saída sanitizada.

### Registro de atualização

| Data | Tipo | Estado |
|---|---|---|
| 2026-11-14 | Inventário real recebido do operador, analisado e sanitizado para o GitHub público | `HOST_BASELINE_PARTIAL` |
| 2026-11-14 | Precondições para P1: conta isolada, nenhuma permissão Docker, sem shell genérico | `SECURITY_DESIGN_REQUIRED` |
| 2026-11-14 | Acesso remoto MCP, instalação do túnel, deploy e testes autenticados | `NOT_DONE` |


## 12. Complemento do inventário e decisão de reuso (2026-11-14)

- Host: Ubuntu 24.04.4 LTS, 16 CPUs lógicas; 135 contêineres em execução. Filtros Docker `health=unhealthy` e `health=starting` sem retornos. Isso não prova saúde de todos os containers (muitos sem healthcheck).
- Checkout de produção: `HEAD=aeba1d71314747a05cc13f11e95ec9054f7ebe5b`; referência `origin/main` local = `eed8351fed4658b8dbcf8528d3851feec71a3a89`. Essas referências não provam estado remoto atual. O arquivo `shared/delpi_auth.egg-info/SOURCES.txt` permanece modificado (uma linha adicionada), então não fazer reset/restore/pull/deploy automático.
- `command -v tunnel-client` não retornou executável no PATH. Não há comprovação de instalação do túnel.
- Novo reuse gate: `it-portal-api/collectors/linux_host` e a API autenticada GET `/servers/{server_id}/observations/latest` já implementam coleta/consulta de observações com RBAC. Reusar; não duplicar coletor e não conceder Docker socket ao MCP. Instalação/execução automática do coletor e presença de observações no banco ainda exigem read-back de produção.
- Candidato P1: PR #185, 4 ferramentas MCP somente leitura e testes estáticos propostos. Estado **CODE_CANDIDATE / TEST_NOT_RUN / NOT_DEPLOYED**; revisão Git implantada permanece **not_available**, nunca inferida do GitHub HEAD.
- Gate P1 pendente: checkout+testes com dependências, revisão de segurança, observação real, escolha de transporte, Keycloak/Core permissions, smoke autenticado ChatGPT. Nenhum deploy autorizado nesta etapa.


## 13. Gate do coletor Linux em producao (evidencia recebida em 2026-11-14)

**Fonte:** saida enviada pelo operador humano da sessao no `srv-api`; nenhuma chamada SSH/MCP do assistente executada.

| Verificacao | Resultado observado | Conclusao |
|---|---|---|
| `systemctl is-enabled it-portal-linux-collector.timer` | `enabled` | Agendamento configurado para iniciar automaticamente |
| `systemctl is-active it-portal-linux-collector.timer` | `active` | Timer carregado e em execucao no systemd |
| `systemctl is-active it-portal-linux-collector.service` | `inactive` | **Esperado entre disparos para unit Type=oneshot**; nao prova que houve ultimo `submit` bem sucedido |
| Diretorio instalado | `/opt/delpi/it-portal-collector` propriedade `root:root` | Raiz da arvore protegida; ownership dos arquivos/venv e hardening ainda exigem verificacao especifica |
| Usuario tecnico | `delpi-collector` com somente grupo homonimo, sem `sudo`/`docker` na evidencia | Limite de privilegios do coletor preservado na conta verificada; consulta Docker pode vir `partial` ou `unavailable` |

**Confirmacao de configuracao por leitura do codigo:** `it-portal-api/collectors/linux_host/deploy/it-portal-linux-collector.service` declara `Type=oneshot` e executa `run-collector submit` sob `User=delpi-collector`; `it-portal-linux-collector.timer` declara `OnCalendar=hourly`, `RandomizedDelaySec=5m`, `Persistent=true`. Isso nao confirma que o arquivo unit em disco e identico ao versionado, nem confirma ultimo resultado.

### Proximo gate, sem modificacao de producao

```bash
systemctl list-timers --all it-portal-linux-collector.timer --no-pager
systemctl show it-portal-linux-collector.service \
  -p Type -p Result -p ExecMainCode -p ExecMainStatus \
  -p ExecMainStartTimestamp -p ExecMainExitTimestamp --no-pager
systemctl show it-portal-linux-collector.timer \
  -p ActiveState -p LastTriggerUSec -p NextElapseUSecRealtime --no-pager
```

Na interface autenticada do Portal de TI, verificar em **Servidores > srv-api > Observacoes** se existe ultima amostra com `observed_at` recente, `status` e `sections_status` esperados. A consulta no MCP so sera util se a API possuir uma amostra persistida e o token do usuario tiver permissoes `it-portal.access` e `it-portal.servers.view`.

**Pendencias:** data/hora da ultima disparo, `Result`/`ExecMainStatus`, sucesso do POST S2S, observacao confirmada em banco/UI, integridade da arvore root-owned, testes unitarios funcionais do candidato MCP, Keycloak/resource audience e transporte MCP autenticado. **Nao alterar timer, nao forcar start, nao conceder grupo Docker, nao fazer pull/deploy.**

**Codigo P1:** PR #185 integrado a `main` com commit `3fce4744104f404f0ab75b58434cb8a06e4cfecd`; estado `CODE_MERGED / NOT_DEPLOYED / MCP_RUNTIME_NOT_VERIFIED`. O PR #184 mantem a documentacao separada ate merge.


## 14. Evidencia do ultimo disparo do coletor (operador, 2026-11-14)

Amostra de saida `systemctl list-timers` e `systemctl show` do `srv-api`, recebida do operador na conversa. Nenhum comando remoto foi executado pelo assistente.

| Verificacao | Evidencia | Classificacao |
|---|---|---|
| Timer | `ActiveState=active` | PASS, agendamento ativo |
| Ultimo disparo | `2026-11-15 01:04:21 UTC` (14/11 22:04:21 America/Sao_Paulo) | PASS, disparou |
| Proximo evento | `2026-11-15 02:04:59 UTC` (14/11 23:04:59 America/Sao_Paulo) | Programado, nao executado ainda |
| Servico oneshot | `Type=oneshot`, `Result=success`, `ExecMainCode=1` (process exited), `ExecMainStatus=0` | PASS, ultimo processo terminou sem erro |
| Ingestao persistida | Ainda nao confirmado pela UI/API nem leitura de `it_portal.server_observations` | PENDING |

**Interpretacao do codigo:** `it-portal-api/collectors/linux_host/submit.py` invoca HTTP POST e retorna exit code zero apos uma resposta HTTP nao tratada como erro e JSON parseavel; HTTPError e URLError saem por `SystemExit`. Portanto o status 0 torna plausivel um POST aceito, mas **nao** substitui consulta independente ao ultimo registro persistido. O wrapper `run-collector.sh` usa `exec` e `set -euo pipefail`.

**Proximo gate seguro:** Portal de TI autenticado > Servidores > srv-api > Observacoes/ultima coleta. Registrar apenas `observed_at`, `presentation_status`, `source`, resumo `sections_status` e `run_id` se apropriado; nao compartilhar payload integral, IPs ou secrets. Exigir status de coleta recente e consistente com disparo do timer. Se houver observacao, validar se status Docker `partial/unavailable` e esperado para conta sem grupo `docker`. Nao conceder privilegios adicionais para artificialmente completar o snapshot.

**Estado:** `COLLECTOR_TIMER_PASS`, `COLLECTOR_PROCESS_EXIT_PASS`, `OBSERVATION_PERSISTENCE_NOT_VERIFIED`, `LINUX_OPS_MCP_NOT_DEPLOYED`.


## 15. Autorizacao do owner e PR P1-R2 (2026-11-14)

**Decisao explicita do operador:** confirma que a coleta automatica Linux ja funciona e autoriza avancar. Nao repetir a comprovacao da ingestao como prerequisito de desenvolvimento. **Limite de evidencia:** validacao declarada pelo operador; nao representa conectividade MCP ou autenticacao ChatGPT.

**Implementacao proposta em PR #186 (P1-R2), sem deploy:**

- Runtime Python isolado, usuario sem privilegios, imagem/Compose canonico sob profile opt-in `linux-ops` (nenhuma porta publicada, nenhum bind host, nenhum socket Docker, filesystem read-only, recursos limitados e health local).
- Autorizacao por usuario humano com `mcp:tools` e resource audience exata, Core RBAC com `force_refresh=True` em cada chamada; negacao se Core indisponivel ou subject divergente.
- Projecoes de inventario limitadas ao server_id do srv-api, sem dados de rede ou secrets, com stale/partial explicitos.
- Pipeline GitHub Actions dedicado: suite unit/negative tests, import MCP/tool inventory, Docker build. Status `CI_PENDING`, nao afirmar PASS antes de conferir o workflow.
- Configuracao externa OAuth Keycloak, gateway/tunnel e runtime produtivo **nao executados**. Profile opcional nao e autorizacao para publicar.

**Proxima sequencia:** CI/review P1-R2 -> opcao de transporte (Tunnel ou gateway) -> provisionamento OAuth dedicado com audience e callback reais -> smoke autenticado /mcp -> so depois classificar P1 `RUNTIME_VERIFIED`. Nunca fazer `git pull` destrutivo no checkout sujo, nem rebuild global de producao.

**Rastreamento:** PR #185 (codigo P1 ja merged na main), PR #186 (endurecimento/runtime pendente), PR #184 (documentacao em revisao). Nenhum deploy ou alteracao no `srv-api` realizado pelo assistente nesta etapa.


## 16. CI P1-R2 confirmado (2026-11-14)

PR #186, head `02dd50ad8c755557b473ab1a78e348696a9fbfc3`:

- GitHub Actions Architecture Enforcement run `43662826514`: `SUCCESS`.
- GitHub Actions Linux Ops MCP Readonly Tests run `43662826533`: `SUCCESS`.
- Passaram install shared, compile, unit tests e AuthZ negativos, catalogo das 4 tools MCP e `docker build` da imagem isolada.
- Todos os resultados sao de **runner CI**, nao de execucao no `srv-api` nem de OAuth/ChatGPT. A imagem nao foi publicada/iniciada na producao.
- Gate para merge de PR #186: revisao do diff, politica de branch e aprovacao do responsavel. Nao fazer merge ou deploy automaticamente apenas porque o CI passou.

**Status:** `P1-R2 CI_PASS / SOURCE_IN_PR / RUNTIME_NOT_DEPLOYED / AUTHN_NOT_PROVEN_LIVE`.
