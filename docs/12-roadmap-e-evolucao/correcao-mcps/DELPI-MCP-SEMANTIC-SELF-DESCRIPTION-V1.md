# DELPI MCP SEMANTIC SELF-DESCRIPTION V1

**Data:** 2026-11-06
**Escopo:** TÉO, VISTA, CLARA, CAIO, SURI, EVA, DAVI
**Tipo:** governança semântica — padronização da autodescrição dos especialistas.

## 1. Objetivo

Qualquer especialista deve responder confiavelmente, via sua ferramenta
semântica de descoberta (`get_context`), a perguntas como *"o que você
consegue fazer?"*, *"quem é você?"*, *"quais operações exigem
confirmação?"* — fundamentado exclusivamente no catálogo oficial do
seu owner. **Nenhuma tool nova é criada.**

Fluxo canônico:

```text
Owner → fonte canônica de capacidades → catálogo semântico governado
      → get_context → ChatGPT → resposta contextualizada
```

O catálogo **informa**, nunca **autoriza**:
`user capability >= MCP effective capability` — o backend segue sendo
a autoridade final de AuthZ; o catálogo não concede permissões.

## 2. Contratos de descoberta por MCP (inventário real)

| MCP | `get_context` | Identidade | Catálogo | Availability explícita | Schema detalhado |
|---|---|---|---|---|---|
| TÉO | `section="overview|self|workspace|catalog"` | `identity` (acrônimo, display_name) | `capability_surface.agent_directives` + `actions_runtime` | sim (fases/tiers) | via `read`/`catalog` de entidades |
| VISTA | `action="context|catalog"` | `character.identity.acronym` | `catalogVersion` + `effectiveCapabilities` | sim (derive real auth) | via `read` de entidades |
| CLARA | `topic="actor|catalog|schema|persona"` | `identity.acronym` | catalog versionado + entity/action | sim | `topic="schema"` |
| CAIO | `action=...` | `identity.acronym` (derivado do display_name) | entities/actions + risco | sim | via `read`/catálogo |
| SURI | `action="context|catalog"` | `mcp.acronym` + `persona.acronym` | `catalogVersion`, corpus Knowledge v4, escritas governadas | sim | `knowledge` + catálogo |
| EVA | `action=...` | `character.identity.acronym` | catalog + `SEMANTIC_ACTIONS` (proven/planned) | sim (`status=proven|planned`) | via `read`/catálogo |
| DAVI | `action="context|catalog|schema"` | identidade (acrônimo ainda **não publicado**) | capabilities governadas + schemas | sim | `action="schema"` |

**DAVI = PENDING** — refatoração ativa de `external_capabilities`;
não forçar uniformidade enquanto houver conflito.

## 3. Vocabulário comum (representação lógica, não substituição)

Categorias: `read` | `analyze` | `execute` | `delete` | `knowledge` | `context`.

Disponibilidade: `implemented/proven` | `planned` | `unavailable` |
`deprecated` — sempre explícita na capability; catálogo honesto (EVA
marca `planned` para o que não está integrado).

Invariantes preservadas:

```text
READ != WRITE   PREPARE != ACT   SIMULATE != APPLY
RECOMMENDATION != AUTHORIZATION
```

Uma capability no catálogo ≠ autorização — cada execução valida no
backend (Keycloak identidade + Core RBAC + domain API).

## 4. Padrão de resposta ao usuário

Autodescrição deve ser compreensível sem conhecer MCP/API:
especialista + finalidade + "o que consigo" (catálogo efetivo) +
"o que depende de autorização" (condições declaradas pelo backend) +
limitações (planejadas/indisponíveis) + como começar. Não expor
handlers, segredos ou infra.

## 5. Descoberta de schemas

Compacto por padrão; detalhe sob demanda — CLARA `topic="schema"`,
DAVI `action="schema"`, demais via `read` de entidade/catálogo.

## 6. Conformidade (checklist por MCP)

- [x] identidade consultável por `get_context` (acrônimo oficial — publicado V1)
- [x] catálogo com capabilities + availability explícita
- [x] zero secrets/token no catálogo
- [x] schema detalhado acessível quando declarado
- [x] AuthZ exclusivamente backend (catálogo informativo)
- [ ] DAVI — acrônimo/projecão pendente de refatoração (PENDING)

## 7. Regras de evolução

- Catálogo descreve; nunca concede. Capabilities `planned` só viram
  `implemented` com contrato + dispatch + testes no mesmo SHA.
- Mudança de contrato público exige atualização do catálogo no mesmo
  commit (paridade catálogo ↔ tools) e bump da versão do catálogo.
- Não criar serviço central de catálogo nem copiar catálogos de domínio.
- Abstraction Gate: padronização por convenção documental + testes de
  conformidade, **não** por pacote compartilhado antecipado.

## 8. Status

6/7 conformes no runtime atual (`get_context` → identity+catalog
verificados na saga avatar/acrônimos). DAVI `PENDING`. Aceite
conversacional por especialista: `TEST_NOT_RUN` (reteste manual —
"o que você consegue fazer?" em cada conexão MCP).
