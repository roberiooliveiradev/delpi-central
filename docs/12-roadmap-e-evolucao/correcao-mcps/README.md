# Revisão das fichas técnicas dos MCPs DELPI

Levantamento iniciado em **2026-11-06**. A documentação registra decisões e lacunas; implementação e aceite conversacional permanecem pendentes.

- [TÉO](./teo.md): acrônimo existente; divergências de metodologia, descoberta e diagramas a investigar.
- [VISTA](./vista.md): acrônimo aprovado — **Visão Inteligente de Sistemas, Telas e Apresentações**; publicação no MCP pendente.
- [CLARA](./clara.md): acrônimo aprovado — **Controladoria, Leitura, Análise, Resultados e Acompanhamento**; publicação no MCP pendente.
- **DAVI:** suspenso nesta rodada durante a refatoração das ferramentas.
- [CAIO](./caio.md): acrônimo já comprovado no catálogo; revisão de identidade, descoberta e QA conversacional registrada.
- **SURI e EVA:** próximas revisões.

## Governança
Seguir OWNER → FONTE CANÔNICA → CONSUMERS → CONTRATO → IMPLEMENTAÇÃO → RUNTIME → EVIDÊNCIA. Separar aprovado para documentação, observado no catálogo, planejado, implementado e verificado. Ficha não concede AuthZ. Atualizações de runtime, Knowledge, Instructions ou OpenAPI devem ser propostas e testadas conforme a real alteração de cada artefato.
