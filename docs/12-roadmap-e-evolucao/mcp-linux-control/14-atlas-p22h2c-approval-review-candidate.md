# ATLAS P2.2h.2c | Pré-validação Core e tela de revisão inerte

**Data:** 2026-11-16.
**Estado:** candidato offline; SEM rota, grants Core, UI ativa, migração, aprovação, ACT ou deploy.

## Contexto e objetivo

A PR #199 integrou à main a persistência transacional OCI. A próxima camada é separar quem pode **revisar** uma proposta assinada de quem a **solicitou**, antes de criar uma API de aprovação real. Isto NÃO transforma o ChatGPT em autoridade de autorização. O deploy manual do time não deve depender do ATLAS.

## Contratos adicionados

- Backend puro `it_portal_app/domain/atlas_deploy_approval_review.py`: precondições da revisão de proposta Public Hub. A política é desligada por padrão, só aceita usuário humano, identidade UUIDv4 e permissão Core recente (até 60 s; tolerância de relógio +5 s). Exige as permissões separadas propostas `it-portal.access`, `it-portal.deploy.view`, `it-portal.deploy.approve` e nega autoaprovação, status não pendente, revogação, expiração, digest inválido e mudança de ImageID. Retorna exclusivamente `review_candidate_only`, sem qualquer autorização de ação.
- Permissões `it-portal.deploy.view` e `it-portal.deploy.approve` são **nomes candidatos** que NÃO foram cadastrados nem concedidos no Core. Somente o owner de identidade/segurança poderá definir e registrar a política final.
- Frontend `plugins/it-portal/src/features/deploy-approvals/DeploymentReviewPreview.tsx`: componente apresentacional para revisão das identidades (SHA, digest OCI, ImageID atual/alvo e hash da proposta), com UX responsiva e estados vazios. Botões **Aprovar** e **Rejeitar** permanecem sempre desabilitados e não possuem onClick, API, request ou effects.
- A prévia não foi integrada a App.tsx, rotas, navegação, manifest, capabilities ou gateway. **Não aparece aos usuários na produção**, mesmo que outro desenvolvedor faça o deploy canônico do Portal TI.
- Testes negativos de RBAC, expiry, principal S2S, autoaprovação, status, digest e ausência de comunicação/rede. O CI normal da API e da UI será executado após o commit.

## Regra de convivência com deploy manual

**ATLAS é opcional e aditivo.** O modo manual continua sob responsabilidade dos desenvolvedores com acesso atual a Git/Docker. Esta etapa NÃO altera `infra/docker-compose.yml`, `up-prod-sequential.sh`, `up-hml-sequential.sh`, grupos do Linux, permissões de arquivos nem CLI. Se um operador fizer deploy manual e o runtime se mover, propostas ATLAS futuras devem caducar por drift e exigir novo preflight, nunca bloquear comandos manuais.

## Segurança e limites

1. O módulo puro não sabe quem autenticou as dataclasses: um backend confiável deverá construir os dados a partir de JWT de usuário, RBAC Core consultado novamente, journal/binding sob transação, GHCR Sigstore e observação host com challenge fresco. A flag de teste não substitui autenticação.
2. Nunca usar o resultado `review_candidate_only` como autorização para PATCH de status, emissão de nonce de execução, PREPARE/ACT ou Docker.
3. Aprovação real futura exigirá Core grants aprovados pelo owner, separação requester/approver, transação de estado/evento append-only, expiração e revogação, auditoria nominativa, proteção contra replay/concorrência e revalidação no instante do ACT.
4. A futura API deverá começar por **GET de consulta autorizada**, sem POST/PATCH de aprovação, até concluir revisão independente e ensaio em PostgreSQL HML descartável. Não conceder permissão no Keycloak automaticamente.
5. `delpi-verifier` com outro modelo é mandatório para fechar o gate de código. Se indisponível, registrar `INCONCLUSIVE`, não alegar PASS. Os testes CI não substituem o verificador.

## Próxima etapa

P2.2h.2d: acordar o owner dos códigos Core, autorizar uma migration versionada separada do candidate SQL, conectar consulta GET real do journal ao Portal TI e habilitar uma tela de **leitura** apenas para usuários com permissões reais. Só então desenhar o POST de aprovação nominativa. `ACT_DISABLED` permanece.
