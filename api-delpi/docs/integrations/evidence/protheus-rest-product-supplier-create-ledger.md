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
