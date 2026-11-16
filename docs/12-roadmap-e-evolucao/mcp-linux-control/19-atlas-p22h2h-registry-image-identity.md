# ATLAS | P2.2h.2h: resolver ImageID por manifesto OCI imutavel

**Data:** 16/11/2026. **Estado:** candidato em Pull Request; revisão humana, CI e verificador independente pendentes. **PREPARE_DISABLED / ACT_DISABLED**.

## Contexto

A PR #209, integrada, introduziu um verificador de assinatura OCI com `gh attestation verify`. Esse leitor retorna a declaração SLSA e seu SHA-256, mas **não** o digest de configuração usado como ImageID do Docker. Não seria seguro igualar o digest do manifesto assinado ao ImageID do container, porque os dois apontam para objetos OCI diferentes.

## O que foi implementado

`it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_oci_registry.py` define o leitor interno `GHCRImageIdentityReader`.

1. Aceita exclusivamente digest `sha256:<64hex>` e usa o endpoint HTTPS fixo `https://ghcr.io/v2/roberiooliveiradev/delpi-public-hub/manifests/<digest>`. Proíbe URLs, tags e plataformas escolhidas pelo solicitante.
2. Usa `GET`, `httpx.AsyncClient`, SSL/TLS padrão, `follow_redirects=False`, `trust_env=False`, timeout de 5s e limites de resposta. Não executa shell, Docker, GitHub mutations nem deploy.
3. Compara SHA-256 calculado sobre os bytes retornados com o digest solicitado e, se presente, o header `Docker-Content-Digest`. Declarações JSON duplicadas, NaN, schema incorreto e media types não permitidos falham fechados. Confere as regras de OCI Image Spec e OCI Distribution Spec.
4. Se a assinatura aponta para um **índice OCI ou manifest list Docker**, seleciona exatamente um `linux/amd64`, verifica tipo, digest e tamanho do manifesto filho e rejeita ambiguidades. Se for manifesto direto, extrai ImageID, mas marca `platform=unverified`, pois a arquitetura não é atestada no manifesto sozinho.
5. Obtém o campo `config.digest` do manifesto de imagem, com media type e tamanho válidos. O resultado `OCIImageIdentity.image_config_id` corresponde à fórmula de ImageID descrita na OCI Image Config Spec. **Não** afirma que o container em produção executa esses bytes.
6. Em GHCR público que devolva 401, solicita **apenas** token anônimo de pull em `https://ghcr.io/token?scope=repository:roberiooliveiradev/delpi-public-hub:pull&service=ghcr.io`, sem redirecionamentos e sem usar URLs do header de challenge. Token de servidor opcional exige configuração confiável, não pode vir de HTTP/MCP e nunca vai para logs.
7. Cria testes em `it-portal-api/tests/unit/test_atlas_deploy_oci_registry.py` com `httpx.MockTransport`, cobrindo sucesso OCI direto/multiarch, assinatura de conteúdo, troca de token, erros 401/302/403/404/429/5xx, campos adversariais e negações.
8. Adiciona esses testes ao job PostgreSQL descartável no workflow `.github/workflows/atlas-p22e-integration.yml`, acionado quando módulo ou teste mudarem.

## Fronteiras de confiança

- `OCIImageIdentity` confirma uma cadeia de **identidade por digest no registro**. Não atesta assinatura ou proveniência sozinho. A futura composição da evidência CI deverá cruzar `VerifiedOCIStatement.manifest_digest == OCIImageIdentity.manifest_digest` e preencher `CIReleaseEvidence.image_config_id` somente a partir dos dois leitores internos efetivamente executados.
- Não envia requisições à API Protheus, Keycloak, Core ou servidor Linux. Nenhuma credencial de registry é gerada nem registrada automaticamente; o fluxo anônimo GHCR é de leitura pública.
- Não lê bytes do blob de configuração ou das camadas: a identidade `config.digest` é derivada do manifesto validado. Verificação de disponibilidade do blob e da plataforma de um manifesto direto pode ser adicionada numa etapa futura.
- A prova de host atualmente mantém `checkout_clean=False`, `migrations_safe=False` e `rollback_ready=False` por projeto; **não** elevar nem ignorar essas restrições.
- O projeto ainda não tem POST PREPARE real, autorização de aprovação nominativa, RBAC de escrita, role PostgreSQL writer de menor privilégio, ACT ou rollback automático.

## Critérios de aceite

- [ ] CI test-it-portal-api, PostgreSQL efêmero, Docker efêmero, audit e architecture-gate verdes.
- [ ] Revisão `delpi-verifier` por agente diferente, antes da integração final.
- [ ] Revisão de segurança do protocolo/token e confirmação do owner do GHCR.
- [ ] Teste operacional de leitura real de manifest OCI numa release assinada com token de pull em ambiente autorizado, incluindo digest do próprio `public-hub`. Testes mockados não substituem esta evidência.
- [ ] Evidência de compatibilidade com deploy manual, sem qualquer alteração de serviços de produção.

**Próxima etapa segura:** correlacionar os dois leitores com provas frescas, derivar `CIReleaseEvidence` somente de fontes independentes, verificar host+challenge e rollback com autenticação real, então propor RBAC e API PREPARE default-off. ACT é outra fase, com aprovação específica.

## Fontes técnicas

- OCI Image Manifest: https://github.com/opencontainers/image-spec/blob/main/manifest.md
- OCI Image Index: https://github.com/opencontainers/image-spec/blob/main/image-index.md
- OCI Image Configuration (ImageID): https://github.com/opencontainers/image-spec/blob/main/config.md
- OCI Distribution: https://github.com/opencontainers/distribution-spec/blob/main/spec.md
