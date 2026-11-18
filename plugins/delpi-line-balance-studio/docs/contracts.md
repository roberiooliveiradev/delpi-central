# API pública do Studio v0.1

## Escopo do primeiro incremento

O Studio compõe estudos de Engenharia de Processos. O Portal Engenharia é o primeiro consumidor previsto. Outros portais podem usar o mesmo pacote. As APIs de Engenharia mantêm a autoridade sobre métodos de cálculo, viabilidade e dados oficiais. Esta versão é uma biblioteca TypeScript sem dependências de execução.

| Requisito | Critério de aceite |
| --- | --- |
| RQ-LBS-01 · Pacote independente | AC-LBS-01 · Compilar e importar pelo nome do pacote em um consumidor independente. |
| RQ-LBS-02 · Estudo manual | AC-LBS-02 · Criar rascunho sem SKU com operações, postos e cenários. Preservar tempos desconhecidos e operações não atribuídas. Recusar referências inválidas e atribuição duplicada no mesmo cenário. |
| RQ-LBS-03 · Condições de produção | AC-LBS-03 · Derivar minutos produtivos a partir de horários ou duração informada. Validar pausas múltiplas, sobreposições, limites e turnos noturnos. |
| RQ-LBS-04 · Catálogo único | AC-LBS-04 · Expor M1–M6 como planejados e indicar M5 como próxima implementação. |

## Contrato local

- `createManualStudy(input)` recebe um DTO interno tipado e devolve um snapshot independente do objeto de entrada ou erros com caminho e código. É determinístico, sem I/O, persistência, identificação de usuário ou efeitos externos. A pós-condição de sucesso é um estudo `MANUAL / DRAFT_LOCAL`, com cenários `SIMULATION`, tempos informados `PROVIDED` e tempos ausentes `UNKNOWN`. Atribuições fazem referência aos IDs locais e cada operação pode estar em até um posto por cenário.
- A entrada é um DTO fornecido por código consumidor. JSON externo, arquivos e respostas HTTP devem ser convertidos e validados por adapters próprios antes de cruzar esta fronteira. A forma retornada leva `schemaVersion: 1`. A raiz do pacote é a superfície pública do pacote `0.1.0`.
- `summarizeShift(input)` devolve minutos brutos, de pausa e produtivos, com origem `CALCULATED`, ou erros estruturados. Em modo relógio, horários são locais, sem data ou fuso, no formato `HH:mm`. O término anterior ao início representa a madrugada seguinte. Início e término iguais são ambíguos e inválidos. Pausas usam intervalos contíguos semiabertos e podem encostar. Em modo duração, pausas são minutos informados e o total pode abranger até 24 horas. Ambos os modos exigem tempo produtivo positivo.
- Tempo de operação informado em segundos finitos positivos, incluindo frações. Ausência explícita usa `null`. Demanda opcional em unidades por turno configurado e lote opcional em unidades. Quando preenchidos, ambos são inteiros seguros positivos. IDs e nomes precisam ter conteúdo. IDs de operações, postos e cenários são únicos em suas respectivas coleções.
- O catálogo expõe somente identificação, nome e disponibilidade. Esta versão não calcula takt, capacidade, precedência ou viabilidade. Resumos de turno são aritmética de calendário da simulação local.
- AuthN, AuthZ e auditoria do host são aplicáveis quando houver integração oficial. Aqui a biblioteca não recebe credenciais, não registra dados e não abre rede. O consumidor pode apresentar códigos de validação sem registrar o conteúdo do estudo.

## Abstraction Gate

A API pública resolve o consumo do mesmo estado por futuros editores e portais. As únicas divisões são estudo manual, horário do turno e catálogo. Integrações de dados oficiais, persistência, métodos computacionais e UI serão contratados à medida que houver consumidores e requisitos concretos. A remoção do pacote é suficiente para reverter este incremento enquanto nenhum portal o importar.
