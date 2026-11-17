# My Requests — Plano de transição para catálogo JSON de apresentação

**Estado:** PLANNED — execução sujeita a inventário, testes e gates.  
**Owner:** My Requests (UI e experiência); requests-api continua owner de tipos operacionais, políticas, formulários genéricos e workflows; Engineering API continua owner de PRC.  
**Origem:** decisão do PO de retirar a dependência de migrations para alterar títulos e descrições dos cards; CRUD administrativo fica para fase posterior.  
**Escopo:** copy e ordenação visual dos tipos no My Requests. Não altera owner, autorização ou source of truth de solicitações.

## 1. Motivação e evidência (PROVEN)

A página `plugins/my-requests/src/pages/NewRequestPage.tsx` busca `listRequestTypes()` do requests-api e renderiza `type.name` e `type.description` diretamente. A mesma resposta atualmente orienta a escolha do tipo e a navegação. `AdminTypesPage.tsx` lista tipos em modo somente leitura. O requests-api expõe `GET /v1/request-types` e `GET /v1/request-types/{code}`, mas não foram encontradas rotas de mutação de catálogo nessa interface. As migrations V006 e V007 inicializaram nomes e descrições técnicas em `my_requests.request_types`. `requestTypeLabel()` contém fallback antigo; `MinePage` e `WorkQueuePage` também consomem os tipos da API.

O tipo `raw-material-creation` aciona `PrcRequestPage` e Engineering API; `invoice-issuance` aciona o wizard de notas fiscais. Os códigos técnicos NÃO serão renomeados. PRC e nota fiscal pertencem a domínios distintos.

## 2. Decisão de escopo

**TARGET:** um JSON versionado no repositório do MFE controla exclusivamente os textos visíveis, ícones somente se o contrato visual existente permitir, ordem e eventualmente ajuda curta dos tipos conhecidos. Ele substitui `type.name/description` da API como fonte da *apresentação* dos cards, sem substituir o catálogo operacional.

**Não autorizado:** usar JSON público para conceder permissões, declarar um tipo operacional ativo, criar workflow, alterar `permission_prefix`, `presentation_mode`, `form_schema`, `branch_scope`, modificar requests-api/Engineering API, inserir linhas no banco, ou suprimir backend AuthZ. A existência de item JSON não torna um novo tipo funcional. Mudança de owner/SoT ou criação de novos tipos funcionais sem backend requer `ARCHITECTURE_DECISION_REQUIRED` e retorno à Coordination.

O frontend pode continuar consumindo GET de tipos para disponibilidade e resolução do formulário. A *apresentação* deve deixar de depender de `name/description` da API. Não confundir isso com desligar os endpoints operacionais: caso o PO deseje eliminar também esse GET, inventariar contrato alternativo aprovado que assegure disponibilidade e autorização; sem contrato aprovado, fail closed.

## 3. Catálogo proposto

Arquivo candidato: `plugins/my-requests/src/content/requestTypeCatalog.json` (confirmar caminho e convenção no inventário). Exemplo ilustrativo:

```json
{
  "version": 1,
  "types": [
    {
      "code": "raw-material-creation",
      "title": "Criação e alteração de matéria-prima",
      "description": "Solicite o cadastro de uma nova matéria-prima ou a atualização dos dados de uma já existente.",
      "order": 10
    },
    {
      "code": "invoice-issuance",
      "title": "Emissão de notas fiscais",
      "description": "Solicite a emissão de uma nota fiscal e acompanhe o andamento do pedido.",
      "order": 20
    }
  ]
}
```

`version` = versão de schema do JSON, não versão do domínio. Chaves imutáveis; JSON é conteúdo de apresentação e não contém URLs, permissões, handlers, claims, schemas de formulário, SQL ou configurações operacionais. Validar schema em build/test: IDs únicos, textos não vazios, ordem estável e referências a tipos suportados. Evitar `dangerouslySetInnerHTML`/HTML dinâmico.

## 4. Regra de composição

1. Obter tipos operacionais autorizados de fonte oficial (GET existente) onde exigido para disponibilidade/formulário.
2. Cruzar por `code` estável: apenas tipos existentes, ativos e elegíveis nos contratos oficiais podem aparecer para criação. Permissões continuam com `canCreateRequestType` e *sempre* revalidadas pelo backend.
3. Apresentar `title`, `description` e `order` do JSON quando houver entrada. Política para tipo API sem copy JSON: definir e testar fallback seguro (por exemplo, texto neutro de apresentação ou legado), nunca ocultar inadvertidamente um tipo autorizado sem regra explícita.
4. Entrada JSON sem tipo operacional correspondente: não criar card clicável; diagnosticar em teste/telemetria de catálogo. Sem endpoints novos.
5. Deep links, formulários PRC/NF, rotas e permissões continuam usando `code` real e DTO operacional. Não substituir `type.name` em payloads de API sem necessidade.
6. Revisar todos os usos de apresentação: `NewRequestPage`, `AdminTypesPage`, `presentationLabels.ts`, `MinePage`, `WorkQueuePage`, detalhes, filtros, breadcrumbs e toasts. Aplicar mudança de copy consistente onde apropriado, sem reescrever dados históricos e sem quebrar listagens.
7. Se o GET falhar, não inferir autorização com base apenas no JSON. Exibir indisponibilidade contextual, sem exposição indevida de formulários.

## 5. Fases de implementação

**P0 — inventário:** confirmar HEAD/git status; mapear usos de `type.name/description`, requests-api GET, navegação PRC/NF, fallback e testes. Documentar contrato exato e RQ/AC.

**P1 — JSON + reader tipado:** adicionar JSON, validação e função pura de apresentação por `code` com fallback explícito, snapshot/testes para os dois cards.

**P2 — conectar UI:** usar JSON em cards da tela Nova solicitação, no texto de ajuda da página e nos lugares de apresentação apropriados; preservar filtragem por permissão/atividade operacionais. Atualizar fallback antigo. Administração pode mostrar copy JSON como leitura, claramente rotulada; não simular edição.

**P3 — provas:** testes JSON válido/inválido, IDs duplicados, item JSON inexistente na API, tipo operacional sem JSON, sem permissão, desativado, deep link, duas jornadas PRC/NF, listas, legacy, light/dark/responsive. Testar 401/403 e não usar cache estático para AuthZ. Construir MFE.

**P4 — HML e revisão PO:** deploy HML somente, SHA/digest, rollback, browser/screenshots, cards com copy aprovada, fluxo autorizado de cada tipo e negativa de permissão. Reportar PASS/INCONCLUSIVE honestamente.

**P5 — PRD:** nova autorização explícita após aceite HML; deploy do MFE mínimo, sem migrations ou API changes, smoke e rollback.

## 6. Critérios de aceite (AC)

- AC-01: card PRC mostra "Criação e alteração de matéria-prima" e descrição aprovada, abrindo o fluxo oficial de criação/alteração.
- AC-02: card NF mostra "Emissão de notas fiscais" e descrição aprovada, abrindo wizard existente.
- AC-03: copy vem do JSON, não do texto técnico `name/description` retornado pelo requests-api.
- AC-04: códigos `raw-material-creation` / `invoice-issuance`, permissões, status `active`, forms, workflows e AuthZ unchanged; JSON não concede acesso.
- AC-05: não criar migrations, CRUD, rotas nem um novo owner de tipos operacionais.
- AC-06: fallback/ausência/duplicidade e deep link cobertos por testes; nenhuma regressão das listas.
- AC-07: HML visual e funcional documentada; PRD não autorizado por esta fase.

## 7. Próxima evolução — CRUD governado (PLANNED, fora do escopo)

Quando o owner aprovar, implementar API de gestão do catálogo com AuthZ backend, validação, auditoria, versionamento, draft/publish e fluxo de revisão. Nesse momento, migrar *a fonte de apresentação* do JSON para o contrato administrativo oficial, mantendo compatibilidade de `code`. Não afirmar que um CRUD de textos é suficiente para criar tipos operacionais: publicar um novo tipo requer owner de domínio, formulário, permissão e workflow governados. A reconexão é uma fase futura explícita, não uma reversão implícita.

## 8. Riscos e rollback

Risco principal: confundir JSON de UI com source of truth de autorização/tipo. Mitigação: merge pelo código com fonte operacional + validação backend. Risco secundário: copy divergente em filtros, listagens e deep links. Mitigação: leitor de copy centralizado e matriz de uso. Rollback: restaurar bundle anterior do My Requests e conteúdo versionado, sem alteração de banco.

## 9. Execução e evidências

Task proposta: `MY-REQUESTS-JSON-PRESENTATION-CATALOG-TRANSITION-01`. Executor deve produzir BASE_HEAD, IMPLEMENTATION_SHA, FINAL_MAIN_SHA, diff, testes, HML digest, screenshot, riscos, dados de disponibilidade e prova de ausência de alterações em backend/migrations/RBAC. Estado inicial: PLANNED / TEST_NOT_RUN.
