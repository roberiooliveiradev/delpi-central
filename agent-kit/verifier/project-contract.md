# Contrato de verificação — modelo para qualquer projeto

Copie a seção abaixo para o `AGENTS.md` na raiz do projeto (Cursor e Devin leem esse arquivo) e preencha
a parte **B**. A parte **A** é igual em todos os projetos: é o ciclo que o agente executor segue.

O marcador `<!-- delpi-verifier:contract -->` liga o *stop gate* do kit neste repositório. Sem ele, o
verificador continua disponível, mas nada obriga o executor a chamá-lo.

---

```markdown
## Verificação (delpi-verifier)

<!-- delpi-verifier:contract v1 -->

### A. Ciclo do executor

Antes de declarar uma tarefa concluída (ou de entregar o EXECUTION REPORT), o agente que implementou
**deve** rodar o verificador via `verify.py` e seguir o ciclo abaixo. O executor **nunca** se autoverifica.

1. **Quando chamar:** depois de qualquer alteração de código, configuração, migration, contrato ou teste.
   Mudança só de texto em documentação pode dispensar, desde que o relatório final diga isso.
2. **Como chamar:** grave o `PEDIDO DE VERIFICAÇÃO` num arquivo em
   `<git-dir>/delpi-verifier/requests/` (nunca no working tree) e rode **um** comando:

       python ~/.delpi-agent-kit/verify.py --request-file <arquivo>

   (No Windows/Devin Desktop: `%USERPROFILE%\.delpi-agent-kit\verify.cmd --request-file <caminho-wsl>`.)

   Conteúdo do pedido:

       PEDIDO DE VERIFICAÇÃO
       objetivo: <pedido original completo, com RQ-* e AC-*>
       escopo: <base..head | working tree>
       repositorio: <opcional: caminho, se não for a raiz do workspace>
       alegacoes: <o que você fez; testes que rodou e resultado>
       modelo_executor: <seu modelo>
       rodada: <1 | 2 | 3>
       ordens_anteriores: <rodadas 2 e 3: cada OC-* e sua resposta (corrigida ou contestada + evidência)>

   Não envie seu raciocínio nem o histórico da conversa: o verificador julga pelo pedido e pelo código.
3. **Ordens de correção (OC-\*):** corrija cada uma no **código de produção**. Não altere teste, runner,
   configuração de cobertura ou limites para fazer a reconferência passar. Se você discorda de uma OC,
   **conteste com evidência** (comando, saída, arquivo:linha) em vez de corrigir.
4. **Nova rodada:** depois de corrigir, rode o `verify.py` de novo com `rodada` + 1 e as ordens anteriores.
   Ele reverifica tudo, não só as ordens.
5. **Limite:** no máximo **3 rodadas**. Se a rodada 3 terminar em `REWORK`, pare e entregue ao humano com
   o histórico.
6. **DECISION_REQUIRED e EXECUTION_DRIFT** encerram o ciclo na hora: não decida sozinho, devolva ao humano.
7. **Relatório final:** inclua o veredito do verificador **sem editar**, a tabela de rodadas
   (rodada → veredito → OCs abertas/fechadas) e o que ficou como resíduo.

### B. Específico deste projeto

- **Fontes de autoridade (em ordem):** <lista, da mais forte para a mais fraca>
- **Comandos de verificação:**
  - <comando> — <quando usar>
- **Regras que não podem ser quebradas:** <invariantes de domínio/arquitetura; aponte o documento canônico>
- **Áreas sensíveis (verificar com mais rigor):** <auth, dinheiro, dados pessoais, migrations...>
- **Comandos proibidos ao verificador (além dos padrões):** <deploy, scripts de produção...>
- **Vocabulário extra:** <termos de status/evidência próprios do projeto, se houver>
```
