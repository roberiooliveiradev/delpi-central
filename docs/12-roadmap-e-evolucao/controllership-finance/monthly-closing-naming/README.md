# Monthly closing naming — «Fechamento mensal da Controladoria» no lugar de PROC-0072

| Campo | Valor |
|---|---|
| Status | **READY** — [trilha de execução](./track.md) |
| Doc | 169 |
| Produto | Portal Controladoria & Finanças + CLARA |
| Origem | verificação da CLARA em PROD, 14/11/2026 |
| Prompt | [prompts/N0-N5-cursor.md](./prompts/N0-N5-cursor.md) |

`PROC-0072` é o **código** do macroprocesso no Transformômetro (TÉO), não o nome. O nome é **Fechamento mensal da Controladoria**. Hoje a CLARA mostra o código ao usuário porque ele está nas instruções do conector, na descrição da ferramenta de conhecimento, na ficha de inteligência dela e em 76 das 115 fontes da base de conhecimento. Este plano troca o código pelo nome em tudo o que o usuário vê, sem apagar documento e sem quebrar a rastreabilidade com o TÉO.

## Conteúdo

| Arquivo | O que tem |
|---|---|
| [plan.md](./plan.md) | problema, origens (inventário), decisões D1–D6, regras de substituição, exceções, critério de aceite |
| [track.md](./track.md) | trilha N0–N5 para o Cursor: protocolo, paradas, rollback, verificação pela CLARA |
| [prompts/N0-N5-cursor.md](./prompts/N0-N5-cursor.md) | prompt de execução |

## Próximos passos

1. Cursor: executar N0–N5.
2. Claude: verificar pela CLARA em PROD (track.md §6).
3. Retomar a ampliação da CLARA (pendência a partir do achado, motivo ao resolver, bateria de perguntas) e a T10 do entry-audit.
