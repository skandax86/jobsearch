"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { ProfileStructuredSections } from "@/components/ProfileStructuredSections";
import {
  getResume,
  updateResume,
  type ResumeContentJson,
  type ResumeItem,
} from "@/lib/api";
import { emptyResumeContent } from "@/lib/dashboard";

export default function ResumeEditPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const resumeId = params.id;
  const [resume, setResume] = useState<ResumeItem | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState<ResumeContentJson>(emptyResumeContent());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
          setTitle(body.data.title || "");
          setContent({ ...emptyResumeContent(), ...(body.data.content || {}) });
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

  async function onSave(event: FormEvent) {
    event.preventDefault();
    const cleaned = title.trim();
    if (!cleaned) {
      setError("Resume name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const { status, body } = await updateResume(resumeId, {
        title: cleaned,
        content,
      });
      if (status >= 200 && status < 300 && body.data) {
        router.push(`/dashboard/resumes/${body.data.id}`);
      } else {
        setError(body.errors[0]?.message ?? "Could not save resume.");
      }
    } catch {
      setError("Unable to reach the API.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <DashboardShell
      breadcrumbs={[
        { label: "Workspace", href: "/dashboard/resumes" },
        { label: "Resumes", href: "/dashboard/resumes" },
        {
          label: resume?.title || "Resume",
          href: resume ? `/dashboard/resumes/${resume.id}` : undefined,
        },
        { label: "Edit" },
      ]}
      title="Edit resume"
      description="Update the name and structured fields. Same schema as profile and tailored saves."
      actions={
        <>
          <Link
            href={resume ? `/dashboard/resumes/${resume.id}` : "/dashboard/resumes"}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-white"
          >
            Cancel
          </Link>
        </>
      }
    >
      {loading ? <p className="text-sm text-slate-500">Loading…</p> : null}
      {!loading && resume ? (
        <form
          onSubmit={(e) => void onSave(e)}
          className="rounded-xl border border-slate-200 bg-white p-5 space-y-5"
        >
          <label className="block text-sm">
            <span className="text-slate-600">Resume name</span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
          <div className="grid sm:grid-cols-2 gap-3">
            {(
              [
                ["name", "Full name"],
                ["email", "Email"],
                ["phone", "Phone"],
                ["location", "Location"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="block text-sm">
                <span className="text-slate-600">{label}</span>
                <input
                  value={content.contact?.[key] ?? ""}
                  onChange={(e) =>
                    setContent((prev) => ({
                      ...prev,
                      contact: { ...prev.contact, [key]: e.target.value || null },
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                />
              </label>
            ))}
          </div>
          <label className="block text-sm">
            <span className="text-slate-600">Headline</span>
            <input
              value={content.headline ?? ""}
              onChange={(e) =>
                setContent((prev) => ({ ...prev, headline: e.target.value || null }))
              }
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-600">Summary</span>
            <textarea
              rows={3}
              value={content.summary ?? ""}
              onChange={(e) =>
                setContent((prev) => ({ ...prev, summary: e.target.value || null }))
              }
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-600">Skills (comma-separated)</span>
            <textarea
              rows={2}
              value={(content.skills || []).join(", ")}
              onChange={(e) =>
                setContent((prev) => ({
                  ...prev,
                  skills: e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                }))
              }
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
          <ProfileStructuredSections content={content} onChange={setContent} />
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
            <Link
              href={`/dashboard/resumes/${resume.id}`}
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm hover:bg-slate-50"
            >
              Cancel
            </Link>
          </div>
        </form>
      ) : null}
      {!loading && !resume && error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : null}
    </DashboardShell>
  );
}
