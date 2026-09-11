# ADR-004 — Sala de interação pertence ao Portal de Engenharia

- **Status:** Accepted no nível de ownership; protocolo físico ainda depende de decisões P-01…P-05
- **Data:** 2026-09-11

## Contexto

O Portal Comercial possui uma Sala de interação madura, mas `commercial-api` pertence ao bounded context Comercial. Reutilizá-lo como backend de Engenharia criaria acoplamento entre domínios e permissions inadequadas.

## Decisão

A Sala de Engenharia pertence ao `engineering-api` e persiste estado próprio no schema do contexto.

O Comercial serve como referência de experiência/protocolo. Componentes puramente visuais e genéricos podem ser extraídos/evoluídos em `@delpi/plugin-ui` quando houver reutilização comprovada.

## Invariantes

- mensagem não altera status oficial de LMP/MP/NC;
- persist-before-publish;
- membership/resource scope fail-closed;
- identidade baseada no usuário canônico, sem cadastro paralelo;
- room ID conhecido não concede acesso;
- realtime independente do `commercial-api`;
- menções/anexos/reactions seguem contratos tipados;
- offline notification usa Core/catalog próprio quando aprovado.

## Decisões abertas antes da implementação produtiva

1. unicidade de sala por contexto;
2. membership automático/manual;
3. retenção;
4. storage de anexos;
5. tecnologia realtime Flask-compatible.

Essas decisões permanecem em `DECISOES-FUNCIONAIS-PENDENTES.md` e bloqueiam as subetapas correspondentes, não a fundação do Portal.
