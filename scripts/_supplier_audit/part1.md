# Auditoria do Modelo de Fornecedores — TOTVS Protheus (DELPI)

> CLASS = READ / INVENTORY / AUDIT. Nenhuma escrita foi executada. Todas as consultas foram SELECT read-only (com `NOLOCK` apenas em contagens agregadas), dicionário SX\* e catálogo `sys.*`.
> Base de evidência: SQL Server `srv-db01` (192.168.1.230), database `DELPI`, dicionários por empresa `SX?010` (empresa 01), `SX?030`, `SX?040`, `SX?050`.
> Convenção de evidência: **PROVEN** (evidência direta em dicionário/schema físico/dados/código), **TO_INVENTORY** (existe lead mas sem prova), **UNKNOWN** (não determinável com as capabilities disponíveis), **NOT_APPLICABLE**.

# 1. Executive Summary

- O cadastro de fornecedores é a tabela **`SA2`**, física **`SA2010`** na empresa 01 (MODO=C, compartilhada entre filiais — `A2_FILIAL` vazio em 100% dos registros). Empresas 03, 04 e 05 possuem tabelas próprias (`SA2030`, `SA2040`, `SA2050`) com bases distintas. **[PROVEN]**
- A SA2010 possui **248 campos de dicionário** (SX3010), dos quais 3 são virtuais (`A2_DTPAWB`, `A2_NOMFAV`, `A2_PAISDES` — não existem fisicamente) e o físico tem +5 colunas de sistema (`D_E_L_E_T_`, `R_E_C_N_O_`, `R_E_C_D_E_L_`, `S_T_A_M_P_`, `I_N_S_D_T_`). **[PROVEN]**
- **Identidade física**: PK `R_E_C_N_O_` + índice único `SA2010_UNQ (A2_FILIAL, A2_COD, A2_LOJA, R_E_C_D_E_L_)`. Chave de negócio = **`A2_COD` + `A2_LOJA`** (filial em branco). **CNPJ/CPF não é chave e não é único** (32 valores duplicados, inclusive entre códigos distintos). **[PROVEN]**
- **Geração de código**: `A2_COD` tem default `GETSXENUM("SA2")` nas empresas 01 e 05; nas empresas 03/04 o default não existe (entrada manual). Padrão observado: sequencial numérico 6 dígitos (`003929` atual máximo), com exceções manuais (`VIAGEM`, `FISCO`, `INPS`...). A tabela de numerador `SXE` **não existe** na base DELPI — mecanismo de resolução do próximo número é **TO_INVENTORY** (provavelmente lado appserver/licença TOTVS ou rotina MATA020). **[PROVEN parcial + TO_INVENTORY]**
- **Customizações DELPI na SA2**: apenas 3 campos de usuário — `A2_YROHS` (RoHS?, usado em 67% dos registros), `A2_YFGEN` (For. Genérico) e `A2_ZTABPRC` (Tab. Preço Compra, F3→AIA). Não há tabelas Z\* de fornecedor. **[PROVEN]**
- **Tabelas relacionadas materialmente usadas**: `SA5` Produto×Fornecedor (40.671 linhas, tabela cadastral separada — NÃO criada junto com SA2), `SAD` Grupo×Fornecedor (5.512), `AIA`/`AIB` tabelas de preço (329/8.616), `AIC` tolerância de entrada (636). Contatos/dados bancários ficam **dentro da SA2** (tabelas DKI/D30/FV6 existem mas têm 0 linhas). **[PROVEN]**
- **Lookups obrigatórios por validação** (SX9/X3): `SE4` cond. pagamento, `SED` natureza, `SA6` banco, `SA4` transportadora, `SYA` país, `CCH` país BACEN, `CC2` município IBGE, `CT1` conta contábil, `SX5` tabelas genéricas (12=UF, Y7=grupo, 58=forma pgto, T3=segmento, 48, 83, MF...), `SA1` cliente vinculado, `SRA` funcionário vinculado, `SAE`, `ACJ` DDI, `SYR` origem. **[PROVEN]**
- **Consumidores transacionais** (apenas leem SA2): SC1, SC7, SC8, SD1, SF1, SE2, SE5, SF3, SFT, SCY, SCE, SDS, SFJ — centenas de milhares de linhas. **[PROVEN]**
- **Rotina dona do cadastro**: `MATA020` (referenciada na SX2). A API/ponte deverá respeitar as mesmas validações. **[PROVEN]**
- Inventário de relacionamentos: **607 relações SX9 com SA2 como dominante** — a maioria de módulos TOTVS não instalados/sem dados na DELPI. Classificação: `COMPLETE_BY_AVAILABLE_METADATA` para a metadesesencial; `INCOMPLETE` para módulos verticais sem evidência de uso.
- **Capacidade não coberta**: a lógica interna da rotina MATA020 (ADVPL server-side) e o contrato da API/ponte do Gabriel não são introspectáveis por esta auditoria → seções `Questions for Gabriel` e `Capability Gaps`.

# 2. Scope and Evidence

| Fonte | Uso | Cobertura |
|---|---|---|
| SX2010/SX2030/SX2040/SX2050 (SX2) | tabela/alias/modo/chave única/rotina | completa p/ SA2, SA5 e tabelas relacionadas |
| SX3010/SX3030/SX3040/SX3050 (SX3) | 100% dos campos + VALID/RELACAO/F3/CBOX/WHEN | completa |
| SIX010 (SIX) | índices lógicos SA2/SA5 | completa |
| SX9010 (SX9) | relações declaradas dominante/filho | completa (607+41) |
| SXB010 (SXB) | consulta padrão FOR | completa |
| SX5010 (SX5) | domínios genéricos usados pela SA2 | parcial — apenas tabelas referenciadas por SA2 |
| sys.tables/sys.columns/sys.indexes/sys.triggers | schema físico, PK/UNQ, triggers | completa |
| Dados SA2010/SA5010 (read-only, NOLOCK) | fill rates, domínios, duplicidades | completa p/ perguntas da auditoria |
| Código api-delpi | evidência de uso vigente (read) | completa p/ leituras existentes |
| Rotina MATA020 (ADVPL) | **indisponível** — binário/appserver | CAPABILITY_GAP |
| API/ponte Gabriel | **inexistente no repo** — ainda não implementada | N/A |

# 3. Supplier Data Model Overview

```text
SA2 / SA2010 — FORNECEDOR (master, MATA020)                     [empresa 01]
├── SA5 / SA5010 — Amarração Produto × Fornecedor (MATA061)     [cadastral, NÃO automática]
│     ├── AIA/AIB — Tabela de Preços do Fornecedor              [cadastral, opcional]
│     ├── AIC — Tolerância na Entrada de Material               [cadastral, opcional]
│     └── SAD — Amarração Grupo × Fornecedor                    [cadastral, 5.5k regs usados]
├── Lookups obrigatórios conforme campos enviados:
│     SE4 (cond. pagto) · SED (natureza) · SA6 (banco) · SA4 (transportadora)
│     SYA (país) · CCH (país BACEN) · CC2 (município IBGE) · CT1 (conta contábil)
│     SX5 (UF '12', grupo 'Y7', forma pgto '58', segmento 'T3', '48', '83', 'MF')
│     SA1 (cliente vinculado) · SRA (funcionário) · SAE · ACJ (DDI) · SYR (origem)
├── Cadastro-complemento existentes mas VAZIOS na DELPI:
│     DKI (contatos×forn.) · D30 (compl. SIMP) · DD1 (docs exigidos) · FV6 (dados pagto favorecido) · G4R
├── Apenas-dicionário (módulos sem tabela física):
│     D2C (contatos) · COP · DD5 · FTG · BA4 · G4S · SS3
└── Consumidores transacionais (read-only do cadastro):
      SC1 Solicitação · SC7 Pedido Compra · SC8 Cotação · SF1 NF Entrada
      SD1 Itens NF Entrada · SE2 Contas a Pagar · SE5 Mov. Bancária
      SF3/SFT Livros Fiscais · SCY Hist. Pedidos · SCE · SDS · SFJ
```

# 4. Authoritative Master Table

| Propriedade | Valor | Evidência |
|---|---|---|
| Alias | `SA2` | SX2010.X2_CHAVE |
| Tabela física (emp. 01) | `SA2010` | SX2010.X2_ARQUIVO + sys.tables |
| Outras empresas | `SA2030` (emp 03), `SA2040` (emp 04), `SA2050` (emp 05) | sys.tables + SX2030/40/50 |
| Descrição | Fornecedores / Suppliers | X2_NOME |
| MODO/MODOUN/MODOEMP | C / E / E (compartilhada entre filiais; unidade e empresa exclusivas) | SX2010 |
| Rotina owner | `MATA020` (módulo Compras) | SX2010 |
| Chave única lógica | `A2_FILIAL + A2_COD + A2_LOJA` | X2_UNICO |
| PK física | `R_E_C_N_O_` (`SA2010_PK`) | sys.indexes is_primary_key |
| Único físico | `SA2010_UNQ (A2_FILIAL, A2_COD, A2_LOJA, R_E_C_D_E_L_)` | sys.indexes is_unique |
| TTS/auditoria | `X2_TTS=S`; trigger física `SA2010_STAMP`; tabela `SA2010_TTAT_LOG` (estrutura pronta, 0 linhas) | SX2010 + sys.triggers |
| Registros | emp01: 3.663 (19 deletados) · emp03: 226 · emp04: 68 · emp05: 314 | COUNT read-only |
| Campos dicionário | 248 (emp01) / 242 (emp03/04) / 248 (emp05) | SX3 |

Nota empresas: o registro de empresas (SM0) não existe nesta base — nomes das empresas 03/04/05 = **UNKNOWN**. Diferença 248↔242 campos: empresas 03/04 não possuem `A2_PABCB, A2_ECDTEX, A2_ECSEQ, A2_ECFLAG` (SYS) nem `A2_YFGEN, A2_YROHS` (DELPI).

# 5. SA2010 / SA2 — Complete Schema (SX3010, empresa 01)

Legenda de metadata: `V`=X3_VALID · `DEF`=X3_RELACAO (init/default) · `F3=`consulta padrão · `CBOX`=domínio enumerado · `WHEN`=condicional · `OBRIG1`=X3_OBRIGAT flag pos.1 · `DELPI`=PROPRI=U (custom) · `SYS`=PROPRI=S.

| # | Campo | Tipo | Tam | Dec | Título (SX3) | Metadata |
|---|---|---|---|---|---|---|
