# Portal de Engenharia — cutover e rollback

> **Status:** runbook de coexistência; execução depende de GATE-PARITY e autorização explícita.  
> **Princípio:** target-first, redirect-last.

## 1. Objetivo

Migrar a experiência de Engenharia para o novo Portal sem interromper os usuários, perder permissions/deep links ou remover os legados antes de a substituição estar comprovada.

## 2. Escopo de cutover

Legados principais candidatos:

```text
dashboard-engineering
dashboard-lmps
```

`controle-mp` segue o roadmap próprio de migração para `my-requests`; o Portal Engenharia não toma ownership desse cutover.

Transformômetro permanece ativo como owner do TRANSFORMA+.

## 3. Fases

### C0 — baseline

- inventário de usuários/roles/permissions;
- rotas/deep links atuais;
- funcionalidades do legado;
- métricas de uso quando disponíveis;
- rollback path.

### C1 — coexistência

Novo Portal entra no Core sem remover os apps existentes.

```text
Portal Engenharia ativo
Dashboard Engenharia ativo
Dashboard LMPs ativo
```

Usuários de homologação recebem novo acesso; produção geral pode continuar no legado.

### C2 — soft cutover

Depois do GATE-PARITY:

- promover Portal no launcher/menu;
- reduzir destaque dos legados, se aprovado;
- atualizar CTAs internos para o target;
- manter deep links antigos operacionais;
- observar erros/latência/uso.

### C3 — redirect controlado

Somente quando:

- target saudável;
- paridade aceita;
- permissions migradas;
- deep links mapeados;
- rollback imediato disponível.

Criar redirects de rotas legadas para destinos equivalentes no Portal, preservando chaves/query quando possível.

### C4 — hard cutover

- remover legado do launcher/manifest/runtime conforme política;
- preservar redirect de compatibilidade pelo período definido;
- arquivar documentação de operação do legado sem apagar histórico técnico necessário.

## 4. Ordem recomendada por legado

### dashboard-engineering

Destino:

```text
/apps/dashboard-engineering
→ /apps/engineering/overview
```

Subrotas LMP/Transforma devem apontar para o drill equivalente, não necessariamente para a mesma página genérica.

Antes do redirect, provar:

- dois indicadores estratégicos;
- meta/realizado/IDD;
- resumo TRANSFORMA+;
- filtros/período equivalentes;
- permission population.

### dashboard-lmps

Destino:

```text
/apps/dashboard-lmps
→ /apps/engineering/lmps
```

Rotas de NC/detalhe precisam de mapa específico com chaves reais. Não usar redirect genérico que perca a LMP/NC selecionada.

Antes do hard cutover, provar lista, detalhe, produtos, histórico, Gantt e NCs, inclusive escrita.

## 5. Permissions

Cutover de UI não pode preceder migração de autorização.

Procedimento:

1. extrair usuários/grupos/roles com permissions legadas;
2. calcular mapping para capabilities `engineering.*`;
3. revisar ampliações/reduções;
4. provisionar de forma idempotente;
5. testar personas positivas e negativas;
6. só então alterar menu/redirect.

Nunca usar superadmin como única evidência.

## 6. Deep links

Inventariar consumidores internos antes da troca:

- Portal/launcher;
- Home de outros portais;
- Chat/AI action targets;
- notificações;
- documentos/wiki;
- e-mails/atalhos;
- rotas de integração;
- favoritos persistidos.

Cada link recebe destino:

```text
PRESERVAR
REDIRECT
ATUALIZAR_PRODUCER
MANTER_LEGADO
SEM_EQUIVALENTE_COM_ACEITE
```

## 7. Dados

O cutover dos dashboards é principalmente de leitura/composição; não criar migração de dados TOTVS para o Portal.

Estado novo da Sala permanece no schema do `engineering-api` e não participa de rollback para os dashboards legados. Se o Portal for despromovido, preservar dados da Sala e bloquear apenas UI conforme incidente/política.

## 8. Observação pós-soft-cutover

Monitorar:

- erros 4xx/5xx;
- timeouts por downstream;
- 403 inesperados;
- rota 404/deep link;
- remoteEntry/mount;
- socket/reconnect da Sala;
- falhas FILESERVER;
- divergência de indicador;
- feedback dos usuários.

Definir janela e thresholds antes do GO; não escrever números arbitrários no runbook sem baseline.

## 9. Rollback

### Soft cutover

Rollback simples:

- restaurar destaque/menu do legado;
- remover/promover menos o target;
- manter Portal disponível para diagnóstico se seguro.

### Redirect

- reverter regra no gateway/Portal;
- restaurar rota legada;
- não apagar dados do target.

### Hard cutover

Só executar depois de janela de estabilidade e backup/artefato do legado. Para rollback tardio, reconstruir imagem/manifest da versão conhecida e reativar com permissions originais.

## 10. Stop-the-line

Abortar cutover se houver:

- perda de permission/IDOR;
- divergência material de indicador não explicada;
- NC escrita quebrada;
- deep link crítico sem destino;
- taxa de erro/timeout incompatível com baseline;
- dados ausentes apresentados como zero;
- FILESERVER expondo path/credencial;
- regressão federada grave;
- rollback não testado.

## 11. Evidência de GO

Checklist:

```text
[ ] GATE-ARCH PASS
[ ] GATE-AUTHZ PASS
[ ] GATE-RBAC PASS
[ ] GATE-MFE PASS
[ ] GATE-PARITY dashboard-engineering PASS
[ ] GATE-PARITY dashboard-lmps PASS ou decisão explícita de coexistência
[ ] redirects mapeados
[ ] personas reais validadas
[ ] backup/artefatos legados disponíveis
[ ] rollback ensaiado
[ ] Help atualizado
[ ] observabilidade ativa
[ ] Product Owner autorizou o cutover
```

## 12. Pós-cutover

- documentar versão/data;
- manter redirects pelo período aprovado;
- remover código/infra legado somente em etapa separada;
- atualizar inventário e docs de plataforma;
- remover planos `.cursor` concluídos;
- registrar pendências P1/P2 fora do caminho crítico.
