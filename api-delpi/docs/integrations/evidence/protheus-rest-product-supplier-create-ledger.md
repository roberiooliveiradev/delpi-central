# Ledger de evidência — `delpiprodforn` (SA5 Produto × Fornecedor)

Prova runtime TST01 (`192.168.1.233:8701/rest`, serviço `dev_rest_minha_delpi`),
2026-11-19. Objeto: `DLP04I02.PRW`.

## Write CREATE provado

```text
POST /delpiprodforn/v1/ProdForn/incluir → 200
body: {A5_PRODUTO:10080010, A5_FORNECE:999999, A5_LOJA:01,
       A5_FABR:999999, A5_FALOJA:01, A5_REFGRD:"",
       A5_NOMEFOR:'TESTE INCLUSAO', A5_CODPRF:'TST-DLP04I02-001',
       A5_DESCPRF:'TERM. LINGUETA...', codusr:'000461'}
Read-back SA5010: vínculo gravado com todos os campos ✓
```

## Cadeia causal resolvida (3 ciclos de diagnóstico)

| Build | Sintoma | Descoberta |
|---|---|---|
| `0.5.1-codusr` | 500 `server_error` | `JOB threads doesn't support remote/visual components` (srvobject.cpp) |
| `0.5.2-diag` | idem | marcadores s1–s11 → último = s3 (dentro de `Activate()`) |
| `0.5.3-diag` | 500 genérico RESTALL | **THREAD ERROR nativo**: `FWMBROWSE:ACTIVATE ← U_DMATA061 ← FWVLDACTIVATE ← Activate` — causa raiz |
| `0.5.4-diag` | **400 `official_validation`** | modelo `MATA061` carregou e ativou headless; `VldData` rejeitou `A5_REFGRD` (FWWHEN "Modo edicao nao respeitado") |
| `0.5.5-diag` | **200** | guarda `!Empty()` → `VldData`→`CommitData`→SA5 gravado |
| `0.6.0` | consolidação | marcadores removidos, handler governado integral, `cMdlId` dinâmico |

## Decisões de runtime registradas

1. **Modelo primário `MATA061`** (TDN PCOM10001, rotina automática) —
   headless comprovado. `DMATA061` = fallback (wrapper browse CRM; sua
   vld-activate instancia `FWMBrowse` em JOB).
2. **`SetVldActivate({||.T.})`** — substitui a vld-activate que
   ExecBlock-ava a user function de browse.
3. **`A5_REFGRD` vazio → `SetValue` omitido** — `X3_WHEN` rejeita
   atribuição até de `""`.
4. **AIF não recebe linha SA5** nesta rotina (provado — `AIF010` sem
   registros `SA5` pós-write). Patch `AIF_ZCDUSR` = no-op seguro.
   **Auditoria do ator (`codusr`) fica no ledger da api-delpi —
   decisão PO 2026-11-19.** Se TOTVS passar a gerar AIF p/ SA5, o
   patch volta a anotar automaticamente (não-fatal por desenho).

## Não provado (permanece marcado)

- UPDATE (PUT) — carga do vínculo pela PK sem view: BLOCKED, 501.
- READ (GET) — TO_INVENTORY, 501.
- DELETE — BLOCKED (semântica `a060VldGrv` grid vazio), 501.
- `A5_REFGRD` **não-vazio** (produto com grade) — caminho não exercitado.

## Rodada 0.7.0 — CRUD completo (pedido PO, 2026-11-19)

GET/PUT/DELETE saem de `501` para o ciclo MVC oficial, reutilizando a
cadeia headless provada no POST (modelo `MATA061` + `SetVldActivate` +
guardas `!Empty()`):

```text
Carga do documento: dbSelectArea("SA5") + dbSetOrder(2)
  (indice FILIAL+PRODUTO+...) + MsSeek(xFilial("SA5")+produto)
  → Activate() em VIEW (GET) ou UPDATE (PUT/DELETE)
  → lFindSA5Line: navega a grade (Length/GoLine/IsDeleted/GetValue)
    casando FORNECE+LOJA+FABR+FALOJA; REFGRD validado no header
  → GET: GetValue nos campos da linha (header p/ PRODUTO/REFGRD)
  → PUT: SetValue so nos atributos editaveis (identidade imutavel)
  → DELETE: DeleteLine() na linha — ultimo vinculo e rejeitado pela
    validacao oficial a060VldGrv (grid sem linhas ativas) por desenho
```

Classificação: `SOURCE_CANDIDATE` — hipóteses `VALIDAR NO TST01`:
carga por posição de alias, métodos `GoLine/IsDeleted/DeleteLine/
GetValue` do FWFormModel, produtos com múltiplos `A5_REFGRD`.
Prova pendente: compilar `0.7.0` → exercitar GET/PUT/DELETE no vínculo
`10080010×999999/01` (o DELETE dogfood a reversão do registro de teste).

## PROVEN_RUNTIME 0.7.0 — CRUD completo (TST01 :8701, 2026-11-19)

```text
GET    /consultar → 200 — data{} com todos os campos via VIEW op
PUT    /alterar   → 200 — A5_NOMEFOR 'TESTE INCLUSAO'→'TESTE ALTERADO VIA PUT' (read-back SA5010 ✓)
DELETE /excluir   → 200 — vinculo 999999/01 removido (read-back: 0 ativo; 6 vinculos do produto intactos)
GET pos-delete    → 404 not_found (correto)
```

Hipóteses `VALIDAR NO TST01` da rodada **confirmadas**: carga por
posição de alias (`dbSetOrder(2)+MsSeek`), `Activate` VIEW/UPDATE,
`Length/GoLine/IsDeleted/DeleteLine/GetValue` do FWFormModel.

### Regressão encontrada no teste negativo → fix 0.7.1

GET num vínculo real (`FABR=FALOJA=''`) retornou `400 client_error` —
a validação de identidade exigia não-vazio em `A5_FABR`/`A5_FALOJA`.
Dado real prova que vínculos sem fabricante próprio guardam `''`
(6/6 vínculos do produto 10080010). Fix: mesma regra do `A5_REFGRD`
(presença+tipo exigidos, valor pode ser vazio) → build `0.7.1`.

## Confirmação 0.7.1 (TST01 :8701, 2026-11-19)

```text
GET /consultar — vinculo real 10080010x000098/01 (A5_FABR='' A5_FALOJA='')
→ 200 | id=dlp04i02-0.7.1 | data{} com todos os campos
   (antes: 400 client_error indevido — regressao fechada)
```

CRUD SA5 = PROVEN_RUNTIME integral: CREATE/READ/UPDATE/DELETE + casos
negativos (404 pos-delete, 400 payload incompleto) + identidade com
opcionais vazios (REFGRD/FABR/FALOJA). Estado final do produto
10080010: 6 vinculos originais intactos; registro de teste removido
pela propria rota (dogfooding do DELETE).

## Rodada 0.8.x — catálogo SA5 completo (TST01 :8701, 2026-11-19)

```text
0.8.0 live:
  PUT /alterar A5_LEAD_T+A5_CODPRCA → 400 "Informe ao menos um campo"
    CAUSA: aadd(aR,"A","B","C") multi-arg grava so o 1o elemento
    (catalogo efetivo ~14 campos — padrao ADVPL documentado no DLP04I01)
  GET /consultar → 500 cru HTTPREST
0.8.1 live:
  PUT /alterar A5_LEAD_T+A5_CODPRCA → 200 MATA061 commit reconhecido
    (catalogo unitario funcional p/ escrita — PROVEN_RUNTIME)
  GET /consultar → 500 cru
0.8.2 live:
  GET /consultar → 500 cru; PUT sem attrs → 400 client_error
    id=dlp04i02-0.8.2 (build confirmado no RPO)
    console.log (dev_rest_minha_delpi) revelou a causa raiz:
      THREAD ERROR InterFunctionCall: cannot find function
      __OBJHASDATA — no ErrorBlock da linha 899 — chamada dentro
      do recover aborta a thread sem recover => 500 sem envelope.
      Erro original: oGrid:aFields = propriedade invalida no
      submodelo de grade. A familia __Obj* esta FORA do AppMap
      deste build — o veneno estava no remedio desde o 0.8.0
      (begin sequence interna + errorblock envenenado).
0.8.3 (pendente compile — VALIDAR NO TST01):
  ErrorBlock limpo (e:Description+Break); aSA5FormFields via
  oGrid:GetStruct():GetFields() (prova DLPDBG01 — id no item 3);
  AScan com == (match exato — '=' casa prefixo A5_PE/A5_PESO);
  baseline provado 0.7.x como fail-safe; xSA5JsonSafe D->DtoS.
```

Licao registrada: **nunca chamar funcao inexistente-no-build dentro
de ErrorBlock** — erro dentro do handler de erro mata a thread sem
recover e mascara a causa original. Familia `__Obj*` indisponivel
neste RPO; enumeracao de campos do form e via `GetStruct():GetFields()`.
