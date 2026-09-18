# ADR — Portal Transforma+ como experiência sobre o domínio Transformômetro

**Status:** TARGET documentado (2026-09-18). **Não implementado.**  
**Documento:** [`PORTAL-TRANSFORMA-PLUS.md`](../../../docs/12-roadmap-e-evolucao/transformometro-app/PORTAL-TRANSFORMA-PLUS.md)  
**Ciclo de domínio:** [`CICLO-INTELIGENCIA-DE-PROCESSO.md`](../../../docs/12-roadmap-e-evolucao/transformometro-app/CICLO-INTELIGENCIA-DE-PROCESSO.md)

## Contexto

O MFE `transformometro` hoje navega por Dashboard, Processos, Atas, Configurações e Exportar/Importar. O Portal Comercial já prova um shell de produto (Início, Visão geral, Sala, tarefas, lista operacional, carteira, administração, ajuda) montado sobre primitivos de `@delpi/plugin-ui`.

A decisão de produto é dar ao programa de transformação a experiência **Portal Transforma+**, usando o Comercial como referência de UX.

## Decisão

1. **Portal Transforma+ é a experiência de produto.** Não é bounded context, não é API e não é dono de processo, medição, diagnóstico, evidência, diagrama ou ata.
2. **Transformômetro permanece a autoridade de domínio** dessas capabilities, inclusive as que o ciclo de inteligência ainda marca como TARGET.
3. **Não renomear** neste ciclo: `transformometro-api`, schemas, tabelas, packages, MCP, GPT Actions, URLs, OpenAPI, nomes internos de domínio. Renomeação técnica exige ADR próprio.
4. **Reuso visual ≠ acoplamento de domínio.** O MFE Transformômetro não importa internals do Comercial. O Comercial não vira owner de componente de domínio Transforma+.
5. Componente genérico já em Core, Portal host ou `@delpi/plugin-ui` pode ser reutilizado. Componente que vive só no Comercial só sai de lá se passar no Abstraction Gate. Duas telas parecidas não bastam.
6. Página de UI não cria rota HTTP, tool MCP nem GPT Action. Home, overview, «meus processos» e portfólio consomem leituras já existentes (`search_records`, `get_record`, `get_process_context`, `analyze` / dashboard) até um read model com contrato próprio ser justificado.
7. Menu oculto, perfil, cargo e favorito não autorizam. AuthZ continua no backend. Capability do portal e do TÉO ≤ capability do usuário autenticado.

## Consequências

- Branding pode evoluir sem migração de backend.
- Contratos, MCP e Actions permanecem estáveis neste passe.
- Risco de migração cai porque não há rename em massa.
- Salas de interação, tarefas e favoritos do Comercial são domínio daquele contexto. Não são infraestrutura compartilhada comprovada.
- Implementação permanece **não autorizada**.
