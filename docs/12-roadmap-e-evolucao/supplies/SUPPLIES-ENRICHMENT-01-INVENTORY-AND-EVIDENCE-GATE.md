# SUPPLIES-ENRICHMENT-01 — Inventário P0 e contrato de evidência CNPJ

> Data 2026-10-21. Estado: INVENTORY / PARTIAL / DOCUMENTED. Sem implementação, provider call, migration, job, deploy ou PUT. Main HEAD consultado: 811d4c7179927ef10a54c90e5daa8721f7aaa47f. Documentação de enriquecimento no PR #106, ainda não comprovada integrada ao main.

## 1. Estado e ownership
- api-delpi: contrato real de proveniência v1 lido no main em api-delpi/docs/integrations/supplier-write-provenance-contract.md. POST/PUT aceitam change_context opcional; campos com UNKNOWN_LEGACY para consumer sem contexto. GOVERNMENT_API, THIRD_PARTY_API e modos de sugestão externa são fail-closed / rejeitados em v1, até contrato de evidência verificável.
- supplies-api (Flask): owner da orquestração de consultas de CNPJ, AuthZ Core, revisão, divergências, aceite/recusa e estado próprio. plugins/supplies: interface BFF-only; api-delpi: leitura SA2/PUT/tracking e provenance cross-consumer.
- Código integral da supplies-api ainda requer inventário de rotas, ORM, testes, contrato de fornecedor, Core scopes e S2S em HEAD por Cursor. GitHub code search retornou miss, que NÃO prova ausência. Contratos de enriquecimento do PR #106 são TARGET, não rotas existentes.

## 2. Inventário de fontes e acesso
| Fonte | Evidência externa | Elegibilidade | Estado |
|---|---|---|---|
| Serpro Consulta CNPJ para PJ | Serviço oficial informa contratação PJ, e-CNPJ, Consumer Key/Secret, modalidades Básica/QSA/Empresa, preço por tipo/volume | Candidato prioritário; contratação e direitos ainda não comprovados na DELPI | CONTRACT/KEYS/JSON = TO_INVENTORY |
| Conecta gov.br CNPJ 2.0.2 | Swagger OAuth2 oficial e esquema de referência | Adesão indicada para órgãos públicos; NÃO é API automaticamente liberada a PJ | NOT APPROVED FOR DELPI |
| REDESIM e consulta humana | Consulta cadastral pública | Não assumir direito de scraping nem endpoint transacional | NOT APPROVED AS API |
| Dados abertos RFB | Download dataset | Outra arquitetura e governança, não lookup realtime comprovado | FUTURE/TO_INVENTORY |

Fontes oficiais consultadas:
- https://www.gov.br/pt-br/servicos/obter-solucao-de-consulta-de-dados-do-cadastro-nacional-de-pessoas-juridicas-cnpj
- https://www.gov.br/conecta/catalogo/apis/consulta-cnpj
- https://www.gov.br/conecta/catalogo/apis/consulta-cnpj/swagger_api_cnpj.md/swagger_view

CONTRACT_SIGNED=TO_INVENTORY; PLAN_SELECTED=TO_INVENTORY; AUTHORIZED_PAYLOAD=TO_INVENTORY; DELPI_CREDENTIALS=NOT_VERIFIED; PROVIDER_LIVE_TEST=TEST_NOT_RUN; SECURITY_LEGAL_GATE=PENDING. Não usar Swagger Conecta como se fosse o contrato comercial Serpro.

## 3. Mapping candidato externo → SA2
| Externo | api-delpi/SA2 | Elegibilidade |
|---|---|---|
| CNPJ estabelecimento | tax_id/A2_CGC | identidade, protegido, never apply |
| Razão social | supplier_name/A2_NOME C(50) | comparar; PUT/tamanho/homologação pendentes |
| Nome fantasia | supplier_short_name/A2_NREDUZ C(20) | não presumir fantasia igual abreviação interna |
| Logradouro + número/complemento | address/A2_END C(40) | exigir transformação sem truncar; manual review |
| Bairro | district/A2_BAIRRO C(20) | comparável condicional |
| CEP | postal_code/A2_CEP C(8) | normalizar 8 dígitos |
| Cidade/UF/IBGE | city/A2_MUN, state/A2_EST, city_code/A2_COD_MUN | trio dependente, conciliação CC2; IBGE não é código Protheus |
| Telefone/email | area_code,phone,email | fonte pública pode divergir de contatos operacionais; manual |
| Situação/CNAE/QSA | sem PUT comprovado | somente informativo; CPF/QSA fora do MVP |
| Financeiro/pagamento/contábil | internos | não sugerir update externo |

Source da matriz: api-delpi/docs/integrations/protheus-rest-supplier-post-field-matrix.md (contrato/documentação no GitHub, não homologação PUT em runtime). Nenhum campo liberado automaticamente para PUT por este inventário. Dados externos nulos NÃO apagam dado ERP.

## 4. Contrato de evidência end-to-end (PROPOSED / não implementado)
1. supplies-api autenticada lê SA2 via api-delpi e valida code/store, CNPJ exato, unidade e resource scope via Core fail-closed.
2. Consulta apenas CNPJ do próprio fornecedor em provider oficial contratado; registra evidence_id opaco, provider_id/versão, timestamp, fonte e digests server-side vinculados ao CNPJ, recurso, actor, correlation_id. Sem payload externo integral por padrão.
3. Gera review_id e baseline version/fingerprint, mapeia campos tipados, elegibilidade/proveniência por campo; PREPARE/DRAFT não é PUT.
4. ACCEPT/REJECT individual e bulk pending-only com idempotency/revision, snapshot explícito e eventos de decisão próprios em supplies-api.
5. Antes de declarar GOVERNMENT_API em change_context v2, api-delpi verifica assinatura ou referência de evidência por S2S ao owner, vínculo review_id/decision_id/source/field/supplier/actor/TTL e antifraude/replay; declarações simples de MFE/BFF não bastam.
6. PUT permanece com gate desligado até autorização específica; tracking de api-delpi registra CONFIRMED apenas com prova. ACK/UNKNOWN não alteram latest_confirmed origin.

## 5. Rotas TARGET (não implementadas)
| Método | Candidata supplies-api | Finalidade |
|---|---|---|
| POST | /suppliers/{code}/{store}/enrichment-reviews | consulta CNPJ e comparação sob demanda |
| GET | /suppliers/{code}/{store}/enrichment-reviews/{review_id} | comparação/provenance autorizada |
| GET | /suppliers/{code}/{store}/enrichment-reviews | histórico paginado |
| POST | /suppliers/{code}/{store}/enrichment-reviews/{review_id}/decisions | aceitar/recusar 1 campo |
| POST | /suppliers/{code}/{store}/enrichment-reviews/{review_id}/bulk-decisions | aceitar/recusar elegíveis pendentes em transação |
| POST | /suppliers/{code}/{store}/enrichment-reviews/{review_id}/prepare-update | diff draft sem write |
| PUT | rota já existente de fornecedor | apenas futuro GO, Core AuthZ, evidence verificada, api-delpi |

## 6. Gates
| Gate | Estado | Evidência faltante |
|---|---|---|
| G0 code inventory supplies-api | PARTIAL | HEAD/status, routes, services, ORM/migrations, Core policy, S2S, producers/consumers, testes, runtime |
| G1 provider | PENDING | contratação/credenciais/termos Serpro, manual real, payload sandbox, auth/rate/quotas |
| G2 mapping/PUT | TO_INVENTORY | campos de resposta realmente contratada, SX3/allowlist PUT, CC2, estado de filial |
| G3 LGPD/retention | PENDING | DPO: base legal, dado pessoal, prazos por snapshot/decisão/auditoria, criptografia, exclusão, acessos |
| G4 evidence trust | PENDING | contrato api-delpi cross-consumer, assinatura ou verificação S2S, anti-replay e audit |
| G5 implementation GO | NOT_AUTHORIZED | contract freeze conjunto e etapa explicitamente liberada |
| G6 runtime E2E | TEST_NOT_RUN | smoke autenticado e provider homologado |

## 7. Riscos e próxima etapa
- Sem fonte licenciada, não fazer call external nem scraping; sem política de retenção aprovada, não criar tabela de snapshot externo.
- Busca CNPJ pode incluir dados pessoais mesmo em PJ; QSA, representantes/CPF fora do MVP. Retenção de actor_subject e source_reference também requer revisão.
- Uma atualização manual possui origem MANUAL_USER_INPUT e modo MANUAL_DIRECT; consulta gov com aceite exige evidence de consulta e decisão. Aceitar sugestão sem PUT não é persistência ERP.
- Não criar permissão por botão/campo. Não habilitar automação nem gate Protheus.
- Próxima execução correta: Cursor P0.1 somente inventário real supplies-api no HEAD; Compras/Security para contrato Serpro; DPO para retenção; arquitetura para evidência v2 antes de qualquer implementação.

**FINAL: INVENTORY PARTIAL/DOCUMENTED; IMPLEMENTATION NOT AUTHORIZED; NO CODE/DB/DEPLOY.**

## 9. Correção de inventário — LGPD institucional existente (2026-10-21)

**EXECUTION_DRIFT documental identificado e corrigido:** o inventário P0 inicial tratou LGPD como se faltasse uma política institucional. No `main`, `docs/README.md` indica a pasta canônica `docs/13-auditoria-lgpd/`, e há documentação já vigente:

- `docs/13-auditoria-lgpd/ropa-registro-tratamento.md` (26/05/2026): controlador DELPI, encarregado, bases legais e retenção por categoria. Logs de auditoria de Core/Transformômetro/Indicadores: **2 anos**, com anonimização de IP/payload; uso de aplicações **1 ano** com consentimento `usage_tracking`; consentimentos **5 anos após revogação**; notificações **180 dias**; conta de usuário enquanto ativa. **Não converter esses prazos automaticamente em prazo de snapshot CNPJ ou integration_tracking**, pois são tratamentos/categorias diferentes.
- `docs/13-auditoria-lgpd/relatorio-lgpd.md`: auditoria de 26/05/2026, 38 inconformidades resolvidas conforme status documental.
- `docs/13-auditoria-lgpd/relatorio-adequacao-lgpd.md`: 12 fases de adequação, 38 ocorrências resolvidas/risco aceito, registro de jobs de retenção, anonimização, acesso/portabilidade e consentimento. Descrição documental não substitui prova runtime.
- `docs/04-core-api/rastreamento-uso-apps.md`: enum `usage_tracking`, consentimento/revogação, purge e exportação do titular.

**Gate LGPD reclassificado:** `INSTITUTIONAL_LGPD_POLICY = PROVEN (docs)`; `LGPD_CONTROLS_IMPLEMENTED = DOCUMENTED (runtime not revalidated)`; `ENRICHMENT_CNPJ_TREATMENT_COVERAGE_IN_ROPA = TO_INVENTORY`; `REVIEW/PROPOSAL/DECISION_RETENTION = TO_INVENTORY`; `SERPRO_DATA_USE_TERMS = PENDING`; `LEGAL_NEW_TREATMENT_DECISION = PENDING ONLY IF NOT COVERED BY CURRENT ROPA/POLICY`. O próximo passo é *aplicar a política existente* e registrar extensão pontual da operação ROPA caso não esteja coberta — não criar política paralela ou exigir nova avaliação genérica do zero.

A regra de dois anos para audit logs no ROPA **não prova** prazo de `integration_tracking.supplier_field_provenance`, que, conforme relatório SUPPLIER-PROVENANCE-01, mantém retenção atual sem expurgo automático e pendência de prazo formal. Confirmar escopo/owner antes de afirmar conformidade completa.
