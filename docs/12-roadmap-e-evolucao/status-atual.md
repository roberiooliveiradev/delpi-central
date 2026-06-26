# Minha DELPI — Status Atual

> **Arquivo:** `docs/12-roadmap-e-evolucao/status-atual.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** estado atual conhecido da plataforma, componentes, documentação e pendências controladas

---

## 1. Objetivo

Este documento consolida o status atual da **Minha DELPI**.

Ele serve como referência rápida para entender:

- o que já existe;
- quais componentes compõem a plataforma;
- quais camadas já estão documentadas;
- quais pontos exigem confirmação em código;
- quais temas ainda devem evoluir.

---

## 2. Nome atual da plataforma

O nome atual do produto é:

```text
Minha DELPI
```

Nomes antigos como `DELPI Central` ou `Central DELPI` devem ser tratados como legados.

Regra editorial:

> Documentação nova deve usar **Minha DELPI** como nome oficial.

---

## 3. Componentes atuais conhecidos

Componentes principais:

```text
gateway
portal
core-api
keycloak
keycloak-db
postgres-core
api-delpi
postgres-plugins
minha-delpi-ai-api
ollama
minha-delpi-chat
strategic-indicators
dashboard-lmps
```

Plugins/módulos (inventário): [../08-plugins/README.md](../08-plugins/README.md).

Plugins citados na documentação operacional:

```text
strategic-indicators
dashboard-lmps
minha-delpi-chat
qualidade / external-nc (API DELPI / roadmap)
```

---

## 4. Core API

Status:

```text
Documentada em pacote modular (controllers-e-rotas, use-cases, migrations, etc.) + visão enxuta em visao-geral-core-api.md.
```

Responsabilidades atuais:

- autenticação recebida via JWT;
- sincronização de usuário local;
- RBAC;
- superadmin;
- permissões efetivas;
- apps;
- rotas;
- manifestos;
- versões de plugin;
- rollback;
- favoritos;
- notificações;
- eventos administrativos;
- Socket.IO.

Documentos:

- [04-core-api/README.md](../04-core-api/README.md)
- [04-core-api/visao-geral-core-api.md](../04-core-api/visao-geral-core-api.md)
- [04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md)
- [04-core-api/use-cases.md](../04-core-api/use-cases.md)
- [04-core-api/unit-of-work.md](../04-core-api/unit-of-work.md)
- [04-core-api/repositories.md](../04-core-api/repositories.md)
- [04-core-api/modelos-de-banco.md](../04-core-api/modelos-de-banco.md)
- [04-core-api/migrations.md](../04-core-api/migrations.md)
- [04-core-api/erros-api.md](../04-core-api/erros-api.md)
- [04-core-api/notificacoes.md](../04-core-api/notificacoes.md)

---

## 5. Autenticação e autorização

Status:

```text
Documentadas com Keycloak, JWT, RBAC, Permission Resolver, superadmin e decorators/policies.
```

Pilares:

```text
Keycloak autentica
Core API autoriza
PermissionResolver calcula permissões efetivas
Portal consome /me e /me/apps
Backends protegidos validam JWT
```

---

## 6. Plugin System

Status:

```text
Documentado com manifesto, registro, atualização, versionamento, rollback e tipos de plugin.
```

Contrato atual:

```text
schemaVersion: "1.0.0"
```

Tipos suportados:

```text
microfrontend
iframe
backend-only
```

Tabelas:

```text
apps
app_routes
app_manifests
app_versions
permissions
```

---

## 7. Portal Frontend

Status:

```text
Documentado como shell frontend da Minha DELPI.
```

Responsabilidades:

- autenticar com Keycloak;
- consumir `/me`;
- consumir `/me/apps`;
- montar menu dinâmico;
- carregar microfrontends;
- renderizar iframes;
- exibir favoritos;
- tratar autorização de UI;
- **Descubra o portal** — tour gamificado (card na home, painel, sync Core API). Ver [descubra-o-portal.md](../06-portal-frontend/descubra-o-portal.md).

---

## 8. API DELPI

Status:

```text
Documentada em visão geral, integração TOTVS, postgres-plugins, rotas operacionais e módulos de domínio.
```

Responsabilidades:

- backend operacional;
- integração com TOTVS;
- integração com Portal RH;
- consumo do banco `postgres-plugins`;
- módulos de domínio;
- backend do plugin de qualidade;
- endpoints operacionais para plugins.

Pendência controlada (evolução):

> Rotas e contratos finos da API DELPI mudam com o código; a referência mantida no repositório está em `api-delpi/docs/api/` (OpenAPI + guias por domínio).

---

## 9. Infraestrutura

Status:

```text
Documentada com Docker Compose, ambientes, Gateway, bancos e variáveis.
```

Componentes:

- Docker Compose dev/prod;
- rede `delpi-network`;
- volumes persistentes;
- Gateway Nginx;
- Keycloak;
- PostgreSQLs;
- builds de frontend/backend/plugins.

---

## 10. Bancos de dados

Status:

```text
Documentados por responsabilidade.
```

Bancos:

```text
postgres-core
postgres-plugins  (API DELPI + Minha DELPI AI API / pgvector)
keycloak-db
TOTVS externo
Portal RH externo
```

Documentação: [../09-banco-de-dados/README.md](../09-banco-de-dados/README.md) · [../02-infraestrutura/bancos-de-dados.md](../02-infraestrutura/bancos-de-dados.md).

---

## 11. Plugins atuais

| Plugin | Status documental | Observação |
|---|---|---|
| `strategic-indicators` | Documentado com base na infraestrutura | Detalhes funcionais dependem do código real do plugin |
| `dashboard-lmps` | Documentado com manifesto e contexto LMP | APIs/telas finais dependem do código real |
| `minha-delpi-chat` | Documentado (chat + AI API) | Ver [08-plugins/README.md](../08-plugins/README.md) |
| `qualidade` | Documentado na API DELPI (`api-delpi/docs/api`) | NC / rotas — conforme código |

---

## 12. Pendências controladas (evolução contínua)

1. Manter `api-delpi/docs/api/` alinhado a novo código (revisão periódica).
2. Implementação e telas finais dos MFEs `strategic-indicators`, `dashboard-lmps`.
3. Manifestos e versões registradas em homologação/produção.
4. Configuração final do Gateway em produção.
5. Módulo de qualidade / NC conforme roadmap.
6. Estratégia de schema/migrations compartilhada para dados em `postgres-plugins` (AI API + API DELPI).
7. Contratos de APIs externas consumidas pelos plugins (quando aplicável).

---

## 13. Riscos conhecidos

- divergência entre manifesto documentado e manifesto registrado;
- permissões duplicadas ou com nomes diferentes para mesmo acesso;
- Gateway não servir `remoteEntry.js` esperado;
- cache RBAC em memória em cenário multi-réplica;
- `depends_on` não garantir readiness;
- rotas da `api-delpi` descritas em `api-delpi/docs/api` — revisar após mudanças grandes no código;
- reset local pode apagar Keycloak e exigir reconfiguração.

---

## 14. Próximas ações recomendadas

1. Validar links internos da pasta `docs/` após mudanças grandes.
2. Comparar manifestos do repositório com o que está registrado em cada ambiente.
3. Revisar periodicamente `api-delpi/docs/api/` vs routers FastAPI.
4. Inventariar chamadas HTTP feitas por cada plugin (consumo de APIs).
5. Definir ou documentar evolução do schema em `postgres-plugins` (AI + domínio).
6. Revisão técnica por pasta do monorepo conforme necessidade.

---

## 15. Documentos relacionados

- [decisoes-tecnicas.md](./decisoes-tecnicas.md)
- [pendencias-tecnicas.md](./pendencias-tecnicas.md)
- [roadmap.md](./roadmap.md)
- [../00-visao-geral/mapa-da-plataforma.md](../00-visao-geral/mapa-da-plataforma.md)
- [../README.md](../README.md)