# Editor de turnos, pausas e parâmetros

**Status:** TARGET / contrato de UI proposto, não fonte oficial de calendário.

## Entradas alternativas
1. **Horários:** hora inicial e final do turno (HH:mm), data/virada se necessário.
2. **Minutos:** duração bruta diretamente, número positivo finito.

Presets são opcionais e editáveis (ex.: 07:30–16:30), **nunca** supor jornada oficial sem consulta canônica ao owner. Exibir cada campo somente quando pertinente.

## Múltiplas pausas
Tabela editável com: identificador, início/fim ou duração, tipo/observação opcional, adicionar/remover. Validar:
- Horários válidos HH:mm, intervalo com duração positiva.
- Pausas dentro do turno, sem sobreposição; rejeitar/avisar em vez de contar duas vezes.
- Cruzamento de meia-noite: normalizar com referência temporal explícita; 22:00–06:00 pode significar +1 dia somente se política escolhida. Não aceitar ambiguidade de duração de 24h ou mais.
- Modo minutos: pausas em duração quando não houver relógio, sem afirmar posicionamento temporal nem validar ausência de sobreposição que não foi informada.
- Múltiplos dias: usar data completa e contrato futuro; não extrapolar a regra de 24h.
- Pausa parcial/incompleta: bloquear resultado final, indicar campo.

## Indicadores imediatos
`gross = duração validada`; `pauseTotal = soma dos intervalos não sobrepostos`; `productive = gross - pauseTotal`; se `productive <= 0`, inválido. `taktPreview = productive / demand` somente quando demanda e período estão coerentes; marcar **prévia local / PROVIDED**, não resultado oficial.
Ao executar M1 com roteiro oficial, enviar `available_minutes` definido pela validação, `demand` e `batch_size` quando fornecido ao domínio; retornar e exibir somente resultado calculado no backend como `CALCULATED`.

## Controles de quantidade
Demanda, lote e número de postos: stepper (+/-) e edição numérica com validação de inteiro positivo; não forçar slider. `0` para postos pode representar ainda não configurado na UX, mas **não** enviar como número válido ao domínio. `0` pausas permitido. Presets não são fontes oficiais.

## Critérios
- CLOCK e MINUTES produzem mesmo total quando equivalentes.
- Turno noturno com pausa 23:45–00:15 validado sob política explícita.
- Pausa fora do turno rejeitada.
- Pausas sobrepostas rejeitadas.
- Hora final igual inicial exige regra (não assumir 24h).
- Validações disponíveis por teclado, labels, mensagens e screen reader.
