# Suppliers F4 — Retorno do Gabriel (owner da API REST Protheus)

**Data da resposta:** 2026-10-21. **Origem:** e-mail de Gabriel Araújo, assunto `Re: API Fornecedor X MinhaDelpi`, captura compartilhada pelo PO; evidência de comunicação, **não prova de deploy/código**. Credenciais e dados pessoais desnecessários não transcritos.

## Retorno nos seis tópicos

| Tema | Resposta do owner | Classificação | Próxima prova |
|---|---|---|---|
| REST porta 8701 usa DELPI_TST01? | **Sim**; Gabriel citou imagem de teste como evidência, não incluída nesta captura | **OWNER_CONFIRMED / PROVEN documental** | Manter evidência SQL+GET F4.2; mapa DBAccess formal se necessário |
| Endpoint REST produtivo DELPI | Gabriel informou que verificaria e enviaria a informação | **PENDING** | URL, ambiente, serviço/DBAccess e GET comparado à SQL DELPI |
| POST retornar código+loja | Gabriel informou que faria ajuste quando estivesse pronto | **PLANNED** | Contrato de sucesso, código+loja, deploy homolog e POST+GET reconciliação |
| Campos obrigatórios POST | Gabriel se comprometeu a enviar a relação | **PENDING** | Matriz oficial e validações por campo/tipo |
| Campos mutáveis PUT e restrições | Gabriel se comprometeu a enviar a relação | **PENDING** | Matriz PUT validada, limpeza/omissão e testes |
| Timeout/erro após Execauto | Gabriel sugeriu tabela intermediária com status de integração (1 Enviado ao Protheus; 2 Integrado com Sucesso; 3 Erro Não Integrado), gravar erros e painel futuro | **PROPOSAL, NOT APPROVED** | ADR/contrato de ownership e reconciliação, não implementar automaticamente |

## Decisão técnica provisória

**A confirmação do owner fecha a dúvida sobre a base de testes**: REST `:8701` é `DELPI_TST01`. O relatório F4.2 já havia comprovado por SQL o registro `003878/01` e GET REST coincidente. A listagem operacional usa `DELPI`. **Persistência em produção continua BLOCKED**; gates CREATE/UPDATE permanecem OFF na última verificação reportada, revalidar runtime antes de atuar.

A proposta de acompanhamento de integração é material e merece análise própria: não colocar tabela duplicando dados TOTVS no Postgres do supplies por conveniência, nem assumir owner antes de ADR. Distinguir `REQUEST_ACCEPTED`, `SENT`, `ACKNOWLEDGED`, `PERSISTENCE_CONFIRMED`, `REJECTED`, `OUTCOME_UNKNOWN`; sem retry automático em POST/PUT em caso indeterminado. O esquema de estados é **candidato de desenho**, não contrato homologado, e não deve ser imposto ao Gabriel sem alinhamento.

## Próxima ação

1. Aguardar informações prometidas sobre endpoint de produção, retorno POST e matrizes POST/PUT.
2. Solicitar reunião com Gabriel para discutir owner da trilha de integração, chave de correlação, idempotência, confirmação por GET/SQL, tratamento de timeout e painel futuro; manter boundary `api-delpi` para regra TOTVS e `supplies-api` para composição do produto.
3. Enquanto aguarda, continuar evolução F5 de consulta CNPJ estruturada read-only, sem LLM obrigatório, sem ativar gravação produtiva.
4. Quando o contrato novo chegar, reancorar HEAD, inspecionar código/ADRs, classificar `EXECUTION_DRIFT` se necessário e executar gate controlado em ambiente correto.

**GATE:** resposta do Gabriel não equivale a autorização para trocar `URL_REST` nem ligar CREATE/UPDATE. Sem novas escritas nesta documentação.

## Referências

- `api-delpi/docs/integrations/protheus-rest-supplier-api-contract.md`
- `api-delpi/docs/integrations/protheus-rest-supplier-write-handoff.md`
- `docs/12-roadmap-e-evolucao/supplies/evidence/suppliers-f4-post-put-sql-persistence-gabriel-handoff-2026-10-20.md` (se já integrado da branch documental anterior)
