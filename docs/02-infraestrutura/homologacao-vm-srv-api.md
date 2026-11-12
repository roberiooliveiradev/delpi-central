# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 12/11/2026 · **Estado:** HTTP LAN parametrizado; Keycloak HML autorizado a iniciar após publish; gateway/apps **não** iniciados.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-HTTP-KEYCLOAK-01`.  
> **BASE_HEAD (reancoragem):** `98e7657d4c311d14d7b1d3978d6b8930e98729b4` (`origin/main`).  
> **SHA integrado:** *preencher após push* (compose HTTP + Keycloak).

## 1. Objetivo e regras congeladas

Ambiente de homologação independente na mesma VM `srv-api`, sem interferir em produção.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- Git: commit/push só no computador local; VM apenas `git pull --ff-only`.
- **Autorizado nesta rodada:** configurar HTTP LAN, publicar, iniciar **somente** `delpi-hml-keycloak`, bootstrap mínimo de realm/client/usuário de teste.
- **Ainda proibido:** gateway HML, Portal, Core API, Production Control, restore sanitizado, HTTPS/intranet pública, exposição internet.

## 2. Inventário de portas (leitura — 12/11/2026)

IP LAN confirmado: **192.168.1.237/24** (`ens192`).

| Bind | Porta | Responsável (amostra) | Finalidade |
|---|---|---|---|
| 0.0.0.0 / :: | 80 | `delpi-gateway` + nginx host | Produção HTTP |
| 0.0.0.0 | 443 / 8443 | nginx host | Produção TLS / auxiliar |
| 0.0.0.0 | 22 | sshd | Administração |
| 0.0.0.0 | 5432 | Postgres host (não HML) | Serviço externo/local |
| 0.0.0.0 | 8080 | `inventario-ti-glpi-1` | GLPI |
| 0.0.0.0 | 8082/8083/8085 | PAC nginx / Evolution | Outros produtos |
| 0.0.0.0 | 11434 | `delpi-ollama` | Ollama |
| 127.0.0.1 | 18088 | `controle-mp-prod-front` | Controles MP |
| 127.0.0.1 | 3000 / 8001 | api-delpi local / aux | Loopback |
| — | **18080** | **livre** (IPv4/IPv6) | **Reservada HML** |

Decisão: entrada única HML = `http://192.168.1.237:18080` (sem HTTPS nesta fase). Não publicar portas de Postgres/Keycloak/APIs HML no host.

Firewall UFW: sem regras verbosas retornadas na coleta; acesso permanece na LAN/Tailscale existentes — não abrir internet.

## 3. Configuração OIDC / HTTP

| Variável | Valor de exemplo (`.env.hml` / example) |
|---|---|
| `DELPI_HML_BIND_ADDR` | `192.168.1.237` |
| `DELPI_HML_PUBLIC_ORIGIN` | `http://192.168.1.237:18080` |
| `KC_HOSTNAME` / `KC_HOSTNAME_PORT` | `192.168.1.237` / `18080` |
| `KC_HOSTNAME_STRICT_HTTPS` | `false` |
| `KC_PROXY` | `edge` |
| `KEYCLOAK_ISSUER` | `http://192.168.1.237:18080/auth/realms/delpi` |
| `KEYCLOAK_JWKS_URL` | interno `http://keycloak:8080/.../certs` |
| `VITE_KC_*` | origem HTTP `:18080` |

Keycloak imagem: `quay.io/keycloak/keycloak@sha256:f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9` (tag efetiva 24.0 / digest produtivo reconfirmado).

Gateway HML: bind `${DELPI_HML_BIND_ADDR}:18080:80`; `X-Forwarded-Port 18080` no `/auth/`. **Não iniciado nesta etapa** → login browser/Portal = **PENDING**.

## 4. Situação factual

| Frente | Estado |
|---|---|
| 3 PostgreSQL HML | **PASS** (healthy, isolados) |
| Compose/tests estáticos | **PASS** (`validate`) |
| Keycloak HML container | **PENDING ativação pós-publish** |
| Bootstrap realm/client/user | **PENDING pós-ativação** (`keycloak-hml-bootstrap.sh`) |
| Gateway / Portal login | **PENDING / BLOQUEADO** |
| Produção | **PRESERVAR** (IDs monitorados antes/depois) |

### REUSE GATE

| Capacidade | Decisão |
|---|---|
| Compose `extends` + profiles | **REUSE/EXTEND** (`keycloak` profile) |
| `keycloak-dev-bootstrap.sh` Admin REST | **EXTEND** → `keycloak-hml-bootstrap.sh` (sem MCP/direct grants) |
| Deploy paralelo | **NEW rejeitado** |

## 5. Próxima fila

| Ordem | Entrega | Estado |
|---|---|---|
| 1 | Publish HTTP + Keycloak config | **EM CURSO** |
| 2 | `up --scenario keycloak` + bootstrap | **PENDING** |
| 3 | Gateway HML + validação browser | **BLOQUEADO** |
| 4 | Apps / restore | **BLOQUEADO** |

## 6. Referências

- [Docker Compose](./docker-compose.md) §5.1
- `infra/README-ambiente.md`
- `infra/scripts/hml-compose.sh`, `infra/scripts/keycloak-hml-bootstrap.sh`
