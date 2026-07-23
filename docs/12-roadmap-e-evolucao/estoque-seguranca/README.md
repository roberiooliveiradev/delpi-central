# Estoque de Segurança — roadmap

## Escopo entregue

- Listagem e KPIs de MPs vs estoque de segurança (SBZ × SB2)
- Detalhe em modal central com cobertura SC7, empenhos SD4 e extrato cronológico consolidado (01+98+99)
- Empresa padrão 01 (`*010`); filiais TOTVS `01`/`02` com RBAC granular

## Limitações conhecidas

- Data da projeção do empenho: `SC2.C2_DATPRI` da OP do empenho (`D4_OP`), não `D4_DATA` nem a OP do PA
- Empresa 05 / sufixo dinâmico de tabelas fora do escopo desta entrega
- Extrato consolidado (não abas por armazém); ESTSEG permanece no resumo consolidado

## Referências

- Plugin: [plugins/estoque-seguranca/README.md](../../../plugins/estoque-seguranca/README.md)
- API: [api-delpi/docs/api/estoque-seguranca.md](../../../api-delpi/docs/api/estoque-seguranca.md)
