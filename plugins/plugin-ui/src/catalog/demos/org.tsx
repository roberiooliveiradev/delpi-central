import { OrgMembershipFlow, orgMembershipFlowBemClasses } from "../../components/org";
import type { CatalogEntryDraft } from "../types";

const demoClassNames = orgMembershipFlowBemClasses("delpi-ui");

export const orgCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "org.OrgMembershipFlow",
    family: "org",
    exportName: "OrgMembershipFlow",
    title: "OrgMembershipFlow",
    description:
      "Organograma interativo read-only (carteira/grupo ↔ pessoa) com pan/zoom — sem editor BPMN.",
    demos: [
      {
        id: "portfolio-roots",
        label: "Por carteira",
        render: () => (
          <div className="dashboard-plugin-ui-catalog" style={{ minHeight: 440 }}>
            <OrgMembershipFlow
              classNames={demoClassNames}
              aria-label="Demo organização por carteira"
              nodes={[
                {
                  id: "p-sul",
                  kind: "portfolio",
                  entityId: "p-sul",
                  title: "Sul",
                  subtitle: "18 cli · 3 membros",
                },
                {
                  id: "u-ana",
                  kind: "person",
                  entityId: "u-ana",
                  title: "Ana Silva",
                },
                {
                  id: "u-pedro",
                  kind: "person",
                  entityId: "u-pedro",
                  title: "Pedro Costa",
                },
              ]}
              edges={[
                { id: "e1", source: "p-sul", target: "u-ana" },
                { id: "e2", source: "p-sul", target: "u-pedro" },
              ]}
            />
          </div>
        ),
      },
      {
        id: "group-roots",
        label: "Por grupo",
        render: () => (
          <div className="dashboard-plugin-ui-catalog" style={{ minHeight: 440 }}>
            <OrgMembershipFlow
              classNames={demoClassNames}
              aria-label="Demo organização por grupo"
              nodes={[
                {
                  id: "g-inside",
                  kind: "group",
                  entityId: "g-inside",
                  title: "Inside Sales",
                  subtitle: "4 membros",
                },
                {
                  id: "u-ana",
                  kind: "person",
                  entityId: "u-ana",
                  title: "Ana Silva",
                },
                {
                  id: "u-bia",
                  kind: "person",
                  entityId: "u-bia",
                  title: "Bia Souza",
                },
              ]}
              edges={[
                { id: "e1", source: "g-inside", target: "u-ana" },
                { id: "e2", source: "g-inside", target: "u-bia" },
              ]}
            />
          </div>
        ),
      },
    ],
  },
];
