import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { Introduction } from "./pages/Introduction";
import { CapturedResults } from "./pages/CapturedResults";
import { Benchmark } from "./pages/Benchmark";
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Introduction />} />
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route
            path="/verify"
            element={<CapturedResults key="verification" kind="verification" />}
          />
          <Route
            path="/recognize"
            element={<CapturedResults key="recognition" kind="recognition" />}
          />
          <Route path="/benchmarks" element={<Benchmark />} />
          <Route
            path="*"
            element={
              <>
                <h1>Page not found</h1>
                <Link className="button primary" to="/dashboard">
                  Return to dashboard
                </Link>
              </>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
