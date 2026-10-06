# 29 — Ajuda

## Estado

**TARGET / SYNCHRONIZED_WITH_FEATURES**

## Objetivo

**Ajuda** é o manual do usuário do Portal Controladoria & Finanças.

Deve seguir o padrão atual dos Portais Comercial e Suprimentos:
- página própria;
- acesso pela topbar;
- índice de conteúdo;
- conceitos;
- orientação "o que quero fazer / onde / como";
- FAQ/glossário quando útil;
- links/deep links para superfícies do Portal.

## Rota lógica

```text
/apps/controllership-finance/help
```

Permission: `controllership-finance.access`.


## Reuso obrigatório de `@delpi/plugin-ui`

A estrutura do manual já existe no kit e deve ser usada em vez de um manual local paralelo.

Import canônico:

```ts
import {
  createDashboardUserManual,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardSectionCard,
  HelpTooltip,
  FieldLabel,
  SectionHintLabel,
} from "@delpi/plugin-ui/index";
```

Estilos/runtime:

```ts
await import("@delpi/plugin-ui/styles");
```

`createDashboardUserManual` fornece o conjunto estrutural de manual:

```text
Frame
Scope
Layout / TOC
Section
Concepts
GuideTable
Faq
Glossary
Eyebrow
```

O conteúdo PT-BR permanece no plugin consumidor e deve ser sincronizado com as features.

Os Portais Comercial e Suprimentos já usam esse padrão; o novo Portal deve seguir a mesma abordagem.

**DO NOT RECREATE:** frame do manual, TOC/layout, concepts table, guide table, FAQ/glossary chrome ou tooltip genérico.

## Princípio

```text
USER_FACING_CHANGE
→ HELP_SYNC
```

Mudança material user-facing não está concluída enquanto a Ajuda correspondente estiver stale.

## Estrutura inicial

### Conceitos

Explicar pelo menos:
- Portal Controladoria & Finanças;
- Central de Fechamento;
- competência;
- preliminary/final;
- source/freshness;
- blocker;
- evidence/anexo;
- validação;
- N/A;
- pendência;
- finalizar;
- enviar;
- pacote/versão;
- Sala de interação;
- Minhas tarefas;
- ACCESS/MANAGE em linguagem de usuário.

### Navegação

Orientar:
- Início;
- Visão geral;
- Sala de interação;
- Minhas tarefas;
- Administração;
- Ajuda;
- Página do usuário quando a rota estiver implementada;
- Central de Fechamento e páginas internas.


### Página do usuário

Conteúdo a publicar **somente quando a rota estiver implementada**:

- o que é o perfil de usuário do Portal;
- quais dados vêm do cadastro corporativo/Core;
- onde editar foto, cargo e contatos no Meu Perfil da Minha DELPI;
- diferença entre "Não informado" e "temporariamente indisponível";
- que outro usuário do mesmo Portal pode ser consultado por viewer com ACCESS;
- que permissions/capabilities de outro usuário não são exibidas;
- que, no próprio perfil, o Portal pode mostrar label + códigos técnicos `controllership-finance.access` e `controllership-finance.manage`;
- que visualizar perfil não concede poder administrativo;
- que Administração continua dependente de MANAGE;
- como retornar ao contexto anterior.

Contrato fonte:
- [31-pagina-do-usuario.md](./31-pagina-do-usuario.md)

### Central de Fechamento

Referenciar conteúdo de Cockpit, Checklist e Documentos, Estoque e Conciliação, Classificações e Pendências e Pacote e Envio.

### Visão geral

Explicar significado dos indicadores aprovados, fórmula em linguagem de negócio, período/unidade, source, freshness, indisponível != zero e drilldowns.

### Sala de interação

Explicar contexto da sala, participantes, mensagens, diferença entre conversar e executar ação do processo e visibilidade/segurança.

### Minhas tarefas

Explicar de onde as tarefas vêm, como navegar ao owner, `pending_since` e ausência de SLA formal.

### Administração

Explicar ACCESS vs MANAGE, draft/review/publish/effective_from, snapshot, inativação e catálogos.

## Composição lógica

```text
HelpHeader
→ HelpScope
→ TableOfContents
→ Concepts
→ Guides
→ FAQs
→ Glossary
→ ContextualLinks
```

Preferir componentes de `@delpi/plugin-ui` e padrões já usados nos Portais Comercial/Suprimentos.

## Help contextual

Além da página geral, páginas materiais devem poder apontar para a seção correspondente da Ajuda.

O Help contextual não duplica conteúdo integral; direciona para a fonte vigente.

## Estados

A Ajuda é conteúdo versionado do produto e não deve depender de source operacional para renderizar o manual básico.

Ainda assim, tratar loading quando o conteúdo for carregado dinamicamente, not found para seção/deep link inválido e forbidden quando o usuário não possui acesso ao Portal.

## Governança

- UX/textos em PT-BR;
- identificadores técnicos em inglês;
- evitar detalhe técnico irrelevante ao usuário;
- não prometer funcionalidade ainda não implementada;
- conteúdo futuro deve ser marcado/ocultado até o gate correspondente; a seção Página do usuário não deve aparecer como funcionalidade disponível antes do runtime da rota;
- exemplos não substituem regra.

## Critérios de aceite

- acessível pela topbar;
- manual navegável por teclado;
- índice e headings semânticos;
- links internos/deep links válidos;
- conteúdo sincronizado com páginas implementadas;
- claro/escuro e mobile;
- nenhuma instrução contradiz AuthZ/business rules vigentes.
