# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 12/11/2026 · **Estado:** HTTPS HML ativo; CA pública preparada no PC de teste; login browser ainda **PENDING** até instalação da CA no store Windows.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-TLS-BROWSER-VALIDATION-01` (continuidade de `HML-TLS-ACTIVATE`).  
> **BASE_HEAD:** `def694b899537f279a000fff093b327e7f42f23a`.  
> **MAIN_INTEGRATED_SHA:** *(docs desta validação)*.

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

## 5. Estado pós-ativação + validação browser (12/11/2026)

| Item | Resultado |
|---|---|
| Gateway `:18080` + `:18443` | **PASS** (healthy) |
| Cert servidor SAN `IP:192.168.1.237` + cadeia CA | **PASS** (`openssl verify`, s_client) |
| Fingerprint CA vs implantação | **PASS** (match exato) |
| Issuer / JWKS HTTPS | **PASS** |
| Portal bake Vite HTTPS | **PASS** (`https://192.168.1.237:18443/{,/auth}`) |
| `/core-api/health` 200 · `/core-api/me` sem token 401 | **PASS** |
| Produção gateway ID/`StartedAt` | **PASS** inalterado |
| Pacote CA pública no PC (`Desktop\\delpi-hml-ca\\`) | **PASS** (só `.crt` + README) |
| Confiança CA no store Windows/Chrome | **PENDING** (interop WSL/`certutil` falhou; wizard GUI não concluído) |
| `isSecureContext` / `crypto.subtle` no browser | **TEST_NOT_RUN** |
| Login PKCE / `/core-api/me` autenticado / logout | **PENDING** |

### Fingerprints (VM HML)

- CA: `sha256 Fingerprint=B6:F7:02:A4:7A:21:4A:1B:D9:FB:1B:39:9D:29:A0:A8:AB:1F:4F:B4:EA:59:A3:56:8B:DC:A6:F9:89:07:5A:E5`
- Server: `sha256 Fingerprint=46:72:1F:78:F0:54:C5:0D:D4:0A:41:ED:6B:A1:EB:B6:30:65:09:21:ED:B0:9C:7C:F0:B7:89:A4:01:AA:3A:8B`

### Instalação CA no Windows (PC autorizado)

Arquivo: `C:\Users\analistaptd\Desktop\delpi-hml-ca\hml-local-ca.crt`  
Instruções: `...\delpi-hml-ca\INSTALAR-CA-README.txt`

1. Confirmar fingerprint SHA-256 acima.
2. Duplo clique → Instalar Certificado → Usuário atual.
3. **Colocar todos os certificados no repositório a seguir** → Procurar → **Autoridades de Certificação Raiz Confiáveis**.
4. Concluir → reiniciar Chrome.
5. `https://192.168.1.237:18443/login` sem aviso → F12: `isSecureContext===true`, `typeof crypto.subtle==="object"`.
6. SSO `hml-tester` → sessão → `/core-api/me` → logout.

Sem evidência no navegador com CA confiável: nunca declarar `PASS` de login.

### Custódia da CA

- `hml-local-ca.key` ainda **presente** na VM HML (`infra/hml-certs/`, permissões restritas).
- Remoção da VM **não** executada: exige backup + autorização operacional explícita.
- Gateway continua usando só `hml-gateway.{crt,key}`.

## 6. Admin Console Keycloak HML (rate-limit)

**Causa raiz (CONFIRMADO):** `limit_req zone=auth_zone` no catch-all `location /auth/` + `error_page 429 → JSON` fazia o Admin Console receber módulos JS com HTTP 429 e MIME `application/json` (`error loading dynamically imported module`).

**Correção (somente HML):** `gateway/snippets/hml-proxy-locations.conf` — sem `auth_zone` em `/auth/resources/` e `/auth/admin/`; `auth_zone` preservado em `openid-connect/(token|auth|logout)` e `login-actions/`. Gateway produtivo não alterado.

Relatório de revisão: `HML_KEYCLOAK_ADMIN_CONSOLE_REVIEW` (entrega operacional no chat da task).

## 7. Produção

IDs e `StartedAt` do gateway produtivo preservados. Portas 80/443 produtivas intactas; HML exclusivo em `:18443`/`:18080`.

## 8. Ativação plataforma HML (Gates B–F) — cenários seletivos

`hml-compose.sh` autoriza ups isolados (não desbloqueia `baseline`/`platform`/`production-control` como pacote):

| Cenário | Container | Dependências prévias |
|---|---|---|
| `redis` | `delpi-hml-redis` | 7 base healthy; **sem** publish `:6379` |
| `api-delpi` | `delpi-hml-api-delpi` | Redis + plugins DB; TOTVS=`totvs-disabled.hml.invalid`; migrations plugins on start |
| `plugin-ui` | `delpi-hml-plugin-ui` | Gateway HTTPS; `remoteEntry.js` |
| `production-control-api` | `delpi-hml-production-control-api` | api-delpi; `PC_RUN_MIGRATIONS_ON_STARTUP=true` (HML only) |
| `production-control-ui` | `delpi-hml-production-control` | plugin-ui + PC API |

Relatório operacional: `HOMOLOGATION_PLATFORM_SERVICES_ACTIVATION_REPORT`.

## 9. Drift / pendências

- Drift `5c20be0311` (DÉLIA) permanece para owner DÉLIA.
- Custódia CA: backup criptografado preparado; remoção da VM exige autorização explícita.
- Credenciais HML (`KEYCLOAK_ADMIN_PASSWORD`, `HML_TEST_PASSWORD`) rotacionadas no Gate A (valores só em `.env.hml` privado).

## 10. Referências

- `portal/src/data/keycloakClient.ts`, `keycloak-js@26.2.3`
- `infra/scripts/hml-tls-prepare.sh`, `infra/scripts/hml-compose.sh` (`tls-activate`)
- `gateway/nginx.hml.conf`, `gateway/snippets/hml-proxy-locations.conf`, `gateway/Dockerfile.hml`
- `infra/env.hml.example`, `infra/docker-compose.hml.yml`
