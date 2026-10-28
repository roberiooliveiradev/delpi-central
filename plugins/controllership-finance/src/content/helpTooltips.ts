/**
 * Textos dos balões de explicação (HelpTooltip / SectionCard.hint / titleHint).
 * Fonte única — ajuda contextual desta entrega (IMP-MFE-HOME), sem CMS.
 */

export const CF_HELP = {
  shell: {
    portal:
      "Portal Controladoria & Finanças: Início com saudação, contexto operacional e acesso às áreas do produto.",
    navHome:
      "Início: saudação, contexto operacional, busca de caminhos e catálogo das áreas do portal.",
  },
  home: {
    overview:
      "Saudação personalizada e destaques do contexto operacional. Indicadores aparecem como indisponíveis quando a origem de dados ainda não está conectada — «—» nunca significa zero confirmado.",
    context:
      "Contexto operacional do seu dia na Controladoria & Finanças. Nesta versão, a Central de Fechamento ainda não está conectada — as seções mostram o estado honesto de cada fonte.",
    events:
      "Eventos e interações do seu dia: tarefas e alertas operacionais. Nesta versão ainda não há fontes conectadas — quando existirem, aparecem aqui sem precisar recarregar.",
    shortcuts:
      "Caminhos por seção do portal. Busque aqui, no botão Buscar da barra superior ou com Ctrl/Cmd+K — o objetivo é chegar à ação em até dois cliques.",
    search:
      "Filtra seções e rotas do catálogo (rótulo e palavras-chave). A URL guarda ?q= para compartilhar o filtro.",
    palette:
      "Busca rápida do portal: botão Buscar na barra superior ou Ctrl/Cmd+K. Mesmo catálogo do Início, em popover ancorado à barra.",
    recents:
      "Últimos caminhos abertos neste portal — guardados só neste navegador, sem dados sensíveis.",
  },
  claraConsent: {
    page:
      "Autorização verificável: o plano que a CLARA preparou só executa depois do seu clique aqui. Esta página mostra o plano selado por inteiro — o que você vê é exatamente o que será autorizado — e devolve ao servidor a autorização emitida no preparo, com sessão renovada. Responder «sim» no chat não autoriza nada.",
    batch:
      "O lote inteiro é autorizado de uma vez: revise cada operação — descrição, efeito, motivo, dependências e impedimentos. Operações bloqueadas aparecem como bloqueadas e não são autorizadas. O plano não pode ser ampliado depois.",
    proposal:
      "Revise a operação exata — descrição, efeito, motivo e validade — antes de autorizar; depois peça a execução na conversa com a CLARA.",
  },
  closing: {
    page:
      "Baixas financeiras: eventos de baixa a pagar e a receber do ERP, com filtros de período, natureza e tipo de movimento. Valores são agrupados por moeda — nunca somados entre moedas — e não representam fechamento contábil oficial.",
    side:
      "Alterne entre baixas a pagar (fornecedores) e baixas a receber (clientes). Os mesmos filtros se aplicam às duas visões.",
    filters:
      "Período é obrigatório. A consulta é automática: ao alterar qualquer filtro válido os resultados se atualizam sem botão — campos digitáveis aguardam uma breve pausa na digitação. Natureza e tipo de movimento usam os códigos de origem do ERP — ainda sem classificação contábil nesta versão.",
    summary:
      "Resumo exploratório do período: quantidade de eventos, valores por moeda e qualidade dos vínculos. Não é total oficial de fechamento.",
    table:
      "Detalhe dos eventos de baixa. A contagem junto ao título mostra o universo filtrado, não apenas a página atual. Em «Colunas» você escolhe quais campos exibir, em «Fonte» ajusta o tamanho do texto e a borda direita de cada cabeçalho permite redimensionar a coluna — as preferências ficam gravadas no seu usuário. «Filial não identificada» significa que a origem não informa a filial do registro — não é erro nem filial 01/02.",
    linkStatus:
      "Situação do vínculo: indica quando o documento ou a natureza financeira de origem não foi localizado, preservando o evento em vez de escondê-lo.",
    pagination: {
      pageSize: "Quantidade de eventos exibidos por página.",
      previous: "Página anterior.",
      next: "Próxima página.",
      info: "Faixa exibida e total de eventos do filtro atual.",
      jump: "Ir diretamente para uma página.",
      jumpEmpty: "Informe o número da página.",
      jumpInvalid: "Use apenas números.",
      jumpBelowMin: "A página mínima é 1.",
    },
  },
  stockInventory: {
    page:
      "Estoque histórico — P7: consulta operacional dos saldos de estoque registrados no fechamento de cada mês no ERP. Os resultados ainda não equivalem ao relatório oficial MATR460 — use-os como consulta de apoio ao fechamento, não como documento oficial.",
    filters:
      "Competência é obrigatória e sempre aponta para o último dia do mês. A consulta é automática: ao alterar qualquer filtro válido os resultados se atualizam sem botão — Armazém aguarda uma breve pausa na digitação. Filial é apenas filtro de dados — Matriz (01), Filial 02 ou Todas — sem alterar permissões. Visão restringe os tipos de produto; Armazém usa o código de origem do ERP.",
    indicators:
      "Valor histórico total e quantidade de itens calculados sobre todo o universo do filtro, não apenas a página exibida. Quando o snapshot do mês não existe na origem, o total não é exibido — ausência nunca aparece como zero.",
    status:
      "Disponibilidade da origem: «Disponível» = snapshot encontrado; «Parcial» = alguma filial solicitada não tem snapshot no mês; «Não encontrado» = o ERP não gravou fechamento de estoque para a competência; «Sem itens» = o snapshot existe mas os filtros não retornaram registros. Estados de acesso: «Acesso restrito» = seu usuário não possui a permissão do Portal; «Consulta ainda não habilitada» = a liberação do conjunto de dados está desativada no ambiente; «Integração de dados pendente» = a credencial técnica entre o Portal e a origem ainda aguarda autorização — acione o suporte.",
    summaryType:
      "Totais por tipo de produto (MP, PI, PA e demais) sobre o universo filtrado, com a participação percentual de cada grupo no valor histórico total.",
    summaryWarehouse:
      "Totais por armazém e filial sobre o universo filtrado, com a participação percentual de cada grupo no valor histórico total.",
    table:
      "Detalhamento por produto e armazém no snapshot do mês, com a contagem do universo filtrado junto ao título. Ordenação fixa por filial, armazém e produto. Em «Colunas» você escolhe campos, em «Fonte» ajusta o texto e a borda direita de cada cabeçalho redimensiona a coluna — preferências gravadas no seu usuário. Quando o snapshot não existe para a competência, só o aviso é exibido — a tabela vazia não representaria saldo zero.",
  },
  checklist: {
    page:
      "Checklist da competência: itens esperados do fechamento mensal conforme a versão publicada do checklist. Cada competência guarda um snapshot próprio — publicar uma versão nova nunca altera meses já abertos. «Esperado» significa item previsto para entrega — não indica documento entregue, recebido ou validado.",
    competence:
      "Competência no formato AAAA-MM. Ao abrir um fechamento, o Portal copia os itens do checklist publicado e vigente naquele momento; se ainda não existir versão publicada, o fechamento abre mesmo assim, com a lista de exigências vazia — a repetição nunca duplica a abertura.",
    open:
      "Abrir o fechamento copia os itens da versão publicada do checklist para o mês escolhido. Quando não há versão publicada, a abertura acontece mesmo assim e a lista começa vazia — estado legítimo, não erro. Itens publicados depois não entram retroativamente no mês já aberto.",
    filters:
      "Filtros de leitura: origem do documento, área destinataria, escopo de filial e estado. São dimensões de dados — não alteram permissões nem o snapshot.",
    table:
      "Itens esperados da competência. Origem indica de onde o documento costuma vir (ERP TOTVS, fonte externa ou ambos); Destinatário é a área que recebe o documento quando conhecida — «A definir» marca pendência real do checklist, não erro de dados.",
    state:
      "Estado do item nesta competência. «Esperado» é o estado inicial de todo item — significa que a entrega está prevista, ainda sem documento anexado nem validação. «Aceito» marca evidência validada por pessoa autorizada. «Não aplicável» só vale para itens condicionais e exige justificativa auditada. «Cancelado» é terminal — o item sai da lista ativa com histórico preservado.",
    validation:
      "Validação humana da evidência — distinta do anexo: «anexado» nunca significa «validado». Cada arquivo (ou o conjunto inteiro, quando a regra é «Conjunto») exige aceite ou rejeição de validador autorizado. A rejeição pede motivo estruturado — «Outro» exige comentário — e marca a evidência para substituição. Substituir ou cancelar um anexo invalida a decisão anterior e exige nova validação. A reversão de uma rejeição só é permitida ao mesmo validador, com justificativa, enquanto nenhuma versão nova for anexada. Todo aceite, rejeição e reversão fica no histórico — nada é apagado.",
    exceptionalItem:
      "Item excepcional: entregável previsto só nesta competência, sem alterar o checklist mestre. Exige justificativa auditada e pode ser condicional para aceitar «Não aplicável».",
    reportRef:
      "Referência ao relatório ERP (R-ID) quando a origem é conhecida. Itens externos e pendências mapeadas não têm R-ID — a ausência não implica automação indisponível nem entrega dispensada.",
    detail:
      "Detalhe do item com proveniência: versão do template de origem, requisitos e notas. O conteúdo é o snapshot da competência — não muda quando o template mestre evolui.",
    documents:
      "Evidências anexadas à competência como um todo. Arraste ou selecione um arquivo (PDF, imagem, XLS, XLSX ou CSV, até 25 MB) para enviar; cada envio registra autor, data e integridade do arquivo. «Substituir» cria uma versão nova e preserva a anterior em «Versões» — só quem anexou ou um gestor pode substituir. «Cancelar» retira o documento da lista sem apagar arquivos nem histórico, que ficam em «Eventos». «Baixar» entrega o documento original — exige autorização e fica registrado na auditoria. Anexar uma evidência não valida o documento nem entrega o item: o checklist permanece «Esperado».",
    itemDocuments:
      "Evidências vinculadas a este item do checklist — a mesma regra de upload da competência vale aqui (PDF, imagem, XLS, XLSX ou CSV, até 25 MB). Um documento de item só pode ser anexado a um item da competência aberta. «Substituir», «Versões», «Eventos» e «Cancelar» funcionam como nas evidências da competência: a versão substituída fica marcada como «Substituída» e continua baixável, e o cancelamento é lógico — nada é apagado. Erros comuns: arquivo acima de 25 MB, formato não permitido, arquivo vazio ou conteúdo que não corresponde à extensão.",
  },
  admin: {
    page:
      "Administração do checklist mestre — exige permissão de gestão (controllership-finance.manage). Todo ciclo é versionado: criar rascunho, editar itens, publicar com vigência prospectiva e inativar. Competências já abertas nunca mudam — elas guardam um snapshot próprio. Usuários e permissões não são administrados aqui: pertencem ao Core.",
    versions:
      "Versões do template: «Rascunho» editável até a publicação, «Publicada» vigente a partir da competência informada, «Inativada» preservada no histórico. Só existe um rascunho por vez por template. Clique na linha para abrir a versão — a listagem pode ser alternada entre Tabela e Cards e as colunas são ordenáveis. Busca, modo de visualização e colunas ficam no painel do topo; ações de ciclo de vida (publicar, inativar, descartar) existem apenas dentro da página de cada versão.",
    items:
      "Itens da versão em modo de leitura — chave, entregável, origem, destinatário, obrigatoriedade, escopo de filial e regra de validação. Clique na linha para abrir o documento; alterne entre Tabela e Cards e ordene pelas colunas.",
    editDraft:
      "Edição do rascunho: altere, adicione ou remova itens e salve de uma vez — a gravação é atômica. Se outra sessão publicou ou alterou a versão, o salvamento é recusado («revisão desatualizada») para nunca sobrescrever trabalho alheio: recarregue e reaplique.",
  },
  adminVersion: {
    page:
      "Versão do checklist mestre — página contextual de uma versão específica (aberta a partir da listagem da Administração). O painel do topo concentra o estado do ciclo, os indicadores do snapshot, as ações da versão (histórico, edição, publicação, inativação conforme o estado) e os controles da listagem — busca, modo Tabela/Cards e colunas. Publicada e inativada são somente leitura; alterar a exigência de um documento para competências futuras acontece no catálogo de documentos, nunca na versão histórica.",
    meta:
      "Metadados da versão: estado do ciclo (rascunho → revisão → publicada → inativada), quantidade de documentos, competência a partir da qual vale, data de publicação e revisão de controle de concorrência. As ações disponíveis dependem do estado: rascunho pode ser editado, enviado à revisão ou descartado; em revisão pode ser publicada com vigência prospectiva ou devolvida com motivo; publicada pode ser inativada — nada reescreve competências já abertas.",
    items:
      "Documentos pertencentes a esta versão do checklist — o conteúdo exato daquele snapshot, não a configuração vigente hoje. Clique na linha ou no card para abrir o documento naquela versão. Em rascunho, «Editar itens» habilita a edição atômica governada.",
  },
  adminVersionDocument: {
    page:
      "Documento na versão — representação histórica do item dentro do snapshot daquela versão do checklist, sempre em leitura. Não confundir com o cadastro do catálogo documental: aqui você vê como o documento era exigido naquela versão; para mudar a exigência dali em diante, use «Editar exigência futura», que abre o fluxo governado do catálogo sem tocar o histórico.",
    identification:
      "Identificação do documento na versão: chave, nome, finalidade e orientações de preparação registradas no snapshot.",
    requirement:
      "Exigência do documento naquela versão: obrigatoriedade, origem, destino, via (eletrônico/físico), escopo de filial, regra de validação e referência TOTVS quando houver.",
  },
  adminEvents: {
    page:
      "Histórico de auditoria do checklist mestre — trilha de eventos do template ou de uma versão específica, em página completa: tipo do evento, data, hora, ator, versão afetada e detalhes registrados. O ator aparece pelo identificador técnico da auditoria; a exibição de nome e foto depende de contrato de identidade em decisão (UX-014). O histórico é imutável — nada aqui pode ser editado.",
  },
  documentsAdmin: {
    page:
      "Documentos do fechamento — catálogo mestre dos tipos de documento exigidos em cada competência (exige permissão de gestão). Cada documento tem vigência derivada das versões publicadas do checklist: vigente, futuro ou encerrado. Cadastro e edição abrem páginas completas — nunca modal. Filtros ficam na URL: F5, link direto e voltar/avançar restauram a consulta. Cadastrar documentos não é pré-requisito para abrir um fechamento.",
    list:
      "Tipos de documento do fechamento: exigência (obrigatório/condicional/opcional), destino (Contabilidade, Fiscal ou uso interno), vigência inicial e final derivadas da timeline de versões, e situação atual. Editar abre a página completa de configuração. Desativar não apaga o histórico — a exigência apenas deixa de valer para competências futuras.",
    formNew:
      "Novo documento do fechamento: informe nome, finalidade, orientações de preparação, obrigatoriedade, destino e a competência a partir da qual será exigido. A vigência é prospectiva — a exigência só vale para competências abertas a partir dela. O identificador técnico é gerado do nome e fica imutável depois. Cadastrar o tipo não exige anexar nenhum arquivo: anexação acontece na competência, na aba Documentos e interações.",
    formEdit:
      "Editar documento: alterações de configuração e de exigência viram uma nova versão publicada com vigência prospectiva — o histórico anterior e os fechamentos encerrados nunca são reescritos. «Encerrar exigência» deixa de exigir o documento a partir da próxima competência, sem excluí-lo. A alteração é propagada às versões futuras já publicadas cobertas pela janela; se uma gravação falhar no meio, o erro é exibido e repetir a operação conclui o que faltou — versão em rascunho/revisão com conteúdo idêntico é retomada, e uma com conteúdo diferente é recusada até ser concluída.",
    validity:
      "Vigência por competência: «exigido a partir de» define a primeira competência em que o documento é cobrado (nunca retroativa); «exigido até» é opcional e torna a exigência temporária — o documento deixa de ser cobrado no período seguinte. Competências já abertas guardam snapshot próprio e não mudam.",
    history:
      "Histórico de alterações do documento: eventos de auditoria das versões que contêm este tipo — autor, data, versão e tipo de evento (rascunho criado/atualizado, revisão, publicação).",
  },
  p3: {
    panel:
      "Cutoff e conciliação (P3): o fechamento exige confirmação humana do cutoff — nunca é inferido de dados aparentemente estáveis. Depois do cutoff, as fontes oficiais aplicáveis (Entradas/Saídas, Inventário P7 e posição H02) são revalidadas e conciliadas. A prontidão só é alcançada com divergência monetária de exatamente R$ 0,00 em todas as fontes — R$ 0,01 ou −R$ 0,01 bloqueiam. Fonte indisponível permanece explícita: nunca é convertida em zero nem libera a prontidão. Mudar qualquer input depois da revalidação exige nova revalidação. «Estoque fechado» reflete somente o estado canônico do ERP (T03) — o Portal não fecha estoque por conta própria nem escreve no TOTVS.",
  },
  reports: {
    panel:
      "Matriz R01–R15: cobertura de evidências por relatório do processo de fechamento, derivada do snapshot da competência. «Consulta operacional» (baixas SE5, estoque SB9) é visão auxiliar — não é relatório oficial nem comprovação de paridade. «Contrato pendente» marca fontes sem owner/contrato confirmado — a captura segue fluxo manual governado de evidências. «Coberto» significa todos os itens vinculados ao R-ID validados — não é aceite de negócio do relatório.",
  },
  pendencies: {
    page:
      "Pendências e classificações (P4): registro e tratamento governado do que falta ou divergiu no fechamento — evidência ausente, rejeição, divergência de conciliação, correção estrutural ou dependência externa. Ciclo de vida fechado: Aberta → Em análise / Aguardando externo → Resolvida ou Descartada (descarte exige justificativa e não significa «não se aplica»).",
    queue:
      "Fila de pendências da competência. «Assumir» atribui você como responsável — muda só a responsabilidade, com histórico preservado; não concede acesso a recursos. Reatribuição e confirmação de classificação exigem permissão de gestão. Sugestões automáticas (regra ou IA) aparecem marcadas como «sugestão» — nunca são decisão: a confirmação é humana e auditada. «Idade» é tempo factual desde o registro — não é SLA nem atraso.",
  },
  packages: {
    page:
      "Pacotes e revisão (P5): a competência é entregue em pacotes por destinatário (Contábil, Fiscal). «Finalizar» congela uma versão imutável do pacote — não envia nada a ninguém. «Enviar para análise» disponibiliza a versão dentro da Minha DELPI aos revisores designados: nunca é anexo de e-mail nem entrega externa. Cada pacote avança de forma independente — o envio de um destinatário não muda o estado dos demais.",
    list:
      "Pacotes por destinatário da competência. Estados: «Pacote incompleto» (em elaboração ou versão de trabalho), «Pacote finalizado» (versão congelada, ainda não enviada) e «Enviado para análise» (disponível aos revisores na Minha DELPI). A coluna Revisão reflete o estado real do ciclo de análise — incluindo bloqueios como «Aguardando esclarecimento» ou «Ajustes solicitados».",
    detail:
      "Detalhe do pacote do destinatário: versão vigente, áreas obrigatórias de revisão, aceites registrados, esclarecimentos e histórico de versões. Versões enviadas são imutáveis — correções exigem «Reabrir» (nova versão de trabalho) ou «Criar complemento» (nova versão vinculada). Nova versão zera as exigências de aceite: aceites anteriores ficam no histórico, mas não contam para a versão vigente.",
    review:
      "Revisão do pacote: cada área obrigatória da versão vigente precisa de um aceite humano real — o aceite é irreversível e auditado, sem edição nem estorno. «Solicitar ajustes» ou «Rejeitar» exigem motivo e reabrem o ciclo sem perder o histórico. Esclarecimentos abertos bloqueiam a conclusão mensal até serem respondidos. Reatribuir um revisor preserva o que ele já decidiu — o substituto atua só dali para frente.",
    closing:
      "Estado do fechamento mensal: a competência só conclui quando todos os pacotes aplicáveis foram enviados, aceitos por pessoa humana real e por cada área obrigatória da versão vigente, sem esclarecimentos abertos e sem rejeição terminal — o Portal nunca conclui por vacuidade ou apenas por valores declarados. A «rejeição terminal» da competência é reservada ao coordenador formal designado e bloqueia a conclusão; é distinta da rejeição de uma área num pacote.",
  },
  myTasks: {
    page:
      "Minhas tarefas: projeção somente do seu próprio trabalho pendente — pendências sob sua responsabilidade (P4), revisões de áreas obrigatórias de pacote aguardando seu aceite (P5) e esclarecimentos abertos em pacotes que você enviou. Cada item abre a página dona do recurso. «Pendente desde» é um dado factual de registro — não é SLA nem atraso.",
    queue:
      "Trabalho atribuído a você: somente itens que exigem ação sua aparecem aqui — nunca tarefas de outros usuários. A projeção respeita a elegibilidade de revisão configurada: se sua área exige vínculo a grupo corporativo do Core e o vínculo não existe, a revisão não é listada. Abrir leva à página que decide o recurso — a ação real (resolver, aceitar, responder) acontece lá.",
    summary:
      "Resumo por tipo de trabalho pendente: total, revisões de pacote, pendências do fechamento e esclarecimentos abertos aguardando sua resposta.",
  },
  profile: {
    identity:
      "Identidade corporativa: nome, e-mail e dados do cadastro de pessoa vêm do Core em tempo real — o Portal não mantém cadastro nem edição própria. Se o perfil corporativo estiver indisponível, só os dados básicos de sessão são exibidos.",
    groups:
      "Vínculos corporativos: grupos e funções do Core associados à sua identidade. Eles alimentam a elegibilidade de revisão configurada nos catálogos governados — um grupo ausente pode impedir a atribuição de revisões.",
    permissions:
      "Permissões efetivas neste portal: resolvidas pelo Core a cada sessão. «Acesso ao portal» permite consultar e operar suas atribuições; «Gestão» libera administração do checklist, catálogos e operações administrativas. As permissões são só suas — outro usuário não as vê aqui.",
  },
  catalogs: {
    page:
      "Catálogos governados (P6): configurações de referência da Central de Fechamento — bancos e contas, motivos de rejeição, papéis de anexo, destinos de notificação, áreas obrigatórias por tipo de pacote e elegibilidade de revisão. Exige permissão de gestão. O código de cada entrada é a identidade e não pode ser alterado; edições são versionadas (revisão/OCC) e a desativação é prospectiva — nada já registrado é reescrito.",
    list:
      "Catálogos disponíveis: cartões com contagem de entradas ativas e inativas. Catálogo vazio é estado legítimo — os processos aplicam o fallback documentado (ex.: área obrigatória = destinatário do pacote; elegibilidade = apenas assignment ativo) e registram a fonte na auditoria.",
    entries:
      "Entradas do catálogo selecionado: código (identidade imutável), rótulo, atributos livres em JSON, estado e revisão. Atributos carregam a semântica específica de cada catálogo — ex.: área destino em «áreas obrigatórias», grupos Core exigidos em «elegibilidade de revisão».",
    form:
      "Nova entrada ou edição: o código só é definido na criação — depois vira identidade imutável. Salvar uma edição exige a revisão vigente; se outra sessão alterou a entrada, o salvamento é recusado — recarregue e reaplique. Vigência inicial opcional define a partir de qual competência a entrada vale.",
  },
  cockpit: {
    page:
      "Cockpit do fechamento: visão consolidada do estado real da competência — checklist/evidências (P2), cutoff e conciliação (P3), pendências (P4) e pacotes/conclusão (P5). É leitura derivada do backend: bloqueios e fontes indisponíveis aparecem como estão — nenhum card fica «verde» por cálculo local.",
    closing:
      "Conclusão mensal: estado derivado do contrato C2 — pacotes aplicáveis enviados e aceitos, áreas obrigatórias atendidas, sem esclarecimentos abertos, sem rejeição terminal e sem bloqueios de P2/P3/P4. Razões de bloqueio são listadas textualmente quando presentes.",
    checklist:
      "Checklist e evidências (P2): contagem real dos itens do snapshot por estado — aguardando evidência, aceitos, não aplicáveis ou cancelados.",
    p3:
      "Cutoff e conciliação (P3): estado de cada domínio — disponível/indisponível — e a proveniência do registro de conciliação: «oficial» (respaldado por artefato oficial anexado) ou «declarado» (informado pelo cliente, não comprova fechamento). Divergência mostra o valor real conciliado; fonte indisponível nunca vira zero.",
    p4:
      "Pendências (P4): contagem por estado — Aberta, Em análise, Aguardando externo, Resolvida, Descartada. Pendências em aberto permanecem visíveis como bloqueio.",
    p5:
      "Pacotes (P5): estado real de cada pacote de destinatário e do ciclo de revisão — do pacote incompleto até a revisão aceita. O fechamento mensal concluído é um estado distinto e posterior a tudo isto.",
  },
  monthlyClosing: {
    page:
      "Fechamento mensal: bancada de trabalho por mês de referência em três abas — Visão geral (situação, atenções e próximos passos do fechamento), Documentos e interações (evidências P2) e Relatórios e divergências (atenções, cartões por família que abrem páginas contextuais de relatório e cobertura R01–R15). Selecione o mês para consultar; escolher um mês não abre competência — meses sem abertura formal mostram explicação e a ação autorizada.",
    indicators:
      "Indicadores deste fechamento: O que falta resolver (situações que impedem a conclusão — clique para localizar na lista), Divergências (diferenças encontradas nas conferências — clique para abrir Relatórios) e Documentos a tratar (contagem ainda indisponível — «—» até existir a métrica). «—» significa dado indisponível — nunca zero confirmado.",
    tabs:
      "Três visões do mesmo mês: Visão geral consolida o estado do fechamento; Documentos e interações abre as evidências e anexos P2 (exige competência aberta); Relatórios e divergências mostra divergências comprovadas, fontes indisponíveis e o catálogo em cartões — «Abrir relatório» leva à página contextual do relatório dentro do próprio Fechamento Mensal, sem nova aba.",
    pdfPreview:
      "Prévia do PDF do relatório selecionado: exibida quando existir um PDF homologado com produtor e contrato autorizado. Enquanto não existir, a seção informa a indisponibilidade — o Portal não gera PDF fictício nem reutiliza evidência anexada como relatório oficial.",
    reportsIndicators:
      "Indicadores do mês: Divergências identificadas (diferenças comprovadas pelos owners, incluindo inconsistências de vínculo), Relatórios disponíveis (famílias com consulta autorizada respondendo) e Fontes não verificadas (fontes indisponíveis ou conferências pendentes). «—» significa que nem todas as fontes responderam — nunca é zero confirmado.",
    reportsAttention:
      "O que precisa de atenção: divergência comprovada (diferença calculada pelo owner), fonte indisponível (a consulta não respondeu ou está parcial) e conferência não realizada (atividade ainda não executada). Cada item mostra origem, data da consulta e próxima ação; «Ver detalhes» expande valores, fatos e orientação de correção manual no TOTVS quando comprovada — sem escrever no ERP.",
    reportsCatalog:
      "Relatórios organizados em cartões por família: Baixas financeiras (pagamentos e recebimentos SE5) e Estoque e conciliação (posição P7 + conferência Entradas/Saídas − P7 − H02). «Abrir relatório» abre a página contextual do relatório — a situação do cartão reflete a consulta real, não a homologação do relatório oficial.",
    reportsResults:
      "Página contextual do relatório: totais calculados pelo backend, agrupamentos em tabelas por colunas e registros com filtros e paginação reais do contrato. A competência vem da rota e os filtros vigentes ficam na própria URL — atualizar a página (F5), abrir um link direto ou navegar com voltar/avançar restaura o contexto da análise, e o retorno à aba Relatórios e divergências preserva a família e a seleção anterior.",
    attention:
      "Situações reais que precisam ser resolvidas neste fechamento: relatórios que não puderam ser consultados, divergências, documentos pendentes e pendências em aberto. Cada ação leva ao local onde a situação é tratada. Se houver mais situações, use «Mostrar todas» para expandir a lista aqui mesmo.",
    stockAxis:
      "Conferência do estoque: mostra se a conferência do mês foi finalizada e se os relatórios necessários puderam ser consultados. O próximo passo indicado vem da situação real deste fechamento.",
    docsAxis:
      "Documentos do mês: documentos exigidos neste fechamento e sua situação — aguardando evidência ou aceitos. «Nenhum documento exigido» é uma situação normal, não um erro.",
    packageAxis:
      "Documentos para a Contabilidade: situação do conjunto de documentos destinado à Contabilidade — pronto para envio ou já enviado para revisão. O envio acontece na página de gerenciamento.",
    recentActivity:
      "Atividades recentes: últimos registros reais das conferências deste mês (até cinco). Ainda não cobre todas as áreas — ausência de registros é normal e nenhuma atividade é simulada.",
    conclusion:
      "O fechamento é concluído pelo sistema quando todas as condições são atendidas — não existe botão de concluir. As situações que impedem a conclusão aparecem em «O que precisa de atenção».",
    sendPackage:
      "O envio dos documentos à Contabilidade é uma operação separada da conclusão e exige confirmação na página de gerenciamento. Um conjunto só pode ser enviado quando está pronto.",
    documentsTab:
      "Cartões por documento: «Exigido» vem da lista de documentos definida para o mês; «Adicional» é um arquivo anexado só a este fechamento. «Ver documento» abre a página de detalhe com prévia, versões e histórico. O menu ⋮ de cada cartão oferece abrir, enviar nova versão e remover. Pesquisa e filtro ficam na URL.",
    requestsSummary:
      "Solicitações reais de ajuste registradas pelos revisores (decisões com motivo e comentário). «Abrir conversa» leva ao detalhe do documento, onde o contexto completo fica disponível. Responder não encerra a solicitação automaticamente.",
    additionalDocument:
      "Documento adicional: arquivo anexado somente a este fechamento. Não cria exigência geral, não se torna obrigatório nos próximos meses e não altera fechamentos concluídos.",
    detailFile:
      "Prévia, download e versões do arquivo. «Enviar nova versão» cria uma versão nova — a anterior fica preservada no histórico e pode ser selecionada na lista de versões. Se a prévia falhar, «Tentar novamente» recarrega e o download continua disponível. «Remover documento» retira o arquivo da lista sem apagar versões e histórico — a exigência continua valendo.",
    detailInteractions:
      "Solicitações e decisões reais registradas neste documento (ajuste solicitado, conferido, revertido) com autor e data. São atos formais de validação — diferentes das mensagens da conversa.",
    detailConversation:
      "Conversa livre sobre este documento, iniciada pela Controladoria quando necessário — não é preciso esperar solicitação da Contabilidade. Cada mensagem é gravada com autor e data e permanece disponível ao recarregar a página. A foto e o nome exibidos vêm do perfil oficial do participante e só são consultados dentro deste documento autorizado; quando não há foto, aparecem as iniciais. Uma mensagem não valida o documento, não encerra solicitações de ajuste e não libera o arquivo para a Contabilidade.",
    detailHistory:
      "Linha do tempo operacional do documento: anexação, novas versões, remoção e decisões de conferência — sempre com responsável, foto do perfil oficial (ou iniciais) e data. Downloads e mensagens da conversa ficam fora daqui; a trilha de auditoria técnica permanece completa. Versões anteriores permanecem disponíveis.",
  },
} as const;
