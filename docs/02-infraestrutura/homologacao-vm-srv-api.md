# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 12/11/2026 · **Estado:** HTTPS HML ativo em `https://192.168.1.237:18443`; login browser aguarda CA confiável no PC de teste.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-TLS-ACTIVATE`.  
> **BASE_HEAD:** `6f58adcad4582b25f7d7055d55a436dee1148471`.  
> **MAIN_INTEGRATED_SHA:** `baaf0aa05d20f5643f37bf518c7509927e984ba2`.

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

## 5. Estado pós-ativação (12/11/2026)

| Item | Resultado |
|---|---|
| Gateway `:18080` + `:18443` | **PASS** (healthy) |
| Issuer público HTTPS | **PASS** `https://192.168.1.237:18443/auth/realms/delpi` |
| Portal bake Vite HTTPS | **PASS** (sem `:18080` / sem `minhadelpi.com.br`) |
| `/`, `/login`, OIDC discovery, `/core-api/health`, SVG, manifest | **PASS** via HTTPS com `--cacert` |
| Produção (IDs gateway/`StartedAt`) | **PASS** inalterados |
| Confiança CA no store do SO/navegador | **PENDING** (sistema ainda não confia sem instalação) |
| Login browser PKCE completo | **PENDING** (depende da confiança da CA) |

### Fingerprints (VM HML)

- CA: `sha256 Fingerprint=B6:F7:02:A4:7A:21:4A:1B:D9:FB:1B:39:9D:29:A0:A8:AB:1F:4F:B4:EA:59:A3:56:8B:DC:A6:F9:89:07:5A:E5`
- Server: `sha256 Fingerprint=46:72:1F:78:F0:54:C5:0D:D4:0A:41:ED:6B:A1:EB:B6:30:65:09:21:ED:B0:9C:7C:F0:B7:89:A4:01:AA:3A:8B`

### Teste browser (PC com CA)

1. Confirmar fingerprint da CA por canal confiável.
2. Instalar **somente** `infra/hml-certs/hml-local-ca.crt` (Windows: Autoridades de Certificação Raiz Confiáveis).
3. Abrir `https://192.168.1.237:18443/login` **sem** aviso de certificado.
4. DevTools: `isSecureContext === true` e `typeof crypto.subtle === "object"`.
5. SSO → `hml-tester` → `/core-api/me` → logout.

Sem evidência no navegador com CA confiável: nunca declarar `PASS` de login.

## 6. Produção

IDs e `StartedAt` do gateway produtivo preservados durante o cutover HML. Diff de “Up X hours” é apenas relógio — sem recreate.

## 7. Drift / pendências

- Drift `5c20be0311` (DÉLIA) permanece para owner DÉLIA.
- Redis / API DELPI / Plugin UI / Production Control: fora de escopo.
- **Próxima ação:** instalar CA no PC de teste autorizado e validar login browser.
- Custódia: remover `hml-local-ca.key` da VM após backup autorizado.

## 8. Referências

- `portal/src/data/keycloakClient.ts`, `keycloak-js@26.2.3`
- `infra/scripts/hml-tls-prepare.sh`, `infra/scripts/hml-compose.sh` (`tls-activate`)
- `gateway/nginx.hml.conf`, `gateway/snippets/hml-proxy-locations.conf`, `gateway/Dockerfile.hml`
- `infra/env.hml.example`, `infra/docker-compose.hml.yml`
