# ATLAS P2.2h.2v-x | Pacote integrado de Core humano, diagnostico HML e challenge TOCTOU

**Data:** 16/11/2026 | **Status:** PR candidata, revisão pendente | **PROD:** intocada | **PREPARE/ACT:** desabilitados.

## Resultado funcional

As PRs #215 a #217 validaram assinatura de duas provas Linux, identidade da release CI/OCI e leituras read-only do journal, mas ainda não havia um componente efetivo que consultasse novamente a permissão humana no Core no início e no fim de um exame custoso. Esta entrega liga a autoridade real do Core ao fluxo de **diagnóstico HML apenas**, sem instalar ou ativar nada em servidor.

### V. Consulta Core real, obrigatoriamente fresca

Arquivo: it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_core_gate.py.

- O objeto TrustedHumanActor deve ser construído exclusivamente a partir do JWT já validado pelo middleware, nunca a partir de uma requisição livre, cabeçalho arbitrário ou mensagem MCP.
- FreshCorePrepareInspector usa o loader oficial delpi_auth.middleware.fastapi_auth.load_user_rbac com force_refresh=True, que desativa cache e fallback obsoleto na chamada. O loader é awaitable no mesmo event loop do backend; não iniciar asyncio.run por requisição.
- Verifica subject UUIDv4 idêntico entre middleware e resposta Core, principal_type user e permissões **explícitas** de it-portal.access, it-portal.deploy.view e it-portal.deploy.prepare. Não autoriza serviço, bot, superadmin, role wildcard ou Core indisponível.
- Falha com códigos finitos e não expõe token, corpo do /me, dados do usuário ou credencial. Resultado FreshCoreGrantObservation confirma que os grants foram vistos, mas mantém prepare_eligible=False e can_execute=False.
- **Atenção:** it-portal.deploy.prepare ainda não está registrado/provisionado como permissão oficial Core nesta PR. Não habilitar MANIFEST, Keycloak, Core nem expor essa rotina automaticamente.

### W. Diagnostico HML com dupla revalidação Core

Arquivo: it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_hml_admission.py.

- Gate default OFF. Rejeita ambiente prod, serviço diferente de public-hub, requester divergente do subject humano e todo resultado que represente PREPARE/ACT liberado.
- Chama Core com force_refresh primeiro, depois FullReadOnlyReadinessReviewer já existente (com release GitHub/Sigstore/GHCR, Git/Docker assinados e terceira leitura de challenge) e por último Core novamente com force_refresh, sem confiança em grant antigo.
- Nega grant revogado durante avaliação, Core indisponível, troca de subject, reconsulta com lacuna superior a 60 segundos, resultado adulterado ou evidências divergentes.
- HMLPilotBlockedDiagnostic consolida somente ambiente, serviço, commits de base/destino e causas genéricas de bloqueio. Não transporta JWT, challenge, segredo, statement assinado ou comprovante HMAC bruto.
- Bloqueios obrigatórios continuam: canal e identidade de host ainda não atestados, restore de backup não ensaiado, rollback não comprovado, migração não validada, papel writer e consumo transacional de nonce não autorizados, PREPARE e ACT desligados.
- Mesmo com grant Core observado, a leitura não concede direito de criar proposta, autorizar um deploy ou operar Docker.

### X. Proteção extra contra troca de challenge durante análise

Arquivos: atlas_deploy_readiness_review.py e atlas_deploy_full_readiness.py.

- A segunda leitura de challenge preserva issued_at, já confirmado contra a primeira. A terceira leitura read-only não aceita alteração de issued_at mesmo se expires_at permanecer igual.
- Um SELECT posterior ainda não impede consumo por outra transação depois da última leitura. O consumo único exige UPDATE concorrente na transação governada de PREPARE, com papel DB exclusivo e constraints já definidas no journal. Não construir endpoint ou iniciar essa operação nesta PR.

## Testes

- tests/unit/test_atlas_deploy_hml_admission.py: força force_refresh=True, impede serviços, superadmin wildcard, usuário sem grant, falha Core, dados adulterados, troca de subject, target prod, revogação na segunda leitura, relógio fora da janela e prova upstream falsamente aprovada.
- Tests de release e full readiness existentes recebem regressões para o novo issued_at. A prova de runtime continua coberta pelo job Docker e pelo teste interoperável da PR #217.
- CI ATLAS usa PostgreSQL 16 descartável; nenhum teste precisa de credenciais reais Core/host/GHCR ou de serviço da DELPI.

## Roteiro operacional futuro (dependências reais)

1. O owner confirma o desenho de Core com permissão nominativa it-portal.deploy.prepare e sua atribuição explícita, mais separação de reviewer/approval. A presença de permissão em um teste não registra grant no sistema real.
2. O DBA avalia um papel separado SELECT-only para a tabela de challenges, preservando o role it_portal_atlas_journal_reader sem esse acesso. Qualquer writer deve ser específico, transacional e aprovado posteriormente.
3. O operador de Linux valida canal autenticado com Keycloak S2S ou mTLS entre host e backend, isolamento de chaves, execução sem grupo docker/sudo e proxy estritamente read-only de inspect. No momento esse canal não existe no ATLAS.
4. Equipe documenta e executa restauração de backup em ambiente isolado, rollback real à imagem anterior por digest, ensaio de migração reversível e plano de contingência; prints e checklists sem testes práticos não constituem evidência suficiente.
5. Teste de interoperabilidade real, mas **somente após autorização do owner**, confronta o repo e GitHub CLI/Sigstore/GHCR, o journal e os recibos do host em HML. Exigir delpi-verifier independente e revisão humana antes de publicar a integração.
6. Qualquer modo PREPARE futuro exige grant Core e writer transacional com nonce único e idempotência; ACT requer aprovação operacional separada, executor isolado e controle de rollback.

## Portões de aceite para esta PR

- [ ] Seis checks GitHub Actions e suíte ATLAS verdes.
- [ ] Revisão independente por outro agente delpi-verifier registrada, sem equivalência com CI.
- [ ] Revisão humana de Core real versus dados de request, force_refresh e clocks.
- [ ] Verificar que nenhuma rota, env, role/grant, migration, script de deploy ou serviço sofreu alteração.
- [ ] Não declarar piloto real HML/PROD ou autorização de PREPARE/ACT.

**Limite:** código de verificação e relatório default-off. Nenhuma modificação de ambiente, credencial, permissão ou host.
