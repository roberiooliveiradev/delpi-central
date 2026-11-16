# Chamado GLPI #1597 — despesas de viagem

Data: 2026-11-16. **Escopo:** correção monetária, modal de Deslocamento e envio ao Financeiro.

## Contratos e decisões
- Categoria **Deslocamento** já existente (`ground_transport`): modal opcional em registros legados, obrigatório em novos lançamentos; três modalidades: veículo próprio (`own_vehicle`), carro de aplicativo (`ride_hailing`) e transporte público (`public_transport`). Não há nova categoria.
- Veículo próprio: distância informada pelo colaborador; tarifa consultada no servidor pela **data da despesa**. Tarifa inicial em 2026: **R$ 1,20/km**, seed em migration V004. Atualização anual: inserir nova linha em `travel_expenses.mileage_rates` com `valid_from` e valor aprovado; **não** editar linha já usada. Reembolsos existentes preservam a tarifa aplicada.
- Outros modais mantêm lançamento monetário manual. `amountBrl`, distância e tarifa têm validação Decimal no backend.
- Cupom/comprovante não teve regra alterada: **continua emitindo aviso de ausência**, mas não impede cadastro nem envio. Solicitação expressa do usuário.
- Botão **Enviar ao Financeiro**: destinatário fixo `financeiro@delpi.com.br`, CC ao e-mail persistido do autor da prestação, anexo PDF gerado no servidor. Usa credenciais corporativas Microsoft Graph com `GRAPH_REPORTS_TENANT_ID`, `GRAPH_REPORTS_CLIENT_ID`, `GRAPH_REPORTS_CLIENT_SECRET`, `GRAPH_REPORTS_MAIL_SENDER` (fallback `GRAPH_*` onde aplicável). Não logar segredos.
- Serviço guarda reserva durável em `finance_dispatches` antes de chamar Graph, evitando duplo clique e reprocessamento automático após resultado incerto. Falhas exigem conferência manual da caixa de saída. Ao aceitar Graph (202), transição `draft → submitted` com auditoria. Sem nova tentativa automática (timeout pode já ter entregue).
- **Sem integração TOTVS, aprovação ou pagamento automático.**

## Banco e endpoints
- Migration V004 (somente UP): três colunas de modal/quilometragem/tarifa em expenses; tabela `mileage_rates`; tabela `finance_dispatches`.
- GET `/apps/travel-expenses-api/mileage-rate?date=YYYY-MM-DD`: retorna tarifa vigente.
- POST `/apps/travel-expenses-api/reports/{id}/send-to-finance`: envio idempotente por reserva. Exige autor com permissão de edição e status draft; e-mail do autor e ao menos uma despesa positiva.
- API rejeita valores malformados com erro de domínio 400, sem traceback HTTP 500. Frontend aceita formatos BRL e mostra validação humana.

## Aceite e publicação
1. Executar `pytest tests -q` em `travel-expenses-api` e `npm test && npm run typecheck && npm run build` em `plugins/travel-expenses`.
2. Verificar criação/edição/exclusão das despesas existentes e totais, comparação `R$324,00` => R$324,00.
3. Selecionar Deslocamento > Veículo próprio > 270 km no dia 12/11/2026 => R$324,00. Verificar persistência da tarifa e PDF.
4. Deslocamento > Aplicativo e Transporte público: valor manual, sem quilometragem. Outras categorias sem alteração.
5. Sem cupom: aviso presente, cadastro aceito e envio permitido.
6. Usar **destinatários de testes controlados** antes do envio real em produção; validar Microsoft Graph e credenciais, status e CC. **Não enviar e-mail de teste para financeiro@delpi.com.br antes da publicação aprovada**.
7. Inspecionar migrations/backups e homologar antes de merge ou deploy em produção.

## Limites conhecidos e recuperação
- Em `finance_dispatches` com status `failed` ou `sending`, **não** reenviar automaticamente. Conferir Graph / Itens Enviados e registrar evidência; retomar via procedimento operacional aprovado, sem alteração manual rotineira de dados.
- Status de entrega `sent` significa aceitação da API Graph (HTTP 202), **não leitura pelo Financeiro**.
- Sem testes reais de credenciais SMTP/Graph na PR, a integração só pode ser validada no ambiente autorizado.
