# DÉLIA — Evidência visual do Companion Dock em Portal real

**Data:** 2026-10-19 (horários visíveis nas capturas: cerca de 09:50–09:52, fuso da interface não verificado).  
**Origem:** três capturas de tela fornecidas pelo Product Master nesta conversa; as imagens não foram anexadas como binários ao repositório.  
**Natureza:** observação visual manual de interface; não é log de teste, captura de rede, Playwright nem evidência de AuthZ.  
**HEAD de documentação observado:** `a4354d101c85bd6e1375ad2a969bf419d0fc9106`; SHA/configuração efetivamente implantados no Portal: **TO_INVENTORY**.

## Fatos visíveis

1. **Durante a interação:** o Dock exibe avatar da DÉLIA com apresentação de atividade, texto “Entendendo sua solicitação...” e controle “Interromper resposta”; o composer mantém a solicitação digitada.
2. **Após a interação anterior:** o Dock exibe resposta contendo uma lista de dez registros e indicação de fonte `transformometro-api` com horário exibido; o composer volta a oferecer “Enviar”. A indicação de fonte é dado apresentado na UI, **não** verificação independente da fonte ou dos registros.
3. **Outra interação:** o Dock mostra mensagem “Atividade bloqueada”, indicação “Fonte indisponível”, explicação de que não foi possível consultar fonte autoritativa e ausência de fonte vinculada. Isso prova a **representação visual** da indisponibilidade, não a causa técnica ou o postcondition no serviço de domínio.

## Classificação

| Cenário | Resultado | Limite da evidência |
|---|---|---|
| RENDER_DOCK_EM_PORTAL_REAL | PROVEN (captura fornecida) | Não comprova SHA deployed, autorização backend ou testes automatizados |
| PROCESSING_VISUAL | PROVEN (captura fornecida) | Não comprova request trace ou cronologia exata |
| EXIT_PROCESSING_VISUAL | PROVEN (captura de estado posterior) | Não comprova transição `responding` one-shot |
| SOURCE_UNAVAILABLE_VISUAL | PROVEN (captura fornecida) | Não comprova origem da falha nem regra de domínio |
| RESPONDING_ONE_SHOT | INCONCLUSIVE | Requer animação capturada via browser automation |
| ABORT_REQUEST_REAL | TEST_NOT_RUN | Requer trace de request, abort e resposta tardia |
| KEYBOARD_AND_SCREENREADER | TEST_NOT_RUN | Não demonstrado pelas capturas |
| PORTAL_DOCK_AUTOMATED_QA | TEST_NOT_RUN | Capturas manuais não encerram E09/E10 |

## Decisão de produto e continuidade

O Product Master declarou o layout do Dock satisfatório. Não abrir novo ciclo de refinamento visual sem defeito comprovado. Próximos esforços de implementação devem priorizar componentes ainda não implementados, com inventário/reuse gate antes de código. Os residuais de browser (responding one-shot, abort real, teclado e testes integrados autenticados) permanecem registrados para execução posterior; nenhuma fase/aceite é promovido por estas imagens.

**EXISTING_EQUIVALENT=YES** para a superfície Dock e os estados exibidos. **REUSE_DECISION=REUSE**. **PHASE_PROGRESSION=NONE**.
