# 08 — P1 — Cockpit da Competência

## Job

"Como está o fechamento deste mês, o que já está pronto e o que ainda impede a conclusão?"

## Cabeçalho

- competência;
- unidade;
- freshness;
- estado geral derivado.

## Eixos independentes

### Estoque
- PRELIMINARY
- WAITING_FOR_CUTOFF
- REVALIDATION_REQUIRED
- READY_TO_CLOSE
- STOCK_CLOSED

### Documentos
Contagens por REQUIRED/CONDITIONAL/OPTIONAL, pendentes, terceiros, validação, substituição, aceitos e N/A.

### Pacote
- PACKAGE_INCOMPLETE
- READY_TO_FINALIZE
- PACKAGE_FINALIZED
- PACKAGE_SENT
- WAITING_FOR_CLARIFICATION
- MONTHLY_CLOSING_COMPLETED global derivado

## Pendências

Mostrar:
- o quê;
- motivo;
- unidade;
- source;
- provider/responsável;
- evidência;
- ação;
- pending_since.

Sem SLA formal.

## Histórico

Anexos, validações, rejeições, N/A, cutoff, revalidação, estoque fechado, pacote finalizado/enviado, esclarecimentos e conclusão.

## Ações

P1 não sacramenta, valida ou envia. É cockpit + navegação P2/P3/P5.

## Critérios-chave

- STOCK_CLOSED + REQUIRED pendente → pacote incompleto;
- último doc aceito → sem auto-send;
- pre-cut zero → não final;
- paridade monetária exige divergência exatamente R$ 0,00; qualquer valor monetário não zero continua divergência e bloqueia READY_TO_CLOSE;
- H02 indisponível → não zero;
- PACKAGE_SENT + clarification → não complete;
- source parcial → PARTIAL;
- FORBIDDEN → sem exposição.
