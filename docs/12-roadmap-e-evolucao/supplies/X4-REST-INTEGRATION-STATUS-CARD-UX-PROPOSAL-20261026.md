# X4 — Diagnóstico visual da integração REST de fornecedores (P0 UX / contrato proposto)

> **Data:** 2026-10-26 · **Estado:** `TARGET / PLANNED` · **Implementação:** `NOT_AUTHORIZED` · **Runtime do diagnóstico:** `TEST_NOT_RUN`.
> **Referências:** [X4.PROD-C1 handoff](./X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md), [X4.PROD-C1 cutover](./X4-PROD-C1-SUPPLIER-PRODUCTION-REST-CUTOVER.md), [Gestão cadastral](./FORNECEDORES-GESTAO-CADASTRAL-ROADMAP.md).

## 1. Evidência apresentada pelo PO e intenção

Capturas autenticadas de 26/10/2026 mostram:
- **Lista:** `/apps/supplies/suppliers` carrega a tabela SQL de fornecedores, com busca, filtros e ações `Novo fornecedor` / `Atualizar`.
- **Ficha:** `/apps/supplies/suppliers/002469/01` apresenta o erro genérico «O Portal Suprimentos está temporariamente indisponível» e botão `Tentar novamente`. **A captura não comprova que o serviço inteiro esteja indisponível.** O GET detalhado usa integração REST upstream; a lista funciona por SQL.
- Última evidência R4 **reportada**: `AMBIENTE=1` resolvendo REST produtiva `192.168.1.231:8061/restall`, flags CREATE/UPDATE=true, token upstream 401, consulta de fornecedores pendente de autenticação; sem POST/PUT real. Verificar HEAD/runtime no início de execução futura.
- Desejo do PO: um **indicador flutuante/discreto** para verificar a prontidão da REST por operação, **sem gravar no ERP**.

**Não confundir quatro conceitos:** listagem SQL E13, consulta REST E14, flags de create/update e persistência real via POST/PUT. Diagnóstico read-only não valida escrita.

## 2. Layout proposto — lista de Fornecedores

Posicionamento preferencial: **card compacto flutuante ancorado no canto inferior direito da área de conteúdo da página Fornecedores**, acima de controles persistentes existentes, com distância de segurança e sem encobrir linhas, filtros, ações, navegação, teclado ou controles de acessibilidade; em telas estreitas, trocar por painel inline próximo do cabeçalho em vez de overlay. Deve ser **visível apenas para usuário autorizado à gestão/diagnóstico**, não para todo usuário de leitura. A lista deve continuar utilizável mesmo com a REST indisponível.

### Wireframe desktop, estado compacto

```text
┌─ Fornecedores ───────────────────── [Novo fornecedor] [Atualizar] ─┐
│ Busca / filtros                                                    │
│ Cadastro de fornecedores  (SQL DELPI, independente da REST)       │
│  ... tabela ...                                                    │
│                          ┌──────────────────────────────────────┐ │
│                          │ ● Integração Protheus  [Verificar]  │ │
│                          │ REST: Autenticação pendente   [▾]   │ │
│                          └──────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### Expandido

```text
┌─ Integração REST de fornecedores ─────── [Verificar agora] [×] ┐
│ Ambiente: Produção                         Última verificação: — │
│ Configuração e proteção do destino ........ Prontas (reportado) │
│ Autenticação técnica ...................... HTTP 401            │
│ Consulta REST de fornecedores ............. Não verificada      │
│ Inclusão (POST) ........................... Habilitada*         │
│ Alteração (PUT) ........................... Habilitada*         │
│ *Gravação não comprovada: nenhum POST/PUT executado no teste.    │
│ A listagem desta página usa consulta SQL independente.          │
└──────────────────────────────────────────────────────────────────┘
```

Valores acima são **exemplos baseados no último relatório**, não diagnóstico ao vivo. Nunca exibir verde `Pronta para operar` se autenticação ou GET falhar.

## 3. Layout proposto — ficha individual

Em `/apps/supplies/suppliers/:code/:store`, manter o mesmo diagnóstico na mesma posição/forma, compartilhando componente e fonte de dados (sem estado paralelo). Enquanto o GET da ficha falha, **não substituir a mensagem de erro do conteúdo por um sucesso fictício do diagnóstico**:

```text
← Fornecedores / Ficha 002469/01
┌─ 002469/01 — Ficha do fornecedor ─────────────────────────────┐
└───────────────────────────────────────────────────────────────┘
⚠ Não foi possível consultar a ficha pela integração REST.
  [Tentar novamente]      (mensagem exata depende do contrato de erro)
             ┌─ Integração Protheus ────────────────────────────┐
             │ ⚠ Autenticação REST falhou (HTTP 401) [Verificar]│
             │ [Detalhes ▾]                                    │
             └─────────────────────────────────────────────────┘
```

**Critério:** a mensagem da ficha deve diferenciar falha REST de indisponibilidade geral **somente se o BFF entregar sinal de erro seguro e inequívoco**. Caso contrário, preservar erro genérico e usar o card administrativo para diagnóstico; não inferir causa de 401 pela UI nem revelar URL interna.

### Ações e navegação

- `Verificar agora` verifica **apenas a integração**, não refaz carregamento da ficha e não grava dados.
- `Tentar novamente` continua recarregando a ficha, independentemente do card.
- Não ocultar ação `Novo fornecedor` nem sugerir que POST funciona só porque flags estão ON; ações de escrita já seguem AuthZ e tratamento de falhas.
- Não expor dados do fornecedor consultado no payload de diagnóstico.

## 4. Mobile / acessibilidade

- Mobile: card vira painel **inline recolhível** após hero / antes da tabela ou erro; nenhuma sobreposição fixa ou rolagem horizontal; não ocluir botão principal ou conteúdos.
- Claro/escuro conforme tokens `@delpi/plugin-ui`; CSS sob `.dashboard-supplies-portal`.
- Um acionador com rótulo acessível `Verificar integração REST de fornecedores`; regiões de status `aria-live=polite` só quando o usuário pedir refresh; foco e Escape/close conforme componente do kit; sem blink/polling automático.
- Nunca colocar estados `PASS` de diagnostico legado de forma permanente sem timestamp ou sinalizar evidência desatualizada.

## 5. Contrato a inventariar e propor (sem implementação)

Fluxo: `MFE supplies → supplies-api → api-delpi → REST Protheus`. Procurar status/health já existentes em `api-delpi`; usar rota nova **somente se não houver contrato compatível**. `supplies-api` é owner da AuthZ do diagnóstico e composição; Core define effective permissions, usar capability administrativa **existente** adequada, fail-closed, sem nova permissão por botão.

Modelo de resposta **TARGET**, não declarar contrato implementado:

```json
{
  "checked_at": "2026-10-26T12:00:00-03:00",
  "environment": "production",
  "configuration": "ok",
  "authentication": "failed",
  "suppliers_read": "not_checked",
  "create_gate": "enabled",
  "update_gate": "enabled",
  "write_validation": "not_tested",
  "overall": "upstream_pending"
}
```

Verificações:
1. Resolver ambiente/base/path e conferir pin e segregação (sem divulgar host para browser).
2. Conectar e autenticar no token upstream sem logar segredo; timeout controlado.
3. GET **não destrutivo** para consulta conhecida/autorizada, somente após token válido, sem enumerar cadastros de terceiros.
4. Ler flags efetivas CREATE/UPDATE, guards e autorização sem executá-los como operação de escrita.
5. Devolver estado sanitizado, erros genéricos e horário; nenhum token, senha, URL interna, header `Authorization` ou dados fiscais no frontend.
6. Não chamar POST/PUT reais nem simular transação potencialmente persistente como health-check.

**Estados:** `not_checked`, `checking`, `ready_for_attempt` (auth + GET válidos, gates/guard coerentes; **não prova escrita**), `upstream_pending` (401/404), `unavailable` (timeout/5xx/config/segurança), `stale` (resultado antigo). Falha do próprio endpoint de diagnóstico = `unavailable`, não falha comprovada do ERP. Resposta sob autenticação/autorização adequada; data/hora local clara.

## 6. Aceite e sequenciamento

**P0**: inventariar endpoint/permission/kit/consumidores no HEAD e congelar contrato (autorizar separadamente). **P1**: implementar diagnóstico read-only no owner canônico + BFF/AuthZ + card compartilhado nas duas páginas e Help. **P2**: testes positive/sibling/negative, mobile, temas, federado, deploy e smoke autenticado. Não usar mudança de UX para desbloquear a primeira escrita produtiva.

Critérios RQ/AC:
- AC-01: na lista, diagnóstico não bloqueia consulta SQL.
- AC-02: na ficha, estado de erro continua visível e retry independente.
- AC-03: card flutuante não cobre ações; mobile inline.
- AC-04: status separado por configuração, token, GET, flags, escrita não testada.
- AC-05: refresh manual idempotente, sem gravação e sem polling.
- AC-06: nenhum segredo ou host interno no MFE.
- AC-07: AuthZ do backend baseada em Core, fail-closed; não é uma permission nova.
- AC-08: 401/404 upstream geram `upstream_pending`, não `ready`.
- AC-09: timeout, 403, 404, erro do próprio diagnóstico e estado stale claros.
- AC-10: desktop/mobile, tema claro/escuro, foco e teclado, Help sincronizada.

**Fora de escopo:** mudança de rotas Protheus, DDL/params, ativação de flags, primeiro POST/PUT real, histórico/auditoria, dashboards globais, novos grants.

**STOP / EXECUTION_DRIFT:** falta de owner de verificação read-only; contrato que exigiria escrita; ausência de autorização adequada; uso de informação sensível; mudança compartilhada não compatível com demais consumidores.

**Resultado esperado:** especificação de UX, **não UI publicada**. Não confundir com o G8 produtivo ou o cutover já documentado.
