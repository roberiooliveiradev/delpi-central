import type { AdminBundleNumberMeta, AdminBundleSectionMeta } from "./ChatAdminBundleSettingsPanel";
import type { ChatIntelligenceSettingMeta } from "./chatIntelligenceSettingMeta";

export const CHAT_VISION_SECTIONS: AdminBundleSectionMeta[] = [
  {
    id: "vision",
    title: "Visão de documentos",
    description: "OCR, desenhos técnicos e extração estruturada de PDFs anexados.",
  },
  {
    id: "limits",
    title: "Limites de processamento",
    description: "Teto de páginas e caracteres para equilibrar custo e latência.",
  },
];

export const CHAT_VISION_TOGGLE_META: Record<
  | "documentVisionEnabled"
  | "documentVisionAutoWithDrawing"
  | "documentVisionAutoVlmFallback"
  | "attachmentImageOcrEnabled"
  | "documentVisionStampCropEnabled"
  | "documentVisionImageDescribeEnabled",
  ChatIntelligenceSettingMeta
> = {
  documentVisionEnabled: {
    title: "Visão de documentos",
    summary: "Ativa pipeline de OCR/VLM em PDFs e imagens anexadas ao chat.",
    pros: ["Responde sobre conteúdo de desenhos e manuais sem reenviar texto."],
    cons: ["Aumenta latência e uso de GPU/CPU no primeiro processamento."],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
  },
  documentVisionAutoWithDrawing: {
    title: "Auto-detecção de desenho técnico",
    summary: "Dispara extração especializada quando o anexo parece desenho de engenharia.",
    pros: ["Melhor leitura de carimbo, BOM e cotas em PDFs de produto."],
    cons: ["Pode rodar pipeline pesado em PDFs que não são desenho."],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
  },
  documentVisionAutoVlmFallback: {
    title: "Fallback VLM quando OCR falha",
    summary: "Usa modelo multimodal local quando o texto extraído é insuficiente.",
    pros: ["Recupera páginas escaneadas ou com layout complexo."],
    cons: ["Muito mais lento; depende de Ollama/VLM configurado no Docker."],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
    tip: "Requer CHAT_DOCUMENT_VISION_OLLAMA_MODEL no .env — não é editável na admin.",
  },
  attachmentImageOcrEnabled: {
    title: "OCR em imagens anexadas",
    summary: "Tesseract em PNG/JPG antes de indexar o anexo.",
    pros: ["Texto de fotos e prints entra no contexto do chat."],
    cons: ["Qualidade depende da resolução; adiciona tempo no upload."],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
  },
  documentVisionStampCropEnabled: {
    title: "Recorte de carimbo (1ª página)",
    summary: "Isola o bloco de título/carimbo em desenhos para melhorar OCR.",
    pros: ["Código de produto e revisão mais confiáveis."],
    cons: ["Heurística pode falhar em layouts não padrão."],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  documentVisionImageDescribeEnabled: {
    title: "Descrição VLM de figuras",
    summary: "Gera legenda textual de imagens embutidas no PDF via modelo multimodal.",
    pros: ["Contexto para diagramas sem texto selecionável."],
    cons: ["Custo alto; exige modelo VLM no ambiente."],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
  },
};

export const CHAT_VISION_NUMBER_META: Record<
  "documentVisionMaxPages" | "documentVisionMaxChars",
  AdminBundleNumberMeta
> = {
  documentVisionMaxPages: {
    title: "Máximo de páginas por documento",
    summary: "Quantas páginas processar por anexo antes de truncar.",
    pros: ["Evita timeouts em PDFs enormes."],
    cons: ["Páginas além do limite ficam fora do contexto."],
    speedNote: "Menos páginas = resposta mais rápida.",
    qualityNote: "Mais páginas = mais contexto, porém mais lento.",
    min: 1,
    max: 30,
    step: 1,
  },
  documentVisionMaxChars: {
    title: "Máximo de caracteres extraídos",
    summary: "Teto de texto injetado no prompt a partir da visão.",
    pros: ["Protege o limite de tokens do LLM."],
    cons: ["Documentos densos podem ser cortados no meio."],
    speedNote: "Menos caracteres = prompt menor e turno mais rápido.",
    qualityNote: "Mais caracteres = respostas mais completas sobre o anexo.",
    min: 1000,
    max: 50000,
    step: 500,
  },
};
