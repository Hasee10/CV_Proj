import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import {
  Activity,
  Scan,
  TextSearch,
  ChartNoAxesCombined,
  Menu,
  X,
  BookOpen,
} from "lucide-react";
import { Brand } from "../ui/Brand";
import { useModelStatus } from "../../hooks/useModelStatus";
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
  const location = useLocation();
  const toggle = useRef<HTMLButtonElement>(null);
  const heading = useRef<HTMLDivElement>(null);
  const first = useRef(true);
  const status = useModelStatus();
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
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">
        <Link to="/" aria-label="ChequeVerify introduction">
          <Brand />
        </Link>
        <div className="sidebar-section">RESEARCH WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to}>
              <Icon size={19} aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <BookOpen size={19} aria-hidden="true" />
          <div>
            Built for human review<span>Computer Vision · Fall 2026</span>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="workspace-bar">
          <span>
            ChequeVerify <span className="slash">/</span>{" "}
            <strong>{title}</strong>
          </span>
          <span className="academic-label">Academic prototype</span>
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
            <Outlet context={status} />
          </div>
        </main>
        <footer className="workspace-footer">
          <span>Recognition. Comparison. Human review.</span>
          <span>LoGo-HTR / ATHN</span>
        </footer>
      </div>
    </div>
  );
}
