# Minha DELPI — Visão Geral da Plataforma

> **Arquivo:** `docs/00-visao-geral/minha-delpi-visao-geral.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** visão funcional e técnica de alto nível

---

## 1. Objetivo

Este documento apresenta a visão geral da **Minha DELPI**, explicando o que é a plataforma, quais problemas ela resolve, quais serviços a compõem e como seus principais fluxos funcionam.

Este é um documento de entrada para pessoas técnicas e não técnicas que precisam entender a plataforma antes de consultar documentações mais específicas de arquitetura, infraestrutura, Core API, Portal, API DELPI ou plugins.

---

## 2. O que é a Minha DELPI

A **Minha DELPI** é a plataforma corporativa da DELPI para centralizar o acesso a aplicações internas, dashboards, módulos operacionais e futuras soluções plugáveis.

Ela atua como um portal único de entrada para o ecossistema digital da empresa, oferecendo:

- autenticação única via Keycloak;
- governança centralizada de usuários;
- controle de acesso por permissões;
- organização de apps e rotas;
- carregamento de plugins e microfrontends;
- separação entre governança da plataforma e domínios de negócio;
- base para expansão incremental de novos módulos.

A plataforma não é apenas um frontend. Ela é um ecossistema composto por Portal, Core API, API DELPI, Minha DELPI AI API (chat e agentes), Keycloak, bancos de dados, gateway e plugins.

---

## 3. Nome oficial e legado de nomenclatura

O nome atual da plataforma é:

**Minha DELPI**

O nome **DELPI Central** aparece em documentos históricos, arquivos, variáveis, clients, comentários e estruturas criadas em fases anteriores do projeto.

Regra de documentação:

> Toda documentação nova deve usar **Minha DELPI** como nome oficial. O termo **DELPI Central** deve aparecer apenas quando necessário para se referir a nomes técnicos legados ainda existentes no código ou na infraestrutura.

Exemplos de ocorrências legadas que podem continuar existindo:

- client Keycloak chamado `delpi-central`;
- audience JWT `delpi-central`;
- variáveis ou arquivos históricos;
- documentos antigos de arquitetura;
- nomes de containers ou comentários antigos.

---

## 4. Problemas que a plataforma resolve

A Minha DELPI resolve problemas comuns de ambientes corporativos com múltiplas aplicações internas.

### 4.1 Acesso fragmentado

Antes de uma plataforma central, cada aplicação tende a ter seu próprio login, seu próprio controle de acesso e sua própria forma de publicação.

A Minha DELPI centraliza o acesso em um portal único.

### 4.2 Autorização espalhada

Sem governança central, permissões podem ficar duplicadas ou inconsistentes entre sistemas.

A Minha DELPI centraliza permissões na Core API e fornece uma visão autorizada para o Portal.

### 4.3 Dificuldade de integrar novos módulos

Novos módulos podem ser acoplados de forma improvisada se não houver contrato formal.

A Minha DELPI usa um sistema de plugins baseado em manifesto, permitindo registrar apps, permissões e rotas de forma padronizada.

### 4.4 Mistura entre plataforma e negócio

A plataforma precisa governar usuários, apps e permissões. Já os módulos de negócio precisam consultar TOTVS, bancos próprios e regras operacionais.

A Minha DELPI separa esses papéis:

- **Core API** governa a plataforma;
- **API DELPI** atende domínios operacionais e integrações;
- **Plugins** entregam experiências funcionais específicas.

---

## 5. Componentes principais

A Minha DELPI é composta pelos seguintes componentes.

---

## 5.1 Gateway

O **Gateway** é o ponto único de entrada HTTP da plataforma.

Ele é baseado em Nginx e fica responsável por encaminhar as requisições para os serviços internos.

Responsabilidades:

- expor a plataforma na porta pública;
- rotear chamadas para Portal, Core API, Keycloak, API DELPI e plugins;
- isolar serviços internos da exposição direta;
- concentrar configuração de proxy reverso;
- permitir publicação por path.

Exemplos de destinos (gateway):

```text
/                              → Portal
/core-api/*                    → Core API (+ /socket.io)
/auth/*                        → Keycloak
/apps/api-delpi/*              → API DELPI
/apps/minha-delpi-ai/api/*     → Minha DELPI AI API
/apps/<plugin-id>/*            → Microfrontends (assets + shell)
```

A configuração exata de rotas deve ser documentada no arquivo específico do gateway.

---

## 5.2 Portal

O **Portal** é o frontend principal da Minha DELPI.

Ele é desenvolvido com React e Vite.

Responsabilidades:

- iniciar o login via Keycloak;
- manter o usuário autenticado durante a sessão;
- consumir a Core API;
- exibir dados do usuário;
- montar o menu dinâmico;
- listar apps autorizados;
- listar e gerenciar favoritos;
- receber notificações/eventos em tempo real;
- carregar plugins e microfrontends;
- conduzir onboarding com **Descubra o portal** (tour gamificado na home e painel flutuante).

O Portal não é a fonte de verdade de autorização.

Ele recebe da Core API uma lista de apps e rotas já filtradas conforme as permissões efetivas do usuário.

---

## 5.3 Core API

A **Core API** é o backend de governança central da Minha DELPI.

Ela é implementada em Python com Flask.

Responsabilidades:

- validar autenticação via JWT;
- sincronizar usuário autenticado localmente;
- manter usuários, roles, groups e permissions;
- resolver permissões efetivas;
- aplicar RBAC;
- gerenciar apps;
- gerenciar rotas;
- registrar plugins;
- validar manifestos;
- armazenar versões de plugins;
- gerenciar favoritos;
- gerenciar notificações;
- publicar eventos administrativos via Socket.IO;
- manter auditoria.

A Core API usa o banco `postgres-core`.

Ela não deve armazenar dados operacionais de módulos de negócio quando esses dados pertencem a domínios específicos. Esses dados devem ficar na API DELPI ou em bancos próprios de plugins/domínios.

---

## 5.4 Keycloak

O **Keycloak** é o provedor de identidade da plataforma.

Responsabilidades:

- autenticar usuários;
- emitir tokens OAuth2/OIDC;
- manter o realm da plataforma;
- manter clients de autenticação;
- permitir SSO entre aplicações integradas;
- fornecer JWKS para validação de assinatura JWT.

A autorização final da Minha DELPI não depende de permissões completas no JWT.

O JWT identifica o usuário. A Core API resolve permissões efetivas internamente.

---

## 5.5 Minha DELPI AI API

Backend FastAPI do módulo **Minha DELPI** (chat, agentes, conhecimento, tools, admin).

- Exposta em `/apps/minha-delpi-ai/api`
- Documentação de rotas: `minha-delpi-ai-api/docs/api/`
- Separada da Core API (governança) e da API DELPI (TOTVS/operacional)

---

## 5.6 API DELPI

A **API DELPI** é o backend operacional integrado ao TOTVS e domínios analíticos.

Ela é separada da Core API.

Responsabilidades típicas:

- consultar dados de negócio;
- integrar com TOTVS;
- expor rotas operacionais;
- atender módulos de domínio;
- persistir dados de plugins quando aplicável;
- usar o banco `postgres-plugins` para domínios novos que não pertencem ao banco core.

A API DELPI não substitui a Core API.

Regra de separação:

```text
Core API  → governança da plataforma
API DELPI → dados e regras operacionais de negócio
```

---

## 5.7 Plugins e microfrontends

Plugins são módulos integrados à Minha DELPI por manifesto.

Eles podem ser:

- `microfrontend`;
- `iframe`;
- `backend-only`.

Um plugin pode declarar:

- identidade;
- nome;
- versão;
- tipo;
- base path;
- entry point;
- permissões;
- rotas;
- dependências;
- metadados de UI;
- configuração de backend.

A Core API valida e registra o manifesto. Depois, o Portal recebe os apps e rotas autorizados e carrega o plugin conforme o tipo de integração.

---

## 6. Visão macro da arquitetura

A visão simplificada da plataforma é:

```text
Usuário
  ↓
Gateway
  ↓
Portal React
  ↓
Keycloak ───────────────┐
  ↓                     │
JWT                     │
  ↓                     │
Core API Flask           │
  ↓                     │
Postgres Core            │
  ↓                     │
Apps, rotas, permissões  │
  ↓                     │
Portal carrega plugins   │
  ↓                     │
API DELPI / AI API / Plugins / Postgres Plugins
```

---

## 7. Fluxo de login

O fluxo de login funciona, em alto nível, assim:

1. Usuário acessa a Minha DELPI pelo Portal.
2. Portal inicia o login no Keycloak.
3. Usuário autentica no Keycloak.
4. Keycloak retorna um access token JWT.
5. Portal chama a Core API usando `Authorization: Bearer <token>`.
6. Core API valida o JWT.
7. Core API cria ou atualiza o usuário local, se necessário.
8. Core API resolve roles, groups e permissions.
9. Portal recebe os dados do usuário e os apps autorizados.
10. Portal monta o menu e permite acesso aos módulos.

---

## 8. Fluxo de autorização

A autorização é resolvida pela Core API.

O fluxo é:

```text
JWT validado
  ↓
Usuário local identificado
  ↓
Roles diretas
  ↓
Grupos do usuário
  ↓
Roles herdadas por grupos
  ↓
Permissões das roles
  ↓
Overrides individuais
  ↓
Permissões efetivas
  ↓
Apps e rotas filtrados
```

Superadmin possui bypass e recebe acesso amplo conforme as regras dos decorators e serviços de autorização.

---

## 9. Fluxo de apps e menu dinâmico

O Portal não monta o menu a partir de configuração estática local.

Ele consulta a Core API.

Fluxo:

1. Portal autentica o usuário.
2. Portal chama endpoint de apps do usuário.
3. Core API lista apps ativos e suas rotas.
4. Core API aplica autorização por permissão.
5. Core API retorna apenas apps/rotas permitidos.
6. Portal monta sidebar, app launcher e rotas disponíveis.

Isso permite que alterações administrativas em apps, rotas, roles e permissões reflitam no Portal sem exigir deploy do frontend.

---

## 10. Fluxo de plugin

O ciclo básico de um plugin é:

```text
Plugin implementado
  ↓
Manifesto criado
  ↓
Admin registra manifesto na Core API
  ↓
Core API valida schema e regras
  ↓
Core API cria app, permissões, rotas e versão
  ↓
Portal passa a receber o plugin se o usuário tiver permissão
  ↓
Gateway serve os assets ou rota do plugin
```

Quando um plugin é atualizado:

- mudanças estruturais exigem nova versão via registro;
- mudanças não estruturais podem ser feitas por atualização de manifesto;
- rollback usa o histórico salvo em `app_versions`.

---

## 11. Fluxo de eventos em tempo real

A plataforma possui eventos administrativos em tempo real.

Exemplos de eventos:

- app atualizado;
- rota criada;
- rota removida;
- plugin registrado;
- plugin ativado/desativado;
- permissões alteradas;
- favorito adicionado/removido.

Fluxo:

```text
Use case executa regra
  ↓
Use case coleta evento
  ↓
Unit of Work commita transação
  ↓
EventBus publica evento
  ↓
Handlers de domínio executam efeitos internos
  ↓
Socket.IO publica evento para Portal
```

Eventos podem ser globais ou direcionados para um usuário específico.

---

## 12. Ambientes

A plataforma possui pelo menos dois modos de execução via Docker Compose:

### Desenvolvimento

Arquivo:

```text
infra/docker-compose.dev.yml
```

Características:

- Keycloak em `start-dev`;
- volumes de código montados;
- bancos expostos localmente;
- Dockerfiles de desenvolvimento;
- gateway usando configuração de desenvolvimento.

### Produção

Arquivo:

```text
infra/docker-compose.yml
```

Características:

- Keycloak em `start`;
- Dockerfiles de produção;
- sem volumes de código principais;
- serviços reiniciando com `unless-stopped`;
- logs com rotação em serviços críticos;
- gateway como ponto único exposto.

---

## 13. O que pertence a cada camada

### Portal

Pertence ao Portal:

- layout;
- experiência do usuário;
- consumo da Core API;
- integração com Keycloak no frontend;
- carregamento visual de plugins;
- renderização do menu.

Não pertence ao Portal:

- decidir permissões efetivas;
- manter cadastro de RBAC;
- registrar plugins;
- acessar diretamente banco da plataforma.

---

### Core API

Pertence à Core API:

- usuários;
- roles;
- groups;
- permissions;
- apps;
- rotas;
- manifestos;
- versões de plugins;
- favoritos;
- notificações;
- auditoria;
- eventos administrativos;
- autorização da plataforma.

Não pertence à Core API:

- regras operacionais do TOTVS;
- dados transacionais de módulos específicos;
- persistência principal de plugins de domínio;
- lógica visual do frontend.

---

### API DELPI

Pertence à API DELPI:

- consultas operacionais;
- integração com TOTVS;
- domínios de negócio;
- rotas de módulos internos;
- persistência em `postgres-plugins` quando aplicável.

Não pertence à API DELPI:

- registrar plugins na plataforma;
- definir menu do Portal;
- governar RBAC central;
- substituir a Core API.

---

### Plugins

Pertence aos plugins:

- experiência funcional específica;
- telas e fluxos do módulo;
- integração com APIs necessárias;
- manifesto declarativo;
- assets e build próprios.

Não pertence aos plugins:

- controlar usuários globalmente;
- definir permissões fora do manifesto;
- alterar diretamente dados de governança da Core API.

---

## 14. Princípios técnicos da plataforma

A Minha DELPI deve evoluir seguindo estes princípios:

1. **Governança centralizada**  
   Usuários, permissões, apps e rotas são governados pela Core API.

2. **Separação de responsabilidades**  
   Portal, Core API, API DELPI e plugins têm papéis distintos.

3. **Autorização interna e auditável**  
   O Keycloak autentica; a Core API autoriza.

4. **Plugins por contrato**  
   Todo plugin deve declarar manifesto válido.

5. **Evolução incremental**  
   A plataforma deve permitir adicionar novos módulos sem quebrar contratos existentes.

6. **Clean Architecture no backend**  
   Use cases dependem de ports; infraestrutura implementa detalhes.

7. **Reatividade administrativa**  
   Mudanças administrativas devem gerar eventos e refletir no Portal.

8. **Documentação alinhada ao código**  
   Documentação histórica não deve prevalecer sobre implementação real.

---

## 15. Glossário rápido

| Termo | Significado |
|---|---|
| Minha DELPI | Nome oficial atual da plataforma |
| DELPI Central | Nome legado usado em documentos e artefatos antigos |
| Portal | Frontend principal da plataforma |
| Core API | Backend de governança central |
| API DELPI | Backend operacional e de integrações |
| Keycloak | Provedor de identidade |
| RBAC | Controle de acesso baseado em roles |
| Plugin | Módulo registrado por manifesto |
| Microfrontend | Plugin frontend carregado dinamicamente |
| Manifesto | Contrato JSON que descreve um plugin |
| App | Representação registrada de uma aplicação na Core API |
| App Route | Rota de navegação vinculada a um app |
| Permission | Código de permissão usado no RBAC |
| Role | Papel que agrupa permissões |
| Group | Grupo de usuários que pode receber roles |
| Superadmin | Usuário com bypass administrativo |

---

## 16. Próximas leituras

1. [Mapa da plataforma](./mapa-da-plataforma.md)
2. [README da documentação](../README.md)
3. [Portal — visão geral](../06-portal-frontend/visao-geral-portal.md)
4. [Descubra o portal](../06-portal-frontend/descubra-o-portal.md) — onboarding gamificado
5. [Core API — visão geral](../04-core-api/visao-geral-core-api.md)
6. [API DELPI — documentação de rotas](../../api-delpi/docs/api/README.md)
7. [Plugin system — manifesto](../05-plugin-system/manifesto-plugin.md)

