"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { DomainCard } from "@/components/knowledge/DomainCard";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import type { DomainStats } from "@/types";

export default function KnowledgePage() {
  const [domains, setDomains] = useState<DomainStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<DomainStats[]>("/knowledge/domains")
      .then((res) => setDomains(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
          <Link href="/knowledge/upload">
            <Button>Upload Document</Button>
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {domains.map((d) => (
              <DomainCard key={d.domain} stats={d} />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
