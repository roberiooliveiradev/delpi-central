# Portal Engenharia MFE — Plano incremental de refinamentos pós-redesign

> **Status:** `PO_REFINEMENT_APPROVED / IMPLEMENTATION_PENDING / OPEN_FOR_MORE_FEEDBACK` · **Registrado:** 2026-11-07.
>
> **Origem:** inspeção visual DEV/localhost fornecida pelo Product Owner após o redesign PRC e análise de código atual. **Deploy de produção continua SUSPENSO** até aceite visual e gates funcionais.
>
> **Documentos-base:** [wireframes](./MFE-PRODUCT-REGISTRATION-UX-WIREFRAMES.md), [plano Devin UX0–UX5](./MFE-PRODUCT-REGISTRATION-DEVIN-IMPLEMENTATION-PLAN.md), [matriz plugin-ui](./MFE-PRODUCT-REGISTRATION-COMPONENTS-AND-ACCEPTANCE.md), [contrato técnico PRC](./PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md).
>
> **Política:** esta lista é **incremental**. Não iniciar implementação de todos os itens nem encerrar o refinamento antes que o PO conclua suas observações. Cada nova decisão deve ganhar ID, evidência, contrato, UX/AC e status, sem perder precedência.

## 0. Estado visual observado

O PO reconhece melhoria substancial do frontend pós-refatoração. As capturas DEV mostram:

- Central de solicitações agora possui breadcrumb, hero, filtros, DataTableSection e badges.
- Detalhe utiliza hero, progress, cards e abas; ficha técnica, verificação, histórico e revisões têm composição dedicada.
- Nova solicitação possui wizard de identificação, ficha técnica e revisão; opção de criação ou alteração.
- **Problema confirmado:** em `Nova solicitação → Alterar produto existente`, o usuário deve preencher manualmente **Revisão-base**; ao informar apenas código oficial, vê erro `Informe a revisão-base vigente do produto (número ≥ 1)`.
- Este campo é detalhe interno do controle técnico de concorrência, não informação que deve ser exigida de usuário de negócio.

A evidência fornecida é **visual**; não supor que outros fluxos estejam aceitos ou que HML esteja concluída.

## PRC-REF-001 — Revisão-base sempre automática em alteração de produto

**Decisão PO (aprovada):** ao abrir solicitação de **alteração**, o usuário informa/seleciona o **produto** e descreve o que deseja modificar. O usuário **não precisa saber, localizar, digitar nem selecionar** a revisão-base. O sistema deve resolver de modo governado a **última revisão técnica vigente** e garantir que a solicitação seja baseada nela. Não se trata de escolher a última revisão do TOTVS nem inventar revisão `1`.

**UI TARGET:**

```text
Nova solicitação                                     Etapa 1 / 3
[ Nova matéria-prima ] [ Alterar produto existente ✓ ]

Produto a alterar *
[Código oficial TOTVS ou lookup pelo BFF ..................] [Localizar]
  → Se identificado: [Descrição oficial disponível] [Informações úteis]
  → Se não encontrado: mensagem clara / correção de código

A revisão técnica de referência será identificada automaticamente.
(NENHUM input, select, número ou campo obrigatório de revisão-base)

                                              [Cancelar] [Avançar]
```

**UX:** remover `Revisão-base` do formulário, do validation summary e do resumo final do wizard para o usuário operacional. Não trocar input por número fixo, campo oculto com valor adivinhado ou default `1`. Na ficha de solicitação concluída, a revisão-base pode permanecer nos dados de auditoria e histórico técnico quando legitimamente disponível, sem virar escolha do solicitante.

### 1. Código existente — inventário verificado

- `plugins/engineering/src/features/product-registration/pages/PrcCreatePage.tsx`: mantém `baseRevision` em `useState("")`, valida `parseInt(baseRevision,10) >= 1`, renderiza campo `Revisão-base` e serializa `baseRevision` no payload e no resumo do wizard.
- `plugins/engineering/src/features/product-registration/api/productRegistrationApi.ts`: `PrcIntakeBody.baseRevision?: number | null` e `fetchPrcRecord(recordId)` tipados; ainda não há comprovação de endpoint de lookup de revisão vigente **por código oficial** disponível ao MFE.
- `engineering-api/engineering_app/interface/http/routes/product_registration_routes.py`: `IntakeBody.baseRevision: int | None`, recebe `POST /v1/product-registration/intake/requests`; a rota repassa o atributo à aplicação.
- `engineering-api/engineering_app/application/use_cases/product_registration/service.py`: ao receber `update`, busca record técnico por código oficial via repositório, obtém `current_revision_number`; **se record existe e `baseRevision` não é informado ou difere, hoje retorna `PrcConcurrencyError("stale_revision")`**; busca snapshot da revisão corrente para composição. Sem record técnico, o branch atual admite outra situação; **não inventar revisão no MFE**.
- Portanto, esconder input na UI **não é suficiente**: se a Engenharia tem record corrente, o backend atual exigirá valor manual e rejeitará a tentativa. O contrato servidor precisa de mudança explícita pelo owner Engineering API ou introdução de lookup oficial que não tire autoridade do backend.

### 2. Contrato-alvo preferido (backend-first, sem exposição de revision internals no wizard)

**Preferir a menor mudança no caso de uso de intake do owner Engineering API**:

1. Para `requestType="update"` e `officialProductCode` autenticado e válido, buscar record técnico vigente de Engenharia pelo repositório próprio.
2. Se houver record, resolver `baseRevision = current_revision_number` **no backend**, obter snapshot correspondente e associar de maneira atômica/consistente a base e os deltas da solicitação. Usar mecanismo de versão/transaction/lock/retry canônico para evitar TOCTOU.
3. O contrato público de intake não deve exigir que o humano forneça `baseRevision`. **Se for aceito opcional para compatibilidade de consumidores existentes**, não permitir fixar revisão arbitrária antiga; conflito ou divergência deve retornar resposta de contrato explícita (e manter clients históricos compatíveis onde possível). A decisão do servidor sobre a revisão corrente permanece mandatória.
4. Se **não existir record técnico publicado na Engenharia**, inventariar regra de negócio já vigente: o sistema pode ou não admitir solicitação de alteração para produto oficial ainda sem snapshot técnico. Não gerar revisão fictícia nem declarar revisão do TOTVS como revisão Engenharia. Documentar estado `NO_TECHNICAL_BASE`/regra canônica e ação correta sem inventar novo erro se já existir um código apropriado. Escalar questão de owner se exigir decisão funcional nova.
5. No momento de salvar, aplicar CAS/idempotência e, quando relevante, garantir que a base ainda seja a corrente; uma revisão avançada concorrente produz `409 stale_revision` e exige atualização da solicitação, jamais rebase silencioso de alterações já aprovadas.
6. Não alterar revisões históricas publicadas, `technical_snapshot`, audit trail e provenance. O source of truth de revisão técnica permanece no repository/Domain API de Engenharia; TOTVS continua SoT do produto **oficial**.
7. Não requisitar revisão-base ao frontend; o MFE encaminha somente os dados de negócio e deltas selecionados. Caso o backend precise de token opaco de concorrência produzido por endpoint read, isso deve ser retornado e validado via contrato apropriado, **nunca digitado pelo usuário**, e não autoriza bypass de verificação live.

**Justificativa arquitetural:** a decisão modifica parte do contrato/caso de uso de intake sob owner Engineering API; **não é somente CSS/UI**. Mudança deve ser testada em REST, domínio, PostgreSQL (quando disponível) e paridade EVA/consumers; aplicar contract-first e manter compatibilidade. Não criar novo bounded context, query TOTVS direta nem dependência de internals.

### 3. Arquivos-alvo e componentes

| Local | Trabalho necessário |
|---|---|
| `PrcCreatePage.tsx` | Remover state, render, validação e resumo manual `baseRevision`; usar texto neutro de base automática; UX loading/erro ao identificar produto se lookup oficial já existir |
| `productRegistrationApi.ts` | Atualizar tipo `PrcIntakeBody` e serialização do fluxo update sem revisão humana; respeitar contract server final |
| `engineering-api/.../product_registration/service.py` | Resolver revisão corrente no backend, CAS/idempotência/estado sem record e conflito de versão |
| `engineering-api/.../product_registration_routes.py` | Atualizar contrato doc/schema, se necessário, mantendo compatibilidade |
| Testes `productRegistration.test.ts` e casos frontend novos | Assert não exibir campo, não exigir revision, envio update sem número, 409 explicável e tratamento sem record |
| `engineering-api/tests/test_product_registration.py` / paridade EVA | Asserts da revisão corrente, concorrência e clientes existentes |
| Documentação PRC e manual `HelpPage.tsx` | Atualizar orientação para `revisão controlada pelo sistema`, não pedir ao solicitante que informe versão |

**Kit-first:** usar `EngineeringPageHero`, `EngineeringSectionCard`, `EngineeringFieldLabel`, `EngineeringActionButton`, `EngineeringStateBanner`, campos oficiais de `engineeringUi.ts`; não criar componente novo só para esconder revisão.

### 4. Critérios de aceite PRC-REF-001

- [ ] Ao escolher **Alterar produto existente**, não existe campo `Revisão-base` nem validação de número ≥1 nas três etapas do wizard.
- [ ] Usuário com `engineering.access` consegue iniciar alteração informando produto oficial e deltas legítimos, sem conhecer revisão técnica.
- [ ] A Engineering API resolve a **última revisão técnica corrente** da Engenharia quando existente e a associa corretamente ao caso.
- [ ] O sistema não confunde revisão técnica Engenharia com cadastro/revisão TOTVS.
- [ ] Se a revisão corrente mudar durante o intake, 409/CAS com recuperação segura; nenhum rebase ou publicação implícita.
- [ ] Se não houver record técnico, a política existente é inventariada e testada; nada de default `1`.
- [ ] Atualização seletiva preservada, com motivos, PN opcional, supplier code+store e verificação oficial posterior.
- [ ] REST, EVA, testes e usuários legados não sofrem regressão de contrato; IDs de revisão e audit trail permanecem governados.
- [ ] Typecheck/build/Vitest e testes Python/PG pertinentes; browser real para demonstrar não existência do input nas três etapas.
- [ ] Erro de backend em mudança concorrente se traduz em orientação funcional ao usuário (não exibir exceção interna).

**Status:** `PO_APPROVED / TO_IMPLEMENT`; não declarar corrigido apenas por este documento.

## PRC-REF-002 e seguintes — espaço reservado a próximas observações do PO

**Status:** `AWAITING_USER_FEEDBACK`. Anexar cada novo refinamento com: `ID / imagem e sintoma / decisão PO / análise do contrato / UX antes-depois / componentes do kit / arquivos / AC / owner / status`. Não inventar desejos ou antecipar a lista.

## Sequenciamento

1. Coletar demais apontamentos do Product Owner no mesmo plano sem perder o item PRC-REF-001.
2. Revisar owner/contrato e dependencies entre refinamentos; aprovar qualquer alteração de authority em Coordination.
3. Gerar implementação Devin em lote coerente depois de fechar feedback, mantendo deploy produtivo suspenso.
4. QA real DEV/HML por screenshots e tarefas executadas; aceite do PO em separado.

**Status de projeto:** `VISUAL_REFINEMENT_IN_PROGRESS / PRC-REF-001_APPROVED / PRODUCTION_DEPLOY_SUSPENDED`.
