# Minha DELPI — Ambientes Dev e Prod

> **Arquivo:** `docs/02-infraestrutura/ambientes-dev-prod.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** diferenças operacionais e técnicas entre os ambientes Docker de desenvolvimento e produção

---

## 1. Objetivo

Este documento descreve as diferenças entre os ambientes de **desenvolvimento** e **produção** da Minha DELPI, tomando como base os arquivos:

```text
infra/docker-compose.dev.yml
infra/docker-compose.yml
```

A documentação não substitui os arquivos Compose. Ela explica como a stack deve ser interpretada, quais diferenças são intencionais e quais pontos precisam de atenção antes de usar uma configuração em ambiente produtivo.

---

## 2. Arquivos de ambiente

A infraestrutura atual usa dois Compose principais:

```text
infra/docker-compose.dev.yml
infra/docker-compose.yml
```

| Arquivo | Uso esperado |
|---|---|
| `docker-compose.dev.yml` | Desenvolvimento local |
| `docker-compose.yml` | Execução próxima de produção ou produção controlada |

Ambos os arquivos assumem que o comando será executado a partir da pasta:

```text
infra/
```

---

## 3. Serviços comuns aos dois ambientes

Serviços presentes nos dois Compose (maio/2026):

```text
postgres-core, keycloak-db, keycloak
core-api, portal, gateway
postgres-plugins (pgvector)
api-delpi
minha-delpi-ai-api, ollama
strategic-indicators, minha-delpi-chat, dashboard-lmps, dashboard-delpi
```

Apenas em **produção** (opcional): `vllm` com profile `docker compose --profile gpu`.

Detalhamento: [docker-compose.md](./docker-compose.md).

---

## 4. Diferenças principais

| Tema | Desenvolvimento | Produção |
|---|---|---|
| Keycloak | `start-dev` | `start` |
| Core API | `Dockerfile.dev` | `Dockerfile.prod` |
| Portal | `Dockerfile.dev` | `Dockerfile.prod` |
| Gateway | `Dockerfile.dev` + `nginx.dev.conf` montado | `Dockerfile.prod` |
| Código local | Montado como volume | Em geral, imagem fechada |
| Postgres Core | Porta `5432:5432` exposta | Porta não exposta diretamente no Compose atual |
| Postgres Plugins | Porta `5433:5432` exposta | Porta não exposta diretamente no Compose atual |
| Variáveis Vite | Ambiente do container | Build args no build do Portal |
| Logs com rotação | Menos padronizado | Configurado em serviços críticos |

---

## 5. Keycloak

### 5.1 Desenvolvimento

No desenvolvimento, o Keycloak executa com:

```yaml
command: ["start-dev"]
```

Esse modo é próprio para ambiente local e facilita desenvolvimento, mas não deve ser tratado como configuração produtiva.

### 5.2 Produção

No ambiente de produção, o Keycloak executa com:

```yaml
command: ["start"]
```

Esse modo exige maior atenção a:

- hostname;
- proxy headers;
- HTTPS;
- redirect URIs;
- issuer real do token;
- URL pública do Keycloak;
- URL interna de JWKS acessível pelos containers.

Variáveis relevantes:

```env
KC_HTTP_ENABLED=
KC_HTTP_PORT=
KC_HTTP_RELATIVE_PATH=
KC_HOSTNAME=
KC_HOSTNAME_STRICT=
KC_HOSTNAME_STRICT_HTTPS=
KC_PROXY=
KC_PROXY_HEADERS=
```

---

## 6. Core API

### 6.1 Desenvolvimento

Build:

```yaml
build:
  context: ..
  dockerfile: core-api/Dockerfile.dev
```

Volume:

```yaml
../core-api:/app
```

Isso permite editar o código local e refletir alterações no container.

### 6.2 Produção

Build:

```yaml
build:
  context: ..
  dockerfile: core-api/Dockerfile.prod
```

Em produção, o código não deve depender de volume local. A imagem deve conter a versão construída e testada da aplicação.

---

## 7. Portal

### 7.1 Desenvolvimento

Build:

```yaml
build:
  context: ../portal
  dockerfile: Dockerfile.dev
```

Volumes:

```yaml
../portal:/app
/app/node_modules
```

Variáveis Vite são fornecidas como ambiente do container:

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

### 7.2 Produção

Build:

```yaml
build:
  context: ../portal
  dockerfile: Dockerfile.prod
  args:
    VITE_KC_URL: ${VITE_KC_URL}
    VITE_KC_REALM: ${VITE_KC_REALM}
    VITE_KC_CLIENT_ID: ${VITE_KC_CLIENT_ID}
    VITE_KC_REDIRECT_URI: ${VITE_KC_REDIRECT_URI}
```

Ponto crítico:

> Variáveis `VITE_*` são embutidas no build do frontend. Alterá-las em produção pode exigir rebuild da imagem do Portal.

---

## 8. Gateway

### 8.1 Desenvolvimento

Build:

```yaml
build:
  context: ../gateway
  dockerfile: Dockerfile.dev
```

Configuração montada:

```yaml
../gateway/nginx.dev.conf:/etc/nginx/nginx.conf
```

Esse volume indica que o ambiente local usa uma configuração de Nginx específica de desenvolvimento.

### 8.2 Produção

Build:

```yaml
build:
  context: ../gateway
  dockerfile: Dockerfile.prod
```

No Compose de produção fornecido, o arquivo Nginx não é montado como volume, então a configuração deve estar embutida na imagem do gateway.

---

## 9. Bancos expostos localmente

No desenvolvimento, os bancos são expostos para facilitar inspeção e debug.

```yaml
postgres-core:
  ports:
    - "5432:5432"

postgres-plugins:
  ports:
    - "5433:5432"
```

Em produção, esses bancos não aparecem expostos diretamente no Compose atual. O acesso deve ocorrer pela rede interna Docker ou por mecanismos controlados de administração.

---

## 10. Volumes persistentes

Os dois ambientes usam volumes nomeados:

```text
postgres_core_data
keycloak_data
postgres_plugins_data
```

Esses volumes preservam dados entre recriações de containers.

Em desenvolvimento, para resetar completamente:

```bash
docker compose -f docker-compose.dev.yml down -v
```

Atenção:

> `down -v` remove os dados persistidos. Nunca executar em produção sem procedimento formal de backup e restauração.

---

## 11. API DELPI

A API DELPI existe nos dois ambientes.

No desenvolvimento:

```yaml
volumes:
  - ../api-delpi:/app
```

Em ambos os ambientes, a API DELPI recebe variáveis para:

- datasource TOTVS;
- JWT/Keycloak;
- `postgres-plugins`;
- Portal RH.

Ponto importante:

> Dentro do container `api-delpi`, as variáveis `DB_*` representam o datasource TOTVS, porque o Compose mapeia `TOTVS_DB_*` para `DB_*`.

---

## 12. Plugins/microfrontends

Plugins atuais na stack:

```text
dashboard-delpi
strategic-indicators
dashboard-lmps
```

Em desenvolvimento, os plugins usam volumes de código local.

No Compose de produção fornecido, `strategic-indicators` e `dashboard-lmps` também aparecem com volumes de código montados. Isso deve ser revisado antes de tratar esse Compose como produção fechada.

Recomendação:

```text
Produção deve usar imagem versionada, sem depender de volume de código-fonte local.
```

---

## 13. Logs

O Compose de produção usa rotação de logs em serviços específicos.

Exemplo:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

Esse padrão reduz risco de crescimento indefinido dos arquivos de log do Docker.

Recomendação:

- padronizar logging em todos os serviços críticos;
- evitar registrar tokens, senhas ou secrets;
- centralizar logs em ambiente produtivo quando possível.

---

## 14. `depends_on` e readiness

Os Compose usam `depends_on`, por exemplo:

```yaml
core-api:
  depends_on:
    - postgres-core
    - keycloak
```

Isso controla ordem básica de criação dos containers, mas não garante que o serviço interno está pronto para aceitar conexões.

Riscos:

- Core API iniciar antes do Postgres aceitar conexão;
- Core API iniciar antes do Keycloak expor JWKS;
- Gateway iniciar antes dos upstreams responderem.

Recomendação:

- adicionar healthchecks;
- adicionar retry/backoff nas aplicações;
- validar `/health` da Core API após subir stack.

---

## 15. Comandos comuns

Subir desenvolvimento:

```bash
cd infra
docker compose -f docker-compose.dev.yml up --build
```

Subir desenvolvimento em segundo plano:

```bash
cd infra
docker compose -f docker-compose.dev.yml up -d --build
```

Parar desenvolvimento preservando volumes:

```bash
cd infra
docker compose -f docker-compose.dev.yml down
```

Parar desenvolvimento removendo volumes:

```bash
cd infra
docker compose -f docker-compose.dev.yml down -v
```

Subir produção/conjunto próximo de produção:

```bash
cd infra
docker compose -f docker-compose.yml up -d --build
```

Ver logs:

```bash
cd infra
docker compose -f docker-compose.yml logs -f core-api
```

---

## 16. Checklist antes de usar ambiente de produção

- [ ] Keycloak usando `start`, não `start-dev`.
- [ ] Hostname e proxy do Keycloak configurados.
- [ ] Redirect URIs do Portal configuradas no Keycloak.
- [ ] `KEYCLOAK_ISSUER` bate com o `iss` real do token.
- [ ] `KEYCLOAK_JWKS_URL` acessível pelos containers backend.
- [ ] Bancos não estão expostos publicamente sem necessidade.
- [ ] Secrets não estão versionados.
- [ ] Volumes persistentes possuem política de backup.
- [ ] Gateway possui configuração de produção embutida/testada.
- [ ] Plugins não dependem de volumes locais de código-fonte.
- [ ] Logs têm rotação e não expõem dados sensíveis.
- [ ] Healthchecks ou procedimentos de readiness estão definidos.

---

## 17. Pontos de atenção

1. Desenvolvimento privilegia hot reload e inspeção local.
2. Produção deve privilegiar imagem fechada, segurança e previsibilidade.
3. `VITE_*` é público e embutido no frontend.
4. `depends_on` não garante readiness.
5. Bancos expostos em dev não devem ser expostos em produção.
6. Volumes persistentes não devem ser removidos sem backup.
7. Gateway é o único serviço exposto na porta `80` nos Compose atuais.
8. Keycloak exige coerência entre URL pública, issuer e proxy.
9. API DELPI usa `DB_*` como datasource TOTVS dentro do container.
10. O Compose de produção atual deve ser revisado quanto a volumes de plugins antes de uso produtivo estrito.

---

## 18. Documentos relacionados

```text
docs/02-infraestrutura/docker-compose.md
docs/02-infraestrutura/gateway-nginx.md
docs/02-infraestrutura/bancos-de-dados.md
docs/02-infraestrutura/variaveis-de-ambiente.md
docs/03-autenticacao-autorizacao/keycloak-sso.md
docs/04-core-api/visao-geral-core-api.md
docs/07-api-delpi/visao-geral-api-delpi.md
```
