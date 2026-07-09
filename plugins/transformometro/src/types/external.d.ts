declare module "mermaid" {
  interface MermaidConfig {
    startOnLoad?: boolean;
    securityLevel?: string;
    theme?: string;
  }

  interface MermaidAPI {
    initialize: (config: MermaidConfig) => void;
    render: (id: string, code: string) => Promise<{ svg: string }>;
  }

  const mermaid: MermaidAPI;
  export default mermaid;
}

declare module "html-to-image" {
  export function toPng(node: HTMLElement, options?: Record<string, unknown>): Promise<string>;
  export function toSvg(node: HTMLElement, options?: Record<string, unknown>): Promise<string>;
}
