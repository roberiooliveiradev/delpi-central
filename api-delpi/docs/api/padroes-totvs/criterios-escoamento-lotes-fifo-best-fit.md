# Critérios de escoamento de lotes — FIFO, Best Fit e FEFO

> **Produto:** Minha DELPI | **Domínio:** Protheus, estoque, suprimentos e produção  
> **Status:** referência de conhecimento externo (TOTVS), **não homologada no ambiente DELPI**  
> **Consulta das fontes:** 13/10/2026 | **Finalidade:** reutilização em análises, requisitos e implementações futuras.

Parte da [biblioteca canônica de padrões TOTVS](./README.md). Trata-se de **seleção operacional de lotes**, não do método financeiro/contábil de **custo FIFO/PEPS**.

## 1. Regras e diferenças

| Critério | Ordenação/prioridade | Desempate na documentação TOTVS | Objetivo |
|---|---|---|---|
| **FIFO (PEPS)** — *First In, First Out* | Lote com **data de entrada mais antiga** primeiro | **Menor data de validade** | Rotação por antiguidade |
| **Best Fit** — escoamento por quantidade | **Saldo disponível do lote mais próximo** da quantidade necessária | **Data de entrada mais antiga** | Reduzir divisão/quebra/fracionamento de lotes |
| **FEFO** — *First Expired, First Out* | **Menor data de validade** primeiro | **Entrada mais antiga**, seguida por ordenação alfanumérica conforme TOTVS | Minimizar risco associado a vencimento |

### FIFO
- Ordenar os lotes elegíveis por data de entrada crescente e consumir o mais antigo antes dos demais.
- Na igualdade de datas de entrada, usar a data de validade crescente, conforme a regra divulgada pela TOTVS.
- **Benefício:** redução de envelhecimento. **Limitação:** pode manter lotes parcialmente consumidos e não é substituto de FEFO para materiais cuja validade seja prioritária.

### Best Fit
- Priorizar o lote elegível cujo **saldo disponível esteja mais próximo da demanda** para reduzir fracionamentos.
- Em empate de quantidade/adequação, usar **data de entrada crescente**.
- A regra **não prioriza automaticamente idade ou vencimento**. A validade, status e disponibilidade entram como verificações de elegibilidade/restrição operacional, a serem confirmadas no cenário DELPI.
- **Não presumir algoritmo exato** para lotes menores que a demanda, múltiplos lotes necessários, ausência de saldo suficiente, concorrência, reservas ou mais de um empate; a documentação resumida da TOTVS não determina todos esses casos. Validar comportamento real antes de codificar um espelho de sua regra.
- **Benefício:** pode esgotar um lote de forma eficiente. **Limitação:** lotes mais antigos podem ficar parados.

### FEFO
- Prioriza a data de validade mais próxima, com desempates documentados pela TOTVS.
- Pode ser o critério preferido quando vencimento/shelf life tem precedência, sujeito à decisão operacional e às regras de qualidade.

## 2. Exemplo ilustrativo — consumo de cabo

Demanda de uma OP: **180 m** do mesmo produto (mesma unidade de medida), com lotes liberados e no mesmo escopo de filial/armazém.

| Lote | Entrada | Saldo |
|---|---|---:|
| A | 01/09/2026 | 500 m |
| B | 20/09/2026 | 200 m |
| C | 05/10/2026 | 180 m |

- **FIFO:** consome 180 m do lote **A**, restando **320 m** nele.
- **Best Fit:** escolhe o lote **C**, de encaixe exato, e o zera.
- **FEFO:** não pode ser determinado neste exemplo, pois faltam as datas de validade.

**Atenção:** é uma simulação de conceito, **não evidência da parametrização ou da execução do Protheus DELPI**. O Best Fit de lotes também **não é um algoritmo de otimização de corte de cabos/bobinas/retalhos**.

## 3. Configuração documentada no TOTVS Protheus

A TOTVS descreve, após a **expedição contínua de junho de 2026**, as três alternativas de requisição automática. Para o cadastro de produtos:

1. No **SIGACFG**, verificar `MV_CADPROD` e a inclusão da tabela de dados complementares **D4Z**.
2. No **SIGAEST → MATA010 → Indicadores do Produto → Dados Complementares → Escoamento de Lote**, selecionar a regra. **`3 - Por Qtd. (Best Fit)`** é a opção explícita para Best Fit.
3. Nos cenários que utilizam **SBZ**, a TOTVS referencia o campo **`BZ_ESLOTE`**.
4. Personalizações de sequência, quando o padrão não atende, são previstas via ponto de entrada **`MTSLDORD`** (exigem análise técnica).
5. O artigo específico Best Fit cita **Protheus a partir de 12.1.2310**. Conferir a **expedição contínua efetivamente aplicada** e a disponibilidade/configuração no ambiente real.

**Atenção para ordens de produção:** o artigo TOTVS **SIGAPCP/MATA650** consultado descreve FEFO como regra de sugestão de lotes no empenho/consumo sem lote previamente definido. Não assumir que a configuração do SIGAEST muda automaticamente o resultado de **empenho, requisição, apontamento e baixa de OP**. Homologar cada rotina. **Nenhuma configuração DELPI foi lida ou alterada neste registro.**

## 4. Orientações para futuras implementações na Minha DELPI

**Aplicações candidatas:** sugestão de separação no Almoxarifado; abastecimento de fábrica/Factory Supply; atendimento de OP; painel de lotes abertos e envelhecimento; simulações de aproveitamento, comparação FIFO x Best Fit e justificativa da escolha.

Fluxo conceitual, **ainda não implementado**:

```text
Demanda (produto, filial, armazém, quantidade, unidade)
  -> obter lotes e saldos da fonte operacional autorizada
  -> filtrar lotes elegíveis: status/qualidade, validade, reservas, local etc.
  -> aplicar estratégia explicitamente selecionada
  -> devolver sugestão auditável: lotes, quantidades e justificativas
  -> comparar com execução TOTVS em homologação
```

**Regras para o projeto:**
- Implementar regra de seleção no **domínio/use case**; isolar leitura TOTVS no **repository/adapter**, conforme [integração TOTVS](../../../../docs/07-api-delpi/integracao-totvs.md).
- Não inferir lotes a partir do saldo **agregado** de `SB2`; confirmar no Protheus os campos/tabelas reais de rastreabilidade, disponibilidade, empenhos, filial, armazém e sublote.
- Padronizar unidades e casas decimais antes de comparar saldos; respeitar produto, filial, armazém, validade, status e reservas.
- Não misturar **custo contábil FIFO** com **FIFO físico** de seleção de lote.
- Registrar cada seleção com `strategy`, demanda, fonte/data dos saldos, regras de elegibilidade, candidatos rejeitados, desempates e motivo final.
- Tratar alocação parcial, falta de material e concorrência de estoque explicitamente, sem garantir que um único lote sempre atenderá.
- **Escopo desta entrega: somente documentação.** Não foram criados endpoints, algoritmos, novos parâmetros, alterações no ERP ou integração transacional.

## 5. Checklist mínimo de homologação

- [ ] Identificar versão, expedição contínua e parâmetros existentes no Protheus DELPI.
- [ ] Confirmar produtos com controle de lotes, uso de D4Z/SBZ e telas efetivamente disponíveis.
- [ ] Testar FIFO com empates de entrada; Best Fit com encaixe exato, dois lotes adequados e empate; FEFO com validades distintas.
- [ ] Testar bloqueios de qualidade, vencimento, saldo reservado, lote indisponível, sublote e filiais/locais diferentes.
- [ ] Testar quando a demanda exige **múltiplos lotes** e quando não há saldo total suficiente.
- [ ] Testar conversões de unidade, decimais e movimentações concorrentes.
- [ ] Comparar resultados no SIGAEST versus empenhos/requisições/apontamentos do SIGAPCP.
- [ ] Definir junto a Suprimentos/Produção/Qualidade qual política usar em cada processo.
- [ ] Registrar evidência real, exceções e testes antes de declarar qualquer regra como **padrão DELPI homologado**.

## 6. O que fazer / não fazer

| Fazer | Não fazer |
|---|---|
| Identificar a política usada e registrar o critério de decisão | Tratar FIFO, FEFO e Best Fit como sinônimos |
| Validar **saldos disponíveis e elegibilidade** antes da seleção | Escolher lote bloqueado/vencido por ser antigo ou encaixar na demanda |
| Homologar comportamento por rotina TOTVS | Supor que toda rotina Protheus compartilha a mesma lógica |
| Separar simulação de ações de reserva/baixa | Escrever no ERP sem contrato, autorização e validação |
| Revisar fonte e versão da TOTVS quando houver atualização | Assumir que esta referência prova configuração ativa na DELPI |

## 7. Fontes oficiais (consultadas em 13/10/2026)

- TOTVS SIGAEST, 12/08/2026, [Requisição dos lotes automáticos: sequência FEFO, FIFO e Best Fit](https://centraldeatendimento.totvs.com/hc/pt-br/articles/11795195718807-Cross-Segmento-Backoffice-Linha-Protheus-SIGAEST-Requisi%C3%A7%C3%A3o-dos-Lotes-autom%C3%A1ticos-%C3%A9-poss%C3%ADvel-alterar-a-sequ%C3%AAncia).
- TOTVS SIGAEST, 11/09/2026, [Escoamento por quantidade (Best Fit): definição e configuração](https://centraldeatendimento.totvs.com/hc/pt-br/articles/42097754377367-Cross-Segmento-TOTVS-Backoffice-Linha-Protheus-SIGAEST-Como-funciona-a-regra-de-escoamento-de-lotes-por-quantidade-Best-Fit).
- TOTVS SIGAPCP, [Regra de lote nos empenhos da MATA650](https://centraldeatendimento.totvs.com/hc/pt-br/articles/360035198573-Manufatura-Linha-Protheus-SIGAPCP-Regra-utilizada-pelo-Sistema-para-definir-a-ordem-dos-lotes-nos-empenhos).
- TOTVS TDN, [Regra de escoamento de lotes](https://tdn.totvs.com/x/LHGaPg) e [ponto de entrada MTSLDORD](https://tdn.totvs.com/pages/releaseview.action?pageId=6087842).

**Proveniência:** referências públicas do fornecedor. **Validação no ambiente DELPI: pendente.**
