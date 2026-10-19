# API REST Protheus — contrato técnico de fornecedores (GET, POST e PUT)

**Origem:** documento recebido do responsável pela solicitação, *Documentação Técnica - API de Integração Protheus e MinhaDelpi (002)*, seções 1–3.3.  
**Registrado:** 2026-10-19. **Estado:** contrato externo documentado; POST/PUT na `api-delpi` **não implementados** nesta atualização.  
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

### 3.2 POST / (inclusão, ainda não implementada na API DELPI)

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

### 3.3 PUT /:ID (alteração, fora do escopo do primeiro POST)

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

**Estado documental:** `POST_CONTRACT_SOURCE=DOCUMENTED`; `POST_RUNTIME=NOT_IMPLEMENTED`; `LIVE_WRITE=NOT_AUTHORIZED`; `CONTRACT_GAPS=TO_INVENTORY`.
