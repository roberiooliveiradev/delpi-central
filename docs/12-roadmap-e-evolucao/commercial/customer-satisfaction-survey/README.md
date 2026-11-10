# Customer Satisfaction Survey — DELPI

> Status: DISCOVERY / TO_INVENTORY. Documento de levantamento inicial, sem aprovação de escopo técnico, arquitetura, cronograma ou implementação.

## Objetivo

Centralizar a análise da pesquisa de satisfação de clientes solicitada pelo Comercial, mantendo separadas as regras informadas, as decisões pendentes e as propostas futuras. A solução pretendida deverá considerar o Portal Comercial existente e a evolução do CRM, sem presumir ownership técnico antes do inventário.

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
- Até cinco dias após o encerramento: consolidar resultados, comentários e clientes críticos.
- Classificar problemas em Produto, Qualidade, Entrega, Atendimento, Comercial, Técnico, Comunicação ou Preço.
- Acompanhar planos de ação com problema, cliente, causa, ação, responsável, prazo e status; prever retorno ao cliente e reavaliação.

## Contexto da ata 2026/016 (INFORMADO)

- Pesquisa de satisfação é a primeira prioridade comercial, ligada a não conformidade relatada pela Qualidade.
- Comercial e Stefani já teriam preparado perguntas e indicadores; localizar chamado e documentação complementar.
- Considerar gestão restrita de destinatários e disparos, LGPD e liberação de indicadores conforme validação.
- Avaliar primeira entrega modular no Portal Comercial, com possível integração futura ao CRM; arquitetura não decidida.
- Expectativa condicionada de primeira versão até fim de novembro de 2026; não é compromisso aprovado nem entrega comprovada.

## Definições de negócio pendentes (PENDING)

1. Universo elegível de clientes, seleção de contatos e critérios de exclusão.
2. Uma resposta por cliente ou múltiplas respostas por contato; deduplicação, peso e agregação por cliente.
3. Identificação dos respondentes; anonimato; vínculo com cadastro comercial; tratamento de informações pessoais.
4. Canais de envio, responsáveis, entregabilidade, lembretes, expiração e reenvio.
5. Perguntas obrigatórias ou opcionais, opção não aplicável, respostas parciais e versionamento do questionário.
6. Fórmula oficial de NPS e denominadores de percentuais, respostas inválidas ou ausentes.
7. Regra de classificação de cliente crítico, critérios de alertas e ações relevantes.
8. Definições e autoridade dos segmentos, carteiras, faturamento, região e cliente estratégico.
9. Abertura/fechamento de campanha, permissões, auditoria e visibilidade de respostas individuais.
10. Estados e aprovações dos planos de ação, retorno ao cliente e reavaliação.
11. Critérios de comparação histórica entre campanhas e versões de perguntas.
12. Responsáveis por cada etapa, SLA de consolidação, métricas de sucesso e política de retenção.

## Análise técnica futura — não aprovada

Após validação funcional, levantar HEAD, branch, fontes canônicas, contratos existentes, consumidores, permissões e testes; determinar a menor solução suficiente. Só então detalhar entidades, endpoints, CRUD, integrações, frontend e critérios de aceite. Não criar backlog técnico como se fosse decisão tomada.

## Próxima atividade

Consolidar uma especificação funcional rastreável: requisito -> evidência -> regra de negócio -> pendência -> decisão do owner -> critério de aceite, preservando as perguntas completas do documento original e validando-as com Comercial/Qualidade.
