import { CircleHelp, FilePenLine, FolderTree, LayoutDashboard } from "lucide-react";
import { PERCORSI } from "./percorsi";

// Flat list for the sidebar; `labelKey` is an i18n key.
export const NAVIGAZIONE = [
  { id: "panoramica", labelKey: "nav.overview", to: PERCORSI.panoramica, icon: LayoutDashboard },
  { id: "aree", labelKey: "nav.areas", to: PERCORSI.aree, icon: FolderTree },
  { id: "editor", labelKey: "nav.editor", to: PERCORSI.editor, icon: FilePenLine },
  { id: "guida", labelKey: "nav.guide", to: PERCORSI.guida, icon: CircleHelp },
];
