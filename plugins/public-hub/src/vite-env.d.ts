/// <reference types="vite/client" />

import type { DetailedHTMLProps, HTMLAttributes } from "react";

declare module "@delpi/plugin-ui/styles";
declare module "@delpi/plugin-ui/signature";
declare module "@delpi/signature-kit";
declare module "@delpi/plugin-ui/screen-loading";
declare module "*.svg" {
  const src: string;
  export default src;
}

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "model-viewer": DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
        src?: string;
        alt?: string;
        "camera-controls"?: boolean;
        "touch-action"?: string;
        "shadow-intensity"?: string;
        exposure?: string;
        "environment-image"?: string;
      };
    }
  }
}
