/**
 * Multi-seleção de telas abre a aba Tela — não Elemento (blocos do palco).
 * Voltar a 1 tela não troca a aba: o usuário pode continuar em Tela ou Programação.
 */
export function resolveSlideBatchRibbonTab(input: {
  selectedSlideCount: number;
  currentTab: string;
}): "slide" | null {
  if (input.selectedSlideCount > 1 && input.currentTab !== "slide") {
    return "slide";
  }
  return null;
}
