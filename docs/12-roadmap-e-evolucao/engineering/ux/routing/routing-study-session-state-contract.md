# EVA / Portal Engenharia — Routing Study V2 — Session State & Rules

**Estado:** `TARGET / CONTRACT_PROPOSAL / IMPLEMENTATION_NOT_PROVEN`  
**Data:** 2026-11-17.  
**Owner do estado de UX:** Portal Engenharia. **Owner da identidade:** Keycloak/Core. **Owner AuthZ:** Core + domínio. **Owner da fonte:** API-DELPI. **Owner dos cálculos:** domínio determinístico Engenharia/EVA. **Owner de publicação de roteiro:** Engenharia.  
**Objetivo:** preservar a edição de estudo após refresh e durante a sessão **da aba**, sem criar persistência oficial nem estender autoridade do frontend.

## 1. Persistência temporária escolhida

Usar `sessionStorage` para rascunho de estudo **não sensível**, por identidade autorizada + produto + filial/estágio + versão do esquema. É armazenamento **best-effort** da mesma aba/top-level browsing context; sobrevive ao refresh e normalmente à navegação interna, mas **não é promessa de persistência após encerramento da aba, restauração do navegador, dispositivo diferente, limpeza de dados ou restrições de storage**.

Não usar `localStorage`, banco oficial, memória do modelo, log ou backend para guardar o estudo sem nova decisão.

**Chave conceitual (não literal obrigatória):** `engineering:routing-study:v2:{principal-safe-key}:{product}:{branch}:{stage}`. A identidade deve ser uma chave não sensível e não reversível quando exigido, nunca JWT/email completo/segredo. Não usar `branch=all` para atribuir resultado a uma filial física; preservar a seleção explícita.

### 1.1 Salvar

- Debounce curto de alterações de formulário e postos; usar `visibilitychange` ou unmount onde disponível, com fallback de atualização imediata para ações críticas.
- Informar status `Salvo nesta aba`, `Salvando...`, `Não foi possível salvar`, somente quando confirmado pelo navegador; não exibir sucesso antecipado.
- Tratar quota excedida, `SecurityError`, storage indisponível e serialização inválida sem quebrar a tela; manter estado em memória e informar risco de perda.
- Permitir cálculo e edição mesmo sem storage, mas alertar honestamente que refresh poderá perder dados.
- Armazenar apenas dados necessários, com versão e timestamp; preferir IDs/chaves e parâmetros a payload oficial volumoso ou resultados completos de API.

### 1.2 Recuperar

Fluxo obrigatório:
1. Estabelecer identidade atual do Portal e checar autorização **live** antes de recuperar ou consultar recurso protegido.
2. Ler chave do contexto do produto/filial/estágio; validar JSON/schema, versão, limites, tipos, tempo de validade de sessão (se definido), tamanho e ownership. Não confiar no storage para AuthZ nem como código executável.
3. Mostrar `Rascunho recuperado nesta aba` quando aplicável; permitir revisão e limpeza.
4. Consultar novamente contexto/roteiro autorizado; comparar versão/hash/revisão/identidade de operações/filial/estágio, quando a fonte permitir. Se não existir revisão confiável, marcar `REVALIDATION_REQUIRED` e não afirmar estabilidade oficial.
5. Invalidar resultados anteriores quando parâmetros ou fonte divergirem; não reusar um `CALCULATED` antigo como atual.
6. Em mudanças de usuário, produto, filial e estágio: chave isolada e autorização renovada; não mostrar dados de estudo de outro usuário nem misturar dados.
7. Em rascunho inválido/antigo: recuperar apenas campos compatíveis quando seguro e avisar; caso contrário descartar com mensagem clara. Nada de falha silenciosa.

### 1.3 Limpar / iniciar novo estudo

Ação visível: `Limpar estudo`; abrir diálogo de confirmação:
- "Este comando descarta os preenchimentos, postos hipotéticos, ordenação, vínculos de operações e cenários salvos **nesta aba e para este contexto**. Não altera roteiro, BOM, ERP ou qualquer registro oficial."
- `Cancelar` mantém tudo; `Limpar estudo` confirma remoção de storage e reset do estado transitório.
- Após confirmação: limpar controles, postos hipotéticos, resultados/cenários e mensagens de erro; remover **somente** a chave do estudo atual; manter consulta oficial do roteiro e identidade autenticada; permitir novo estudo vazio.
- Estado de sucesso só após remover ou esvaziar a entrada; falha de storage deve ser comunicada e não pode afirmar remoção de bytes não confirmada.
- `Novo cenário` difere de `Limpar`: preserva estudo e cria um novo conjunto de parâmetros para comparação; respeitar limite existente.

## 2. Modelo de dados proposto

```ts
type RoutingStudyDraftV2 = {
  schemaVersion: 2;
  savedAt: string; // ISO 8601
  context: {
    productCode: string;
    branch: string; // seleção explícita, inclusive all quando aplicável
    stageProductCode: string;
    bomLevel: number;
    sourceRevision?: string | null; // apenas se a fonte fornecer
    sourceFingerprint?: string | null; // derivado de material de fonte autorizado
  };
  mode: "quick" | "configure_posts";
  inputs: {
    demand?: number | null;
    shiftMinutes?: number | null;
    breakMinutes?: number | null;
    batchSize?: number | null;
    numStations?: number | null; // apenas se explicitamente informado
  };
  proposedPosts: Array<{
    clientId: string; // ID local estável, sem confundir código oficial
    name: string;
    order: number; // sequência de apresentação/hipótese, NÃO roteiro oficial
    operationRefs: string[]; // referências das operações oficiais no contexto
    workCenterRefs: string[]; // CTs oficiais associados, hipótese de uso
    resourceRefs: string[];
    operators?: number | null;
    parallelPositions?: number | null;
    note?: string;
  }>;
  scenarios: Array<{
    clientId: string;
    label: string;
    inputs: RoutingStudyDraftV2["inputs"];
    proposedPostIds: string[];
    isHypothesis: true;
  }>;
};
```

**Schema ilustrativo sujeito a contrato aprovado**: conferir operações e chaves reais no BFF; jamais persistir resultado do modelo como se fosse oficial. Não incluir tokens, payload bruto de desenho, PII, permissões ou segredos. Regras de validação e limites numéricos alinhados ao backend antes de implementar.

## 3. Regra de domínio e de segurança

**CT ≠ posto físico necessariamente.** Mesmo um CT único pode atender diversas estações ou um posto pode executar operações de diversos CTs sob restrições. A quantidade de CTs da fonte **não preenche automaticamente** `numStations` real.

**Operações do roteiro:** leitura `OBSERVED`. **Inputs do usuário:** `PROVIDED`. **Resultados do motor:** `CALCULATED`. **Postos, sequência e alocação propostas:** `SIMULATION / DRAFT_LOCAL`. **Informação não confirmada:** `UNKNOWN`.

- O frontend pode organizar hipóteses de postos, mas não afirmar viabilidade de precedência, capacidade, recursos, operadores ou paralelismo.
- Não enviar campos avançados não aceitos pelo `POST /v1/products/{code}/line-balance`. O contrato atual não comprova avaliação de alocação por posto.
- Se `mode=configure_posts`, oferecer o cálculo rápido **separado e explicitamente rotulado** como cálculo **sem validação da distribuição manual**, ou bloquear ação de simulação avançada até haver capability aprovada; jamais mascarar a limitação.
- Novo motor/contrato para alocação explícita requer owner, consumers, input/output, erros, AuthZ live, limites, precedência, segurança, observabilidade, testes e `ARCHITECTURE_DECISION_REQUIRED` quando mudar boundary.
- Publicação e aprovação de processo são exclusivas da Engenharia; operação de limpar ou configurar não tem write oficial.

## 4. Cenários de organização (TARGET)

**Análise rápida:** demanda, turno, pausas, lote/numStations opcionais; calcula takt e indicadores suportados.  
**Configurar postos:** UI progressiva com cards para adicionar/remover/ordenar; multisseleção de **operações existentes** (não inserir operações livres), referência a CTs/recursos autorizados, operadores e posições paralelas propostos. Nome de posto é texto editável, mas código oficial/CT/recurso só por seleção do roteiro. Precedências, exclusividade de recurso, restrições de compartilhamento e viabilidade ficam `UNKNOWN` até contrato de validação.  
**Comparação:** cenários locais com parâmetros explícitos, sem persistência permanente, número máximo conforme contrato vigente, sem misturar operação entre estágios.

## 5. Especificação de UX de persistência

- Status compacto próximo ao título do estudo: `Rascunho nesta aba` e timestamp se salvo; `Recuperado` ao reabrir página; `Não salvo` em erro.
- Não dizer `Salvo na conta`, `Sincronizado` ou `Estudo oficial`.
- `Limpar estudo` aparece próximo às ações de estudo, com confirmação acessível e foco restaurado.
- Não pedir confirmação a cada alteração comum.
- Permitir abandonar a página e retornar na mesma aba sem perder edição quando o ambiente mantém sessionStorage.
- A seleção de filial/estágio define escopo da chave e da recuperação; mudança de contexto não pode impor dados da seleção anterior.
- A tecla Enter em inputs não deve executar mutação oficial; não persistir material sensível em traces, logs ou analytics.

## 6. Testes e aceite propostos

| AC | Cenário | Comprovação |
|---|---|---|
| ST-01 | editar → refresh | formulário, postos, ordem e seleção permanecem |
| ST-02 | mudar de seção/página e voltar na mesma aba | recuperar estudo do contexto autenticado |
| ST-03 | abrir outro produto/filial/estágio | não misturar rascunhos |
| ST-04 | principal troca / logout / acesso revogado | fail-closed, sem exibir conteúdo de outro usuário |
| ST-05 | corrigir parâmetro e recalcular | invalidar resultado antigo |
| ST-06 | roteiro/revisão alterado | exigir revisão de vínculos e cálculo; sem CALCULATED stale |
| ST-07 | storage indisponível/quota | edição continua, falha comunicada |
| ST-08 | Limpar → Cancelar | nenhum dado removido |
| ST-09 | Limpar → Confirmar | estado local removido; fonte oficial preservada |
| ST-10 | Novo cenário | preserva cenário anterior; diferencia A/B |
| ST-11 | múltiplas operações por posto | seleção válida + nenhuma operação inventada |
| ST-12 | ordenar posto | ordem local altera, roteiro oficial não |
| ST-13 | setup sem lote / parâmetros inválidos | contrato honesto e validação |
| ST-14 | saída para log/evento | sem secrets/PII/rota de escrita oficial |
| ST-15 | advanced ainda não suportado | UI não declara cálculo de viabilidade da configuração |

**Evidence:** E2E navegador real com SSO de teste e rede governada, reload + nova visita na mesma aba, dark/light e mobile. Cada resultado deve ser rotulado `PASS/FAIL/TEST_NOT_RUN/INCONCLUSIVE`.

## 7. Decisões pendentes

- `TARGET`: `sessionStorage` para rascunho, com retenção de sessão e chave por contexto. Confirmar requisitos corporativos de dados locais antes de implementar.
- `TO_INVENTORY`: fonte de revisão/hash do roteiro, identificadores estáveis de operação, caps/max-size de storage, recursos disponíveis, comportamento do Portal em múltiplas abas.
- `ARCHITECTURE_DECISION_REQUIRED` se implementação avançada exigir novo contrato, motor, owner ou boundary.
- `NO_DEPLOY_FROM_DOC`: documentação apenas, nenhuma mudança runtime/autorização de publicação.
