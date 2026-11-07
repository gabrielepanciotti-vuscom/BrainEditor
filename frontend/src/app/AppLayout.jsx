import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { AppShell, Button } from "@suite/design-system";
import { LanguageSwitcher } from "@suite/i18n";
import { useAuth } from "../auth/authContext";
import { useT } from "../i18n/useT";
import { BRANDING } from "./branding";
import { NAVIGAZIONE } from "./navigazione";

function Marchio({ nome }) {
  const logo = BRANDING?.logo;
  const nomeMostrato = BRANDING?.name || nome;
  if (!logo?.light && !logo?.dark) {
    return <span className="truncate text-sm font-semibold text-text">{nomeMostrato}</span>;
  }
  return (
    <>
      <img src={logo.light || logo.dark} alt={nomeMostrato} className="h-6 dark:hidden" />
      <img src={logo.dark || logo.light} alt={nomeMostrato} className="hidden h-6 dark:block" />
    </>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const t = useT();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const attivo = (to) => (to === "/" ? pathname === "/" : pathname.startsWith(to));

  return (
    <AppShell>
      <AppShell.Sidebar>
        {NAVIGAZIONE.map(({ id, labelKey, to, icon: Icon }) => (
          <AppShell.Sidebar.Item
            key={id}
            icon={<Icon size={18} />}
            label={t(labelKey)}
            active={attivo(to)}
            onClick={() => navigate(to)}
          />
        ))}
      </AppShell.Sidebar>
      <div className="flex min-w-0 flex-1 flex-col">
        <AppShell.Topbar>
          <Marchio nome={t("app.name")} />
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            {user?.nome && <span className="hidden text-sm text-muted sm:inline">{user.nome}</span>}
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut size={14} aria-hidden />
              {t("auth.logout")}
            </Button>
          </div>
        </AppShell.Topbar>
        <AppShell.Content>
          <Outlet />
        </AppShell.Content>
      </div>
    </AppShell>
  );
}
