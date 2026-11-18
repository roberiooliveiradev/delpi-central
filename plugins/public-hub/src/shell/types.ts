import type { ReactNode } from "react";

export interface PublicPageContext {
  appId: string;
  pageId: string;
  token: string;
}

/**
 * Modo de decoração do shell. `bare` remove toda a decoração (sem
 * `pub-stage`, sem `ThemeToggle`, sem logo): a página controla tema e
 * layout — usado por formulários do kit que gerenciam o próprio tema.
 */
export type PublicChrome = "default" | "kiosk" | "fullpage" | "bare";

/**
 * Contrato que cada app implementa para expor uma página pública no shell.
 * O shell cuida do transversal (marca, loading, not-found, erro); o app só
 * carrega os dados por token e renderiza a view.
 */
export interface PublicPageDefinition {
  /** Título do documento (opcional). */
  documentTitle?: string;
  /**
   * `kiosk` oculta logo e preenche viewport (TV wall). `fullpage` estica o
   * conteúdo na viewport. `bare` remove toda a decoração do shell.
   */
  chrome?: PublicChrome;
  /** Título quando `load` retorna null/undefined (default: «Página não encontrada»). */
  notFoundTitle?: string;
  /** Mensagem exibida quando `load` retorna null/undefined. */
  notFoundMessage?: string;
  /** Carrega os dados da página. Retorne null/undefined para "não encontrado". */
  load: (ctx: PublicPageContext) => Promise<unknown>;
  /** Renderiza a view com os dados carregados. */
  render: (data: unknown, ctx: PublicPageContext) => ReactNode;
}

export type AppPublicPages = Record<string, PublicPageDefinition>;

export type PublicRegistry = Record<string, AppPublicPages>;
