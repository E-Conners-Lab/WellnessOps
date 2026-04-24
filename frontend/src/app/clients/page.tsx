"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import type { Client } from "@/types";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Client[]>("/clients")
      .then((res) => setClients(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
          <Link href="/clients/new">
            <Button>New Client</Button>
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
          </div>
        ) : clients.length === 0 ? (
          <Card className="text-center py-12">
            <p className="text-gray-500">No clients yet.</p>
            <Link href="/clients/new" className="mt-3 inline-block">
              <Button size="sm">Add your first client</Button>
            </Link>
          </Card>
        ) : (
          <div className="space-y-3">
            {clients.map((c) => (
              <Link key={c.id} href={`/clients/${c.id}`}>
                <Card className="hover:border-brand-300 transition-colors cursor-pointer">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {c.display_name}
                      </h3>
                      {c.budget_tier && (
                        <span className="text-xs text-gray-500 capitalize">
                          {c.budget_tier}
                        </span>
                      )}
                    </div>
                    <span className="text-sm text-gray-400">
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
