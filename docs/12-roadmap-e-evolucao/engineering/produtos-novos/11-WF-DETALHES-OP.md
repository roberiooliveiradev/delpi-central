# Wireframe — Detalhes da OP

**Status:** TARGET / PROPOSED — wireframe funcional candidato; não constitui código, contrato aprovado ou implantação. **Processo:** PROC-0073. **Host:** Portal Engenharia → Ferramentas → Produtos Novos. **Autoridade:** Keycloak identidade; Core RBAC; engineering-api BFF alvo; sistemas de Engenharia/Produção detêm OP, programação, desenho e regras oficiais. TÉO/Transformômetro documenta a melhoria, não executa produção.

**Padrão transversal:** aderir ao design system real `@delpi/plugin-ui` após inventário; URL compartilhável; foco/teclado/contraste, desktop/mobile, loading/empty/error/forbidden/stale/partial; filtros só em escopo autorizado; sem números fictícios em runtime; mutação requer AuthZ ao vivo, idempotência quando aplicável, confirmação e read-back. Campos e rotas abaixo são conceituais, não endpoints comprovados.

**Objetivo:** oferecer uma visão única da programação, solicitação, verificação e eventual pendência da OP selecionada.

### Wireframe
```text
Produtos Novos > Programação > OP [identificador]  [Estado da programação] [Estado acompanhamento]
Produto | Desenho/revisão oficial | Unidade | Data prevista | Início real (se comprovado)
Abas: Resumo | Checklist | Ocorrências | Histórico
Resumo: etapas requeridas / verificadas / pendentes, responsável, eventos de programação
Ações: [Solicitar acompanhamento] [Abrir checklist] [Ver ocorrência]
Conclusão: verificação completa → confirmação Engenharia → fluxo oficial do desenho
```
### Casos-limite
Múltiplas OPs por produto; alterações de desenho/roteiro; OP sem checklist aplicável; revisão do desenho alterada durante verificação. Não extrapolar validade das verificações para revisão diferente sem regra oficial.
### AC
AC-DE-01 fonte e revisão visíveis; AC-DE-02 acesso por unidade; AC-DE-03 ações governadas; AC-DE-04 estados de falta de fonte e dados divergentes; AC-DE-05 completude não implica publicação automática.

## Pendências de implementação
Inventariar contratos, componentes e rotas reais; validar com os owners; elaborar testes, design visual e checklist de acessibilidade. Nenhuma autoridade técnica é atribuída pelo wireframe.
