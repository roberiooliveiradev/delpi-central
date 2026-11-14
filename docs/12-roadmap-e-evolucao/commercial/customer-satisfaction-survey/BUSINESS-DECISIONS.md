# Pesquisa de satisfação — Decisões de negócio e registro histórico

> Estado: LEVANTAMENTO PRINCIPAL DE NEGÓCIO CONSOLIDADO (10/11/2026). O documento preserva 20 perguntas, respostas do plano e decisões do solicitante. **Não representa 20 decisões pendentes**, nem prova implementação. Referência central: [índice mestre](./REQUIREMENTS-INDEX.md).
>
> Fontes: "Plano de Monitoramento da Satisfação dos Clientes — Delpi" (fornecido pelo Comercial) e ata do Transformômetro 2026/016, "Retorno às Demandas Comerciais — Transforma Mais" (06/11/2026, parcialmente assinada). Fonte técnica e owners ainda requerem inventário.

## Como consultar e manter

Para cada questão, manter status, resposta, owner, data, justificativa, impacto e fonte. `DECIDED` significa decisão funcional, **não** implementação. Registros `PENDING`/`TO_INVENTORY` referem-se principalmente a detalhes técnicos, segurança ou validações formais; não reabrir a entrevista inteira sem bloqueio real. O [índice mestre](./REQUIREMENTS-INDEX.md) é a entrada principal. A [arquitetura REST/CAIO](./BACKEND-API-PROPOSAL.md) foi aceita em 10/11/2026 e ainda não está implementada.

## Decisão mais recente de 11/11/2026 — produto completo em duas entregas

**Diretriz expressa do solicitante:** tudo o que o *Plano de Monitoramento da Satisfação dos Clientes — Delpi* solicita como processo funcional deverá ser implementado no produto, **em sequência**. A **entrega 1** desenvolve pesquisa, participantes, links manuais, formulário, respostas e indicadores. A **entrega 2** desenvolverá classificação dos problemas, planos de ação, responsável/prazo/status, acompanhamento, retorno aos clientes, reavaliação e indicador de percentual de ações concluídas. **Não descartar nem tratar a segunda entrega como opcional** por não integrar o primeiro ciclo. As decisões de não fazer gestão de planos de ação referiam-se **somente à entrega 1** e ficam superadas se interpretadas como exclusão definitiva. A operação de convites segue manual, sem disparo por e-mail no Portal. Preservar o Word como escopo integral e o [índice mestre](./REQUIREMENTS-INDEX.md) como controle de cobertura; detalhes técnicos da entrega 2 ficam para seu desenvolvimento, sem apagar intenção.

## Atualização de escopo em 11/11/2026 — decisão posterior do solicitante

A primeira entrega deverá permitir **criação de campanhas, escolha de participantes TOTVS, cópia manual de link ou mensagem de convite, formulário público, respostas definitivas e indicadores históricos**. A decisão posterior **revoga** a previsão inicial (Q06/Q07) de envio direto/reenvio de e-mail pelo Portal. **Não haverá envio por integração nem confirmação de entrega**; o usuário fará o envio fora da aplicação. O tratamento e os planos de ação descritos em Q15–Q17 **serão implementados na entrega 2**, não na entrega 1. Até lá, o Comercial poderá conduzir seu trabalho por processo externo, sem isso representar dispensa definitiva do requisito. A nova permissão `commercial.marketing` será tratada durante a implementação; nenhuma outra nova permissão. CAIO e testes deverão acompanhar cada etapa. **Fonte posterior prevalece sobre os textos históricos abaixo.** Contrato: [SURVEY-FIRST-RELEASE-CONTRACT.md](./SURVEY-FIRST-RELEASE-CONTRACT.md).

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
**Requisito confirmado em complemento:** Cada empresa selecionada terá um link específico e obrigatório por campanha, vinculado à empresa e às perguntas padronizadas. O usuário poderá copiar esse link e compartilhá-lo por e-mail, WhatsApp ou Teams; deverá existir também opção de disparo direto por e-mail ao contato informado (cláusula de disparo direto **revogada** pela decisão de 11/11/2026 — envio somente manual, fora do Portal). Ao receber uma resposta, o sistema deverá associá-la ao cliente e à campanha e disponibilizá-la em visão tabular com perguntas e respostas para cálculo dos indicadores. Preservar a regra Q01: uma única resposta por empresa por campanha.
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
**Status:** DECIDED quanto à identificação por empresa e matriz funcional de acesso (informado pelo solicitante; implementação e códigos reais TO_INVENTORY). Política de transparência ao respondente e conformidade jurídica/técnica da retenção histórica ainda requerem validação.
**Resposta — identificação:** As respostas da pesquisa serão identificadas e vinculadas somente à empresa cliente e à campanha; notas e comentários por empresa serão visíveis apenas aos perfis autorizados. O questionário não deve exigir nem armazenar nome/e-mail da pessoa física que respondeu como identificador da resposta. O e-mail usado para convite é dado operacional de envio, não identificação do respondente. Link compartilhável não comprova identidade pessoal.
**Resposta — perfis:** Criar/estabelecer a permissão proposta `commercial.marketing` para gerir esta frente. O solicitante informa que já existe `commercial.manager` (registro literal da entrevista; **o código confirmado no backend é `commercial.manage`** — ver [matriz §4.1 do contrato](./SURVEY-FIRST-RELEASE-CONTRACT.md)). Ambos os perfis poderão configurar campanhas e seus destinatários, gerar links, consultar respostas individualizadas e tratar os dados/resultados. A cláusula original de **disparar convites foi revogada pela decisão de 11/11/2026**: a distribuição é manual, por cópia do link/mensagem, sem envio pela aplicação.
**Resposta — demais usuários:** Os outros usuários que têm acesso ao Portal Comercial verão apenas resumo/indicadores agregados; não terão acesso às configurações, disparos, respostas individualizadas, listas restritas de destinatários ou tratamento operacional da pesquisa.
**Fonte:** Resposta do solicitante à Q04 e complemento em 2026-11-10; o plano inicial prevê resultados por cliente e não estabelece identificação nominal do respondente.
**Owner funcional:** Comercial (validação formal PENDING).
**Impacto:** Segregar operações e dados pessoais/sensíveis; verificar autorização em cada endpoint e consulta no backend (filtro apenas no frontend não constitui autorização). O resumo agregado deve evitar identificar indiretamente clientes em grupos muito pequenos.
**TO_INVENTORY:** Confirmar os códigos/semântica atuais de permissões, owners e mecanismo de aplicação no backend, conforme contratos canônicos existentes. `commercial.marketing` é requisito novo, não permissão já implementada. `commercial.manager` era existência relatada nesta decisão; **a auditoria de 11/11/2026 confirmou `commercial.manage` como o código real** (`commercial_permissions.py`, manifest), sendo `commercial.manager` o termo legado usado na entrevista — ver [matriz §4.1](./SURVEY-FIRST-RELEASE-CONTRACT.md).
**Complemento decidido em 2026-11-10:** O solicitante definiu manutenção histórica por tempo indeterminado, sem prazo fixo de exclusão programada, para comparação plurianual; o estado da pesquisa pertence ao escopo da API Comercial. Não equivale a autorização irrestrita de conservação de dados pessoais: finalidade, minimização, proteção, atendimento a direitos dos titulares e revisão de conformidade LGPD permanecem requisitos de governança. **TO_INVENTORY:** mecanismos de auditoria, limiares mínimos para agregações e regras de segmentação que possam revelar respostas individuais. Evitar coleta incidental de identificadores pessoais além do necessário à entrega/segurança do convite.

## B. Campanhas, envio e formulário

### Q05 — Calendário e abertura
**Pergunta:** As duas campanhas semestrais (maio/junho e novembro/dezembro) terão datas fixas ou configuráveis? Quem poderá criá-las, aprová-las, iniciar e encerrar?
**Status:** DECIDED quanto às janelas de referência, configuração livre de datas, abertura e encerramento automáticos; PENDING apenas para detalhes operacionais/técnicos e eventuais aprovações.
**Resposta:** Manter como configuração inicial no banco de dados duas campanhas de referência por ano: primeira em maio/junho e segunda em novembro/dezembro, conforme plano original. Os perfis já autorizados à configuração da pesquisa (`commercial.marketing` e `commercial.manage` — código confirmado; `commercial.marketing` ainda a criar) poderão alterar livremente as datas de início e término. Não fixar essas datas no código nem impor obrigatoriamente as janelas originais.
**Abertura automática (DECIDED):** A campanha deverá abrir automaticamente ao alcançar a data de início configurada, sem ativação manual por Marketing/Manage. Antes dessa data, os links não deverão receber respostas. A abertura automática não implica disparo automático de e-mails/convites, que é uma decisão separada.
**Encerramento automático (DECIDED):** A campanha deverá encerrar automaticamente ao atingir a data de término configurada. Após o encerramento, o link não deverá aceitar novas respostas, preservando os dados e indicadores já recebidos. Não exigir ação manual de Marketing/Manage para encerrar. O instante exato de corte e fuso horário devem ser especificados na implementação.
**Natureza:** Requisito de implementação futura; não afirmar que registros ou funcionalidade já existam no banco.
**Fonte:** Concordância explícita do solicitante em 2026-11-10 com datas configuráveis e respostas posteriores: "Não, elas vão encerrar automaticamente" e "Abertura também automática".
**PENDING:** Modelo de recorrência, eventual aprovação de campanha, alterações após início, instante de corte/fuso horário, prazo de consolidação depois do fechamento, validações e auditoria.
**Impacto:** Preservar planejamento semestral com flexibilidade operacional e histórico das datas aplicadas a cada campanha.

### Q06 — Canal de distribuição
**Pergunta:** Qual será o canal inicial (e-mail, WhatsApp, SMS ou combinação), e o envio será manual, assistido ou automático?
**Status:** SUPERSEDED pela decisão de 11/11/2026 — envio somente manual, por cópia de link/mensagem; sem integração de e-mail.
**Resposta histórica (10/11/2026, registro superado):** O Portal Comercial deverá oferecer envio direto de convite exclusivamente por e-mail para o contato configurável da empresa cliente. Também deverá permitir copiar o link exclusivo por cliente/campanha para compartilhamento manual pelo usuário em WhatsApp, Microsoft Teams, e-mail externo ou outros canais. Não incluir integrações de disparo direto por WhatsApp ou Teams neste escopo.
**Decisão final (11/11/2026, vigente):** **sem envio de mensagens pelo Portal** — nenhum envio de e-mail, WhatsApp, Teams ou outro canal pela aplicação; **sem integração de disparo**; o usuário autorizado **copia manualmente** o convite/link resolvido e **compartilha externamente** pelo canal de sua escolha. Não implementar rastreamento de envio, comprovação de entrega nem status Enviado/Entregue.
**Distinção importante:** Abertura automática de campanha (Q05) não significa envio automático de convites; nenhum disparo em lote, agendado ou automático foi aprovado nesta decisão. A previsão histórica de acionamento de envio direto pelo usuário autorizado foi revogada pela decisão final acima.
**Fonte:** Resposta do solicitante em 2026-11-10: "Concordo com você", à proposta de envio direto apenas por e-mail e cópia manual para outros canais. Revogação registrada em 11/11/2026.
**Owner funcional:** Comercial; permissão de gestão conforme Q04 (`commercial.marketing` e `commercial.manage`), a validar tecnicamente.
**PENDING / TO_INVENTORY (revistos após 11/11):** formato do convite (parcialmente definido nas decisões de mensagem padrão da UI-02), disponibilidade do link conforme janela de campanha, segurança do token/link e tratamento dos contatos conforme Q03. As pendências de serviço de envio de e-mail e de rastreamento de envio/erro/entrega foram eliminadas junto com o disparo.
**Impacto:** Menor número de integrações, preservando a escolha de canal de contato pelo usuário fora do Portal. A rastreabilidade possível do envio direto por e-mail deixou de existir com a revogação.

### Q07 — Lembretes e tentativas
**Pergunta:** Quantos convites/lembretes podem ser enviados por contato? Quais prazos, expiração e regras para reenvio?
**Status:** SUPERSEDED quanto ao reenvio direto — o usuário recopia e encaminha o mesmo link externamente, sem disparo no Portal.
**Resposta (histórico 10/11, vigência ajustada em 11/11):** Usuários autorizados por `commercial.marketing` ou `commercial.manage` poderão visualizar empresas que ainda não responderam e **recopiar manualmente** o convite. A recópia utiliza o mesmo link exclusivo da empresa na campanha, sem criar outro link nem permitir uma segunda resposta. Não implementar lembretes automáticos por prazo ou intervalo. A expressão "reenvio" é apenas operacional: **a aplicação não envia nada** — o usuário recopia o link/mensagem e compartilha externamente.
**Fonte:** Resposta expressa do solicitante em 2026-11-10: "Manual", após a proposta de reenvio manual de convites aos clientes pendentes com o mesmo link.
**Condições (ajustadas após 11/11):** A validade do link continua restrita às datas da campanha (Q05); não há envio direto pelo Portal em nenhum canal — ver decisão final da Q06.
**PENDING (revistos):** Limites de recópias/tentativas, eventual aviso sobre frequência excessiva, registro e auditoria das recópias e detalhes de permissões no backend. A pendência de comprovação de entrega de e-mail foi eliminada com a revogação do envio direto; permanecem pendências legítimas de segurança do link (proteção do token, validade e auditoria de acesso).
**Impacto:** Fluxo operacional simples, sem automação de lembretes; identificação de pendências por empresa e prevenção de respostas duplicadas.

### Q08 — Obrigatoriedade e não aplicabilidade
**Pergunta:** Quais das 15 perguntas serão obrigatórias? Será permitida resposta "não se aplica", envio parcial ou alteração após envio?
**Status:** DECIDED quanto à seleção obrigatória de uma alternativa em cada dimensão, opção "Não se aplica" e edição após submissão final; rascunhos interrompidos permanecem restritos à sessão do formulário conforme contrato da entrega 1.
**Resposta:** Das 15 perguntas padronizadas do plano, tornar obrigatórias somente a pergunta de satisfação geral (escala 1–5, base do IGS) e a pergunta de recomendação (escala 0–10, base do NPS). Nas dez perguntas de avaliação por dimensão (1–5), permitir a opção "Não se aplica", sem exigir uma nota numérica em todos os casos. As três perguntas abertas serão opcionais.
**Regra para indicadores:** "Não se aplica" não representa nota zero nem nota neutra; excluir esses registros do cálculo da média da respectiva dimensão e informar o número de respostas válidas no indicador. As perguntas obrigatórias precisam ser respondidas para a submissão final.
**Fonte:** Resposta do solicitante em 2026-11-10: "Concordo com a regra", em resposta à proposta explícita de duas perguntas obrigatórias, opção "Não se aplica" nas dez avaliações e três abertas opcionais.
**Decisão complementar — alteração após envio (pergunta 10 da entrevista, distinta da Q10 de IGS abaixo):** O cliente poderá revisar e modificar as respostas antes da submissão final. Após clicar em "Enviar" e a submissão ser concluída, a resposta será definitiva: não poderá ser alterada, inclusive enquanto a campanha permanecer aberta. Preservar uma única resposta por empresa/campanha (Q01). Fonte: concordância explícita do solicitante em 2026-11-10. Owner: Comercial (validação formal PENDING). Trata-se de requisito futuro, não de comportamento implementado comprovado.
**Decisão complementar de 11/11/2026 (solicitante):** **Nenhuma das dez dimensões pode permanecer sem seleção no envio definitivo.** Cada dimensão exige uma escolha explícita: **nota inteira de 1 a 5 OU “Não se aplica”**. Não exigir necessariamente nota numérica, mas exigir escolha. Na representação técnica da resposta definitiva, `null` corresponde exclusivamente à opção “Não se aplica” selecionada, nunca a pergunta ignorada. O formulário deve impedir confirmação se faltar qualquer seleção e a `commercial-api` deve rejeitar payload sem dimensão ou com escolha não resolvida. Rascunho interrompido antes do envio não é resposta definitiva e segue o contrato de estado local da primeira entrega. **Fonte:** esclarecimento explícito do solicitante em 11/11/2026, posterior à Q08 original. **Impacto:** fecha o gate da ambiguidade entre “Não se aplica” e “não respondido”; formalização do owner Comercial ainda segue pendente como nas demais decisões.
**Impacto:** Mantém IGS e NPS com notas válidas e evita distorcer avaliações de assuntos não conhecidos pelo cliente, preservando resposta única por empresa/campanha (Q01).

### Q09 — Evolução do questionário
**Pergunta:** As perguntas e escalas serão fixas ou configuráveis por campanha, preservando versão histórica?
**Status:** DECIDED (informado pelo solicitante; validação formal do owner Comercial PENDING).
**Resposta:** As 15 perguntas do plano original serão o questionário oficial, mantendo texto, ordem e quantidade iguais em todas as campanhas. Não permitir personalização desses elementos por campanha. Preservar as regras de obrigatoriedade e "Não se aplica" definidas em Q08.
**Fonte:** Concordância explícita do solicitante à pergunta 9 da entrevista, em 2026-11-10.
**Owner da decisão:** Comercial — validação formal PENDING.
**Data:** 2026-11-10.
**Complemento de conferência documental (11/11/2026):** as 15 perguntas literais e a ordem das seções 3–6 do Word foram conferidas e transcritas no [catálogo da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md#14-catálogo-textual-canônico-das-15-perguntas--conferência-com-o-word-em-11112026), associadas às chaves técnicas existentes. **Gate textual FECHADO (15/15).** A criação do identificador técnico concreto de `questionnaire_version` e sua verificação em API, banco, telas e histórico permanecem **PENDING**. Não reabrir a Q09 funcional para decidir novamente textos fixos ou personalização por campanha.
**Justificativa:** Garantir comparabilidade entre campanhas.
**Impacto:** Questionário padronizado e comparabilidade histórica; detalhes técnicos de versionamento e contratos permanecem TO_INVENTORY.

## C. Indicadores e segmentação

### Q10 — Regra oficial de IGS
**Pergunta:** O IGS será a média das respostas individuais à pergunta geral, ou a média primeiro por empresa e depois entre empresas?
**Status:** DECIDED (pergunta 11 da entrevista; decisão informada pelo solicitante; validação formal do owner Comercial PENDING).
**Resposta:** Calcular o IGS como a média aritmética simples das notas da pergunta obrigatória de satisfação geral (escala 1–5), considerando uma resposta por empresa participante da campanha. Cada empresa tem peso igual, sem ponderação por faturamento, porte ou importância comercial. Exemplo: notas 3, 4 e 5 resultam em IGS 4,0. Não confundir com média das dez dimensões.
**Fonte:** Concordância explícita do solicitante em 2026-11-10 à proposta da pergunta 11 da entrevista.
**Owner da decisão:** Comercial — validação formal PENDING.
**Data:** 2026-11-10.
**Justificativa:** Indicador simples e comparável entre empresas e campanhas.
**Contexto interpretativo do Word (§4):** “Mais importante do que estabelecer uma 'nota ideal' é acompanhar a evolução do indicador e identificar quais clientes ou dimensões estão deteriorando.” O objetivo é acompanhar variações ao longo do tempo, **não** impor meta/semáforo automático, nem divulgar respostas identificáveis a quem só tem `commercial.access`. A comparação depende das campanhas e bases oficiais disponíveis.
**Impacto:** Peso igual por empresa e cálculo a partir das notas gerais válidas; contratos e implementação permanecem TO_INVENTORY.

### Q11 — Regra oficial de NPS
**Pergunta:** Confirmar cálculo de NPS: percentual de notas 9–10 menos percentual de notas 0–6, excluindo ausências; como agregar múltiplos contatos?
**Status:** DECIDED (pergunta 12 da entrevista; decisão informada pelo solicitante, validação formal do owner Comercial PENDING).
**Resposta:** Adotar a fórmula padrão de NPS: promotores = notas 9–10; neutros = 7–8; detratores = 0–6. NPS em pontos = percentual de empresas promotoras menos percentual de empresas detratoras, usando como denominador todas as respostas válidas, inclusive as neutras. Cada empresa tem peso igual, uma resposta por empresa/campanha, sem ponderação por faturamento, porte ou importância comercial. Exemplo: 60% promotores, 20% neutros, 20% detratores = NPS +40.
**Fonte:** Concordância explícita do solicitante em 2026-11-10 à proposta da pergunta 12 da entrevista.
**Owner da decisão:** Comercial — validação formal PENDING.
**Data:** 2026-11-10.
**Leitura conjunta prevista pelo Word (§5):** satisfação geral mede a experiência atual; NPS mede a disposição de recomendar; perguntas dimensionais explicam por que o cliente está satisfeito ou insatisfeito. É uma **orientação analítica**, não autorização para o frontend calcular novos índices ou diagnosticar causas automaticamente. A interpretação é apoiada nos indicadores canônicos da API.
**Impacto:** Indicador comparável entre campanhas; implementação e contratos técnicos TO_INVENTORY.

### Q12 — Críticos e satisfeitos
**Pergunta:** As faixas 1–2 (críticos) e 4–5 (satisfeitos) se referem à pergunta geral, a cada dimensão ou a ambas? Qual denominador?
**Status:** DECIDED quanto à aplicação simples da classificação (pergunta 13 da entrevista; validação formal do owner Comercial PENDING).
**Resposta:** Aplicar as faixas 1–2 (críticos) e 4–5 (satisfeitos) somente à pergunta obrigatória de satisfação geral (escala 1–5); nota 3 fica como faixa intermediária, sem atribuir ao plano original nomenclatura não comprovada. Calcular os percentuais com denominador igual ao total de empresas com resposta válida à satisfação geral na campanha, uma resposta por empresa. Nas dez dimensões, mostrar apenas médias das notas válidas e suas quantidades, sem classificar individualmente clientes como críticos ou satisfeitos por dimensão. 'Não se aplica' não entra nas médias das dimensões.
**Fonte:** Escolha explícita do solicitante em 2026-11-10 pelo 'caminho de fluxo simples', em resposta à alternativa de classificar apenas a satisfação geral ou também as dez dimensões. A aplicação somente à geral é a interpretação operacional mais simples dessa escolha.
**Owner da decisão:** Comercial — validação formal PENDING.
**Data:** 2026-11-10.
**Impacto:** Indicadores enxutos e comparáveis, sem duplicação de classificações. Implementação futura, não estado atual comprovado.

### Q13 — Segmentações oficiais
**Pergunta:** Quais fontes e regras oficiais definirão segmento, região, vendedor/carteira, tempo de relacionamento, faturamento e cliente estratégico? Qual período de referência?
**Status:** SOURCE_DEFINED quanto às sete segmentações; TO_INVENTORY quanto à fonte e às regras técnicas de cada atributo.
**Resposta pelo plano:** Analisar os resultados por cliente, segmento, vendedor, região, tempo de relacionamento, volume/faturamento da conta e clientes estratégicos versus demais clientes. O documento inclui exemplo de tabela comparativa com colunas Geral, Clientes estratégicos e Demais clientes para satisfação geral e médias por dimensão (seção 7, página 3). Não é necessária nova decisão do solicitante sobre QUAIS filtros deseja.
**PENDING / TO_INVENTORY:** Localizar autoridade e disponibilidade dos campos nas APIs/cadastro existentes, como determinar cliente estratégico e período de referência para atributos variáveis; não criar classificação ou fonte paralela.
**Natureza:** Fonte de requisito de negócio, não evidência de que filtros e integrações estejam implementados.
**Impacto:** Reaproveitar dados existentes e apresentar comparações simples sem novas dimensões inventadas.
### Q14 — Comparação histórica
**Pergunta:** Comparar por campanha anterior, mesmo semestre do ano anterior ou ambos? Como lidar com mudanças de perguntas e composição de clientes?
**Status:** SOURCE_DEFINED para comparação com pesquisa anterior e visão semestral/anual; PENDING apenas para critérios técnicos de comparação com públicos diferentes.
**Resposta pelo plano:** Mostrar evolução semestral/anual e comparação dos indicadores com a pesquisa anterior (seções 8 e 9, página 4). A decisão de manter as quinze perguntas iguais entre campanhas já está registrada em Q09.
**PENDING / TO_INVENTORY:** Tratamento de campanhas com composição diferente de empresas, períodos sem resposta e bases insuficientes; não presumir comparação individual ou mesmo semestre do ano anterior como requisito separado.
**Impacto:** Uma evolução histórica simples atende ao plano sem multiplicar modos de comparação.
## D. Tratamento, ações e governança

### Q15 — Critério e triagem de problemas
**Pergunta:** O que torna uma resposta ou comentário um problema a tratar, quem classifica nas oito categorias e quais situações exigem acompanhamento?
**Status:** SOURCE_DEFINED quanto às oito categorias; DECIDED quanto aos perfis responsáveis pelo tratamento; PENDING apenas para critérios de relevância e detalhes operacionais.
**Resposta pelo plano:** Cada problema identificado deve ser classificado como Produto, Qualidade, Entrega, Atendimento, Comercial, Técnico, Comunicação ou Preço (seção 8, etapa 2, página 4). A consolidação deve listar principais comentários e clientes críticos em até cinco dias após o encerramento (etapa 1).
**Responsabilidade DECIDED:** O tratamento da pesquisa, incluindo triagem e classificação, cabe aos usuários autorizados por `commercial.marketing` ou `commercial.manage`, conforme decisão do solicitante em 2026-11-10. O plano não estabelece critério automático para transformar notas/comentários em problemas: não inventar detecção automática ou nova aprovação.
**Finalidade adicional expressa no Word (§6):** a terceira pergunta aberta (“Existe alguma necessidade ou expectativa que a Delpi ainda não esteja atendendo?”) pode revelar **novas oportunidades comerciais, técnicas e de relacionamento**. Preservar a informação na leitura e na consolidação da entrega 1; eventual encaminhamento e tratamento integram a entrega 2, com avaliação humana de relevância, sem gerar automaticamente uma oportunidade ou classificação.
**Impacto:** Reutilizar oito categorias do plano, sem inventar novas categorias ou automação.
### Q16 — Gestão de ações
**Pergunta:** Quem cria e atribui planos de ação, quais etapas/status e critérios de aprovação e conclusão deverão existir?
**Status:** SOURCE_DEFINED quanto aos campos mínimos; DECIDED quanto aos perfis com responsabilidade de gestão; PENDING para enumerações/status e procedimentos não especificados.
**Resposta pelo plano:** Para cada oportunidade relevante, manter Problema, Cliente, Causa, Ação, Responsável, Prazo e Status (seção 8, etapa 3, página 4). Na estrutura do CRM também estão previstos plano de ação, responsável pela ação, prazo, status e reavaliação (seção 10, páginas 4–5). O painel mostra ações concluídas ÷ ações identificadas (seção 9).
**Responsabilidade DECIDED:** Usuários autorizados por `commercial.marketing` ou `commercial.manage` gerem o tratamento, podendo registrar, atribuir e acompanhar ações, conclusões e reavaliações no escopo da pesquisa. O responsável indicado em cada ação é um campo operacional do plano, não uma terceira permissão de gestão. **PENDING técnico/operacional:** Valores de status e critérios simples de conclusão ainda não estão definidos; não inferir workflow de aprovação complexo.
**Impacto:** Um registro simples de ações com seus campos pode ser a menor solução suficiente, após inventário de eventual recurso existente.
### Q17 — Retorno ao cliente
**Pergunta:** Em quais situações é obrigatório responder ao cliente, por qual canal e quem aprova/registra o retorno e a reavaliação?
**Status:** SOURCE_DEFINED quanto ao público-alvo do retorno; DECIDED quanto aos perfis responsáveis por acompanhar o retorno; PENDING quanto ao canal operacional.
**Resposta pelo plano:** Prever retorno aos clientes com críticas relevantes, inclusive com texto-modelo informando recebimento da avaliação e ações em andamento (seção 8, etapa 4, página 4). Registrar reavaliação no acompanhamento (seção 10, página 5).
**Responsabilidade DECIDED:** O tratamento e acompanhamento do retorno ao cliente competem aos usuários autorizados por `commercial.marketing` ou `commercial.manage`, segundo decisão de 2026-11-10. **PENDING:** Canal efetivo de retorno e detalhes de registro. O texto-modelo não autoriza envio automático, não define prazo específico e não pressupõe uma aprovação adicional.
**Texto-modelo literal do Word (§8, etapa 4), apenas referência de comunicação:**

> “Recebemos sua avaliação e identificamos alguns pontos que merecem atenção. Gostaríamos de apresentar as ações que estamos conduzindo para melhorar sua experiência com a Delpi.”

É **exemplo**, não template aprovado para envio automático, não prova de ações já iniciadas e não obriga a mensagem padronizada. O contato efetivo, pelo canal definido pelo Comercial, integra a entrega 2.

**Sequência operacional de referência (§10 do Word):** Cliente → Pesquisa enviada → Data da pesquisa → Responsável → IGS → NPS → Notas por dimensão → Comentários → Pontos críticos → Plano de ação → Responsável pela ação → Prazo → Status → Reavaliação. **Interpretação de implantação:** a entrega 1 registra campanha, participante, resposta e dados/indicadores; a entrega 2 registra tratamento, ação, acompanhamento e reavaliação. “Pesquisa enviada” é redação do Word, **não prova de convite efetivamente entregue** no processo atual de cópia manual; IGS e NPS são resultados agregados, não pontuações individuais da resposta. A lista descreve rastreabilidade operacional, não impõe uma tela ou tabela única.

**Impacto:** Fechar o ciclo com o cliente sem criar integração adicional sem necessidade.
### Q18 — Acesso, retenção e auditoria
**Pergunta:** Quem pode gerir campanhas, destinatários, disparos, respostas individuais, indicadores e ações? Por quanto tempo os dados serão mantidos?
**Status:** DECIDED quanto aos perfis de gestão e à intenção de retenção histórica por tempo indeterminado; TO_INVENTORY quanto à execução das regras de segurança, auditoria e validação LGPD.
**Resposta pelo plano:** O plano descreve resultados e acompanhamento por cliente, mas não fixa permissões, retenção, auditoria ou regra de divulgação de respostas individualizadas (seções 7–10). A decisão complementar informada pelo solicitante em Q04 restringe configuração/envios/respostas individualizadas a `commercial.marketing` e `commercial.manage` e libera apenas indicadores agregados aos demais usuários do Portal Comercial.
**Decisão complementar (2026-11-10):** Guardar pesquisas e respostas historicamente por tempo indeterminado em tabelas no domínio da API Comercial para acompanhar a evolução da DELPI ao longo dos anos; não estabelecer exclusão automática por prazo fixo por simples conveniência técnica. **TO_INVENTORY:** Contratos reais das permissões, armazenamento em schema de responsabilidade comercial, proteção dos convites/links, auditoria, segregação de acesso e limiares de agregação. **Governança:** Validar finalidade, base legal, transparência, minimização, segurança, direitos dos titulares e revisão periódica da necessidade de retenção, conforme LGPD. A decisão funcional não dispensa conformidade nem constitui prova de implementação; backend permanece autoridade.
**Impacto:** Preservar a matriz funcional decidida sem atribuir ao plano regra que ele não traz.
## E. Uso do que já existe

### Q19 — Integração e ownership
**Pergunta:** Quais recursos atuais do Portal Comercial/CRM/customer-experience serão reutilizados, e qual API será autoridade de cada dado e regra?
**Status:** DECIDED quanto ao domínio proprietário futuro e à estratégia de inventário incremental; TO_INVENTORY quanto a contratos, código e recursos reais.
**Resposta pelo plano:** A seção 10, páginas 4–5, lista campos de acompanhamento no CRM: pesquisa enviada, data, responsável, IGS, NPS, notas por dimensão, comentários, pontos críticos, plano de ação, responsável, prazo, status e reavaliação. O solicitante já informou que a primeira solução será no Portal Comercial existente e reutilizará clientes do ERP TOTVS via API DELPI (Q03).
**Decisão complementar (2026-11-10):** Persistência das campanhas, convites, respostas e acompanhamentos no escopo de dados e regras da API Comercial, em tabelas/esquemas sob sua responsabilidade; não criar autoridade cadastral paralela ao TOTVS. Inventário técnico será incremental, realizado antes de cada frente de desenvolvimento de rotas, modelos e interface, e não exigido como uma grande fase documental separada. **TO_INVENTORY por frente:** Confirmar HEAD, branch e working tree; fonte canônica e owner; contratos/consumidores; rotas de clientes, formulários e ações reutilizáveis; permissões backend; testes e comportamento comprovado. Não assumir estrutura física, endpoints ou capacidades antes dessa verificação.
**Impacto:** Evitar cadastro paralelo, CRUD duplicado e deslocamento de regras para o frontend.
### Q20 — Critérios de sucesso e primeira entrega
**Pergunta:** Como saberemos que a primeira entrega resolveu a necessidade da Qualidade e do Comercial? Quais resultados mínimos devem estar disponíveis antes de iniciar uma campanha real?
**Status:** SOURCE_DEFINED quanto aos resultados esperados e ao prazo de consolidação; PENDING quanto à homologação formal e escopo exato de uma primeira entrega.
**Resposta pelo plano:** Monitorar IGS, NPS, taxa de resposta (respondentes ÷ convidados), médias por dimensão, percentuais satisfeitos (4–5) e críticos (1–2), evolução semestral/anual, planos de ação concluídos (concluídos ÷ identificados); consolidar em até cinco dias após a pesquisa, incluindo comentários e clientes críticos (seções 8–9, página 4). O processo proposto também cobre classificação, ação e retorno aos clientes com críticas relevantes.
**PENDING:** Owner e aceitação formal, evidência de medição do prazo, indicadores mínimos da primeira entrega e testes de segurança/operacionais. Não interpretar o prazo como SLA de processamento automático em tempo real.
**Impacto:** Base objetiva para critérios de aceite, sem aprovação automática de backlog técnico.
## Já definido pelas fontes — não perguntar novamente sem necessidade

- Periodicidade desejada: duas campanhas por ano, janelas maio/junho e novembro/dezembro.
- Conteúdo-base: dez avaliações por dimensão (1–5), uma satisfação geral (1–5), uma recomendação (0–10), três perguntas abertas.
- Indicadores desejados: IGS, NPS, taxa de resposta, médias por dimensão, satisfação/críticos, evolução e ações concluídas.
- Consolidação prevista: até cinco dias após o encerramento.
- Primeira prioridade segundo ata 2026/016: pesquisa de satisfação; prazo de primeira entrega citado como expectativa condicionada, não compromisso.

## Encaminhamento do levantamento

**Encaminhamento após decisões complementares de 2026-11-10:** Não perguntar novamente sobre segmentações, evolução, categorias, campos de ação, tratamento por Marketing/Manage, retenção histórica ou escopo de persistência na API Comercial. Prosseguir com especificação funcional baseada no plano e decisões do solicitante. Executar inventário técnico bounded por frente imediatamente antes de projetar/implementar rotas, dados e interface; esclarecer somente lacunas materiais para as quais não haja decisão ou contrato canônico. Nenhuma implementação está comprovada ou autorizada por este documento.
