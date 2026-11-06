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
