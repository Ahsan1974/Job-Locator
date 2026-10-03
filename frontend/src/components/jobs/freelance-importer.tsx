"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link2, Plus } from "lucide-react";
import { useState } from "react";

import { api } from "@/lib/api";
import type { Job } from "@/types";

export function FreelanceImporter() {
  const qc = useQueryClient();
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const importer = useMutation({
    mutationFn: () =>
      api<Job>("/jobs/import-freelance", {
        method: "POST",
        body: JSON.stringify({ url, title: title || null }),
      }),
    onSuccess: () => {
      setUrl("");
      setTitle("");
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  return (
    <div className="glass-panel mb-6 p-4">
      <div className="flex items-start gap-3">
        <Link2 className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
        <div className="min-w-0 flex-1">
          <h2 className="font-semibold">Import a freelance project</h2>
          <p className="mt-0.5 text-xs text-ink-muted">
            Paste an Upwork, Fiverr, Freelancer, or PeoplePerHour link. Add a title if the board blocks preview access.
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-[1fr_16rem_auto]">
            <input
              className="input-field"
              type="url"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://www.upwork.com/jobs/…"
            />
            <input
              className="input-field"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Project title (optional)"
            />
            <button
              type="button"
              className="btn-primary justify-center"
              disabled={!url.trim() || importer.isPending}
              onClick={() => importer.mutate()}
            >
              <Plus className="h-4 w-4" />
              {importer.isPending ? "Importing…" : "Import"}
            </button>
          </div>
          {importer.isSuccess && <p className="mt-2 text-xs text-success">Project imported and deduplicated.</p>}
          {importer.isError && <p className="mt-2 text-xs text-danger">{(importer.error as Error).message}</p>}
        </div>
      </div>
    </div>
  );
}
