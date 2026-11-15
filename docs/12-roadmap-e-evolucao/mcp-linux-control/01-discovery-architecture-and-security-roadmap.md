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
