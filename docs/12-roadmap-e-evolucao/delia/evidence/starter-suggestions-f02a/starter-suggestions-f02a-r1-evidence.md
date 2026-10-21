# F02-A-R1 â€” Starter suggestions visÃ­veis em produÃ§Ã£o â€” evidÃªncia de execuÃ§Ã£o

- **Data:** 2026-10-21
- **Task:** DELIA-UX-F02A-R1-PRODUCTION-DEFAULT-STARTERS-01
- **Spec:** 93 Â§16 (decisÃ£o de produto â€” quatro perguntas por padrÃ£o)
- **Base de reancoragem:** `9c69742a1b51700f8fe03b1b519aecdb12d8d706` (worktree rebased sobre origin/main apÃ³s `2de2b96210` e `9c69742a1b`)
- **SHA testado (impl):** `41fbb9657d70af45bea036627da26c5b26cd7309`
- **EvidÃªncia anterior:** starter-suggestions-f02a-evidence.md (F02-A, gate QA)

## 1. CorreÃ§Ã£o aplicada (menor diff)

`resolveStarterSuggestions()` deixou de depender de `demoScenario` e retorna a lista congelada `DELIA_STARTER_SUGGESTIONS` para todo usuÃ¡rio admitido Ã  aplicaÃ§Ã£o. O seam permanece como ponto Ãºnico para a futura projeÃ§Ã£o de elegibilidade por sessÃ£o (spec Â§16). Arquivos tocados:

- `plugins/delia/src/suggestions/starterSuggestions.ts` â€” resolver sem parÃ¢metro; comentÃ¡rios atualizados (Â§16).
- `plugins/delia/src/App.tsx` â€” chamada sem `demoScenario`; comentÃ¡rio atualizado. `demoScenario` segue usado apenas para os turns demo.
- `plugins/delia/src/suggestions/starterSuggestions.test.tsx` â€” testes reescritos para o comportamento padrÃ£o + ocultaÃ§Ã£o apÃ³s turn.

**NÃ£o tocado:** `demoMode.ts` (admissÃ£o `isDemoAllowed` + `?delia-demo=` intacta), plugin-ui (componente render-only sem mudanÃ§a), backend, Core/RBAC, Keycloak, MCPs, VD-F05, qualquer contrato de sugestÃµes.

## 2. Resultados de teste (medidos)

| VerificaÃ§Ã£o | Resultado |
|---|---|
| Vitest plugins/delia | **276/276** (22 arquivos; inclui 8 testes starter-suggestions e suÃ­te demo-mode completa â€” outros gates preservados) |
| Typecheck plugins/delia | PASS |
| Build plugins/delia | PASS |
| Browser QA local em bundle de produÃ§Ã£o (sem `VITE_DELIA_DEMO`, sem `?delia-demo`) | **40/40 PASS** |

## 3. Browser QA â€” produÃ§Ã£o-paridade (localhost, sem parÃ¢metros)

Contextos executados com a imagem `delia` reconstruÃ­da **sem** `VITE_DELIA_DEMO=1` (paridade com produÃ§Ã£o) e URL `/apps/delia` pura:

- `page:section` + `page:no-special-param` â€” seÃ§Ã£o visÃ­vel com URL limpa.
- `page:4-cards`, `page:2-columns` â€” 4 cards, grid 2 colunas em 1440px.
- `page:label`, `page:titles`, `page:tooltip` â€” rÃ³tulo "Explore algumas possibilidades", perguntas Â§16, HelpTooltip funcional.
- `page:draft-filled`, `page:focus-on-composer` â€” seleÃ§Ã£o preenche o rascunho ("O que Ã© SIPOC?") e foca o composer com caret no fim.
- `page:no-auto-submit` â€” zero POST `/interaction/turns` em todas as seleÃ§Ãµes (pÃ¡gina e Dock).
- `page:draft-preserved` + `page:note` â€” rascunho nÃ£o vazio preservado, nota `role=status` exibida.
- `page:keyboard-enter`, `page:focus-ring` â€” ativaÃ§Ã£o por Enter, outline 3px.
- `page:hidden-after-turn` â€” apÃ³s turn real enviado, seÃ§Ã£o sai junto com a recepÃ§Ã£o.
- `w420/w360/w320` â€” â‰¤2 cards, 1 coluna, sem overflow horizontal; descriÃ§Ãµes ocultas â‰¤400px.
- `short` (720Ã—400) â€” â‰¤1 card, composer visÃ­vel.
- `zoom200` â€” composer visÃ­vel, sem overflow.
- `dock` â€” â‰¤2 cards, descriÃ§Ãµes ocultas, draft preenchido, zero auto-submit.
- `page:vdf05-dictation-present` â€” controle de ditado VD-F05 presente no composer (smoke de regressÃ£o).

## 4. SeguranÃ§a/ownership (verificado no diff)

- Nenhuma permissÃ£o, capability, contrato, endpoint ou autorizaÃ§Ã£o criada.
- As quatro perguntas sÃ£o prompts editÃ¡veis de orientaÃ§Ã£o; a autorizaÃ§Ã£o efetiva permanece no backend quando o usuÃ¡rio envia a pergunta editada.
- Gates de demo das demais funcionalidades DÃ‰LIA preservados (suÃ­te demo-mode 100% verde).

## 5. Deployment (2026-10-21)

- Host `operador@192.168.1.237` `~/projetos/delpi-central` â€” `git pull --ff-only` para `4191b65649202d028979327a0eda9eee0c894390` (= `origin/main` no momento do deploy).
- Deploy canÃ´nico: `infra/scripts/up-prod-sequential.sh --cpu --build delia` â€” **somente** o MFE `delia` (plugin-ui inalterado nesta task; backend `delia-api` nÃ£o reconstruÃ­do).
- `delpi-delia` recriado; `delpi-plugin-ui`, `delpi-delia-api`, `delpi-gateway` intocados.
- **Bundle servido verificado** (`delpi-delia:/usr/share/nginx/html/assets/App-DD7hFFiM.js`, build 12:40):
  - os 4 fixture ids presentes (`data-formats`, `sipoc-concept`, `available-sources`, `operational-analysis`);
  - resolver compilado como `function Vn(){return Bn}` â€” retorno incondicional da lista (gate demo removido);
  - guard de ambiente demo compilado como `Un)!=="1"` (env ausente em produÃ§Ã£o â†’ demo-mode continua fechado); parse de `?delia-demo=` preservado;
  - nota de rascunho "Edite ou apague" presente.
- **QA de browser autenticado em produÃ§Ã£o: PENDENTE** â€” nÃ£o existe usuÃ¡rio de teste `e2e-delia` no Keycloak de produÃ§Ã£o (realm `delpi`) e a task proÃ­be modificar Keycloak. ValidaÃ§Ã£o depende de sessÃ£o real do usuÃ¡rio autorizado (mesmo precedente de VD-F05). CritÃ©rio de verificaÃ§Ã£o: abrir `https://minhadelpi.com.br/apps/delia` sem parÃ¢metros â†’ 4 cards visÃ­veis; clicar â†’ preenche o rascunho, foca o campo, nÃ£o envia; enviar a conversa â†’ cards somem com a recepÃ§Ã£o.

## 6. Incidentes de ambiente

- **Index do worktree corrompido por resÃ­duo de stash-pop** (sessÃ£o anterior): ~20k arquivos staged por normalizaÃ§Ã£o CRLF + 18 arquivos `UU` de conflito de stash em Ã¡reas nÃ£o relacionadas (controllership-finance, supplies, docs). Resolvido com `git reset` (indexâ†’HEAD, worktree intacto) e stage apenas dos 3 arquivos de escopo. Nenhum trabalho concorrente perdido ou commitado.
- **Arquivo de evidÃªncia commitado truncado e corrigido em follow-up:** a primeira tentativa de escrita via heredoc foi truncada pela expansÃ£o de backticks do shell externo; a versÃ£o truncada (35 linhas) foi commitada em `4191b65649`. Este arquivo substitui integralmente o conteÃºdo correto.
- Primeiro run do QA falhou apenas em `page:hidden-after-turn` por timeout de 2,5 s aguardando turn real do backend local (modo demo anterior respondia instantaneamente). Corrigido o script para aguardar detach atÃ© 45 s â†’ PASS no re-run.

## 7. Estado canÃ´nico

```text
F02A_R1_DEFAULT_STARTERS=EXECUTED
TESTED_SHA=41fbb9657d70af45bea036627da26c5b26cd7309
DEPLOYED_SHA=4191b65649202d028979327a0eda9eee0c894390
DEMO_GATE_REMOVED_FOR_DEFAULT_STARTERS=YES
OTHER_DEMO_GATES_PRESERVED=YES
BACKEND_TOUCHED=NO
PHASE_ADVANCE=NO
```