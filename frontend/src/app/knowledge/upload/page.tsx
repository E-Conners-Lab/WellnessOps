"use client";

import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { UploadForm } from "@/components/knowledge/UploadForm";
import { Card } from "@/components/ui/Card";

export default function UploadPage() {
  const router = useRouter();

  return (
    <AppShell>
      <div className="mx-auto max-w-lg space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Upload Document</h1>
        <Card>
          <UploadForm
            onSuccess={() => {
              // Brief delay to show success message before navigating
              setTimeout(() => router.push("/knowledge"), 1500);
            }}
          />
        </Card>
      </div>
    </AppShell>
  );
}
