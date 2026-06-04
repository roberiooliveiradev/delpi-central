import type { LucideIcon } from "lucide-react";

import {
  ADMIN_SECTIONS,
  type AdminNavState,
  type AdminSection,
  type AdminSubTab,
} from "./adminNavigation";
import { getNestedPages, getNestedPageLabel } from "./adminNavPages";
import { getContentSearchTextForTarget } from "./adminNavSearchIndex";

export type AdminNavNode = {
  id: string;
  label: string;
  searchText: string;
  target: AdminNavState;
  children?: AdminNavNode[];
};

export type AdminNavTreeSection = {
  key: AdminSection;
  label: string;
  description: string;
  icon: LucideIcon;
  nodes: AdminNavNode[];
};

function normalizeSearch(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "");
}

function buildSearchText(target: AdminNavState, ...parts: string[]): string {
  const content = getContentSearchTextForTarget(target);
  return [parts.join(" "), content].filter(Boolean).join(" ").toLowerCase();
}

function buildSubTabNode(
  sectionKey: AdminSection,
  sectionLabel: string,
  sectionDescription: string,
  subTab: { key: AdminSubTab; label: string },
): AdminNavNode {
  const nested = getNestedPages(subTab.key);
  const baseTarget: AdminNavState = { section: sectionKey, subTab: subTab.key };

  if (nested.length === 0) {
    return {
      id: `${sectionKey}/${subTab.key}`,
      label: subTab.label,
      searchText: buildSearchText(
        baseTarget,
        sectionLabel,
        subTab.label,
        sectionDescription,
      ),
      target: baseTarget,
    };
  }

  const branchTarget: AdminNavState = { ...baseTarget, page: nested[0]?.key };

  return {
    id: `${sectionKey}/${subTab.key}`,
    label: subTab.label,
    searchText: buildSearchText(
      branchTarget,
      sectionLabel,
      subTab.label,
      sectionDescription,
      ...nested.map((page) => page.label),
    ),
    target: branchTarget,
    children: nested.map((page) => {
      const pageTarget: AdminNavState = {
        section: sectionKey,
        subTab: subTab.key,
        page: page.key,
      };

      return {
        id: `${sectionKey}/${subTab.key}/${page.key}`,
        label: page.label,
        searchText: buildSearchText(
          pageTarget,
          sectionLabel,
          subTab.label,
          page.label,
          sectionDescription,
        ),
        target: pageTarget,
      };
    }),
  };
}

export function buildAdminNavTree(): AdminNavTreeSection[] {
  return ADMIN_SECTIONS.map((section) => {
    const nodes: AdminNavNode[] =
      section.subTabs.length > 0
        ? section.subTabs.map((sub) =>
            buildSubTabNode(section.key, section.label, section.description, sub),
          )
        : [
            {
              id: `${section.key}/root`,
              label: section.label,
              searchText: buildSearchText(
                { section: section.key },
                section.label,
                section.description,
              ),
              target: { section: section.key },
            },
          ];

    return {
      key: section.key,
      label: section.label,
      description: section.description,
      icon: section.icon,
      nodes,
    };
  });
}

function nodeMatchesQuery(node: AdminNavNode, normalized: string): boolean {
  return normalizeSearch(node.searchText).includes(normalized);
}

function filterNodes(nodes: AdminNavNode[], normalized: string): AdminNavNode[] {
  const result: AdminNavNode[] = [];

  for (const node of nodes) {
    const childMatches = node.children ? filterNodes(node.children, normalized) : [];
    const selfMatch = nodeMatchesQuery(node, normalized);

    if (selfMatch) {
      result.push({ ...node, children: node.children });
      continue;
    }

    if (childMatches.length > 0) {
      result.push({ ...node, children: childMatches });
    }
  }

  return result;
}

export function filterAdminNavTree(
  tree: AdminNavTreeSection[],
  query: string,
): AdminNavTreeSection[] {
  const normalized = normalizeSearch(query);

  if (!normalized) {
    return tree;
  }

  return tree
    .map((section) => {
      const sectionContent = section.nodes
        .map((node) => node.searchText)
        .join(" ");
      const sectionMatch = normalizeSearch(
        `${section.label} ${section.description} ${sectionContent}`,
      ).includes(normalized);

      const filteredNodes = filterNodes(section.nodes, normalized);

      if (sectionMatch) {
        return { ...section, nodes: section.nodes };
      }

      if (filteredNodes.length === 0) {
        return null;
      }

      return { ...section, nodes: filteredNodes };
    })
    .filter((section): section is AdminNavTreeSection => section !== null);
}

export function isAdminNavTargetActive(nav: AdminNavState, target: AdminNavState): boolean {
  if (nav.section !== target.section) {
    return false;
  }

  if (target.section === "overview") {
    return true;
  }

  if (nav.subTab !== target.subTab) {
    return false;
  }

  if (target.page) {
    return nav.page === target.page;
  }

  if (nav.page) {
    return false;
  }

  return true;
}

function collectActiveNodeIds(
  nodes: AdminNavNode[],
  nav: AdminNavState,
  activeIds: string[],
): boolean {
  for (const node of nodes) {
    const childActive =
      node.children && node.children.length > 0
        ? collectActiveNodeIds(node.children, nav, activeIds)
        : false;
    const selfActive = isAdminNavTargetActive(nav, node.target);

    if (selfActive || childActive) {
      activeIds.push(node.id);
      return true;
    }
  }

  return false;
}

export function getExpandedNodeIdsForNav(
  nav: AdminNavState,
  filteredTree: AdminNavTreeSection[],
  searchQuery: string,
): Set<string> {
  const expanded = new Set<string>();
  const activeIds: string[] = [];

  for (const section of filteredTree) {
    collectActiveNodeIds(section.nodes, nav, activeIds);
  }

  for (const id of activeIds) {
    expanded.add(id);
  }

  const section = filteredTree.find((item) => item.key === nav.section);

  if (section) {
    expanded.add(section.key);
  }

  if (normalizeSearch(searchQuery)) {
    for (const section of filteredTree) {
      for (const node of section.nodes) {
        if (node.children && node.children.length > 0) {
          expanded.add(node.id);
        }
      }
    }
  }

  return expanded;
}

export function getAdminNavBreadcrumb(nav: AdminNavState): string {
  const section = ADMIN_SECTIONS.find((item) => item.key === nav.section);

  if (!section) {
    return "Administração";
  }

  if (section.subTabs.length === 0 || !nav.subTab) {
    return section.label;
  }

  const sub = section.subTabs.find((item) => item.key === nav.subTab);

  if (!sub) {
    return section.label;
  }

  if (nav.page) {
    const pageLabel = getNestedPageLabel(nav.subTab, nav.page);

    return pageLabel
      ? `${section.label} · ${sub.label} · ${pageLabel}`
      : `${section.label} · ${sub.label}`;
  }

  return `${section.label} · ${sub.label}`;
}

/** @deprecated Use isAdminNavTargetActive */
export function isAdminNavLeafActive(
  nav: AdminNavState,
  leaf: { section: AdminSection; subTab?: AdminSubTab; page?: string },
): boolean {
  return isAdminNavTargetActive(nav, {
    section: leaf.section,
    subTab: leaf.subTab,
    page: leaf.page,
  });
}

/** @deprecated Use getExpandedNodeIdsForNav */
export function getExpandedSectionsForNav(
  nav: AdminNavState,
  filteredTree: AdminNavTreeSection[],
  searchQuery: string,
): Set<AdminSection> {
  const ids = getExpandedNodeIdsForNav(nav, filteredTree, searchQuery);
  const sections = new Set<AdminSection>([nav.section]);

  for (const section of filteredTree) {
    if (ids.has(section.key) || section.nodes.some((node) => ids.has(node.id))) {
      sections.add(section.key);
    }
  }

  return sections;
}
