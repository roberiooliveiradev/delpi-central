# Revisão das fichas técnicas dos MCPs DELPI

**Inventário do código existente:** [INVENTARIO-FONTES-EXISTENTES.md](./INVENTARIO-FONTES-EXISTENTES.md). Os sete especialistas **já possuem fichas implementadas dentro de seus MCPs**. Não criar novas fichas nem registry paralelo em `shared/`; o objetivo é corrigir eventuais divergências entre fonte, projeção, GPT e runtime.

Levantamento iniciado em **2026-11-06**. A documentação registra decisões e lacunas; implementação e aceite conversacional permanecem pendentes.

- [TÉO](./teo.md): ficha e acrônimo existentes; divergências de metodologia, descoberta e diagramas a investigar.
- [VISTA](./vista.md): acrônimo aprovado — **Visão Inteligente de Sistemas, Telas e Apresentações**; publicação no MCP pendente.
- [CLARA](./clara.md): acrônimo **já presente no JSON canônico** — **Controladoria, Leitura, Análise, Resultados e Acompanhamento**; verificar apenas propagação/consumo no MCP/GPT.
- [DAVI](./davi.md): **acronimo aprovado — Dados, Análises e Visão Inteligente**; ficha provisória publicada; identidade no MCP pendente e auditoria técnica suspensa durante refatoração.
- [CAIO](./caio.md): **novo acrônimo aprovado — Consultor de Análise e Inteligência de Oportunidades**; runtime ainda usa 'Operacional'; migração e QA pendentes.
- [SURI](./suri.md): acrônimo aprovado — **Suprimentos Unificados, Resultados e Inteligência**; publicação no MCP pendente; divergência crítica Knowledge read-only versus capacidades de escrita no catálogo.
- [EVA](./eva.md): ficha e acrônimo já existentes **Engenharia Virtual Assistida**; plano de paridade, descoberta e QA registrado.

## Governança
Seguir OWNER → FONTE CANÔNICA → CONSUMERS → CONTRATO → IMPLEMENTAÇÃO → RUNTIME → EVIDÊNCIA. Separar aprovado para documentação, observado no catálogo, planejado, implementado e verificado. Ficha não concede AuthZ. Atualizações de runtime, Knowledge, Instructions ou OpenAPI devem ser propostas e testadas conforme a real alteração de cada artefato.

## Critério de identidade aprovado
Todo acrônimo deve fazer sentido com a área de atuação do especialista. Alterações propostas só passam a ser fatos de runtime depois da publicação na fonte canônica, integração e teste de aceite.
