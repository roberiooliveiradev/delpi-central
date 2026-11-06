# Product Registration — decisões do Product Owner e handoff de integração (2026-11-06)

> **Status:** `DECISION_APPROVED / IMPLEMENTATION_PENDING / HML_AUTHORIZED_CONDITIONALLY / PRODUCTION_NOT_AUTHORIZED`.
> **Owner da decisão:** Product Owner Portal Engenharia. **Escopo:** Product Registration e permissões do Portal Engenharia. Registrar e implementar a alteração sem inferir que o código ou o Core já estão ajustados.

## Decisões aprovadas

1. **Engenharia** é owner do workflow operacional de criação e alteração de materiais: solicitações, fila, atendimento, draft, comparação, revisões, publicação da cópia técnica governada e auditoria. **TOTVS** permanece source of truth do cadastro oficial, consultado pelo contrato read-only da **api-delpi**. Engineering API é BFF da experiência Engenharia.
2. **Somente duas permissões de Portal Engenharia:** `engineering.access` para acessar as páginas e executar CRUD/workflow operacional do módulo, **inclusive verificar e concluir sob as invariantes de domínio**, e `engineering.manager` para administração. **Não registrar nem exigir as cinco permissões novas `engineering.product-registration.{read,create,process,verify,admin}`.** O identificador `engineering.manager` é decisão de contrato do PO, **não foi encontrado como implementação registrada no repositório na inspeção inicial**: conferir catálogo, registration e owner Core antes de introduzir ou aplicar o controle de administração. No frontend, no backend REST e na EVA, substituir coerentemente os checks PRC granulares; qualquer acesso sem `engineering.access` deve falhar fechado. O acesso operacional amplo não elimina identidade humana, escopo de dados por solicitante, transições de estado, expectedVersion/CAS, auditoria, idempotência, confirmação verificável em ações EVA terminais e read-back oficial antes de concluir. Reavaliar a antiga política da fila por perfil: não inventar autorização baseada em papel não declarado.
3. **Autorizar ajuste interno da api-delpi para expor `accountingAccount` (`B1_CONTA`)**, inclusive SQL/mapeamento quando necessário, exclusivamente no owner `api-delpi`. Conferir `PRODUCT_DETAIL_ENGINEERING_FIELDS`, `_product_engineering_view`, DTO, policy, testes de contrato e provenance. Manter a chamada por `Portal/EVA -> Engineering API -> api-delpi -> TOTVS`. Engenharia não acessa banco/ODBC/TOTVS diretamente e **não escreve ERP**. Se qualquer campo requerido não for verificável, `verify_and_complete` deve bloquear a publicação.
4. **Autorizar homologação controlada em HML, condicionada aos gates técnicos e operadores habilitados:** revisão e aplicação `V012__product_registration_core.sql` + `eng_prc_grants.sql` pelo operador autorizado, migrações, verificação RBAC, testes PostgreSQL, UI, MCP/elicitation e consulta real via api-delpi/TOTVS em HML. Credenciais, dados, segredos e conexões só por meios autorizados. **Sem deploy/migration em produção**; rollback e postconditions obrigatórios.
5. **Correção do conflito PRODUCTS autorizada:** quatro arquivos em `plugins/engineering/src/features/products/` continham conflitos `Updated upstream` vs `Stashed changes`. A resolução em `main` preservou o ramo `Updated upstream` que contém navegação URL, filtros avançados, abas e testes adicionais: commits `0f2654e7a45f`, `8f517b8a4ac5`, `12110a8c70d`, `774be9547160`. Após esses commits foi verificada ausência de conflict markers nos quatro arquivos. **Build, typecheck e testes globais ainda não foram executados nesta atualização**. No próximo ciclo validar se a funcionalidade legítima do ramo descartado está coberta; não classificar como integração PASS sem esse teste.

## Revogações e precedência

A decisão de RBAC desta seção **substitui e prevalece** sobre as propostas anteriores de cinco permissões PRC e sobre declarações de que `engineering.access` não autoriza o Product Registration. Trechos históricos permanecem como evidência de decisões superadas, **não** como instrução de implementação.

No entanto, duas permissões de Portal não constituem autorização irrestrita de recursos ou aprovação artificial: Domain API continua autoridade para dados e mutações, com validação live e gates de operação terminal. Operações administrativas exigem `engineering.manager` **após verificar/registrar o contrato Core correto**; enquanto o contrato não estiver operacional, operações administrativas devem falhar fechado.

## Ordem de implementação e gates

- **PRC-D1:** baseline real, `AGENTS.md`, HEAD/status, isolamento multiagente, verificação do merge PRODUCTS e execução `typecheck/build/test` do plugin. Se houver falha remanescente, atribuir corretamente e corrigir dentro do ownership autorizado.
- **PRC-D2:** implementar refatoração do RBAC conforme duas permissões em REST, application, EVA, frontend, testes e manifests Core quando pertinente; preservar escopo por recurso e gates. Verificar como `engineering.manager` é realmente registrado; não criar as cinco permissões antigas. Adaptar testes que assertavam 403 com somente access. Evitar autoaprovação de operações administrativas.
- **PRC-D3:** implementar `B1_CONTA` em `api-delpi` sob owner apropriado e testes de contrato na view `engineering`, sem ampliar acesso além da policy. Confirmar JSON campo oficial retornado e consumido por `OfficialProductReader`; revalidar comparação create/update e SA5 Part Number.
- **PRC-D4:** revisão do esquema e grants; procedimento HML, execução somente em ambiente autorizado pelo operador e com evidência do banco/rollback.
- **PRC-D5:** testes integrados REST × EVA × UI, MCP elicitation real/harness fiel, PostgreSQL, HML via api-delpi/TOTVS, negativos e positivo, ações semânticas `planned -> proven` por evidência individual. Não confundir tests mocks com homologação da fonte.
- **PRC-D6:** ledger final com SHA, regressões, APPROVAL/FAIL/NOT_RUN, owner, rollout/rollback e decisão separada para produção.

## Decisões ainda pendentes

- Campos required de abertura versus conclusão e política de freshness/SLA do snapshot TOTVS (**C/F**): owners de Engenharia/api-delpi devem validar; não inventar valores.
- Detalhes exatos de registro do `engineering.manager` no Core: inventariar, implementar sob owner Core ou registrar ADR quando a alteração extrapolar authority.
- Publicação produtiva continua bloqueada até autorização explícita separada.

## Evidências de referência

- Base PRC-C1..C3 `773332c110`, UI `b517fc1a83`, EVA dispatch `8c69509340`, parity `3c46a1a08b` e correção terminal `19f924da62`.
- Último relatório PRC-C5 (fornecido pelo executor, não verificado independentemente neste documento): 119 testes PASS locais, 4/17 ações EVA marcadas proven, migration/grants não aplicados e HML não executado.
- Contratos: `PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md` e `PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md`.


## Decisão adicional aprovada — Part Number opcional quando ausente no TOTVS (2026-11-06)

> **Status:** `PO_APPROVED / CONTRACT_UPDATED / CODE_CHANGE_PENDING`. **Precedência:** esta decisão substitui qualquer validação anterior de `suppliers[].partNumber` obrigatoriamente não vazio. O drift identificado em PRC-D5.3 (`SA5.A5_CODPRF` vazio em produto oficial real) está **resolvido como decisão funcional**, mas a implementação exige alteração e testes.

- Para o vínculo de fornecedor `suppliers[]`, `partNumber` representa `A5_CODPRF` e é **opcional quando ausente/vazio na fonte oficial TOTVS**. Não inventar Part Number, não forçar preenchimento artificial e não bloquear um cadastro oficial válido apenas porque `A5_CODPRF` está vazio. Exigir e validar normalmente identidade do fornecedor, loja e demais campos obrigatórios aprovados; não tornar o fornecedor inteiro opcional por decorrência desta decisão.
- Quando o solicitante/analista **informar Part Number não vazio**, ou quando uma alteração **selecionar explicitamente esse campo**, a Engenharia deve comparar o valor final esperado com o valor da SA5 retornado pela `api-delpi`. Divergência, campo não verificável, ausência de vínculo, timeout ou acesso negado bloqueiam `verify_and_complete`; não publicar revisão. Se uma alteração explicitamente solicitar remover/limpar Part Number, o valor vazio é um delta explícito e só poderá concluir após comprovação de vazio no TOTVS (não confundir campo omitido, que significa não alterar).
- Para fornecedor oficial com `A5_CODPRF` vazio, aceitar `partNumber` omitido, `null` ou string vazia no **ingresso**, normalizando para representação canônica consistente (recomendação: string vazia `""` no modelo e snapshot), sem converter para valor inventado. **Distinguir ausência do atributo na resposta oficial (unverifiable) de atributo explicitamente vazio (verificável)**. Verificar contrato atual da `api-delpi` antes de implementar.
- Comparação de suppliers não pode associar arbitrariamente vínculos apenas por `partNumber`. Inspecionar identidade composta atual `(supplierCode, store, partNumber)`: caso PN deixe de ser obrigatório, preservar identidade de `supplierCode+store`, observar PN como atributo comparável, tratar duplicatas/ambiguidade da SA5 e manter independência da ordem do array. Não permitir que PN divergente passe como igualdade por supressão de campo.
- **CREATE:** aceitar suppliers sem Part Number, comparar fornecedores e atributos presentes/obrigatórios via leitura oficial; PN não informado corresponde a valor oficial vazio, não é wildcard para aceitar PN não vazio. **UPDATE:** preservar omissão como `não alterado`, compare apenas paths selecionados e assegure atualização explícita de PN, inclusive para vazio, com CAS/baseline e auditoria.
- **Canais em paridade:** REST intake, draft, reference-data, UI, EVA semântica (seis tools preservadas), testes e documentação devem refletir a mesma regra; AuthZ `engineering.access`, confirmação terminal e BFF `Engineering API -> api-delpi -> TOTVS` permanecem inalterados.
- **Critérios de aceite:** (1) supplier com SA5 PN vazio completa após match de todos os demais campos; (2) supplier com PN informado e oficial divergente bloqueia; (3) campo de PN ausente na resposta oficial não é interpretado como vazio; (4) remoção explícita de PN só conclui quando TOTVS vazio; (5) nenhum campo não selecionado de UPDATE é sobrescrito; (6) snapshot/auditoria preservam provenance e razão da alteração; (7) testes REST, PG, UI e EVA conforme aplicável; (8) nenhuma escrita no TOTVS.

**Esta decisão aprova a regra, não deploy.** Homologação DEV/HML controlada permanece autorizada sob gates; produção não autorizada.
