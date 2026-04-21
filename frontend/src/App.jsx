import { useState, useRef, useCallback } from "react";
import axios from "axios";
import { AuthProvider, useAuth } from "./AuthContext";

// ── Helpers ───────────────────────────────────────────────────────────────────
function scoreColor(s) {
  if (s >= 75) return "#22c55e";
  if (s >= 50) return "#f59e0b";
  return "#ef4444";
}
function scoreLabel(s) {
  if (s >= 75) return "Good";
  if (s >= 50) return "Average";
  return "Needs Work";
}
function clamp(v) { return Math.min(Math.max(v, 0), 100); }

// ── Ring ──────────────────────────────────────────────────────────────────────
function Ring({ score, size = 148, stroke = 10 }) {
  const r = (size - stroke * 2) / 2;
  const circ = 2 * Math.PI * r;
  const pct = clamp(Math.round(score));
  const offset = circ - (pct / 100) * circ;
  const color = scoreColor(pct);
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth={stroke} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={stroke}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(.4,0,.2,1)" }} />
      </svg>
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      }}>
        <span style={{ fontSize: 30, fontWeight: 700, color, lineHeight: 1 }}>{pct}</span>
        <span style={{ fontSize: 10, color: "#64748b", marginTop: 4, letterSpacing: 1, textTransform: "uppercase" }}>
          {scoreLabel(pct)}
        </span>
      </div>
    </div>
  );
}

// ── Bar ───────────────────────────────────────────────────────────────────────
function Bar({ label, score, note }) {
  const pct = clamp(Math.round(score));
  const color = scoreColor(pct);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 13, color: "#94a3b8" }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 600, color }}>
          {score}
          {note && <span style={{ fontSize: 11, color: "#64748b", marginLeft: 5, fontWeight: 400 }}>{note}</span>}
        </span>
      </div>
      <div style={{ height: 5, background: "#1e293b", borderRadius: 99 }}>
        <div style={{
          height: "100%", borderRadius: 99, background: color, width: `${pct}%`,
          transition: "width 1s cubic-bezier(.4,0,.2,1)",
        }} />
      </div>
    </div>
  );
}

// ── Tag ───────────────────────────────────────────────────────────────────────
const tagStyles = {
  strength:   { bg: "#052e16", border: "#166534", text: "#86efac" },
  weakness:   { bg: "#2d0a0a", border: "#991b1b", text: "#fca5a5" },
  suggestion: { bg: "#0c1a3a", border: "#1d4ed8", text: "#93c5fd" },
};
function Tag({ text, type }) {
  const s = tagStyles[type] || tagStyles.suggestion;
  return (
    <div style={{
      background: s.bg, border: `1px solid ${s.border}`,
      borderRadius: 8, padding: "8px 12px",
      fontSize: 13, color: s.text, lineHeight: 1.5, marginBottom: 6,
    }}>
      {text}
    </div>
  );
}

// ── Card ──────────────────────────────────────────────────────────────────────
function Card({ children, style }) {
  return (
    <div style={{
      background: "#0f172a", border: "1px solid #1e293b",
      borderRadius: 14, padding: 22, ...style,
    }}>
      {children}
    </div>
  );
}

// ── Section heading ───────────────────────────────────────────────────────────
function Heading({ icon, title }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
      <span style={{ fontSize: 15 }}>{icon}</span>
      <span style={{ fontSize: 11, fontWeight: 700, color: "#475569", letterSpacing: 1.2, textTransform: "uppercase" }}>
        {title}
      </span>
    </div>
  );
}

// ── Upload zone ───────────────────────────────────────────────────────────────
function UploadZone({ file, onFile, loading }) {
  const ref = useRef();
  const [drag, setDrag] = useState(false);
  const drop = useCallback((e) => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f?.type === "application/pdf") onFile(f);
  }, [onFile]);
  return (
    <div
      onClick={() => !loading && ref.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={drop}
      style={{
        border: `2px dashed ${drag ? "#3b82f6" : file ? "#22c55e55" : "#1e293b"}`,
        borderRadius: 12, padding: "40px 20px", textAlign: "center",
        cursor: loading ? "not-allowed" : "pointer",
        background: drag ? "#1e3a5f20" : "transparent",
        transition: "all 0.2s",
      }}
    >
      <input ref={ref} type="file" accept=".pdf" style={{ display: "none" }}
        onChange={(e) => e.target.files[0] && onFile(e.target.files[0])} />
      <div style={{ fontSize: 36, marginBottom: 12 }}>{file ? "📄" : "⬆️"}</div>
      {file ? (
        <>
          <div style={{ color: "#22c55e", fontWeight: 600, fontSize: 14 }}>{file.name}</div>
          <div style={{ color: "#475569", fontSize: 12, marginTop: 4 }}>{(file.size / 1024).toFixed(1)} KB · PDF</div>
        </>
      ) : (
        <>
          <div style={{ color: "#e2e8f0", fontWeight: 600, fontSize: 14 }}>Drop your resume here</div>
          <div style={{ color: "#475569", fontSize: 13, marginTop: 4 }}>PDF only · click or drag &amp; drop</div>
        </>
      )}
    </div>
  );
}

// ── Spinner ───────────────────────────────────────────────────────────────────
function Spinner() {
  return (
    <div style={{ textAlign: "center", padding: "32px 0" }}>
      <div style={{
        width: 40, height: 40, borderRadius: "50%", margin: "0 auto 14px",
        border: "3px solid #1e293b", borderTop: "3px solid #3b82f6",
        animation: "spin 0.8s linear infinite",
      }} />
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <span style={{ color: "#475569", fontSize: 13 }}>Analyzing resume…</span>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
function Empty({ label }) {
  return <p style={{ fontSize: 13, color: "#334155", fontStyle: "italic" }}>{label}</p>;
}

// ── Auth Page ─────────────────────────────────────────────────────────────────
function AuthPage() {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async () => {
    setError("");
    if (!form.email || !form.password) return setError("Please fill in all fields.");
    if (mode === "signup" && !form.name) return setError("Name is required.");
    setLoading(true);
    await new Promise((r) => setTimeout(r, 350));
    const result = mode === "login"
      ? login(form.email, form.password)
      : signup(form.name, form.email, form.password);
    setLoading(false);
    if (!result.success) setError(result.error);
  };

  const toggle = () => {
    setMode(mode === "login" ? "signup" : "login");
    setError("");
    setForm({ name: "", email: "", password: "" });
  };

  const inp = {
    width: "100%", padding: "11px 14px", borderRadius: 8,
    border: "1px solid #1e293b", background: "#0a0f1e",
    color: "#e2e8f0", fontFamily: "inherit", fontSize: 14, outline: "none",
    boxSizing: "border-box",
  };
  const lbl = { fontSize: 11, fontWeight: 600, color: "#475569", letterSpacing: "0.08em", textTransform: "uppercase", display: "block", marginBottom: 6 };

  return (
    <div style={{
      minHeight: "100vh", background: "#020617",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "'Inter', sans-serif", color: "#e2e8f0", padding: 20,
    }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'); *{box-sizing:border-box;margin:0;padding:0}`}</style>

      <div style={{ width: "100%", maxWidth: 400 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 12, background: "#1d4ed8",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 20, fontWeight: 700, color: "#fff", margin: "0 auto 14px",
          }}>R</div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>
            Resume<span style={{ color: "#3b82f6" }}>IQ</span>
          </h1>
          <p style={{ fontSize: 13, color: "#475569", marginTop: 6 }}>
            {mode === "login" ? "Sign in to analyze your resume" : "Create your free account"}
          </p>
        </div>

        {/* Card */}
        <Card>
          <h2 style={{ fontSize: 17, fontWeight: 600, marginBottom: 22 }}>
            {mode === "login" ? "Welcome back" : "Get started"}
          </h2>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {mode === "signup" && (
              <div>
                <label style={lbl}>Full Name</label>
                <input name="name" type="text" placeholder="John Doe" value={form.name} onChange={handle} style={inp} />
              </div>
            )}
            <div>
              <label style={lbl}>Email</label>
              <input name="email" type="email" placeholder="you@example.com" value={form.email} onChange={handle} style={inp} />
            </div>
            <div>
              <label style={lbl}>Password</label>
              <input name="password" type="password" placeholder="••••••••" value={form.password} onChange={handle} style={inp}
                onKeyDown={(e) => e.key === "Enter" && submit()} />
            </div>
          </div>

          {error && (
            <div style={{
              marginTop: 14, background: "#2d0a0a", border: "1px solid #7f1d1d",
              color: "#fca5a5", borderRadius: 8, padding: "10px 14px", fontSize: 13,
            }}>
              ⚠️ {error}
            </div>
          )}

          <button
            onClick={submit}
            disabled={loading}
            style={{
              marginTop: 20, width: "100%", padding: 13,
              borderRadius: 10, border: "none",
              fontFamily: "inherit", fontWeight: 600, fontSize: 14,
              cursor: loading ? "not-allowed" : "pointer",
              background: loading ? "#1e293b" : "#2563eb",
              color: loading ? "#475569" : "#fff",
              transition: "background 0.2s",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            }}
          >
            {loading && (
              <div style={{
                width: 16, height: 16, borderRadius: "50%",
                border: "2px solid #475569", borderTop: "2px solid #94a3b8",
                animation: "spin 0.7s linear infinite",
              }} />
            )}
            {loading ? "Please wait…" : mode === "login" ? "Sign In" : "Create Account"}
          </button>

          <p style={{ textAlign: "center", fontSize: 13, color: "#475569", marginTop: 18 }}>
            {mode === "login" ? "Don't have an account? " : "Already have an account? "}
            <span
              onClick={toggle}
              style={{ color: "#3b82f6", cursor: "pointer", fontWeight: 600 }}
            >
              {mode === "login" ? "Sign up" : "Sign in"}
            </span>
          </p>
        </Card>
      </div>
    </div>
  );
}

// ── Resume Analyzer ───────────────────────────────────────────────────────────
function ResumeAnalyzer() {
  const { user, logout } = useAuth();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function analyze() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await axios.post("http://127.0.0.1:8000/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.response?.data?.message;
      setError(
        detail ||
        (err.code === "ERR_NETWORK"
          ? "Cannot reach backend at http://127.0.0.1:8000 — make sure the server is running."
          : "Something went wrong. Please try again.")
      );
    } finally {
      setLoading(false);
    }
  }

  const ai = result?.ai_analysis || {};
  const strengths   = Array.isArray(ai.strengths)   ? ai.strengths   : [];
  const weaknesses  = Array.isArray(ai.weaknesses)  ? ai.weaknesses  : [];
  const suggestions = Array.isArray(ai.suggestions) ? ai.suggestions : [];

  return (
    <div style={{
      minHeight: "100vh", background: "#020617",
      color: "#e2e8f0", fontFamily: "'Inter', sans-serif",
      paddingBottom: 64,
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        *{box-sizing:border-box;margin:0;padding:0}
        ::-webkit-scrollbar{width:5px}
        ::-webkit-scrollbar-track{background:#0f172a}
        ::-webkit-scrollbar-thumb{background:#1e293b;border-radius:99px}
      `}</style>

      {/* Topbar */}
      <header style={{
        background: "#0a0f1e", borderBottom: "1px solid #1e293b",
        padding: "14px 28px", display: "flex", alignItems: "center",
        justifyContent: "space-between", position: "sticky", top: 0, zIndex: 50,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8,
            background: "#1d4ed8", display: "flex", alignItems: "center",
            justifyContent: "center", fontSize: 14, fontWeight: 700, color: "#fff",
          }}>R</div>
          <span style={{ fontWeight: 700, fontSize: 15 }}>
            Resume<span style={{ color: "#3b82f6" }}>IQ</span>
          </span>
        </div>

        {/* User info + logout */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 13, color: "#475569" }}>
            👤 <span style={{ color: "#94a3b8" }}>{user.name}</span>
          </span>
          <button
            onClick={logout}
            style={{
              padding: "6px 14px", borderRadius: 7,
              border: "1px solid #1e293b", background: "transparent",
              color: "#64748b", fontSize: 12, fontFamily: "inherit",
              cursor: "pointer", transition: "all 0.2s",
            }}
            onMouseOver={(e) => { e.target.style.borderColor = "#ef4444"; e.target.style.color = "#ef4444"; }}
            onMouseOut={(e) => { e.target.style.borderColor = "#1e293b"; e.target.style.color = "#64748b"; }}
          >
            Logout
          </button>
        </div>
      </header>

      <main style={{ maxWidth: 1000, margin: "0 auto", padding: "36px 20px 0" }}>

        {/* Hero */}
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, color: "#f1f5f9", marginBottom: 10 }}>
            AI Resume Analyzer
          </h1>
          <p style={{ color: "#475569", fontSize: 14, maxWidth: 460, margin: "0 auto" }}>
            Upload your PDF resume and instantly get ATS score, grammar analysis, and AI-powered improvement suggestions.
          </p>
        </div>

        {/* Upload */}
        <Card style={{ marginBottom: 24 }}>
          <UploadZone file={file} onFile={setFile} loading={loading} />
          <button
            onClick={analyze}
            disabled={!file || loading}
            style={{
              marginTop: 16, width: "100%", padding: "13px",
              borderRadius: 10, border: "none",
              fontFamily: "inherit", fontWeight: 600, fontSize: 14,
              cursor: file && !loading ? "pointer" : "not-allowed",
              background: file && !loading ? "#2563eb" : "#1e293b",
              color: file && !loading ? "#fff" : "#475569",
              transition: "background 0.2s",
            }}
          >
            {loading ? "Analyzing…" : "Analyze Resume →"}
          </button>

          {error && (
            <div style={{
              marginTop: 12, background: "#2d0a0a", border: "1px solid #7f1d1d",
              color: "#fca5a5", borderRadius: 10, padding: "10px 14px", fontSize: 13,
            }}>
              ⚠️ {error}
            </div>
          )}
        </Card>

        {/* Loading */}
        {loading && <Card><Spinner /></Card>}

        {/* Results */}
        {result && !loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>

            <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: 18 }}>
              <Card style={{
                display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center", gap: 10,
              }}>
                <Heading icon="🎯" title="ATS Score" />
                <Ring score={result.ats_score} />
                <p style={{ fontSize: 12, color: "#475569", textAlign: "center", lineHeight: 1.5, maxWidth: 130 }}>
                  Based on resume content, formatting &amp; keywords
                </p>
              </Card>

              <Card>
                <Heading icon="📊" title="Score Breakdown" />
                <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                  <Bar label="Structure Score" score={result.structure_score} />
                  <Bar
                    label="Grammar Score"
                    score={result.grammar_score}
                    note={
                      result.grammar_errors != null
                        ? `${result.grammar_errors} error${result.grammar_errors !== 1 ? "s" : ""} found`
                        : null
                    }
                  />
                  <Bar label="Readability Score" score={result.readability_score} />
                </div>
              </Card>
            </div>

            {result.grammar_errors > 0 && (
              <div style={{
                display: "flex", alignItems: "center", gap: 14,
                background: "#2d0a0a", border: "1px solid #991b1b",
                borderRadius: 12, padding: "14px 20px",
              }}>
                <span style={{ fontSize: 24 }}>⚠️</span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: "#fca5a5" }}>
                    {result.grammar_errors} grammar {result.grammar_errors === 1 ? "error" : "errors"} detected
                  </div>
                  <div style={{ fontSize: 12, color: "#64748b", marginTop: 3 }}>
                    Review your spelling, punctuation, and sentence structure to improve your grammar score.
                  </div>
                </div>
              </div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 18 }}>
              <Card>
                <Heading icon="💪" title="Strengths" />
                {strengths.length === 0
                  ? <Empty label="No strengths detected." />
                  : strengths.map((s, i) => <Tag key={i} text={s} type="strength" />)}
              </Card>
              <Card>
                <Heading icon="⚠️" title="Weaknesses" />
                {weaknesses.length === 0
                  ? <Empty label="No major weaknesses found." />
                  : weaknesses.map((s, i) => <Tag key={i} text={s} type="weakness" />)}
              </Card>
              <Card>
                <Heading icon="💡" title="Suggestions" />
                {suggestions.length === 0
                  ? <Empty label="No suggestions at this time." />
                  : suggestions.map((s, i) => <Tag key={i} text={s} type="suggestion" />)}
              </Card>
            </div>

            {result.text_preview && (
              <Card>
                <Heading icon="📝" title="Extracted Text Preview" />
                <div style={{
                  fontFamily: "monospace", fontSize: 12, color: "#64748b",
                  whiteSpace: "pre-wrap", lineHeight: 1.7,
                  maxHeight: 150, overflowY: "auto",
                  background: "#020617", borderRadius: 8,
                  padding: "12px 14px", border: "1px solid #1e293b",
                }}>
                  {result.text_preview}
                </div>
              </Card>
            )}

            <p style={{ textAlign: "center", fontSize: 11, color: "#1e293b" }}>
              Results are based on automated analysis · accuracy may vary across ATS platforms
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────
function AppInner() {
  const { user } = useAuth();
  return user ? <ResumeAnalyzer /> : <AuthPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}