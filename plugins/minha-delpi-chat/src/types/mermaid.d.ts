declare module "mermaid" {
  type MermaidConfig = Record<string, unknown>;

  type MermaidRenderResult = {
    svg: string;
  };

  type MermaidAPI = {
    initialize: (config: MermaidConfig) => void;
    render: (id: string, code: string) => Promise<MermaidRenderResult>;
  };

  const mermaid: MermaidAPI;
  export default mermaid;
}
