# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 11/11/2026 · **Estado:** Compose HML publicado; autorização operacional limitada aos **três PostgreSQL** de homologação após gates.  
> **Escopo:** coordenação de infraestrutura transversal; runtime HML ainda parcial (só bancos, se ativados).  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-COMPOSE-PUBLISH-AND-DATABASES-01`.  
> **Reancorar sempre** HEAD remoto/`main` antes de operar.

## 1. Objetivo e regras congeladas

Preparar um **ambiente de homologação independente**, na mesma VM VMware `srv-api`, para validar versões do Minha DELPI e plugins selecionados com usuários, sem interferir nos cadastros, bancos, credenciais, integrações ou containers produtivos.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- **Fluxo Git acordado:** editar/testar/commit/push no computador local; a VM recebe apenas Git `fetch` e `pull --ff-only` autorizados. Nada de commit/push na VM. Sem atualização automática da homologação.
- **Autorização desta rodada:** iniciar seletivamente apenas `postgres-core`, `keycloak-db` e `postgres-plugins` do projeto `delpi-hml`, após gates estáticos/segurança e publicação na `main`.
- **Proibido nesta rodada:** Keycloak, Core API, Portal, Production Control, gateway, migrations de apps, restore de dados produtivos, exposição na intranet.
- Bancos independentes; cópia de produção apenas por processo **controlado e sanitizado**, ainda não executado.
- Keycloak com **paridade de versão e contratos da produção**, mas instância, banco, credenciais, clients e sessões independentes; **não iniciar** Keycloak nesta etapa.

As instruções oficiais, `.cursor`, decisões/ADRs e implementação no HEAD atual têm precedência sobre este registro de continuidade (ver [índice documental](../README.md)).

## 2. Situação factual e evidências

| Frente | Estado | Evidência/limite |
|---|---|---|
| VM/produção | **PROVEN (11/11/2026)** | 16 vCPUs; ~47 GiB RAM; disco sistema ~394G (`/dev/sda2`); swap 8G em `/dev/sdb`; ~227G livres; swap 0B usado na medição pré-ativação. |
| Git SSH homologação | **PASS** | Deploy Key read-only `delpi-hml-readonly srv-api`; alias `github.com-delpi-hml`; checkout em `/home/operador/projetos-teste/delpi-central`. |
| Compose HML | **PUBLICADO / em integração** | Arquivos versionados: `infra/docker-compose.hml.yml`, `infra/env.hml.example`, `infra/scripts/hml-compose.sh`, `infra/scripts/tests/test_hml_compose_isolation.py`, `gateway/nginx.hml.conf`, `gateway/Dockerfile.hml` + docs. |
| Isolamento estático | **PASS** | `./infra/scripts/hml-compose.sh validate` → `HML_COMPOSE_ISOLATION=PASS`; profile `databases` = 3 serviços; `baseline` = 12; rede `delpi-hml-network`; volumes `delpi-hml-*`; `up --scenario baseline` recusado. |
| Keycloak HML | **PLANNED (não iniciado)** | Produção: `quay.io/keycloak/keycloak:24.0` digest `sha256:f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9`. HML pinna a mesma tag; issuer/hostname via `DELPI_HML_PUBLIC_HOST` (`hml.delpi.invalid` placeholder — **não** `127.0.0.1` permanente). |
| Bancos HML | **AUTORIZADO a iniciar (pós-pull)** | Somente via `./infra/scripts/hml-compose.sh up --scenario databases` com `infra/.env.hml` exclusivo. |
| Acesso por intranet | **PENDING** | Gateway/HTTPS ainda não ativados. |
| Runtime apps HML | **BLOQUEADO** | Sem Keycloak/Portal/APIs/gateway nesta rodada. |

### REUSE GATE

| Capacidade | Decisão |
|---|---|
| `docker-compose.yml` (prod) | **REUSE** via `extends` + `!override` |
| `up-prod-sequential.sh` | **EXTEND** padrão sequencial/`--no-deps` em `hml-compose.sh` |
| Deploy Key / checkout HML | **REUSE** |
| Novo Compose paralelo copiado | **NEW rejeitado** |

## 3. Arquitetura-alvo (parcialmente implantável)

| Componente | Produção | Homologação |
|---|---|---|
| Checkout | `~/projetos/delpi-central` | `~/projetos-teste/delpi-central` |
| Compose | Projeto `infra` | Projeto `delpi-hml` |
| Rede | `infra_delpi-network` | `delpi-hml-network` |
| Containers | Nomes globais produtivos | Prefixo `delpi-hml-` |
| Dados | Volumes atuais | Volumes `delpi-hml-*` |
| Gateway | Porta 80 | Planejado `127.0.0.1:18080` (não nesta etapa) |
| Integrações | Produtivas | Fail-closed |

### Limites de recurso (bancos HML)

| Serviço | mem_limit | cpus |
|---|---|---|
| postgres-core | 1g | 1.0 |
| keycloak-db | 768m | 0.5 |
| postgres-plugins | 1g | 1.0 |

## 4. Próxima fila

| Ordem | Entrega | Estado |
|---|---|---|
| 1 | Publicar Compose HML na `main` (local) | **EM CURSO** |
| 2 | `git pull --ff-only` no checkout HML | **PENDING** |
| 3 | Criar `infra/.env.hml` exclusivo (não versionado) | **PENDING** |
| 4 | `up --scenario databases` sequencial + health | **PENDING** |
| 5 | Verificar isolamento vs produção | **PENDING** |
| 6 | Keycloak / apps / gateway / restore sanitizado | **BLOQUEADO** (etapas futuras) |

## 5. Protocolo de retomada

1. Reancorar GitHub `main` e este documento.
2. Confirmar que só `delpi-hml-postgres-*` / `delpi-hml-keycloak-db` estão no escopo ativo.
3. Não iniciar Keycloak/apps sem nova autorização.
4. Não copiar `.env` de produção; não fazer push a partir da VM.

**STOP:** referência não autorizada a banco/volume/hostname/credencial produtiva; OOM ou degradação produtiva; qualquer `up` fora de `databases`.

## 6. Referências técnicas

- [Docker Compose](./docker-compose.md)
- [Ambientes](./ambientes-dev-prod.md) / `infra/README-ambiente.md`
- [Gateway Nginx](./gateway-nginx.md)
- [Bancos de dados](./bancos-de-dados.md)
- `.cursor/rules/platform-delivery-runtime-operations.mdc`, `local-first-deploy.mdc`, `infra-sequential-container-startup.mdc`
