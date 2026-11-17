# Arquitetura greenfield

**Status:** TARGET. Criar o Studio de forma independente em `plugins/delpi-line-balance-studio/`, com API pública futura importável por diferentes portais.

```text
Host A: Portal Engenharia    Host B: outro portal
          |                         |
          +---- contratos públicos Studio ----+
                           |
               DELPI Line Balance Studio
           app / model / ports / methods / features
                           |
          @delpi/plugin-ui (componentes visuais)
                           |
              adapters fornecidos pelo host
                           |
             Domain APIs/Engineering domain
```

## Boundaries
- **Studio:** workflow, estado de edição, origens manual/oficial, tabelas, postos, cenários, catálogo.
- **Plugin UI:** controles, gráficos, visualização tabular e design system. Sem cálculos de Engenharia.
- **Domínio Engineering/EVA:** takt, balanceamento, precedência, otimização, restrições e viabilidade. Sem depender de React/HTTP/SDK.
- **Portais:** autorização de entrada, navegação, adapters BFF e integração; não acoplados à implementação do Studio.
- **API-DELPI:** única fonte oficial do roteiro, sob autorização; cenário manual nunca se torna cadastro oficial.
- **Core/Keycloak:** AuthN/AuthZ live; token não vai ao Studio nem a export/draft.

## Decisão de independência
NÃO ler a implementação legada como base técnica, extrair tipos ou copiar componentes de `plugins/engineering`; NÃO fazer import de `LineBalancingPage`, `yamazumi.ts`, `PostConfigurator`, `ProductRoutingTab` ou seus testes. Podem ser utilizados padrões corporativos e API externa oficiais independentemente da tela antiga. O primeiro consumidor pode importar o Studio apenas depois da validação de API pública.

## Módulos planejados
`src/app` composição, `src/model` modelo puro, `src/ports` portas, `src/methods/catalog` catálogo, `src/methods/yamazumi` primeira ferramenta visual, `src/features/{study-origin,operation-editor,shift-editor,station-editor,scenario-comparison}`, `src/ui`, `tests`.

Modo de distribuição (remote federation vs bundled) deve ser escolhido após inventário das convenções de build, sem presumir ou cadastrar manifest agora. Alteração de owner ou source of truth permanece governada.
