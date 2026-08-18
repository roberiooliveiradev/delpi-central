# Homologação Onda A — KPIs C1 (workshop)

> **Status:** pronto para agenda com o Comercial  
> **Fichas:** [KPI-FICHAS.md](./KPI-FICHAS.md) (`KPI-ROL`, `KPI-CARTEIRA`, `KPI-ROL-CARTEIRA`, `KPI-HIT-RATE`)  
> **Owner nas fichas:** Comercial — a confirmar (homologação)  
> **Engineering:** usa o **baseline de código** documentado nas fichas até assinatura (`aprovada`)

## Objetivo

Validar (ou ajustar formalmente) as quatro fichas C1 sem mudar SQL neste workshop, salvo decisão explícita registrada em ata.

## Agenda sugerida (60–90 min)

| Bloco | Tempo | Conteúdo |
|-------|-------|----------|
| 1 | 10 min | Contexto: Portal = área comercial na Minha DELPI; GR/TV depois |
| 2 | 20 min | ROL — fórmula atual SD2−SD1 + meta SI |
| 3 | 15 min | Hit rate — AD1 status 9; cohorts abertura vs aceite |
| 4 | 20 min | Carteira — snapshot `valor_aberto`; ≠ PCP |
| 5 | 15 min | ROL e carteira — lado a lado vs soma |
| 6 | 10 min | Próximos passos e owners |

## Critério de saída da Onda A (docs)

- Cada ficha C1 em `em_validacao` **ou** `aprovada` (ou `bloqueada` com motivo)  
- Checklists das fichas respondidos (sim/não/adiado)  
- Decisão explícita: **manter lado a lado** ou **autorizar soma** (com bases)  
- Hit rate: **preservar** ou **abrir mudança de regra** (requer ciclo à parte)

## Perguntas por ficha

### KPI-ROL

1. Os impostos descontados no SQL (ICM, IMP5, IMP6) definem o «líquido» oficial?  
2. Competência por data de emissão da NF (`D2_EMISSAO`) está correta?  
3. Devoluções SD1 (CF 1201/2201 / tipo D) estão corretas?  
4. A meta SI usada no % está correta para a Visão geral?

### KPI-HIT-RATE

1. Manter ganhas (status 9 / aceite no período) ÷ revisões abertas no período?  
2. Cada revisão no denominador é intencional?  
3. Há intenção de mudar para ganhas ÷ (ganhas+perdidas) do mesmo cohort? (**fora** do cockpit atual se sim)

### KPI-CARTEIRA

1. `valor_aberto` da lista de pedidos é a métrica oficial de carteira?  
2. É bruto ou líquido?  
3. Confirma: carteira **não** é programação PCP?

### KPI-ROL-CARTEIRA

1. Confirma **lado a lado** na Visão geral (sem soma automática)? **Sim no código** — soma UI **bloqueada** até ficha aprovada (`.cursor`).  
2. Se quiser soma depois: qual base única (líquido/bruto) e fórmula?

## Registro da reunião (preencher)

| Campo | Valor |
|-------|-------|
| Data | |
| Participantes | |
| Decisões | |
| Fichas → status | |
| Próxima revisão | |

## Relação com implementação

O plano de cockpit (MTD/YTD, card carteira, helps) **pode** seguir em paralelo com baseline `em_validacao`. Mudança de fórmula TOTVS **não** entra sem nova ata.
