# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 12/11/2026 · **Estado:** HTTPS interno HML autorizado (`HML-TLS-ACTIVATE`); endpoint canônico `https://192.168.1.237:18443`.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-TLS-ACTIVATE`.  
> **BASE_HEAD:** `6f58adcad4582b25f7d7055d55a436dee1148471`.  
> **MAIN_INTEGRATED_SHA:** *(preencher após push)*.

## 1. Objetivo e regras congeladas

Ambiente de homologação independente na mesma VM `srv-api`.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- Git: commit/push só no computador local; VM apenas `git pull --ff-only`.
- **Executado (pré-TLS):** DBs → Keycloak → Gateway → Core API → Portal (HTTP `:18080`).
- **Causa raiz PKCE:** Chromium não expõe `crypto.subtle` em HTTP por IP privado → `Web Crypto API is not available`.
- **Decisão:** Alternativa C — HTTPS interno porta `18443`, CA local, sem domínio público/internet.
- **Ainda proibido sem autorização:** Redis; API DELPI; Plugin UI; Production Control; restore; exposição à internet; confiança indiscriminada da CA.

## 2. Diagnóstico PKCE / Web Crypto (comprovado)

| Evidência | Resultado |
|---|---|
| Origem HTTP | `http://192.168.1.237:18080/login` |
| `window.isSecureContext` | **false** |
| `typeof crypto.subtle` | **undefined** |
| Biblioteca | `keycloak-js@26.2.3` (`pkceMethod: "S256"`) |
| Clique SSO | Erro antes do redirect ao Keycloak |

## 3. HTTPS interno — arquitetura ativada

| Item | Valor |
|---|---|
| Origem canônica | `https://192.168.1.237:18443` |
| HTTP legado | `http://192.168.1.237:18080` (health/rollback; login browser não é o caminho) |
| Issuer | `https://192.168.1.237:18443/auth/realms/delpi` |
| Certs | `infra/hml-certs/` (fora do Git); gerar com `hml-tls-prepare.sh` |
| Gateway | `nginx.hml.conf` listen 80 + 443 ssl; volume só `hml-gateway.{crt,key}` |
| Cutover | `./infra/scripts/hml-compose.sh up --scenario tls-activate` |

### REUSE GATE

| Capacidade | Decisão |
|---|---|
| Gateway HML / DNS dinâmico | **EXTEND** — dual HTTP+HTTPS |
| CA/certs | **NEW** (`hml-tls-prepare.sh`) — sem CA corporativa inventariada |
| keycloak-js / PKCE S256 | **REUSE** |
| Bootstrap KC | **EXTEND** — origem HTTPS + `sslRequired=external` |
| Portal Vite bake | **EXTEND** — `VITE_KC_*` https `:18443` |
| Core API JWT | **REUSE** — `KEYCLOAK_ISSUER` HTTPS exclusivo HML |

### Confiança da CA

1. Gerar certs na VM HML: `./infra/scripts/hml-tls-prepare.sh`.
2. Confirmar fingerprint SHA-256 da CA por canal confiável.
3. Instalar **somente** `hml-local-ca.crt` no store do PC de teste autorizado.
4. Nunca distribuir `hml-local-ca.key`. Gateway não monta a chave da CA.
5. Sem evidência no cliente → confiança = `PENDING` (não declarar PASS).

### Rollback

1. Não promover o endpoint HTTPS se login falhar.
2. Gateway/Portal/Core/Keycloak HML podem voltar a imagens anteriores via Git + rebuild HML.
3. HTTP `:18080` permanece operacional para health, mas **sem** Secure Context / PKCE browser.
4. Não usar `docker compose down -v`; não resetar bancos; não tocar produção.

## 4. Operação na VM

```bash
cd /home/operador/projetos-teste/delpi-central
git pull --ff-only
# Atualizar infra/.env.hml para URLs HTTPS (espelhar env.hml.example; preservar secrets)
./infra/scripts/hml-tls-prepare.sh   # se certs ainda não existirem
./infra/scripts/hml-compose.sh up --scenario tls-activate
```

## 5. Teste browser (obrigatório no PC com CA)

```text
https://192.168.1.237:18443/login
window.isSecureContext === true
typeof crypto.subtle === "object"
Entrar com DELPI SSO → Keycloak HML → hml-tester → /core-api/me → logout
```

Sem evidência efetiva no navegador com CA confiável: classificar `PENDING` / `INCONCLUSIVE`, nunca `PASS`.

## 6. Produção

Comparar IDs/`StartedAt`/portas 80/443 antes e depois de qualquer up HML. STOP se houver interferência.

## 7. Drift / pendências

- Drift `5c20be0311` (DÉLIA) permanece para owner DÉLIA.
- Redis / API DELPI / Plugin UI / Production Control: fora de escopo.
- Confiança da CA nos PCs de teste: processo de TI / evidência no cliente.

## 8. Referências

- `portal/src/data/keycloakClient.ts`, `keycloak-js@26.2.3`
- `infra/scripts/hml-tls-prepare.sh`, `infra/scripts/hml-compose.sh` (`tls-activate`)
- `gateway/nginx.hml.conf`, `gateway/snippets/hml-proxy-locations.conf`, `gateway/Dockerfile.hml`
- `infra/env.hml.example`, `infra/docker-compose.hml.yml`
