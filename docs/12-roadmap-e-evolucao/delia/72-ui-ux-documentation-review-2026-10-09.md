# DÉLIA — Revisão integral da documentação de UI/UX

**Data:** 2026-10-09  
**Natureza:** documentation review, sem implementação ou aceite de runtime  
**HEAD analisado inicialmente:** `86b9459976123123a8277c0aa3b091da4255e66f`  
**HEAD de referência da revisão:** revalidar após commits documentais  
**Veredito:** `ACCEPT_WITH_RESIDUAL` para **direção documental de UX**, NÃO para frontend implementado nem fase de execução.

## Escopo e autoridade

Revisados diretamente no GitHub: [09 — UX](./09-ux-copilot.md), [69 — experiência conversacional, multimodalidade e motion](./69-conversation-experience-ux-wireframes-and-activity-plan.md), [70 — atividade de ferramentas e fontes](./70-tool-activity-and-source-transparency-ux-specification.md), [71 — fila por conversa e Meus Trabalhos](./71-conversation-queue-and-my-work-ux-specification.md). Confronto estrutural com autoridades [16](./16-execution-master-plan.md), [17](./17-component-and-contract-map.md), [49](./49-architecture-and-design-patterns-standard.md), [50](./50-standalone-copilot-application-architecture.md), [51](./51-platform-integration-baseline.md), [52](./52-standalone-repository-and-bootstrap-plan.md), [21](./21-data-and-state-model.md), [20](./20-testing-and-acceptance-matrix.md), [25](./25-requirements-traceability.md), e temas [36](./36-copilot-tasks-cases-and-interaction-rooms.md), [43](./43-durable-workflow-runtime.md), [53](./53-multimodal-meeting-frontline-and-industrial-copilot.md). Revisão de consistência documental; **não comprova testes, runtime, contratos ou completude de CP/RQ no HEAD**. Não substituir reancoragem completa de Devin no SHA de implementação.

## Achados e ações

| ID | Severidade | Achado | Encaminhamento |
| --- | --- | --- | --- |
| UX-R01 | Alta (editorial) | Textos das seções recentes 69 e dos docs 70/71 continham backticks escapados como `\\`...`, inclusive fences de wireframe, prejudicando Markdown no GitHub. | **CORRIGIDO** nos 69/70/71 em commits documentais sequenciais; verificação: fences pares (69:30, 70:14, 71:12), nenhum backtick escapado residual. |
| UX-R02 | Média | Direção visual aprovada pode ser lida como autorização de desenvolvimento. | Manter `APPROVED_PRODUCT_UX_DIRECTION` separado de `IMPLEMENTATION_NOT_AUTHORIZED`. Gate de fase: fonte `16` + ledger, não docs 69–71. |
| UX-R03 | Alta | Atividade de MCP/APP/web em progresso exige eventos verificáveis; a experiência atual descrita é HTTP JSON. | Primeira slice apenas loading genérico local + proveniência do JSON final. Activity streaming só após inventário + contrato aprovado; não inventar SSE. |
| UX-R04 | Alta | Conversas/histórico, fila durável, Meus Trabalhos e multi-dispositivo aparecem nos wireframes, mas não têm runtime comprovado nesta revisão. | `TO_INVENTORY`; não prometer essas funções em produção. Separar protótipo de comportamento real. |
| UX-R05 | Média | Mistura de UX atual, design target e mockups ricos pode induzir implementação de tabelas/charts/attachments, áudio Live. | Criar matriz por capability com `PROVEN / TO_INVENTORY / PLANNED / TARGET` antes do Devin; contrato `presentation.v1` do backend determina blocos permitidos. |
| UX-R06 | Média | Catálogo `plugin-ui` documenta elementos candidatos, mas adequação de Timeline, Message Thread, Composer, Loading, Navigation não está provada. | `EXISTING_EQUIVALENT=TO_INVENTORY`; `REUSE_DECISION=TO_DECIDE` por componente; proibir fork de Minha DELPI Chat. |
| UX-R07 | Média | Fila per-conversation vs Work durable tem ownership diferente e requer contrato de identidade, concorrência, cancelamento e política de dependências. | Separar queue intent UI do durable scheduler/Work; validar em [21]/[36]/[43] antes de implementação. |
| UX-R08 | Média | Multimodalidade inclui ditado com revisão por IA e Live; pipelines, retenção e captura não foram comprovados. | Primeira entrega candidata = ditado/transcrição/ajuste conservador/revisão explícita. Live posteriormente, conforme fase; política de privacidade e media contracts antes de código. |
| UX-R09 | Média | Figuras dos mockups gerados em chat não foram versionadas; documentos têm wireframes ASCII. | Não afirmar que há PNGs/frames pixel-perfect aprovados no GitHub; armazenar assets de referência apenas após seleção e higienização. |
| UX-R10 | Média | Especificações propõem timings e alturas em pixels que ainda não foram validados em devices, Zoom/reduced-motion. | Tratar como alvos UX; testar responsividade, a11y e contrastes nos temas Portal. |
| UX-R11 | Média | Ausência de matriz única rastreando WF-01..06, WF-T01..06, WF-Q01..05 até componentes, contratos e CP/RQ. | Devin inicia com mapa `WF → owner → feature gate → existing equivalent → contract → acceptance test`. Não criar CP/RQ arbitrários. |
| UX-R12 | Baixa | UX 09 é mais ampla (C0–C7: Twin, Control Tower, Process, Meeting, etc.) do que 69–71. | Não considerar 69–71 uma substituição integral da 09; são temas especializados e não especificam superfícies avançadas. |
| UX-R13 | Alta | Indicação de sucesso técnico, sucesso da tool e resultado de negócio podem ser confundidos. | Preserve `tool completed != grounded FACT != authoritative outcome`, com fontes internas vs web externas explícitas. |
| UX-R14 | Alta | Confirmação, links de autorização, mensagens de owner e botões em mockups podem introduzir AuthZ paralela. | Só renderizar CTA vindo de contrato backend governado; Core live AuthZ + Domain authority + Policy/Decision em qualquer write. |

## Matriz de direção de produto, estado e owner

| Tema | Direção documentada | Owner para execução | Evidência/estado a revalidar |
| --- | --- | --- | --- |
| Página inicial / recepção | Saudação simples, sugestões permitidas e composer | DÉLIA MFE + `plugin-ui` | DESIGN, implementação TO_INVENTORY |
| Sidebar e conversa | Sidebar DÉLIA separada da sidebar Portal | DÉLIA MFE; Portal host | Histórico durável TO_INVENTORY |
| Timeline / presentation.v1 | Renderizações text/notice, limitations/provenance | DÉLIA backend + MFE | Contrato no SHA corrente, testes não executados aqui |
| Dock flutuante | Mesmo renderer, forma compacta | Portal host + DÉLIA MFE | Contrato de continuidade de sessão TO_INVENTORY |
| Activity UI | Compacto/expandido, status real | DÉLIA backend projection + MFE | Eventos progressivos TO_INVENTORY |
| MCP/apps/web | Nome semântico + fontes + limitações, sem logs | Owners Domain/MCP; backend projection | Disclosure e status por owner TO_INVENTORY |
| Ditado | STT + ajuste IA conservador + revisão humana | DÉLIA application / adapters legítimos + MFE | PLANNED; provider/storage TO_INVENTORY |
| Live voice | Sessão bidirecional futura | DÉLIA + media providers | TARGET |
| Imagem/vídeo | Frame → vídeo curto → assistido → continuous | DÉLIA + owners autorizados | TARGET; etapas condicionadas à fase |
| Mini fila por conversa | FIFO, reordenação pendente, compacta e altura limitada | DÉLIA MFE + owner de conversation/work | Contrato/persistência TO_INVENTORY |
| Meus Trabalhos | Surface consolidada durável por permissões | DÉLIA Work e Domain/Core | TARGET / runtime TO_INVENTORY |
| Motion | Pulse discreto, transições, reduced motion | `plugin-ui` / MFE | Tempos propostos, a11y NOT_TESTED |
| Branding | `--primary #089BDB`, tema Portal light/dark | Portal + `plugin-ui` | Tokens documentados; novo branding próprio TO_DECIDE |

## Sequência recomendada após o review

1. **Devin / DQ0 (somente inventário):** HEAD/status, instructions/authorities/ledger, estado da fase, MFE, dock Portal, `plugin-ui` catalog e contracts. Matriz `EXISTING_EQUIVALENT` / `REUSE_DECISION` por item.
2. **Contrato e fatia mínima:** avaliar `presentation.v1`, loading JSON, rendering seguro, estados de erro/confirmação e provenance; separar descritivo do executável. Contrato antes do frontend.
3. **UI inicial quando autorizada:** recepção, composer reutilizado, timeline, loading honesto e dock; acessibilidade/dark/light, testes e review independente.
4. **Evoluções distintas:** activity events em tempo real; histórico persistente; fila per-conversation; Work durable; ditado; rich blocks; Live/visual. Cada uma exige owner/fase/capability/contrato e testes separados. Esta lista não impõe ordem sobre `16`.
5. **Review:** `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE` com SHA, tests, evidência de generalização/safety/task outcome, residual search e ledger.

## Veredito

**`ACCEPT_WITH_RESIDUAL` somente para coerência e direção documental de UX após reparo de Markdown.** Sem aceite de fase, runtime ou readiness. **`TEST_NOT_RUN`** para frontend e integração. As dependências UX-R02–R14 permanecem abertas ou condicionadas ao contrato; não resolver por suposição. Em evidência contrária: `STOP → EXECUTION_DRIFT / ARCHITECTURE_DECISION_REQUIRED`, nunca redesenhar silenciosamente.
