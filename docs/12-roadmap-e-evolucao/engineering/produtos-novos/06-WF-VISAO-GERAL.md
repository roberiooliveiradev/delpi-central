# Wireframe — Visão geral

**Status:** TARGET / PROPOSED — wireframe funcional candidato; não constitui código, contrato aprovado ou implantação. **Processo:** PROC-0073. **Host:** Portal Engenharia → Ferramentas → Produtos Novos. **Autoridade:** Keycloak identidade; Core RBAC; engineering-api BFF alvo; sistemas de Engenharia/Produção detêm OP, programação, desenho e regras oficiais. TÉO/Transformômetro documenta a melhoria, não executa produção.

**Padrão transversal:** aderir ao design system real `@delpi/plugin-ui` após inventário; URL compartilhável; foco/teclado/contraste, desktop/mobile, loading/empty/error/forbidden/stale/partial; filtros só em escopo autorizado; sem números fictícios em runtime; mutação requer AuthZ ao vivo, idempotência quando aplicável, confirmação e read-back. Campos e rotas abaixo são conceituais, não endpoints comprovados.

**Objetivo:** permitir que Engenharia planeje a semana e enxergue a carteira de novos produtos e riscos de acompanhamento.

### Wireframe
```text
Produtos Novos                         [Período ▼] [Unidade ▼] [Buscar OP/produto]
Carga Máquina: última sincronização / aviso de indisponibilidade
[OPs previstas] [Solicitadas] [Em acompanhamento] [Pendências] [Concluídas]
Próximas OPs: OP | Produto | Unidade | Previsão | Situação | Acompanhamento | Abrir
Minha fila: chamados novos | verificações pendentes | divergências em análise
```
### Comportamentos
- Período padrão: semana corrente na zona de negócio; seleção semana, mês ou datas livres; persistência em URL.
- Cards levam à lista já filtrada; contagens sempre derivadas do backend autorizado, com período e referência temporal explícitos.
- Tabela ordenada por data prevista, sem equiparar programação a início; linha abre Detalhes da OP.
- Alerta de dados atrasados exibe timestamp e causa, sem afirmar programação atual.
### Ações/permissões
Engenharia vê carteiras autorizadas; líder pode acessar 'Solicitar acompanhamento' conforme RBAC; Qualidade vê itens da filial autorizada.
### AC
AC-VG-01 filtros consistentes entre cards e tabelas; AC-VG-02 dados stale visíveis; AC-VG-03 usuário sem acesso não vê OP de unidade alheia; AC-VG-04 cards não apresentam números sem dados.

## Pendências de implementação
Inventariar contratos, componentes e rotas reais; validar com os owners; elaborar testes, design visual e checklist de acessibilidade. Nenhuma autoridade técnica é atribuída pelo wireframe.
