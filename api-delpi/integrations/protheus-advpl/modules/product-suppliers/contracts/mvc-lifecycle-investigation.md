# Investigação — ciclo de vida MVC para a fachada SA5

Hipótese de mecanismo (a comprovar, não implementar): fachada WSRESTFUL
instancia `FWLoadModel('DMATA061')`, alimenta header `DMdFieldSA5` +
linhas `DMdGridSA5` e confirma pelo commit oficial do modelo.

## CREATE (incluir vínculo)
- Modelo: header recebe `A5_PRODUTO` (+`A5_REFGRD` se grade); grid recebe
  linha `{FORNECE, LOJA, FABR, FALOJA, …attrs}`.
- Validações oficiais no caminho: `a060LinOk` (dup via `ExistChav`,
  index 9 quando `MV_GRADE`), `a060VldGrv`, triggers SX3.
- ⚠ `a060LinOk` lê `M->A5_REFGRD`/`M->A5_PRODUTO` — variável de tela; em
  contexto REST sem view pode estar vazia → checagem de duplicidade pode
  usar chave errada. `VALIDAR NO TST01` (possível necessidade de
  `M->A5_*` seed ou op alternativa).
- Assinatura exata do ciclo `FWLoadModel → SetValue/SetOperation →
  CommitData/Activate` = `TO_INVENTORY` na doc TDN/POC — não presumir.

## READ (localizar vínculo)
- Sem rotina oficial de leitura REST no fonte. Opções:
  (a) `FWLoadModel` + `Load`/GetValue pela PK — mecanismo de framework,
  mas é leitura via modelo (plausível, `TO_INVENTORY`);
  (b) leitura segue fora do `.PRW`, na superfície SQL governada da
  api-delpi — **evidência auxiliar legítima**, separada do contrato de
  escrita (precisa projetar FABR/FALOJA/REFGRD — gap G0-C).
- Decisão recomendada: READ fora do `.PRW` (b) — pendente de owner.

## UPDATE (alterar atributos do vínculo)
- Carregar modelo pela PK de 7 campos, editar apenas campos editáveis
  (NOMEFOR/CODPRF/DESCPRF/…), `a060LinOk` não revalida insert.
- Identidade é imutável — mudança de chave = delete+create, nunca update.
- Política de omitidos: **representação completa dos campos editáveis**
  até semântica comprovada — mesmo padrão fail-closed do SB1.
- `TO_INVENTORY`: semântica exata de linha em update via modelo.

## DELETE (remover vínculo) — ⚠ achado crítico
- `a060VldGrv` (posValidacao oficial) **falha quando todas as linhas do
  grid estão deletadas** (`lRet:=.F.` + Help `STR0001/STR0002`).
- Consequência no modelo: excluir **o último** vínculo de um produto via
  `DMATA061` é bloqueado pela própria rotina oficial — regra de negócio
  "produto mantém ≥1 fornecedor" ou artefato de validação? `VALIDAR NO TST01`.
- Excluir vínculo quando restam ≥2 = caminho plausível (deletar linha do
  grid + commit). Operação 5 do MenuDef (ACCESS 3) existe mas semântica
  browse×modelo não comprovada — não presumir.
- Política DELETE: permanece **bloqueada por contrato** até semântica
  oficial + aprovação do owner.

## RQ-01 — Matriz de evidência por API MVC (G2-B2, rodada 2)

| API | Assinatura usada | Evidência | Status |
|---|---|---|---|
| `FWLoadModel('DMATA061')` | função → oModel | `ViewDef` do fonte oficial (linha ~198) | PROVEN_SOURCE |
| `oModel:SetOperation(nOp)` | method | contrato MPFormModel (FWMVCDEF) | FRAMEWORK — VALIDAR NO TST01 |
| `oModel:Activate()` | method | contrato MPFormModel | FRAMEWORK — VALIDAR NO TST01 |
| `oModel:GetModel(id)` | `GetModel('DMdGridSA5')` | `a060VldGrv` no fonte oficial | PROVEN_SOURCE |
| `oModel:GetValue(field)` | grid/header | `a060LinOk` no fonte oficial | PROVEN_SOURCE |
| `sub:SetValue(field,val)` | grid/header | framework; `SetValue` não aparece no fonte | FRAMEWORK — VALIDAR NO TST01 |
| `grid:AddLine()` | method | framework (linhas do grid) | FRAMEWORK — VALIDAR NO TST01 |
| `grid:Length()/:GoLine/:IsDeleted` | methods | `a060VldGrv` no fonte oficial | PROVEN_SOURCE |
| `line:isInserted()` | method | `a060LinOk` no fonte oficial | PROVEN_SOURCE |
| `oModel:VldData()` | method | framework (bPreValidacao/bPosValidacao existem) | FRAMEWORK — VALIDAR NO TST01 |
| `oModel:CommitData()` | method | framework | FRAMEWORK — VALIDAR NO TST01 |
| `oModel:DeActivate()` | method | framework | FRAMEWORK — VALIDAR NO TST01 |
| `oModel:GetErrorMessage()` | method | framework — forma exata do retorno incerta | VALIDAR NO TST01 |
| `oModel:Load(...)` | não usado | assinatura para carga por PK incerta | VALIDAR NO TST01 (evitado) |

## Achados da rodada 2 (fonte oficial)

- `a060VldGrv` falha quando `Length()==nDeleted` — inclui o caso
  **grid vazio (0==0)**: CREATE exige `AddLine`; UPDATE falha fechado se
  as linhas não carregarem na ativação.
- `a060LinOk` é `bLinOk` do grid (`AddGrid`, linha ~143); roda dup-check
  `ExistChav` apenas em `isInserted()`, lendo `M->A5_PRODUTO`/`M->A5_REFGRD`
  do contexto de tela. Sem view, `M->` é indefinido → dup-check pode
  validar chave incompleta ou falhar — VALIDAR NO TST01, memvars não são
  preenchidos artificialmente.
- `a060VldGrv` chama `Help()` (UI) no caminho de erro — comportamento
  fora de tela = VALIDAR NO TST01.
- Relação oficial propaga `A5_FILIAL (xFilial)`, `A5_PRODUTO`, `A5_REFGRD`
  do header ao grid — o fonte não precisa reescrevê-los por linha.

## Resolução em runtime — TST01 2026-11-19 (PROVEN)

Cadeia causal completa medida por marcadores ConOut + THREAD ERROR nativo:

| Suspeita | Resultado | Evidência |
|---|---|---|
| `M->A5_*` em `a060LinOk` causaria exceção | REFUTADA | o throw aconteceu ANTES de qualquer campo — dentro de `Activate()` |
| `VldData`/callback visual | REFUTADA | `Activate()` falhou antes; após fix, `VldData` rodou e rejeitou por validação de negócio (400 governado) |
| **`Activate()` → `FWVLDACTIVATE` → `ExecBlock` → `U_DMATA061` → `FWMBrowse`** | **CONFIRMADA (causa raiz)** | THREAD ERROR: `FWMBROWSE:ACTIVATE(FWMBROWSE.PRW:671) ← U_DMATA061(DMATA061.PRX:34) ← FWVLDACTIVATE ← Activate` |

### Fatos provados

1. **`FWLoadModel("MATA061")` é o modelo headless oficial** — rotina
   automática documentada no TDN (PCOM10001). `Activate()` passa em
   thread JOB. `DMATA061` é o wrapper de browse/CRM — não usar como
   primário (vld-activate chama a user function do browse).
2. **`oModel:SetVldActivate({|| .T.})`** substitui a validação de
   ativação que ExecBlock-ava a user function — ponto de extensão
   documentado do `MPFormModel`. Mantido nos dois caminhos.
3. **`A5_REFGRD` tem `X3_WHEN`** ("Ref Grd Cfg") que rejeita atribuição
   até de string vazia — `SetValue` omitido quando vazio; o modelo
   deriva/inicializa. Mesma guarda `!Empty()` aplicada nos loops do grid.
4. **Componentes do modelo `MATA061`**: `MdFieldSA5` (header) e
   `MdGridSA5` (grid) — sem o prefixo `D` do DMATA061 (`DMd*`).
5. **`AIF` não recebe linha SA5** — `AIF010` consultada após write
   bem-sucedido: zero registros `AIF_TABELA='SA5'`. O patch `AIF_ZCDUSR`
   é no-op seguro; **auditoria do ator fica no ledger api-delpi**
   (decisão PO 2026-11-19).
6. **Prova de write**: `POST /incluir` → 200 → `SA5010` read-back
   `10080010 × 999999/01` gravado com todos os atributos.
