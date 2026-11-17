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
