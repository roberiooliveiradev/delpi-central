# Guia de desenvolvimento — Rotas REST Protheus (ADVPL/WSRESTFUL)

Guia interno para criar novas rotas REST customizadas no Protheus no padrão que a DELPI já usa.
Cobre **o nosso lado do trabalho**: como escrever o `.PRW`, de onde saem os contratos das rotinas
oficiais e quais boas práticas seguir. O processo de compilação no RPO é responsabilidade da
equipe TOTVS e está fora do escopo deste documento.

> Documento irmão: `protheus-write-integration-playbook.md` (topologia, superfície api-delpi,
> rastreio, homologação live). Este guia foca exclusivamente no **fonte ADVPL** que publica a rota.

---

## 1. Princípio central

> **A API nunca escreve direto no banco. A API chama a rotina oficial do ERP.**

Toda rota REST que escreve dados no Protheus é uma **fachada fina** sobre uma rotina oficial
(`MATA***`, `FINA***`, `CTBA***`…) executada pelo **mecanismo oficial daquela rotina** —
`MSExecAuto` quando a rotina o suporta (ex.: `MATA010`), ou o **modelo MVC oficial** quando a
rotina é MVC (ex.: `MATA061`/SA5, `FWLoadModel`+`ModelCommit`, cuja ativação Model-2 exige
validação). A rotina oficial é a mesma que a
tela do ERP executa — ela valida, aplica gatilhos, dispara pontos de entrada e grava as tabelas
relacionadas. Nosso `.PRW` só faz:

```
HTTP request (JSON)
   → parse + validação de entrada
   → montar arrays no formato ExecAuto
   → MSExecAuto(rotina oficial)
   → capturar lMsErroAuto / GetAutoGrLog
   → resposta HTTP normalizada
```

Consequências:

- Se a rotina oficial rejeita, a API devolve o erro oficial — nunca contornamos validação.
- Se a rotina oficial faz efeitos colaterais (títulos, estoque, livros fiscais), eles acontecem
  porque a rotina os faz — não porque o fonte os executa manualmente.
- Customizações do ambiente (pontos de entrada `M***FIM`, validações `A030***`, triggers de
  campo) rodam automaticamente, porque a rotina as dispara.

---

## 2. Anatomia de uma rota WSRESTFUL

Referência de produção: `docs/13-fontes-totvs-protheus/04. Estoque/DLP04I01.PRW`
(serviço `delpiproduto`, publicado em `192.168.1.233:8061/restall/delpiproduto/v1/...`; `:8701` é REST alternativo datado 2026-11-19).

### 2.1 Declaração do serviço — é isto que publica a rota

```advpl
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'

WSRESTFUL DelpiFaturamento DESCRIPTION "Api REST para Faturamento Delpi" FORMAT "application/json"

    WSMETHOD POST faturar DESCRIPTION 'Fatura itens de pedido de venda (MATA460)' PATH '/v1/faturar' WSSYNTAX '/v1/faturar' TTALK "v1"
    WSMETHOD PUT  faturar DESCRIPTION 'Altera faturamento'                    PATH '/v1/faturar' WSSYNTAX '/v1/faturar' TTALK "v1"

END WSRESTFUL
```

Regras:

- **`WSRESTFUL <Nome>`** — o nome vira o **segmento de URL**: o serviço `DelpiProduto` publica
  sob `/rest/delpiproduto/...`. Escolha o nome como escolheria o path público — é contrato.
- **`WSMETHOD <VERBO> <funcao>`** — um bloco por verbo+path. A `<funcao>` é o nome do handler.
- **`PATH '/v1/...'`** — segmento após o nome do serviço. Mantenha versionado (`/v1/`).
- Uma classe `WSRESTFUL` compilada no RPO aparece automaticamente no catálogo `/restall`.
  Não existe registro separado: **compilou, a rota existe**.

### 2.2 O handler — `WSRECEIVE`

```advpl
WSMETHOD POST faturar WSRECEIVE WSRESTFUL DelpiFaturamento

Local aArea      := GetArea()
Local cJSON      := Self:GetContent()       // body bruto
Local oDados     := JsonObject():New()
Local oJsonRet   := JsonObject():New()
Local cErroBlk   := ''
Local oException := ErrorBlock({|e| cErroBlk := e:Description + e:ErrorStack, Break(e) })

PRIVATE lMsErroAuto    := .F.
Private lMsHelpAuto    := .T.
Private lAutoErrNoFile := .T.

Self:SetContentType("application/json")
oDados:FromJson(cJSON)

Begin Sequence
    // ... montagem dos arrays + MSExecAuto ...
    Recover
    ErrorBlock(oException)
    oJsonRet := RETOBJ(oJsonRet,"400","Erro",cErroBlk,cIdtoken)
End sequence

If lRet ; Self:setStatus(200) ; Else ; Self:setStatus(400) ; EndIf
Self:setResponse(oJsonRet:toJson())

FreeObj(oJsonRet) ; FreeObj(oDados) ; RestArea(aArea)
Return .T.
```

Checklist do handler (seguir sempre, nesta ordem):

1. `GetArea()` no início, `RestArea(aArea)` no fim — nunca vazar área de trabalho.
2. `ErrorBlock` + `Begin Sequence/Recover` envolvendo **toda** a lógica — erro de runtime vira
   400 controlado, não crash do thread REST.
3. `PRIVATE lMsErroAuto := .F.` **antes** do `MSExecAuto` — tem que ser `PRIVATE` (não `LOCAL`):
   a rotina oficial escreve nesse escopo. `lMsHelpAuto := .T.` suprime telas de help; sem ela a
   rotina pode travar esperando interação que nunca vem.
4. `FreeObj` de **todos** os `JsonObject()` criados — handlers REST vazam memória sem isso.
5. `Return .T.` — obrigatório para o broker REST tratar como sucesso de método.

---

## 3. MSExecAuto — o contrato que importa

### 3.1 Forma geral

```advpl
MSExecAuto({|x,y,z| MATA460(x,y,z)}, aItens, aCabec, aParam)
```

- **Code block**: recebe os argumentos e chama a rotina oficial. Para rotinas com suporte a
  ExecAuto, **sempre** `MSExecAuto`, nunca chamada direta (`MATA460(...)`) — o ExecAuto
  prepara o ambiente automático (empresa/filial, supressão de telas, captura de erros).
  Rotinas **MVC** (ex.: `MATA061`) **não** usam arrays ExecAuto: a persistência vai pelo
  modelo oficial instanciado (`FWLoadModel`), preservando validações e pontos de entrada.
- **Arrays**: cada rotina tem o seu formato. O elemento atômico é a tripla:

  ```advpl
  {"CAMPO", valor, NIL}
  ```

  `NIL` na terceira posição = validação padrão do dicionário (SX3). Alguns campos aceitam
  expressão (gatilho) no lugar de valor — usar só quando a documentação da rotina pedir.

- **Operação** (quando aplicável): `3`=inclusão, `4`=alteração, `5`=exclusão. Nem toda rotina
  usa — o `MATA460` não recebe código de operação, recebe `aParam` (perguntas).

### 3.2 Arrays típicos

| Rotina | Cabeçalho | Itens | Extra |
|---|---|---|---|
| `MATA010` (produto) | `aSB1` com `{B1_*, v, Nil}` | — | op `3/4/5` |
| `MATA410` (pedido) | `aCabec` `{C5_*, v, Nil}` | `aItens` = array de sub-arrays `{C6_*, v, Nil}` | op `3/4/5` |
| `MATA460` (faturamento) | `aCabec` `{F2_*, v, Nil}` (SF2) | `aItens` = sub-arrays `{D2_PEDIDO, D2_ITEMPV, D2_QUANT}` apontando o pedido | `aParam` = perguntas `MV_PAR01..n` |
| `FINA060` (borderô/títulos) | — | `aBor`, `aTit` | op `3` |

Regras dos itens:

- Um **sub-array por linha** — `aItens` é array de arrays.
- `{"LINPOS","C6_ITEM","01"}` marca o item na alteração; `{"AUTDELETA","S"}` remove linha.
- Campos ausentes **não são ignorados** — dependendo da rotina, são **zerados**. Foi o bug real
  do `delpiproduto`: a rotina lê todos os 21 `B1_*` incondicionalmente; um PUT parcial apagaria
  os campos omitidos. **Regra: em rotinas de cadastro, sempre enviar a representação completa.**

### 3.3 Captura de erro — sempre igual

```advpl
If lMsErroAuto
    aLogAuto := GetAutoGrLog()
    For nY := 1 To Len(aLogAuto)
        cErro += aLogAuto[nY] + CRLF
    Next nY
    oJsonRet := RETOBJ(oJsonRet,"400","Erro",cErro,cIdtoken)
Else
    oJsonRet := RETOBJ(oJsonRet,"200","OK","...",cIdtoken)
EndIf
```

`lMsErroAuto` é a única fonte de verdade do resultado. `GetAutoGrLog()` devolve o log oficial
da rotina — é o que vai no response pro consumidor diagnosticar.

---

## 4. De onde sai o contrato da rotina (ordem de investigação)

Antes de escrever **qualquer** linha de `aadd`, obter o contrato nesta ordem:

| # | Fonte | O que dá |
|---|---|---|
| 1 | **Fontes DELPI** (`docs/13-fontes-totvs-protheus/`) | Prova de que a rotina é a que o ambiente usa (ex.: PE `M460FIM` ⇒ faturamento = MATA460), padrões de chamada já existentes (`DLP05F01` ⇒ `MSExecAuto(mata410, aCabec, aItens, 4)`) |
| 2 | **TDN TOTVS** (buscar "ExecAuto MATA###") | Assinatura oficial documentada, exemplos de arrays, campos obrigatórios |
| 3 | **Catálogo `/restall`** | Rotas **já publicadas** — pode já existir o endpoint; separar aba ADVPL (classes) da aba TLPP (endpoints REST) |
| 4 | **POC no TST01** | Verdade final — o `aParam` e a lista de campos variam por release/dicionário; nenhum documento substitui o teste |

Se a rotina **não tem ExecAuto documentado**, assumir que não é preparada para automação
(evidence: suporte TOTVS responde isso explicitamente). Alternativas: outra rotina irmã
documentada, ou avaliar com a TOTVS se há interface oficial.

Regra de evidência para cada campo que vai no array:

```text
CONFIRMADO_NO_FONTE     → existe em fonte DELPI/TOTVS que já roda
CONFIRMADO_NO_TDN       → exemplo oficial documentado
HIPOTESE_A_VALIDAR      → deduzido; obrigatoriamente marcado no fonte
```

Todo campo `HIPOTESE_A_VALIDAR` fica comentado no fonte com `VALIDAR NO TST01` — o rascunho
nunca finge precisão que não tem.

---

## 5. Contrato JSON — design de entrada e saída

### 5.1 Entrada

- **Nomes de campo = nomes Protheus** (`B1_DESC`, `F2_CLIENTE`, `D2_PEDIDO`). Não inventar
  alias amigável no `.PRW` — a camada que traduz contrato é a api-delpi, não o Protheus.
- **Representação completa para cadastros** (ver §3.2). Documentar no cabeçalho do fonte a
  lista exata de campos que a rotina lê.
- **Validar antes do ExecAuto**: campos obrigatórios vazios, tipos (`Val()`, `STOD()`),
  arrays vazios — devolver 400 com mensagem clara **sem chamar a rotina**.

### 5.2 Saída — `RETOBJ` padronizado

```advpl
oJsonRet := RETOBJ(oJsonRet, "200", "OK",   "Registro integrado com sucesso!", cIdtoken)
oJsonRet := RETOBJ(oJsonRet, "400", "Erro", cErro,                            cIdtoken)
```

Sempre o mesmo shape: `{code, status, message, idtoken}`. O log oficial da rotina vai no
`message` — não reformatar, o texto é o que o ERP devolveu.

### 5.3 Idempotência

O ERP não é idempotente. O contrato deve deixar claro:

- `POST` de inclusão duplicado = o que a rotina oficial fizer com duplicidade (geralmente rejeita
  por chave — confiar nela).
- Em faturamento/operações de lote, 1 chamada = 1 operação de negócio (ex.: 1 NF por POST).
  Não aglutinar silenciosamente na v1.

---

## 6. Boas práticas — checklist de código

### Fazer

- [ ] `WSRESTFUL` nomeado como o path público (é contrato de URL)
- [ ] `PATH` versionado (`/v1/`)
- [ ] `PRIVATE lMsErroAuto/lMsHelpAuto/lAutoErrNoFile` antes do ExecAuto
- [ ] `ErrorBlock`+`Begin Sequence` em todo o handler
- [ ] Validar entrada antes de chamar a rotina
- [ ] `GetAutoGrLog()` completo no response de erro
- [ ] `FreeObj` em todo `JsonObject`; `RestArea(aArea)` no fim
- [ ] Cabeçalho `{Protheus.doc}` documentando: contrato ExecAuto, campos, o que é `VALIDAR`
- [ ] `FWLogMsg`/`ConOut` para rastro no console do appserver (diagnóstico de homologação)

### Nunca fazer

- [ ] `SELECT`/`INSERT`/`UPDATE`/`RecLock` direto em tabelas do ERP (`SB1`, `SF2`, `SD2`,
      `SE1`, `SC5`…) — sempre a rotina oficial
- [ ] `lMsErroAuto` como `LOCAL` — a rotina não enxerga; flag sempre `.F.` mesmo falhando
- [ ] `MSHelp()`/`MsgInfo()`/`Alert()` em handler REST — trava o thread sem usuário
- [ ] Chamar `MATA***` direto sem `MSExecAuto`
- [ ] Hardcodar empresa/filial quando `PREPARE ENVIRONMENT`/o broker já resolve o contexto —
      confirmar por ambiente na POC
- [ ] Commit de credenciais, senhas ou `codusr` fixo — o `.PRW` recebe só dados de negócio

---

## 7. Homologação — o ciclo obrigatório antes de produção

```text
1. Fonte pronto (este guia) — campos CONFIRMADOS + hipóteses marcadas
2. Compilar no RPO do TST01 (equipe TOTVS)
3. Confirmar publicação: GET /restall no ambiente de teste lista o serviço
4. POC: chamada mínima real → observar lMsErroAuto/log oficial
5. Iterar aParam/campos até a rotina aceitar o payload
6. Casos: positivo, rejeição oficial (ex.: pedido bloqueado), campo inválido
7. Read-after-write: conferir nas tabelas (SF2/SD2, SE1…) que o efeito foi o da rotina
8. Só então: compilar em produção + superfície api-delpi (gate OFF até autorização)
```

Sinais de sucesso/fracasso vêm **sempre do `lMsErroAuto` + `GetAutoGrLog()`** — o log oficial
é o oráculo. Erro "campo X inválido" = campo errado/ausente; erro de perguntas = `aParam` errado.

---

## 8. Convenções

| Item | Convenção | Exemplo |
|---|---|---|
| Arquivo fonte | `DLP<modulo><seq>.PRW` na pasta de fontes do módulo | `DLP05W01.PRW` (Faturamento) |
| Classe/serviço | `Delpi<dominio>` | `DelpiProduto`, `DelpiFaturamento` |
| Handler | verbo + substantivo | `incProd`, `faturar` |
| Path | `/v1/<recurso>/<acao>` | `/v1/IncProduto/alterar`, `/v1/faturar` |
| Token de log | `cIdtoken` fixo da família | `"gda"` |
| Pasta de fontes | `docs/13-fontes-totvs-protheus/<NN. Módulo>/` | `05. Faturamento/` |

---

## 9. Exemplos no repositório

| Fonte | Rotina oficial | Status |
|---|---|---|
| `docs/13-fontes-totvs-protheus/04. Estoque/DLP04I01.PRW` | `MATA010` (produto) | **Em produção/homologação** — referência do padrão |
| `docs/13-fontes-totvs-protheus/05. Faturamento/DLP05W01.PRW` | `MATA460` (faturamento) | **Rascunho** — aguarda compilação TST01 + POC do `aParam` |

---

## 10. Quando NÃO escrever rota nova

Antes de abrir o editor, checar na ordem:

1. `/restall` (abas ADVPL **e** TLPP — o catálogo tem ~2.100 serviços) — já existe endpoint?
2. Rotina oficial tem ExecAuto documentado? Se não → conversar com TOTVS sobre interface oficial.
3. A operação é consulta? APIs nativas (`/api/fat`, `/wms`, `/api/gfe`…) podem cobrir sem
   código DELPI.

Escrever `.PRW` é a última opção, não a primeira — mas quando necessário, este guia é o molde.
