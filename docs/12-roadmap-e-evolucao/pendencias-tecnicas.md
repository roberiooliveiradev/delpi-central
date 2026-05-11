# Minha DELPI — Pendências Técnicas

> **Arquivo:** `docs/12-roadmap-e-evolucao/pendencias-tecnicas.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** pendências técnicas, riscos, validações e próximos levantamentos

---

## 1. Objetivo

Este documento registra pendências técnicas conhecidas da Minha DELPI.

A intenção é manter uma lista controlada de pontos que ainda precisam de confirmação, implementação, revisão ou decisão.

---

## 2. API DELPI — inventário completo de rotas

Tipo:

```text
Código / Documento
```

Pendência:

```text
Inventariar rotas reais da api-delpi diretamente nos routers/controllers atuais.
```

Motivo:

- documentação atual não deve inventar endpoints;
- rotas TOTVS precisam ser confirmadas;
- contratos consumidos pelos plugins precisam ser listados;
- permissões operacionais precisam ser associadas às rotas.

---

## 3. API DELPI — separar definitivamente TOTVS e postgres-plugins

Tipo:

```text
Código / Arquitetura
```

Pendência:

```text
Garantir datasource PostgreSQL separado para módulos de plugins.
```

Motivo:

- evitar reutilização de BaseRepository TOTVS;
- evitar acoplamento com SQL Server/legado;
- suportar domínios novos como qualidade.

---

## 4. Postgres Plugins — estratégia de migrations

Tipo:

```text
Infra / Código / Operação
```

Pendência:

```text
Definir ferramenta e fluxo oficial de migrations para postgres-plugins.
```

Motivo:

- `plugins-init.sql` só roda na criação inicial do volume;
- domínios novos precisam evoluir schema;
- qualidade exigirá múltiplas tabelas.

---

## 5. Plugins existentes — manifestos reais

Tipo:

```text
Código / Documento
```

Pendência:

```text
Confirmar manifestos reais de dashboard-delpi, strategic-indicators e dashboard-lmps.
```

Motivo:

- documentos indicam padrões esperados;
- pode haver variações antigas de basePath, entry e permission code;
- registro real precisa bater com Gateway.

---

## 6. Dashboard LMPs — permission code final

Tipo:

```text
Produto / Código
```

Pendência:

```text
Padronizar permission code do dashboard-lmps.
```

Códigos que precisam ser unificados, se aparecerem no código/manifestos:

```text
dashboard-lmps.view
dashboard-lmps.access
dashboard-lmps.read
```

---

## 7. Gateway — configuração final por plugin

Tipo:

```text
Infra
```

Pendência:

```text
Confirmar rotas reais do Gateway para todos os plugins e API DELPI.
```

Verificar:

- `/apps/dashboard-delpi`;
- `/apps/strategic-indicators`;
- `/apps/dashboard-lmps`;
- `/apps/api-delpi`;
- `/core-api`;
- `/auth`.

---

## 8. Gateway — WebSocket/Socket.IO

Tipo:

```text
Infra / Operação
```

Pendência:

```text
Confirmar suporte completo a Socket.IO/WebSocket no Gateway.
```

Motivo:

- Portal depende de eventos em tempo real;
- Core API usa Socket.IO;
- proxy precisa preservar upgrade headers.

---

## 9. RBAC — cache distribuído

Tipo:

```text
Arquitetura / Escalabilidade
```

Pendência:

```text
Avaliar substituição ou complemento do cache em memória por cache distribuído.
```

Motivo:

- cache em memória funciona em instância única;
- múltiplas réplicas podem ficar inconsistentes;
- eventos RBAC precisariam invalidar cache em todos os nós.

---

## 10. Core API — inconsistências transacionais

Tipo:

```text
Código
```

Pendência:

```text
Revisar use cases que fazem commit/rollback interno ou abrem Unit of Work internamente.
```

Motivo:

- padrão oficial é commit no Unit of Work externo;
- eventos devem ser publicados após commit.

---

## 11. Notificações — contrato repository

Tipo:

```text
Código
```

Pendência:

```text
Confirmar se notifications.get(notification_id) existe no port e no repository concreto.
```

---

## 12. Keycloak — configuração reproduzível

Tipo:

```text
Operação / Infra
```

Pendência:

```text
Criar procedimento automatizado ou exportável para realm/client local.
```

Motivo:

- reset com volume apaga Keycloak;
- configuração manual pode gerar divergência;
- onboarding fica mais lento.

---

## 13. Ambientes — healthchecks

Tipo:

```text
Infra / Operação
```

Pendência:

```text
Adicionar healthchecks nos serviços principais do Compose.
```

Serviços prioritários:

```text
postgres-core
postgres-plugins
keycloak-db
keycloak
core-api
api-delpi
gateway
```

---

## 14. Qualidade / External NC — implementação

Tipo:

```text
Produto / Código
```

Pendência:

```text
Implementar módulo de qualidade conforme especificação.
```

Subpendências:

- criar plugin frontend;
- criar contexto backend na `api-delpi`;
- criar schema `quality`;
- criar migrations;
- criar use cases;
- criar permissions;
- criar manifesto;
- registrar plugin;
- validar RBAC.

---

## 15. Plugins — detalhes funcionais

Tipo:

```text
Código / Documento
```

Pendência:

```text
Complementar documentação funcional dos plugins existentes.
```

Plugins:

```text
dashboard-delpi
strategic-indicators
dashboard-lmps
```

Faltam:

- telas reais;
- KPIs;
- chamadas de API;
- permissões finais;
- contratos de resposta;
- estados de loading/erro;
- componentes principais.

---

## 16. Segurança — tokens em plugins/iframes

Tipo:

```text
Segurança
```

Pendência:

```text
Definir política final para repasse de token a plugins e iframes.
```

Regras já definidas:

- não passar token em query string;
- backend deve validar JWT;
- frontend não é barreira final.

---

## 17. Produção — volumes de código em plugins

Tipo:

```text
Infra
```

Pendência:

```text
Revisar volumes de código em serviços de plugins no compose de produção.
```

Motivo:

- produção normalmente deve usar imagem buildada;
- volumes podem mascarar build e gerar divergência.

---

## 18. Priorização sugerida

Prioridade alta:

1. Inventário real de rotas da `api-delpi`.
2. Manifestos reais dos plugins existentes.
3. Permission code final do `dashboard-lmps`.
4. Strategy de migrations do `postgres-plugins`.
5. Healthchecks/readiness no Compose.
6. Gateway para Socket.IO e plugins.

Prioridade média:

1. Cache RBAC distribuído.
2. Automação Keycloak.
3. Auditoria final.
4. Testes automatizados por camada.

---

## 19. Documentos relacionados

```text
docs/12-roadmap-e-evolucao/status-atual.md
docs/12-roadmap-e-evolucao/decisoes-tecnicas.md
docs/12-roadmap-e-evolucao/roadmap.md
```
