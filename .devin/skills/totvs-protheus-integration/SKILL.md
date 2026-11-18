---
name: totvs-protheus-integration
description: Especialista TOTVS/Protheus para análise e integração ADVPL/TLPP, fonte versionada no Delpi-ti/protheus-erp, RESTALL, RPO, MATA010, MATA061, SB1/SA5 e api-delpi. Invoque para inventário de rotinas, CRUD, contratos, revisão, desenvolvimento e handoff de compilação ERP.
---

# Especialista — Integração TOTVS/Protheus (escrita)

Aplique o protocolo canônico completo definido em:

- **Regra operacional**: `.cursor/rules/totvs-protheus-write-integration.mdc`
  (auto-carrega por globs; esta skill é o ponto de invocação explícita)
- **Guia ADVPL**: `api-delpi/docs/integrations/protheus-advpl-route-development-guide.md`
- **Playbook de superfície**: `api-delpi/docs/integrations/protheus-write-integration-playbook.md`
- **Evidência live**: `api-delpi/docs/integrations/evidence/protheus-rest-product-update-ledger.md`
- **Negócio TOTVS/DELPI**: `api-delpi/docs/api/padroes-totvs/`; **fontes primários**: `Delpi-ti/protheus-erp` (`master`@SHA); **espelho**: `docs/13-fontes-totvs-protheus/`

## Resumo operacional

1. Rotina oficial primeiro (`Delpi-ti/protheus-erp` master@SHA → espelho DELPI → TDN/SX3 → RESTALL vigente → POC TST01).
2. Escrita = REST governado + **rotina oficial compatível**: `MSExecAuto` para MATA010 quando suportado; MVC oficial para MATA061/SA5 após contrato e homologação. **Nunca** SQL/RecLock direto em `S*`.
3. Superfície api-delpi: gate OFF por default, pin de ambiente, `codusr` via Core,
   tracker antes da escrita, zero retry em timeout.
4. Contrato ExecAuto: campo confirmado (fonte/TDN) ou marcado `VALIDAR NO TST01`.
5. Escrita live: snapshot → TST01 → verify → PROD intacta → restore → ledger versionado.
6. Em revisão: rodar o checklist da regra sobre o diff; violação = «⚠ Desvio de integração TOTVS».

Saída esperada: `OPERAÇÃO | ROTINA OFICIAL | CONTRATO | GATE+PIN | IDENTIDADE | RASTREIO | EVIDÊNCIA`.

## Atualização de autoridade de fontes (2026-11)

- **Fonte versionada primária ADVPL/TLPP:** repositório privado `Delpi-ti/protheus-erp`, branch `master`, consultado no HEAD vigente via GitHub autorizado. Registrar `SOURCE_REPO/BRANCH/SHA/PATH/BLOB_SHA` em cada análise.
- `docs/13-fontes-totvs-protheus/` do `delpi-central` é espelho/cópia de referência; comparar SHA do blob com o repositório ERP, não tratá-lo como versão automaticamente atual.
- Código no GitHub prova **fonte versionado**, não prova compilação, publicação no RPO ou execução em PRD/TST01. Para runtime exigir inspeção autorizada do RPO/versão e/ou evidência da equipe ERP. RESTALL demonstra superfície publicada, não equivalência binária nem sucesso da escrita.
- Em SB1, `DLP04I01.PRW` usa MATA010/`MSExecAuto` para CREATE/UPDATE com 22 campos na fonte inspecionada. Em SA5, `Dmata061.prx` define modelo MVC Model-2 e chave `FILIAL+FORNECE+LOJA+PRODUTO+FABR+FALOJA+REFGRD`; **não** assumir que `MSExecAuto` com arrays de MATA010 se aplica a MATA061.
- `MATA010M_DLP.PRW` contém submodelo `Model061` (grid SA5) condicionado a `MV_CADPROD` e permissões. Investigar essa alternativa de reuso antes de criar integração separada, sem inferir runtime.
- Não há prova de rota REST de escrita SA5 publicada no último inventário; MATI060/EAI não estava configurado. Revalidar se houve mudança. Operações CRUD requerem contracts oficiais, autorização do owner e read-back pela chave completa.
- Só escrever por rotina oficial validada: ExecAuto quando suportado; modelo MVC se aprovado e homologado. Jamais `RecLock` ou SQL de escrita direta. Separar `PROVEN_SOURCE`, `PROVEN_RUNTIME`, `TO_INVENTORY` e `TEST_NOT_RUN`.
