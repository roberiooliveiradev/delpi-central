---
name: totvs-protheus-integration
description: Especialista em integração de escrita TOTVS/Protheus — protocolo para criar ou revisar rotas REST ADVPL (WSRESTFUL/MSExecAuto) e superfícies api-delpi que escrevem no ERP. Invoque para qualquer tarefa envolvendo MATA*/FINA*/ExecAuto, .PRW, /restall, integrações/protheus ou escrita no ERP.
---

# Especialista — Integração TOTVS/Protheus (escrita)

Aplique o protocolo canônico completo definido em:

- **Regra operacional**: `.cursor/rules/totvs-protheus-write-integration.mdc`
  (auto-carrega por globs; esta skill é o ponto de invocação explícita)
- **Guia ADVPL**: `api-delpi/docs/integrations/protheus-advpl-route-development-guide.md`
- **Playbook de superfície**: `api-delpi/docs/integrations/protheus-write-integration-playbook.md`
- **Evidência live**: `api-delpi/docs/integrations/evidence/protheus-rest-product-update-ledger.md`
- **Negócio TOTVS/DELPI**: `api-delpi/docs/api/padroes-totvs/` + `docs/13-fontes-totvs-protheus/`

## Resumo operacional

1. Rotina oficial primeiro (fontes DELPI → TDN → `/restall` ADVPL+TLPP → POC TST01).
2. Escrita no Protheus = `WSRESTFUL` + `MSExecAuto`. **Nunca** SQL direto em tabela `S*`.
3. Superfície api-delpi: gate OFF por default, pin de ambiente, `codusr` via Core,
   tracker antes da escrita, zero retry em timeout.
4. Contrato ExecAuto: campo confirmado (fonte/TDN) ou marcado `VALIDAR NO TST01`.
5. Escrita live: snapshot → TST01 → verify → PROD intacta → restore → ledger versionado.
6. Em revisão: rodar o checklist da regra sobre o diff; violação = «⚠ Desvio de integração TOTVS».

Saída esperada: `OPERAÇÃO | ROTINA OFICIAL | CONTRATO | GATE+PIN | IDENTIDADE | RASTREIO | EVIDÊNCIA`.
