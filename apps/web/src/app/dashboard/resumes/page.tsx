"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import {
  deleteResume,
  listResumes,
  parseResume,
  uploadResume,
  type ResumeItem,
} from "@/lib/api";
import { formatDateTime, resumeOriginLabel } from "@/lib/dashboard";

export default function ResumesPage() {
  const router = useRouter();
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [parsingId, setParsingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [pendingParseId, setPendingParseId] = useState<string | null>(null);
  const [originFilter, setOriginFilter] = useState<"all" | "uploaded" | "generated">("all");
  const [sort, setSort] = useState<"created_at" | "updated_at">("created_at");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const loadResumes = useCallback(async () => {
    const { status, body } = await listResumes({
      origin: originFilter,
      sort,
      order,
    });
    if (status === 401) {
      router.replace("/login");
      return;
    }
    if (status >= 200 && status < 300 && body.data) {
      setResumes(body.data.items);
      setError(null);
    } else {
      setError(body.errors[0]?.message ?? "Failed to load resumes.");
    }
  }, [originFilter, sort, order, router]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      await loadResumes();
      if (!cancelled) setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [loadResumes]);

  useEffect(() => {
    const pending = resumes.some((r) => r.status === "parsing");
    if (!pending) return;
    const timer = window.setInterval(() => {
      void loadResumes();
    }, 2000);
    return () => window.clearInterval(timer);
  }, [resumes, loadResumes]);

  useEffect(() => {
    if (!pendingParseId) return;
    const item = resumes.find((r) => r.id === pendingParseId);
    if (!item) return;
    if (item.status === "extracted" || item.status === "needs_review") {
      setPendingParseId(null);
      if (item.parser?.includes("fallback") || item.ai_parse_error) {
        setNotice(
          "Saved with heuristic fallback (AI unavailable/timed out). Review fields, then try Re-parse when LM Studio is ready.",
        );
        setError(item.ai_parse_error ? `AI: ${item.ai_parse_error}` : null);
      } else if (item.status === "needs_review") {
        setNotice("Extraction saved with limited fields — review and fill what’s missing.");
      } else {
        setNotice(
          item.parser?.startsWith("ai_")
            ? "AI extraction saved. Opening editor…"
            : "Extraction saved. Opening editor…",
        );
      }
      router.push(`/dashboard/resumes/${item.id}/edit`);
    } else if (item.status === "parse_failed") {
      setPendingParseId(null);
      setError("Could not extract text from that file. Try Re-parse.");
    } else if (item.status === "parsing") {
      setNotice("Still extracting… local AI can take 1–3 minutes. Keep LM Studio running with the model loaded.");
    }
  }, [resumes, pendingParseId, router]);

  async function onUpload(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a PDF or Word file first.");
      return;
    }
    setError(null);
    setNotice(null);
    setUploading(true);
    try {
      const { status, body } = await uploadResume(file);
      if (status >= 200 && status < 300 && body.data) {
        setFile(null);
        setPendingParseId(body.data.id);
        setNotice("Uploaded — extracting into the standard resume schema…");
        await loadResumes();
      } else {
        setError(body.errors[0]?.message ?? "Upload failed.");
      }
    } catch {
      setError("Unable to reach the API.");
    } finally {
      setUploading(false);
    }
  }

  async function onParse(resumeId: string) {
    setParsingId(resumeId);
    setError(null);
    try {
      const { status, body } = await parseResume(resumeId);
      if (status >= 200 && status < 300) {
        setNotice("Re-parse complete.");
        await loadResumes();
      } else {
        setError(body.errors[0]?.message ?? "Parse failed.");
      }
    } catch {
      setError("Unable to reach the API.");
    } finally {
      setParsingId(null);
    }
  }

  async function onDelete(resume: ResumeItem) {
    const name = resume.title || "this resume";
    if (!window.confirm(`Delete “${name}”? This cannot be undone.`)) return;
    setDeletingId(resume.id);
    setError(null);
    try {
      const { status, body } = await deleteResume(resume.id);
      if (status >= 200 && status < 300) {
        setNotice(`Deleted “${name}”.`);
        await loadResumes();
      } else {
        setError(body.errors[0]?.message ?? "Could not delete resume.");
      }
    } catch {
      setError("Unable to reach the API.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <DashboardShell
      breadcrumbs={[{ label: "Workspace" }, { label: "Resumes" }]}
      title="Resumes"
      description="Upload a PDF/Word file or open a generated resume. View and edit open as dedicated pages."
    >
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <form onSubmit={onUpload} className="flex flex-col sm:flex-row gap-3 items-start flex-1">
            <input
              type="file"
              accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate-600"
            />
            <button
              type="submit"
              disabled={uploading}
              className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60 shrink-0"
            >
              {uploading ? "Uploading…" : "Upload"}
            </button>
          </form>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <select
              value={originFilter}
              onChange={(e) => setOriginFilter(e.target.value as typeof originFilter)}
              className="rounded-lg border border-slate-200 px-2 py-1.5 bg-white"
            >
              <option value="all">All types</option>
              <option value="uploaded">Uploaded</option>
              <option value="generated">Generated</option>
            </select>
            <select
              value={`${sort}:${order}`}
              onChange={(e) => {
                const [nextSort, nextOrder] = e.target.value.split(":") as [
                  typeof sort,
                  typeof order,
                ];
                setSort(nextSort);
                setOrder(nextOrder);
              }}
              className="rounded-lg border border-slate-200 px-2 py-1.5 bg-white"
            >
              <option value="created_at:desc">Created · newest</option>
              <option value="created_at:asc">Created · oldest</option>
              <option value="updated_at:desc">Updated · newest</option>
              <option value="updated_at:asc">Updated · oldest</option>
            </select>
          </div>
        </div>

        {loading ? <p className="text-sm text-slate-500">Loading resumes…</p> : null}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        {notice ? <p className="text-sm text-emerald-700">{notice}</p> : null}

        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Resume name</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Created at</th>
                <th className="px-4 py-3 font-medium">Updated at</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {resumes.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                    No resumes match these filters.
                  </td>
                </tr>
              ) : (
                resumes.map((resume) => (
                  <tr key={resume.id} className="bg-white hover:bg-slate-50/80">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">
                        {resume.title || "Untitled resume"}
                      </p>
                      {resume.source_mime_type ? (
                        <p className="text-xs text-slate-500 mt-0.5">
                          {resume.source_mime_type.includes("pdf")
                            ? "PDF"
                            : resume.source_mime_type.includes("word")
                              ? "Word"
                              : resume.source_mime_type}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 capitalize text-slate-700">
                      {resumeOriginLabel(resume)}
                    </td>
                    <td className="px-4 py-3 capitalize text-slate-700">
                      <div>{resume.status.replaceAll("_", " ")}</div>
                      {resume.parser ? (
                        <div className="text-xs text-slate-400 mt-0.5 normal-case">
                          {resume.parser}
                          {resume.ai_parse_error ? " · AI fallback" : ""}
                        </div>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                      {formatDateTime(resume.created_at)}
                    </td>
                    <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                      {formatDateTime(resume.updated_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap justify-end gap-3">
                        <Link
                          href={`/dashboard/resumes/${resume.id}`}
                          className="text-brand-700 hover:underline"
                        >
                          View
                        </Link>
                        <Link
                          href={`/dashboard/resumes/${resume.id}/edit`}
                          className="text-brand-700 hover:underline"
                        >
                          Edit
                        </Link>
                        <button
                          type="button"
                          onClick={() => void onDelete(resume)}
                          disabled={deletingId === resume.id}
                          className="text-red-600 hover:underline disabled:opacity-50"
                        >
                          {deletingId === resume.id ? "Deleting…" : "Delete"}
                        </button>
                        {resume.source_object_key ? (
                          <button
                            type="button"
                            onClick={() => void onParse(resume.id)}
                            disabled={parsingId === resume.id}
                            className="text-slate-500 hover:underline disabled:opacity-50"
                          >
                            {parsingId === resume.id ? "Parsing…" : "Re-parse"}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </DashboardShell>
  );
}
