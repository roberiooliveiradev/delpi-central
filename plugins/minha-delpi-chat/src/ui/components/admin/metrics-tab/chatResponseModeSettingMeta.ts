import type { ChatIntelligenceSettingMeta } from "./chatIntelligenceSettingMeta";
import type { AdminBundleSectionMeta } from "./ChatAdminBundleSettingsPanel";

export const CHAT_RESPONSE_MODE_SECTIONS: AdminBundleSectionMeta[] = [
  {
    id: "modes",
    title: "Modos de resposta",
    description:
      "Controla se o usuário pode escolher Texto, Painel ou Automático por sessão.",
  },
];

export const CHAT_RESPONSE_MODE_TOGGLE_META: Record<
  "responseModesEnabled",
  ChatIntelligenceSettingMeta
> = {
  responseModesEnabled: {
    title: "Modos de resposta na sessão",
    summary:
      "Exibe o seletor Rápida / Normal / Pensador no chat. Desligado, todas as mensagens usam o preset Normal.",
    pros: [
      "Usuário controla quando ver tabelas e gráficos versus prosa.",
      "Útil em demos e suporte quando o modo automático erra o formato.",
    ],
    cons: [
      "Mais opções na UI podem confundir quem não conhece os modos.",
      "Modo Texto pode ocultar painéis úteis se escolhido por engano.",
    ],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "neutral",
    tip: "Mantenha ligado em ambientes com usuários avançados; em rollout inicial pode ficar desligado.",
  },
};
