# Arquitetura — documentação

> **Status:** documentação oficial (maio/2026)

Visão técnica macro da Minha DELPI: camadas, fluxos e organização do monorepo.

---

## Documentos

| Arquivo | Conteúdo |
|---|---|
| [arquitetura-geral.md](./arquitetura-geral.md) | Camadas, gateway, AI API, bancos |
| [estrutura-de-repositorio.md](./estrutura-de-repositorio.md) | Pastas do monorepo |
| [fluxo-de-requisicao.md](./fluxo-de-requisicao.md) | HTTP, login, `/me`, plugins |
| [clean-architecture.md](./clean-architecture.md) | Core API e API DELPI |
| [event-driven-e-socket.md](./event-driven-e-socket.md) | Eventos, Socket.IO |

---

## Mapa rápido

```text
Gateway → Portal | Core API | Keycloak | API DELPI | AI API | Plugins
Core API → postgres-core
API DELPI / AI API → TOTVS + postgres-plugins
```

Índice operacional: [../00-visao-geral/mapa-da-plataforma.md](../00-visao-geral/mapa-da-plataforma.md).
