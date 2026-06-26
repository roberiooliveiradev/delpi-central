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

## 2. API DELPI — manter documentação alinhada ao código

Tipo:

```text
Documento / Código
```

Estado:

```text
Existe pacote oficial em api-delpi/docs/api/ (guias + referência rápida).
```

Pendência residual:

```text
Revisar periodicamente routers FastAPI vs markdown após mudanças grandes (PRs que alterem prefixos ou nomenclatura).
```

Motivo:

- evitar drift entre documentação e código;
- contratos consumidos pelos plugins devem permanecer rastreáveis;
- rotas TOTVS continuam sensíveis a ambiente (VPN, credenciais).

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
Confirmar manifestos reais de strategic-indicators e dashboard-lmps.
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

Manifesto atual do repositório (`plugins/dashboard-lmps/dash-lmps.manifest.json`): permission `dash-lmps.access`, `id` `dash-lmps`.

Códigos legados que podem aparecer em docs ou código antigo:

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

Verificar (conferir `gateway/nginx.conf` e manifestos):

- `/apps/strategic-indicators`;
- `/dash-lmps` (plugin iframe `dash-lmps` — não usar `/apps/dashboard-lmps` salvo novo manifesto);
- `/apps/minha-delpi-chat`;
- `/apps/minha-delpi-ai/api/`;
- `/apps/api-delpi`;
- `/core-api`;
- `/auth`;
- `/socket.io/` (upgrade WebSocket).

---

## 8. Gateway — WebSocket/Socket.IO

Tipo:

```text
Infra / Operação
```

Estado:

```text
Stack dev documentada em gateway-nginx.md com location /socket.io/ → core-api.
```

Pendência residual:

```text
Validar paridade nos ambientes não-dev (proxies adicionais, WAF, timeouts de upgrade).
```

Motivo:

- Portal depende de `admin.changed` e notificações;
- proxies intermediários podem truncar upgrade se mal configurados.

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

## 11. Notificações — port mínimo do repository

Tipo:

```text
Código (baixa prioridade)
```

Estado:

```text
O port expõe create, list_unread, mark_read, mark_all_read. mark_read usa Session.get() na implementação SQLAlchemy — não é obrigatório expor get(id) no Protocol.
```

Pendência opcional:

```text
Se surgir necessidade de ler uma notificação específica por id fora de mark_read, estender o port com método explícito e cobrir por teste.
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
minha-delpi-chat
strategic-indicators
dashboard-lmps (dash-lmps)
```

Faltam:

- telas reais;
- KPIs;
- chamadas de API;
- permissões finais;
- contratos de resposta;
- estados de loading/erro;
- componentes principais.

Documentação de inventário: [../08-plugins/README.md](../08-plugins/README.md).

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

1. Manter `api-delpi/docs/api/` revisado após mudanças em routers.
2. Manifestos reais dos plugins existentes vs registrados em cada ambiente.
3. Permission codes legados (`dashboard-lmps.*` vs `dash-lmps.*` no manifesto atual).
4. Strategy de migrations do `postgres-plugins` (compartilhado com AI API).
5. Healthchecks/readiness no Compose.
6. Gateway em produção (timeouts, WebSocket, TLS).

Prioridade média:

1. Cache RBAC distribuído.
2. Automação / export reproduzível Keycloak.
3. Auditoria final.
4. Testes automatizados por camada.

---

## 19. Documentos relacionados

- [status-atual.md](./status-atual.md)
- [decisoes-tecnicas.md](./decisoes-tecnicas.md)
- [roadmap.md](./roadmap.md)
- [../../api-delpi/docs/api/README.md](../../api-delpi/docs/api/README.md)
