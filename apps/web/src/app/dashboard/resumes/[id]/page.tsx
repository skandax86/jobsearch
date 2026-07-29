"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { ResumeContentView } from "@/components/ResumeContentView";
import { getResume, type ResumeItem } from "@/lib/api";
import { resumeOriginLabel } from "@/lib/dashboard";

export default function ResumeViewPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const resumeId = params.id;
  const [resume, setResume] = useState<ResumeItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"preview" | "json">("preview");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const { status, body } = await getResume(resumeId);
        if (cancelled) return;
        if (status === 401) {
          router.replace("/login");
          return;
        }
        if (status >= 200 && status < 300 && body.data) {
          setResume(body.data);
          setError(null);
        } else {
          setError(body.errors[0]?.message ?? "Resume not found.");
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
  }, [resumeId, router]);

  const jsonText = useMemo(
    () => (resume?.content ? JSON.stringify(resume.content, null, 2) : ""),
    [resume],
  );

  async function onCopyJson() {
    if (!jsonText) return;
    try {
      await navigator.clipboard.writeText(jsonText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setError("Could not copy to clipboard.");
    }
  }

  return (
    <DashboardShell
      breadcrumbs={[
        { label: "Workspace", href: "/dashboard/resumes" },
        { label: "Resumes", href: "/dashboard/resumes" },
        { label: resume?.title || "View" },
      ]}
      title={resume?.title || "View resume"}
      description={
        resume
          ? `${resumeOriginLabel(resume)} · ${resume.status.replaceAll("_", " ")}`
          : "Loading resume details…"
      }
      actions={
        resume ? (
          <>
            <Link
              href={`/dashboard/resumes/${resume.id}/edit`}
              className="rounded-lg bg-brand-600 text-white px-3 py-2 text-sm font-medium hover:bg-brand-700"
            >
              Edit
            </Link>
            <Link
              href="/dashboard/resumes"
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-white"
            >
              Back to list
            </Link>
          </>
        ) : null
      }
    >
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
            <button
              type="button"
              onClick={() => setViewMode("preview")}
              className={
                "rounded-md px-3 py-1.5 text-xs font-medium transition " +
                (viewMode === "preview"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-800")
              }
            >
              Preview
            </button>
            <button
              type="button"
              onClick={() => setViewMode("json")}
              className={
                "rounded-md px-3 py-1.5 text-xs font-medium transition " +
                (viewMode === "json"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-800")
              }
            >
              JSON
            </button>
          </div>
          {viewMode === "json" && resume?.content ? (
            <button
              type="button"
              onClick={() => void onCopyJson()}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
              title="Copy JSON"
            >
              <CopyIcon />
              {copied ? "Copied" : "Copy JSON"}
            </button>
          ) : null}
        </div>

        {loading ? <p className="text-sm text-slate-500">Loading…</p> : null}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {!loading && resume?.content ? (
          viewMode === "preview" ? (
            <ResumeContentView content={resume.content} />
          ) : (
            <pre className="max-h-[40rem] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs text-slate-800">
              {jsonText}
            </pre>
          )
        ) : null}

        {!loading && resume && !resume.content ? (
          <p className="text-sm text-slate-500">
            No parsed content yet. Go back to the list and click Re-parse.
          </p>
        ) : null}
      </div>
    </DashboardShell>
  );
}

function CopyIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}
