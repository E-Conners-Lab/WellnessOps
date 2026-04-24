"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import type { Client, AuditSession, DomainStats } from "@/types";
import { DOMAIN_LABELS } from "@/types";

interface CalibrationStats {
  total_scores: number;
  total_overrides: number;
  overall_override_rate: number;
  most_biased: Array<{
    category_name: string;
    avg_delta: number;
    bias_direction: string;
  }>;
}

export default function DashboardPage() {
  const [domains, setDomains] = useState<DomainStats[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [calibration, setCalibration] = useState<CalibrationStats | null>(null);

  useEffect(() => {
    api.get<DomainStats[]>("/knowledge/domains").then((r) => setDomains(r.data));
    api.get<Client[]>("/clients").then((r) => setClients(r.data));
    api.get<CalibrationStats>("/calibration").then((r) => setCalibration(r.data)).catch(() => {});
  }, []);

  const totalDocs = domains.reduce((s, d) => s + d.document_count, 0);
  const totalChunks = domains.reduce((s, d) => s + d.total_chunks, 0);

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <Link href="/clients/new">
            <Button size="sm">New Client</Button>
          </Link>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Card>
            <p className="text-sm text-gray-500">Clients</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{clients.length}</p>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">Knowledge Docs</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{totalDocs}</p>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">Knowledge Chunks</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{totalChunks}</p>
          </Card>
          <Card>
            <p className="text-sm text-gray-500">Domains Active</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">
              {domains.filter((d) => d.document_count > 0).length} / 7
            </p>
          </Card>
        </div>

        {/* Recent clients */}
        {clients.length > 0 && (
          <div>
            <h2 className="mb-3 text-lg font-semibold text-gray-900">Recent Clients</h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {clients.slice(0, 6).map((c) => (
                <Link key={c.id} href={`/clients/${c.id}`}>
                  <Card className="hover:border-brand-300 transition-colors cursor-pointer">
                    <h3 className="font-medium text-gray-900">{c.display_name}</h3>
                    <p className="text-xs text-gray-500">
                      {c.budget_tier ? `${c.budget_tier} tier` : "No tier set"} -- {new Date(c.created_at).toLocaleDateString()}
                    </p>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Calibration insights */}
        {calibration && calibration.total_scores > 0 && (
          <div>
            <h2 className="mb-3 text-lg font-semibold text-gray-900">Scoring Calibration</h2>
            <Card>
              <div className="grid grid-cols-3 gap-4 text-center mb-4">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{calibration.total_scores}</p>
                  <p className="text-xs text-gray-500">Total Scores</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{calibration.total_overrides}</p>
                  <p className="text-xs text-gray-500">Practitioner Overrides</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{calibration.overall_override_rate}%</p>
                  <p className="text-xs text-gray-500">Override Rate</p>
                </div>
              </div>
              {calibration.most_biased.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-600 mb-2">Categories with most AI bias:</p>
                  {calibration.most_biased.map((b) => (
                    <div key={b.category_name} className="flex items-center justify-between text-sm py-1">
                      <span className="text-gray-700">{b.category_name}</span>
                      <span className={`font-medium ${b.avg_delta > 0 ? "text-red-600" : b.avg_delta < 0 ? "text-blue-600" : "text-green-600"}`}>
                        {b.avg_delta > 0 ? "+" : ""}{b.avg_delta} (AI scores {b.bias_direction})
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Knowledge domains */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">Knowledge Base</h2>
            <Link href="/knowledge">
              <Button variant="ghost" size="sm">View All</Button>
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {domains.map((d) => (
              <Card
                key={d.domain}
                className={d.document_count > 0 ? "border-brand-200 bg-brand-50/30" : ""}
              >
                <h3 className="font-medium text-gray-900">
                  {DOMAIN_LABELS[d.domain] || d.domain}
                </h3>
                <div className="mt-2 flex gap-4 text-sm text-gray-500">
                  <span>{d.document_count} docs</span>
                  <span>{d.total_chunks} chunks</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
