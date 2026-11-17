# UX Workspace V4 — simples, visual e tabular

**Status:** TARGET / WIREFRAME_TEXT / VISUAL_NOT_APPROVED. Não há protótipo renderizado deste desenho.  
**Inspiradores:** experiência limpa do Yamazo Studio; barras detalhadas e operações ligadas ao gráfico; edição em tabela; comparação antes/depois. Não copiar telas, assets ou estilos de terceiros.

## Princípios
1. Uma ação primária por etapa, sem formulário gigante na primeira dobra.
2. `Visual` e `Tabela` são **views do mesmo estudo**, seleção persistente e edições sincronizadas.
3. Mostrar somente parâmetros relevantes ao método; seis métodos no catálogo, não seis painéis permanentes.
4. Progresso e classificação: `Origem`, `Operações`, `Condições`, `Balancear`, `Comparar`.
5. Números editáveis com campo preciso e incrementos; drag-and-drop opcional, fallback acessível.
6. Status de gravação honesto (`Salvo nesta aba`, `Não salvo`, `STALE`).
7. Gráfico + tabela podem dividir espaço no desktop, virar seções empilhadas no mobile.

## Wireframe desktop
```text
DELPI LINE BALANCE STUDIO                     [Estudo A v] [Novo] [Limpar]
[Produto DELPI] [Novo processo] [Importar (planejado)]
-------------------------------------------------------------------------------
[Dados de origem / código produto OU título processo manual] [Abrir]
[Operações (N)] [Tempo total] [Takt] [Postos]  *status e provenance*
-------------------------------------------------------------------------------
CONDIÇÕES: [Turno: início 07:30 | fim 16:30] [Pausas (2) editar]
          [Demanda -  +] [Lote - +] [Postos - +] [Tempo produtivo]
-------------------------------------------------------------------------------
[Visual | Tabela]    [Método: M5 Yamazumi v]    [s|min] [Exportar]
OPERACÕES DISPONÍVEIS      CONFIGURAÇÃO DE POSTOS         YAMAZUMI
[+] Operação               [P01] +atribuir              |-- takt --|
[código] [tempo]           [P02] +atribuir              [barras empilhadas]
[editar] [mover]           [Novo posto]                 [hover/seleção]
-------------------------------------------------------------------------------
[Não atribuídas] [Acima do takt] [Restrições] [Cenário A x B]
[Resultados do método] [Proveniência] [Limitações]
```

## Wireframe mobile
```text
[Nome do estudo] [Menu ações]
[Origem v] [Operações resumidas]
[Condições ▾] [Método v]
[Visual | Tabela]
[Postos ▾] [Operações disponíveis ▾]
[Yamazumi responsivo, scroll próprio quando necessário]
[Avisos e resultados]
```

## Estados UX
- Escolha de fonte: produto, manual, importação ainda não disponível.
- Produto: sem código, pesquisando, erro de sintaxe, 403, 404, roteiro vazio, multi-stage, truncado e pronto.
- Manual: estudo vazio, operação em edição, sem tempo, operação válida, duplicidade de ID.
- Turno: incompleto, pausa inválida, sobreposição, atravessa meia-noite, pronto.
- Yamazumi: zero postos, posto vazio, operação não atribuída, parcial sem tempo, acima do takt, takt desconhecido, cenário `STALE`.
- Permissão revogada/storage bloqueado: fechar acesso/avisar, não alegar persistência.
- Exportação: desabilitar resultados ainda não calculados; oferecer exportação de rascunho com etiqueta explícita quando suportado.

## Acessibilidade e temas
Focus visível, labels de campos, botões com nomes; teclado para mover operações; contraste light/dark; tooltip não é única fonte de informação. Não depender só da cor para destaque; labels textuais. Zoom 200%; breakpoints 1440/1024/390/320; sem scroll horizontal na página inteira.

## Regras de componente
Usar `@delpi/plugin-ui` para todos os controles e gráficos genéricos. `Studio` compõe interfaces; componentes específicos reutilizáveis podem viver no próprio pacote. Novos componentes no kit só se apresentarem uso genérico comprovado.
