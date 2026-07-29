"use client";

import { Suspense } from "react";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { LegacyDashboardSection } from "@/components/dashboard/LegacyDashboardApp";

export default function MatchesPage() {
  return (
    <DashboardShell
      breadcrumbs={[{ label: "Jobs" }, { label: "Job matches" }]}
      title="Job matches"
      description="Score resume fit and review skill gaps."
    >
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <LegacyDashboardSection section="matches" />
      </Suspense>
    </DashboardShell>
  );
}
