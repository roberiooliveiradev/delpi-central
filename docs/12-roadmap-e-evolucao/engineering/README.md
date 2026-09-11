# Portal de Engenharia — índice

> **Status:** planejamento oficial — 2026-09-11  
> **Implementação:** não autorizada por este documento. Executar somente após plano Cursor revalidado e solicitação explícita.  
> **Base:** arquitetura Minha DELPI, regras `.cursor`, Portal Comercial/Suprimentos como referência de experiência, ativos atuais de Engenharia e roadmaps vigentes.

## Objetivo

Criar o **Portal de Engenharia** como ponto central de trabalho do domínio Engenharia na Minha DELPI, reunindo visão gerencial, tarefas, colaboração, LMPs, consultas técnicas e acessos a aplicações relacionadas sem duplicar ownership de outros bounded contexts.

O Portal de Engenharia deve funcionar como **módulo-shell do domínio**, no mesmo padrão conceitual dos portais Comercial e Suprimentos: navegação principal consistente, ferramentas em catálogo, composição de dados por API própria, RBAC central, componentes `@delpi/plugin-ui`, rotas compartilháveis e experiência responsiva.

## Decisões de produto já travadas

1. A **TopBar** principal segue esta ordem:

   `Início → Visão geral → Sala de interação → Minhas tarefas → LMPs`

2. **Produtos não fica na TopBar**. É uma ferramenta do Portal de Engenharia, acessível pela vitrine/listagem de ferramentas e por deep links contextuais.
3. **LMPs** é jornada principal e entra na TopBar depois de Minhas tarefas.
4. **Sala de interação** é capacidade transversal do portal, com salas gerais e contextuais.
5. **Controle de MP** aparece como aplicação/ferramenta do Portal, mas o alvo canônico do fluxo é `my-requests` + `requests-api`; não criar segundo MFE de MP.
6. **TRANSFORMA+** permanece com ownership do Transformômetro; o Portal integra resumo/acesso, não duplica o produto.
7. **Desenhos e dados autorizados do FILESERVER** devem ser consumidos por backend/API; o browser não acessa compartilhamentos de rede diretamente.
8. O alvo técnico do portal é um bounded context próprio (`plugins/engineering` + `engineering-api`). Com API própria, o MFE **não chama `api-delpi` diretamente**.

## Documentos deste pacote

| Arquivo | Papel |
|---|---|
| [SCOPE-OWNERSHIP.md](./SCOPE-OWNERSHIP.md) | Escopo funcional, ownership, inventário atual, fronteiras e integrações |
| [WIREFRAMES.md](./WIREFRAMES.md) | Navegação, TopBar, páginas, estados e wireframes textuais |
| [API-ROUTES.md](./API-ROUTES.md) | Contratos alvo do `engineering-api`, dependências e deep links |
| [ROADMAP.md](./ROADMAP.md) | Ledger RQ-*, decisões travadas, fases E*.S*, testes, rollout e aceite |

## Norte do produto

```text
Portal de Engenharia
├── Início                → o que importa para mim agora
├── Visão geral           → como está a Engenharia
├── Sala de interação     → colaboração geral e contextual
├── Minhas tarefas        → worklist pessoal consolidada
├── LMPs                  → jornada operacional principal
└── Ferramentas           → aplicações e consultas especializadas
    ├── Produtos
    ├── Controle de MP
    ├── Documentos técnicos
    ├── Biblioteca de desenhos
    ├── Não conformidades
    ├── TRANSFORMA+
    └── futuras ferramentas de Engenharia
```

## Princípios de implementação

- **Kit-first:** procurar e reutilizar `@delpi/plugin-ui` antes de criar componente local.
- **Sem CSS do kit no MFE:** o plugin só define layout próprio e tokens locais mapeados para `--delpi-ui-*`.
- **Backend decide:** regra de negócio, escopo e autorização efetiva não vivem no frontend.
- **URL compartilhável:** filtros, seleção e detalhes relevantes devem sobreviver a F5/back/forward.
- **Estados explícitos:** loading, empty, error, forbidden e partial quando aplicável.
- **Acessibilidade e responsividade:** desktop, tablet, mobile, teclado, foco e tema claro/escuro são parte da Definition of Done.
- **Ajuda sincronizada:** toda feature user-facing deve manter helps/manual coerentes.
- **Evidência antes de implementação:** revalidar contrato, owner, consumidores e testes antes de cada E*.S*.

## Ativos atuais relacionados

- `plugins/dashboard-engineering` — visão atual de indicadores de Engenharia (LMPs + TRANSFORMA+).
- `plugins/dashboard-lmps` — jornada operacional de LMPs, detalhe, produtos/BOM, histórico, Gantt e NCs.
- `api-delpi /engineering/*` — contratos operacionais atuais de Engenharia/TOTVS.
- `api-delpi /products/*` — dados de produtos, estrutura, onde é usado, desenho, estoque, fornecedores, preço e análise.
- `transformometro-api` + plugin Transformômetro — owner do TRANSFORMA+.
- `plugins/my-requests` + `requests-api` — alvo canônico do Controle de MP.
- FILESERVER corporativo — biblioteca de desenhos já exposta read-only pela `api-delpi`.
- Strategic Indicators — fonte canônica dos scores/indicadores estratégicos.

## Regra de transição

Os plugins atuais não devem ser removidos no primeiro passo. O Portal nasce com integração/paridade progressiva e só absorve/depreca experiências legadas após:

1. paridade funcional comprovada;
2. RBAC e deep links validados;
3. smoke federado no Portal;
4. documentação/Ajuda atualizadas;
5. cutover e rollback definidos.
