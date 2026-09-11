# Portal de Engenharia — fichas de indicadores

> **Status:** baseline de indicadores para a Visão geral.  
> **Regra:** Strategic Indicators é owner das metas/scores estratégicos; o Portal não recalcula IDD.

## 1. Indicadores estratégicos confirmados

O repositório possui dois IDs canônicos para `department_id=engineering`:

```text
engineering-projects-on-time
engineering-transforma-plus
```

Engenharia utiliza agregação departamental **consolidated**. Não inferir score por filial a partir de ausência/presença de `01`/`02`.

## 2. KPI — Projetos concluídos no prazo

| Campo | Definição |
|---|---|
| ID canônico | `engineering-projects-on-time` |
| Nome de negócio | `% de Projetos Concluídos no Prazo` |
| Fonte do realizado | Engenharia/LMP via provider SI/api-delpi |
| Fonte da meta | Strategic Indicators |
| Unidade | `%` |
| Direção | `higher_is_better` |
| Escopo estratégico | consolidado |
| Owner do score | Strategic Indicators |

### Semântica

Mede aderência de projetos/LMPs ao prazo conforme regra canônica do provider atual. O Portal não deve reescrever a definição com base em interpretação visual do dashboard legado.

### Exibição

Quando o contrato SI fornecer, apresentar separadamente:

- realizado;
- meta do período/comparável;
- meta de referência;
- score/IDD;
- status/tendência.

Usar help contextual para explicar o período sem expor campos técnicos.

## 3. KPI — Ganhos TRANSFORMA+

| Campo | Definição |
|---|---|
| ID canônico | `engineering-transforma-plus` |
| Nome de negócio | `Ganhos Financeiros do TRANSFORMA+ DELPI` |
| Fonte do realizado | provider TRANSFORMA+ integrado ao SI |
| Fonte da meta | Strategic Indicators |
| Unidade | monetária conforme contrato vigente |
| Direção | `higher_is_better` salvo mudança canônica |
| Escopo estratégico | consolidado |
| Owner do score | Strategic Indicators |

### Semântica

O Portal pode mostrar resumo e drill para Transformômetro, mas não deve recalcular ganhos a partir de dados internos nem substituir a fonte estratégica.

## 4. Indicadores operacionais candidatos

Os itens abaixo podem enriquecer a Visão geral ou páginas de detalhe, porém não devem ser tratados como KPI estratégico sem catálogo SI oficial:

- LMPs totais no período;
- LMPs em atraso;
- lead time médio/mediano;
- distribuição por status;
- aging por etapa;
- não conformidades abertas/atrasadas;
- taxa de retorno/retrabalho quando o contrato real sustentar;
- volume de tarefas pendentes;
- documentos/desenhos acessados recentemente apenas como atividade, não KPI de desempenho.

Cada indicador operacional precisa de ficha própria antes de virar card gerencial.

## 5. Template obrigatório para novo KPI

```text
ID:
Nome de negócio:
Pergunta que responde:
Owner da regra:
Fonte do realizado:
Fonte da meta:
Fórmula/contrato:
Unidade:
Direção de performance:
Natureza temporal: intervalo | snapshot | estado atual
Escopo: consolidado | filial | pessoa | projeto
Filtros suportados:
Null/empty semantics:
Parcial permitido?:
Drill/deep link:
Help:
Testes de regressão:
```

Nenhum card novo deve ser implementado sem preencher os campos materiais.

## 6. Natureza temporal

A UI não deve aplicar o mesmo rótulo temporal a todos os KPIs.

Exemplos:

- indicador estratégico por período → intervalo;
- quantidade de LMPs atualmente atrasadas → estado atual/snapshot;
- lead time concluído → intervalo sobre itens concluídos, se essa for a regra do owner.

Rótulos `MTD`, `YTD`, `Meta parcial` e similares só entram quando o contrato canônico realmente sustentar essa semântica.

## 7. Filtros

Como Engenharia é consolidada no SI, o filtro da Visão geral deve ser desenhado a partir das capacidades reais das fontes.

Não adicionar `Filial` global apenas porque outros portais possuem esse filtro. Se LMP operacional suportar filial, o recorte pode existir na página LMP sem alterar o score estratégico consolidado.

## 8. Cores/status

Não inferir cores por “quanto maior melhor” no MFE sem `performance_direction`/regra canônica. Usar status/score do SI ou regra documentada pelo owner.

## 9. Partial data

Se TRANSFORMA+ estiver indisponível e LMP continuar disponível:

- Visão geral pode marcar parcial;
- card TRANSFORMA+ mostra indisponível;
- card de projetos continua com dado válido;
- score departamental não deve ser recalculado no frontend removendo o indicador ausente.

## 10. Paridade com `dashboard-engineering`

Antes de deprecar o legado, comparar para o mesmo período:

- realizado;
- meta;
- score;
- unidade/formatação;
- arredondamento;
- fonte;
- timestamp/freshness;
- comportamento em falha parcial.

Diferença intencional exige decisão documentada e aceite do Product Owner.

## 11. Ajuda

A página Help/FAQ deve explicar em linguagem de negócio:

- o que significa “projetos concluídos no prazo”;
- de onde vêm os ganhos do TRANSFORMA+;
- diferença entre realizado, meta e Nota IDD;
- por que Engenharia aparece consolidada;
- diferença entre indicador estratégico e operacional.
