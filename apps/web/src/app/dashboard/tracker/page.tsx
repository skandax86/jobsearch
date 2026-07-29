"use client";

import { Suspense } from "react";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { LegacyDashboardSection } from "@/components/dashboard/LegacyDashboardApp";

export default function TrackerPage() {
  return (
    <DashboardShell
      breadcrumbs={[{ label: "Jobs" }, { label: "Job tracker" }]}
      title="Job tracker"
      description="Track application pipeline status locally."
    >
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <LegacyDashboardSection section="tracker" />
      </Suspense>
    </DashboardShell>
  );
}
