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
