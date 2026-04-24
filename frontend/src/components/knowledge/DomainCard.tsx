import { Card } from "@/components/ui/Card";
import type { DomainStats } from "@/types";
import { DOMAIN_LABELS } from "@/types";

interface DomainCardProps {
  stats: DomainStats;
}

export function DomainCard({ stats }: DomainCardProps) {
  const hasContent = stats.document_count > 0;

  return (
    <Card
      className={hasContent ? "border-brand-200 bg-brand-50/30" : ""}
    >
      <h3 className="font-semibold text-gray-900">
        {DOMAIN_LABELS[stats.domain] || stats.domain}
      </h3>
      <p className="mt-1 text-xs text-gray-500">{stats.collection_name}</p>
      <div className="mt-3 flex gap-6 text-sm">
        <div>
          <span className="font-bold text-gray-900">
            {stats.document_count}
          </span>
          <span className="ml-1 text-gray-500">documents</span>
        </div>
        <div>
          <span className="font-bold text-gray-900">
            {stats.total_chunks}
          </span>
          <span className="ml-1 text-gray-500">chunks</span>
        </div>
      </div>
    </Card>
  );
}
