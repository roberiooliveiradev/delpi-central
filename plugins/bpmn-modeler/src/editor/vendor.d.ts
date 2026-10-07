declare module "bpmn-js-properties-panel" {
  import type { ModuleDeclaration } from "didi";

  export const BpmnPropertiesPanelModule: ModuleDeclaration;
  export const BpmnPropertiesProviderModule: ModuleDeclaration;
}

declare module "@bpmn-io/properties-panel" {
  import type { FunctionComponent } from "preact";

  /** Componente de grupo colapsável do vendor — reutilizado por providers
      customizados (ex.: grupo "Configurações avançadas"). */
  export const Group: FunctionComponent<{
    element?: unknown;
    id?: string;
    label?: string;
    entries?: unknown[];
    shouldOpen?: boolean;
  }>;

  /** Popup container do vendor (runtime export `Popup`). */
  export const Popup: FunctionComponent<Record<string, unknown>> & {
    Title: FunctionComponent<Record<string, unknown>>;
    Body: FunctionComponent<Record<string, unknown>>;
    Footer: FunctionComponent<Record<string, unknown>>;
  };
  export const PopupTitle: FunctionComponent<Record<string, unknown>>;
  export const PopupBody: FunctionComponent<Record<string, unknown>>;
  export const PopupFooter: FunctionComponent<Record<string, unknown>>;
}
