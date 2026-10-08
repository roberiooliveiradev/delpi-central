/* eslint-disable @typescript-eslint/no-explicit-any */
// Declarações mínimas da superfície vendor consumida pelo produto —
// `any` reflete o contrato loose/dinâmico do vendor (moddle objects,
// injector services) sem gerar ruído de casting em cada call site.
declare module "bpmn-moddle" {
  /** Superfície mínima usada por testes do boundary (G4-EXT-1). */
  export class BpmnModdle {
    constructor(packages?: Record<string, unknown>);
    fromXML(
      xml: string,
      typeName?: string,
    ): Promise<{ rootElement: Record<string, unknown> }>;
    toXML(
      element: Record<string, unknown>,
      options?: { format?: boolean; preamble?: boolean },
    ): Promise<{ xml: string }>;
  }
}

declare module "bpmn-js-properties-panel" {
  import type { ModuleDeclaration } from "didi";

  export const BpmnPropertiesPanelModule: ModuleDeclaration;
  export const BpmnPropertiesProviderModule: ModuleDeclaration;
  /** hook do properties panel — resolve serviços do injector do modeler. */
  export function useService(name: string): any;
}

declare module "bpmn-js/lib/util/ModelUtil" {
  export function is(element: any, type: string): boolean;
  export function getBusinessObject(element: any): any;
}

declare module "bpmn-js/lib/features/modeling/util/ModelingUtil" {
  export function isAny(element: any, types: string[]): boolean;
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

  /** Entries leaf do vendor — chamados como função (mesmo padrão do
      renderer `{...entry}`: o descriptor recebe props posicionais). */
  export const TextFieldEntry: FunctionComponent<Record<string, unknown>>;
  export const CheckboxEntry: FunctionComponent<Record<string, unknown>>;
  export function isTextFieldEntryEdited(node: unknown): boolean;
  export function isCheckboxEntryEdited(node: unknown): boolean;

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
