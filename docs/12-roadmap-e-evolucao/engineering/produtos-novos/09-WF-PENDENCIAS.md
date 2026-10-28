# Wireframe — Pendências e divergências

**Status:** TARGET / PROPOSED — wireframe funcional candidato; não constitui código, contrato aprovado ou implantação. **Processo:** PROC-0073. **Host:** Portal Engenharia → Ferramentas → Produtos Novos. **Autoridade:** Keycloak identidade; Core RBAC; engineering-api BFF alvo; sistemas de Engenharia/Produção detêm OP, programação, desenho e regras oficiais. TÉO/Transformômetro documenta a melhoria, não executa produção.

**Padrão transversal:** aderir ao design system real `@delpi/plugin-ui` após inventário; URL compartilhável; foco/teclado/contraste, desktop/mobile, loading/empty/error/forbidden/stale/partial; filtros só em escopo autorizado; sem números fictícios em runtime; mutação requer AuthZ ao vivo, idempotência quando aplicável, confirmação e read-back. Campos e rotas abaixo são conceituais, não endpoints comprovados.

**Objetivo:** evitar que a conclusão da fabricação apague verificações incompletas ou problemas técnicos em aberto.

### Wireframe
```text
Pendências [Abertas | Em correção | Aguardando revisão | Resolvidas] [Unidade ▼]
OP | Produto | Operação | Tipo | Descrição curta | Responsável | Desde | Prioridade | Abrir
Detalhe: evidências, comunicação Matriz/Filial, correção, rechecagem, trilha de decisões
```
### Regras
Divergência registrada pela Qualidade/Engenharia é encaminhada à Engenharia da matriz para correção; somente owner com autoridade formal pode liberar parada/retomada. Ausência de checklist é pendência de acompanhamento, não necessariamente ordem de parada. Comunicação positiva e negativa da filial deve ser rastreável; canal de notificação futuro ainda a decidir.
### AC
AC-PD-01 pendência não some por reprogramação; AC-PD-02 motivo e histórico preservados; AC-PD-03 usuário sem acesso não modifica correção; AC-PD-04 fechamento exige rechecagem aplicável; AC-PD-05 distinguir operacional/qualidade/comunicação.

## Pendências de implementação
Inventariar contratos, componentes e rotas reais; validar com os owners; elaborar testes, design visual e checklist de acessibilidade. Nenhuma autoridade técnica é atribuída pelo wireframe.
