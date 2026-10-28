# Wireframe — Solicitar acompanhamento

**Status:** TARGET / PROPOSED — wireframe funcional candidato; não constitui código, contrato aprovado ou implantação. **Processo:** PROC-0073. **Host:** Portal Engenharia → Ferramentas → Produtos Novos. **Autoridade:** Keycloak identidade; Core RBAC; engineering-api BFF alvo; sistemas de Engenharia/Produção detêm OP, programação, desenho e regras oficiais. TÉO/Transformômetro documenta a melhoria, não executa produção.

**Padrão transversal:** aderir ao design system real `@delpi/plugin-ui` após inventário; URL compartilhável; foco/teclado/contraste, desktop/mobile, loading/empty/error/forbidden/stale/partial; filtros só em escopo autorizado; sem números fictícios em runtime; mutação requer AuthZ ao vivo, idempotência quando aplicável, confirmação e read-back. Campos e rotas abaixo são conceituais, não endpoints comprovados.

**Objetivo:** permitir ao líder de fábrica informar início efetivo/necessidade de acompanhamento sem depender só da programação automatizada.

### Wireframe — diálogo ou página responsiva
```text
Solicitar acompanhamento
[Selecionar OP autorizada 🔎]  Produto/unidade (somente leitura da fonte oficial)
[Operação atual ▼]  [Data/hora efetiva (validar fonte)]
[Observação operacional opcional]  [Exibir previsão existente / duplicidade]
[Cancelar] [Confirmar solicitação]
Após confirmação: protocolo, estado retornado, responsável/fila, vínculo para acompanhar
```
### Comportamentos
OP obrigatória; seleção respeita RBAC e não permite digitar ID arbitrário para acessar registro alheio. Pedido se concilia com previsão existente; idempotência no backend; erro/conflito mostram resultado claro e opção de recuperar. Solicitação NÃO significa verificação realizada ou liberação de produção. O canal automático continua coexistindo.
### AC
AC-SA-01 somente líder autorizado; AC-SA-02 vínculo a OP canônica; AC-SA-03 duplo clique/reenvio não duplica; AC-SA-04 recebimento e persistência confirmados pela API; AC-SA-05 a partir da programação contextualiza OP; AC-SA-06 falha não exibe 'enviado' indevidamente.

## Pendências de implementação
Inventariar contratos, componentes e rotas reais; validar com os owners; elaborar testes, design visual e checklist de acessibilidade. Nenhuma autoridade técnica é atribuída pelo wireframe.
