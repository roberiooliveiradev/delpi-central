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
}
