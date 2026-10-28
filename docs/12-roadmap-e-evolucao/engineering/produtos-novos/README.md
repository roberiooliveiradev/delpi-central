# Produtos Novos — Portal de Engenharia

**Estado:** TARGET / PROPOSED — documentação de produto e UX, sem implementação ou autorização de publicação.  
**Processo:** PROC-0073 — Acompanhamento de Produtos Novos na Produção.  
**Origem de negócio:** Transforma+ / GLPI #1153; AS-IS documental v0.3; TO-BE candidato v0.2.  
**Nomenclatura escolhida pelo solicitante:** **Produtos Novos**.  
**Subtítulo proposto:** Planejamento e Acompanhamento da Produção.

Este pacote é uma **funcionalidade/ferramenta do Portal Engenharia**, não um novo produto, MFE, bounded context ou fonte canônica de OPs, desenhos, BOM e roteiros. Segue a documentação mestra [Portal Engenharia](../README.md), especialmente as decisões de TopBar, `@delpi/plugin-ui`, `engineering-api`, Core RBAC e integrações autorizadas.

## Documentos
- [01-VISAO-E-ESCOPO.md](./01-VISAO-E-ESCOPO.md) — objetivo, atores, escopo, regras e limites.
- [02-UX-PAGINA-INICIAL.md](./02-UX-PAGINA-INICIAL.md) — navegação, wireframe textual, estados e componentes.
- [03-FLUXO-TO-BE.md](./03-FLUXO-TO-BE.md) — fluxo híbrido, desvios, responsabilidades e estados.
- [04-REQUISITOS-CONTRATOS-ACEITE.md](./04-REQUISITOS-CONTRATOS-ACEITE.md) — RQ, AC e contratos a inventariar.
- [05-DECISOES-ROADMAP.md](./05-DECISOES-ROADMAP.md) — evidência, riscos, decisões e evolução.

## Regras de autoridade
- Keycloak: identidade/SSO; Core: app/rota/RBAC; Portal Engenharia: experiência; `engineering-api`: BFF alvo; Domain APIs/sistemas Engenharia/Produção: dados e regras oficiais; Transformômetro: processo de melhoria; Engenharia: aprovação técnica e publicação de desenho.
- Não acessar banco alheio ou importar internals de outro bounded context; contrato e autorização ao vivo antes de qualquer write.
- Previsão de OP não comprova produção iniciada. TO-BE não é AS-IS nem runtime.
- Não sobrescrever o BPMN AS-IS nativo do PROC-0073.
- Antes de implementar: verificar HEAD, código e contratos, aplicar Abstraction Gate, RQ/AC, menor diff, testes no SHA e documentação de outcome.

**Status dos requisitos:** PROPOSED salvo onde houver indicação de evidência ou decisão explícita. A disponibilidade de APIs Carga Máquina/OP não foi provada.

## Wireframes por página — detalhamento v0.1

| Tela | Especificação |
|---|---|
| Visão geral | [06-WF-VISAO-GERAL.md](./06-WF-VISAO-GERAL.md) |
| Programação de OPs | [07-WF-PROGRAMACAO-OPS.md](./07-WF-PROGRAMACAO-OPS.md) |
| Acompanhamentos | [08-WF-ACOMPANHAMENTOS.md](./08-WF-ACOMPANHAMENTOS.md) |
| Pendências e divergências | [09-WF-PENDENCIAS.md](./09-WF-PENDENCIAS.md) |
| Histórico e indicadores | [10-WF-HISTORICO.md](./10-WF-HISTORICO.md) |
| Detalhes da OP | [11-WF-DETALHES-OP.md](./11-WF-DETALHES-OP.md) |
| Checklist por operação | [12-WF-CHECKLIST.md](./12-WF-CHECKLIST.md) |
| Solicitar acompanhamento | [13-WF-SOLICITAR-ACOMPANHAMENTO.md](./13-WF-SOLICITAR-ACOMPANHAMENTO.md) |

São wireframes **textuais e funcionais candidatos**, não layouts visuais finais nem contratos/API provados; não houve alteração de código produtivo.

## Protótipo visual navegável

- [Abrir arquivos do protótipo](./prototipo/README.md) — instruções, escopo e limites.
- [HTML interativo (standalone)](./prototipo/index.html) — demonstração navegável das oito telas com dados fictícios; não integra API nem salva dados.

**Estado:** UX DEMO / PROPOSED. O HTML do GitHub deve ser baixado/aberto em navegador local para executar a navegação. Este protótipo não substitui o design system do Portal nem autoriza implementação.
