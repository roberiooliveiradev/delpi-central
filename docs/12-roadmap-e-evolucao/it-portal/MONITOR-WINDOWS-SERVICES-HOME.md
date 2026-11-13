# Monitor de saúde dos serviços Windows na tela inicial

O monitor utiliza somente os registros já mantidos pelo Portal de TI.
Não realiza novas conexões aos servidores, não abre portas e não executa comandos Start/Stop/Restart.

## Fonte e seleção
- Seleção global, dinâmica: preferências compartilhadas com is_favorite=true e criticality in (high, critical), em servidores não arquivados.
- Estado: inventário completo Windows SCM registrado em host_services, conciliado com host_service_current.
- Coleta existente: a cada 5 minutos por host cadastrado. Atualização de leitura do componente web: a cada 60 segundos e ao retornar à aba.
- Backend: GET /dashboard/windows-services-health, protegido por it-portal.access + it-portal.servers.view.
- Sem migration nem alterações nos scripts PowerShell, tarefas agendadas ou no agente de controle remoto.

## Semântica do indicador
- Denominador: todos os serviços favoritos com criticidade Alta ou Crítica, inclusive temporariamente ausentes.
- Saudável/Em execução: serviço presente, estado running e coleta recente e válida.
- Parado: serviço presente com estado stopped e coleta recente.
- Outros em atenção: pausado, transição ou não encontrado na coleta recente.
- Sem confirmação: última coleta SCM com mais de 15 min, ausente ou com horário inconsistente. NÃO é interpretado como ativo.
- Percentual: inteiro truncado de (em execução / monitorados) * 100. 100% exige todos em execução e confirmados; sem itens o indicador é indefinido, não 100%.
- Mostra subtotais por host, coleta mais recente, e até 12 serviços prioritários não saudáveis com link para o servidor.

## Aceite e implantação
1. Verificar testes da API e do MFE, lint/build, validação de OpenAPI/RBAC e revisão do SQL.
2. Publicar primeiro it-portal-api; validar GET e acesso negado a perfil sem servers.view.
3. Publicar it-portal (não exige atualização de manifesto/permissão nova).
4. Criar serviço de teste como favorito Alta em um Windows; verificar início, parada, coleta atrasada, mudança de criticidade e persistência. NÃO interromper serviços produtivos para teste.
5. Verificar dois ou mais hosts, inclusive host sem coleta recente e serviço ausente.
6. Confirmar que as tarefas SCM existentes seguem agendadas e que a fila de controle remoto não foi alterada.

Sem disponibilidade de coleta recente, o número é conservador e indica falta de confirmação, não uma indisponibilidade comprovada do Windows.
