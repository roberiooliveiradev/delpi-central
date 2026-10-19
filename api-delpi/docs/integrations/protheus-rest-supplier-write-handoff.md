# Handoff — evolução da integração REST de fornecedores Protheus (POST/PUT)

**Registro:** 2026-10-19  
**Estado:** inventário e planejamento de contrato de escrita; **POST/PUT não implementados nesta frente**.  
**Base consultada:** `origin/main` em `8e7eb9640f6b5aa13b10b8f6978ac2e81b10afbc`. Reancorar no HEAD a cada retomada.

> Documento de continuidade, não substitui authorities, especificação aprovada do ERP ou contratos de API. Não converter suposições em contrato sem prova. Nenhum deploy ou escrita no Protheus é autorizado por este documento.

## Objetivo da próxima entrega

Permitir **criação (POST)** e **atualização (PUT)** de fornecedores por integração REST do Protheus, com `api-delpi` como owner da integração e domínio ERP como owner das regras finais, reutilizando a associação de identidade Protheus **governada pelo Core API**. Primeiro fechar contrato backend e segurança; UI apenas após aceite do contrato.

## Estado constatado no repositório

| Tema | Estado | Evidência |
|---|---|---|
| Autenticação Protheus (OAuth password grant), token e gateway HTTP | PROVEN: implementado para leitura | `api-delpi/app/infrastructure/gateways/protheus_rest_gateway.py` |
| Diagnóstico e consulta REST de fornecedor | PROVEN: `GET /integrations/protheus/status` e `GET /integrations/protheus/suppliers/{supplier_id}` | `api-delpi/app/interface/http/routes/integrations/protheus_router.py` |
| Composer e configuração técnicos existentes | PROVEN | `api-delpi/app/composition/protheus_rest_composer.py`, `api-delpi/docs/integrations/protheus-rest-read.md` |
| POST/PUT de fornecedores | TO_INVENTORY quanto a outras superfícies; **não encontrados no router REST consultado** | Mesmo router; pesquisa residual obrigatória antes de criar endpoints |
| Identidade externa do usuário | PROVEN: associação no Core; cutover/sincronização operacionais reportados como PASS | `docs/11-padroes-de-desenvolvimento/core-protheus-identity-ownership.md` e ledger vigente |
| Self identity | PROVEN: `GET /me/external-identities/protheus` | `core-api/app/interfaces/http/me_controller.py` |
| Consultas S2S de identidade | PROVEN: Core expõe by-user e outras rotas internas com token | `core-api/app/interfaces/http/integrations_protheus_identities_controller.py` |
| De-para SA2/SX3 | PROVEN: auditoria extensa; **não é contrato REST** | `api-delpi/docs/api/padroes-totvs/playbooks/playbook-cadastro-fornecedor-sa2.md`, seção 44 |
| Permissões REST Protheus | PROVEN: `api-delpi.integrations.protheus.read` e bypass `api-delpi.access.full` no READ atual; **WRITE ainda não definido** | `api-delpi/app/application/security/api_delpi_permissions.py` |
| Contrato POST/PUT upstream, `codusr`, erros, geração de código, idempotência | TO_INVENTORY / decisão requerida | Não comprovados no código consultado; obter contrato do owner TOTVS |

## Limites e decisões de ownership

- **Core API:** fonte autoritativa UUID Minha DELPI ↔ `SYS_USR.USR_ID`/`USR_CODIGO`. Não consultar banco de Solicitações de Compras nem replicar mapping.
- **API DELPI:** autenticação técnica e adapter REST do Protheus; autenticação/autorização da solicitação; resolução segura do usuário autenticado via contrato Core; auditoria.
- **ERP Protheus:** validação final, geração de código e regras `MATA020`/endpoint de escrita.
- **Portal/produto consumidor:** coleta dos dados e UX, sem definir `codusr`, autoridade ou permissões pelo frontend.

**Reuse gate preliminar:** `EXISTING_EQUIVALENT=YES` para gateway/identity/lookup existentes; `REUSE_DECISION=EXTEND` no boundary da API DELPI. Novas rotas devem ser justificadas após busca residual.

## Fatos relevantes do cadastro

- Chave de negócio: `A2_COD` + `A2_LOJA` no contexto apropriado de empresa/filial; CNPJ/CPF **não é chave única**.
- Valores com zeros à esquerda são strings.
- A geração `GETSXENUM("SA2")` foi observada nas empresas 01/05, com diferenças em 03/04; não presumir comportamento universal.
- A auditoria de 248 campos de SA2, classificações `PROVEN_REQUIRED`/`CANDIDATE_REQUIRED` etc., deriva do dicionário SX3 e não prova o payload aceito pelo REST.
- `MATA020` (ADVPL) e efeitos colaterais internos não foram verificados pelo código consultado.

## Questões que devem ser fechadas antes do código de escrita

1. **Contrato REST upstream:** URL/método real de POST/PUT, request/response por operação, shape de `fornecedor` (objeto versus lista), campos aceitos/obrigatórios, erro e status HTTP.
2. **`codusr`:** confirmar com owner TOTVS se é exatamente `SYS_USR.USR_ID`, seu formato e se a API o valida.
3. **Identidade/autorização:** validar no backend o usuário atuante e `mapping_status=mapped`, `verified=true`; escolher mecanismo autenticado Core→API DELPI que não permita impersonação; estabelecer permissão WRITE específica, sem usar `api-delpi.access.full` por atalho.
4. **Semântica de escrita:** idempotência para POST, colisões, PUT parcial/total, concorrência, limites e timeouts; retries automáticos de GET **não** devem ser copiados cegamente para escrita.
5. **Empresa e numeração:** contexto fiscal/empresa, códigos, loja e comportamento do Protheus quando cadastro já existe.
6. **Auditoria/segurança:** ator, correlation ID, dados sensíveis, redaction, secrets; exigir aprovação para testes vivos. A integração OAuth atual usa query string e endpoint HTTP claro conforme documentação — risco residual, não garantia de transporte seguro.
7. **Operação:** feature gate inicialmente fechado, homologação em ambiente controlado e rollback/compensação; não testar POST/PUT contra produção incidentalmente.

## Próximo fluxo de trabalho

1. Reancorar GitHub HEAD e authorities; inventariar implementações, consumidores, testes e contracts.
2. Recuperar a documentação técnica de POST/PUT do owner Protheus (citada em investigação anterior, **não versionada nesta evidência consultada**) e verificar a semântica de `codusr`; em conflito registrar `ARCHITECTURE_DECISION_REQUIRED`.
3. Redigir contrato API DELPI OpenAPI com `operationId` estável, DTOs, AuthN/AuthZ, erros, idempotência, auditing e critérios RQ/AC conforme convenção vigente.
4. Implementar o menor diff backend-first **sem live writes**, com mocks e testes de segurança/regressão.
5. Homologação controlada mediante autorização do owner; só então considerar UI de fornecedor.

## Disciplina de continuidade no GitHub

- **GitHub é fonte persistente; chat não é authority.** Reancorar no HEAD e ler authorities antes de cada novo trabalho.
- A cada mudança material de estado (investigação, contrato aprovado, implementação, testes, deploy, aceite), atualizar este handoff **e** as authorities/ledger aplicáveis no mesmo conjunto rastreável de commits/PR, com SHAs, evidências, estados PROVEN/TO_INVENTORY/PLANNED e PASS/FAIL/PENDING. Não alegar atualização sem commit confirmado.
- Preservar `docs/integrations/protheus-rest-read.md` como contrato de leitura existente; não declarar POST/PUT implementados antecipadamente.
- Não salvar senhas, tokens, PII nem payloads reais desnecessários.
