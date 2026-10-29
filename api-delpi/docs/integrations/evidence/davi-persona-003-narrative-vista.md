# DAVI-PERSONA-003 — Identidade narrativa e relacionamento fictício DAVI × VISTA

> **Status:** implementação bounded concluída. Ficção narrativa = UX;
> zero impacto em AuthZ, tools, contratos ou integrações.
> Narrative version: **1**.

## 1. Decisão

Usuário aprovou universo fictício para os especialistas DELPI.
Primeira relação narrativa: **DAVI e VISTA são namorados** — complementaridade
entre inteligência de dados (DAVI) e apresentação visual (VISTA).

## 2. Onde a narrativa vive (separação preservada)

| Camada | Fonte | Conteúdo |
|---|---|---|
| Identidade estável | paste Agent Studio (`openai-workspace-agent-davi.md`) + `DAVI_MCP_INSTRUCTIONS` | persona + bloco "Universo fictício (narrativa v1)" |
| Contexto dinâmico | `davi_agent_intelligence.json` → `agent_directives` | seções operacionais (intelligence 002) |
| Narrativa compartilhada | `narrative` em `davi_agent_intelligence.json` (versionada) | universo, relacionamento VISTA, regras de menção, limites |

`narrative` é projetada em `capability_surface.agent_directives` para que o
eco chegue também a chats que usam apenas o plugin MCP.

## 3. Conteúdo implementado

- `persona.appearance` — referência visual (`REFERENCE_NOT_OFFICIAL_AVATAR`;
  jovem, cabelos escuros, casual-tecnológico azul; nunca repetida em respostas).
- `narrative` — universe, `narrative_version=1`, relacionamento VISTA
  (perfil aprovado: ~20 anos, designer competente, pele clara, cabelos pretos
  lisos, óculos, observadora, proativa), regras de menção ocasional e
  boundaries (ficção ≠ autorização/integração/dependência entre MCPs).
- `DAVI_MCP_INSTRUCTIONS` — eco compacto da relação fictícia com limites.
- Paste canônico — bloco narrativo estável + aparência de referência.

## 4. Validação

```text
UNIT/CONTRACT = PASS — 8 novos testes PERSONA-003 (narrativa versionada,
                perfil VISTA consistente, boundaries, aparência não-oficial,
                instructions/paste parity, handoff completo, AuthZ/tools
                inalterados); 43/43 na suíte de contexto
REGRESSION    = suites DAVI governadas + benchmark 264 casos sem regressão
                (nenhum alias/capability alterado; allowlist permanece v30)
MCP           = initialize instructions contêm eco VISTA; agent_directives
                projeta `narrative`; consumo pelo host = TO_INVENTORY
```

## 5. Limites honrados

- Nenhuma tool, capability, endpoint, scope ou AuthZ alterados.
- Relacionamento nunca é justificativa para integração técnica entre MCPs.
- Menção à VISTA é ocasional e contextual; nunca simula tool call.
- Aparência é referência narrativa, não avatar oficial aprovado.
- Handoff criado ≠ handoff recebido pela VISTA (entrega externa pendente).

## 6. Handoff

`api-delpi/docs/integrations/evidence/DAVI-PERSONA-003-VISTA-HANDOFF.md` —
formato obrigatório completo, pronto para entrega ao chat da VISTA.
