# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 12/11/2026 · **Estado:** Portal/Core/Gateway HML ativos em HTTP LAN; **login browser PKCE bloqueado** por Secure Context.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-PKCE-BROWSER-CRYPTO-01`.  
> **BASE_HEAD:** `c9510cf0bd253eb09420bd605fb410be32b92493` (reconfirmado ancestral; HEAD ao iniciar `a154ee559f`).  
> **MAIN_INTEGRATED_SHA:** *(atualizar após push deste pacote)*.

## 1. Objetivo e regras congeladas

Ambiente de homologação independente na mesma VM `srv-api`.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- Git: commit/push só no computador local; VM apenas `git pull --ff-only`.
- **Executado:** DBs → Keycloak → Gateway → Core API → Portal (HTTP `:18080`).
- **Bloqueio atual:** PKCE no **navegador** exige Secure Context (`crypto.subtle`).
- **Ainda proibido sem autorização:** ativar HTTPS HML; Redis; API DELPI; Plugin UI; PC; restore; internet.

## 2. Diagnóstico PKCE / Web Crypto (comprovado)

| Evidência | Resultado |
|---|---|
| Origem | `http://192.168.1.237:18080/login` |
| `window.isSecureContext` | **false** |
| `typeof crypto` | `object` |
| `typeof crypto.getRandomValues` | `function` |
| `typeof crypto.subtle` | **undefined** |
| Biblioteca | `keycloak-js@26.2.3` (`pkceMethod: "S256"` em `portal/src/data/keycloakClient.ts`) |
| Código lib | `sha256Digest()` / PKCE lança `Error: Web Crypto API is not available.` se `crypto.subtle` ausente |
| Clique **Entrar com DELPI SSO** | Erro uncaught; **sem** redirect ao Keycloak (`stillOnLogin=true`) |
| `requestStorageAccess` | Irrelevante — não é a causa |

**Causa raiz:** Chromium (e navegadores modernos) **não** expõem `crypto.subtle` em HTTP para IP privado. PKCE S256 do `keycloak-js` depende de `subtle.digest('SHA-256')`. Não é falha do Keycloak HML nem do Core API (fluxos server-side/curl com PKCE continuam válidos).

## 3. Alternativas avaliadas

| Alt | Descrição | Veredito |
|---|---|---|
| **A** HTTP LAN atual | Manter `:18080` HTTP | **INVIÁVEL** sem enfraquecer PKCE (proibido: desligar PKCE, polyfill fraco, “marcar HTTP como seguro” no browser) |
| **B** Túnel SSH → localhost | `localhost` é Secure Context mesmo em HTTP | **INSUFICIENTE** para intranet multi-máquina: exigiria re-bake de `VITE_KC_*`, issuer, redirects e JWT todos em `localhost`; não atende outros PCs da LAN |
| **C** HTTPS interno | Porta exclusiva (ex. `18443`), CA local confiável nos PCs de teste, sem domínio público/internet | **SELECIONADA** (menor caminho que preserva PKCE S256 + LAN multi-cliente + isolamento) |

### REUSE GATE

| Capacidade | Decisão |
|---|---|
| Gateway HML HTTP | **REUSE** até ativação TLS autorizada |
| CA/certs | **NEW** preparatório (`hml-tls-prepare.sh` → `infra/hml-certs/`, fora do Git) |
| nginx TLS HML | **NEW** exemplo `gateway/nginx.hml.tls.example.conf` (não ligado ao Dockerfile.hml) |
| keycloak-js / PKCE S256 | **REUSE** — sem mudança de política OIDC |
| Ativação `up --scenario tls` | **BLOQUEADA** até autorização explícita |

**Decisão:** não alterar HTTP em execução; **não** ativar HTTPS sem autorização. Entregar apenas preparativos seguros.

## 4. Preparativos entregues (sem ativação)

- `infra/scripts/hml-tls-prepare.sh` — gera CA + cert SAN `IP:192.168.1.237` + `DNS:localhost`
- `infra/hml-certs/` — gitignore de chaves; README de confiança
- `gateway/nginx.hml.tls.example.conf` — esboço listener `:18443`
- Comentários em `infra/env.hml.example` com mapa de variáveis HTTPS futuras

Quando autorizado, a ativação deverá: gerar/confiar CA → publicar só porta TLS HML → rebuild Portal com `VITE_KC_*` https → bootstrap KC (issuer/redirects) → validar login browser → preservar 80/443 prod.

## 5. Estado dos serviços HML

Sete containers healthy na rede `delpi-hml-network` (HTTP `:18080` intacto). Login **browser** PKCE: **FAIL** (Secure Context). Login scriptado/server-side PKCE: permanece válido como evidência de IdP.

## 6. Produção

Nenhum container produtivo alterado nesta tarefa de diagnóstico/preparação.

## 7. Drift / pendências

- Drift `5c20be0311` (DÉLIA) permanece para owner DÉLIA.
- **Próxima ação:** autorização explícita para ativar HTTPS interno HML (`HML-TLS-ACTIVATE`).
- Redis / API DELPI / Plugin UI: fora de escopo.

## 8. Referências

- `portal/src/data/keycloakClient.ts`, `keycloak-js@26.2.3`
- `infra/scripts/hml-tls-prepare.sh`, `infra/hml-certs/README.md`
- `gateway/nginx.hml.tls.example.conf`
