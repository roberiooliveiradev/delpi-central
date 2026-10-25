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
      "Competência no formato AAAA-MM. Ao abrir uma competência o Portal registra os itens do checklist vigente naquele momento — a repetição não duplica a abertura.",
    open:
      "Abrir a competência copia os itens da versão publicada do checklist para o mês escolhido. Se nenhuma versão estiver publicada, a abertura é recusada — não existe fallback.",
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
      "Versões do template: «Rascunho» editável até a publicação, «Publicada» vigente a partir da competência informada, «Inativada» preservada no histórico. Só existe um rascunho por vez por template.",
    items:
      "Itens da versão em modo de leitura — chave, entregável, origem, destinatário, obrigatoriedade, escopo de filial e regra de validação.",
    editDraft:
      "Edição do rascunho: altere, adicione ou remova itens e salve de uma vez — a gravação é atômica. Se outra sessão publicou ou alterou a versão, o salvamento é recusado («revisão desatualizada») para nunca sobrescrever trabalho alheio: recarregue e reaplique.",
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
} as const;
