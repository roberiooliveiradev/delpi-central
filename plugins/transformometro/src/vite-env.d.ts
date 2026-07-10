/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TRANSFORMOMETRO_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module "@delpi/plugin-ui/styles";
