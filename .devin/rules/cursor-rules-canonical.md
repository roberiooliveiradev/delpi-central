---
description: "Fonte canônica de regras: .cursor/rules/*.mdc"
trigger: always_on
---

# Regras canônicas deste repositório

A fonte de verdade das diretrizes é `.cursor/rules/*.mdc`, importada
automaticamente pelo Devin (`read_config_from.cursor` em `.devin/config.json`).

- Regras `alwaysApply: true` já estão no contexto — siga-as sem reler.
- Regras com `description`/`globs` aparecem na lista de regras disponíveis:
  quando o tema for material à tarefa, leia o arquivo `.mdc` correspondente
  antes de decidir/implementar.
- Não duplicar nem reescrever regras em `.devin/rules/` — este diretório é
  apenas para config específica do Devin. Nova regra de engenharia vai em
  `.cursor/rules/` e se registra em `responsibility-map.json`
  (ver `development-standards-index.mdc`, seção "Governança das regras").
