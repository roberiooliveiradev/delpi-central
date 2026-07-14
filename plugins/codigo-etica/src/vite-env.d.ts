/// <reference types="vite/client" />

declare module "@delpi/plugin-ui/styles";

declare module "*.svg" {
  const src: string;
  export default src;
}

