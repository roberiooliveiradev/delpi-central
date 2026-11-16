# ATLAS P2.2h.2b | Journal transacional vinculado à imagem OCI

**Data:** 2026-11-16  
**Estado:** implementação candidata em PR, revisão independente pendente. **Não migrado / sem API / sem ACT / sem deploy.**

## Objetivo

Armazenar a proposta e a identidade exata da imagem assinada na **mesma transação PostgreSQL**, com idempotência. A P2.2h.2a implementou a validação e o hash do candidato; esta etapa acrescenta um adapter de persistência **inerte**, sem alterar o journal genérico do Portal TI.

## Mudanças técnicas

- **Vínculo atômico:** uma transação bloqueia a chave (solicitante, request ID), consulta o relógio do banco, revalida as provas CI/host, consome o challenge uma única vez, insere proposta + registro OCI + evento prepared. Se qualquer operação falhar, toda a transação é revertida, inclusive o challenge.
- **Replay estrito:** mesmo request ID só devolve a proposta quando os dados armazenados são idênticos: identidades, ambientes, commits, digest do manifesto, ImageIDs anterior/novo, rollback, hash da atestação, challenge host, hash do preview, hash canônico, timestamps, nonce e estado pendente.
- **Imutabilidade:** o campo proposal_hash do journal-base referencia o mesmo binding_sha256. O registro OCI é protegido por FK, constraints e triggers SQL que impedem update/delete do binding e mudança da identidade do parent. Propostas Public Hub sem binding não passam a estados de aprovação/execução.
- **DDL apenas de teste:** arquivo 12-atlas-p22h2b-disposable-oci-bindings.sql, aplicável somente após o esquema candidato P2.2d em PostgreSQL descartável. **Não é uma migração PROD**.
- **CI:** o workflow existente atlas-p22e-integration.yml executa testes PostgreSQL 16 descartáveis de criação, retry, concorrência, erro injetado no evento, rollback, prova vencida, assinatura negada, atualização indevida e interdição de aprovação sem vínculo. Também roda os 72 testes P2.2h.2a.
- **Sem alteração em:** journal genérico existente, rotas API, grants Core, migrations versionadas, Compose, Keycloak, gateway, MCP ou executores.

## Limites e segurança

A opção backend_policy_enabled=True **não representa autorização**. Um futuro backend só poderá chamar o adapter após autenticação de usuário, RBAC Core, verificação independente Sigstore e challenge de host com freshness, health e rollback. Nenhuma dessas fontes está conectada ao adapter nesta PR. Objetos dataclass construídos por usuário ou modelo não são prova autêntica.

O adapter retorna somente um estado pending_approval no journal inerte. Não aprova, não concede permissão para ACT e não instala imagem no servidor. O esquema precisa de revisão do owner de PostgreSQL, política de grants, controle da aprovação nominativa e migração futura antes de qualquer uso. **PREPARE_API_DISABLED / ACT_DISABLED / PROD_UNTOUCHED.**

## Aceite e próximos gates

1. CI PostgreSQL real descartável com testes genéricos e OCI PASS, incluindo dois escritores concorrentes criando um único binding/evento.
2. Falha no último INSERT reverte proposal, binding e consumo do nonce; jamais confundir retorno do adapter com autorização.
3. CI arquitetura, Portal TI e governança PASS. **Revisão obrigatória por outro modelo/agente delpi-verifier** ainda pendente nesta entrega.
4. P2.2h.2c: revisão de owner e desenho de migração versionada, autenticação Core, API PREPARE, UI de aprovação nominativa e testes em homologação antes de pensar em executor.

**Rollback:** o código só está em branch/PR e a migração é documental. Nenhuma operação no banco produtivo ou contêiner foi efetuada.
