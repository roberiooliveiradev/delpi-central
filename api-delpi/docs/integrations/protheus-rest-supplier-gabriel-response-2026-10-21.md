# Retorno Gabriel — endpoint produtivo, POST e campos cadastrais (2026-10-21)

**Origem:** e-mail `Re: API Fornecedor X MinhaDelpi` de Gabriel Araújo, fornecido pelo PO com planilha `Campos Obrigatorios.xlsx` e screenshot TOTVS. **Natureza:** declaração do owner + mapeamento documental; não comprova deploy do REST produtivo nem persistência de todos os campos. Nenhum segredo incluído.

## Fatos comunicados pelo owner

| Tema | Resposta | Classificação |
|---|---|---|
| Serviço REST para banco produtivo DELPI | `http://192.168.1.231:8061/restall` | **OWNER_REPORTED**, endpoint ainda **NOT_TESTED** |
| POST retornar código + loja | Gabriel declarou **"Implementado"** | **OWNER_REPORTED**; verificar `supplier_code` e `supplier_store` efetivos no JSON |
| Campos obrigatórios para inclusão | Relação em `Campos Obrigatorios.xlsx` | **OWNER_REPORTED**; documento lista 18 pares campo Minha DELPI ↔ TOTVS; confirmar semântica de obrigatoriedade por contexto no contrato/método |
| Restrições PUT | Código e Loja não editáveis; Gabriel recomenda também bloquear CNPJ/CPF | **OWNER_REPORTED**; contrato Minha DELPI já protege documentos fiscais, código e loja; proteção upstream complementar pendente de alinhamento |

## Relação da planilha anexada — transcrição fiel

| minha_delpi_field | totvs_field |
|---|---|
| `supplier_store` | `A2_LOJA` |
| `supplier_name` | `A2_NOME` |
| `supplier_short_name` | `A2_NREDUZ` |
| `tax_id` | `A2_CGC` |
| `address` | `A2_END` |
| `district` | `A2_BAIRRO` |
| `postal_code` | `A2_CEP` |
| `city` | `A2_MUN` |
| `city_code` | `A2_COD_MUN` |
| `state` | `A2_EST` |
| `bacen_country_code` | `A2_CODPAIS` |
| `financial_nature_code` | `A2_NATUREZ` |
| `contact_name` | `A2_CONTATO` |
| `area_code` | `A2_DDD` |
| `phone` | `A2_TEL` |
| `email` | `A2_EMAIL` |
| `payment_condition_code` | `A2_COND` |
| `accounting_account` | `A2_CONTA` |

**Interpretação cautelosa:** a planilha tem título de campos obrigatórios, mas as duas colunas somente documentam **mapeamento**, não validações condicionais por empresa/filial, nem formato/tipo ou nulabilidade; não mudar o required-field registry sem inspeção e homologação. `supplier_store` figura na lista apesar de gerar dúvidas sobre identidade gerada — confirmar comportamento POST concreto.

## Confronto com F4.3 e investigação tax_id

- Na homologação F4, o POST de fornecedor `003874/01` retornou sucesso e código, mas `DELPI_TST01.SA2010.A2_CGC` permaneceu vazio. O tracking registrou `RECONCILIATION_REQUIRED` com `mismatched_fields=['tax_id']`.
- O documento do owner relaciona explicitamente `tax_id` a `A2_CGC`: **isso não comprova que Execauto esteja persistindo o campo**. Inspecionar shape exato recebido na API Gabriel e contrato MATA020 antes de alegar correção.
- O defeito independente UPDATE `IntegrationTrackingService.confirm()` sem `evidence` segue sujeito a correção e nova prova.

## Decisão operacional PO — MANTER HOMOLOGAÇÃO

**Não trocar endpoint neste momento.**
- `REST_TEST = http://192.168.1.233:8701/rest` → `DELPI_TST01` (já comprovado).
- `SQL_HOMOLOGATION = 192.168.1.230 / DELPI_TST01 / SA2010` read-only.
- `REST_PROD_CANDIDATE = http://192.168.1.231:8061/restall` — informado por Gabriel, **sem configurar, chamar ou executar writes** nesta decisão.
- `DELPI` produtivo e `PARAMETROS_MINHADELPI` devem permanecer inalterados.
- Gates `PROTHEUS_SUPPLIER_CREATE_ENABLED` e `PROTHEUS_SUPPLIER_UPDATE_ENABLED` permanecem OFF fora de teste isolado autorizado.

## Próximos passos

1. Fechar bug `confirm(evidence=...)` e re-homologar PUT na `DELPI_TST01` com GET+SQL.
2. Confrontar o payload POST `tax_id` com a matriz `A2_CGC`, obter do Gabriel confirmação do mapping real e corrigir somente no owner certo.
3. Validar o shape de retorno de código e loja, campos realmente obrigatórios e semântica de campos PUT via REST de testes.
4. Documentar contrato atualizado após evidência concreta. Qualquer migração para REST PROD exige GO separado, aprovação TOTVS, smoke read-only e plano de rollback.

**Esta atualização é exclusivamente documental.**
