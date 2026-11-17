# GLPI #1612 | Posicionamento fiel ao soltar elementos no TV Dashboard

**Data:** 17/11/2026  
**Plugin:** `plugins/tv-dashboard`  
**Escopo:** editor WYSIWYG, arraste e soltura de blocos, grupo/multisseleção e preferências de encaixe.

## Incidente

O elemento podia recuar para a última posição processada em `pointermove` ao ser solto, inclusive próximo às bordas. Além disso, o encerramento de grupos podia reaplicar `gesture` anterior depois do encaixe em objetos, descartando parte do resultado do gesto. As preferências de snap chegavam ao handler via refs atualizados em `useEffect`, não sincronicamente no clique do toggle.

## Correção

- `useCanvasBlockInteraction`: processar a coordenada recebida em `pointerup` antes de finalizar e persistir o gesto.
- `useComunicadoEditorDrag`: quando há encaixes sucessivos no grupo, usar sempre `finalGesture`, sem sobrescrever o resultado anterior com o estado de entrada.
- `useComunicadoEditorStage`: atualizar refs de grade/objetos no mesmo evento que altera cada preferência.
- Preservar o contrato de posicionamento livre (`snapToGrid=false` e `snapToObjects=false`): coordenadas fracionárias e próximas/fora das bordas, sem margem artificial; regras de tamanho e limites canônicos permanecem inalteradas.

## Verificação

Regressões adicionadas:
- `finalizeMultiFramesWithSnap.test.ts`: soltar próximo das bordas e no pasteboard sem grade;
- `useComunicadoEditorDrag.drop.contract.test.ts`: última coordenada do ponteiro, composição de snaps no grupo e sincronização dos toggles.

**CI:** conferir resultados da PR antes do merge; nenhuma validação manual em navegador/TV está implícita nesta documentação.

## Deploy

Somente após merge da PR na `main`, no host `srv-api`:

```bash
cd /home/operador/projetos/delpi-central
git pull --ff-only origin main
bash ./infra/scripts/up-prod-sequential.sh --build tv-dashboard
```

Sem alterações de API ou migração neste escopo. Após publicar, testar no editor arraste de um bloco e de grupo com ambos os encaixes desligados e depois religados; comparar posição ao soltar e após atualizar a página.


## Investigação complementar após deploy da PR #255 (17/11/2026)

**Sintoma confirmado pelo solicitante:** o elemento continua recuando para dentro do slide após o deploy da correção frontend. O registro inicial acima permanece como histórico, mas **não solucionou o incidente**.

### Causa de backend identificada

O fluxo `PresentationPatchService` aplica o quality loop após `upsert_block`, mesmo quando o editor enviou a posição final do elemento. Se o movimento introduz `safe_area_violation` (`safeMargin=3%`) ou `block_frame_overflow`, `SafeAutoFixService._clamp_patch` recalcula as coordenadas (`x/y` no mínimo `3%`) e pode reduzir `w/h`. Esse estado modificado retorna no ACK e substitui a posição escolhida no editor. Para colisões, `block_overlap` também poderia produzir um relayout involuntário.

### Correção complementar

No quality loop de `tv-dashboard-api/tv_app/application/services/data/presentation_mutation/patch_service.py`:

- Os identificadores com `frame` explicitamente informado em `upsert_block`/`create_block` passam a ser protegidos contra *autocorreções de geometria* geradas pelo próprio movimento: `safe_area_violation`, `block_frame_overflow`, `block_frame_non_positive`, `block_overlap`.
- A auditoria e seus avisos continuam sendo calculados e exibidos, sem apagar a evidência de possíveis problemas de layout.
- As correções automáticas não geométricas (ex.: contraste em conteúdo novo) permanecem ativas.
- A operação `apply_safe_layout_fixes` continua permitindo ajuste de margem e reposicionamento **quando explicitamente solicitada**.
- Não é alterada a normalização canônica de coordenadas/tamanhos nem o comportamento dos ímãs no frontend.

**Testes integrados:** `tv-dashboard-api/tests/test_safe_layout_quality_loop.py` cobre posição fracionária junto às bordas, posicionamento fora do slide (pasteboard), sobreposição intencional e correção solicitada explicitamente.

**Publicação:** essa etapa altera **somente a API**, não apenas o plugin frontend. Após merge da PR complementar, no `srv-api`:

```bash
cd /home/operador/projetos/delpi-central
git pull --ff-only origin main
bash ./infra/scripts/up-prod-sequential.sh --build tv-dashboard-api
```

**Validação operacional obrigatória:** desligar encaixes Na grade e Objetos, arrastar um bloco até x<3% e y<3%, soltar, esperar o ACK e atualizar a página. Posição e dimensão devem ser preservadas. Repetir com blocos parcialmente fora do slide, grupos e encaixes religados. O chamado permanece aberto até aprovação do usuário em produção.

