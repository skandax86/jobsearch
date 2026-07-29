"use client";

import { Suspense } from "react";

import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { LegacyDashboardSection } from "@/components/dashboard/LegacyDashboardApp";

export default function BoardsPage() {
  return (
    <DashboardShell
      breadcrumbs={[{ label: "Workspace" }, { label: "Job boards" }]}
      title="Job boards"
      description="Personal LinkedIn and Naukri access via Cursor MCP."
    >
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <LegacyDashboardSection section="boards" />
      </Suspense>
    </DashboardShell>
  );
}
