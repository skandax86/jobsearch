"use client";

import { Suspense } from "react";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { LegacyDashboardSection } from "@/components/dashboard/LegacyDashboardApp";

export default function DiscoveryPage() {
  return (
    <DashboardShell
      breadcrumbs={[{ label: "Jobs" }, { label: "Job discovery" }]}
      title="Job discovery"
      description="Search and ingest roles from configured providers."
    >
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <LegacyDashboardSection section="discovery" />
      </Suspense>
    </DashboardShell>
  );
}
