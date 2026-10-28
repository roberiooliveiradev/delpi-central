# 01 — Visão e escopo

## Problema e resultado
No AS-IS do PROC-0073, o acompanhamento de produtos novos depende de acionamentos humanos, verificações por checklist e comunicação entre Engenharia, Produção e Qualidade. Falhas de aviso/retomada e falta de visão agregada dificultam antecipação e rastreabilidade. O TO-BE pretende proporcionar à Engenharia uma **lista de OPs de produtos novos previstas na semana, no mês ou em período arbitrário** e acionar o acompanhamento quando a produção efetivamente começar, seja por evento confiável, seja por chamado do líder.

## Diretriz de produto decidida
- Nome da ferramenta: **Produtos Novos**.
- Alternativa: **B — fluxo integrado e rastreável com acionamento híbrido**.
- Previsão via Carga Máquina/OP + acionamento manual do líder coexistem e são conciliados sem duplicidade.
- Matriz: Engenharia verifica; filial: Qualidade verifica com checklist e envia e-mail/conformidade à Engenharia da matriz no AS-IS. No TO-BE, propor registro estruturado sem afirmar que os e-mails atuais foram substituídos.
- Divergência técnica: Engenharia da matriz corrige; autoridade formal de interrupção/retomada permanece a confirmar.
- Engenharia é responsável pela retirada governada da indicação Produto Novo após conclusão conforme, via sistema oficial de desenhos.

## Personas e escopo
- Engenharia: planejar acompanhamento, visualizar programação, registrar verificações na matriz, tratar divergências e avaliar encerramento.
- Líder de Produção: solicitar início de acompanhamento na OP autorizada.
- Qualidade da filial: executar checklist, registrar resultados, comunicar divergência/conformidade.
- Gestor autorizado: acompanhar pendências e indicadores agregados, conforme escopo de acesso.
- Não pressupor que solicitante do GLPI seja gestor designado.

## Fora do escopo da primeira definição
- Bloqueio sistêmico automático de produção sem regra e owner aprovados.
- Edição/publicação direta de desenho pelo MFE, EVA, prompt ou ferramenta MCP.
- Um novo cadastro fonte de verdade de produtos/OPs/roteiros.
- SLA ou metas numéricas inventadas.

## Estado e evidência
AS-IS v0.3 validado documentalmente; baseline documental criada sem métricas; TO-BE proposto. Existem lacunas sobre fontes de OP, classificação produto novo, autoridade formal e exemplos operacionais dos checklists/e-mails.
