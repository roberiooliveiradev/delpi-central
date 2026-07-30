import type { ComiteEticaAccess } from "../security/cecAccess";

export type CecAppTab = "atas" | "pending" | "members" | "signature";

type CecAppTabsProps = {
  activeTab: CecAppTab;
  access: ComiteEticaAccess | null;
  onChange: (tab: CecAppTab) => void;
};

export function CecAppTabs({ activeTab, access, onChange }: CecAppTabsProps) {
  const tabs: Array<{ id: CecAppTab; label: string }> = [
    { id: "atas", label: "Atas" },
  ];
  if (access?.can_sign) {
    tabs.push({ id: "pending", label: "Pendências" });
  }
  if (access?.can_manage) {
    tabs.push({ id: "members", label: "Membros" });
  }
  if (access?.can_sign) {
    tabs.push({ id: "signature", label: "Minha assinatura" });
  }

  return (
    <nav className="cec-tabs" aria-label="Seções do Comitê de Ética">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={`cec-tabs__item${activeTab === tab.id ? " cec-tabs__item--active" : ""}`}
          aria-current={activeTab === tab.id ? "page" : undefined}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
