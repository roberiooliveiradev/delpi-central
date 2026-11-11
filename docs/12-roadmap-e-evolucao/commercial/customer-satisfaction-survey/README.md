# Customer Satisfaction Survey — DELPI

> Status: REQUISITOS FUNCIONAIS CONSOLIDADOS / TO_INVENTORY técnico incremental. **Sem evidência de implementação, homologação ou aprovação de backlog técnico.**

## Objetivo

Centralizar a análise da pesquisa de satisfação de clientes solicitada pelo Comercial, mantendo separadas as regras do plano, as decisões de negócio, o padrão arquitetural aceito e as verificações técnicas ainda necessárias. A solução pretendida deverá considerar o Portal Comercial existente e a evolução do CRM, sem presumir ownership técnico antes do inventário.

## Fontes

- Plano de Monitoramento da Satisfação dos Clientes — Delpi (documento fornecido pelo Comercial; fonte de requisitos de negócio, não de implementação).
- Transformômetro: ata 2026/016 — Retorno às Demandas Comerciais — Transforma Mais, reunião de 06/11/2026 (parcialmente assinada em 10/11/2026; conteúdo sujeito a validação).
- Documentação canônica do Portal Comercial nesta pasta pai.
- Revisar eventual reutilização de `docs/12-roadmap-e-evolucao/customer-experience/` e das capacidades já existentes de formulários; nenhuma reutilização está comprovada aqui.

## Informações expressas no plano (INFORMADO)

- Duas pesquisas por ano: maio/junho e novembro/dezembro.
- Dez dimensões avaliadas de 1 a 5: qualidade, prazo de entrega, atendimento, agilidade, comunicação, suporte técnico, suporte comercial, flexibilidade, confiabilidade e parceria.
- Uma pergunta geral de satisfação (1–5), referida como IGS; definida como média das notas atribuídas pelos clientes.
- Uma pergunta de recomendação NPS (0–10); fórmula do indicador não explicitada no plano.
- Três perguntas abertas: pontos fortes, melhorias e necessidades/expectativas ainda não atendidas.
- Segmentações desejadas: cliente, segmento, vendedor, região, tempo de relacionamento, volume/faturamento e clientes estratégicos versus demais.
- Indicadores desejados: IGS, NPS, taxa de resposta (clientes respondentes / convidados), médias por dimensão, percentuais de satisfeitos (notas 4–5) e críticos (notas 1–2), evolução semestral/anual e ações concluídas / identificadas.
- Até cinco dias após o encerramento: consolidar resultados, comentários e clientes críticos (processo previsto no plano).
- Classificar problemas em Produto, Qualidade, Entrega, Atendimento, Comercial, Técnico, Comunicação ou Preço.
- O plano original prevê ações com problema, cliente, causa, ação, responsável, prazo e status; **essas funcionalidades não integrarão a primeira entrega**.

## Contexto da ata 2026/016 (INFORMADO)

- Pesquisa de satisfação é a primeira prioridade comercial, ligada a não conformidade relatada pela Qualidade.
- Comercial e Stefani já teriam preparado perguntas e indicadores; localizar chamado e documentação complementar.
- Considerar gestão restrita de destinatários e disparos, LGPD e liberação de indicadores conforme validação.
- Avaliar primeira entrega modular no Portal Comercial, com possível integração futura ao CRM; arquitetura não decidida.
- Expectativa condicionada de primeira versão até fim de novembro de 2026; não é compromisso aprovado nem entrega comprovada.

## Navegação da documentação

**Entrada obrigatória para análise e desenvolvimento:** [REQUIREMENTS-INDEX.md](./REQUIREMENTS-INDEX.md) — tabela mestre com 34 requisitos, origem, estado e links para aprofundamento. **Não reproduza todo o material em novos documentos.**

- [BUSINESS-DECISIONS.md](./BUSINESS-DECISIONS.md) — histórico das decisões de negócio; consultar somente o assunto vinculado ao requisito.
- **Plano de Monitoramento da Satisfação dos Clientes — Delpi** — documento integral está nas fontes do projeto, não copiado para esta pasta do GitHub. As seções 1–10 são a fonte de negócio; o índice cita as páginas pertinentes.
- [BACKEND-API-PROPOSAL.md](./BACKEND-API-PROPOSAL.md) — **padrão arquitetural aceito em 10/11/2026**, atualizado pelo recorte de 11/11; implementação pendente.
- [SURVEY-FIRST-RELEASE-CONTRACT.md](./SURVEY-FIRST-RELEASE-CONTRACT.md) — **contrato fechado da primeira entrega:** três tabelas, campanhas, participantes, convite por cópia, formulário externo, respostas e indicadores, sem envio de e-mail pela aplicação e sem planos de ação.
- [FRONTEND-FIRST-RELEASE-PLAN.md](./FRONTEND-FIRST-RELEASE-PLAN.md) — planejamento das telas internas, **seção única Pesquisa de Satisfação do Cliente na Visão Geral com indicadores gerais**, formulário público, indicadores e testes, respeitando a primeira entrega.
- Outros arquivos técnicos de detalhe devem ser criados **somente quando necessários** para uma frente concreta e vinculados ao ID correspondente no índice.

## Situação e limites

As decisões principais de negócio já foram levantadas e registradas no índice. **Em 11/11/2026**, o solicitante restringiu a primeira entrega à pesquisa e aos indicadores, retirando envio de e-mail pela aplicação e desenvolvimento de planos de ação. Estas disposições prevalecem sobre referências históricas do plano e da entrevista. São regras **propostas para implementação**, não funcionalidades comprovadamente existentes. A gestão da pesquisa cabe aos códigos `commercial.marketing` (a criar durante o desenvolvimento) ou `commercial.manage` (existente); as respostas terão histórico no domínio da API Comercial para comparação plurianual; o cadastro mestre de clientes permanece no TOTVS, consultado por meio da API DELPI, conforme fontes e decisões.

Retenção por tempo indeterminado é intenção funcional declarada, condicionada aos controles de privacidade e conformidade com a LGPD. **Segurança, permissões reais, contratos, modelos físicos, rotas, consumidores, testes e possibilidade de reutilização ainda exigem evidências técnicas.**

## Fluxo de evolução limitado

1. Selecionar uma frente/ID no [índice](./REQUIREMENTS-INDEX.md).
2. Ler somente o detalhe já referenciado e os contratos canônicos da frente.
3. No GitHub, confirmar HEAD, branch e, quando houver acesso ao ambiente de trabalho, working tree; inspecionar owners, consumidores, permissões e testes.
4. Registrar ali o menor conjunto de mudanças e critérios de aceite necessários, sem criar documento duplicado.
5. Implementar e verificar antes de marcar `IMPLEMENTADO` ou `VALIDADO` com evidência (código e testes não são prova automática de uso real).

**Não repetir a entrevista inteira nem criar ciclos de documentação sem um bloqueio concreto.** Questões sem impacto imediato podem permanecer identificadas para a frente correspondente, sem impedir toda a iniciativa.
