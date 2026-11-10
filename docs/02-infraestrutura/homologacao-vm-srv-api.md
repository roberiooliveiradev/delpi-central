# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 10/11/2026 · **Estado:** PREPARAÇÃO, sem autorização para ativar containers.  
> **Escopo:** coordenação de infraestrutura transversal; não é comprovação de runtime nem aprovação do Compose.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **Referência Git da última verificação documental:** `main` em `1a2c217866bbe52db933330176b63d50493eb509` (referência histórica; reancorar sempre).

## 1. Objetivo e regras congeladas

Preparar um **ambiente de homologação independente**, na mesma VM VMware `srv-api`, para validar versões do Minha DELPI e plugins selecionados com usuários, sem interferir nos cadastros, bancos, credenciais, integrações ou containers produtivos.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- **Fluxo Git acordado:** editar/testar/commit/push no computador local; a VM recebe apenas Git `fetch` e `pull --ff-only` autorizados. Nada de commit/push na VM. Sem atualização automática da homologação.
- **Proibido até autorização explícita posterior:** `docker compose up/build/pull/down` e equivalentes, migrations, restores, importação de dados, criação/início de containers, exposição na intranet e mudanças na operação de produção.
- Bancos independentes; cópia de produção apenas por processo **controlado e sanitizado**, ainda não executado.
- Keycloak com **paridade de versão e contratos da produção**, mas instância, banco, credenciais, clients e sessões independentes; sem alterar cadastro produtivo.

As instruções oficiais, `.cursor`, decisões/ADRs e implementação no HEAD atual têm precedência sobre este registro de continuidade (ver [índice documental](../README.md)).

## 2. Situação factual e evidências

| Frente | Estado | Evidência/limite |
|---|---|---|
| VM/produção | **PROVEN por saída operacional fornecida** | VMware, Ubuntu 24.04.4, 16 vCPUs, ~24 GB RAM, 4 GB swap, disco 200 GB; 34 GB livres na medição de 10/11. Eventos OOM em 03–04/11. Não revalidado em tempo real aqui. |
| Git SSH homologação | **PASS relatado pelo Cursor; aceito como preparação** | Tarefa `HML-GITHUB-READONLY-CLONE-01`; Deploy Key `delpi-hml-readonly srv-api` (read-only), alias `github.com-delpi-hml`. `ssh -T` autenticou; `git ls-remote` retornou SHA; tentativa de `push --dry-run` foi negada. |
| Checkout HML | **PASS relatado pelo Cursor** | Clone em `/home/operador/projetos-teste/delpi-central`, `main`, limpo, no SHA histórico `1a2c217866bbe52db933330176b63d50493eb509`. Nenhum deploy. |
| Produção preservada | **PASS relatado pelo Cursor** | Remoto produtivo HTTPS inalterado; checkout produtivo ficou no SHA `1fa326f502...` durante a preparação, sem pull/deploy. |
| Docker HML | **PLANNED / WIP local; PENDING REVIEW** | Tarefas `HML-DOCKER-REANCHOR-AND-READONLY-GIT-01` e predecessora; arquivos preparados só na working tree local, **não integrados** à `main` nesta data. |
| Isolamento Compose | **PASS estático relatado, não auditado independentemente no diff** | Cenário `platform`: 10 serviços; `baseline`: 12; projeto `delpi-hml`, rede própria, imagens `delpi-hml/*:local`, única publicação `127.0.0.1:18080`; `up` bloqueado pelo script; nenhum container HML criado segundo a VM. |
| Keycloak HML | **PLANNED / PENDING** | Produção no Compose usa `quay.io/keycloak/keycloak:24.0` e `start`; digest de produção relatado `sha256:f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9`. Reconfirmar digest antes da ativação. Realm/client/usuários não provisionados. |
| Banco e dados HML | **PENDING** | Sem dump, sanitização, restore ou migrations. |
| Acesso por intranet | **PENDING** | Gateway só planejado em loopback. Hostname, HTTPS e proxy do host não definidos nem implantados. |
| Expansão da VM | **PENDING** | Solicitação/avaliação em andamento; alvo preliminar: 16 vCPUs, 48 GB RAM, 8 GB swap, 400 GB disco; **não é capacidade instalada nem dimensionamento validado**. |
| Runtime HML | **TEST_NOT_RUN / não autorizado** | Sem container, banco de teste ativo, login ou fluxo de negócio homologado. |

### Arquivos preparados localmente, ainda não publicados

`infra/docker-compose.hml.yml`, `infra/env.hml.example`, `infra/scripts/hml-compose.sh`, `infra/scripts/tests/test_hml_compose_isolation.py`, `gateway/nginx.hml.conf`, `gateway/Dockerfile.hml`; alterações em `.gitignore`, `infra/README-ambiente.md` e `docs/02-infraestrutura/docker-compose.md`.

**Atenção:** estes caminhos são relato do WIP local, não arquivos comprovadamente existentes no HEAD remoto. Não fazer `git clean`, `reset --hard` nem `pull` destrutivo sobre o WIP; preservar também alterações concorrentes.

## 3. Arquitetura-alvo (não implantada)

| Componente | Produção | Homologação proposta |
|---|---|---|
| Checkout | `~/projetos/delpi-central` | `~/projetos-teste/delpi-central` |
| Compose | Projeto `infra` | Projeto `delpi-hml` |
| Rede | `infra_delpi-network` | Rede exclusiva `delpi-hml-network` |
| Containers | Nomes globais produtivos | Prefixo exclusivo `delpi-hml-` |
| Dados | Volumes e bancos atuais | Volumes próprios, bancos isolados |
| Imagens build | Tags atuais | `delpi-hml/<serviço>:local` |
| Gateway | Produção exposta na porta 80 | Planejado `127.0.0.1:18080`, sem exposição externa por enquanto |
| Integrações | Produtivas | **Fail-closed**, sem TOTVS/Protheus, MyWEG, envios, schedulers e publicadores reais por padrão |

Cenário seletivo proposto: PostgreSQL Core/plugins/Keycloak, Redis, Keycloak, Core API, API DELPI, Portal, Plugin UI, gateway e, opcionalmente, Production Control MFE/API. Necessário conferir owners, consumidores, dependências e variáveis resolvidas no HEAD atual.

### Riscos críticos não resolvidos

1. **OIDC/navegador:** `http://127.0.0.1:18080/auth` só representa o loopback do próprio cliente; não funciona como issuer/redirect definitivo para computadores da intranet. Definir hostname HTTPS, redirect URIs, issuer, audiência, headers de proxy e build args do Portal antes de ativar usuários.
2. **Paridade Keycloak ≠ compartilhar identidade:** mesma versão/features da produção, mas banco, realm/client, secrets, cookies e sessões separados. Nenhuma mutação administrativa em produção para bootstrap de HML.
3. **Segurança dos dados:** testar configuração resolvida de TODAS as APIs e jobs, não só nomes de volumes; sem acesso de escrita à produção nem saída externa por padrão.
4. **Imagens Docker:** evitar tag produtiva, especialmente `infra-production-control-api`, potencialmente usada por publicadores MyWEG. Inspecionar também binds externos, `network_mode: host`, aliases, `extra_hosts` e dependências.
5. **Capacidade:** swap lotada e eventos OOM anteriores impedem ativação sem avaliação de recursos, limites e observabilidade.
6. **Revisão:** testes estáticos do executor não substituem diff review independente nem `nginx -t`; Nginx não estava disponível no ambiente usado nos testes.

## 4. Próxima fila — executar só mediante autorização pertinente

| Ordem | Entrega verificável | Estado |
|---|---|---|
| 1 | Reancorar WIP local no `origin/main` atual sem perder mudanças concorrentes e revisar **diff completo**, inclusive novos arquivos | **PENDING** |
| 2 | Corrigir contratos de URL/hostname/issuer OIDC e revisar fluxo futuro por HTTPS na intranet | **PENDING** |
| 3 | Confirmar isolamento efetivo de Compose, imagens, env, binds, volumes, DNS, auth e integrações; repetir testes estáticos | **PENDING** |
| 4 | Review independente do diff e aceite formal (`ACCEPT/REWORK/INCONCLUSIVE`) | **PENDING** |
| 5 | Publicar os arquivos HML **a partir do computador local** conforme branch/PR/merge governados; confirmar SHA integrado em `main` | **PENDING** |
| 6 | `git pull --ff-only` autorizado no checkout HML, sem deploy | **PENDING** |
| 7 | Confirmar ampliação da VM, capacidade e política de resource limits | **PENDING** |
| 8 | Preparar `.env.hml` seguro fora do Git, bancos, proteção de egress e processo sanitizado de dados | **PENDING** |
| 9 | Preparar Keycloak isolado e gateway HTTPS; revisar RBAC, URL pública e clients | **PENDING** |
| 10 | Autorizar expressamente a primeira subida seletiva, com smoke, logs, rollback e proteção da produção | **BLOQUEADO** |

O documento não autoriza execução dessas etapas. **Nenhum serviço HML deve ser iniciado neste momento.**

## 5. Protocolo de retomada para outro chat

1. Abrir este registro, [README de infraestrutura](./README.md), [Compose](./docker-compose.md), documentação de ambientes e autoridades vigentes.
2. Reancorar **GitHub branch padrão/HEAD remoto** e checar `git status`, divergência e ownership nas árvores local, produção e HML.
3. Confrontar cada status com código, diff, testes e runtime existentes; usar `PROVEN | TO_INVENTORY | PLANNED | TARGET` e testes `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN`.
4. Não converter relato do Cursor em prova de merge, deploy ou funcionamento. Reportar `EXECUTION_DRIFT` se a premissa atual divergir da evidência.
5. Confirmar o `TASK_ID` existente ou convenção vigente; não criar authorities paralelas.
6. Avançar só na próxima etapa autorizada; registrar base/final HEAD, arquivos, AC, testes, status de PR/merge, impactos, pendências e evidências aqui ao concluir.

**STOP:** qualquer tentativa de utilizar bancos/cadastros de produção, iniciar containers sem autorização, executar mutações por SSH na árvore de produção ou fazer commit/push a partir da VM.

## 6. Referências técnicas

- [Docker Compose](./docker-compose.md)
- [Ambientes dev/prod](./ambientes-dev-prod.md)
- [Gateway Nginx](./gateway-nginx.md)
- [Bancos de dados](./bancos-de-dados.md)
- [Variáveis de ambiente](./variaveis-de-ambiente.md)
- [Instruções oficiais do arquiteto](../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md)
- `.cursor/rules/platform-delivery-runtime-operations.mdc`, `local-first-deploy.mdc`, `infra-sequential-container-startup.mdc` e regras de segurança/identidade.

**Próxima ação autorizada no escopo técnico:** revisão do WIP Docker local; sem ativação.
