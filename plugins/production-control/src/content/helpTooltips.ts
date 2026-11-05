export const helpTooltips = {
  home: "Painel inicial do PCP: OTD da filial no mês, pedidos a faturar até hoje (estoque/faturado), volume de PAs e fila de OPs atrasadas.",
  productionVolume:
    "Agregação da quantidade produzida de PAs (última operação do roteiro SG2 — entrada em estoque). No modo Dia: mês corrente com média só em dias úteis. No modo Mês × ano ant.: jan→hoje em buckets mensais comparado ao mesmo período do ano anterior.",
  problemAnalysis:
    "Grade de detectores de exceção da fábrica. Cada cartão roda uma regra sobre os dados do TOTVS; abra o cartão para ver os registros que precisam de ação.",
  incompleteOrderSets:
    "Compara a estrutura do produto raiz (vigente na emissão da OP mãe) com as OPs criadas no mesmo conjunto. Falta = intermediário da estrutura sem OP. Sobra = OP de produto fora da estrutura. Matéria-prima não entra.",
  quantityMismatches:
    "Compara a quantidade de cada intermediário com OP no conjunto à necessidade da estrutura para a quantidade da OP mãe. Abaixo = OP filha menor que o esperado. Acima = OP filha maior. Só entram códigos que já existem no conjunto; falta de OP fica no detector de conjuntos incompletos.",
  uncoveredDemand:
    "Mesma regra da aba Demanda: saldo aberto sem estoque nem OP suficiente (sem cobertura), ou OP prevista só depois da entrega ao cliente. Atrasadas com buraco também aparecem aqui.",
  sharedStructureIntermediates:
    "Intermediários PI/PA da estrutura vigente hoje que aparecem em mais de um PA com apontamento produtivo nos últimos 12 meses. Alteração de engenharia nesse código impacta todos os acabados listados.",
  machineLoad:
    "Fila de operações alocadas (SH8) congelada por filial e período. A fila de todos os CTs é carregada de uma vez, então trocar de aba é imediato. Os estados de execução vêm do cockpit do operador e se atualizam sozinhos a cada 30 s, sem recarregar a fila: «Produzindo» = run ativo no posto, «Parada» = parada registrada, «Pausada» = execução pausada pelo operador, «Estado não confirmado» = leitura inconsistente e «Não iniciada» = nenhum run aberto. Se a leitura do cockpit falhar, a fila continua na tela com o aviso de indisponibilidade — nunca volta a mostrar apontamento antigo. Os saldos produzidos e pendentes vêm do TOTVS (SH6/SC2) numa leitura própria, também a cada 30 s. «Já apontada» (linha tachada / Limpar fila) só vale quando o saldo da própria operação acabou e não há run aberto — apontamento parcial continua na fila e um run ativo nunca é escondido por saldo zerado. O saldo do cabeçalho da OP só muda na última operação do roteiro. Use Atualizar para regenerar a programação a partir do TOTVS (horizonte padrão, em geral 14 dias). Em um CT com pouca programação, «Ampliar horizonte» consulta só aquele centro além da janela-base (21/28/42 dias ou data final), mostra prévia e inclui na preparação WORKING — nunca chega ao cockpit antes de «Enviar para máquinas»; na próxima atualização geral as exceções somem. O rastreio localiza o conjunto (C2_NUM) ou o produto (PA) em todos os CTs e mostra o mesmo estado do cockpit. No link do operador, o posto pode iniciar a contagem de peças em tempo real a partir do contador Pulso (1 golpe = 1 peça); a meta fica congelada pelo saldo da operação no momento do Play, com MI convertido para peças, e atingir 100% não encerra o run automaticamente. O apontamento oficial continua no coletor TOTVS. Seleção de operações: clique na linha ou no checkbox para selecionar; Ctrl/⌘+clique marca ou desmarca itens soltos; Shift+clique seleciona o intervalo até a última linha marcada. A barra acima da tabela mostra a contagem e «Limpar seleção» (Esc também limpa, fora de campos e modais). A seleção é só da tela — não altera a programação — e some ao trocar de centro de trabalho, filial, período, filtros ou ao atualizar a fila. Com 2+ operações selecionadas o arraste individual fica suspenso e o botão direito numa linha selecionada mostra o menu da seleção: «Agrupar operações selecionadas» reúne as marcadas na posição da primeira selecionada na fila, mantendo a ordem relativa de todas — é uma reordenação como o arraste, com Ctrl+Z disponível. O agrupamento fica bloqueado quando uma operação com execução em andamento seria deslocada, quando o estado do cockpit está indisponível ou com o filtro «Somente com impedimento» ativo; transferir e retirar em lote chegam na próxima etapa. Pelo menu de contexto da operação (botão direito numa linha), «Solicitar correção a Processos» abre um chamado do tipo Problema de Processo em Minhas Solicitações — com o motivo, a observação e o contexto da operação (filial, CT, OP, produto, PA e ferramenta) congelados no envio. A solicitação vai para a mesma fila do departamento de Processos que atende os reportes do operador e NÃO altera a programação, o roteiro nem o TOTVS.",
  machineLoadLocate:
    "Conjunto = C2_NUM (6 primeiros dígitos da OP completa). Ex.: 10840401003 inclui todas as OPs 108404…. Produto (PA) lista os conjuntos daquele acabado.",
  branch:
    "Filial TOTVS da consulta. Só aparecem as filiais liberadas no seu perfil; se você tem só uma, ela já entra selecionada.",
  materials:
    "Três recortes de matéria-prima: excesso de SC1 (documento inteiro já coberto depois do ESTSEG), solicitações insuficientes (cobertura + SC1 não chega no estoque de segurança) e consulta de ruptura no conjunto do PA pelos empenhos abertos (SD4) no extrato saldo + pedidos − empenhos — substitutos entram; empenho zerado não aparece na lista. Após mudar empenho no Protheus, atualize a consulta (cache ~2 min). Não elimina no TOTVS.",
  lineFeeder:
    "Antes da primeira consulta, o cartão central orienta o uso de Coletar. Use Coletar para escolher os postos da programação publicada pelo PCP e quantas horas de produção deseja abastecer em cada um. A consulta calcula as matérias-primas pelos empenhos das operações contempladas e desconta uma vez o saldo real no ponto de uso — o que resta é a quantidade a coletar. A coluna CT mostra só o código do primeiro posto que usará o material; as demais origens ficam no detalhe da linha. Não há marcação de separado/entregue nem reserva de material: cada consulta é uma fotografia atualizada. «Em risco» indica que o almoxarifado não cobre o que falta. Solicitações urgentes do operador ficam no sino do cabeçalho e não misturam quantidade com esta prévia.",
  lineFeederPickPlan:
    "Fluxo legado de listas persistidas (não é o caminho principal do Alimentador). A coleta dinâmica por horizonte substitui a geração de listas com marcação manual no painel principal.",
  lineFeederCollect:
    "Selecione um ou mais postos da fila publicada e informe as horas. O mesmo número de horas vale para cada posto escolhido. Depois use Consultar materiais.",
  deliveryMap:
    "OPs mãe de PA com saldo em aberto, agrupadas pela data prevista de entrega. O primeiro bloco reúne hoje e atrasadas. Observações vêm do TOTVS (C2_OBS). MP-OK e Feedback são marcações manuais do PCP. A barra de progresso carrega só nas 3 primeiras tabelas (hoje+atrasadas primeiro); demais datas ficam sem barra. Linha riscada só quando o conjunto atinge 100%. A lista congela até clicar em Atualizar.",
  reports:
    "Relatórios operacionais do Portal PCP. A entrada lista cards do catálogo; ao abrir um card você entra na página do relatório, com voltar ao catálogo. Saldos: na filial 01 só códigos 9…; na 02 códigos 8… e 9…. Ordens de produção: padrão em aberto (sem data real de fim). «Entrega de» e «Entrega até» filtram só a ponta preenchida; vazio não recorta essa ponta. Em Todas entram abertas e encerradas juntas, com ou sem data de fim. Se a data de fim for preenchida em Todas, ela recorta só as encerradas; as em aberto permanecem. Em Não, a data de fim recorta as encerradas. Colunas: nº da OP, produto, emissão, início, entrega, quantidade, saldo e observações.",
  productModels:
    "Anexe um arquivo .glb ao código do produto da ordem de produção (PI ou PA). No cockpit, o operador vê o 3D na operação daquele produto; o desenho PDF continua sendo o do PA.",
  sequencingProfiles:
    "Cadastro das regras que o botão Otimizar planejamento aplica por centro de trabalho. A entrega do PA é sempre o primeiro critério. Critérios opcionais: Ferramenta (agrupa quem usa a mesma ferramenta) e Código do cabo (agrupa pelo código exato do material — os grupos SB1 só dizem quais materiais entram na verificação). Um perfil em rascunho pode ser editado e ativado; somente perfis ativos podem ser vinculados a um CT. Nada aqui altera a fila na hora — as regras valem na próxima otimização.",
  mywegNeedsSb1:
    "Situação do vínculo com o cadastro SB1 do Protheus. Código informado na origem só vira confirmado após validação real. Divergência e ambiguidade mostram o motivo sem editar cadastro.",
  mywegNeedsEvolution:
    "Compara duas fotografias MyWEG. «Por remessa» mostra movimentos e reprogramações; «Por produto» consolida totais e diferença líquida. Variação observada ≠ abatimento WEG. Faturamento/FIFO são hipóteses separadas.",
  mywegNeeds:
    "Necessidades WEG (filial 02 · ES). «Consulta de necessidades» mostra KPIs, histórico de coletas e filtros da tabela. «Comparação entre coletas» analisa mudanças entre duas datas (por remessa ou por produto). Clique nas barras do histórico para trocar a coleta. Sem tempo real nem geração de OP.",
  mywegNeedsKpiIncreased:
    "A mesma combinação produto/remessa existe nas duas coletas e a quantidade aumentou.",
  mywegNeedsKpiDecreased:
    "A mesma combinação produto/remessa existe nas duas coletas e a quantidade diminuiu. Redução observada não significa, por si só, que o material foi faturado ou atendido.",
  mywegNeedsKpiAppeared:
    "Combinações de produto e data de remessa que não existiam na coleta anterior. Não significa necessariamente produto novo — pode ser remessa que mudou de data.",
  mywegNeedsKpiDisappeared:
    "Combinações presentes na coleta anterior e ausentes na atual. Não significa automaticamente pedido cancelado — pode ser remessa que migrou para outra data.",
  mywegNeedsKpiHorizon:
    "Subconjunto das alterações cuja data de remessa está entre a data da coleta atual e os 14 dias seguintes. Não some este número aos outros indicadores.",
  mywegNeedsProbableShifts:
    "O sistema identifica possíveis mudanças de datas comparando quantidades do mesmo produto entre duas coletas. A correspondência é estimada e não confirma alteração de um pedido específico. Uma saída e uma entrada podem representar possível deslocamento de data; o pareamento pode ser parcial; o produto pode ter simultaneamente mudança de data e aumento/redução. Ocorrências não devem ser somadas aos indicadores de movimento. Não comprova faturamento nem abatimento reconhecido pela WEG.",
  mywegNeedsProbableAdvancement:
    "Quantidade do mesmo produto que diminuiu em uma data de remessa e aumentou em outra data anterior. Hipótese de antecipação — não prova identidade de pedido.",
  mywegNeedsProbablePostponement:
    "Quantidade do mesmo produto que diminuiu em uma data de remessa e aumentou em outra data posterior. Hipótese de postergação — não prova identidade de pedido.",
  mywegNeedsProbableTotal:
    "Total de pareamentos estimados entre datas (ocorrências, não pedidos distintos). Inclui antecipações, postergações e redistribuições na mesma data quando existirem.",
  mywegNeedsProductAnalysis:
    "Consolida a necessidade do produto somando todas as remessas das duas coletas. Diferença líquida = total atual − total anterior. Mudança só de datas com total estável aparece como «quantidade mantida, com alteração nas datas». Não afirma cadastro, cancelamento, faturamento ou atendimento. Reprogramações prováveis são complementares e não alteram os totais.",
  mywegNeedsAnalysisRemessa:
    "Análise por combinação produto e data de remessa — movimentos observados (aumento, redução, entrada, saída) e possíveis reprogramações.",
  mywegNeedsAnalysisProducts:
    "Análise consolidada por produto DELPI — totais e diferença líquida considerando todas as remessas, inclusive as inalteradas.",
} as const;
