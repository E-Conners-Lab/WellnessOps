"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api, APIError } from "@/lib/api";
import type { KnowledgeDocument } from "@/types";
import { DOMAIN_LABELS } from "@/types";

const DOMAINS = Object.entries(DOMAIN_LABELS);

interface UploadFormProps {
  onSuccess?: (doc: KnowledgeDocument) => void;
}

export function UploadForm({ onSuccess }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [domain, setDomain] = useState("");
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [tags, setTags] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !domain || !title) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("domain", domain);
    formData.append("title", title);
    if (source) formData.append("source", source);
    if (tags) formData.append("tags", tags);

    try {
      const response = await api.upload<KnowledgeDocument>(
        "/knowledge/documents",
        formData
      );
      setSuccess(
        `Ingested "${response.data.title}" -- ${response.data.chunk_count} chunks created`
      );
      setFile(null);
      setTitle("");
      setSource("");
      setTags("");
      onSuccess?.(response.data);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Upload failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-lg bg-green-50 p-3 text-sm text-green-700">
          {success}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Domain
        </label>
        <select
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          required
          className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">Select a domain</option>
          {DOMAINS.map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <Input
        label="Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
        placeholder="Document title"
      />

      <Input
        label="Source (optional)"
        value={source}
        onChange={(e) => setSource(e.target.value)}
        placeholder="URL, book title, or reference"
      />

      <Input
        label="Tags (optional, comma-separated)"
        value={tags}
        onChange={(e) => setTags(e.target.value)}
        placeholder="air quality, WELL standard, VOC"
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          File
        </label>
        <input
          type="file"
          accept=".txt,.md,.pdf,.docx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          required
          className="block w-full text-sm text-gray-500 file:mr-4 file:rounded-lg file:border-0 file:bg-brand-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-brand-700 hover:file:bg-brand-100"
        />
      </div>

      <Button type="submit" loading={loading} disabled={!file || !domain || !title}>
        Upload and Ingest
      </Button>
    </form>
  );
}
