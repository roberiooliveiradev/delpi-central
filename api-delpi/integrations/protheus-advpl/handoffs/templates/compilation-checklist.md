# Checklist de compilação — entrega ADVPL DELPI

> Preenchido pela equipe ERP/TOTVS. Um arquivo por ambiente/entrega.

## Identificação

- **ID da entrega (package_id):**
- **Versão do pacote:**
- **SHA-256 do ZIP recebido:**
- **SHA do delpi-central (source_commit):**
- **Data de recebimento:**

## Arquivos recebidos

| path | sha256 | module_id | artifact_type |
|------|--------|-----------|---------------|
| …    | …      | …         | …             |

- [ ] Hashes conferem com `manifest.json`
- [ ] Origem das dependências verificada (repo ERP `master`@SHA / mirror)

## Ambiente de compilação

- **Ambiente-alvo:** TST01 / PRD
- **AppServer / RPO selecionado (responsável ERP):**
- **Versão do Protheus (appserver/lib):**
- **Top connect / includes utilizados:**

## Resultado da compilação

- **Resultado:** OK / ERRO / WARNINGS
- **Erros e warnings:**
- **Fontes efetivamente compilados no RPO:**

## Validação pós-publicação

- [ ] Rotas REST publicadas verificadas no catálogo RESTALL
- [ ] Ensaios de leitura executados
- [ ] Ensaios de escrita (se autorizados) com ledger + read-back
- **Resultado de homologação:**

## Responsáveis e rollback

- **Responsável técnico (compilação):**
- **Responsável DELPI (entrega):**
- **Data da operação:**
- **Plano de rollback/reversão:**
