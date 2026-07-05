export type ComunicadoFrame = {
  x: number;
  y: number;
  w: number;
  h: number;
};

export type ComunicadoBlockStyle = {
  fontSize?: number;
  color?: string;
  textAlign?: "left" | "center" | "right";
  fontWeight?: "normal" | "bold";
  objectFit?: "cover" | "contain";
};

export type ComunicadoBlockBase = {
  id: string;
  type: "heading" | "text" | "image" | "video";
  frame: ComunicadoFrame;
  style?: ComunicadoBlockStyle;
};

export type ComunicadoTextBlock = ComunicadoBlockBase & {
  type: "heading" | "text";
  content: string;
};

export type ComunicadoMediaBlock = ComunicadoBlockBase & {
  type: "image" | "video";
  assetId?: string;
  url?: string;
};

export type ComunicadoBlock = ComunicadoTextBlock | ComunicadoMediaBlock;

export type ComunicadoBackground =
  | { type: "color"; value: string }
  | { type: "image"; assetId?: string; url?: string; value?: string };

export type ComunicadoConfig = {
  version?: number;
  headline?: string;
  subtitle?: string;
  background?: ComunicadoBackground;
  blocks?: ComunicadoBlock[];
};

export type ComunicadoScreenData = {
  version?: number;
  headline?: string;
  subtitle?: string;
  background?: ComunicadoBackground;
  blocks?: ComunicadoBlock[];
};
