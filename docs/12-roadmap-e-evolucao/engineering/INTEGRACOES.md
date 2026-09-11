# Portal de Engenharia — integrações

> **Status:** contrato de integração para planejamento.  
> **Regra:** cada downstream deve ser acessado por port/gateway próprio no `engineering-api` e revalidado contra OpenAPI/código vigente.

## 1. Mapa

```text
plugins/engineering
      │
      ▼
engineering-api
      ├── Core API
      ├── api-delpi
      ├── strategic-indicators-api
      ├── requests-api
      ├── transformometro-api
      └── storage/FILESERVER allowlisted
```

O MFE não fala diretamente com nenhum desses providers, exceto contratos transversais explicitamente permitidos pela plataforma (por exemplo, assets do `plugin-ui`).

## 2. Matriz de downstreams

| Downstream | Uso | Owner | Falha segura |
|---|---|---|---|
| Core API | identidade, permissions efetivas, usuários, app/rotas, notificações | Plataforma | AuthZ falhou → fail-closed; identidade opcional de avatar pode degradar quando seguro |
| api-delpi | LMP, Produtos, estrutura, onde-usado, desenhos, estoque, fornecedores, preço | TOTVS/API corporativa | composições de leitura podem ficar `partial`; mutações não são mascaradas |
| Strategic Indicators | indicadores/meta/realizado/IDD de Engenharia | SI | Visão geral mostra indisponível/parcial; nunca recalcular score no Portal |
| requests-api | Controle de MP / solicitações | Minhas Solicitações | resumo/CTA degrada; workflow não é replicado |
| transformometro-api | TRANSFORMA+ | Transformômetro | resumo degrada; CTA pode permanecer se autorização/rota conhecida |
| FILESERVER/storage | documentos técnicos | storage corporativo | biblioteca indisponível explícita; sem fallback para path arbitrário |

## 3. Core API

### Responsabilidades

- permissions efetivas;
- dados do usuário/identidade necessários à UI;
- catálogo de apps/rotas;
- notificação de plataforma quando aplicável;
- auditoria/plataforma conforme contratos existentes.

### Regra

Não assumir que o JWT contém permission list completa. O E0 deve confirmar os endpoints efetivos do Core atual e usar o resolver/padrão compartilhado já adotado por serviços maduros.

### Cache

Cache de authorization só pode existir se o projeto já possuir padrão explícito de TTL/invalidação/fail-closed. Não criar cache local longo para evitar chamada Core.

## 4. api-delpi — Engenharia/LMP

O `engineering-api` cria anti-corruption DTOs e não repassa payloads crus ao frontend.

Famílias a revalidar:

```text
/engineering/lmps/*
```

Cobertura esperada do legado:

- summary/dashboard;
- listagem;
- detalhe;
- produtos;
- histórico/events/flow;
- Gantt/lead quando contrato existir;
- não conformidades.

Qualquer mudança de regra TOTVS pertence à `api-delpi`, não ao BFF do Portal.

## 5. api-delpi — Produtos e desenhos

Famílias existentes a mapear no E0:

- pesquisa/detalhe;
- structure/BOM;
- parents/where-used;
- drawing metadata/pdf;
- stock;
- suppliers;
- purchases/pricing/cost impact quando permitido.

O Portal pode compor uma ficha 360°, mas cada dimensão preserva a semântica do owner.

## 6. Strategic Indicators

IDs confirmados:

```text
engineering-projects-on-time
engineering-transforma-plus
```

Regras:

- `department_id=engineering`;
- agregação atual consolidada;
- meta, realizado, comparable/reference goal e score pertencem ao SI quando o contrato os fornecer;
- MFE não recalcula IDD;
- `engineering-api` apenas adapta o contrato para o DTO do Portal.

## 7. requests-api / Controle de MP

O Portal deve tratar Controle de MP como integração de workflow externo.

Padrão:

```text
Portal Engenharia
→ resumo opcional via engineering-api
→ CTA/deep link
→ my-requests
→ requests-api
```

Antes de implementar, confirmar:

- request type IDs reais;
- rotas `/new`, `/mine`, `/work-queue` e detalhe;
- permissões do solicitante/analista;
- parâmetros de deep link suportados.

Não inventar `allowed_actions` se o owner não fornecer.

## 8. Transformômetro

O Portal pode consumir resumo read-only e gerar deep link. Não chamar tabelas internas nem copiar domínio.

Revalidar:

- endpoint de resumo vigente;
- permission de acesso;
- route target do plugin;
- campos públicos seguros para compor no Portal.

## 9. FILESERVER / documentos técnicos

Há duas situações distintas:

### Desenhos

Já possuem contratos backend conhecidos; preferir reuso via api-delpi.

### Outras bibliotecas

Criar adapter no `engineering-api` apenas após configurar:

- `library_id` lógico;
- raiz allowlisted server-side;
- extensões;
- profundidade;
- tamanho máximo;
- preview/download;
- RBAC;
- auditoria;
- timeout.

Nunca aceitar `path` fornecido pelo usuário como autoridade.

## 10. Realtime da Sala

A Sala deve possuir canal próprio do `engineering-api`. O Comercial é referência de protocolo/UX, não provider.

Requisitos de integração:

- handshake autenticado;
- Core-first authorization;
- sala hub/user quando necessário;
- subscribe/unsubscribe de `room:{id}`;
- keepalive/reconnect;
- persist-before-publish;
- anti-eco;
- room/inbox events;
- menção offline → Notification Catalog/Core quando aprovado.

Se o serviço Flask exigir extensão/biblioteca nova, documentar a escolha e validar compatibilidade com Nginx, processo/container e deploy.

## 11. Auth propagation

Regra por downstream deve seguir padrão existente:

- token do usuário só é propagado quando o downstream espera user context;
- service credential apenas quando contrato de integração exigir;
- nunca logar token;
- não trocar autorização do usuário por credencial técnica que amplie acesso sem policy no BFF.

## 12. Timeout/retry

Cada gateway deve ter timeout explícito.

Retry:

- permitido apenas para leitura/idempotência e falha transitória apropriada;
- nunca retry cego de POST/mutação sem idempotency contract;
- orçamento total do endpoint deve ser menor que timeout do gateway externo.

Composições devem preferir fan-out controlado, não N chamadas por card/linha.

## 13. Erros

Traduzir provider errors para semântica do Portal:

- 401/403 → autenticação/autorização;
- 404 → recurso ausente quando semântica exigir;
- 422 → entrada inválida;
- 5xx/timeout → downstream indisponível;
- parcial apenas quando dado restante continua correto.

Não expor stack, SQL, hostname, path físico ou credenciais.

## 14. Observabilidade de integração

Por gateway registrar métricas/tags não sensíveis:

```text
provider
operation
status_class
latency_ms
timeout
partial_source
```

Usar correlation/request id. Logs devem permitir provar qual downstream falhou sem reproduzir payload sensível.

## 15. Testes contratuais

Para cada adapter:

- happy path;
- schema/normalização;
- 401/403;
- 404;
- 422 quando aplicável;
- timeout;
- 5xx;
- resposta incompleta/malformed;
- sem permissão/resource scope;
- partial composition quando permitido;
- nenhum acesso direto do MFE ao provider.
