import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { Introduction } from "./pages/Introduction";
import { PendingPage } from "./pages/PendingPage";
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Introduction />} />
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route
            path="/verify"
            element={
              <PendingPage
                title="Cheque verification"
                milestone="F2"
                description="Upload a cheque image and mark its numeric and written amount fields, or provide two separate crops."
              />
            }
          />
          <Route
            path="/recognize"
            element={
              <PendingPage
                title="Amount recognition"
                milestone="F3"
                description="Recognise one numeric or written amount field and inspect the unchanged model output."
              />
            }
          />
          <Route
            path="/benchmarks"
            element={
              <PendingPage
                title="Research benchmarks"
                milestone="F4"
                description="Explore the saved baseline and ATHN evaluation, with genuine handwriting and synthetic data presented separately."
              />
            }
          />
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
