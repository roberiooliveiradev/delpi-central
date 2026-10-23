# DÉLIA — VD-F06: Ditado progressivo com edição livre — Product / UX Specification

**Status:** PRODUCT_UX_SPEC / TARGET; implementação não autorizada por este documento. **Data:** 2026-10-23. **Owner visual:** plugins/plugin-ui; **consumer:** plugins/delia. **Owners técnicos de STT e admission:** conforme arquitetura e contratos canônicos. **Complementa:** docs 119 (ditado funcional), 120 (VD-F04 visual) e contracts/dictation-transcription-contract-v1.md (VD-F03). **Não substitui** esses documentos nem suas decisões congeladas.

## 1. Visão de produto e regra central

A pessoa deve poder **falar, ver a transcrição aparecer progressivamente e editar o texto durante a captura**, sem precisar finalizar a gravação para manipular o draft. Pode mover o cursor para qualquer posição, selecionar e substituir um trecho, apagar, digitar e retomar a fala no ponto escolhido. **Edição humana prevalece** sobre revisões tardias do STT. A transcrição **nunca envia a mensagem automaticamente**.

Um texto finalizado pelo STT continua sendo conteúdo editável do usuário, **não FACT**, autorização, comando executável nem confirmação de write.

## 2. Capabilities e limites

| Capacidade | Decisão UX | Estado técnico |
|---|---|---|
| Digitar/editar livremente durante captura | Obrigatória | TARGET — exige verificar limites do atual bodyOverride |
| Transcrição incremental enquanto fala | Obrigatória | TARGET / TO_INVENTORY — v1 atual recebe captura completa |
| Mostrar parcial vs confirmado | Obrigatória | TARGET |
| Cursor livre e inserção no meio | Obrigatória | TARGET — reaproveitar seleção/caret existente |
| Substituir seleção com fala | Obrigatória | TARGET |
| Preservar edições humanas sob parcial tardio | Obrigatória | TARGET |
| Pausar, retomar, finalizar, cancelar | Obrigatória no design; disponibilidade real deve ser comprovada | TO_INVENTORY |
| Editar transcrição final, enviar manualmente | Obrigatória; já existe base VD-F03 | PROVEN no contrato v1 |
| Degradar para gravação+transcrição final | Obrigatória | REUSE VD-F03 |
| Multiplataforma: full-page, Dock, mobile | Obrigatória | TARGET |
| Auto-submit / comandos por voz / execução | PROIBIDOS nesta fase | NOT_AUTHORIZED |

## 3. Aparência: uma única superfície de composer

Conservar **MessageComposer** como única moldura, sem painel flutuante ou segundo cartão. Tipografia, cor, raio, foco e espaçamento devem reutilizar os tokens de `plugin-ui`; texto não salta de posição ao entrar ou sair do modo voz.

**Layout desktop/full-page:** área editável ocupa a mesma posição de sempre; linha inferior de ações com ícone de microfone, indicador compacto de gravação, duração, pausa/retomada, finalizar e descartar; waveform discreta em faixa de baixa altura, associada a amplitude **real** captada pelo gravador. Indicador de conexão/estado só quando relevante. Contraste AA, sem depender exclusivamente de cor.

**Layout Dock:** prioridade ao texto editável; controles agrupados sem tapar o textarea; ações com rótulos acessíveis e dicas; labels visíveis apenas quando couberem, sem reduzir área de clique. Breakpoints reais da superfície, não suposição de largura de viewport.

**Mobile (320, 360, 375, 420px):** textarea editável, teclado virtual não pode esconder ações essenciais; waveform pode ser compactada/ocultada sem perder status textual; targets adequados e scroll interno correto; nada deve criar overflow horizontal da conversa/página.

**Texto transcrito:** caracteres confirmados aparecem no draft normal; **parcial reconhecido, mas ainda instável**, aparece como segmento distinto e reversível, com tratamento sutil (p.ex. sublinhado pontilhado ou tom auxiliar + texto de status para leitor de tela). Não use animação simulando digitação nem um cursor fictício. Não alterar seleção/caret do usuário por simples atualização de parcial.

**Transparência de áudio:** antes de transmitir dados a serviço remoto, aviso contextual de finalidade e processamento, conforme decisão da spec 120; não reinstalar o banner amarelo permanente removido por VD-F04. O status de microfone deve ser inequívoco mesmo com a pessoa digitando.

## 4. Estados e microinterações

| Estado | Visual | Edição e ações |
|---|---|---|
| `idle/writing` | Composer padrão | edição normal; iniciar ditado quando admitido |
| `requesting_permission` | microfone aguardando, texto contextual | draft preservado, sem declaração de gravação antes de permissão |
| `recording_listening` | mic ativo, timer real, waveform baseada em amostras | textarea editável; mover caret, selecionar, digitar; pausar/finalizar/descartar |
| `partial_transcript` | trecho provisório identificado, indicador discreto | edições humanas permitidas; novas revisões limitadas ao segmento de STT |
| `reconciling` | sem bloqueio global do editor | correlacionar versão do parcial e edição humana; não sobrescrever mudança |
| `paused` | mic em pausa explícita, tempo honesto | editar normalmente; retomar no ponto atual conforme regra de segmento |
| `finalizing` | status textual de conclusão, sem progresso falso | não bloquear edição; aplicar somente final autorizado para o segmento |
| `review` | composer normal, transcrição confirmada | revisão livre e envio manual |
| `recoverable_error` | aviso contextual, mic não ativo se encerrado | manter draft, oferecer fallback/manual; nunca descartar texto |
| `unavailable` | opção voz desabilitada/explicada | digitação normal continua |

Transições devem ser idempotentes; múltiplos cliques em finalizar não disparam múltiplas transcrições. Stop/cancel invalidam eventos tardios da sessão; ao cancelar, conteúdo **já confirmado e editado pelo usuário** não é apagado implicitamente. Diferenciar **descartar captura não confirmada** de **limpar o draft**. Se cancelar envio remoto não for garantido, comunicar que a espera local parou mas processamento remoto pode continuar.

## 5. Cursor, seleção e reconciliação: decisões explícitas

1. **Caret real do editor** é a fonte para escolher o próximo ponto de inserção, nunca o último caractere por conveniência. Inserir no fim somente se o usuário realmente estiver no fim ou se a seleção inicial não existir conforme fallback documentado.
2. Cada **segmento de fala** recebe `segmentId`, `sessionId`, revisão/ordem, momento de captura e **âncora de edição** correspondente ao caret/seleção quando o segmento iniciou. Movimento de cursor durante o segmento **não deve retroativamente mover** o texto daquele segmento.
3. Ao mover o caret e continuar a falar, **o próximo segmento** é ancorado na nova posição. Não deslocar unilateralmente o segmento atual após chegada tardia de tokens.
4. Se houver seleção, a inserção confirmada do segmento substitui **apenas a seleção capturada** quando a operação ainda for válida. Se o texto foi editado nesse intervalo, resolver conflito preservando edição humana.
5. A transcrição parcial tem um intervalo de texto de propriedade **exclusiva daquela revisão STT**; finais/substituições de parcial só podem modificar esse intervalo se ele ainda existir e não foi editado manualmente.
6. Se o usuário digitar ou apagar **dentro** da região provisória, ela perde a autoridade de substituição automática. Preservar o texto do usuário e apresentar novo STT como sugestão/pendência não destrutiva ou aguardar resolução manual; **nunca forçar overwrite**.
7. Edições fora da região provisória deslocam âncoras por operações de texto determinísticas; não usar offset absoluto velho nem append silencioso.
8. Eventos fora de ordem, duplicados, de sessão anterior ou após cancel/unmount são descartados por IDs/revisões/sequence; não reordenar palavras arbitrariamente.
9. Composição IME, colagem, undo/redo, autocorreção, ditado de pontuação, emojis, quebras de linha e seleção touch precisam de testes específicos. Não interceptar seleção para controlar o provider.
10. Uma limitação do textarea nativo sobre marcação de trecho provisório precisa ser resolvida com **menor solução legítima**; não instalar editor rich-text por conveniência. Se for necessário outro modelo/representação, aplicar Abstraction Gate e retornar decisão à coordenação.
11. Não salvar áudio, buffer, texto parcial ou posições do cursor em Personal Memory, logs comuns ou telemetry de conteúdo. Dados de telemetria devem ser mínimos e sem segredo.

**Caso de referência A:** draft “Analise os setores.”, caret antes de “setores”; usuário dita “três principais ” → resultado “Analise os três principais setores.”.

**B:** durante uma palavra parcial o usuário corrige “setor” para “linha”; resposta STT tardia tentando substituir “setor” não pode reverter “linha”.

**C:** usuário dita frase 1 no meio, move o cursor para início e dita frase 2: a frase 1 permanece onde foi ancorada, a segunda começa no início.

**D:** seleção de “última semana”; ditado confirmado “último trimestre” substitui apenas a seleção ainda válida, não outro texto que tenha ocupado o mesmo offset.

**E:** cancelamento com segmento já confirmado, edição manual e parcial pendente: manter o confirmado/editado, retirar somente o parcial ainda não admitido conforme regra UX visível.

## 6. Live transcript e contrato técnico a validar

Contrato existente `dictation.transcription.v1`: `POST /dictation/transcriptions` para um áudio **já concluído**, com merge no caret capturado no início do ditado (doc v1). **Não há evidência suficiente de streaming incremental no contrato atual.**

Investigar, nesta ordem: capability de STT no provider atual; Domain/API/MCP/provider contracts; adapter existente; modelo/transportes já previstos; limites de duração, tamanho, latência e permissões. `EXISTING_EQUIVALENT=TO_INVENTORY`; `REUSE_DECISION=TO_DECIDE_AFTER_INVENTORY` até conclusão factual.

Contrato incremental, **candidato não aprovado**, deve suportar: `session_id`, `segment_id`, `sequence`, `revision`, `is_final`, `text`, timestamps de segmento quando disponíveis, limite de payload, erro tipado, cancel e rejoin de sessão apenas se legitimamente previsto; a camada de aplicação correlaciona com as âncoras locais de edição, sem transformar timestamps STT em autoridade sobre o draft. O provider pode operar por chunks ou stream contínuo; planner e UI não devem depender de mechanics específicas.

**Preferência:** streaming real do serviço STT já adotado mediante adapter provider-neutral, quando suportado. Um recurso do navegador só entra após compatibilidade, privacidade e governança. Se sem streaming real, manter fallback de VD-F03 claramente identificado como “Transcrevendo após finalizar”; **não simular transcrição ao vivo** revelando progressivamente texto recebido no final.

## 7. Segurança, privacidade e autoridade

Permissão de microfone e envio remoto de áudio são gates distintos. Captura exige admissão da capability; credenciais e tokens nunca entram em UI/áudio/logs. Não disponibilizar áudio para outras capabilities por default. Cancelamento local não é promessa de revogação remota; UI reflete o estado verdadeiro. Nunca executar ou enviar texto como mensagem por voz sem confirmação explícita de usuário. Falha de provider não elimina conteúdo editado.

Sem novo auth engine, registry privado, scheduler, Personal Memory, parser de voz, segundo gravador ou composer. Preservar a separação de STT (texto do usuário) de comandos/actions governados.

## 8. Acessibilidade

Editor e ações por teclado, foco visível, botões nativos, nomes de controles “Iniciar ditado”, “Pausar ditado”, “Retomar ditado”, “Finalizar ditado”, “Descartar captura”; estado de gravação comunicado textualmente e com ícone, timer sem anúncios a cada segundo. Anunciar **texto confirmado por segmento** de forma agrupada, evitando que `aria-live` leia cada token/tecla; `aria-live=polite` em status resumido. Não roubar foco do editor em resultados parciais. Compatibilidade com leitor de tela real precisa de QA manual, não só testes DOM. Respeitar reduced motion, contraste e zoom 200%. Touch caret/selection deve funcionar durante gravação.

## 9. QA / acceptance matrix proposta

| ID | Critério |
|---|---|
| VD-L01 | Ao falar, parcial surge durante a captura, com origem STT real verificada |
| VD-L02 | Texto confirmado é editável sem encerrar captura |
| VD-L03 | Reposicionar caret no meio e ditar novo segmento insere nesse ponto |
| VD-L04 | Seleção substituída exatamente, sem perda de texto vizinho |
| VD-L05 | Correção manual dentro do parcial prevalece sobre STT tardio |
| VD-L06 | Movimento do caret não desloca segmento já iniciado |
| VD-L07 | Duplicados/reordenação/cancelamento descartados determinísticamente |
| VD-L08 | Digitar, apagar, colar, desfazer/refazer, IME, touch durante fala |
| VD-L09 | Pausa/retomada e finalizar conservam seleção/draft |
| VD-L10 | Falha, timeout, mic revogado preservam o texto e fallback honestamente |
| VD-L11 | Full-page + Dock real + mobile 320–420 sem sobreposição |
| VD-L12 | Foco, teclado, leitor de tela e reduced motion |
| VD-L13 | Privacidade de áudio, capacidade admitida, envio manual somente |
| VD-L14 | Regressão VD-F03/VD-F04/VD-F05/MessageComposer/Queue |
| VD-L15 | Latência percebida e texto parcial/final auditados sem números fictícios |
| VD-L16 | Streaming indisponível → fallback real v1, sem fake-live |

Estados dos testes: `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`. Não declarar `PASS` por protótipo.

## 10. Decisões pendentes e execução

1. Inventariar suporte real de provider/adapter para STT parcial e transportes de sessão.
2. Definir formato tipado incremental e postconditions do reconhecimento; preservar `dictation.transcription.v1`.
3. Validar modelo mínimo para ancoragem/reconciliação e comportamento de parcial em textarea existente; prototipar e testar conflitos **antes** de evoluir abstrações.
4. Implementar componente/estados **no plugin-ui** e integração DÉLIA por contrato; v1 permanece fallback.
5. QA áudio real pt-BR, full-page/Dock, mobile, SR quando disponível; regressões; commit/push; evidência no SHA/config.
6. Task de streaming backend e task UX podem ser divididas por ownership, mas nenhuma finge que a outra já está pronta.

**Product decision (documentado):** funcionalidade e aparência acima são alvo obrigatório de VD-F06. **Não há aprovação implícita** para criar endpoint, troca de provider, infraestrutura de streaming, novo editor ou ativação em produção.

```text
SPEC=VD-F06_PROGRESSIVE_LIVE_EDITABLE_DICTATION
SPEC_STATUS=PRODUCT_DIRECTION_DOCUMENTED
STREAMING_IMPLEMENTED=NOT_PROVEN
EXISTING_EQUIVALENT=TO_INVENTORY
REUSE_DECISION=TO_DECIDE_AFTER_INVENTORY
CURRENT_V1_FALLBACK=REUSE
OWNER_UI=PLUGIN_UI
CONSUMER=DELIA
PHASE_PROGRESSION=NONE
```
