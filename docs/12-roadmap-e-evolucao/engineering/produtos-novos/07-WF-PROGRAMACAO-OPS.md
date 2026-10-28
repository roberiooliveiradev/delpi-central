# Wireframe — Programação de OPs

**Status:** TARGET / PROPOSED — wireframe funcional candidato; não constitui código, contrato aprovado ou implantação. **Processo:** PROC-0073. **Host:** Portal Engenharia → Ferramentas → Produtos Novos. **Autoridade:** Keycloak identidade; Core RBAC; engineering-api BFF alvo; sistemas de Engenharia/Produção detêm OP, programação, desenho e regras oficiais. TÉO/Transformômetro documenta a melhoria, não executa produção.

**Padrão transversal:** aderir ao design system real `@delpi/plugin-ui` após inventário; URL compartilhável; foco/teclado/contraste, desktop/mobile, loading/empty/error/forbidden/stale/partial; filtros só em escopo autorizado; sem números fictícios em runtime; mutação requer AuthZ ao vivo, idempotência quando aplicável, confirmação e read-back. Campos e rotas abaixo são conceituais, não endpoints comprovados.

**Objetivo:** antever os produtos novos que serão fabricados no Carga Máquina, por intervalo e unidade, sem iniciar automaticamente a produção.

### Wireframe
```text
Programação   [Semana|Mês|Personalizado] [Data inicial] [Data final]
[Unidade ▼] [Produto/OP 🔎] [Situação programação ▼] [Situação acompanhamento ▼]
Atualizado em: dd/mm hh:mm   [Atualizar consulta]
OP | Produto | Descrição | Unidade | Data prevista | Operações previstas | Produto Novo? | Acompanhamento | ⋯
[Detalhes] [Solicitar acompanhamento (somente líder autorizado)]
```
### Campos e semântica
OP/id canônico, produto/código, descrição, unidade, datas previstas, operação/roteiro quando disponível, status de programação e de acompanhamento separados, fonte e última sincronização. Origem exata, classificação 'novo' e disponibilidade são TO_INVENTORY.
### Reprogramação e exceções
- Alterações de data atualizam previsão, preservam trilha e não geram conclusão/início falsos.
- OP sem classificação confiável fica indeterminada, não é silenciosamente excluída como 'não nova'.
- Cancelamento, duplicidade e ausência de eventos de início mostram estados explícitos.
### AC
AC-OP-01 semana/mês/período arbitrário; AC-OP-02 programação ≠ início; AC-OP-03 reprogramação auditável; AC-OP-04 paginação e filtros no backend autorizado; AC-OP-05 sincronização falha sem dados inventados.

## Pendências de implementação
Inventariar contratos, componentes e rotas reais; validar com os owners; elaborar testes, design visual e checklist de acessibilidade. Nenhuma autoridade técnica é atribuída pelo wireframe.
