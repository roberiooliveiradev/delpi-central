# Pesquisa de satisfação — Registro de decisões em aberto

> Estado: DISCOVERY / PENDING. Criado em 2026-11-10. As perguntas abaixo são questões de levantamento, **não** requisitos aprovados. Responder sequencialmente; registrar decisão, responsável, data, justificativa e impacto antes de alterar contratos ou backlog.
>
> Fontes: "Plano de Monitoramento da Satisfação dos Clientes — Delpi" (fornecido pelo Comercial) e ata do Transformômetro 2026/016, "Retorno às Demandas Comerciais — Transforma Mais" (06/11/2026, parcialmente assinada). Fonte técnica e owners ainda requerem inventário.

## Como atualizar

Para cada questão: `Status: PENDING | DECIDED | NEEDS_VALIDATION`; `Resposta`; `Owner da decisão`; `Data`; `Justificativa`; `Impacto`; `Fonte`. Resposta do usuário é decisão informada, sujeita à validação do owner quando necessário. Não confundir proposta com aprovação de implementação.

## A. Público, contatos e identificação

### Q01 — Unidade de resposta
**Pergunta:** A pesquisa poderá receber apenas uma resposta por empresa cliente, ou múltiplas respostas de contatos da mesma empresa? Se múltiplas, como representar cada empresa nos indicadores?
**Status:** DECIDED (informado pelo solicitante; validação pelo owner comercial conforme governança).
**Resposta:** Cada empresa cliente terá somente uma resposta por campanha de pesquisa. Não permitir segunda resposta para a mesma empresa na mesma campanha.
**Owner da decisão:** Comercial — validação formal PENDING.
**Data:** 2026-11-10.
**Fonte:** Resposta do solicitante na conversa: "cada empresa cliente só terá uma resposta".
**Justificativa:** Ainda não informada.
**Impacto:** A unidade de contabilização será a empresa cliente por campanha. Convidar mais de um contato, seleção do respondente autorizado, reenvios e eventuais correções da resposta continuam PENDING; não pressupor uma única pessoa de contato ou regra automática de deduplicação por CNPJ.
 
### Q02 — Elegibilidade e amostragem
**Pergunta:** Quais clientes entram em cada campanha (todos os ativos, clientes estratégicos, volume mínimo, período de compra, exclusões)?
**Status:** DECIDED (informado pelo solicitante; validação formal do owner Comercial pendente).
**Resposta:** O público não será fixo. O usuário autorizado selecionará na aplicação as empresas participantes de cada campanha dentre os clientes cadastrados no ERP e consultáveis no Portal Comercial.
**Requisito confirmado em complemento:** Cada empresa selecionada terá um link específico e obrigatório por campanha, vinculado à empresa e às perguntas padronizadas. O usuário poderá copiar esse link e compartilhá-lo por e-mail, WhatsApp ou Teams; deverá existir também opção de disparo direto por e-mail ao contato informado. Ao receber uma resposta, o sistema deverá associá-la ao cliente e à campanha e disponibilizá-la em visão tabular com perguntas e respostas para cálculo dos indicadores. Preservar a regra Q01: uma única resposta por empresa por campanha.
**Data:** 2026-11-10.
**Fonte:** Explicações do solicitante na conversa após Q02 (a segunda explicação substitui a hipótese anterior de link opcional).
**Pendências não inferidas:** permissões de gestão, envio efetivo/integração de e-mail, segurança e ciclo de vida do link, prevenção de resposta duplicada, auditoria, identificação do respondente e tratamento de links compartilhados.
**Impacto:** seleção configurável e registro por empresa/campanha, sem criar novo cadastro paralelo de clientes.

### Q03 — Contatos e fonte canônica
**Pergunta:** De onde virão os contatos e quem poderá manter ou aprovar a lista de destinatários (TOTVS, Portal Comercial, CRM, outra base)?
**Status:** DECIDED quanto à origem dos clientes e preenchimento/edição do contato para o envio; PENDING quanto às permissões específicas e validações técnicas.
**Resposta — cadastro do cliente:** Apenas clientes cadastrados no ERP TOTVS poderão participar. O TOTVS permanece autoridade sobre o cadastro; a seleção deve reutilizar a consulta de clientes já disponível ao Portal Comercial via API DELPI. Cliente inexistente deverá ser cadastrado no ERP pelo fluxo atual. Não haverá cadastro paralelo de empresas na pesquisa.
**Resposta — contato para envio:** Ao selecionar um cliente para a campanha, os campos de contato/e-mail devem ser pré-preenchidos com os dados disponíveis no cadastro consultado. O usuário configurador poderá editar ou informar o e-mail no contexto do convite antes de gerar/enviar o link. A edição desses dados para o convite não cria novo fluxo de cadastro e não implica gravação no ERP; eventual atualização do cadastro mestre permanece no procedimento regular do TOTVS.
**Data:** 2026-11-10.
**Fonte:** Respostas do solicitante à Q03 e complemento: "deixa o campo como editável, mas já traz os dados do cadastro do cliente".
**PENDING / TO_INVENTORY:** Verificar quais campos de contato a rota atual realmente retorna; perfil autorizado a configurar/envios; regras de validação, privacidade, rastreabilidade e armazenamento do destinatário efetivamente utilizado na campanha; escopo de unidades e identidade canônica do cliente.
**Impacto:** Reutilizar a fonte oficial de clientes; evitar duplicação cadastral; permitir contato específico por campanha preservando autoria e rastreabilidade.

### Q04 — Identificação e confidencialidade
**Pergunta:** Respostas serão identificadas, anônimas ou confidenciais com acesso restrito? O cliente será informado do tratamento e finalidade?
**Status:** DECIDED quanto à identificação por empresa e matriz funcional de acesso (informado pelo solicitante; implementação e códigos reais TO_INVENTORY). Política de transparência ao respondente e retenção PENDING.
**Resposta — identificação:** As respostas da pesquisa serão identificadas e vinculadas somente à empresa cliente e à campanha; notas e comentários por empresa serão visíveis apenas aos perfis autorizados. O questionário não deve exigir nem armazenar nome/e-mail da pessoa física que respondeu como identificador da resposta. O e-mail usado para convite é dado operacional de envio, não identificação do respondente. Link compartilhável não comprova identidade pessoal.
**Resposta — perfis:** Criar/estabelecer a permissão proposta `commercial.marketing` para gerir esta frente. O solicitante informa que já existe `commercial.manager`. Ambos os perfis poderão configurar campanhas e seus destinatários, gerar links, disparar convites, consultar respostas individualizadas e tratar os dados/resultados.
**Resposta — demais usuários:** Os outros usuários que têm acesso ao Portal Comercial verão apenas resumo/indicadores agregados; não terão acesso às configurações, disparos, respostas individualizadas, listas restritas de destinatários ou tratamento operacional da pesquisa.
**Fonte:** Resposta do solicitante à Q04 e complemento em 2026-11-10; o plano inicial prevê resultados por cliente e não estabelece identificação nominal do respondente.
**Owner funcional:** Comercial (validação formal PENDING).
**Impacto:** Segregar operações e dados pessoais/sensíveis; verificar autorização em cada endpoint e consulta no backend (filtro apenas no frontend não constitui autorização). O resumo agregado deve evitar identificar indiretamente clientes em grupos muito pequenos.
**TO_INVENTORY:** Confirmar os códigos/semântica atuais de permissões, owners e mecanismo de aplicação no backend, conforme contratos canônicos existentes. `commercial.marketing` é requisito novo, não permissão já implementada; `commercial.manager` é existência relatada, ainda não confirmada por inventário nesta decisão.
**PENDING complementar:** Aviso de privacidade e finalidade ao cliente, política de retenção, auditoria, limiares mínimos para agregações e regras de segmentação que possam revelar respostas individuais. Evitar coleta incidental de identificadores pessoais além do necessário à entrega/segurança do convite.

## B. Campanhas, envio e formulário

### Q05 — Calendário e abertura
**Pergunta:** As duas campanhas semestrais (maio/junho e novembro/dezembro) terão datas fixas ou configuráveis? Quem poderá criá-las, aprová-las, iniciar e encerrar?
**Status:** DECIDED quanto às janelas de referência, configuração livre de datas, abertura e encerramento automáticos; PENDING apenas para detalhes operacionais/técnicos e eventuais aprovações.
**Resposta:** Manter como configuração inicial no banco de dados duas campanhas de referência por ano: primeira em maio/junho e segunda em novembro/dezembro, conforme plano original. Os perfis já autorizados à configuração da pesquisa (`commercial.marketing` e `commercial.manager`, sujeitos à validação técnica) poderão alterar livremente as datas de início e término. Não fixar essas datas no código nem impor obrigatoriamente as janelas originais.
**Abertura automática (DECIDED):** A campanha deverá abrir automaticamente ao alcançar a data de início configurada, sem ativação manual por Marketing/Manager. Antes dessa data, os links não deverão receber respostas. A abertura automática não implica disparo automático de e-mails/convites, que é uma decisão separada.
**Encerramento automático (DECIDED):** A campanha deverá encerrar automaticamente ao atingir a data de término configurada. Após o encerramento, o link não deverá aceitar novas respostas, preservando os dados e indicadores já recebidos. Não exigir ação manual de Marketing/Manager para encerrar. O instante exato de corte e fuso horário devem ser especificados na implementação.
**Natureza:** Requisito de implementação futura; não afirmar que registros ou funcionalidade já existam no banco.
**Fonte:** Concordância explícita do solicitante em 2026-11-10 com datas configuráveis e respostas posteriores: "Não, elas vão encerrar automaticamente" e "Abertura também automática".
**PENDING:** Modelo de recorrência, eventual aprovação de campanha, alterações após início, instante de corte/fuso horário, prazo de consolidação depois do fechamento, validações e auditoria.
**Impacto:** Preservar planejamento semestral com flexibilidade operacional e histórico das datas aplicadas a cada campanha.

### Q06 — Canal de distribuição
**Pergunta:** Qual será o canal inicial (e-mail, WhatsApp, SMS ou combinação), e o envio será manual, assistido ou automático?
**Status:** PENDING
**Resposta:** —
**Impacto:** integração, entregabilidade, auditoria e custos.

### Q07 — Lembretes e tentativas
**Pergunta:** Quantos convites/lembretes podem ser enviados por contato? Quais prazos, expiração e regras para reenvio?
**Status:** PENDING
**Resposta:** —
**Impacto:** status de entrega, prevenção de duplicatas e taxa de resposta.

### Q08 — Obrigatoriedade e não aplicabilidade
**Pergunta:** Quais das 15 perguntas serão obrigatórias? Será permitida resposta "não se aplica", envio parcial ou alteração após envio?
**Status:** PENDING
**Resposta:** —
**Impacto:** experiência e denominadores dos cálculos.

### Q09 — Evolução do questionário
**Pergunta:** As perguntas e escalas serão fixas ou configuráveis por campanha, preservando versão histórica?
**Status:** PENDING
**Resposta:** —
**Impacto:** comparabilidade, modelagem, governança e histórico.

## C. Indicadores e segmentação

### Q10 — Regra oficial de IGS
**Pergunta:** O IGS será a média das respostas individuais à pergunta geral, ou a média primeiro por empresa e depois entre empresas?
**Status:** PENDING
**Resposta:** —
**Impacto:** peso dos clientes e precisão do IGS.

### Q11 — Regra oficial de NPS
**Pergunta:** Confirmar cálculo de NPS: percentual de notas 9–10 menos percentual de notas 0–6, excluindo ausências; como agregar múltiplos contatos?
**Status:** PENDING
**Resposta:** —
**Impacto:** KPI principal; fórmula não está explicitada no documento.

### Q12 — Críticos e satisfeitos
**Pergunta:** As faixas 1–2 (críticos) e 4–5 (satisfeitos) se referem à pergunta geral, a cada dimensão ou a ambas? Qual denominador?
**Status:** PENDING
**Resposta:** —
**Impacto:** alertas e indicadores.

### Q13 — Segmentações oficiais
**Pergunta:** Quais fontes e regras oficiais definirão segmento, região, vendedor/carteira, tempo de relacionamento, faturamento e cliente estratégico? Qual período de referência?
**Status:** PENDING
**Resposta:** —
**Impacto:** filtros, segurança e consistência com Portal Comercial.

### Q14 — Comparação histórica
**Pergunta:** Comparar por campanha anterior, mesmo semestre do ano anterior ou ambos? Como lidar com mudanças de perguntas e composição de clientes?
**Status:** PENDING
**Resposta:** —
**Impacto:** evolução semestral/anual.

## D. Tratamento, ações e governança

### Q15 — Critério e triagem de problemas
**Pergunta:** O que torna uma resposta ou comentário um problema a tratar, quem classifica nas oito categorias e quais situações exigem acompanhamento?
**Status:** PENDING
**Resposta:** —
**Impacto:** fila de trabalho e métricas de criticidade.

### Q16 — Gestão de ações
**Pergunta:** Quem cria e atribui planos de ação, quais etapas/status e critérios de aprovação e conclusão deverão existir?
**Status:** PENDING
**Resposta:** —
**Impacto:** ciclo de correção e indicador de ações concluídas.

### Q17 — Retorno ao cliente
**Pergunta:** Em quais situações é obrigatório responder ao cliente, por qual canal e quem aprova/registra o retorno e a reavaliação?
**Status:** PENDING
**Resposta:** —
**Impacto:** fechamento da jornada e rastreabilidade.

### Q18 — Acesso, retenção e auditoria
**Pergunta:** Quem pode gerir campanhas, destinatários, disparos, respostas individuais, indicadores e ações? Por quanto tempo os dados serão mantidos?
**Status:** PENDING
**Resposta:** —
**Impacto:** LGPD, segurança e controle backend.

## E. Uso do que já existe

### Q19 — Integração e ownership
**Pergunta:** Quais recursos atuais do Portal Comercial/CRM/customer-experience serão reutilizados, e qual API será autoridade de cada dado e regra?
**Status:** TO_INVENTORY (questão técnica; não depende só de entrevista).
**Resposta:** —
**Impacto:** menor implementação suficiente; evitar duplicidade e violação de ownership.

### Q20 — Critérios de sucesso e primeira entrega
**Pergunta:** Como saberemos que a primeira entrega resolveu a necessidade da Qualidade e do Comercial? Quais resultados mínimos devem estar disponíveis antes de iniciar uma campanha real?
**Status:** PENDING
**Resposta:** —
**Impacto:** escopo, teste, homologação e resultado operacional.

## Já definido pelas fontes — não perguntar novamente sem necessidade

- Periodicidade desejada: duas campanhas por ano, janelas maio/junho e novembro/dezembro.
- Conteúdo-base: dez avaliações por dimensão (1–5), uma satisfação geral (1–5), uma recomendação (0–10), três perguntas abertas.
- Indicadores desejados: IGS, NPS, taxa de resposta, médias por dimensão, satisfação/críticos, evolução e ações concluídas.
- Consolidação prevista: até cinco dias após o encerramento.
- Primeira prioridade segundo ata 2026/016: pesquisa de satisfação; prazo de primeira entrega citado como expectativa condicionada, não compromisso.

## Próxima pergunta em entrevista

**Q04** — As respostas serão identificadas pelo cliente/contato ou confidenciais, e quem poderá ver respostas individuais?
