# src — Árvore de implementação proposta

**Status:** DOCUMENTED ONLY. Nesta entrega nenhum arquivo TS/TSX, build ou runtime foi criado. A estrutura é documentada por arquivos README para que as pastas existam no GitHub sem módulos vazios.

- [app](app/README.md): composição do Studio sem dependência do host.
- [model](model/README.md): tipos, invariantes e estado.
- [ports](ports/README.md): contratos agnósticos de origem, análise e drafts.
- [methods](methods/README.md): catálogo M1–M6 e métodos específicos.
- [features](features/README.md): editores de origem, operações, turnos, postos e cenários.
- [ui](ui/README.md): composição visual específica usando o Plugin UI.

**Regra de implementação:** revisar G0 e os documentos em `../docs/`; componentes e contratos só passam a `PROVEN` com código, testes e consumer.
