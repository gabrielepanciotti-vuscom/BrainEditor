import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { CircleHelp, LayoutDashboard } from "lucide-react";
import { PageHeader, Spinner, ToastProvider } from "@suite/design-system";
import AppLayout from "./app/AppLayout";
import { AuthProvider } from "./auth/AuthProvider";
import { useAuth } from "./auth/authContext";
import LoginPagina from "./auth/LoginPagina";
import { PERCORSI, relativo } from "./app/percorsi";
import PaginaAree from "./aree/PaginaAree";
import EditorNota from "./editor/EditorNota";
import Lingue from "./i18n/Lingue";
import { useT } from "./i18n/useT";

const FUTURE = { v7_startTransition: true, v7_relativeSplatPath: true };

function Panoramica() {
  const t = useT();
  return <PageHeader icon={<LayoutDashboard size={20} />} title={t("overview.title")} />;
}

function Guida() {
  const t = useT();
  return <PageHeader icon={<CircleHelp size={20} />} title={t("guide.title")} />;
}

function Portale() {
  const { user, caricando } = useAuth();

  // The session is resolved first: without this wait the login would
  // flash for users who are already signed in.
  if (caricando) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size={32} />
      </div>
    );
  }
  if (!user) return <LoginPagina />;

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Panoramica />} />
        <Route path={relativo(PERCORSI.aree)} element={<PaginaAree />} />
        <Route path={relativo(PERCORSI.editor)} element={<EditorNota />} />
        <Route path={relativo(PERCORSI.guida)} element={<Guida />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <Lingue>
      <BrowserRouter future={FUTURE}>
        <ToastProvider>
          <AuthProvider>
            <Portale />
          </AuthProvider>
        </ToastProvider>
      </BrowserRouter>
    </Lingue>
  );
}
