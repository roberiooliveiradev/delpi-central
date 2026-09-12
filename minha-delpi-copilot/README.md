# Minha DELPI Copilot

Este diretório é o ponto de entrada da iniciativa **Minha DELPI Copilot** dentro do monorepo `delpi-central`.

O Copilot é a evolução da Minha DELPI para uma plataforma em que a IA funciona como uma segunda interface operacional: explica, consulta, analisa, navega e executa capabilities autorizadas usando os mesmos contratos de negócio da UI.

## Documentação completa

A documentação arquitetural e funcional canônica está em:

[`../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md)

## Estado

**Fase:** documentação/arquitetura base.  
**Runtime dedicado:** ainda não criado neste diretório.

A implementação deve evoluir componentes existentes sempre que possível:

- `minha-delpi-ai-api` — inteligência, planner, actions, RAG, policies, memory, presentation;
- `plugins/minha-delpi-chat` — experiência conversacional;
- `portal` — CopilotBridge, Router, Workspace Context e Platform Actions;
- Core API — apps, rotas, permissões e governança;
- `api-delpi` e demais APIs — Business Actions por OpenAPI.

Não criar um segundo motor de IA desconectado do chat base.

## Primeiro incremento recomendado

```text
Portal Capability Catalog
+ CopilotBridge
+ portal.open_app
+ portal.open_route
+ Workspace Context mínimo
```

Ver [`12-roadmap.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/12-roadmap.md).
