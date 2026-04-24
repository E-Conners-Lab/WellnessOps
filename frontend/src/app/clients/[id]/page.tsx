"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api, APIError } from "@/lib/api";
import type { AuditSession, Client } from "@/types";

export default function ClientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params.id as string;

  const [client, setClient] = useState<Client | null>(null);
  const [sessions, setSessions] = useState<AuditSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<Client>(`/clients/${clientId}`),
      api.get<AuditSession[]>(`/clients/${clientId}/sessions`),
    ])
      .then(([clientRes, sessionsRes]) => {
        setClient(clientRes.data);
        setSessions(sessionsRes.data);
      })
      .finally(() => setLoading(false));
  }, [clientId]);

  const startSession = async (tier: string) => {
    setCreating(true);
    try {
      const res = await api.post<AuditSession>("/audits", {
        client_id: clientId,
        audit_tier: tier,
      });
      router.push(`/audit/${res.data.id}`);
    } catch (err) {
      alert(err instanceof APIError ? err.message : "Failed to start session");
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  if (!client) {
    return (
      <AppShell>
        <p className="text-gray-500">Client not found.</p>
      </AppShell>
    );
  }

  const statusColors: Record<string, string> = {
    in_progress: "bg-yellow-100 text-yellow-800",
    observations_complete: "bg-blue-100 text-blue-800",
    diagnosis_pending: "bg-purple-100 text-purple-800",
    report_draft: "bg-orange-100 text-orange-800",
    report_final: "bg-green-100 text-green-800",
    closed: "bg-gray-100 text-gray-800",
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {client.display_name}
            </h1>
            {client.budget_tier && (
              <p className="text-sm text-gray-500 capitalize">
                {client.budget_tier} tier
              </p>
            )}
          </div>
        </div>

        {client.notes && (
          <Card>
            <p className="text-sm text-gray-600">{client.notes}</p>
          </Card>
        )}

        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">
              Start New Audit
            </h2>
          </div>
          <div className="flex gap-3">
            <Button onClick={() => startSession("core")} loading={creating}>
              Core Audit
            </Button>
            <Button
              variant="secondary"
              onClick={() => startSession("extended")}
              loading={creating}
            >
              Extended Audit
            </Button>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Session History
          </h2>
          {sessions.length === 0 ? (
            <p className="text-sm text-gray-500">No sessions yet.</p>
          ) : (
            <div className="space-y-3">
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => router.push(`/audit/${s.id}`)}
                  className="w-full text-left"
                >
                  <Card className="hover:border-brand-300 transition-colors cursor-pointer">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium text-gray-900 capitalize">
                          {s.audit_tier} Audit
                        </span>
                        <p className="text-xs text-gray-500">
                          {new Date(s.started_at).toLocaleDateString()}
                        </p>
                      </div>
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          statusColors[s.status] || "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {s.status.replace(/_/g, " ")}
                      </span>
                    </div>
                  </Card>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
