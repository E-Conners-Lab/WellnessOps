"use client";

import { useRef, useState } from "react";
import { Button } from "./Button";
import { api, APIError } from "@/lib/api";

interface PhotoCaptureProps {
  sessionId: string;
  onAnalyzed?: (data: {
    photo_path: string;
    thumbnail_path: string;
    description: string;
  }) => void;
  compact?: boolean;
}

export function PhotoCapture({ sessionId, onAnalyzed, compact }: PhotoCaptureProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [description, setDescription] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCapture = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Show local preview
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result as string);
    reader.readAsDataURL(file);

    setUploading(true);
    setError(null);
    setDescription(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.upload<{
        photo_path: string;
        thumbnail_path: string;
        description: string;
      }>(`/audits/${sessionId}/photos/analyze`, formData);

      setDescription(res.data.description);
      onAnalyzed?.(res.data);
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Photo upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (compact) {
    return (
      <div className="inline-flex items-center gap-2">
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/heic"
          capture="environment"
          onChange={handleCapture}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          {uploading ? (
            <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          )}
          {uploading ? "Analyzing..." : "Photo"}
        </button>
        {preview && (
          <img src={preview} alt="Captured" className="h-10 w-10 rounded object-cover" />
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <input
        ref={fileRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/heic"
        capture="environment"
        onChange={handleCapture}
        className="hidden"
      />

      <Button
        type="button"
        variant="secondary"
        onClick={() => fileRef.current?.click()}
        loading={uploading}
        className="w-full"
        size="lg"
      >
        {uploading ? "Analyzing photo..." : "Take Photo"}
      </Button>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {preview && (
        <div className="relative">
          <img
            src={preview}
            alt="Captured photo"
            className="w-full rounded-lg object-cover max-h-64"
          />
          {uploading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 rounded-lg">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-white border-t-transparent" />
            </div>
          )}
        </div>
      )}

      {description && (
        <div className="rounded-lg bg-blue-50 p-3">
          <p className="text-xs font-semibold text-blue-700 mb-1">AI Vision Analysis:</p>
          <p className="text-sm text-blue-800">{description}</p>
        </div>
      )}
    </div>
  );
}
