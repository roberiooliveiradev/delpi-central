# Wireframe — Acompanhamentos

**Status:** TARGET / PROPOSED — wireframe funcional candidato; não constitui código, contrato aprovado ou implantação. **Processo:** PROC-0073. **Host:** Portal Engenharia → Ferramentas → Produtos Novos. **Autoridade:** Keycloak identidade; Core RBAC; engineering-api BFF alvo; sistemas de Engenharia/Produção detêm OP, programação, desenho e regras oficiais. TÉO/Transformômetro documenta a melhoria, não executa produção.

**Padrão transversal:** aderir ao design system real `@delpi/plugin-ui` após inventário; URL compartilhável; foco/teclado/contraste, desktop/mobile, loading/empty/error/forbidden/stale/partial; filtros só em escopo autorizado; sem números fictícios em runtime; mutação requer AuthZ ao vivo, idempotência quando aplicável, confirmação e read-back. Campos e rotas abaixo são conceituais, não endpoints comprovados.

**Objetivo:** operar fila de verificações por unidade, OP, responsável, estado e prioridade operacional autorizada.

### Wireframe
```text
Acompanhamentos [Meus | Minha unidade | Todos autorizados] [Situação ▼] [Período ▼]
OP | Produto | Unidade | Responsável | Início real | Etapas OK / requeridas | Pendências | Status | Abrir
Painel lateral: detalhes resumidos, última ação, próximo responsável, histórico
```
### Jornada
Acionamento manual ou evento oficial confiável cria/associa acompanhamento lógico; Engenharia na matriz ou Qualidade na filial executa checklist; incompleto mantém pendência; correção retorna à verificação.
### Ações e governança
'Assumir'/'Iniciar verificação'/'Registrar resultado' são candidatas sujeitas a política e API; não mudar status oficial por clique local. Retorno pós-save com read-back, conflito de concorrência e recuperação segura.
### AC
AC-AC-01 filtro por tarefa autorizada; AC-AC-02 unidade e responsável consistentes; AC-AC-03 duplicidade reconciliada; AC-AC-04 lista não mascara pendências de OP concluída; AC-AC-05 auditabilidade de cada mutação.

## Pendências de implementação
Inventariar contratos, componentes e rotas reais; validar com os owners; elaborar testes, design visual e checklist de acessibilidade. Nenhuma autoridade técnica é atribuída pelo wireframe.
