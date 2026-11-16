# ATLAS P2.2h.2a | Vínculo OCI imutável para proposta e aprovação

**Status:** CANDIDATO EM PR / VERIFICAÇÃO INDEPENDENTE PENDENTE / SEM MERGE / SEM DEPLOY  
**Contexto:** Public Hub PROD, imagem em execução diferente da imagem final assinada pelo CI.  
**Escopo:** contrato Python puro e testes negativos; nenhuma permissão Core, rota, migração ou executor ativado.

## Evidência confirmada no pré-verificador

O operador executou `infra/scripts/public-hub-release-preflight.sh --plan prod` e obteve `PLAN_OK_NO_DEPLOY`. O preflight verificou a atestação de `f81ddd0075de1e4ef8bb68ca58791e9c43e70759` e do manifesto `sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a`, enquanto o contêiner ainda usava `sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb` (commit `03cecb7ed90946c799a66ca9b22b45beb221282e`). A saída também informa `approval=NOT_IMPLEMENTED`, `readiness=NOT_VERIFIED` e `rollback=NOT_VERIFIED`.

**Consequência:** o sucesso de leitura não autoriza promover uma imagem. `plan_sha256=17f1730c4b5798168ca35c215b3e66f3947fdb998b82328219f03ed0d1e07110` é um identificador diagnóstico, jamais uma aprovação.

## Contrato implementado no candidato

`it_portal_app/infrastructure/persistence/atlas_deploy_oci_seal.py` cria apenas um candidato de proposta **com toda a identidade da imagem vinculada ao hash**:

- Repositório, imagem GHCR, workflow signatário e ref `refs/heads/main` fixos, sem valores arbitrários de entrada.
- Ambiente `prod|hml`, serviço `public-hub`, contêiner e projeto Compose da allowlist.
- Requester e request ID UUIDv4; SHA completo da imagem aprovada e SHA de base distintos.
- **Digest OCI do manifesto assinado**, ImageID da release e ImageID anterior, preservados como campos diferentes.
- Checksum da declaração da atestação, hash do challenge host, referência à imagem de rollback e hash do preview.
- Verificação da frescura (120s, tolerância de +5s) e compatibilidade exata das provas CI e host, mais `healthy`, `checkout_clean` e rollback atestado.
- Hash canônico sobre todos esses campos, emitido com `status=candidate_only` e validade de 10 minutos.
- Verificação de **formato/consistência** de uma aprovação atribuída a outro usuário, feita no portal, vigente, com permissão Core reavaliada recentemente, sem revogação nem execução anterior. O único retorno positivo é `approval_evidence_shape_only`, não uma permissão de ACT.

**Limites inegociáveis:** classes Python e booleanos de entrada não são prova autêntica. Somente um backend confiável pode construir essas evidências a partir de GitHub/Sigstore, Core e coletor host com desafio consumido no banco. O novo módulo **não faz essa aquisição**, não possui `docker`, SQL, HTTP, credenciais nem funções de deploy. Seu uso direto com objetos criados pelo ChatGPT não autoriza nada.

## Persistência proposta, ainda NÃO migrada

É preferível criar uma tabela própria associada à proposta genérica para não alterar silenciosamente o journal de outros serviços. **Exemplo para revisão pelo owner de PostgreSQL, não executar em PROD:**

```sql
-- CANDIDATO DDL, NÃO É UMA MIGRATION PROD. Depende da proposta P2.2d.
CREATE TABLE it_portal.atlas_deploy_oci_bindings (
  proposal_id uuid PRIMARY KEY
    REFERENCES it_portal.atlas_deploy_proposals(id) ON DELETE RESTRICT,
  environment varchar(4) NOT NULL CHECK (environment IN ('hml', 'prod')),
  service_id varchar(64) NOT NULL CHECK (service_id = 'public-hub'),
  signed_manifest_digest varchar(71) NOT NULL
    CHECK (signed_manifest_digest ~ '^sha256:[0-9a-f]{64}$'),
  release_image_id varchar(71) NOT NULL
    CHECK (release_image_id ~ '^sha256:[0-9a-f]{64}$'),
  base_image_id varchar(71) NOT NULL
    CHECK (base_image_id ~ '^sha256:[0-9a-f]{64}$'),
  rollback_image_id varchar(71) NOT NULL
    CHECK (rollback_image_id = base_image_id),
  ci_statement_sha256 char(64) NOT NULL
    CHECK (ci_statement_sha256 ~ '^[0-9a-f]{64}$'),
  host_challenge_sha256 char(64) NOT NULL
    CHECK (host_challenge_sha256 ~ '^[0-9a-f]{64}$'),
  sealed_binding_sha256 char(64) NOT NULL
    CHECK (sealed_binding_sha256 ~ '^[0-9a-f]{64}$'),
  CONSTRAINT atlas_oci_distinct_image_ids CHECK (release_image_id <> base_image_id)
);
```

O futuro `PREPARE` do backend deverá inserir proposal+binding+evento **na mesma transação**, comparar todos os campos sob lock quando `request_id` for repetido, e recomputar o hash canônico com parâmetros realmente confiáveis. A aprovação nominativa no Portal de TI deverá exibir os identificadores completos da release e associar o `approved_by`, `approved_at` e versão ao `sealed_binding_sha256`. Antes do ACT, exigir nova consulta Core, nonce único, verificação da assinatura, rollback demonstrado, lock e read-back do estado do contêiner.

O DDL é incompleto propositalmente como implementação: owner deve definir FK imutável da identidade de requester/ambiente ao proposal, impedir mudanças de bindings após `approved`, negar aprovação de proposta sem binding, políticas de grants e auditoria. **Não iniciar deploy usando somente este SQL.**

## Evidência de testes e próximos gates

- 72 testes unitários offline (com casos de assinatura/commit/digest trocados, ambiente, host, challenge, drift, rollback, TTL, permissão vencida, autoaprovação permitida com validações mantidas e replay/revogação); nenhuma conexão com produção.
- `python -m py_compile` passa no novo módulo.
- Ainda faltam: verificador independente `delpi-verifier` em outro modelo, revisão do owner do journal, migração de banco **somente após autorização**, testes de concorrência no PostgreSQL descartável, API PREPARE com RBAC Core, UI de aprovação e executor isolado testado em HML.
- **ACT, PREPARE via API e promoção da release em PROD continuam desabilitados.**
