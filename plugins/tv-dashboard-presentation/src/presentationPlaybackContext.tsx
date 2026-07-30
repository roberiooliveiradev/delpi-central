import { createContext, useContext, type ReactNode } from "react";

export type PresentationPlaybackValue = {
  /** Pausa do avanço automático do deck (Espaço / Retomar). */
  deckPaused: boolean;
};

const DEFAULT: PresentationPlaybackValue = { deckPaused: false };

const PresentationPlaybackContext = createContext<PresentationPlaybackValue>(DEFAULT);

export function PresentationPlaybackProvider({
  deckPaused,
  children,
}: {
  deckPaused: boolean;
  children: ReactNode;
}) {
  return (
    <PresentationPlaybackContext.Provider value={{ deckPaused }}>
      {children}
    </PresentationPlaybackContext.Provider>
  );
}

export function usePresentationPlayback(): PresentationPlaybackValue {
  return useContext(PresentationPlaybackContext);
}
