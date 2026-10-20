# API REST Protheus — contrato técnico de fornecedores (GET, POST e PUT)

**Origem:** documento recebido do responsável pela solicitação, *Documentação Técnica - API de Integração Protheus e MinhaDelpi (002)*, seções 1–3.3.  
**Registrado:** 2026-10-19. **Atualizado:** implementação backend do POST (feature-gated).  
**Estado:** contrato externo documentado; POST na `api-delpi` **implementado com escrita real desabilitada por padrão**; PUT **fora de escopo**.  
**Segurança:** transcrição **sanitizada**; nenhuma credencial, token ou URL de host é incluída. O PDF original contém segredo em texto claro e **não deve ser versionado**.

> Esta é a descrição do contrato conforme a fonte recebida, **não** uma homologação da execução REST. Erros e detalhes não fornecidos permanecem `TO_INVENTORY`. Para contratos aprovados e estado do código, conferir HEAD, authorities e handoff vigente.

## 1. Parâmetros e arquitetura

A fonte situa os parâmetros na tabela `PARAMETROS_MINHADELPI` do banco Intranet. Os nomes são `USR_PROTHEUS`, `PSW_PROTHEUS`, `URL_REST`, `PATH_AUTH` e `PATH_SUPPLIERS`. Seus **valores sensíveis não são documentados aqui**.

**Divergência da própria fonte:** a tabela inicial apresenta rótulos `PATH_AUTH`/`PATH_SUPPLIERS` invertidos em relação às funções descritas adiante. A implementação READ existente usa um resolver que somente aceita configurações alinhadas ou inversão inequívoca, sem alterar dados de parametrização automaticamente.

## 2. Autenticação técnica

- `POST {URL_REST}{PATH_AUTH}?grant_type=password&username=...&password=...`.
- Os três parâmetros aparecem na **query string**, conforme o protocolo upstream; **nunca registrar URL completa, credenciais ou tokens** em logs.
- Sucesso: HTTP 200 com `access_token`, `refresh_token`, `scope`, `token_type=Bearer` e `expires_in`. A documentação declara validade de 3600 segundos.
- Falta de `grant_type`, `username` ou `password`: HTTP 400, com `code`, `message` e `detailedMessage`.
- Requisições de fornecedor usam `Authorization: Bearer <token>` (notação de contrato, não um token real).

**Diferença documental x implementação:** a fonte propõe persistir tokens via procedure `pr_InserirTokenProtheus`. A API DELPI existente usa cache em memória do processo e **não usa** essa procedure na entrega READ. Não alterar a estratégia sem decisão arquitetural e evidências.

**Risco conhecido:** a fonte utiliza transporte HTTP e credenciais na query string. A documentação não constitui autorização para teste autenticado; exigir decisão de risco e rotação de credenciais eventualmente expostas.

## 3. Fornecedores — regras gerais

Base do recurso: `{URL_REST}{PATH_SUPPLIERS}`. As operações de gravação são processadas pela rotina Protheus **Execauto MATA020**; nunca gravar diretamente em `SA2`.

Para recursos por ID, a fonte define `:ID = A2_COD (6 dígitos) + A2_LOJA (2 dígitos)`, concatenados sem separador, mantendo zeros à esquerda; exemplo sintético: `00000101`.

### 3.1 GET /:ID (já exposto pela API DELPI)

`GET {URL_REST}{PATH_SUPPLIERS}/:ID`

- HTTP 400, `code_error=001`: ID inválido.
- HTTP 400, `code_error=002`: fornecedor não encontrado, segundo o documento.
- Não inferir que o upstream usa HTTP 404 para ausência: a camada interna pode traduzir os erros.

### 3.2 POST / (inclusão)

**API DELPI:** `POST /integrations/protheus/suppliers` · `operationId=create_protheus_rest_supplier`  
**Permissão:** `api-delpi.integrations.protheus.suppliers.create` (não herdada de read nem de `api-delpi.data`)  
**Feature gate:** `PROTHEUS_SUPPLIER_CREATE_ENABLED=false` (default) — com gate fechado **não** há consulta ao Core, parâmetros, OAuth nem POST upstream.  
**Precedência:** payload estrutural → autenticação/permissão → feature gate → identidade Core → configuração/token → escrita. Gate fechado precede erro de identidade.  
**Identidade:** `codusr` resolvido via Core S2S (`mapped` + `verified` + `protheus_user_id` 6 dígitos) somente com o gate aberto; cliente **não** envia `codusr`.  
**Matriz de campos:** `protheus-rest-supplier-post-field-matrix.md`.

Upstream Protheus:

`POST {URL_REST}{PATH_SUPPLIERS}`

Estrutura JSON **ilustrativa**, com dados fictícios e sem credencial:

```json
{
  "codusr": "000161",
  "fornecedor": {
    "supplier_store": "01",
    "person_type": "J",
    "tax_id": "00000000000000",
    "supplier_name": "FORNECEDOR EXEMPLO",
    "supplier_short_name": "FORNECEDOR EXEMPLO",
    "address": "RUA EXEMPLO",
    "district": "CENTRO",
    "postal_code": "00000000",
    "state": "SC",
    "city": "CIDADE EXEMPLO",
    "city_code": "00000",
    "area_code": "00",
    "phone": "00000000",
    "state_registration": "",
    "municipal_registration": "",
    "contact_name": "",
    "email": "exemplo@example.invalid",
    "payment_condition_code": "010",
    "country_code": "",
    "bacen_country_code": "01058",
    "accounting_account": "00000000",
    "financial_nature_code": "0000",
    "rohs_indicator": "N",
    "payment_method_code": "01"
  }
}
```

**Importante:** `fornecedor` é **objeto** no POST; `codusr` deverá ser calculado no backend a partir da identidade autenticada e do Core, nunca aceito livremente do cliente. O exemplo não prova que cada campo é obrigatório nem que os valores sintéticos sejam aceitos pelo ERP.

| HTTP | `code_error` | Situação descrita na fonte |
|---|---|---|
| 400 | `001` | ID inválido **ou** JSON inválido; discriminar pelo texto `error` |
| 400 | `002` | Campos obrigatórios não preenchidos |
| 400 | `003` | Falha Execauto na inclusão; a mensagem literal pode dizer **“Falha ao alterar fornecedor”** |

A fonte não descreve status/payload de **sucesso** POST, idempotência, regras de retry, obrigatoriedade exaustiva nem geração/retorno do novo `A2_COD`. Esses pontos são `TO_INVENTORY` e não devem ser inventados.

### 3.3 PUT /:ID (alteração)

**API DELPI:** `PUT /integrations/protheus/suppliers/{supplier_id}` · `operationId=update_protheus_rest_supplier`  
**Permissão:** `api-delpi.integrations.protheus.suppliers.update` (não herdada de read, create nem de `api-delpi.data`)  
**Feature gate:** `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` (independente do POST). Gate fechado não consulta Core, parâmetros, OAuth nem executa PUT.  
**Precedência:** id e payload → autenticação/permissão → feature gate → identidade Core → configuração/token → escrita.  
**Request público:** objeto `fornecedor` com campos comprovados (`supplier_name`, `supplier_short_name`). O backend monta o array upstream e resolve `codusr` no Core somente com o gate aberto.  
**Allowlist inicial:** somente os dois campos do exemplo contratual. Demais campos do POST permanecem não editáveis até prova upstream.  
**Resposta 2xx:** `update_acknowledged=true` e `persistence_proven=false` — HTTP de sucesso não comprova persistência.  
**Live write:** não autorizado nesta entrega.

Upstream Protheus:

`PUT {URL_REST}{PATH_SUPPLIERS}/:ID`

Exemplo estrutural sanitizado:

```json
{
  "codusr": "000161",
  "fornecedor": [
    {
      "supplier_name": "FORNECEDOR EXEMPLO ATUALIZADO",
      "supplier_short_name": "EXEMPLO"
    }
  ]
}
```

No PUT, `fornecedor` é **array**, diferentemente do POST.

| HTTP | `code_error` | Situação descrita |
|---|---|---|
| 400 | `001` | ID inválido |
| 400 | `002` | JSON inválido |
| 400 | `003` | Falha na alteração / detalhes Execauto |
| 404 | `004` | Fornecedor não encontrado |

A fonte não define semântica de PATCH versus substituição integral, concorrência ou payload de sucesso PUT.

## 4. Contrato interno da API DELPI — gates de implementação

A documentação externa **não autoriza** replicar `codusr` recebido do frontend. O backend deve resolver a identidade no Core (`SYS_USR.USR_ID`, **semântica exata com `codusr` ainda a validar no upstream**), exigir mapping válido/verificado, autenticação e permissão WRITE específica.

Antes de habilitar POST real, comprovar e testar:
- autenticação, autorização e identidade do autor, incluindo 401/403 e falhas do Core;
- DTO com campos aceitos/limites, `operationId` estável e respostas/erros compatíveis;
- tratamento de duplicidade e idempotência; timeout **sem retry automático de escrita**;
- auditoria, redaction, gestão de secrets e feature gate inicialmente desabilitada;
- validação de comportamento real do ERP somente em teste explicitamente autorizado.

**Não executar POST de produção nem copiar o PDF original ao repositório.** A documentação SA2 e seus 248 campos são inventário de dicionário, não contrato REST de obrigatoriedade.

## 5. Referências versionadas

- `api-delpi/docs/integrations/protheus-rest-read.md`
- `api-delpi/docs/integrations/protheus-rest-supplier-write-handoff.md`
- `api-delpi/docs/api/padroes-totvs/playbooks/playbook-cadastro-fornecedor-sa2.md`
- `docs/11-padroes-de-desenvolvimento/core-protheus-identity-ownership.md`

**Estado documental:** `POST_CONTRACT_SOURCE=DOCUMENTED`; `POST_RUNTIME=IMPLEMENTED_GATED`; `LIVE_WRITE=NOT_AUTHORIZED`; `CONTRACT_GAPS=TO_INVENTORY`.

## 6. Vínculo com o de-para completo SA2 — material entregue ao Gabriel

**Documento complementar canônico de inventário:** [Auditoria do Modelo de Fornecedores — TOTVS Protheus (DELPI)](../api/padroes-totvs/playbooks/playbook-cadastro-fornecedor-sa2.md), em especial a seção **44 — FINAL SUPPLIER FIELD MAPPING** e **44.3 — SUPPLIER_MASTER_FULL_MAPPING**.

**Como usar os documentos conjuntamente:**

| Fonte | Papel | Limite |
|---|---|---|
| **Este documento REST** | Endpoint, autenticação, shape do body `codusr` + `fornecedor`, campos semânticos exemplificados, erros e limites conhecidos | Não comprova quais campos são obrigatórios nem o payload exaustivo aceito pelo Protheus |
| **Playbook/de-para SA2** | Correspondência entre campos de negócio e `A2_*`, tipos, comprimentos, validações SX3, F3/lookup, empresa e classificação de cadastro | Inventário de dicionário e dados; **não** substitui o contrato REST nem prova o comportamento do Execauto/MATA020 |
| **Core identity ownership** | Associação autoritativa do usuário Minha DELPI com identidade Protheus | Não define por si só a semântica `codusr` do endpoint upstream |

O de-para foi identificado como o material técnico de campos já compartilhado com Gabriel **segundo o contexto informado pelo solicitante**; o histórico de envio/aceite de Gabriel não foi verificado no GitHub. **Não presumir aceite do contrato pelo owner Protheus.**

**Regra de rastreabilidade:** ao implementar o POST, cruzar cada propriedade externa de `fornecedor` com a coluna `business_field` e o respectivo `totvs_field` da seção 44.3, documentando diferenças de nomes (`tax_id` versus `tax_document`, por exemplo), obrigatoriedade, default e tratamento por empresa. Não inferir equivalência quando a nomenclatura divergir: classificar `TO_INVENTORY` e validar junto ao owner. Não enviar campos `DO_NOT_SEND` nem os marcados como `SYSTEM_GENERATED` sem contrato específico.

**Próximo gate:** produzir uma matriz de rastreabilidade **campo REST → business_field do de-para → campo SA2 → regra/validação → evidência → decisão** antes de aceitar a implementação de escrita em produção. Preservar cada documento em sua autoridade e vincular alterações relevantes nos dois.
