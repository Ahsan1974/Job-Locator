"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Resume } from "@/types";
import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Star,
  Trash2,
  CheckCircle,
  CloudUpload,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { formatRelativeDate } from "@/lib/utils";

export default function ResumePage() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: resumes, isLoading } = useQuery<Resume[]>({
    queryKey: ["resumes"],
    queryFn: () => api<Resume[]>("/resumes"),
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api<Resume>("/resumes/upload", { method: "POST", body: formData });
    },
    onSuccess: () => {
      setUploadError(null);
      qc.invalidateQueries({ queryKey: ["resumes"] });
    },
    onError: (e: Error) => setUploadError(e.message),
  });

  const setPrimary = useMutation({
    mutationFn: (id: string) =>
      api(`/resumes/${id}/set-primary`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });

  const deleteResume = useMutation({
    mutationFn: (id: string) => api(`/resumes/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files?.length) return;
      const file = files[0];
      const allowed = ["application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
      if (!allowed.includes(file.type)) {
        setUploadError("Please upload a PDF or DOCX file.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setUploadError("File must be under 10 MB.");
        return;
      }
      upload.mutate(file);
    },
    [upload],
  );

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Resume</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Upload and manage your resumes. Set one as primary for AI-powered matching.
        </p>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
        className={`glass-panel p-10 flex flex-col items-center gap-4 cursor-pointer transition border-2 ${
          dragging ? "border-accent bg-accent/5" : "border-dashed border-line/60 hover:border-accent/50 hover:bg-accent/5"
        }`}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.doc,.docx"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className={`flex h-14 w-14 items-center justify-center rounded-2xl transition ${
          dragging ? "bg-accent/20 text-accent" : "bg-line/40 text-ink-muted"
        }`}>
          {upload.isPending ? (
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          ) : (
            <CloudUpload className="h-6 w-6" />
          )}
        </div>
        <div className="text-center">
          <p className="font-semibold text-sm">
            {upload.isPending ? "Uploading…" : "Drop your resume here or click to browse"}
          </p>
          <p className="mt-1 text-xs text-ink-faint">PDF or DOCX · max 10 MB</p>
        </div>
        {uploadError && (
          <div className="flex items-center gap-2 rounded-xl bg-danger/10 px-4 py-2 text-xs text-danger">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {uploadError}
          </div>
        )}
      </div>

      {/* Resume list */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => <div key={i} className="skeleton h-24 w-full" />)}
        </div>
      ) : !resumes?.length ? (
        <div className="glass-panel p-12 text-center">
          <FileText className="mx-auto mb-3 h-10 w-10 text-ink-faint" />
          <p className="text-sm font-medium">No resumes yet</p>
          <p className="mt-1 text-xs text-ink-faint">Upload a PDF or DOCX to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {resumes.map((resume, i) => (
            <motion.div
              key={resume.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-panel overflow-hidden"
            >
              <div className="flex items-start gap-4 p-5">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-medium text-sm truncate">{resume.filename}</p>
                    {resume.is_primary && (
                      <span className="inline-flex items-center gap-1 rounded-md bg-accent/15 px-2 py-0.5 text-[11px] font-semibold text-accent">
                        <Star className="h-3 w-3" /> Primary
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-xs text-ink-faint">
                    Uploaded {formatRelativeDate(resume.created_at)}
                  </p>
                  {resume.parsed_skills && resume.parsed_skills.length > 0 && (
                    <p className="mt-1 text-xs text-ink-muted">
                      {resume.parsed_skills.length} skills parsed
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {!resume.is_primary && (
                    <button
                      type="button"
                      onClick={() => setPrimary.mutate(resume.id)}
                      disabled={setPrimary.isPending}
                      className="btn-ghost !px-2.5 !py-1.5 text-xs"
                      title="Set as primary"
                    >
                      <Star className="h-3.5 w-3.5" /> Set primary
                    </button>
                  )}
                  {resume.parsed_skills && resume.parsed_skills.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setExpandedId(expandedId === resume.id ? null : resume.id)}
                      className="btn-ghost !px-2.5 !py-1.5 text-xs"
                    >
                      Skills {expandedId === resume.id ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      if (confirm("Delete this resume?")) deleteResume.mutate(resume.id);
                    }}
                    disabled={deleteResume.isPending}
                    className="btn-ghost !px-2.5 !py-1.5 text-xs text-danger hover:bg-danger/10"
                    title="Delete"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {/* Expanded skills */}
              {expandedId === resume.id && resume.parsed_skills && (
                <div className="border-t border-line/60 px-5 py-4">
                  <p className="mb-2 text-xs font-semibold text-ink-faint uppercase tracking-wide">
                    Parsed Skills
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {resume.parsed_skills.map((skill) => (
                      <span
                        key={skill}
                        className="rounded-lg bg-accent/10 px-2.5 py-1 text-xs font-medium text-accent"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                  {resume.parsed_experience && (
                    <div className="mt-3">
                      <p className="text-xs font-semibold text-ink-faint uppercase tracking-wide mb-1">Experience</p>
                      <p className="text-xs text-ink-muted whitespace-pre-wrap">{resume.parsed_experience}</p>
                    </div>
                  )}
                  {resume.parsed_education && (
                    <div className="mt-3">
                      <p className="text-xs font-semibold text-ink-faint uppercase tracking-wide mb-1">Education</p>
                      <p className="text-xs text-ink-muted whitespace-pre-wrap">{resume.parsed_education}</p>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}

      {resumes && resumes.length > 0 && (
        <div className="glass-panel p-4 flex items-start gap-3">
          <CheckCircle className="h-4 w-4 shrink-0 text-success mt-0.5" />
          <p className="text-xs text-ink-muted">
            Your primary resume is used for match scoring, cover letter generation, and skill gap analysis.
            Navigate to a job page and use the <strong>Match</strong>, <strong>Cover Letter</strong>, or{" "}
            <strong>Skill Gap</strong> buttons to see AI-powered insights.
          </p>
        </div>
      )}
    </div>
  );
}
