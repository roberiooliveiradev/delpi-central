# Chamado #1583 — Favoritos e criticidade dos Serviços Windows

## Entrega
Evolução da área **Servidores > Serviços Windows** no Portal de TI.
Mantém os indicadores do inventário SCM e a sincronização existente do
SRV-DB01 a cada cinco minutos, sem mudar os scripts PowerShell, a
autenticação Keycloak do coletor ou o Task Scheduler.

### Experiência visual
- Estrela contextual e discreta na própria célula do serviço; preenchida
  apenas quando favorito, sem criar mais uma coluna na tabela.
- Controle segmentado **Todos os serviços | Favoritos (n)**, com total
  persistido calculado pelo backend para todo o servidor, não somente
  para os 25 itens exibidos na página.
- Filtro de favoritos executado no servidor e combinado com busca,
  estado, modo de inicialização, presença e paginação.
- Criticidade **Normal / Alta / Crítica**, editável no detalhe expandido
  somente para favoritos. Indicador sutil de criticidade ao lado do nome.
- Estado vazio específico para a visão de favoritos; feedback de
  falha de gravação sem esconder a tabela nem perder os filtros.
- Estilo scoped por .dashboard-it-portal, tokens adaptáveis a tema escuro,
  foco visível, botões acessíveis e redução de movimento quando indicada.

### Persistência e integridade
- Migration **V007__windows_service_favorites.sql**. Não modificar V006.
- Preferência compartilhada por server_id + service_key (identidade
  casefold do Win32_Service, não display_name), com FK no inventário real.
- A escolha persiste após refresh, mudança de sessão, novas coletas e
  desaparecimento temporário de um serviço (is_present=false).
- A ingestão SCM somente modifica host_services; nunca sobrescreve
  preferências. A lista faz LEFT JOIN, inclusive para serviços sem favorito.
- Não há salvamento no localStorage ou reenvio de preferência no coletor.
- Auditoria transacional dos ajustes no histórico do servidor, com
  identidade do colaborador e estado anterior/posterior. Reenvio de
  preferência idêntica não cria eventos redundantes.

### Autorização
- Leitura requer it-portal.access + it-portal.servers.view.
- Edição de favoritos compartilhados requer adicionalmente
  **it-portal.host-services.manage**.
- Backend revalida autorização no Core para cada PUT, sem cache,
  e devolve 403 quando a permissão foi revogada e 503 quando o
  Core está indisponível.
- Servidor arquivado não recebe alterações; serviço inexistente retorna
  404; dados inválidos retornam 422.
- Nenhum endpoint ou botão de iniciar, parar ou reiniciar serviços.

## Contratos HTTP
GET /servers/{server_id}/host-services
  - Novo filtro opcional: favorites_only=true (default false).
  - Cada item inclui service_key, is_favorite, criticality.
  - Resposta inclui favorites_count (todo o servidor).
PUT /servers/{server_id}/host-services/{service_key}/preferences
  - Body: {"is_favorite": true, "criticality": "normal|high|critical"}.
  - Remover favorito exige {"is_favorite": false, "criticality": "normal"}.
  - Response: service_key, is_favorite, criticality.
  - OperationId: set_it_windows_host_service_preference.

## Ordem de implantação
1. Concluir PR e exigir CI de API + frontend + arquitetura verdes.
2. Confirmar backup e política de migrations; atualizar main no srv-api.
3. Deploy it-portal-api com migration V007 aplicada antes de
   expor o MFE (tabelas novas são aditivas).
4. Publicar o manifesto **it-portal.manifest.json v0.3.1**
   como **nova versão estrutural** no Portal Admin: adicionar permissão
   requer POST /core-api/admin/apps/register, não PUT cosmético.
5. Conceder it-portal.host-services.manage somente a perfis autorizados
   a manter preferências compartilhadas, com it-portal.servers.view.
6. Publicar MFE it-portal; abrir servidor > Serviços Windows,
   verificar conteúdo e favoritos sem permissões e com permissão.
7. Testar favoritar e remover serviço não crítico, classificar prioridade,
   atualizar a página, conferir histórico, navegar até a página seguinte,
   repetir a coleta SCM e confirmar a persistência.
8. Verificar que a tarefa Windows de cinco minutos segue operando
   normalmente. Nenhum novo passo precisa ser executado no Windows.

## Fora deste escopo
Alertas automáticos, monitoramento contínuo, disponibilidade/uptime,
definição de um estado esperado de execução e Start/Stop/Restart remoto
serão tratados em iniciativas futuras. Favorito e criticidade são
metadados de atenção, não disparadores de incidente.

## Testes
- Backend: pytest e integração Postgres com base temporária (V007,
  identidade, filtro, refresh/coleta posterior, permissões e auditoria).
- Frontend: vitest, lint e TypeScript build (estrela, filtro, editor
  contextual, modo somente leitura e contrato de manifesto).
