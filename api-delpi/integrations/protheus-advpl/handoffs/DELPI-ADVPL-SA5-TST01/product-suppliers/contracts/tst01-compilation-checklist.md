# Checklist de compilação e validação TST01 — DLP04I02.PRW (SA5)

Pacote: `DELPI-ADVPL-SA5-TST01-v0.4.0` — classificação
`COMPILATION_REVIEW_CANDIDATE`. Este documento não atesta compilação nem
homologação; define o que a equipe ERP deve executar e registrar.

- Fonte: `src/DLP04I02.PRW` (classe REST `DelpiProdForn`)
- Modelo oficial: `DMATA061` (rotina MATA061, MVC Model-2)
- Proveniência: `Delpi-ti/protheus-erp@master` —
  `73. CRM/Dmata061.prx` (blob `b45cc9333c410a58d5836f78b79a140c6056c9c6`),
  `73. CRM/MATA010M_DLP.PRW` (blob `a56c2a5079991742a544c39dd75fde8f3e9eda48`)
- Escopo executável: somente POST `/v1/ProdForn/incluir`. PUT, GET e
  DELETE retornam 501 por contrato.

## Etapa A — Pré-compilação

- [ ] Confirmar ambiente **TST01** (nunca PRD).
- [ ] Confirmar que o modelo `DMATA061` está presente/compilado no RPO
      de destino e que a rotina MATA061 funciona na interface oficial.
- [ ] Conferir includes: `TOTVS.CH`, `RESTFUL.CH`, `PROTHEUS.CH`,
      `FWMVCDEF.ch` e biblioteca MVC/REST disponíveis na build.
- [ ] Conferir colisão de nomes: fonte `DLP04I02`, classe `DelpiProdForn`,
      paths `/v1/ProdForn/*` — pesquisar no RPO e em fontes locais.
- [ ] Confirmar owners autorizados (Equipe ERP + Integrações TOTVS +
      Coordination).
- [ ] Conferir que o pacote contém apenas os arquivos previstos (ver
      `manifest.json` do pacote; nada de `.env`, credenciais ou módulos
      alheios).
- [ ] Conferir pontos de entrada ativos em MATA061 que possam afetar o
      ciclo do modelo (PEs não visíveis no fonte versionado).

## Etapa B — Compilação controlada (exclusivo equipe ERP)

Executada somente após autorização própria da equipe ERP. Registrar:

| Campo | Valor a registrar |
|---|---|
| Build Protheus | |
| AppServer | |
| RPO de destino | |
| Fonte + SHA-256 | |
| Data e executor | |
| Resultado da compilação | |
| Warnings / errors | |
| Dependências ausentes | |
| Classe REST visível após compilação (`/v1/ProdForn/*`) | |

## Etapa C — Validação MVC em TST01 (após aprovação para testes mutáveis)

Formato por caso: `CASE_ID | PRECONDITION | INPUT | EXPECTED | ACTUAL |
RESULT | EVIDENCE`

| # | Caso | Esperado |
|---|---|---|
| C-01 | CREATE produto sem grade (`A5_REFGRD=""`) | vínculo criado; HTTP 200 |
| C-02 | CREATE produto com grade (`A5_REFGRD` preenchido) | vínculo criado |
| C-03 | CREATE vínculo duplicado (7 campos iguais) | rejeição oficial via a060LinOk/ExistChav |
| C-04 | CREATE fornecedor/loja inexistente | rejeição oficial |
| C-05 | CREATE payload incompleto/JSON inválido | HTTP 400, sem mutação |
| C-06 | `M->A5_PRODUTO`/`M->A5_REFGRD` em `a060LinOk` sem view | verificar se memvars existem; dup-check correto? |
| C-07 | `Help()` em `a060VldGrv`/`a060LinOk` sem tela | sem travamento/erro fatal? |
| C-08 | Retorno de `CommitData()` na build instalada | tipo e semântica do retorno |
| C-09 | Erro de validação oficial | resposta 400 estável; detalhe só no log |
| C-10 | Erro de persistência (simulado) | sem HTTP 200 |
| C-11 | Resposta ambígua de commit | erro; **nenhum retry automático** |
| C-12 | Read-back independente pela PK integral SA5 | confirma `PERSISTENCE_CONFIRMED` |
| C-13 | Comparativo antes/depois em TST01 | apenas SA5 alterado, nada mais |
| C-14 | PROD intacta | nenhuma alteração produtiva |
| C-15 | PUT/GET/DELETE | HTTP 501, sem mutação |

Restrições: não usar registros produtivos; testes mutáveis só com
autorização; se `M->`/`a060LinOk` falhar sem view, resultado = `FAIL` e a
implementação retorna à revisão de arquitetura (não criar memvars
artificiais nem contornar `ExistChav`).

## Etapa D — Decisão (estados separados)

Compilação bem-sucedida **não** implica homologação. Cada estado exige
evidência e aprovação distintas:

```text
TST01_COMPILED → TST01_RUNTIME_VALIDATED → TST01_WRITE_VALIDATED
             → PRD_APPROVED → PRD_PUBLISHED
```

## Rollback / reversão (responsabilidade ERP)

- Artefato anterior: RPO anterior ao deploy do `DLP04I02` (a equipe ERP
  mantém backup do RPO antes da compilação).
- Reversão: restaurar RPO anterior ou remover o fonte compilado +
  republicar; despublicar os paths `/v1/ProdForn/*` se expostos.
- Evidência pós-reversão: classe `DelpiProdForn` indisponível;
  read-back SA5 mostra estado anterior; PROD confirmada intacta.
- Nenhum script automático de publicação/reversão faz parte deste pacote.

## Bloqueios de runtime conhecidos (VALIDAR NO TST01)

1. Semântica do retorno de `CommitData()` na build instalada.
2. Comportamento de `M->A5_PRODUTO`/`M->A5_REFGRD` em `a060LinOk` sem view.
3. `Help()` do callback oficial em contexto REST headless.
4. API exata de `GetErrorMessage()` no MPFormModel.
5. Regra efetiva do SX3/modelo para `A5_REFGRD` vazio.
6. Mecanismo oficial de carga do vínculo pela PK integral (UPDATE —
   hoje bloqueado/501).
7. Semântica de exclusão SA5 (DELETE — bloqueado; `a060VldGrv` rejeita
   todas-linhas-excluídas e grid vazio).
