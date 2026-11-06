# Revisão das fichas técnicas dos MCPs DELPI

**Inventário do código existente:** [INVENTARIO-FONTES-EXISTENTES.md](./INVENTARIO-FONTES-EXISTENTES.md). Os sete especialistas **já possuem fichas implementadas dentro de seus MCPs**. Não criar novas fichas nem registry paralelo em `shared/`; o objetivo é corrigir eventuais divergências entre fonte, projeção, GPT e runtime.

Levantamento iniciado e execução conduzida em **2026-11-06**. Seis de sete MCPs executados, verificados em runtime e deployados; DAVI pendente por refatoração em andamento.

- [TÉO](./teo.md): **EXECUTADO** — acrônimo já correto; aliases `guide_version v1|v2` implementados, ADR de diagramas reconciliado (BPMN nativo), hint de identidade no `get_context`.
- [VISTA](./vista.md): **EXECUTADO** — acrônimo **Visão Inteligente de Sistemas, Telas e Apresentações** publicado na fonte e projetado; metadata do `delete` alinhada às 8 entidades; fix de schema `colorRules` que quebrava o builder OpenAPI.
- [CLARA](./clara.md): **EXECUTADO** — acrônimo já no JSON; projeção `identity.acronym` corrigida no `agent_directives`.
- [DAVI](./davi.md): **PENDING** — refatoração em andamento (waves em commit ativo); mudança exata documentada no plano.
- [CAIO](./caio.md): **EXECUTADO** — expansão atualizada para **Consultor de Análise e Inteligência de Oportunidades** em todas as superfícies; acrônimo projetado.
- [SURI](./suri.md): **EXECUTADO** — acrônimo **Suprimentos Unificados, Resultados e Inteligência** publicado; `suri.boundaries` reconciliado com o registro fechado de escritas; `corpus_version` 4.
- [EVA](./eva.md): **EXECUTADO** — acrônimo já correto; projeção `identity.acronym` corrigida; nenhuma flag de escrita/import alterada.

## Governança
Seguir OWNER → FONTE CANÔNICA → CONSUMERS → CONTRATO → IMPLEMENTAÇÃO → RUNTIME → EVIDÊNCIA. Separar aprovado para documentação, observado no catálogo, planejado, implementado e verificado. Ficha não concede AuthZ. Atualizações de runtime, Knowledge, Instructions ou OpenAPI devem ser propostas e testadas conforme a real alteração de cada artefato.

## Critério de identidade aprovado
Todo acrônimo deve fazer sentido com a área de atuação do especialista. Alterações propostas só passam a ser fatos de runtime depois da publicação na fonte canônica, integração e teste de aceite.
## Testes diretos de aceite no ChatGPT (2026-11-06)

[Relatório de aceite funcional](./ACEITE-MCP-2026-11-06.md): TÉO, VISTA, CLARA e CAIO PASS (somente leitura); **SURI FAIL/EXECUTION_DRIFT** (corpus 3 no MCP versus 4 no GitHub; catálogo sem acrônimo); **EVA INCONCLUSIVE** (erro interno das tools). DAVI não testado. Este resultado atual de conexão **não confirma** o aceite final dos seis serviços anunciado no relatório anterior. Nenhum teste de GPT individual ou escrita foi executado.


### Reteste após remediação — conexão ChatGPT (2026-11-06)

**Atualização posterior ao incidente:** testes diretos no MCP conectado agora confirmam **SURI PASS** (`mcp.acronym` correto, Knowledge corpus 4 e `suri.boundaries` atualizado) e **EVA PASS** (`get_context(catalog)` e `knowledge(eva.usage)` respondem com acrônimo correto). Os resultados SURI FAIL e EVA INCONCLUSIVE acima são o **histórico do teste anterior**, não o estado mais recente desta conexão. Os seis especialistas passaram nos cenários de identidade/leitura efetivamente testados; **não significa aceite completo no GPT individual nem teste de writes**. DAVI não testado. Veja [reteste documentado](./ACEITE-MCP-2026-11-06.md).


## Avatares MCP (2026-11-06)

[Diagnóstico e gate de aceite dos avatares](./ACEITE-AVATARES-MCP-2026-11-06.md): cinco MCPs expõem metadados HTTPS na sessão; SURI possui avatar aprovado no owner mas não projeta sua URL; HTTP externo e renderização no ChatGPT ainda precisam de aceite. Não confundir avatar da ficha com ícone do plugin/GPT.


## Implementação de avatares inline — handoff para Devin

- [Plano completo de implementação](./PLANO-AVATAR-IMAGECONTENT-MCP-APPS-V1.md) — POC TÉO, A/B ImageContent/MCP Apps, correção SURI, rollout, deploy e critérios de aceite.
- [Prompt de execução para Devin](./PROMPT-DEVIN-AVATARES-INLINE-V1.md) — instruções de execução, commits, push, deploy, reteste no ChatGPT e relatório obrigatório. DAVI fora da implementação até terminar refatoração.

### Reteste avatares — execução backend (2026-11-06)

AVATAR-INLINE-MCP-V1 implementado: 6/6 MCPs servem o avatar oficial como
`ImageContent` via `read(entity=avatar,action=get)` (helper canônico
`delpi_mcp.avatar_image`), SURI com rota pública nova + `avatar_distribution`
projetado; 6/6 rotas HTTPS públicas retornam 200 com MIME/sha corretos.
Renderização inline no ChatGPT = `TEST_NOT_RUN` (ver
[ACEITE-AVATARES](./ACEITE-AVATARES-MCP-2026-11-06.md) e
[PLANO](./PLANO-AVATAR-IMAGECONTENT-MCP-APPS-V1.md) §10). DAVI fora de escopo.

### HOTFIX AVATAR-INLINE-V1 — CLARA + SURI (2026-11-06)

Duas falhas do aceite real ChatGPT corrigidas e verificadas em runtime:
CLARA `_wrap` descartava `ImageContent` (commit `ac8136040f`); SURI schema
`read` sem `avatar` no Literal (commit `5e5f56781c`, deploy `supplies-mcp`).
Ambos retornam `[TextContent, ImageContent]` em runtime. Visual no
ChatGPT: `TEST_NOT_RUN` (reteste manual documentado em ACEITE-AVATARES).

### MCP-AVATAR-UI-V2 — piloto TÉO (2026-11-06)

Superfície MCP Apps compartilhada (`delpi_mcp/avatar_ui.py`) + TÉO com
`show_avatar`→`ui://delpi/teo/avatar/v1` verificado em runtime (resource
HTML + CSP + meta). Visual no ChatGPT: `TEST_NOT_RUN` — reteste manual
necessário antes do rollout dos demais MCPs.
