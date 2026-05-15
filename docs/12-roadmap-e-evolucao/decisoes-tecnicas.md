# Minha DELPI — Decisões Técnicas

> **Arquivo:** `docs/12-roadmap-e-evolucao/decisoes-tecnicas.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** decisões arquiteturais e técnicas consolidadas

---

## 1. Objetivo

Este documento registra as principais decisões técnicas da Minha DELPI.

Quando uma decisão exigir detalhamento maior, ela pode ser expandida em ADR específico no futuro.

---

## 2. Nome oficial

Decisão:

```text
O produto passa a ser documentado como Minha DELPI.
```

Consequências:

- documentação nova usa Minha DELPI;
- nomes técnicos antigos podem permanecer em código quando renomear for arriscado;
- documentação deve indicar legado quando necessário.

---

## 3. Separar autenticação e autorização

Decisão:

```text
Keycloak autentica.
Core API autoriza.
```

Consequências:

- Keycloak emite JWT;
- Core API valida JWT;
- Core API cria/sincroniza usuário local;
- Core API calcula permissões efetivas;
- roles do Keycloak não são fonte final de autorização funcional.

---

## 4. Usar RBAC interno

Decisão:

```text
Permissões finais da plataforma são resolvidas pelo RBAC interno da Core API.
```

Entidades principais:

```text
User
Role
Group
Permission
UserPermission override
```

Consequências:

- apps e rotas dependem de permissions internas;
- Portal consome `/me` e `/me/apps`;
- superadmin é flag local;
- alterações RBAC exigem invalidação de cache.

---

## 5. Usar Plugin System por manifesto

Decisão:

```text
Apps/plugins são registrados por manifesto JSON validado pela Core API.
```

Contrato atual:

```text
schemaVersion: "1.0.0"
```

Consequências:

- Core API persiste app, rotas, manifesto, versões e permissões;
- Portal não hardcoda plugins;
- permissões de plugin são declaradas no manifesto;
- alterações estruturais exigem nova versão.

---

## 6. Suportar três tipos de plugin

Decisão:

```text
Suportar microfrontend, iframe e backend-only.
```

| Tipo | Uso |
|---|---|
| `microfrontend` | módulos frontend integrados |
| `iframe` | sistemas externos/legados |
| `backend-only` | serviços sem UI governados pela plataforma |

---

## 7. Usar Gateway como entrada HTTP

Decisão:

```text
Gateway Nginx é a entrada HTTP da plataforma.
```

Consequências:

- Portal, Core API, Keycloak, API DELPI e plugins são roteados pelo Gateway;
- paths públicos precisam bater com manifestos;
- WebSocket/Socket.IO deve ser suportado pelo Gateway;
- plugins devem ser servidos por `/apps/<plugin>`.

---

## 8. Separar bancos por responsabilidade

Decisão:

```text
Cada banco tem responsabilidade própria.
```

| Banco | Responsabilidade |
|---|---|
| `postgres-core` | governança da plataforma |
| `keycloak-db` | dados internos do Keycloak |
| `postgres-plugins` | domínios de plugins e persistência auxiliar (ex.: RAG / AI API) |
| TOTVS | fonte operacional externa/legada |
| Portal RH | fonte externa específica |

---

## 9. Hospedar backends operacionais na API DELPI

Decisão:

```text
A API DELPI é o backend operacional para integrações e módulos de domínio.
```

Consequências:

- consultas TOTVS ficam na `api-delpi`;
- domínios de plugin podem viver na `api-delpi`;
- módulo de qualidade deve usar `api-delpi`;
- `postgres-plugins` é o banco de persistência para módulos novos.

---

## 10. Usar Clean Architecture na API DELPI

Decisão:

```text
A API DELPI deve seguir fluxo Route → Composer → UseCase → Port → Repository concreto.
```

Consequências:

- rotas não contêm SQL;
- use cases não dependem de framework web;
- repositories de TOTVS e Postgres Plugins são separados;
- domínio novo não reutiliza infraestrutura TOTVS indevidamente.

---

## 11. Usar Unit of Work na Core API

Decisão:

```text
Core API usa Unit of Work para transações, repositories e eventos.
```

Consequências:

- use cases acessam repositories via UoW;
- eventos são coletados durante execução;
- commit/rollback fica centralizado;
- eventos são publicados após commit.

---

## 12. Eventos após commit

Decisão:

```text
Eventos devem ser publicados somente após commit transacional.
```

Consequências:

- Portal não reage a alterações que falharam no banco;
- RbacEventHandler invalida cache após persistência;
- Socket.IO emite eventos administrativos consistentes.

---

## 13. Socket.IO para atualização em tempo real

Decisão:

```text
Usar Socket.IO para notificar Portal sobre mudanças administrativas.
```

Evento principal:

```text
admin.changed
```

---

## 14. Padronizar erro como `{ errors: [...] }`

Decisão:

```text
Erros de API seguem formato único com code, message e path.
```

Consequências:

- Portal trata erro por `code`;
- mensagens podem mudar sem quebrar lógica;
- validações de manifesto podem apontar JSONPath;
- respostas evitam vazamento de stack trace.

---

## 15. Usar documentação por camadas

Decisão:

```text
Documentação oficial é centralizada em docs/, separada por camadas e público.
```

Pastas:

```text
00-visao-geral
01-arquitetura
02-infraestrutura
03-autenticacao-autorizacao
04-core-api
05-plugin-system
06-portal-frontend
07-api-delpi
08-plugins
09-banco-de-dados
10-guias-operacionais
11-padroes-de-desenvolvimento
12-roadmap-e-evolucao
```

---

## 16. Módulo de qualidade como plugin oficial

Decisão:

```text
O módulo de não conformidades externas será um plugin oficial da Minha DELPI.
```

Arquitetura:

```text
frontend próprio
backend na api-delpi
persistência no postgres-plugins
governança pela Core API
```

---

## 17. Não hardcodar plugins no Portal

Decisão:

```text
Portal monta apps e rotas a partir de /me/apps.
```

Consequências:

- novos plugins entram por manifesto;
- RBAC filtra rotas;
- favoritos e menu dependem da Core API.

---

## 18. Decisões a revisar futuramente

1. Cache RBAC em memória versus cache distribuído.
2. Estratégia oficial de migrations do `postgres-plugins`.
3. Padronização final de permission codes dos plugins antigos.
4. Política de publicação/armazenamento de assets versionados.
5. Estratégia de healthchecks e readiness no Docker Compose.
6. Estratégia de testes automatizados por camada.

---

## 19. Documentos relacionados

- [status-atual.md](./status-atual.md)
- [pendencias-tecnicas.md](./pendencias-tecnicas.md)
- [roadmap.md](./roadmap.md)
- [../01-arquitetura/arquitetura-geral.md](../01-arquitetura/arquitetura-geral.md)
- [../README.md](../README.md)
