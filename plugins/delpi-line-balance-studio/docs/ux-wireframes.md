# UX clean — wireframes de primeira versão

**TARGET / não renderizado.** Inspiração de produto: experiência Yamazumi simples e tabelas configuráveis, sem copiar telas ou identidades de terceiros.

## Fluxo
1. [Produto oficial] [Criar do zero] [Importar — futuro].
2. Operações (tabela editável ou visual) e elementos.
3. Condições (turno por início/fim ou duração, múltiplas pausas, demanda, lote).
4. Método (seletor M1–M6, cada um com status real).
5. Yamazumi (postos ↔ operações ↔ barras e linha de takt).
6. Cenários (A/B/Antes e Depois), exportações e limitações.

```text
DELPI LINE BALANCE STUDIO                         [Estudo A] [Novo] [Limpar]
[Produto DELPI] [Processo manual] [Importar futuramente]
[Nome/código __________] [Selecionar origem]
------------------------------------------------------------------------
[Operações] [Tempo total] [Takt] [Postos] [Origem/avisos]
[Condições ▾  Turno: 07:30–16:30 | Pausas (2) | Demanda (+ -)]
------------------------------------------------------------------------
[Método M5: Yamazumi v]       [Visual | Tabela] [s/min] [Exportar]
OPERAÇÕES DISPONÍVEIS     POSTOS                  CARGA × TAKT
[+ Adicionar]             [P01] [+ atribuir]      ---- takt
[descrição | tempo]       [P02] [+ atribuir]      ███ ███ ███
[editar]                  [+ Novo posto]         P01 P02 P03
------------------------------------------------------------------------
[Não atribuídas] [Cargas acima do takt] [Cenário A x B] [Limitações]
```

Mobile 390/320: mostrar Origem → Operações → Turno → Postos → Gráfico → Cenários em pilha; evitar scroll horizontal da página; interações por teclado/botão equivalem ao drag/drop. Só exibir opções avançadas quando necessárias.

A visualização e a tabela editam o MESMO estado; nenhuma view mantém cópia não sincronizada. Tempo agregado permanece uma única categoria quando não existir decomposição confiável.
