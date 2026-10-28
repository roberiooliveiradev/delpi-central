# Wireframe — Histórico e indicadores

**Status:** TARGET / PROPOSED — wireframe funcional candidato; não constitui código, contrato aprovado ou implantação. **Processo:** PROC-0073. **Host:** Portal Engenharia → Ferramentas → Produtos Novos. **Autoridade:** Keycloak identidade; Core RBAC; engineering-api BFF alvo; sistemas de Engenharia/Produção detêm OP, programação, desenho e regras oficiais. TÉO/Transformômetro documenta a melhoria, não executa produção.

**Padrão transversal:** aderir ao design system real `@delpi/plugin-ui` após inventário; URL compartilhável; foco/teclado/contraste, desktop/mobile, loading/empty/error/forbidden/stale/partial; filtros só em escopo autorizado; sem números fictícios em runtime; mutação requer AuthZ ao vivo, idempotência quando aplicável, confirmação e read-back. Campos e rotas abaixo são conceituais, não endpoints comprovados.

**Objetivo:** consultar a trilha de acompanhamento e evidências por OP/produto, sem reinterpretar eventos como aprovações.

### Wireframe
```text
Histórico [Período ▼] [OP/produto] [Unidade ▼] [Tipo de evento ▼]
Linha do tempo: data/hora | ator | ação | origem | revisão | resultado | evidência
Indicadores (se dados medidos): cobertura por operação | pendências | lead time | divergências
```
### Conteúdo
Previsão, reprogramação, chamado do líder, verificação, divergência, correção, retorno, e-mail/comunicação, aprovação e retirada do indicativo somente quando comprovados pela origem. Exibir revisão/versão e links às fontes autorizadas.
### AC
AC-HI-01 trilha íntegra sem eventos inferidos; AC-HI-02 filtro por OP e período; AC-HI-03 indicadores sem baseline aparecem 'não medido'; AC-HI-04 logs/resumos respeitam acesso; AC-HI-05 links não expõem armazenamento privado.

## Pendências de implementação
Inventariar contratos, componentes e rotas reais; validar com os owners; elaborar testes, design visual e checklist de acessibilidade. Nenhuma autoridade técnica é atribuída pelo wireframe.
