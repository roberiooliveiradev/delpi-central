# 07 — Phase 2 Planning Input

Base objetiva para elaboração do plano de implementação. Nada aqui
autoriza implementação — cada item exige decisão arquitetural ou já
está classificado.

## 1. Decisões arquiteturais que precedem qualquer diff

| ID | Decisão | Opções | Evidência | Recomendação preliminar |
|---|---|---|---|---|
| **D-1** | Convergir para 6 verbos semânticos no MCP? | (a) 6 tools substituindo 12; (b) 6 semantic + 12 legadas coexistindo (padrão EVA); (c) manter 12 | ADR item 8; docs 02/04 | (b) — coexistência EVA permite migração ADDITIVE sem BREAKING; decisão de supersession do ADR item 8 necessária |
| **D-2** | Registry semântico separado ou extensão do `capability_surface`? | (a) `vista_semantic_registry.py` tipo `SemanticAction`; (b) campos `semantic_mapping`/`status` no modelo neutral existente | G-01, G-09; `custom-gpt-actions-integration.mdc` ("façade semântica owner-local") | (b) — o modelo neutral já é a fonte canônica; adicionar projeção semântica evita segunda fonte de verdade |
| **D-3** | Forma do `execute` | (a) `execute(entity, action, operations[])` estilo SURI sobre typed ops; (b) `phase: prepare\|commit` no mesmo tool (estilo CAIO delete); (c) manter prepare/commit como tools separadas | 04 §2.execute; Caso A–E em 05 | (a)+(b) combinados: `execute` com `phase` e `operations[]` — preserva PREPARE→COMMIT e compound plans |
| **D-4** | `delete` dedicada ou dentro de execute? | (a) tool `delete` com sealed/elicited confirmation (CAIO/EVA); (b) ops `confirm` dentro de `execute` | G-03; EVA elicitation | (b) com **prova de confirmação verificável** — elevar `confirmation=true` para `target_echo`/elicitation nos ops `confirm`; delete dedicada só se fase 2 adicionar deletes fora de typed ops |
| **D-5** | Confirmação verificável | adicionar `target_echo`/elicitation ao commit para ops `confirm` | EVA `semantic_bridge.py:115-198`; `delpi_mcp` já suporta | Sim — aditivo e independente do resto da convergência; pode ir primeiro (quick win de segurança) |
| **D-6** | Escopo de expansão de capabilities | quais gaps do doc 03 entram: playlist lifecycle? media read? templates? shares? | 03 matriz | Decidir por bloco: (i) playlist lifecycle update/delete/activate — forte candidato a typed ops novos; (ii) media/templates read — moderado; (iii) shares/invites — **excluir** (gestão de acesso humana); (iv) history restore — decisão owner |
| **D-7** | `get_context` com capabilities do usuário | adicionar `principal_capabilities` derivado de AuthZ | G-05; SURI/CAIO precedent | Sim — read-only, aditivo, alto valor de UX do host |
| **D-8** | `delete_data_model` confirmationPolicy | `direct` → `confirm`? | G-02 (INCONCLUSIVE) | Escalar ao owner: se não for deliberado, é fix de 1 linha + teste |
| **D-9** | Actions: 6 ops novas ou projeção das mesmas tools? | GPT Actions precisa de operationIds; 6 semantic ops = 6 opIds + schemas por verbo | 04 §3; orçamento ~100 KiB | Projetar 6 opIds novos (`vista_get_context`, `vista_read`...) enquanto os 12 `gpt_*` deprecam — ou mapear verbos sobre os opIds existentes por `operation` field (decisão de compatibilidade) |
| **D-10** | Auditoria de writes MCP | confirmar gap G-10; se real, adotar trilha estilo CLARA | G-10 (TO_INVENTORY) | Investigar primeiro — pode já estar coberta por observability platform |

## 2. Ordem sugerida de trabalho (sem datas)

```text
E0  Decisões D-1..D-10 aprovadas + ADR item 8 supersession draft
E1  Segurança aditiva independente:
    - D-5: target_echo/elicitation para ops confirm (MCP)
    - D-8: fix delete_data_model se confirmado drift
E2  Registry semântico (D-2): campos no modelo neutral + projeção
    get_context enriquecido (D-7)
E3  Verb tools read/analyze/knowledge (projeção sobre handlers
    existentes — zero lógica nova de execução)
E4  execute com phase + operations[] (facade sobre prepare/commit —
    reusa commit_service integralmente)
E5  Actions: projeção/opIds novos + deprecation dos 12 gpt_*
    (coexistência → retirada controlada, contrato-evolução)
E6  Expansão de capabilities aprovada em D-6 (typed ops novos)
E7  Auditoria/observabilidade (D-10) + docs/ADR/capability matrix
```

## 3. Critérios de aceite já identificáveis

- Paridade MCP↔Actions mantida via **uma** fonte (capability surface
  estendido) — teste tipo `test_vista_unified_boundary`.
- 6 tools novas com schemas Literals fechados; unknown
  `(entity, action)` → erro estruturado, nunca dispatch dinâmico.
- Todo handler novo delega a `GptActionsDispatchService` ou a serviço
  canônico existente — **zero** bypass de `TvPresentationWriteService`.
- Ops `confirm`: confirmação só aceita com prova (`target_echo` ou
  elicitation); host sem elicitation → `confirmation_unavailable`.
- Catálogo com `status` por capability (proven/planned/not_implemented);
  chamada a `not_implemented` → 501 honesto.
- Proposal store: contrato inalterado (opaque, actor-bound, TTL,
  single-use); implementação persistida só se runtime exigir.
- Orçamento Actions ≤100 KiB após projeção de 6 verbos (schemas
  compactos — referência: registry compacto do CAIO).
- Testes novos: conformance MCP (6 tools), wire, facade Actions,
  negative cases (unknown entity/action, echo errado, handle
  inválido, principal_service negado), coexistência legado+novo.
- `specialist-instructions.md` e `agent_directives` atualizados para
  o novo vocabulário **sem** duplicar regra de domínio (instructions
  apontam para catálogo, não re-declaram operações).

## 4. Riscos de migração/compatibilidade

| Consumidor | Risco | Classe | Mitigação |
|---|---|---|---|
| Custom GPT Builder (Actions) | opIds renomeados/novos quebram GPT importado | BREAKING na retirada; ADDITIVE na adição | coexistir 12+6; deprecation no OpenAPI; retirar só após janela |
| MCP clients (Claude/outros) | tool names novas | ADDITIVE se coexistir; BREAKING se substituir | padrão EVA: manter legado até adopção comprovada |
| Chat interno (`tv_dashboard_handoff`) | indirect — usa MCP/tools | BEHAVIORAL se respostas mudarem | regression tests do handoff path |
| `presentation_ops_content.json` | nenhum — fonte inalterada | — | typed ops seguem sendo a autoridade |
| `commit_service`/`proposal_store` | facade nova sobre fluxo real | — | reusa integral; testes de ciclo existentes cobrem |
| capability matrix / ADR / instructions | documentação precisa supersession | DOCS | ADR novo marcando item 8 como superseded + evidence |
| Testes existentes (119+ MCP/GPT) | suites assumem 12 tools | BEHAVIORAL | suites novas + manter legado até retirada |
| `parity_map` | vira mapping 6↔6 ou desaparece | BEHAVIORAL | derivar de uma fonte; teste de drift |

## 5. Itens TO_INVENTORY — **todos fechados no doc 08**

1. ~~`preview_data_block` executa a rota?~~ — **PROVEN** (fase 1).
2. ~~CAS/base_revision~~ — **PROVEN**: CAS completo por op
   (`commit_service.py:231,445`, chain_revision).
3. ~~Auditoria~~ — **PROVEN** domínio (history actor+provenance);
   residual: sem canal → D-10.
4. ~~Parity gate~~ — **PROVEN**: `test_surface_parity_map_*` cobre
   12↔12 completo.
5. ~~Consumidores~~ — **PROVEN** código (handoff só orienta; GPT
   externo + hosts MCP são os consumidores); **INCONCLUSIVE** uso
   runtime (mantém E7).
6. ~~update_playlist fields~~ — **PROVEN gap**: 11 campos; typed
   ops não cobrem name/desc/viewport/transition/duration/playback/
   refresh/masterConfig.
7. ~~Elicitation~~ — **PROVEN**: FastMCP `ctx.elicit`, por-host;
   Actions precisa de `target_echo` (D-5).
8. ~~Budget schema~~ — **PROVEN**: 100 KiB gate; 6 verbos cabem.

Ver `08-follow-up-evidence.md` para evidência completa de cada item.

## 6. O que a fase 2 **não** deve fazer (aprendizado desta fase)

- Não criar registry paralelo que duplique `capability_surface` ou
  `vista_agent_intelligence.json` — estender a fonte canônica.
- Não expor operações arbitrárias (`url`, `method`, `op_name`,
  handler por nome) — allowlist fechada `(entity, action)`.
- Não mudar `PresentationMutation`, `PresentationPatchService`,
  `TvPresentationWriteService` — a convergência é de *superfície*.
- Não reativar `/data/copilot/*`, `tv_dashboard_copilot`, aliases
  retired.
- Não transformar `suggest_change` em LLM call — o materializador
  determinístico é feature, não limitação.
- Não deixar `confirmation=true` como única prova de deleção após a
  convergência.
- Não implementar antes da decisão documentada D-1 (o ADR item 8
  existe exatamente para impedir convergência silenciosa).

## 7. Estado de prontidão

`READY_FOR_PLANNING` com ressalvas: o inventário está completo e
verificável; as 8 perguntas TO_INVENTORY (§5) são pequenas e
fecháveis em uma sessão; nenhuma bloqueia a *elaboração* do plano —
bloqueiam apenas detalhes de implementação das etapas afetadas.
