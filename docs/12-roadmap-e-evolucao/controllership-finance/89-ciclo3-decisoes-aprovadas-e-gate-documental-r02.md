# Documento 89 — Ciclo 3 · Decisões do PO e gate documental R02

**Data:** 2026-10-24  
**Origem:** decisão expressa do PO após inventário C3-R01 (doc 88).  
**Produto:** Portal Controladoria & Finanças / Central de Fechamento / PROC-0072.  
**Estado:** `PRODUCT_SCOPE_DECIDED / DESIGN_AUTHORIZED_ONLY` (marcador documental, não gate de runtime).  
**Implementação:** `IMPLEMENTATION_AUTHORIZED=NO`.

## 1. Decisões aprovadas — escopo e design

| ID | Opção | Decisão de produto | Limite |
|---|---|---|---|
| C3-D01 | **A** | Primeira fatia somente read-only: competência/período, filial, estoque SB9 e baixas por contratos vigentes | Sem status do wizard ou painel novo de evidências |
| C3-D02 | **A** | Separar cálculo, persistência, conferência e homologação; fonte/proveniência por estado | Não inferir etapa ou aceite sem contrato/evidência |
| C3-D03 | **B** | Reabertura de estoque excluída da V1 | Sem execução, endpoint ou histórico novo |
| C3-D04 | **B** | Seleção por período já disponível; adiar novo `closing-context` e exposição de `MV_ULMES` | Nenhuma extensão de contrato autorizada |
| C3-D05 | **A** | Homologação exclusivamente por aceite humano explícito da Controladoria | G6×15 permanece PENDING; sem nova persistência de homologação autorizada |
| C3-D06 | **A** | Excluir superfícies sem fonte/contrato comprovado da V1 | E1–E12 continuam com owners |

Aprovação explícita do PO: apenas escopo/design. Não atribuir autorização a alternativas não selecionadas. O §7 do doc 88 permanece histórico de opções, superado por estas escolhas.

## 2. Inventário efetivo, obrigatório antes de desenhar

Há código read-only existente no HEAD (doc 88), a ser verificado novamente contra HEAD/status, instrução oficial, `.cursor`, ADR-010, docs 24/30/48–53 e consumers/producers/testes:

- MFE `plugins/controllership-finance` com Início e deep-routes vigentes de estoque e baixas.
- BFF `controllership-finance-api`: `/viewer-context`, `/closing/financial-settlements`, `/closing/financial-settlements/summary`, `/closing/stock-inventory`.
- api-delpi: `/financeiro/settlements/*` e `/financeiro/stock-inventory`; último distingue `available/incomplete/no_matching_items/source_missing` por filial.
- Filial/dataset sob scope fail-closed; RBAC efetivo via Core, human Bearer + S2S dedicado ADR-010. Jamais inferir autorização de UI ou JWT.
- Dados já entregues não equivalem a comportamento homologado: testes/rotas no código devem ser confrontados com resultados quando o gate permitir execução de smoke.

A identidade permanece congelada: plugin `controllership-finance`, MFE basePath `/apps/controllership-finance`, BFF `controllership-finance-api` baseUrl `/apps/controllership-finance-api`; permissions somente `.access` e `.manage`.

## 3. Direção de design da V1

Propor jornada `período → filial autorizada → estoque/baixas existentes → estado/proveniência disponível`, reutilizando o MFE/BFF e `@delpi/plugin-ui`. A página hub `/closing` permanece **candidata**, não rota aprovada para implementação. Páginas comuns do Portal (Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda; usuário deep-route) continuam convenção obrigatória, mas nenhuma nova rota deve ser criada nesta etapa.

Na UI, separar:
- **persistência de snapshot** baseada no contrato SB9, inclusive `branchesMissing` e `source_missing`;
- **cálculo/etapas do wizard** sem fonte contratual => não verificado/fora do recorte;
- **conferência** sem aceite comprovado => não inferir;
- **homologação** sem aceite expresso => pendente/não informada.

A redação de estados deverá ser testável, PT-BR, sem reduzir todo o fluxo à palavra “fechado”.

## 4. Próximo gate documental — CF-C3-02-READONLY-DESIGN-CONTRACT-GATE-001

**Executar somente READ + VERIFY + DOCUMENT; zero runtime.**

1. Capturar HEAD + status/branch, ler Project Instructions, instruções oficiais, .cursor aplicáveis, README, docs 86–89.
2. Conferir código, contratos, schemas, auth, producers, consumers e testes de cada rota já existente; distinguir CODE_PRESENT de RUNTIME_VERIFIED.
3. Confrontar RQ-C3-01..09 e AC do doc 88 com D01=A/D04=B; **remover da V1 dependências de `MV_ULMES`/wizard/contrato novo** e documentar lacunas.
4. Especificar wireframe/jornada e informação da página candidata `/closing`, sem criar rota; evitar duplicar Home/P7/Baixas.
5. Definir matriz `RQ → AC → BR-Rxx → owner → contrato vigente → evidência → teste planejado → página`.
6. Fazer inventário concreto `@delpi/plugin-ui` e layout/páginas comuns; prever temas, mobile, teclado/foco, empty/loading/error/help.
7. Verificar segurança fail-closed incluindo `principal_type=user`, effective access (Core), S2S, 403 `scope_unavailable`, 503 indisponibilidade; não inventar permissions.
8. Separar backlog de design V1, itens pós-V1 e dependências de owner; preparar plano page-by-page e critérios de smoke futuro sem executá-lo.
9. Executar busca residual documental de contradições com D01–D06. Atualizar apenas docs canônicos, com erratas rastreáveis.
10. Entregar **EXECUTION REPORT** com evidência, delta, RQ/AC, riscos, decisões materiais remanescentes e próximo gate. Parar com `DECISION_REQUIRED` se surgir mudança real de contrato/boundary/segurança/persistência.

**Saída aceitável:** design documentado pronto para GPT REVIEW, não funcionalidade publicada. Nenhum gate transversal de implementação é concedido aqui.

## 5. Dependências e aprovações não concedidas

- G6×15 = PENDING; Ciclo 2 permanece **47/60 · 55/90 · 0/15**.
- E1–E12 mantidos; E5 (MATA280 writer SB9) é correlação temporal forte, não atribuição auditada do `INSERT`.
- CPV mensal LIVE preservado; E6=C aprovado somente como direção de produto, sem runtime.
- Nenhum scaffold, endpoint, contrato, migration, UI, alteração Protheus ou deploy nesta rodada.
- Para runtime: gate transversal explícito e autorização separada page-by-page, após review, ownership, RQ/AC e decisões remanescentes.

**Próximo resultado esperado:** `GPT REVIEW → decisão sobre gate de design/contratos → eventual autorização de implementação específica`, nunca execução automática.


## 6. Esclarecimento de alcance — crosswalk PROC-0072 E2E (2026-10-24)

Após consulta direta ao TÉO/Transformômetro PROC-0072 (docs 31, 31.1–31.19 e 33), confrontada com o ledger [23](./23-ledger-rq-ac-testes.md) e o contrato P5 [37](./37-p5-submissao-e-revisao-no-portal.md), registra-se o alcance **sem alterar as seis decisões C3-D01..D06**:

- A escolha C3-D01=A e as demais opções delimitam **apenas a primeira fatia read-only de design**; não reduzem a funcionalidade inteira à consulta de SB9/SE5.
- O **TARGET funcional da Central de Fechamento permanece P1–P6**: cockpit, checklist/evidências e aceites de PDFs, cutoff/conciliação, classificações/pendências, versão/submissão/review humano dos pacotes, administração/notificações.
- A submissão P5 aprovada é **portal-first** (reviewers autenticados na Minha DELPI); e-mail é canal de notificação sem pacote anexo ([37](./37-p5-submissao-e-revisao-no-portal.md)). A validação de anexo P2, a revisão do pacote P5 e G6 do inventário de relatórios são aceites distintos.
- “V1” em documentos de P1–P6 significa TARGET funcional V1; “primeira fatia C3” é incremento read-only. Confundir os escopos é EXECUTION_DRIFT documental, não autorização para reabrir decisões TO-BE anteriores.
- A especificação TO-BE completa e o alinhamento por RQ/AC/contratos/gaps constam do [doc 90](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md). Contratos físicos de P2/P5, T03/T05 e gate de runtime permanecem pendentes.

**Não houve nova decisão de produto nem GO de implementação.** Para o próximo brief, consultar primeiro o crosswalk E2E, depois aplicar a fatia específica e os gates por página.
