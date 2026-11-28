import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import {
  Activity,
  Scan,
  TextSearch,
  ChartNoAxesCombined,
  Menu,
  X,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { Brand } from "../ui/Brand";
import { WorkspaceAssistant } from "../ui/WorkspaceAssistant";
import { useModelStatus } from "../../hooks/useModelStatus";
import { useSavedCapture } from "../../hooks/useSavedCapture";
export const navigation = [
  { to: "/dashboard", label: "Dashboard", icon: Activity },
  { to: "/verify", label: "Cheque verification", icon: Scan },
  { to: "/recognize", label: "Amount recognition", icon: TextSearch },
  {
    to: "/benchmarks",
    label: "Research benchmarks",
    icon: ChartNoAxesCombined,
  },
];
export function AppLayout() {
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem("chequeverify.sidebar") === "collapsed";
    } catch {
      return false;
    }
  });
  const location = useLocation();
  const toggle = useRef<HTMLButtonElement>(null);
  const heading = useRef<HTMLDivElement>(null);
  const first = useRef(true);
  const status = useModelStatus();
  const capture = useSavedCapture();
  useEffect(() => {
    setOpen(false);
    if (!first.current) heading.current?.focus({ preventScroll: true });
    first.current = false;
    window.scrollTo(0, 0);
  }, [location.pathname]);
  const title =
    navigation.find((n) => n.to === location.pathname)?.label ??
    "Page not found";
  useEffect(() => {
    document.title = `${title} | ChequeVerify`;
  }, [title]);
  return (
    <div className={`app-shell${collapsed ? " sidebar-collapsed" : ""}`}>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">
        <div className="sidebar-identity">
          <Link to="/" aria-label="ChequeVerify introduction">
            <Brand />
          </Link>
          <button
            className="sidebar-collapse"
            onClick={() => {
              setCollapsed(!collapsed);
              try {
                localStorage.setItem(
                  "chequeverify.sidebar",
                  !collapsed ? "collapsed" : "expanded",
                );
              } catch {
                /* The current toggle still works. */
              }
            }}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
            aria-controls="desktop-navigation"
          >
            {collapsed ? (
              <PanelLeftOpen size={18} />
            ) : (
              <PanelLeftClose size={18} />
            )}
          </button>
        </div>
        <div className="sidebar-section">YOUR WORKSPACE</div>
        <nav id="desktop-navigation" aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              aria-label={label}
              title={collapsed ? label : undefined}
            >
              <Icon size={19} aria-hidden="true" />
              <span className="nav-label">{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <WorkspaceAssistant />
        </div>
      </aside>
      <div className="workspace">
        <header className="workspace-bar">
          <span>
            Workspace <span className="slash">/</span> <strong>{title}</strong>
          </span>
          <span className="header-system" data-state={status.readiness}>
            <span aria-hidden="true" />
            {status.readiness === "ready"
              ? "Model connected"
              : status.readiness === "loading"
                ? "Checking connection"
                : status.readiness === "unavailable"
                  ? "Model unavailable"
                  : status.readiness === "offline"
                    ? "Backend offline"
                    : "Connection error"}
          </span>
          <button
            ref={toggle}
            className="mobile-toggle"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close navigation" : "Open navigation"}
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </button>
        </header>
        <nav
          id="mobile-nav"
          className="mobile-nav"
          aria-label="Mobile navigation"
          hidden={!open}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setOpen(false);
              toggle.current?.focus();
            }
          }}
        >
          {navigation.map((n) => (
            <NavLink key={n.to} to={n.to}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <main id="main-content" className="workspace-content">
          <div tabIndex={-1} ref={heading} className="route-focus">
            <Outlet context={{ ...status, capture }} />
          </div>
        </main>
        <footer className="workspace-footer">
          <span>Recognition. Comparison. Human review.</span>
          <span>LoGo-HTR / ATHN</span>
        </footer>
      </div>
      <div className="mobile-guide">
        <WorkspaceAssistant />
      </div>
    </div>
  );
}
