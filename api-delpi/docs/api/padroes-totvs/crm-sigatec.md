# CRM TOTVS (SIGATEC) — dicionário e censo Delpi

Inventário **dicionário (SX2/SX3) + volume real** (`POST /data/sql`, allowlist desligada em dev).

| | |
|---|---|
| Extração | `POST /data/sql` + `GET /system/tables/{t}/relations\|indexes` |
| Data do censo | 19 ago 2026 |
| Playbook (colunas/índices/SX9) | [playbooks/playbook-crm-totvs-dicionario.md](./playbooks/playbook-crm-totvs-dicionario.md) |
| Produto CRM Delpi | `commercial-api` — [ADR-001](../../../../docs/12-roadmap-e-evolucao/commercial/adr/ADR-001-commercial-api.md) |
| Cliente SA1 | [cadastro-cliente.md](./cadastro-cliente.md) |
| Status 9 vs estágio 13 | [comercial-taxa-conversao-estagios.md](../comercial-taxa-conversao-estagios.md) |

## Achados do censo (o que muda o plano de CRM)

1. **Uma linha por OV.** `AD1010` tem **3767 linhas = 3767 OVs**. `AD1_REVISA` sobe **no mesmo registro** (há OV com revisão `04`/`06`); não há histórico de revisões empilhadas no cabeçalho.
2. **O funil majoritário não é o LMP.** Processo `000001 COMPONENTES` (marcado **inativo** no cadastro AC1) concentra **3075 OVs (82%)**. LMP = `000002 OPORTUNIDADE` (545) + `000003 MODIFICACAO` (147).
3. **Ganha é raro e está no LMP/modificação.** Status `9` = **91 OVs** (20 no 000002, 71 no 000003). No 000001 quase tudo é `2` Perdido (2557) ou `1` Aberto (518) — **zero ganhas**.
4. **Tarefa/agenda/visita TOTVS estão vazias.** `AD8`/`AD7`/`AD5` = 0 linhas. Meu Dia **não** se importa do SIGATEC.
5. **Prospect e contato existem, mas o vínculo na SU5 está vazio.** `SUS` 154 (101 classificado / 53 já cliente). `SU5` 514 (505 ativos) com `U5_CLIENTE`/`U5_PROSPEC` nulos; a amarração viva é `AC8` (80 SA1 + 42 SUS + 46 SA2).
6. **Proposta ADY é compartilhada (filial vazia).** Join `ADY_FILIAL = AD1_FILIAL` dá **0**. Join só `ADY_OPORTU = AD1_NROPOR` dá 3640 matches — **colide** porque SC e ES reutilizam a numeração da OV (`000001` nas duas filiais).
7. **SX2 ≠ físico.** Recorte 182 nomes: **46 com dado**, **69 vazias**, **67 sem objeto** (`42S02`). Não importar o dicionário inteiro.

```text
AC1/AC2 funil ──► AD1 OV (3767) ◄── SA1 cliente (3543) / SUS prospect (224)
                     │
      ┌──────────────┼──────────────┬──────────────┐
      ▼              ▼              ▼              ▼
    ADJ itens     AIJ trilha     ADY proposta    AD2 time
    19250 / 3710  34589          3437 (filial '') 7232
    OVs
```

`AD8` tarefa **não** aparece: tabela existe e está vazia.

## O que fazer / não fazer

**Fazer**

- Cabeçalho da OV = `AD1`; trilha LMP = `AIJ`; documento de proposta = `ADY`/`ADZ`.
- Conversão = `AD1_STATUS = '9'`, não estágio `000013`.
- Filtrar `D_E_L_E_T_ = ''`. Chave OV = `FILIAL + NROPOR` (numeração **não** é única entre filiais).
- CRM Delpi: **ler** TOTVS via api-delpi; follow-up/reminder **nascer** no commercial-api (não há AD8 para copiar).

**Não fazer**

- Tratar `000001 COMPONENTES` como morto só porque `AC1_MSBLQL = 1` — é o maior volume.
- Juntar ADY×AD1 por filial (ADY compartilhada) **nem** só por número de OV sem desambiguar filial.
- Usar `ADC` no lugar de `AIJ` para LMP.
- Confiar em `/system/tables/search?description=CRM`.
- Ligar `DATA_SQL_SKIP_TABLE_WHITELIST` em produção.

## Funil cadastrado vs uso real

| Código | Nome AC1 | Cadastro | OVs | Status 1 | Status 2 | Status 9 |
|--------|----------|----------|----:|---------:|---------:|---------:|
| `000001` | COMPONENTES | 1 Inativo | 3075 | 518 | 2557 | 0 |
| `000002` | OPORTUNIDADE | 2 Ativo | 545 | 507 | 12 | 20 |
| `000003` | MODIFICACAO | 2 Ativo | 147 | 72 | 4 | 71 |

Filiais no `AD1`: **01** 3575 OVs · **02** 192 OVs.

### Estágios atuais — 000002 OPORTUNIDADE (LMP)

| Código | Nome | OVs |
|--------|------|----:|
| 000001 | ANALISE CRITICA | 52 |
| 000002 | COTACAO | 58 |
| 000005 | PROPOSTA CONCLUIDA | 72 |
| 000006 | PROPOSTA ENVIADA/AGUARD RETORN | 292 |
| 000007 | AMOSTRA PCP | 2 |
| 000009 | RELATORIO QUALIDADE | 1 |
| 000010 | AMOSTRA ENVIADA A VENDAS | 4 |
| 000011 | HOMOLOGACAO DE PRODUTO | 2 |
| 000012 | LANCAMENTO / HOMOLOGACAO | 1 |
| 000013 | ENCERRADO | 61 |

Pico em **proposta enviada / aguardando retorno**. Estágios 000003/000004/000008 desta família não aparecem na última posição.

### Estágios atuais — 000003 MODIFICACAO

Maioria em **ENCERRADO (108)** e **PROPOSTA CONCLUIDA (17)**; 71 das 147 OVs estão `AD1_STATUS = 9`.

### Estágios atuais — 000001 COMPONENTES (legado comercial)

| Código | Nome | OVs |
|--------|------|----:|
| 000005 | APRESENTAÇÃO DA PROPOSTA | 1624 |
| 000006 | AGUARDANDO RETORNO CLIENTE | 670 |
| 000001 | APRESENTAÇÃO DA EMPRESA | 305 |
| 000004 | ELABORAÇÃO PROPOSTA COMERCIAL | 213 |
| 000003 | ELABORAÇÃO PROPOSTA TÉCNICA | 155 |
| 000011 | NEGOCIAÇÃO / FECHAMENTO | 83 |
| demais | | 25 |

## Conta, contato, vendedor

| Fato | Número |
|------|-------:|
| OV com cliente `AD1_CODCLI` | 3543 |
| OV com prospect `AD1_PROSPE` | 224 |
| Interseção cliente+prospect | 0 |
| Clientes distintos nas OVs | 75 |
| SA1 ativo | 286 |
| Prospects SUS | 154 (status 1 = 101, status 6 cliente = 53) |
| Contatos SU5 | 514 (505 ativos; **sem** código cliente/prospect na própria SU5) |
| AC8 contato×entidade | 168 (SA1 80, SUS 42, SA2 46) |
| Suspects ACH | 2 |
| Vendedores SA3 | 13 |
| OVs por vendedor | 000001 Laércio **3082**; 000009 **269**; 000007 **251**; demais &lt; 80 |
| Usuários CRM AO3 | 37 (físico **sem** `AO3_NOMUSR` — SX3 mentirosa) |
| Time AD2 | 7232 linhas / ~3777 OVs |
| Conta do vendedor ADL | 1748 |

## Documento de proposta e itens

| Tabela | Linhas | Nota |
|--------|-------:|------|
| `ADY010` | 3437 | `ADY_FILIAL` vazio; `ADY_OPORTU` e `ADY_PROPOS` preenchidos |
| `ADZ010` | 41861 | itens da proposta |
| `ADJ010` | 19250 | itens da OV; **3710** OVs têm item |
| `AD1_PROPOS` preenchido | 74 | quase não amarra proposta no cabeçalho |
| `AIJ010` | 34589 | `AIJ_HISTOR=2` (não-histórico / vigente no combo SX3) = 31172 |

`AIJ_STATUS` no dado: `1` e `2` (alinhado ao combo SX3 atraso); vazio em ~4,5 mil linhas. Não usar os rótulos “aprovado/concluído” do LMP enrichment sem homologar neste extrato.

## Núcleo já na api-delpi

| Física | Uso |
|--------|-----|
| `AD1010` | LMP, `/commercial/proposals`, `/commercial/closing-rate` |
| `ADJ010` | produtos da OV |
| `AIJ010` | `/history/events`, `/history/flow` |
| `AC1010` / `AC2010` | rótulos processo/estágio |
| `ADY010` / `ADZ010` | proposta-comercial |
| `SA1010` / `SA3010` | cliente / vendedor |
| `SU5010` / `SQB010` / `SUM010` / `SE4010` | contato / depto / cargo / cond. pgto |

## Censo de tabelas (182 nomes do recorte)

### Com dado — usar no CRM / import

| Física | Lógica | Papel | Linhas |
|--------|--------|-------|-------:|
| `AD1010` | AD1 | Oportunidade / OV | 3767 |
| `ADJ010` | ADJ | Itens da OV | 19250 |
| `AIJ010` | AIJ | Evolução / LMP | 34589 |
| `ADY010` | ADY | Proposta cabeçalho | 3437 |
| `ADZ010` | ADZ | Proposta itens | 41861 |
| `AD2010` | AD2 | Time da OV | 7232 |
| `AD9010` | AD9 | Contatos da OV | 2826 |
| `ADC010` | ADC | Histórico de OV (legado) | 3464 |
| `ADL010` | ADL | Controle de conta do vendedor | 1748 |
| `AC1010` | AC1 | Processos | 3 |
| `AC2010` | AC2 | Estágios | 37 |
| `ACZ010` | ACZ | Regras do processo | 6 |
| `AC8010` | AC8 | Contato × entidade | 168 |
| `ACA010` | ACA | Equipe de vendas | 6 |
| `ACY010` | ACY | Grupos de clientes | 1 |
| `ADK010` | ADK | Unidade de negócio | 2 |
| `SUS010` | SUS | Prospects | 154 |
| `SU5010` | SU5 | Contatos | 514 |
| `ACH010` | ACH | Suspects | 2 |
| `AO3010` | AO3 | Usuários CRM | 37 |
| `AZS010` | AZS | Papéis × usuário | 2 |
| `SUM010` | SUM | Cargos comerciais | 9 |
| `SUN010` | SUN | Tipo de encerramento | 3 |
| `SQB010` | SQB | Departamento | 28 |
| `SA1010` | SA1 | Clientes | 286 |
| `SA3010` | SA3 | Vendedores | 13 |
| `SE4010` | SE4 | Condições de pagamento | 235 |

### Com dado — satélite TOTVS (não é pipeline comercial Delpi)

| Física | Linhas | Papel SX2 |
|--------|-------:|-----------|
| `AC9010` | 13892 | Objetos × entidades (anexos/CRM objects) |
| `ACB010` | 13468 | Banco de conhecimentos |
| `ACC010` | 44 | Palavras-chave |
| `AC5010` | 7 | Eventos contato × visita |
| `AIF010` | 3079 | Histórico alteração cli/for |
| `AIA/AIB/AIC/AID` | 95–2159 | Preço fornecedor / tolerância / caixa material |
| `AI6/AI7/AI8/AI9` | 10–500 | Portal / web services |
| `SQ3010` / `SQX010` | 23 / 4 | RH (cargo / tipo curso) |

### Vazias mas físicas (SIGATEC instalado, Delpi não usa)

Inclui **`AD8010` tarefa, `AD7010` agenda, `AD5010` visita**, concorrentes, parceiros, regras de desconto/bonificação, televendas, help desk ADE, campanhas SUO.

### Só no dicionário (sem tabela SQL)

67 nomes — exemplos CRM: `AZR010` papéis, `ADM/ADN` perfil contato, `AD8` componentes de tarefa (`ADX`). Maioria `SQ*` RH e `SU*` telemarketing.

## Joins canônicos (ajustados ao dado Delpi)

```sql
-- OV (uma linha vigente; revisão no campo, não em N linhas)
AD1.D_E_L_E_T_ = ''
-- Itens / histórico: mesma filial + número
AD1.AD1_FILIAL = ADJ.ADJ_FILIAL AND AD1.AD1_NROPOR = ADJ.ADJ_NROPOR
AD1.AD1_FILIAL = AIJ.AIJ_FILIAL AND AD1.AD1_NROPOR = AIJ.AIJ_NROPOR
-- Funil
AC1.AC1_PROVEN = AD1.AD1_PROVEN
AC2.AC2_PROVEN = AD1.AD1_PROVEN AND AC2.AC2_STAGE = AD1.AD1_STAGE
-- Cliente
SA1.A1_COD = AD1.AD1_CODCLI AND SA1.A1_LOJA = AD1.AD1_LOJCLI
-- Proposta: NÃO usar filial; desambiguar OV (numeração colide 01/02)
-- ADY.ADY_OPORTU = AD1.AD1_NROPOR  + regra de filial/contexto
-- Contato: preferir AC8 / AD9 a SU5.U5_CLIENTE (vazio nesta base)
```

## Import para o CRM Minha Delpi

| Entidade Delpi | Fonte | Viável? |
|----------------|-------|---------|
| Oportunidade | `AD1` última (única) linha | Sim — guardar `branch+nropor+revisa` |
| Histórico de estágio | `AIJ` | Sim — mapear processo 000001 vs 000002/000003 |
| Produtos | `ADJ` | Sim (3710 OVs) |
| Proposta documento | `ADY`/`ADZ` | Melhor **leitura ao vivo**; join frágil |
| Prospect | `SUS` | Sim (154) |
| Contato | `SU5`+`AC8`+`AD9` | Sim, via AC8/AD9 |
| Tarefa / visita | `AD8`/`AD5` | **Não** — vazio; criar no commercial-api |
| Cliente / vendedor | `SA1`/`SA3` | Referência, não clonar cadastro |

Schemas SX3, índices SIX e SX9 completos: o playbook (snapshot de dicionário; conferir coluna física — caso `AO3_NOMUSR`).
