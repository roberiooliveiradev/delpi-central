# Minha DELPI — Checklist de Code Review

> **Status:** documentação oficial — setembro/2026  
> **Escopo:** Core API, API DELPI, APIs de domínio, Portal, plugins/MFEs, jobs e infraestrutura.

Este checklist deve ser aplicado junto de [responsabilidades-transversais.md](./responsabilidades-transversais.md). Nem todas as oito responsabilidades são materiais em todo PR, mas toda mudança relevante deve declarar quais foram avaliadas.

---

# 1. Arquitetura e boundaries

- [ ] O bounded context/owner da regra está claro?
- [ ] A mudança foi feita no contexto dono, não no consumidor/sintoma?
- [ ] Domain/application não dependem de framework, DB, HTTP ou SDK externo?
- [ ] Apps se integram por contrato, não por import de domain/use case do vizinho?
- [ ] Não há acesso direto ao banco de outro bounded context?
- [ ] `shared/` contém apenas código transversal sem regra de produto?
- [ ] MFE com API própria não bypassa sua API/BFF?
- [ ] Não surgiu segunda fonte de verdade para a mesma regra?

Regra: `.cursor/rules/platform-architecture-boundaries.mdc`.

---

# 2. Segurança, identidade e autorização

- [ ] Backend valida autenticação e autorização efetiva?
- [ ] JWT valida assinatura, issuer, audience e expiração conforme stack vigente?
- [ ] Frontend não é a única barreira de permissão?
- [ ] Escopo de filial/unidade/tenant é validado no backend quando aplicável?
- [ ] Usuário autenticado sem permissão recebe deny correto?
- [ ] Ações admin/destrutivas possuem proteção/auditoria adequada?
- [ ] Não há token/secret/password/API key em código, query string ou logs?
- [ ] Não existe bypass/superadmin ad hoc fora da governança canônica?
- [ ] Negative tests de autorização foram adicionados quando a superfície mudou?

Regra: `.cursor/rules/platform-security-identity-authorization.mdc`.

---

# 3. APIs, contratos e integrações

- [ ] Método/path representam corretamente a capacidade/recurso?
- [ ] Request/response e erros têm contrato explícito?
- [ ] OpenAPI está alinhado ao runtime quando existe?
- [ ] `operationId` permanece estável ou a mudança foi tratada como breaking?
- [ ] Status codes/códigos de erro são coerentes e não escondem falha em `200`?
- [ ] Paginação/limites existem quando o volume pode crescer?
- [ ] Writes sujeitos a repetição possuem idempotência quando necessária?
- [ ] Consumers reais foram inventariados antes de mudança comportamental/breaking?
- [ ] Client HTTP possui timeout e política de retry segura?
- [ ] Contrato entre contexts não contém regra específica do consumidor?

Regras: `.cursor/rules/platform-api-contracts-integration.mdc`, `contract-evolution-backward-compatibility.mdc`.

---

# 4. Dados e persistência

- [ ] O schema pertence ao bounded context correto?
- [ ] PK/FK/UNIQUE/NOT NULL/CHECK refletem invariantes quando aplicável?
- [ ] Índices foram avaliados a partir das queries reais?
- [ ] SQL é parametrizado?
- [ ] Repository não contém HTTP/autorização/regra de apresentação?
- [ ] Transaction/UoW possui fronteira clara e sem commits-surpresa?
- [ ] Race condition/idempotência/concurrency foram consideradas?
- [ ] Alteração de schema possui nova migration?
- [ ] Migration já versionada/aplicada não foi editada?
- [ ] Produção não depende de reset destrutivo?
- [ ] Upgrade/mixed version/rollback ou roll-forward foram considerados?
- [ ] Upload/arquivo durável não depende de filesystem efêmero?

Regra: `.cursor/rules/platform-data-persistence.mdc`.

---

# 5. Frontend, MFE e experiência

- [ ] UI não reimplementa regra de negócio/autorização efetiva?
- [ ] `@delpi/plugin-ui` foi reutilizado antes de criar componente local?
- [ ] CSS do MFE não vaza para Portal/outros plugins?
- [ ] Loading, empty, error e forbidden foram considerados?
- [ ] Formulário preserva estado/erro recuperável e evita double submit quando necessário?
- [ ] Tema claro/escuro funciona quando a mudança visual é material?
- [ ] Layout foi validado em desktop e mobile?
- [ ] Navegação por teclado/focus/labels/contraste foram considerados?
- [ ] Module Federation/host containment continuam corretos?
- [ ] Build do MFE passa?
- [ ] Smoke federado no Portal foi feito quando a mudança pode divergir do standalone?
- [ ] Ajuda/tooltips/manual foram sincronizados em feature user-facing?

Regra: `.cursor/rules/platform-frontend-mfe-experience.mdc`.

---

# 6. Qualidade, testes e evidência

- [ ] O objetivo/bug foi reproduzido ou baseline foi registrado quando possível?
- [ ] A causa raiz, e não apenas o sintoma, foi corrigida?
- [ ] Existe caso positivo?
- [ ] Existe sibling para evitar overfitting?
- [ ] Existe negativo para evitar falso positivo/bypass?
- [ ] Contrato/integração foram testados quando unitário não prova wiring?
- [ ] Teste não foi alterado apenas para aceitar comportamento errado?
- [ ] Evidência corresponde ao commit/configuração atuais?
- [ ] Gate vermelho foi classificado, não ignorado?
- [ ] O objetivo original foi revalidado após os testes?

Pergunta obrigatória:

> Como isto ainda pode estar errado mesmo com os testes passando?

Regra: `.cursor/rules/platform-quality-testing.mdc`.

---

# 7. Delivery, runtime e operações

- [ ] Configuração varia por ambiente sem hardcode de máquina/secret?
- [ ] Docker/Compose continua reproduzível?
- [ ] Health/readiness representam aplicação pronta, não só processo iniciado?
- [ ] Gateway dev/prod foram avaliados quando a rota/proxy mudou?
- [ ] Headers/auth/timeouts/body limits/SSE/WebSocket foram preservados quando aplicável?
- [ ] Artefato implantado é o artefato testado?
- [ ] Migration/deploy order é compatível com rolling deploy?
- [ ] Rollback/roll-forward é conhecido para mudança de risco?
- [ ] Feature flag/shadow/canary possui critério de promoção/remoção quando usado?
- [ ] Não existe passo manual dentro do container que será perdido no rebuild?

Regra: `.cursor/rules/platform-delivery-runtime-operations.mdc`.

---

# 8. Confiabilidade e observabilidade

- [ ] Fluxo crítico possui logs estruturados/correlation ID adequados?
- [ ] Erros preservam código/causa observável sem vazar dados sensíveis?
- [ ] Timeout explícito existe para dependências remotas?
- [ ] Retry só ocorre quando seguro/idempotente?
- [ ] 429/5xx/backoff são tratados sem retry storm?
- [ ] Fan-out/payload/paginação/concurrency possuem limites?
- [ ] Fallback/partial result não transforma falha em sucesso silencioso?
- [ ] Métricas adicionadas têm semântica útil e cardinalidade controlada?
- [ ] SLI/SLO/alerta/runbook foram considerados para fluxo crítico?
- [ ] Redaction de tokens/secrets foi validada?

Regra: `.cursor/rules/platform-reliability-observability.mdc`.

---

# 9. Plugin System e Core governance

Quando aplicável:

- [ ] Manifest segue schema/versão vigentes?
- [ ] `id`, versão, basePath, entry e routes permanecem coerentes?
- [ ] Permission codes declarados correspondem ao enforcement backend?
- [ ] Não há colisão de rota/permissão/app?
- [ ] Alteração de plugin não duplica governança que pertence ao Core API?
- [ ] Menu/rotas do Portal seguem o contrato dinâmico vigente?

---

# 10. API DELPI / TOTVS

Quando aplicável:

- [ ] Route/controller só traduz HTTP e chama camada correta?
- [ ] Use case depende de port/repository, não de detalhe TOTVS direto?
- [ ] Query TOTVS segue regras de performance/semântica do domínio?
- [ ] Contrato de resposta da API DELPI foi preservado?
- [ ] Permission/authz são aplicadas no backend?
- [ ] API DELPI não absorveu regra específica de outro bounded context?

---

# 11. Documentação

- [ ] Fonte normativa afetada foi atualizada?
- [ ] Novo contrato/variável/schema/permission está documentado onde é canônico?
- [ ] Não foi criado documento concorrente para conceito já documentado?
- [ ] Roadmap/changelog não está sendo usado como substituto de arquitetura vigente?
- [ ] Links para arquivos removidos/renomeados foram atualizados?

---

# 12. Aprovação final

- [ ] Responsabilidades transversais materiais foram declaradas/revisadas?
- [ ] Nenhum requisito de segurança foi relaxado?
- [ ] Nenhuma segunda fonte de verdade foi criada?
- [ ] Testes/build/gates relevantes passaram?
- [ ] Falhas externas ao diff foram classificadas com evidência?
- [ ] O runtime real foi validado quando necessário?
- [ ] PR/diff permanece revisável e com objetivo coerente?

## Documentos relacionados

- [responsabilidades-transversais.md](./responsabilidades-transversais.md)
- [padrao-de-rota.md](./padrao-de-rota.md)
- [padrao-de-use-case.md](./padrao-de-use-case.md)
- [padrao-de-repository.md](./padrao-de-repository.md)
- [padrao-de-erro.md](./padrao-de-erro.md)
- [padrao-de-evento.md](./padrao-de-evento.md)
