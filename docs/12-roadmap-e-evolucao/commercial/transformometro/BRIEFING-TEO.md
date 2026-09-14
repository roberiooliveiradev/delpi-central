# Briefing para TÉO — Portal Comercial × Transformômetro

> **Uso:** fornecer contexto confiável ao TÉO para organizar e reconciliar processos/melhorias.  
> **Não usar como:** autorização para criar, revisar ou aprovar registros sem consultar o Transformômetro real.

## Problema a resolver

O Portal Comercial consolidou capacidades que antes estavam distribuídas em outros apps da Minha DELPI e também introduziu capacidades novas/nativas. Precisamos distinguir:

1. o que já existia e provavelmente deve receber **nova revisão** no Transformômetro;
2. o que é realmente novo e pode exigir **nova melhoria/processo**, depois de verificar duplicidades;
3. o que é apenas componente técnico da solução e não deve virar item autônomo no Transformômetro.

## Processo de trabalho desta reconciliação

1. partir do Current State comprovado do Portal;
2. identificar origem técnica anterior das capacidades;
3. consultar os registros reais do Transformômetro;
4. comparar semanticamente problema/processo anterior × capacidade atual;
5. separar nova revisão de novo cadastro;
6. quando necessário, levantar evidência do processo humano real por filial/unidade;
7. somente depois pedir ao TÉO para organizar/redesenhar e propor métricas.

## Atores conhecidos pelo software

O código e a documentação suportam, entre outros:

- usuário comercial com `commercial.access`;
- gestor/admin com `commercial.manage`;
- usuários envolvidos em carteiras/membership;
- responsáveis por tarefas;
- membros de grupos operacionais;
- usuários de salas de interação;
- público de notificação de faturamento (`commercial.billing.notify`).

**PENDING:** tradução desses papéis técnicos para cargos e responsabilidades reais em cada filial/unidade.

## Capacidades atuais comprovadas

- carteiras e membership;
- Minha Carteira;
- Conta 360;
- pedidos abertos e detalhes;
- produção vinculada;
- faturamento e NF;
- analytics/Overview;
- OTD;
- oportunidades/OV;
- propostas ADY;
- tarefas/worklist;
- atividades;
- contatos;
- anexos;
- grupos operacionais;
- SLAs;
- perfis;
- Sala de Interação;
- notificações;
- auditoria;
- realtime.

## Origem conhecida

### Migração comprovada de apps anteriores

- `pedidos-venda-abertos` → Portal Comercial / `open-orders`;
- `propostas-comerciais` → Portal Comercial / `proposals`.

Os MFEs anteriores foram removidos no F2c, mas os contratos de dados na `api-delpi` permaneceram.

### Legado coexistente

- `dashboard-commercial` permanece registrado e em menu no repositório;
- há overlap com KPIs, OTD e oportunidades/OV do Portal;
- uso real em produção permanece `RUNTIME_REQUIRED`.

### Evolução de capacidade anterior

- carteiras comerciais tinham origem legada associada ao PVA;
- o estado canônico atual está no schema `commercial`;
- membership N:N vive em `seller_portfolio_members`.

### Estado nativo do Portal

Há persistência própria comprovada para tarefas, atividades, anexos, favoritos, perfis comerciais, contatos, grupos, SLAs, outbox/checkpoints e Sala de Interação.

### Experiência nova sobre dados existentes

Conta 360, produção vinculada, faturamento/NF, parte do Overview/analytics, OTD e oportunidades combinam experiência/composição do Portal com dados upstream da `api-delpi`/TOTVS e, em alguns casos, estado próprio do Comercial.

## Handoffs e esperas

**Não comprovados ainda pelo GitHub.**

O software sugere pontos de passagem entre comercial, gestão, faturamento e produção, mas não devemos tratar isso como fluxo humano real sem observação/entrevista.

## Sistemas conhecidos

- Portal Comercial (`plugins/commercial`);
- `commercial-api`;
- `api-delpi` / TOTVS;
- `core-api`;
- `strategic-indicators-api` para SI/IDD;
- `dashboard-commercial` legado coexistente;
- Postgres schema `commercial`.

**PENDING:** uso real de e-mail, Teams, WhatsApp, planilhas e outros sistemas fora do Portal.

## Métricas disponíveis tecnicamente

O Portal consome/exibe indicadores como ROL, carteira aberta, hit/closing rate, OTD, IDD, share/ranking de faturamento e outros indicadores comerciais.

Isso prova disponibilidade técnica do indicador, não que ele seja a métrica oficial de sucesso de cada transformação no Transformômetro.

## Desconhecidos obrigatórios

- IDs e conteúdo dos macroprocessos/processos/melhorias já cadastrados no Transformômetro;
- revisão atual de cada registro;
- quais filiais/unidades estão cobertas por cada processo;
- processo humano real ponta a ponta;
- trabalho manual fora do Portal;
- frequência/adoção das funcionalidades;
- resultado operacional medido;
- uso real do `dashboard-commercial` e rotas legadas PVA;
- runtime efetivo de produção.

## Hipóteses — NÃO tratar como fatos

- Pedidos e Propostas são fortes candidatos a **nova revisão** de melhorias anteriores, porque houve migração comprovada de MFEs.
- Carteiras provavelmente representam revisão/evolução de capacidade anterior, não um processo inteiramente novo.
- Minhas Tarefas e Sala de Interação são fortes candidatos a capacidades novas, mas precisam de busca no Transformômetro e evidência de processo antes de novo cadastro.
- Conta 360 pode ser uma nova composição da gestão de clientes, mas pode corresponder a uma melhoria já registrada com outro nome.
- Administração, realtime, BFFs, migrations e permission codes são componentes técnicos e não devem virar melhorias autônomas sem impacto operacional próprio comprovado.

## Restrições para o TÉO

Ao receber este briefing, o TÉO deve:

1. organizar a reconciliação sem transformar hipóteses em fatos;
2. usar o cadastro real do Transformômetro como autoridade para existência/revisão;
3. preservar separação entre processo atual e proposta futura;
4. não criar automaticamente um macroprocesso chamado “Portal Comercial”;
5. preferir associar melhorias aos processos operacionais reais;
6. sinalizar `PENDING` quando não houver evidência suficiente;
7. quando houver várias filiais/unidades relevantes, não selecionar uma silenciosamente;
8. propor métricas futuras somente depois de entender resultado operacional esperado.

## Saída desejada do TÉO

Para cada capacidade/processo reconciliado:

| Campo | Resultado esperado |
|---|---|
| Capacidade Portal | nome atual |
| Origem | app/capacidade anterior ou nativa |
| Macroprocesso existente | ID + nome ou PENDING |
| Processo existente | ID + nome ou PENDING |
| Melhoria existente | ID + título + revisão ou PENDING |
| Equivalência | total / parcial / nenhuma / incerta |
| Decisão | nova revisão / novo cadastro / sem cadastro autônomo / precisa evidência |
| Evidência | fonte que sustenta a decisão |
| Gap | o que ainda falta saber |

Nenhuma decisão deve ser materializada no Transformômetro até revisão humana do cruzamento.