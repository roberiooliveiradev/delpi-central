# Wireframe — Checklist por operação

**Status:** TARGET / PROPOSED — wireframe funcional candidato; não constitui código, contrato aprovado ou implantação. **Processo:** PROC-0073. **Host:** Portal Engenharia → Ferramentas → Produtos Novos. **Autoridade:** Keycloak identidade; Core RBAC; engineering-api BFF alvo; sistemas de Engenharia/Produção detêm OP, programação, desenho e regras oficiais. TÉO/Transformômetro documenta a melhoria, não executa produção.

**Padrão transversal:** aderir ao design system real `@delpi/plugin-ui` após inventário; URL compartilhável; foco/teclado/contraste, desktop/mobile, loading/empty/error/forbidden/stale/partial; filtros só em escopo autorizado; sem números fictícios em runtime; mutação requer AuthZ ao vivo, idempotência quando aplicável, confirmação e read-back. Campos e rotas abaixo são conceituais, não endpoints comprovados.

**Objetivo:** registrar a evidência de acompanhamento técnico de cada etapa aplicável por Engenharia (matriz) ou Qualidade (filial).

### Wireframe
```text
OP / Produto / Desenho revisão / Unidade
Etapas de verificação: [Corte] [Decapagem] [Crimpagem] [Montagem] ... (somente se roteiro oficial exigir)
Etapa selecionada: critérios oficiais | [Conforme] [Divergente] [Não verificada]
Observações | Evidências autorizadas | Executor | Data/hora
[Salvar rascunho] [Enviar resultado] [Abrir divergência]
Resumo de completude e pendências | Histórico por operação
```
### Regras
Etapas, atributos e tolerâncias vêm do owner do roteiro/desenho — não inventar cotas, normas ou critérios técnicos. 'Conforme' exige dado verificável e operador autorizado. Checklist pendente impede conclusão do acompanhamento. Na filial, conclusão conforme aciona comunicação à Engenharia da matriz; desvios geram ocorrência/correção e posterior rechecagem. Rascunho ≠ aprovação técnica.
### AC
AC-CK-01 carregar somente operações aplicáveis; AC-CK-02 dados por OP/etapa/revisão; AC-CK-03 persistência e autor/autorização verificáveis; AC-CK-04 revisão concorrente tratada; AC-CK-05 evidências com provenance; AC-CK-06 usuário não pode aprovar desenho pelo checklist.

## Pendências de implementação
Inventariar contratos, componentes e rotas reais; validar com os owners; elaborar testes, design visual e checklist de acessibilidade. Nenhuma autoridade técnica é atribuída pelo wireframe.
