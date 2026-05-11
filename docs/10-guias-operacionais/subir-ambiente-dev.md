# Minha DELPI — Guia Operacional: Subir Ambiente de Desenvolvimento

> **Arquivo:** `docs/10-guias-operacionais/subir-ambiente-dev.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** subida local da stack de desenvolvimento com Docker Compose

---

## 1. Objetivo

Este guia descreve como subir o ambiente de desenvolvimento da **Minha DELPI**.

O ambiente local usa Docker Compose e sobe os principais serviços da plataforma:

- Gateway;
- Portal;
- Core API;
- Keycloak;
- Postgres da Core API;
- Postgres do Keycloak;
- API DELPI;
- Postgres de plugins;
- plugins/microfrontends.

---

## 2. Pré-requisitos

Antes de executar a stack, garanta que você tenha:

- Docker instalado;
- Docker Compose disponível;
- repositório clonado;
- arquivo `.env` configurado na pasta `infra`;
- portas locais livres, especialmente `80`, `5432` e `5433`;
- acesso aos bancos externos necessários, quando aplicável, como TOTVS e Portal RH.

---

## 3. Estrutura esperada do repositório

A pasta `infra` fica no mesmo nível dos principais projetos.

Estrutura esperada:

```text
/minha-delpi
  /api-delpi
  /core-api
  /gateway
  /infra
    docker-compose.yml
    docker-compose.dev.yml
    /docker
      /postgres
        init.sql
        plugins-init.sql
    /keycloak
      /themes
  /plugins
    /dashboard-delpi
    /dashboard-lmps
    /strategic-indicators
  /portal
```

Os arquivos Compose usam caminhos relativos a partir de `infra`.

---

## 4. Arquivo Compose de desenvolvimento

O arquivo de desenvolvimento é:

```text
infra/docker-compose.dev.yml
```

Características principais:

- usa Dockerfiles de desenvolvimento;
- Keycloak executa com `start-dev`;
- monta código local como volume;
- expõe os bancos localmente;
- Gateway usa configuração de desenvolvimento;
- facilita hot reload e alterações locais.

---

## 5. Acessar a pasta `infra`

A partir da raiz do repositório:

```bash
cd infra
```

Todos os comandos deste guia assumem execução a partir da pasta `infra`.

---

## 6. Subir a stack

Execute:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Para subir em segundo plano:

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

---

## 7. Serviços esperados

A stack de desenvolvimento deve subir, no mínimo:

```text
postgres-core
keycloak-db
keycloak
core-api
portal
dashboard-delpi
strategic-indicators
dashboard-lmps
postgres-plugins
api-delpi
gateway
```

Todos os serviços usam a rede:

```text
delpi-network
```

---

## 8. Portas em desenvolvimento

Portas esperadas no ambiente local:

| Serviço | Porta local |
|---|---:|
| Gateway | `80` |
| Postgres Core | `5432` |
| Postgres Plugins | `5433` |

O Portal, Core API, Keycloak, API DELPI e plugins devem ser acessados pelo Gateway.

---

## 9. Validar Gateway

Após subir a stack, acesse:

```text
http://localhost
```

Resultado esperado:

- Portal carregando;
- nenhuma tela de erro do Nginx;
- assets do frontend respondendo.

---

## 10. Validar Core API

Teste o healthcheck:

```bash
curl http://localhost/core-api/health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

ou resposta equivalente definida no controller de health.

---

## 11. Validar Keycloak

Acesse:

```text
http://localhost/auth
```

ou o path configurado conforme `KC_HTTP_RELATIVE_PATH`.

Verificar:

- Keycloak responde;
- admin console acessível;
- realm configurado;
- client do Portal configurado.

---

## 12. Validar bancos

### 12.1 Postgres Core

Conectar via container:

```bash
docker exec -it delpi-postgres-core psql -U <usuario> -d <database>
```

Ou, em desenvolvimento, via porta local:

```text
localhost:5432
```

### 12.2 Postgres Plugins

Em desenvolvimento:

```text
localhost:5433
```

Container:

```bash
docker exec -it delpi-postgres-plugins psql -U <usuario> -d <database>
```

---

## 13. Aplicar migrations da Core API

Se o banco estiver limpo ou desatualizado:

```bash
docker compose -f docker-compose.dev.yml exec core-api flask db upgrade
```

Se necessário, verificar o estado:

```bash
docker compose -f docker-compose.dev.yml exec core-api flask db current
```

---

## 14. Logs

Ver todos os logs:

```bash
docker compose -f docker-compose.dev.yml logs -f
```

Ver logs da Core API:

```bash
docker compose -f docker-compose.dev.yml logs -f core-api
```

Ver logs do Gateway:

```bash
docker compose -f docker-compose.dev.yml logs -f gateway
```

Ver logs do Keycloak:

```bash
docker compose -f docker-compose.dev.yml logs -f keycloak
```

---

## 15. Rebuild de serviço específico

Para rebuildar apenas a Core API:

```bash
docker compose -f docker-compose.dev.yml up --build core-api
```

Para rebuildar o Portal:

```bash
docker compose -f docker-compose.dev.yml up --build portal
```

---

## 16. Entrar em um container

Core API:

```bash
docker compose -f docker-compose.dev.yml exec core-api sh
```

API DELPI:

```bash
docker compose -f docker-compose.dev.yml exec api-delpi sh
```

Portal:

```bash
docker compose -f docker-compose.dev.yml exec portal sh
```

---

## 17. Parar o ambiente

Parar containers sem remover volumes:

```bash
docker compose -f docker-compose.dev.yml down
```

Parar e remover volumes:

```bash
docker compose -f docker-compose.dev.yml down -v
```

Atenção:

> `down -v` apaga volumes de banco. Use apenas em ambiente local e quando quiser resetar completamente o estado.

---

## 18. Checklist de subida local

- [ ] `.env` existe em `infra`.
- [ ] Docker está rodando.
- [ ] Porta `80` está livre.
- [ ] Porta `5432` está livre, se usar Postgres Core local.
- [ ] Porta `5433` está livre, se usar Postgres Plugins local.
- [ ] `docker compose -f docker-compose.dev.yml up --build` executou.
- [ ] Gateway responde em `http://localhost`.
- [ ] Core API responde em `/core-api/health`.
- [ ] Keycloak responde em `/auth`.
- [ ] Migrations da Core API foram aplicadas.
- [ ] Portal consegue autenticar.
- [ ] `/me` responde após login.
- [ ] `/me/apps` retorna apps autorizados.

---

## 19. Problemas comuns

### 19.1 Porta 80 ocupada

Verificar processo usando a porta:

```bash
sudo lsof -i :80
```

Ou alterar a porta publicada no Compose local.

### 19.2 Core API sobe antes do banco

`depends_on` não garante prontidão completa do Postgres.

Solução:

- aguardar banco;
- reiniciar `core-api`;
- adicionar healthchecks no futuro.

### 19.3 Keycloak inacessível

Verificar:

- logs do `keycloak`;
- logs do `keycloak-db`;
- variáveis `POSTGRES_KC_*`;
- `KC_HTTP_RELATIVE_PATH`;
- Gateway.

### 19.4 Portal não autentica

Verificar:

- `VITE_KC_URL`;
- `VITE_KC_REALM`;
- `VITE_KC_CLIENT_ID`;
- `VITE_KC_REDIRECT_URI`;
- redirect URI no client do Keycloak;
- issuer/audience do token.

---

## 20. Pontos de atenção

1. Execute comandos a partir de `infra`.
2. O ambiente dev usa volumes de código.
3. Keycloak em dev usa `start-dev`.
4. Bancos ficam expostos localmente em dev.
5. Core API usa `FLASK_APP=app.create_app:create_app`.
6. API DELPI usa `DB_*` para TOTVS dentro do container.
7. Gateway é a entrada HTTP principal.
8. `down -v` apaga dados locais.
9. Migrations devem ser aplicadas após reset de banco.
10. O Keycloak precisa ser reconfigurado após reset de volume.

---

## 21. Documentos relacionados

```text
docs/02-infraestrutura/docker-compose.md
docs/02-infraestrutura/ambientes-dev-prod.md
docs/10-guias-operacionais/reset-banco-dev.md
docs/10-guias-operacionais/configurar-keycloak.md
docs/10-guias-operacionais/troubleshooting.md
```
