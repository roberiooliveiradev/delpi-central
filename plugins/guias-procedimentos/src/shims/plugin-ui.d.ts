/**
 * Tipagem mínima do remote `@delpi/plugin-ui` para o `tsc` do MFE.
 * Em runtime o Module Federation resolve o pacote; não puxar o source do kit aqui.
 */
declare module "@delpi/plugin-ui/index" {
  import type { CSSProperties, ReactElement } from "react";

  export type LucideIconPickerLabels = {
    title?: string;
    searchPlaceholder?: string;
    selectedHint?: string;
    emptyHint?: string;
    clear?: string;
    close?: string;
    showingLimit?: string;
    catalogHint?: string;
    noResults?: string;
  };

  export type LucideIconPickerProps = {
    value?: string | null;
    onChange: (iconName: string | null) => void;
    onClose?: () => void;
    curatedOnly?: boolean;
    nameFormat?: "kebab" | "pascal";
    maxResults?: number;
    title?: string;
    labels?: LucideIconPickerLabels;
    className?: string;
    style?: CSSProperties;
    embedded?: boolean;
  };

  export function LucideIconPicker(
    props: LucideIconPickerProps,
  ): ReactElement;

  export function LucideIconByName(props: {
    name?: string | null;
    size?: number;
    strokeWidth?: number;
    className?: string;
    "aria-hidden"?: boolean | "true" | "false";
  }): ReactElement | null;
}

declare module "@delpi/plugin-ui/styles" {}
