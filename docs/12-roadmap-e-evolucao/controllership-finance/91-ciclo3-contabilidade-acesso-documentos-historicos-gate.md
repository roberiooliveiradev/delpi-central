# Documento 91 — Ciclo 3 · Decisão do PO: acesso restrito da Contabilidade/DRE aos documentos históricos

**Data:** 2026-10-24  
**Origem:** decisão expressa do PO na conversa, escolhendo **Opção B — nova permission específica** para a audiência Contabilidade/DRE, com página própria dentro da Central de Fechamento.  
**Produto:** Portal Controladoria & Finanças → Central de Fechamento → PROC-0072.  
**Natureza:** decisão de produto documentada + solicitação de exceção ao contrato de permissões congelado; NÃO é contrato runtime aprovado.  
**Estado:** PRODUCT_DIRECTION_APPROVED / TRANSVERSAL_PERMISSION_CONTRACT_GATE_PENDING.  
**IMPLEMENTATION_AUTHORIZED=NO** nesta rodada.

## 1. Decisão expressa: o que foi aprovado

1. Usuários do DRE/Contabilidade serão **autenticados no Core/Minha DELPI** e terão **permission distinta**, para entrada restrita à área de documentos destinados à Contabilidade na Central de Fechamento. O PO escolheu expressamente **Opção B**, em substituição à recomendação anterior de apenas utilizar a permission geral com resource scope.
2. Esses usuários podem **consultar e baixar pacotes e arquivos do fechamento por competência histórica**, exclusivamente quando liberados e destinados a sua audiência/resource scope.
3. **Sem aceite de DRE/Contabilidade na primeira versão**: não valida anexo P2, não aceita/rejeita PackageVersion P5, não corrige classificação, não edita checklist, não finaliza/submete/reabre o pacote ou o estoque, não acessa Administração nem dados de outros destinatários.
4. A **Controladoria/Joici** produz/extrai relatórios TOTVS, obtém extratos e documentos externos, prepara/concilia, anexa, confere e disponibiliza os pacotes. Joici **pode acumular uploader e validator** se ambas as ações forem autorizadas no contexto, mas são eventos distintos, com ator/instante/versão e sem aceite automático por upload.
5. O Portal permanece domínio amplo: o privilégio de destinatário **não concede o access geral** da Controladoria, nem transforma a página de documentos em um Portal paralelo.

Estas são decisões **funcionais do PO**. Elas não definem, por si, o permission code final, o contrato de Core, o acesso à Home, storage, API de download, semântica de publicação, modelo físico ou critérios de conclusão mensal.

## 2. Conflito explícito com o baseline técnico congelado

Até esta decisão o contrato deste produto permitia EXATAMENTE duas permissions: controllership-finance.access e controllership-finance.manage. Fontes: [01](./01-visao-produto-naming-e-escopo.md), [24](./24-inicio-e-navegacao-principal.md), [23](./23-ledger-rq-ac-testes.md), manifesto plugins/controllership-finance/controllership-finance.manifest.json, teste plugins/controllership-finance/src/manifestContract.structural.test.mjs.

A decisão atual **SOLICITA EXCEÇÃO/REVISÃO DESSE FREEZE**, não atualiza automaticamente a authority canônica nem autoriza editar runtime. Reclassificar o invariant de duas permissions requer **gate transversal explícito** do owner de arquitetura/Core/Portal e migração coordenada de manifest, rotas, BFF, MFE, testes e docs.

**Não adicionar apenas uma linha ao array permissions**: a verificação no código demonstrou dependências relevantes:
- Manifest 1.0.0 declara só duas permissions. A Home/raiz /apps/controllership-finance é protegida por controllership-finance.access; as duas deep routes atuais também usam access.
- O teste manifestContract.structural.test.mjs exige literalmente duas permissions e proíbe granulares.
- Core ListUserAppsUseCase + AppAuthorizationService filtram rotas por permission efetiva e expõem authorizationRoutes para o guard; rotas usam uma permission por entrada.
- O Portal FederatedAppRouteGuard/resolveManifestRoutePermission usa match de rota mais específica; o ProtectedRoute exige a permission efetiva.
- BFF GET /viewer-context requer access, entrega capabilities access/manage; MFE ViewerContextProvider, PluginShell e Home atuais são consumidores desse contrato.
- BFF closing_routes.py exige access em todas as rotas vigentes. **Nunca** ampliar acesso a settlements/stock-inventory por conveniência para atender o leitor de pacotes.
- Core RegisterPluginUseCase sincroniza permissions e reconstrói rotas no registro/atualização do manifesto; verificar compatibilidade/migração sem apagar vínculos.

Portanto adicionar a terceira permission + uma página sem redesenhar o entrypoint e BFF gera **403/rota inacessível**, ou risco de liberação indevida se for forçado o access geral.

## 3. Contrato candidato — não aprovado para runtime

**Permission candidata (CAPABILITY, não nome de pessoa/grupo):** controllership-finance.closing-documents.read.  
**Label administrativo proposto:** Consultar documentos do fechamento.  
**Grupo/audiência candidata para grants do Core:** usuários designados da Contabilidade/DRE. Core possui ownership exclusivo de identidade, grants e effective permissions; a BFF não administra RBAC e não atribui permission pelo nome do setor.

**Página candidata:** /apps/controllership-finance/closing/accounting-documents, UX "Documentos para Contabilidade" com seleção da competência histórica, pacotes liberados, arquivo/versão/proveniência, visualização e download. Esta página não é substituta de P2 nem P5 operacional.

**Entrada no aplicativo — REQUISITO funcional estabelecido no diálogo:** o usuário da Contabilidade deve poder abrir o Portal pela Minha DELPI, chegar ao **Início/entrada restrita do fechamento** e acessar a nova página de documentos. O Início atual da raiz usa access, e o manifesto 1.0.0 declara permission única por rota; não é permitido conceder access geral ou abrir dados de outras páginas para contornar esse fato. O gate técnico precisa especificar uma experiência segura de entrada restrita que preserve a intenção de navegação do PO, testada no Core/launcher/Portal/BFF. Se o modelo vigente não suportar essa experiência sem mudança adicional de contrato, devolver DECISION_REQUIRED com impacto, não implementar alternativa silenciosa.
A **opção B de produto (nova permission)** está aprovada e NÃO deve ser perguntada novamente.

**AuthZ obrigatória por requisição, inclusive download:**
authenticated human AND effective_permission(capability específica resolvida no Core) AND recipient_assignment/ownership AND package/resource_scope AND business_rule(competência + PackageVersion + disponibilização).
Se a origem do vínculo, a liberação, o status da versão ou o Core estiver indisponível, negar **fail-closed**; não confiar apenas em route guard, menu, path, JWT nem arquivo público.

## 4. Fluxo de negócio, histórico e boundary

Controladoria registra e valida evidências em P2 → prepara consolidação P5 → gera PackageVersion → realiza ato de **disponibilização/envio conforme contrato P5 a reconciliar** → Contabilidade/DRE autenticada vê somente recipient packages liberados, por competência, com downloads auditáveis.

A expressão **"fechar o pacote" não é automaticamente "submeter" nem "concluir fechamento"**. Os estados PACKAGE_FINALIZED, PACKAGE_SUBMITTED_FOR_REVIEW e MONTHLY_CLOSING_COMPLETED são distintos no [37](./37-p5-submissao-e-revisao-no-portal.md). A leitura sem aceite da Contabilidade precisa distinguir **destinatário de consulta** de **reviewer P5**.

**Risco de conflito formal com C2/P5:** o doc 37 prevê aceites humanos reais por pacote/área para conclusão mensal. O PO decidiu que a Contabilidade/DRE não aprova na primeira versão. A solução documental deve **separar recipient package de consulta/download de pacote submetido para revisão**, sem promover C2 por vacuidade nem cancelar outros aceites já aprovados. A regra precisa ser homologada pelo owner funcional antes de alterar o doc 37, DTOs ou máquina de estados. O download NÃO é aceite ou evidência de aprovação.

**Storage, source-of-truth, disponibilidade histórica, audit log, prazo de retenção, composição da PackageVersion, mecanismo de download (stream vs link temporário), versionamento e escopo de filiais/recipients** são TO_INVENTORY e requerem decisão de contrato/owner antes de runtime. Proibido expor binários/signed URLs permanentes no frontend ou em logs.

## 5. Impacto por owner e classificação da mudança

| Superfície | Impacto | Estado |
|---|---|---|
| Produto/arquitetura | Rever freeze de duas permissions, registrar ADR/decisão de exceção, classificar diff | DECISION_REQUIRED para contrato transversal |
| Core / Plugin System | Sincronização de permission, grants, /me/apps, authorized routes, deep link, registro, migração e rollback | TO_INVENTORY |
| Manifest e UI Shell | Novo capability/route, entrypoint restrito, menu/launcher, resolver de rota mais específica | TARGET |
| MFE CF | Página de históricos, variant read-only, viewer-context e navegação compatíveis, sem vazar Home/relatórios | TARGET |
| BFF CF/P5 | Lista de competências, pacotes/documentos, fetch/download autorizado por resource, audit e erros | TARGET; P5 storage/contrato físico pendente |
| P2 | Arquivos versionados e validações; Joici uploader+validator com eventos separados e AuthZ | TARGET; owner/validator bindings pendentes |
| P5 C2 | Entrega para consulta sem aceite vs review humano; invariantes atuais preservados até novo gate | DECISION_REQUIRED sem mudança automática de C2 |
| Testes | Positive/sibling/negative de permissão exclusiva, grants/revocation, URL direta/download, versões históricas, cross-recipient/cross-filial, fail-closed | TEST_NOT_RUN |
| Docs + Help | 01/23/24/37/README, manual contextual e padrão plugin-ui first após freeze revisado | PLANNED |

**Evolução de contrato:** adição da capability/rota = candidato ADDITIVE; mudança de roteamento da Home e modelo de acesso = BEHAVIORAL/potencial BREAKING por consumidores e testes que pressupõem duas permissions; documentar compatibilidade e rollback antes de alterar o manifesto. Proibido eliminar ou transferir permissions access/manage existentes para consertar o novo perfil.

## 6. Gates/AC mínimos para autorização futura

1. Confirmar owners (Core, Portal/BFF, P2/P5, Segurança, Controladoria) e ratificar exceção ao freeze **sem alterar outras identidades congeladas**.
2. Fechar código final da permission, significado de capability, caminho/entrypoint e semântica de acesso restrito — especialmente desejo de acesso pelo Início versus deep route.
3. Identificar source físico e owner das PackageVersions, evidências e grants por destinatário; não criar storage por suposição.
4. Definir estado exato que libera consulta/download, relação com submission para review e impacto formal em C2 sem DRE aprovador.
5. Produzir contrato candidato producer→BFF→MFE (list/metadata/download), access control e audit, mais plano de migração/rollback do manifesto registrado.
6. Gate transversal de segurança/contratos/testes aprovado explicitamente; somente então autorizar implementação page-by-page e Help.
7. Testes futuros: Contabilidade permission-only vê só pacotes destinados; /closing/stock-inventory e /financial-settlements negados; ADMIN negado; download HTTP direto fora do scope retorna 403/404; Core/revogação indisponível falha fechado; usuário normal sem a nova capability não herda acesso ao documento; versão não liberada/histórica indevida negada; arquivo baixado íntegro.
8. Não executar cadastro/grant ou publicar manifesto/produto em produção durante o gate documental.

## 7. Próximo brief e verdict

**Brief proposto:** CF-C3-ACCOUNTING-DOCUMENTS-PERMISSION-CONTRACT-INVENTORY-001, modalidade READ+VERIFY+DESIGN_ONLY. Inventariar consumers do Core e do manifest, guards, MFE/BFF, owner e contrato P5/evidências, disponibilidade de download histórico; retornar pacote de decisão das lacunas acima e gate de mudança do permission freeze. **Zero diff runtime.**

**Estado do pedido:** opção B = PO_APPROVED_PRODUCT_DIRECTION. **Contrato runtime = PENDING/DECISION_REQUIRED; IMPLEMENTATION_AUTHORIZED=NO.** Não inferir GO de implementação nem declarar nova permission efetiva enquanto o manifesto/Core não forem alterados após gate explícito.
