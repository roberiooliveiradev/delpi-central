# 05 — Decisões, riscos e roadmap

## Decisões confirmadas como intenção de produto
- **Produtos Novos** é o nome da ferramenta do Portal Engenharia.
- Modelo **B — integrado e rastreável**, com **previsão por programação Carga Máquina/OP** e **acionamento manual pelo líder**.
- Engenharia requer visão antecipada por semana, mês e período selecionado.
- AS-IS: Engenharia acompanha matriz; Qualidade acompanha filial com checklist, comunica por e-mail resultados divergentes ou conformes à Engenharia da matriz, que corrige e remove identificação do desenho.

## Lacunas / TO_INVENTORY
- Presença, endpoints e capacidades reais da API do Portal Engenharia em branch e SHA atuais (o README mestre de set/2026 registra target ainda não existente em main; pode ter evoluído).
- Owner e contrato de Carga Máquina/OP; classificação 'Produto Novo'; data de produção e reprogramação.
- Quem autoriza parada, retomada, avaliação e publicação do desenho; responsável local e gestor formal do processo.
- Owner da persistência de acompanhamento/checklist, idempotência, eventos, audit trail e indicadores.
- Escopo RBAC, navegação, padrão visual real do Portal e estados disponíveis em `@delpi/plugin-ui`.

## Riscos
- Confundir previsão com início; colisões de OP; indicador desatualizado; falha de integração; inconsistência entre desenho e produção; acesso entre unidades; duplicidade e perda de eventos; publicação técnica não autorizada.

## Plano de evolução (sem autorização de implementação)
- **D0 — Inventário**: HEAD/status, authorities, código e contratos existentes, regras `.cursor`; classificar PROVEN/TO_INVENTORY.
- **D1 — Produto/UX**: validar jornada, personas, mockups kit-first, campos e filtros; congelar AC de UX.
- **D2 — Contratos**: definir owner e APIs oficiais, segurança, idempotência, mudanças de OP e eventos.
- **D3 — MVP controlado**: planejar lista de OPs de produtos novos e acionamento manual, somente após contratos verificados.
- **D4 — Acompanhamento**: checklist, divergências, notificações e rastreabilidade, medidos com casos reais.
- **D5 — Encerramento e evolução**: conclusão governada, evidências, indicadores e homologação multidisciplinar.

**Gate:** mudanças de bounded context, owner, fonte de verdade ou authority exigem ARCHITECTURE_DECISION_REQUIRED e retorno à Coordination. `PROPOSED` não significa `READY`, commit de documentação não autoriza código nem prova runtime.
