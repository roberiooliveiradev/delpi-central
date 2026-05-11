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
dashboard-delpi
strategic-indicators
dashboard-lmps
```

Plugins/módulos documentados:

```text
dashboard-delpi
strategic-indicators
dashboard-lmps
qualidade / external-nc
```

---

## 4. Core API

Status:

```text
Implementada e documentada em nível arquitetural, de rotas, use cases, repositories, migrations, models, notificações e erros.
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

```text
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/bootstrap-da-aplicacao.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/use-cases.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/repositories.md
docs/04-core-api/modelos-de-banco.md
docs/04-core-api/migrations.md
docs/04-core-api/erros-api.md
docs/04-core-api/notificacoes.md
```

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
- tratar autorização de UI.

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

Pendência controlada:

> O inventário completo de rotas reais da `api-delpi` ainda depende da leitura direta dos routers/controllers atuais do código.

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
postgres-plugins
keycloak-db
TOTVS externo
Portal RH externo
```

---

## 11. Plugins atuais

| Plugin | Status documental | Observação |
|---|---|---|
| `dashboard-delpi` | Documentado com base na infraestrutura | Detalhes funcionais dependem do código real do plugin |
| `strategic-indicators` | Documentado com base na infraestrutura | Detalhes funcionais dependem do código real do plugin |
| `dashboard-lmps` | Documentado com manifesto e contexto LMP | APIs/telas finais dependem do código real |
| `qualidade` | Documentado como especificação técnica | Requer implementação/evolução conforme roadmap |

---

## 12. Pontos que ainda exigem confirmação de código

1. Rotas completas da `api-delpi`.
2. Implementação final dos plugins `dashboard-delpi`, `strategic-indicators` e `dashboard-lmps`.
3. Manifestos reais finais de todos os plugins.
4. Configuração final do Gateway em produção.
5. Implementação final do módulo de qualidade.
6. Estratégia definitiva de migrations para `postgres-plugins`.
7. Contratos finais de APIs operacionais consumidas pelos plugins.

---

## 13. Riscos conhecidos

- divergência entre manifesto documentado e manifesto registrado;
- permissões duplicadas ou com nomes diferentes para mesmo acesso;
- Gateway não servir `remoteEntry.js` esperado;
- cache RBAC em memória em cenário multi-réplica;
- `depends_on` não garantir readiness;
- rotas da `api-delpi` ainda não totalmente inventariadas;
- reset local pode apagar Keycloak e exigir reconfiguração.

---

## 14. Próximas ações recomendadas

1. Commitar documentação central.
2. Validar links internos.
3. Comparar manifestos reais com documentação.
4. Inventariar rotas reais da `api-delpi`.
5. Inventariar APIs consumidas por plugins existentes.
6. Definir migrations do `postgres-plugins`.
7. Executar revisão técnica por pasta.

---

## 15. Documentos relacionados

```text
docs/12-roadmap-e-evolucao/decisoes-tecnicas.md
docs/12-roadmap-e-evolucao/pendencias-tecnicas.md
docs/12-roadmap-e-evolucao/roadmap.md
docs/00-visao-geral/mapa-da-plataforma.md
```
