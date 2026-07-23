const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface HealthData {
  status: string;
  version: string;
  environment: string;
  timestamp: string;
}

interface HealthResponse {
  data: HealthData;
}

async function getHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/health`, {
      next: { revalidate: 0 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const health = await getHealth();

  return (
    <main className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm">
              CP
            </div>
            <span className="font-semibold text-lg">CareerPilot AI</span>
          </div>
          <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">
            Step 1 — Scaffold
          </span>
        </div>
      </header>

      <section className="flex-1 max-w-5xl mx-auto px-6 py-16 w-full">
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          Your AI Career Operating System
        </h1>
        <p className="text-lg text-slate-600 mb-10 max-w-2xl">
          Discover jobs, optimize resumes, track applications, and prepare for
          interviews — with AI that assists, never replaces, your decisions.
        </p>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { title: "Resume Intelligence", status: "Planned" },
            { title: "Job Discovery", status: "Planned" },
            { title: "Application Tracker", status: "Planned" },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <h2 className="font-medium mb-1">{item.title}</h2>
              <span className="text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
                {item.status}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-10 rounded-xl border border-slate-200 bg-white p-5">
          <h3 className="font-medium mb-3 text-sm text-slate-500 uppercase tracking-wide">
            API Health
          </h3>
          {health ? (
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-slate-500">Status</dt>
                <dd className="font-mono text-green-700">{health.data.status}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Version</dt>
                <dd className="font-mono">{health.data.version}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Environment</dt>
                <dd className="font-mono">{health.data.environment}</dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-red-600">
              API unreachable at {API_URL}. Start it with{" "}
              <code className="bg-slate-100 px-1 rounded">make api</code>.
            </p>
          )}
        </div>
      </section>
    </main>
  );
}
