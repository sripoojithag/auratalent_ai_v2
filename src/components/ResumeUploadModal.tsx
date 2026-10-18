import React, { useState, useRef } from "react";
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, Sparkles, User, Database } from "lucide-react";

interface UploadedCandidateResult {
  candidateId: string;
  resumeId: string;
  fullName: string;
  headline: string;
  totalExperienceYears: number;
  extractedSkillsCount: number;
  chunksCount: number;
  totalPages: number;
  status: "completed" | "failed";
  error?: string;
}

interface ResumeUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export const ResumeUploadModal: React.FC<ResumeUploadModalProps> = ({ isOpen, onClose, onUploadSuccess }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadedCandidateResult[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files).filter(f => f.name.toLowerCase().endsWith(".pdf"));
      setSelectedFiles(files);
      setUploadResults([]);
      setUploadError(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      const files = Array.from(e.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith(".pdf"));
      setSelectedFiles(files);
      setUploadResults([]);
      setUploadError(null);
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setIsUploading(true);
    setUploadError(null);

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append("resumes", file);
    });

    try {
      const response = await fetch("/api/resumes/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.errors?.[0]?.error || "Upload failed");
      }

      setUploadResults(data.results || []);
      onUploadSuccess();
    } catch (err: any) {
      console.error("Resume ingestion error:", err);
      setUploadError(err.message || "Failed to process PDF resumes");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">Real PDF Resume Ingestion</h2>
              <p className="text-xs text-slate-500">Extracts text, section chunks, and candidate profiles into PostgreSQL</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content Area */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Dropzone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 hover:border-blue-500 bg-slate-50 hover:bg-blue-50/40 rounded-xl p-8 text-center cursor-pointer transition-all duration-150 flex flex-col items-center justify-center"
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="application/pdf"
              className="hidden"
              onChange={handleFileChange}
            />
            <div className="w-14 h-14 rounded-2xl bg-white shadow-sm border border-slate-200 flex items-center justify-center text-blue-600 mb-3">
              <FileText className="w-7 h-7" />
            </div>
            <p className="text-sm font-semibold text-slate-700 mb-1">
              Click to browse or drop PDF resume files here
            </p>
            <p className="text-xs text-slate-400">
              Supports real multi-page candidate resumes (max 15MB each)
            </p>
          </div>

          {/* Selected File List */}
          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-600 px-1">
                <span>Selected Resumes ({selectedFiles.length})</span>
                <button
                  onClick={() => setSelectedFiles([])}
                  className="text-rose-500 hover:text-rose-600"
                >
                  Clear all
                </button>
              </div>
              <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
                {selectedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between bg-slate-50 border border-slate-200 px-3 py-2 rounded-lg text-xs"
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <FileText className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
                      <span className="truncate font-medium text-slate-700">{file.name}</span>
                    </div>
                    <span className="text-slate-400 ml-2 font-mono flex-shrink-0">
                      {(file.size / 1024).toFixed(0)} KB
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Message */}
          {uploadError && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 p-3 rounded-xl text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Success Results */}
          {uploadResults.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-700">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Successfully Ingested & Chunked ({uploadResults.length} Candidate{uploadResults.length > 1 ? "s" : ""}):</span>
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {uploadResults.map((r, i) => (
                  <div key={i} className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-1 text-xs">
                    <div className="flex items-center justify-between font-bold text-slate-800">
                      <span className="flex items-center space-x-1.5">
                        <User className="w-3.5 h-3.5 text-emerald-600" />
                        <span>{r.fullName}</span>
                      </span>
                      <span className="text-emerald-700 font-mono text-[11px] bg-emerald-100 px-2 py-0.5 rounded-full">
                        {r.totalExperienceYears} yrs exp
                      </span>
                    </div>
                    <p className="text-slate-600 font-medium">{r.headline}</p>
                    <div className="flex items-center space-x-4 text-[11px] text-slate-500 pt-1 border-t border-emerald-100">
                      <span className="flex items-center space-x-1">
                        <Sparkles className="w-3 h-3 text-purple-500" />
                        <span>{r.extractedSkillsCount} skills</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Database className="w-3 h-3 text-blue-500" />
                        <span>{r.chunksCount} chunks (768-d vectors)</span>
                      </span>
                      <span>{r.totalPages} page{r.totalPages > 1 ? "s" : ""}</span>
                    </div>

                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-lg hover:bg-slate-200/60 transition-colors"
          >
            {uploadResults.length > 0 ? "Done" : "Cancel"}
          </button>
          <button
            disabled={selectedFiles.length === 0 || isUploading}
            onClick={handleUpload}
            className="px-5 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-sm hover:shadow transition-all flex items-center space-x-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Extracting & Ingesting...</span>
              </>
            ) : (
              <>
                <Upload className="w-3.5 h-3.5" />
                <span>Ingest {selectedFiles.length > 0 ? `${selectedFiles.length} Resume${selectedFiles.length > 1 ? "s" : ""}` : "Resumes"}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
