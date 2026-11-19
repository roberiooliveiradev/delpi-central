# Prompt executável — PRC GLPI #1621 / S1 — valores iniciais no formulário compartilhado

> **Status:** EXECUTED / IMPLEMENTED_TESTS_GREEN (19/11/2026) / INDEPENDENT_VERIFICATION_REGISTERED — ver ledger no plano GLPI #1621 §4  
> **Data:** 2026-11-19  
> **TASK_ID:** ENG-PRC-GLPI-1621-S1-FRONTEND-DEFAULTS-01  
> **Tipo:** CODE + TEST (executor: Devin ou Cursor)  
> **Owner:** Portal Engenharia; consumer adicional: My Requests; owner backend não alterado: Engineering API.  
> **Fonte/decisão:** [Plano GLPI #1621](./PRC-GLPI-1621-UNIFIED-REQUEST-IMPROVEMENTS-IMPLEMENTATION-PLAN-2026-11-19.md), seção S1 e adendo de decisão PO em 19/11.  
> **IMPORTANTE:** O texto abaixo é um prompt de execução futura, não evidência de implementação.

---

## PROMPT PARA DEVIN / CURSOR — COPIAR NA ÍNTEGRA

### Missão e resultado de usuário

**TASK_ID:** `ENG-PRC-GLPI-1621-S1-FRONTEND-DEFAULTS-01`  
**DELIVERABLE_TYPE:** `CODE + TEST`  
**USER_OUTCOME:** Nos dois portais, ao abrir **Nova matéria-prima / CREATE**, o formulário PRC compartilhado já apresenta Armazém padrão = `01` e Conta contábil = `11401002`, editáveis. Nenhum fluxo existente é modificado.  
**CURRENT_RUNTIME_GAP:** `PrcRequestForm` inicia `values={}` quando `editCase` está ausente; os dois campos aparecem sem valor inicial.  
**NEXT_CODE_DIFF:** Menor alteração do estado inicial/transições do formulário compartilhado e testes de comportamento/paridade.  
**MODE:** `FRONTEND_ONLY / NO_ENGINEERING_API_DIFF / NO_NEW_ENDPOINT / NO_MIGRATION / NO_ERP_WRITE`.

O Product Owner ratificou a estratégia: **implementação exclusivamente frontend**, sem levar defaults para a Engineering API. Valores a usar **somente em novo CREATE de matéria-prima**: `defaultWarehouse: "01"` e `accountingAccount: "11401002"`, baseados nos defaults comprovados no aplicativo legado (inventário, seção 9). São sugestões iniciais editáveis; **não representam regra autorizativa nem prova de cadastro ERP**. Não incluir outros defaults (`productKind`, `thirdPartyProduct`) por extrapolação.

### 0. Reancoragem obrigatória

Antes de qualquer diff, no checkout existente do repositório `roberiooliveiradev/delpi-central`:

1. Confirmar `git rev-parse HEAD`, `git branch --show-current`, `git status --short`, `git worktree list` e HEAD remoto; inspecionar concorrência. Não criar, trocar ou excluir branch/worktree, não limpar/stash/reset work de terceiros e não usar force push. Se branch inesperada, registrar bloqueio e solicitar decisão.
2. Ler `AGENTS.md`, `.cursor/rules/plan-execution.mdc`, `test-and-commit.mdc`, `platform-frontend-mfe-experience.mdc`, `plugins-reusable-components.mdc`, `feature-help-sync.mdc`, `agent-session-scope.mdc`, `evidence-driven-execution.mdc` e regras relevantes de verificação. O GitHub consultado no planejamento estava no SHA `4886d0decf6635dcf0e45cd586089c77ca5c838a`; **não assumir que continua atual**.
3. Ler o plano `PRC-GLPI-1621-UNIFIED-REQUEST-IMPROVEMENTS-IMPLEMENTATION-PLAN-2026-11-19.md`, `README.md` e `ROADMAP.md` da pasta `docs/12-roadmap-e-evolucao/engineering/`; consultar o contrato PRC vigente e inventário legado somente para confirmar valores e boundaries.
4. Conferir no HEAD os arquivos e consumidores: 
   - `plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx` (implementação canônica);
   - `plugins/plugin-ui/src/utils/prcProductRegistration.ts` (`buildCreateIntakeBody`, validar e reutilizar sem mudança de contrato);
   - `plugins/engineering/src/features/product-registration/pages/PrcCreatePage.tsx` e `../prcIntakePayload.ts` (fonte real `portal-engineering`);
   - `plugins/my-requests/src/features/product-registration/PrcRequestPage.tsx`;
   - `plugins/plugin-ui/src/components/prc/PrcRequestForm.descriptionRequired.test.tsx`;
   - `plugins/plugin-ui/src/components/prc/PrcRequestForm.editCase.test.tsx`;
   - `plugins/engineering/src/features/product-registration/pages/PrcCreatePage.unification.test.ts`.
5. Confirmar a política vigente do lease `agent-kit/scope/session_scope.py`; registrar **todos** os arquivos candidatos numa única operação, sem tocar lease de outra sessão. Não iniciar diff se houver conflito de paths.

**EXISTING_EQUIVALENT=YES** (formulário e API existentes); **REUSE_DECISION=EXTEND** o `PrcRequestForm`. Não criar novo hook/framework/store, serviço de defaults, contrato, API, contexto ou formulário paralelo.

### 1. Requisitos fechados

- **RQ-1621-S1-01:** Nova solicitação CREATE (sem `editCase`) inicializa `defaultWarehouse="01"` e `accountingAccount="11401002"`, ambos visíveis na ficha técnica e presentes no payload `requestedData` após envio válido.
- **RQ-1621-S1-02:** Ambos os campos seguem editáveis; alterações manuais, inclusive vazio/limpeza, não podem ser reescritas por efeitos assíncronos, refetch de `reference-data`, navegação entre etapas ou re-render.
- **RQ-1621-S1-03:** Nenhum default é inserido indevidamente no caminho UPDATE, em `editCase` CREATE/UPDATE, na correção de ficha, em dados oficiais obtidos por `fetchEditContext` ou no futuro fluxo de duplicação com draft próprio.
- **RQ-1621-S1-04:** O mesmo comportamento ocorre com `source="portal-engineering"` (`PRC_PORTAL_SOURCE` do wrapper de Engenharia) e `source="my-requests"`, sem duplicar o wizard; nenhuma mudança em contrato HTTP, Engineering API, api-delpi, requests-api, banco, Core/RBAC ou TOTVS.

### 2. Critérios de aceite obrigatórios (incluir integralmente no pedido ao verificador)

- **AC-1621-S1-01 (positivo):** Renderizar nova solicitação CREATE com as fontes reais `source="portal-engineering"` e `source="my-requests"`; avançar à ficha e confirmar inputs visíveis `defaultWarehouse=01`, `accountingAccount=11401002`.
- **AC-1621-S1-02 (payload):** Submissão CREATE válida por meio dos builders existentes preserva `requestedData.defaultWarehouse="01"` e `requestedData.accountingAccount="11401002"`; `source` mantém origem legítima; sem novos campos de API.
- **AC-1621-S1-03 (edição):** Trocar os dois valores por escolhas válidas e voltar/avançar preserva os dados digitados; caso o usuário zere um obrigatório, a validação vigente bloqueia o envio e **não** repõe o default automaticamente.
- **AC-1621-S1-04 (UPDATE):** Escolher UPDATE e consultar o produto oficial não apresenta/enviará defaults do CREATE como alterações, mesmo se a consulta for lenta; os valores oficiais obtidos são preservados, inclusive string vazia real quando aplicável.
- **AC-1621-S1-05 (editCase):** Caso CREATE/UPDATE em edição inicia com dados do `editCase.draft`, inclusive valores vazios, **sem** substituir pelo default. Editar usa `saveDraft`, não chama novo intake.
- **AC-1621-S1-06 (assíncrono):** Fetch tardio de `reference-data`, carregamento de catálogos, re-render e navegação não sobrescrevem valores manualmente alterados; alternar CREATE/UPDATE não injeta defaults em UPDATE nem perde dados oficiais.
- **AC-1621-S1-07 (paridade):** Suites do `plugin-ui`, unificação e os builds/testes aplicáveis de `plugins/engineering` e `plugins/my-requests` passam; fonte do formulário continua única e wrappers permanecem finos.
- **AC-1621-S1-08 (segurança/escopo):** Diff de produção permanece frontend only, sem arquivos de `engineering-api`, `api-delpi`, `requests-api`, Core, migrations, infra, RBAC, manifests ou contratos HTTP; sem regressão de autorização, fornecedores, anexos, CREATE/UPDATE e correção.
- **AC-1621-S1-09 (evidência):** Testes RED antes da mudança e GREEN depois, regressões no SHA exato, residual search, verificador independente (até três rodadas), resultado e limites relatados honestamente.

### 3. Implementação mínima

1. Escrever primeiro teste(s) de componente em `plugins/plugin-ui/src/components/prc/` que demonstrem o defeito atual, cobrindo fontes dos dois portais e os casos negativos. Apresentar evidência RED.
2. Implementar o menor diff correto **na inicialização e/ou transição do estado do `PrcRequestForm`**, reutilizando o mecanismo `values` e `setValues` existente. Usar as duas chaves oficiais do contrato, não aliases antigos.
3. Guardar o recorte **novo CREATE e ausência de `editCase`**. Ao selecionar UPDATE, trabalhar com baseline oficial e impedir valor inicial de CREATE de aparecer como alteração proposta. Ao retornar a CREATE, aplicar política coerente com a edição corrente sem sobrepor entrada manual. Não depender de `setTimeout`, race condition, efeito que preenche campos tardiamente sem guardas, ou chamadas novas à API.
4. Garantir que o `buildCreateIntakeBody` use naturalmente os valores do estado canônico, com os testes; não alterar builders/DTOs só para inserir defaults no payload ocultamente.
5. Não criar CSS novo, modal, botão ou campo, nem alterar o layout para adicionar defaults. Nenhuma regra de autorização se desloca para o cliente.
6. Os wrappers `PrcCreatePage` e `PrcRequestPage` **não devem receber cópia local da regra**. Só alterá-los se um defeito concreto de integração, demonstrado por teste, exigir ajuste mínimo; se isso ocorrer, registrar justificativa e manter o owner da regra no kit.
7. Não implementar S2 (duplicação) ou S3 (cancelamento), nem "corrigir" gaps de outros fluxos como parte deste escopo.

### 4. Testes, QA e escopo permitido

**Arquivos de produção autorizados:** preferencialmente apenas `plugins/plugin-ui/src/components/prc/PrcRequestForm.tsx`; eventualmente helper puramente local do mesmo pacote **somente se a necessidade for demonstrada**.  
**Testes autorizados:** arquivos `*.test.tsx` e `*.test.ts` em `plugins/plugin-ui/src/components/prc/` e testes de composição/regressão diretamente relevantes em `plugins/engineering` e `plugins/my-requests`, preservando as suítes existentes.  
**Documentação autorizada:** atualizar apenas plano GLPI #1621 e ledger relevante para registrar o outcome real, quando entregue; não marcar PASS antes dos testes.  
**Não modificar:** API, domínio, armazenamento, schemas, migrations, permissions, gateways, infra, Protheus, recursos de outro fluxo.

Executar, quando disponíveis no checkout, os scripts efetivamente definidos em `package.json` e CI:
- `plugins/plugin-ui`: Vitest focado nas specs do `PrcRequestForm`, depois suite pertinente e `npm run build`.
- `plugins/engineering`: teste de `PrcCreatePage.unification.test.ts`, suíte aplicável e build.
- `plugins/my-requests`: suites de PRC aplicáveis e build.
- Gates de arquitetura/guardrails de `.cursor/rules/test-and-commit.mdc` quando materiais; auditoria documental se docs foram alterados.
- Em DEV/HML, quando disponível autorização e ambiente, conferir CREATE nos dois portais (desktop/mobile, claro/escuro, teclado), observando campos e reenvio. Se não executável, `TEST_NOT_RUN`, jamais `PASS` por inferência.

Testes não devem editar dados reais do ERP ou submeter novas solicitações produtivas sem autorização explícita e controles de isolamento. Não fabricar capturas de tela, respostas HTTP ou resultados de verificação.

### 5. Governança de entrega

Antes de qualquer commit, aplicar o ciclo delpi-verifier e reconciliar o diff. Verificar `git diff --check`, paths staged exatos, status da sessão de lease, HEAD remoto e mudanças concorrentes. Branch padrão `main`; sem branch/worktree criada ou trocada automaticamente. Respeitar a política atual de commit/push/deploy de `AGENTS.md`, sem interpretar aprovação deste prompt como autorização irrestrita para produção. **Se o protocolo exigir deploy automático após push e não houver gate/autorização operacional compatível, interromper antes de publicar e relatar a decisão necessária; não pular silenciosamente a regra nem executar deploy por inferência.**

O `EXECUTION REPORT` deve conter `TASK_ID`, `BASE_HEAD`, `EVALUATED_SHA`, `VERIFIED_SHA`, `FINAL_HEAD` se houver commit, `ORIGIN_MAIN`, branch/status, lease, `FILES_CHANGED`, `DIFF_SUMMARY`, `RQ/AC` individualizados, RED/GREEN, builds/CI, verificações negativas, `RUNTIME_CHANGED`, `USER_OUTCOME_PROVEN`, `IMPLEMENTATION_STATUS`, `INDEPENDENT_VERIFICATION`, `EXECUTION_DRIFT`, pendências, e `NEXT_BOUNDED_STEP`. Separar `PROVEN` de `TO_INVENTORY` e `TEST_NOT_RUN` e anexar a tabela de rodadas e o parecer sem edição. **Nenhum autoaceite.**

VERIFICAÇÃO: antes do EXECUTION REPORT e do commit/push/deploy, siga o ciclo da seção 'Verificação (delpi-verifier)' do AGENTS.md (verify.py, até 3 rodadas), com o objetivo contendo exatamente estes RQ/AC. Anexe a tabela de rodadas e o relatório final sem edição.
