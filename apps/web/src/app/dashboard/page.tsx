"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  discoverJobs,
  fetchMe,
  getJobProviders,
  getResume,
  listJobs,
  listMatches,
  listResumes,
  logout,
  parseResume,
  runJobDiscoveryAgent,
  runMatching,
  uploadResume,
  type JobItem,
  type JobProvidersStatus,
  type MatchItem,
  type MePayload,
  type ResumeItem,
} from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [me, setMe] = useState<MePayload | null>(null);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [selected, setSelected] = useState<ResumeItem | null>(null);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [jobsTotal, setJobsTotal] = useState(0);
  const [jobQuery, setJobQuery] = useState("");
  const [jobLocation, setJobLocation] = useState("");
  const [jobCountry, setJobCountry] = useState("");
  const [jobRemoteType, setJobRemoteType] = useState("");
  const [jobSkills, setJobSkills] = useState("");
  const [jobExperience, setJobExperience] = useState("");
  const [jobMinYears, setJobMinYears] = useState("");
  const [includeDemo, setIncludeDemo] = useState(true);
  const [includeRemotive, setIncludeRemotive] = useState(true);
  const [includeNaukri, setIncludeNaukri] = useState(false);
  const [naukriStatus, setNaukriStatus] = useState<JobProvidersStatus["naukri"] | null>(null);
  const [selectedJob, setSelectedJob] = useState<JobItem | null>(null);
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [matchesTotal, setMatchesTotal] = useState(0);
  const [selectedMatch, setSelectedMatch] = useState<MatchItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [matchesError, setMatchesError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [matching, setMatching] = useState(false);
  const [parsingId, setParsingId] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [agentTrace, setAgentTrace] = useState<string | null>(null);
  const [runningAgent, setRunningAgent] = useState(false);

  const loadResumes = useCallback(async () => {
    const { status, body } = await listResumes();
    if (status >= 200 && status < 300 && body.data) {
      setResumes(body.data.items);
      setSelected((current) => {
        if (!current) return current;
        const updated = body.data?.items.find((item) => item.id === current.id);
        return updated ?? current;
      });
    }
  }, []);

  const buildJobFilters = useCallback(() => {
    const skills = jobSkills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const minYears = jobMinYears.trim() ? Number(jobMinYears) : undefined;
    return {
      query: jobQuery || undefined,
      location: jobLocation || undefined,
      country: jobCountry || undefined,
      remote_type: jobRemoteType || undefined,
      skills: skills.length ? skills : undefined,
      experience_level: jobExperience || undefined,
      min_experience_years:
        minYears != null && !Number.isNaN(minYears) ? minYears : undefined,
      include_demo: includeDemo,
      include_remotive: includeRemotive,
      include_naukri: includeNaukri,
      limit: 20,
    };
  }, [
    jobQuery,
    jobLocation,
    jobCountry,
    jobRemoteType,
    jobSkills,
    jobExperience,
    jobMinYears,
    includeDemo,
    includeRemotive,
    includeNaukri,
  ]);

  const loadJobs = useCallback(async () => {
    const filters = buildJobFilters();
    const { status, body } = await listJobs({
      q: filters.query,
      location: filters.location,
      country: filters.country,
      remote_type: filters.remote_type,
      skills: filters.skills?.join(","),
      experience_level: filters.experience_level,
      min_experience_years: filters.min_experience_years,
    });
    if (status >= 200 && status < 300 && body.data) {
      setJobs(body.data.items);
      setJobsTotal(body.data.total);
    }
  }, [buildJobFilters]);

  const loadMatches = useCallback(async () => {
    const { status, body } = await listMatches();
    if (status >= 200 && status < 300 && body.data) {
      setMatches(body.data.items);
      setMatchesTotal(body.data.total);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { status, body } = await fetchMe();
        if (cancelled) return;
        if (status === 401) {
          router.replace("/login");
          return;
        }
        if (status >= 200 && status < 300 && body.data) {
          setMe(body.data);
          const providers = await getJobProviders();
          if (!cancelled && providers.status >= 200 && providers.status < 300 && providers.body.data) {
            setNaukriStatus(providers.body.data.naukri);
            if (providers.body.data.naukri.ready) {
              setIncludeNaukri(true);
              setJobLocation(
                (prev) => prev || providers.body.data!.naukri.default_location || "Bengaluru",
              );
              setJobCountry((prev) => prev || "india");
            }
          }
          await Promise.all([loadResumes(), loadJobs(), loadMatches()]);
        } else {
          setError(body.errors[0]?.message ?? "Failed to load profile.");
        }
      } catch {
        if (!cancelled) setError("Unable to reach the API.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router, loadResumes, loadJobs, loadMatches]);

  useEffect(() => {
    const pending = resumes.some((r) => r.status === "parsing");
    if (!pending) return;
    const timer = window.setInterval(() => {
      void loadResumes();
    }, 2000);
    return () => window.clearInterval(timer);
  }, [resumes, loadResumes]);

  useEffect(() => {
    if (selected || resumes.length === 0) return;
    const withContent = resumes.find((r) => r.content);
    if (withContent) setSelected(withContent);
  }, [resumes, selected]);

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  async function onUpload(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setUploadError("Choose a PDF or Word file first.");
      return;
    }
    setUploadError(null);
    setUploading(true);
    try {
      const { status, body } = await uploadResume(file);
      if (status >= 200 && status < 300) {
        setFile(null);
        await loadResumes();
      } else {
        setUploadError(body.errors[0]?.message ?? "Upload failed.");
      }
    } catch {
      setUploadError("Unable to reach the API.");
    } finally {
      setUploading(false);
    }
  }

  async function onSelect(resume: ResumeItem) {
    setSelected(resume);
    try {
      const { status, body } = await getResume(resume.id);
      if (status >= 200 && status < 300 && body.data) {
        setSelected(body.data);
      }
    } catch {
      // Keep list selection if detail fetch fails.
    }
  }

  async function onParse(resumeId: string) {
    setParsingId(resumeId);
    setUploadError(null);
    try {
      const { status, body } = await parseResume(resumeId);
      if (status >= 200 && status < 300 && body.data) {
        setSelected(body.data);
        await loadResumes();
      } else {
        setUploadError(body.errors[0]?.message ?? "Parse failed.");
      }
    } catch {
      setUploadError("Unable to reach the API.");
    } finally {
      setParsingId(null);
    }
  }

  async function onDiscover(event: FormEvent) {
    event.preventDefault();
    setJobsError(null);
    setDiscovering(true);
    try {
      const { status, body } = await discoverJobs(buildJobFilters());
      if (status >= 200 && status < 300 && body.data) {
        await loadJobs();
        if (body.data.warnings?.length) {
          setJobsError(body.data.warnings.join(" "));
        }
        if (body.data.items[0]) setSelectedJob(body.data.items[0]);
      } else {
        setJobsError(body.errors[0]?.message ?? "Job discovery failed.");
      }
    } catch {
      setJobsError("Unable to reach the API.");
    } finally {
      setDiscovering(false);
    }
  }

  async function onSearchJobs(event: FormEvent) {
    event.preventDefault();
    setJobsError(null);
    await loadJobs();
  }

  async function onRunMatching() {
    setMatchesError(null);
    setMatching(true);
    try {
      const { status, body } = await runMatching({
        resume_id: selected?.id,
        limit: 50,
        min_score: 0,
      });
      if (status >= 200 && status < 300 && body.data) {
        setMatches(body.data.items);
        setMatchesTotal(body.data.matched);
        setSelectedMatch(body.data.items[0] ?? null);
      } else {
        setMatchesError(body.errors[0]?.message ?? "Matching failed.");
      }
    } catch {
      setMatchesError("Unable to reach the API.");
    } finally {
      setMatching(false);
    }
  }

  async function onRunJobDiscoveryAgent() {
    setJobsError(null);
    setAgentTrace(null);
    setRunningAgent(true);
    try {
      const { status, body } = await runJobDiscoveryAgent(buildJobFilters());
      if (status >= 200 && status < 300 && body.data) {
        await loadJobs();
        const warnings = body.data.warnings?.join(" ") || "";
        setAgentTrace(
          `Agent ${body.data.agent} ${body.data.agent_version}: ` +
            `Tools: ${body.data.tool_trace.map((t) => String(t.tool)).join(" → ")}. ${warnings}`,
        );
        if (body.data.items[0]) setSelectedJob(body.data.items[0]);
      } else {
        setJobsError(body.errors[0]?.message ?? "Agent run failed.");
      }
    } catch {
      setJobsError("Unable to reach the API.");
    } finally {
      setRunningAgent(false);
    }
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-semibold text-lg">
            CareerPilot AI
          </Link>
          <button
            type="button"
            onClick={onLogout}
            className="text-sm text-slate-600 hover:text-slate-900"
          >
            Sign out
          </button>
        </div>
      </header>

      <section className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-slate-600">Your account, resumes, jobs, and match scores.</p>
        </div>

        {loading ? <p className="text-sm text-slate-500">Loading…</p> : null}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {me ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4">
            <div>
              <h2 className="text-sm uppercase tracking-wide text-slate-500">User</h2>
              <p className="font-medium">{me.user.display_name || "—"}</p>
              <p className="text-sm text-slate-600">{me.user.email}</p>
            </div>
          </div>
        ) : null}

        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
          <div>
            <h2 className="text-lg font-semibold">Job boards (Cursor MCP)</h2>
            <p className="text-sm text-slate-600">
              Personal LinkedIn and Naukri access runs in Cursor MCP, not this dashboard.
            </p>
          </div>
          <ul className="text-sm text-slate-600 list-disc pl-5 space-y-1">
            <li>
              LinkedIn: enable <code className="text-xs">mcp-server-linkedin</code> (already
              logged in via <code className="text-xs">uvx … --login</code>)
            </li>
            <li>
              Naukri: fill <code className="text-xs">.env.naukri</code>, enable{" "}
              <code className="text-xs">naukri-mcp</code>, then search/apply from Agent chat
            </li>
          </ul>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
          <div>
            <h2 className="text-lg font-semibold">Resumes</h2>
            <p className="text-sm text-slate-600">
              Upload a PDF or Word document (max 10MB). Parsing starts automatically.
            </p>
          </div>

          <form onSubmit={onUpload} className="flex flex-col sm:flex-row gap-3 items-start">
            <input
              type="file"
              accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate-600"
            />
            <button
              type="submit"
              disabled={uploading}
              className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
            >
              {uploading ? "Uploading…" : "Upload"}
            </button>
          </form>
          {uploadError ? <p className="text-sm text-red-600">{uploadError}</p> : null}

          {resumes.length === 0 ? (
            <p className="text-sm text-slate-500">No resumes uploaded yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100 border border-slate-100 rounded-lg">
              {resumes.map((resume) => (
                <li key={resume.id} className="px-4 py-3 flex justify-between gap-4 text-sm">
                  <button
                    type="button"
                    className="text-left"
                    onClick={() => void onSelect(resume)}
                  >
                    <p className="font-medium">{resume.title || "Untitled resume"}</p>
                    <p className="text-slate-500 font-mono text-xs">{resume.id}</p>
                  </button>
                  <div className="text-right text-slate-600 space-y-1">
                    <p className="capitalize">{resume.status.replaceAll("_", " ")}</p>
                    <button
                      type="button"
                      onClick={() => void onParse(resume.id)}
                      disabled={parsingId === resume.id}
                      className="text-xs text-brand-600 hover:underline disabled:opacity-50"
                    >
                      {parsingId === resume.id ? "Parsing…" : "Re-parse"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selected ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
            <h2 className="text-lg font-semibold">Parsed content</h2>
            <p className="text-sm text-slate-600">
              {selected.title} · <span className="capitalize">{selected.status}</span>
            </p>
            {selected.content ? (
              <div className="text-sm space-y-2">
                <p>
                  <span className="text-slate-500">Name:</span>{" "}
                  {selected.content.contact?.name || "—"}
                </p>
                <p>
                  <span className="text-slate-500">Email:</span>{" "}
                  {selected.content.contact?.email || "—"}
                </p>
                <p>
                  <span className="text-slate-500">Headline:</span>{" "}
                  {selected.content.headline || "—"}
                </p>
                <p>
                  <span className="text-slate-500">Skills:</span>{" "}
                  {(selected.content.skills || []).slice(0, 12).join(", ") || "—"}
                </p>
                <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-slate-50 p-3 text-xs">
                  {JSON.stringify(selected.content, null, 2)}
                </pre>
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No parsed content yet. Wait for parsing or click Re-parse.
              </p>
            )}
          </div>
        ) : null}

        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
          <div>
            <h2 className="text-lg font-semibold">Job discovery</h2>
            <p className="text-sm text-slate-600">
              Search saved jobs or discover new ones (demo, Remotive, optional Naukri).
            </p>
          </div>

          <form onSubmit={onDiscover} className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="search"
                value={jobQuery}
                onChange={(e) => setJobQuery(e.target.value)}
                placeholder="Keywords — e.g. data engineer"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <button
                type="button"
                onClick={(e) => void onSearchJobs(e as unknown as FormEvent)}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
              >
                Search
              </button>
              <button
                type="submit"
                disabled={discovering}
                className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
              >
                {discovering ? "Discovering…" : "Discover"}
              </button>
              <button
                type="button"
                onClick={() => void onRunJobDiscoveryAgent()}
                disabled={runningAgent}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
              >
                {runningAgent ? "Agent running…" : "Run agent"}
              </button>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-slate-700">
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeDemo}
                  onChange={(e) => setIncludeDemo(e.target.checked)}
                />
                Demo
              </label>
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeRemotive}
                  onChange={(e) => setIncludeRemotive(e.target.checked)}
                />
                Remotive
              </label>
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeNaukri}
                  onChange={(e) => setIncludeNaukri(e.target.checked)}
                  disabled={naukriStatus != null && !naukriStatus.ready}
                />
                Naukri
                {naukriStatus?.ready ? (
                  <span className="text-xs text-emerald-700">ready</span>
                ) : (
                  <span className="text-xs text-slate-500">
                    {naukriStatus?.hint || "not configured"}
                  </span>
                )}
              </label>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <label className="text-xs text-slate-500 space-y-1">
                <span>Location</span>
                <input
                  type="text"
                  value={jobLocation}
                  onChange={(e) => setJobLocation(e.target.value)}
                  placeholder="e.g. Remote, Bengaluru"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                />
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Country</span>
                <select
                  value={jobCountry}
                  onChange={(e) => setJobCountry(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                >
                  <option value="">Any</option>
                  <option value="us">United States</option>
                  <option value="india">India</option>
                  <option value="uk">United Kingdom</option>
                  <option value="canada">Canada</option>
                  <option value="germany">Germany</option>
                  <option value="worldwide">Worldwide / Anywhere</option>
                </select>
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Remote type</span>
                <select
                  value={jobRemoteType}
                  onChange={(e) => setJobRemoteType(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                >
                  <option value="">Any</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">Onsite</option>
                </select>
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Skills (comma-separated)</span>
                <input
                  type="text"
                  value={jobSkills}
                  onChange={(e) => setJobSkills(e.target.value)}
                  placeholder="e.g. Python, Spark, SQL"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                />
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Experience level</span>
                <select
                  value={jobExperience}
                  onChange={(e) => setJobExperience(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                >
                  <option value="">Any</option>
                  <option value="junior">Junior / entry</option>
                  <option value="mid">Mid</option>
                  <option value="senior">Senior</option>
                </select>
              </label>
              <label className="text-xs text-slate-500 space-y-1">
                <span>Min years (optional)</span>
                <input
                  type="number"
                  min={0}
                  max={40}
                  value={jobMinYears}
                  onChange={(e) => setJobMinYears(e.target.value)}
                  placeholder="e.g. 5"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
                />
              </label>
            </div>
            <p className="text-xs text-slate-500">
              Filters apply to Search (catalog) and Discover / Run agent. For Naukri,
              prefer Location + Min years; leave Experience level on Any (title
              heuristics like “junior” hide most Naukri listings).
            </p>
          </form>
          {jobsError ? <p className="text-sm text-red-600">{jobsError}</p> : null}
          {agentTrace ? <p className="text-xs text-slate-500">{agentTrace}</p> : null}
          <p className="text-xs text-slate-500">{jobsTotal} jobs in catalog</p>

          {jobs.length === 0 ? (
            <p className="text-sm text-slate-500">
              No jobs yet. Click Discover to ingest demo and remote listings.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100 border border-slate-100 rounded-lg">
              {jobs.map((job) => (
                <li key={job.id}>
                  <button
                    type="button"
                    className="w-full text-left px-4 py-3 hover:bg-slate-50"
                    onClick={() => setSelectedJob(job)}
                  >
                    <div className="flex justify-between gap-4 text-sm">
                      <div>
                        <p className="font-medium">{job.title}</p>
                        <p className="text-slate-600">
                          {job.company?.name || "Unknown company"}
                          {job.location ? ` · ${job.location}` : ""}
                        </p>
                      </div>
                      <div className="text-right text-slate-500">
                        <p className="capitalize">{job.remote_type || "—"}</p>
                        <p className="text-xs capitalize">{job.status}</p>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selectedJob ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
            <h2 className="text-lg font-semibold">{selectedJob.title}</h2>
            <p className="text-sm text-slate-600">
              {selectedJob.company?.name || "Unknown company"}
              {selectedJob.location ? ` · ${selectedJob.location}` : ""}
              {selectedJob.remote_type ? ` · ${selectedJob.remote_type}` : ""}
            </p>
            {selectedJob.requirements?.skills?.length ? (
              <p className="text-sm">
                <span className="text-slate-500">Skills:</span>{" "}
                {selectedJob.requirements.skills.slice(0, 12).join(", ")}
              </p>
            ) : null}
            {selectedJob.canonical_url ? (
              <a
                href={selectedJob.canonical_url}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-brand-600 hover:underline"
              >
                Open posting
              </a>
            ) : null}
            {selectedJob.description ? (
              <div
                className="prose prose-sm max-w-none max-h-80 overflow-auto rounded-lg bg-slate-50 p-3 text-sm text-slate-700"
                dangerouslySetInnerHTML={{
                  __html: selectedJob.description.slice(0, 8000),
                }}
              />
            ) : (
              <p className="text-sm text-slate-500">No description available.</p>
            )}
          </div>
        ) : null}

        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Job matches</h2>
              <p className="text-sm text-slate-600">
                Score discovered jobs against your parsed resume (explainable heuristic).
              </p>
            </div>
            <button
              type="button"
              onClick={() => void onRunMatching()}
              disabled={matching}
              className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
            >
              {matching ? "Scoring…" : "Run matching"}
            </button>
          </div>
          {matchesError ? <p className="text-sm text-red-600">{matchesError}</p> : null}
          <p className="text-xs text-slate-500">{matchesTotal} saved matches</p>

          {matches.length === 0 ? (
            <p className="text-sm text-slate-500">
              No matches yet. Parse a resume, discover jobs, then run matching.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100 border border-slate-100 rounded-lg">
              {matches.map((match) => (
                <li key={match.id}>
                  <button
                    type="button"
                    className="w-full text-left px-4 py-3 hover:bg-slate-50"
                    onClick={() => setSelectedMatch(match)}
                  >
                    <div className="flex justify-between gap-4 text-sm">
                      <div>
                        <p className="font-medium">{match.job?.title || "Job"}</p>
                        <p className="text-slate-600">
                          {match.job?.company?.name || "Unknown company"}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-brand-700">
                          {Math.round(match.score * 100)}%
                        </p>
                        <p className="text-xs text-slate-500">{match.model_version}</p>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selectedMatch ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
            <h2 className="text-lg font-semibold">
              Match · {Math.round(selectedMatch.score * 100)}%
            </h2>
            <p className="text-sm text-slate-600">
              {selectedMatch.job?.title}
              {selectedMatch.job?.company?.name
                ? ` · ${selectedMatch.job.company.name}`
                : ""}
            </p>
            {selectedMatch.explanation?.matched_skills?.length ? (
              <p className="text-sm">
                <span className="text-slate-500">Matched:</span>{" "}
                {selectedMatch.explanation.matched_skills.join(", ")}
              </p>
            ) : null}
            {selectedMatch.explanation?.missing_skills?.length ? (
              <p className="text-sm">
                <span className="text-slate-500">Gaps:</span>{" "}
                {selectedMatch.explanation.missing_skills.join(", ")}
              </p>
            ) : null}
            {selectedMatch.explanation?.reasons?.length ? (
              <ul className="text-sm text-slate-700 list-disc pl-5 space-y-1">
                {selectedMatch.explanation.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </section>
    </main>
  );
}
