# Inventário — modelo oficial MATA061 / SA5

Proveniência: `Delpi-ti/protheus-erp`@master — `73. CRM/Dmata061.prx`
(HEAD upstream INCONCLUSIVE, última ref. 86616df50b17; espelho
`docs/13-fontes-totvs-protheus/` blob `b45cc9333c410a58d5836f78b79a140c6056c9c6` @ be614649b7)
e `73. CRM/MATA010M_DLP.PRW` (blob `a56c2a5079991742a544c39dd75fde8f3e9eda48`).

| Elemento | Assinatura/local | Papel | Estado |
|---|---|---|---|
| `DMATA061` | `user Function DMATA061()` | browse FWMBrowse SA5, `dbSetOrder(2)` | PROVEN_SOURCE |
| `MenuDef` | static | ops 1 Vis / 3 Inc / 4 Alt / 5 Exc (ACCESS 3); PE `MT061MN` | PROVEN_SOURCE |
| `ModelDef` | static → `MPFormModel():New('DMATA061', NIL, {a060VldGrv}, NIL, NIL)` | **model id `DMATA061`** | PROVEN_SOURCE |
| `DMdFieldSA5` | `AddFields` c/ `FWFormStruct(1,'SA5', filtro)` | header = produto+refgrd (`A5_PRODUTO`, `A5_NOMPROD`, `A5_REFGRD`, `A5_DESREF`) | PROVEN_SOURCE |
| `DMdGridSA5` | `AddGrid` c/ `MA061MldStruct()` + lineOk `a060LinOk` | grid = vínculos fornecedor do produto | PROVEN_SOURCE |
| `SetRelation` | `A5_FILIAL←xFilial`, `A5_PRODUTO←A5_PRODUTO`, `A5_REFGRD←A5_REFGRD`, `IndexKey(2)` | header dirige o grid | PROVEN_SOURCE |
| `SetPrimaryKey` | `{FILIAL,FORNECE,LOJA,PRODUTO,FABR,FALOJA,REFGRD}` | **identidade 7 campos** | PROVEN_SOURCE |
| `SetUniqueLine` (grid) | `{FORNECE,LOJA,PRODUTO,FABR,FALOJA,REFGRD}` | anti-duplicidade na linha | PROVEN_SOURCE |
| `a060LinOk` | line-ok do grid | no insert, `ExistChav` dup-check; usa `M->A5_REFGRD`/`M->A5_PRODUTO` | PROVEN_SOURCE ⚠ usa `M->` (contexto de tela) |
| `a060VldGrv` | posValidacao do MPFormModel | **rejeita salvar se TODAS as linhas do grid estão deletadas** | PROVEN_SOURCE — impacto DELETE |
| `MA061MldStruct` | static `(lNomeProd)` | struct do grid SA5; **reusada por MATA010M_DLP** (comentário oficial "usado tambem em outros modelos") | PROVEN_SOURCE — reusável |
| `MA061ViewStruct` | static | struct da view; condicional `nModulo==21` (QIE) | PROVEN_SOURCE — só p/ view |
| `A061CPOCQ` | static | lê SX3 p/ desobrigar campos CQ fora do módulo 21 | PROVEN_SOURCE — interna |
| `IntegDef` | static → `MATI060(cXML,...)` | ponte EAI; EAI não configurado (G0-C) | PROVEN_SOURCE, não usar |
| `ViewDef` | static → `FWLoadModel('DMATA061')` + `FWFormView` | prova que o model id é carregável | PROVEN_SOURCE |

### Pontos de entrada / gatilhos identificados
- `MT061MN` — PE do MenuDef (opções de rotina).
- Trigger `A5_FORNECE→A5_LOJA` via `MTA010Proc()` — adicionada no grid **MATA010** (`FwStruTrigger`), não no modelo independente.
- `MODEL_FIELD_OBRIGAT` manipulado em `MA061MldStruct` conforme `nModulo`.

### Funções que NÃO são contrato estável para chamada externa
`a060LinOk`, `a060VldGrv`, `A061CPOCQ`, `IntegDef`, `MenuDef`, `ViewDef` —
callbacks do modelo; a fachada não deve invocá-las diretamente, apenas
instanciar `FWLoadModel('DMATA061')` e deixá-las disparar no ciclo oficial.

### Model061 (submodelo na MATA010 — alternativa B)
- Só ativa se `lMATA061` (`VerifyAccess`: `"SA5" $ MV_CADPROD` + `FwAliasInDic`)
  e `IsAccessByOperation(nOpc, aMATA061Access)` — permissões por operação.
- Grid `MdGridSA5` sobre `SB1MASTER`; `SetUniqueLine` **sem `A5_REFGRD`**
  ({FORNECE,LOJA,FABR,FALOJA}) — produto com grade pode colidir.
- HACK documentado: o id `MdGridSA5` é consumido por MATA060 — não renomear.
- Opera SA5 **dentro** do cadastro de produto — acoplamento indesejado
  para CRUD independente do vínculo.

### Runtime
Presença compilada de DMATA061/MATA061 no RPO e comportamento do modelo
sob contexto REST (sem view/`M->`) = `TO_INVENTORY` / `VALIDAR NO TST01`.
