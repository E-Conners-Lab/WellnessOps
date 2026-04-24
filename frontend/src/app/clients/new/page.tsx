"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api, APIError } from "@/lib/api";
import type { Client } from "@/types";

const clientSchema = z.object({
  display_name: z.string().min(1, "Display name is required"),
  full_name: z.string().optional(),
  email: z.string().email().optional().or(z.literal("")),
  phone: z.string().optional(),
  notes: z.string().optional(),
  budget_tier: z.string().optional(),
  has_wearable: z.boolean().optional(),
  pii_consent: z.boolean().optional(),
});

type ClientForm = z.infer<typeof clientSchema>;

export default function NewClientPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClientForm>({
    resolver: zodResolver(clientSchema),
    defaultValues: { has_wearable: false, pii_consent: false },
  });

  const onSubmit = async (data: ClientForm) => {
    setError(null);
    setLoading(true);
    try {
      const cleaned = {
        ...data,
        email: data.email || undefined,
        phone: data.phone || undefined,
        notes: data.notes || undefined,
        full_name: data.full_name || undefined,
        budget_tier: data.budget_tier || undefined,
      };
      const response = await api.post<Client>("/clients", cleaned);
      router.push(`/clients/${response.data.id}`);
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to create client");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-lg space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">New Client</h1>
        <Card>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <Input
              label="Display Name"
              error={errors.display_name?.message}
              {...register("display_name")}
            />

            <Input label="Full Name (optional)" {...register("full_name")} />

            <Input
              label="Email (optional)"
              type="email"
              error={errors.email?.message}
              {...register("email")}
            />

            <Input label="Phone (optional)" {...register("phone")} />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Budget Tier
              </label>
              <select
                {...register("budget_tier")}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">Not specified</option>
                <option value="budget">Budget</option>
                <option value="moderate">Moderate</option>
                <option value="premium">Premium</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="has_wearable"
                {...register("has_wearable")}
                className="h-4 w-4 rounded border-gray-300 text-brand-600"
              />
              <label htmlFor="has_wearable" className="text-sm text-gray-700">
                Client has a wearable device
              </label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="pii_consent"
                {...register("pii_consent")}
                className="h-4 w-4 rounded border-gray-300 text-brand-600"
              />
              <label htmlFor="pii_consent" className="text-sm text-gray-700">
                Client consents to PII storage
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes (optional)
              </label>
              <textarea
                {...register("notes")}
                rows={3}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex gap-3">
              <Button type="submit" loading={loading}>
                Create Client
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => router.back()}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </AppShell>
  );
}
