# Minha DELPI — Roadmap

> **Arquivo:** `docs/12-roadmap-e-evolucao/roadmap.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** roadmap técnico e evolutivo da plataforma

---

## 1. Objetivo

Este documento apresenta o roadmap técnico e evolutivo da Minha DELPI.

Ele organiza próximos passos por fases, considerando a plataforma como um produto modular composto por Core API, Portal, API DELPI, Plugin System, infraestrutura e plugins.

---

## 2. Princípios

1. Consolidar a base antes de expandir.
2. Evitar acoplamento indevido entre Core API, API DELPI e plugins.
3. Priorizar documentação e contratos explícitos.
4. Evoluir plugins por manifesto.
5. Manter autorização no backend.
6. Separar governança de dados operacionais.
7. Validar cada fase com critérios objetivos.

---

## 3. Fase 0 — Documentação central oficial

Status:

```text
Concluída em primeira versão.
```

Entregas:

- estrutura `docs/`;
- visão geral;
- arquitetura;
- infraestrutura;
- autenticação/autorização;
- Core API;
- Plugin System;
- Portal;
- API DELPI;
- plugins;
- banco de dados;
- guias operacionais;
- padrões de desenvolvimento;
- roadmap e evolução.

---

## 4. Fase 1 — Validação da documentação contra o código

Objetivo:

```text
Garantir que a documentação reflita exatamente o código atual.
```

Atividades:

- revisar rotas reais da Core API;
- revisar routers/controllers da API DELPI;
- revisar manifestos reais de plugins;
- revisar configs do Gateway;
- revisar models e migrations;
- revisar frontend do Portal;
- revisar scripts e Dockerfiles.

---

## 5. Fase 2 — Fechar inventário da API DELPI

Objetivo:

```text
Manter o pacote api-delpi/docs/api/ completo e fiel aos routers FastAPI (revisão contínua).
```

Atividades:

- usar `api-delpi/docs/api/` como referência viva;
- após alterações em routers, atualizar guias ou referência rápida;
- classificar por datasource (TOTVS vs `postgres-plugins`);
- mapear autenticação e dependências de plugins;
- documentar respostas e erros relevantes.

---

## 6. Fase 3 — Consolidar manifestos dos plugins existentes

Objetivo:

```text
Garantir que todos os plugins existentes tenham manifesto válido, coerente e registrável.
```

Plugins:

```text
dashboard-delpi
strategic-indicators
dash-lmps (dashboard-lmps)
minha-delpi-chat
```

Atividades:

- localizar manifestos reais;
- validar contra schema;
- padronizar `basePath`;
- padronizar `entry`;
- padronizar permissões;
- verificar Gateway;
- registrar em ambiente limpo;
- validar `/me/apps`;
- validar carregamento no Portal.

---

## 7. Fase 4 — Padronizar migrations do `postgres-plugins`

Objetivo:

```text
Definir e implementar estratégia de migrations para domínios de plugins.
```

Atividades:

- escolher ferramenta;
- definir pasta;
- definir comando;
- criar migration inicial do schema `quality`, se aplicável;
- documentar fluxo dev/prod;
- integrar com deploy;
- testar reset e upgrade.

---

## 8. Fase 5 — Hardening de infraestrutura local

Objetivo:

```text
Melhorar previsibilidade da stack Docker.
```

Atividades:

- adicionar healthchecks;
- revisar `depends_on`;
- validar readiness;
- revisar volumes em produção;
- revisar logging;
- revisar Gateway para Socket.IO;
- revisar paths de volumes;
- separar claramente dev/prod.

---

## 9. Fase 6 — Módulo de Qualidade / External NC — MVP

Objetivo:

```text
Implementar primeira versão operacional do plugin de não conformidades externas.
```

Escopo MVP:

- frontend básico;
- backend na `api-delpi`;
- schema `quality`;
- cadastro de ocorrência;
- listagem;
- detalhe;
- status inicial;
- comentários;
- anexos básicos;
- permissões mínimas;
- manifesto;
- registro no Plugin System.

Critério de aceite:

- usuário autorizado vê plugin no Portal;
- consegue criar ocorrência;
- consegue listar e abrir detalhe;
- dados persistem em `postgres-plugins`;
- backend valida JWT/permissão.

---

## 10. Fase 7 — Qualidade / External NC — Workflow completo

Objetivo:

```text
Evoluir o MVP para fluxo completo de qualidade.
```

Escopo:

- triagem;
- contenção;
- investigação;
- causa raiz;
- plano de ação;
- conclusão de ações;
- validação de eficácia;
- fechamento;
- reabertura;
- auditoria completa.

---

## 11. Fase 8 — Dashboards e relatórios

Objetivo:

```text
Evoluir módulos com visões gerenciais e exportações.
```

Escopo:

- dashboard de qualidade;
- indicadores por fornecedor;
- indicadores por causa;
- ações vencidas;
- exportação PDF/Excel;
- melhoria dos dashboards existentes.

---

## 12. Fase 9 — Segurança e governança

Objetivo:

```text
Reforçar segurança, autorização e auditoria.
```

Atividades:

- revisar tokens em plugins;
- proibir token em query string;
- validar permissions em API DELPI;
- revisar superadmin;
- revisar auditoria;
- revisar secrets;
- revisar logs;
- revisar CORS/headers/Gateway.

---

## 13. Fase 10 — Escalabilidade

Objetivo:

```text
Preparar a plataforma para múltiplas réplicas e operação mais robusta.
```

Atividades:

- avaliar cache RBAC distribuído;
- avaliar Redis/pubsub;
- revisar Socket.IO em múltiplas instâncias;
- revisar sessions;
- revisar healthchecks;
- revisar observabilidade;
- revisar backups.

---

## 14. Fase 11 — Testes automatizados

Objetivo:

```text
Criar cobertura mínima confiável.
```

Áreas prioritárias:

- PermissionResolver;
- decorators;
- Plugin Manifest Validator;
- RegisterPluginUseCase;
- RollbackPluginVersionUseCase;
- `/me/apps`;
- API DELPI rotas críticas;
- módulo qualidade;
- Portal menu dinâmico;
- microfrontend loading.

---

## 15. Roadmap resumido

```text
Fase 0  — Documentação central
Fase 1  — Validação contra código
Fase 2  — Inventário API DELPI
Fase 3  — Manifestos dos plugins existentes
Fase 4  — Migrations postgres-plugins
Fase 5  — Hardening infraestrutura
Fase 6  — Qualidade MVP
Fase 7  — Qualidade workflow completo
Fase 8  — Dashboards e relatórios
Fase 9  — Segurança e governança
Fase 10 — Escalabilidade
Fase 11 — Testes automatizados
```

---

## 16. Próxima ação recomendada

A próxima ação recomendada após concluir a documentação é:

```text
Fase 1 — Validação da documentação contra o código.
```

Começar por:

1. `api-delpi`;
2. manifestos reais dos plugins;
3. Gateway;
4. Core API controllers;
5. Portal consumo de `/me/apps`.

---

## 17. Documentos relacionados

- [status-atual.md](./status-atual.md)
- [pendencias-tecnicas.md](./pendencias-tecnicas.md)
- [decisoes-tecnicas.md](./decisoes-tecnicas.md)
- [../00-visao-geral/mapa-da-plataforma.md](../00-visao-geral/mapa-da-plataforma.md)
- [../../api-delpi/docs/api/07-qualidade-nc.md](../../api-delpi/docs/api/07-qualidade-nc.md)
