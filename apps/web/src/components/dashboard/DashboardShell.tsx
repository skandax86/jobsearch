"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { DASHBOARD_NAV } from "@/lib/dashboard";
import { fetchMe, logout, type MePayload } from "@/lib/api";

export type BreadcrumbItem = { label: string; href?: string };

export function DashboardShell({
  children,
  breadcrumbs,
  title,
  description,
  actions,
}: {
  children: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  title?: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<MePayload | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

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
        }
      } catch {
        if (!cancelled) router.replace("/login");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  function isActive(href: string): boolean {
    if (href === "/dashboard/resumes") {
      return pathname === href || pathname.startsWith("/dashboard/resumes/");
    }
    return pathname === href || pathname.startsWith(`${href}/`);
  }

  const workspace = DASHBOARD_NAV.filter((item) => item.group === "workspace");
  const jobs = DASHBOARD_NAV.filter((item) => item.group === "jobs");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-14 items-center justify-between gap-4 px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-600 md:hidden"
              onClick={() => setMobileNavOpen((v) => !v)}
            >
              Menu
            </button>
            <Link href="/dashboard/resumes" className="font-semibold tracking-tight">
              CareerPilot AI
            </Link>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden sm:inline text-slate-500 truncate max-w-[220px]">
              {me?.user.email || "…"}
            </span>
            <button
              type="button"
              onClick={() => void onLogout()}
              className="rounded-md border border-slate-200 px-3 py-1.5 text-slate-700 hover:bg-slate-50"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex min-h-[calc(100vh-56px)]">
        <aside
          className={
            (mobileNavOpen ? "fixed inset-y-14 left-0 z-40 block w-72" : "hidden") +
            " md:sticky md:top-14 md:block md:h-[calc(100vh-56px)] md:w-64 shrink-0 border-r border-slate-200 bg-white px-3 py-5 overflow-y-auto"
          }
        >
          <nav className="space-y-6">
            <NavGroup
              label="Workspace"
              items={workspace}
              isActive={isActive}
              onNavigate={() => setMobileNavOpen(false)}
            />
            <NavGroup
              label="Jobs"
              items={jobs}
              isActive={isActive}
              onNavigate={() => setMobileNavOpen(false)}
            />
          </nav>
        </aside>

        {mobileNavOpen ? (
          <button
            type="button"
            aria-label="Close navigation"
            className="fixed inset-0 z-30 bg-slate-900/20 md:hidden"
            onClick={() => setMobileNavOpen(false)}
          />
        ) : null}

        <main className="flex-1 min-w-0 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl space-y-5">
            {breadcrumbs && breadcrumbs.length > 0 ? (
              <nav aria-label="Breadcrumb" className="text-sm text-slate-500">
                <ol className="flex flex-wrap items-center gap-1.5">
                  {breadcrumbs.map((crumb, index) => {
                    const last = index === breadcrumbs.length - 1;
                    return (
                      <li key={`${crumb.label}-${index}`} className="flex items-center gap-1.5">
                        {index > 0 ? <span className="text-slate-300">/</span> : null}
                        {crumb.href && !last ? (
                          <Link href={crumb.href} className="hover:text-slate-800">
                            {crumb.label}
                          </Link>
                        ) : (
                          <span className={last ? "text-slate-800 font-medium" : undefined}>
                            {crumb.label}
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ol>
              </nav>
            ) : null}

            {(title || actions) && (
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  {title ? <h1 className="text-2xl font-semibold tracking-tight">{title}</h1> : null}
                  {description ? (
                    <p className="mt-1 text-sm text-slate-600">{description}</p>
                  ) : null}
                </div>
                {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
              </div>
            )}

            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

function NavGroup({
  label,
  items,
  isActive,
  onNavigate,
}: {
  label: string;
  items: typeof DASHBOARD_NAV;
  isActive: (href: string) => boolean;
  onNavigate: () => void;
}) {
  return (
    <div>
      <p className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </p>
      <div className="space-y-1">
        {items.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.id}
              href={item.href}
              onClick={onNavigate}
              className={
                "block rounded-lg px-3 py-2.5 transition " +
                (active
                  ? "bg-brand-50 text-brand-800"
                  : "text-slate-700 hover:bg-slate-50")
              }
            >
              <span className="block text-sm font-medium">{item.label}</span>
              <span className="block text-xs text-slate-500">{item.blurb}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
