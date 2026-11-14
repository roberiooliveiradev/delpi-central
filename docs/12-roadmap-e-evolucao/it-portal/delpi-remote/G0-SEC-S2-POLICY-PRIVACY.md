# G0-SEC-S2 | Minuta de politica de uso e privacidade do Delpi Remote

**Status:** MINUTA para revisao de TI, Seguranca, RH e Juridico. **Gate:** G0-SEC. **Nenhum acesso remoto foi autorizado.**
**Escopo:** computadores/notebooks corporativos inscritos; sem abranger servidores TOTVS, estacoes pessoais ou acesso remoto por padrao.
**Finalidade proposta:** suporte tecnico, diagnostico e manutencao relacionados a solicitacao rastreavel no Helpdesk, e nao monitoramento de produtividade.

## 1. Modalidades de atendimento

- **Assistido:** solicitar sessao vinculada a chamado e ao dispositivo correto; identificar operador, finalidade e usuario afetado; disponibilizar aviso visivel e controle de encerramento. Consentimento operacional/aviso especifico e desenho de UX dependem de validacao juridica/RH. Nao presumir que clicar em um aviso resolva, por si so, a base legal do tratamento.
- **Nao assistido:** **DESABILITADO por padrao**. So pode ser considerado para dispositivos corporativos expressamente autorizados, com politica publicada, autorizacao nominativa do operador, finalidade, janela, justificativa/numero do chamado e trilha de auditoria. Regras de acionamento fora do expediente e de emergencia exigem decisao formal.
- **Privilegio:** operador deve autenticar com conta individual, MFA recente e RBAC especifico por modalidade/equipamento. Nao compartilhar senha do Windows, usar senha mestre de suporte ou derivar acesso remoto da credencial de coleta G2.
- **Restricoes:** por padrao sem clipboard, arquivos, shell, acesso a camera, microfone, gravacao da tela, captura de teclas, inspecao de conteudo pessoal ou controle de servidor produtivo. Cada ampliacao exige gate e testes independentes.

## 2. Transparencia e notificacao

- Antes da implantacao, RH/Juridico devem revisar comunicado aos colaboradores e atualizar normas internas aplicaveis, definindo quem pode solicitar suporte, quando a modalidade nao assistida seria possivel e como contestar acesso.
- Aviso ao colaborador deve identificar sistema e finalidade, canal para solicitar informacoes e responsavel por atendimento; descrever, em linguagem simples, o que os logs armazenam. Nao afirmar que aviso isolado autoriza qualquer operacao.
- Sessao deve indicar de forma clara quando houver controle e permitir encerramento conforme politica aprovada e requisitos tecnicos do laboratorio.
- A instalacao do **coletor de inventario G2** nao concede automaticamente capacidade de acessar tela, teclado ou arquivos.

## 3. Dados minimos e auditoria

| Categoria | Proposta | Situacao |
|---|---|---|
| Identificador de sessao | UUID aleatorio, gerado e verificado pelo broker | Desenho, ainda nao implementado |
| Operador / alvo | IDs internos do Core e UUID do computador, consultados com autorizacao fresh | Desenho |
| Chamado e justificativa | Referencia do atendimento e finalidade de manutencao | Desenho |
| Eventos | Pedido, permissao, inicio, fim, revogacao, falha de autorizacao e resultado | Desenho |
| Rede | Metadado minimo para apuracao de abuso, se justificado pela TI e Juridico | Necessidade e retencao pendentes |
| Conteudo da tela/arquivos/clipboard | **Nao coletar por padrao** | Restricao de projeto |
| Credenciais/tokens | **Nunca registrar** | Restricao de projeto |

Os logs precisam de integridade, acesso restrito por papel, horario confiavel, monitoramento de alteracoes e exclusao ao fim do prazo aprovado. **Prazo de retencao: A DEFINIR** por TI/Juridico e politica interna, sem inventar dias. Definir finalidade, base legal, controles de acesso, atendimento a titulares, incidentes e transferencias de dados antes do GO.

## 4. Responsabilidades propostas, sem designacao nominal

- **TI / responsavel pela aplicacao:** identidade forte, autorizacao, registro de atendimento, isolamento tecnico e runbook de revogacao.
- **Infra / Seguranca:** firewall, segmentacao, certificados, patching, teste de exposicao, backup/restore e resposta a incidentes.
- **RH / Juridico / encarregado indicado:** revisao de texto de comunicacao, finalidade, base legal adequada, tempo de retencao, procedimentos de direitos e registro de analise de risco.
- **Gestor da unidade:** enquadramento de uso profissional e apoio na comunicacao, sem conceder autorizacao tecnica a contas.

## 5. Condicoes de impedimento

Acesso remoto permanece **BLOQUEADO** na ausencia de qualquer um destes itens: politica revisada e publicada; dispositivo corporativo e operador na allowlist; ticket/finalidade; MFA fresh; isolamento de rede; kill switch testado; mecanismo de aviso; revisao de vulnerabilidade do motor; teste de rollback; armazenamento minimo; aceite formal de seguranca em processo **privado**.

### Pendencias para decisao privada

- Qual e a base legal aplicavel e a necessidade de DPIA/relatorio de impacto para cada modalidade?
- Quais papeis poderao autorizar acesso assistido e nao assistido?
- Qual prazo de retencao, como tratar contestacao e evidencias e como avisar colaborador ausente?
- Qual nivel de notificacao durante tela bloqueada e quais excecoes operacionais?
- Quais canais oficiais recebem solicitacoes de exercicio de direitos e de incidente?

**Esta minuta nao altera a politica corporativa existente nem autoriza controle remoto.** Nao publicar evidencias pessoais, assinaturas, IPs reais ou nomes de empregados no GitHub publico.
