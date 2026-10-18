// import { useState, useEffect } from "react";
// import { 
//   Sparkles, 
//   Sliders, 
//   Search, 
//   Download, 
//   Cpu, 
//   AlertCircle, 
//   User, 
//   Briefcase, 
//   GraduationCap, 
//   GitCommit, 
//   Star, 
//   MessageSquare, 
//   Zap,
//   Info,
//   Layers,
//   RefreshCw,
//   Check,
//   X,
//   ArrowLeftRight,
//   HelpCircle,
//   BarChart3,
//   CheckCircle2,
//   AlertTriangle,
//   Database,
//   Upload
// } from "lucide-react";
// import { Candidate, PipelineResults } from "./types.ts";
// import { ResumeUploadModal } from "./components/ResumeUploadModal.tsx";

// const DEFAULT_JOB_DESCRIPTION = `We are seeking a Senior Machine Learning Platform Engineer to design, build, and optimize high-throughput distributed LLM retrieval systems (RAG).

// Required Skills:
// - PyTorch, Python, and Transformers
// - Vector Databases (Pinecone, Milvus, Qdrant)
// - Docker, Kubernetes, and Ray

// Preferred Skills:
// - Experience with MLOps pipelines (MLflow, Kubeflow)
// - Deep learning performance optimization (TensorRT, vLLM)
// - Strong contributions to open-source ML frameworks

// Experience Required:
// - 5+ years of industry experience working with production-grade ML infrastructure.`;

// const PRESETS = [
//   {
//     name: "Senior ML Platform",
//     desc: DEFAULT_JOB_DESCRIPTION,
//     weights: { semantic: 45, skills: 35, career: 12, behavioral: 8 }
//   },
//   {
//     name: "Staff Frontend Architect",
//     desc: `We are looking for a Staff Frontend Architect specialized in React, Vite, and high-performance WebApps.

// Required Skills:
// - React, TypeScript, and state management (Zustand, Redux)
// - CSS frameworks (Tailwind CSS, CSS modules)
// - Build tooling optimization (Vite, Rollup, ESBuild)

// Experience Required:
// - 6+ years designing accessible, fluid, and scalable UI architectures.`,
//     weights: { semantic: 30, skills: 50, career: 10, behavioral: 10 }
//   },
//   {
//     name: "Lead Backend Developer",
//     desc: `Seeking a Backend Technical Lead to architect performant microservices and ML inference endpoints.

// Required Skills:
// - Python, FastAPI, Asyncio, and Uvicorn
// - SQL & NoSQL (PostgreSQL, Redis, Elasticsearch)
// - System design, API security, OAuth, and Docker

// Experience Required:
// - 5+ years of designing distributed Python servers at high scale.`,
//     weights: { semantic: 40, skills: 30, career: 20, behavioral: 10 }
//   }
// ];

// export default function App() {
//   const [jobDescription, setJobDescription] = useState(DEFAULT_JOB_DESCRIPTION);
//   const [topKRetrieval, setTopKRetrieval] = useState(2000);
//   const [useGeminiEmbedding, setUseGeminiEmbedding] = useState(false);
  
//   const [weights, setWeights] = useState({
//     semantic: 50,
//     skills: 25,
//     career: 15,
//     behavioral: 10
//   });

//   const [systemStatus, setSystemStatus] = useState({
//     success: false,
//     poolSize: 100000,
//     isPoolGenerated: false,
//     modelStatus: "loading",
//     faissStatus: "idle",
//     envHasApiKey: false,
//     database: {
//       connected: false,
//       engine: "PostgreSQL",
//       pgvector: "Initializing"
//     }
//   });

//   const [loading, setLoading] = useState(false);
//   const [results, setResults] = useState<PipelineResults | null>(null);
//   const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
//   const [aiExplanations, setAiExplanations] = useState<Record<string, string>>({});
//   const [explainingId, setExplainingId] = useState<string | null>(null);
//   const [error, setError] = useState<string | null>(null);
//   const [pollingStatus, setPollingStatus] = useState(false);

//   // New recruiter visual helpers
//   const [searchTerm, setSearchTerm] = useState("");
//   const [minExperience, setMinExperience] = useState(0);
//   const [selectedTier, setSelectedTier] = useState<string>("All");
//   const [compareIds, setCompareIds] = useState<string[]>([]);
//   const [compareMode, setCompareMode] = useState(false);
//   const [showHowItWorks, setShowHowItWorks] = useState(false);
//   const [showUploadModal, setShowUploadModal] = useState(false);

//   const handleWeightChange = (key: keyof typeof weights, value: number) => {
//     const diff = value - weights[key];
//     const otherKeys = (Object.keys(weights) as Array<keyof typeof weights>).filter(k => k !== key);
//     const otherSum = otherKeys.reduce((sum, k) => sum + weights[k], 0);
//     const newWeights = { ...weights };
//     newWeights[key] = value;

//     if (otherSum > 0) {
//       otherKeys.forEach(k => {
//         const share = weights[k] / otherSum;
//         const subVal = Math.round(weights[k] - diff * share);
//         newWeights[k] = Math.max(0, Math.min(100, subVal));
//       });
//     } else {
//       otherKeys.forEach(k => {
//         newWeights[k] = Math.max(0, Math.round((100 - value) / 3));
//       });
//     }

//     const currentSum = Object.values(newWeights).reduce((a, b) => a + b, 0);
//     if (currentSum !== 100) {
//       const adjustment = 100 - currentSum;
//       newWeights[otherKeys[0]] = Math.max(0, newWeights[otherKeys[0]] + adjustment);
//     }
//     setWeights(newWeights);
//   };

//   const fetchStatus = async () => {
//     try {
//       const res = await fetch("/api/status");
//       const contentType = res.headers.get("content-type");
//       if (res.ok && contentType && contentType.includes("application/json")) {
//         const data = await res.json();
//         setSystemStatus({
//           success: data.success,
//           poolSize: data.poolSize,
//           isPoolGenerated: data.isPoolGenerated,
//           modelStatus: data.modelStatus,
//           faissStatus: data.faissStatus,
//           envHasApiKey: data.envHasApiKey,
//           database: data.database || {
//             connected: false,
//             engine: "PostgreSQL",
//             pgvector: "Unknown"
//           }
//         });
//         setPollingStatus(data.faissStatus.includes("indexing"));
//       }
//     } catch (err) {
//       console.error("Error fetching system status:", err);
//     }
//   };

//   const initModel = async () => {
//     try {
//       await fetch("/api/init-model", { method: "POST" });
//       fetchStatus();
//     } catch (err) {
//       console.error("Error warming model:", err);
//     }
//   };

//   useEffect(() => {
//     fetchStatus();
//     const interval = setInterval(fetchStatus, pollingStatus ? 2000 : 8000);
//     return () => clearInterval(interval);
//   }, [pollingStatus]);

//   const handleRank = async () => {
//     setLoading(true);
//     setError(null);
//     try {
//       const res = await fetch("/api/rank", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           jobDescriptionText: jobDescription,
//           topKRetrieval,
//           useGeminiEmbedding,
//           weights: {
//             semantic: weights.semantic / 100,
//             skills: weights.skills / 100,
//             career: weights.career / 100,
//             behavioral: weights.behavioral / 100
//           }
//         })
//       });

//       if (!res.ok) {
//         const errData = await res.json();
//         throw new Error(errData.detail || "Failed to match resumes.");
//       }

//       const payload = await res.json();
//       if (payload.success) {
//         setResults(payload.data);
//         if (payload.data.topCandidates && payload.data.topCandidates.length > 0) {
//           setSelectedCandidate(payload.data.topCandidates[0]);
//         }
//         setCompareIds([]);
//         setCompareMode(false);
//       } else {
//         throw new Error("Pipeline returned failure status.");
//       }
//     } catch (err: any) {
//       setError(err.message || "An unexpected pipeline error occurred.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleExplain = async (candidate: Candidate) => {
//     if (!candidate) return;
//     setExplainingId(candidate.candidate_id);
//     try {
//       const res = await fetch("/api/explain", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ candidate, jobDescriptionText: jobDescription })
//       });

//       if (res.ok) {
//         const data = await res.json();
//         if (data.success) {
//           setAiExplanations(prev => ({ ...prev, [candidate.candidate_id]: data.reasoning }));
//           if (selectedCandidate?.candidate_id === candidate.candidate_id) {
//             setSelectedCandidate(prev => prev ? { ...prev, reasoning: data.reasoning } : null);
//           }
//         }
//       }
//     } catch (err) {
//       console.error("AI deep review failed:", err);
//     } finally {
//       setExplainingId(null);
//     }
//   };

//   const handleExportCSV = async () => {
//     if (!results?.topCandidates) return;
//     try {
//       const res = await fetch("/api/export-csv", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ candidates: results.topCandidates })
//       });

//       if (res.ok) {
//         const blob = await res.blob();
//         const url = window.URL.createObjectURL(blob);
//         const a = document.createElement("a");
//         a.href = url;
//         a.download = "matched_talent_export.csv";
//         document.body.appendChild(a);
//         a.click();
//         document.body.removeChild(a);
//       }
//     } catch (err) {
//       console.error("Export failed:", err);
//     }
//   };

//   const applyPreset = (preset: typeof PRESETS[0]) => {
//     setJobDescription(preset.desc);
//     setWeights(preset.weights);
//   };

//   // Compute matched skills and missing skills
//   const getSkillsBreakdown = (candidate: Candidate) => {
//     if (!results?.parsedFeatures) return { matched: candidate.skills, missing: [], additional: [] };
    
//     const required = results.parsedFeatures.requiredSkills.map(s => s.toLowerCase());
//     const preferred = results.parsedFeatures.preferredSkills.map(s => s.toLowerCase());
//     const allReq = [...required, ...preferred];
    
//     const candSkillsLower = candidate.skills.map(s => s.toLowerCase());
    
//     const matched = candidate.skills.filter(s => allReq.includes(s.toLowerCase()));
//     const additional = candidate.skills.filter(s => !allReq.includes(s.toLowerCase()));
    
//     // Find missing requested skills
//     const missing = results.parsedFeatures.requiredSkills.filter(s => !candSkillsLower.includes(s.toLowerCase()));

//     return { matched, missing, additional };
//   };

//   const filteredCandidates = results ? results.topCandidates.filter(c => {
//     const term = searchTerm.toLowerCase();
//     const matchesSearch = c.name.toLowerCase().includes(term) ||
//                           c.headline.toLowerCase().includes(term) ||
//                           c.skills.some(s => s.toLowerCase().includes(term));
//     const matchesExp = c.experience_years >= minExperience;
    
//     let matchesTier = true;
//     if (selectedTier !== "All") {
//       const score = c.scores.finalScore || 0;
//       if (selectedTier === "Excellent") matchesTier = score >= 90;
//       else if (selectedTier === "High") matchesTier = score >= 75 && score < 90;
//       else if (selectedTier === "Good") matchesTier = score >= 60 && score < 75;
//       else if (selectedTier === "General") matchesTier = score < 60;
//     }
    
//     return matchesSearch && matchesExp && matchesTier;
//   }) : [];

//   const toggleCompare = (id: string) => {
//     if (compareIds.includes(id)) {
//       setCompareIds(compareIds.filter(x => x !== id));
//     } else {
//       if (compareIds.length >= 3) return; // limit to 3 for clean side-by-side
//       setCompareIds([...compareIds, id]);
//     }
//   };

//   const getTierBadgeClass = (score: number) => {
//     if (score >= 90) return "bg-emerald-50 text-emerald-700 border-emerald-200";
//     if (score >= 75) return "bg-indigo-50 text-indigo-700 border-indigo-200";
//     if (score >= 60) return "bg-sky-50 text-sky-700 border-sky-200";
//     return "bg-slate-50 text-slate-700 border-slate-200";
//   };

//   const getTierName = (score: number) => {
//     if (score >= 90) return "A+ Outstanding";
//     if (score >= 75) return "A Strategic Match";
//     if (score >= 60) return "B Core Match";
//     return "C General Match";
//   };

//   return (
//     <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex flex-col font-sans antialiased" id="auratalent-root">
      
//       {/* ENTERPRISE APP NAVBAR */}
//       <header className="border-b border-slate-200 bg-white shadow-sm sticky top-0 z-40 px-6 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-4" id="header">
//         <div className="flex items-center space-x-3.5">
//           <div className="p-2.5 bg-indigo-600 rounded-xl shadow-md shadow-indigo-600/10 text-white flex items-center justify-center">
//             <Sparkles className="w-5.5 h-5.5 animate-pulse" />
//           </div>
//           <div>
//             <div className="flex items-center space-x-2">
//               <span className="text-lg font-bold text-slate-900 tracking-tight font-display">AuraTalent AI</span>
//               <span className="text-[10px] font-mono font-medium px-2 py-0.5 bg-indigo-50 text-indigo-600 border border-indigo-100 rounded-full">v2.4 Hybrid Matcher</span>
//             </div>
//             <p className="text-xs text-slate-500 font-medium">Enterprise Candidate Dual-Stage Scoring Hub &bull; 100,000 Pool</p>
//           </div>
//         </div>

//         {/* System Stats Indicators */}
//         <div className="flex flex-wrap items-center gap-3 text-xs" id="system-status-indicator">
          
//           <button 
//             onClick={() => setShowHowItWorks(!showHowItWorks)}
//             className="flex items-center space-x-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 px-3 py-1.5 rounded-lg border border-slate-200 transition font-medium"
//           >
//             <HelpCircle className="w-3.5 h-3.5" />
//             <span>How it Works</span>
//           </button>

//           {/* Model status */}
//           <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-lg">
//             <Cpu className="w-3.5 h-3.5 text-indigo-500" />
//             <span className="text-slate-500 font-medium">Model:</span>
//             {systemStatus.modelStatus.includes("loaded") ? (
//               <span className="text-emerald-600 font-bold flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse"></span>Active</span>
//             ) : systemStatus.modelStatus === "loading" ? (
//               <span className="text-amber-600 font-medium flex items-center animate-pulse"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Warming...</span>
//             ) : (
//               <button onClick={initModel} className="text-rose-500 hover:underline font-bold">Initialize</button>
//             )}
//           </div>

//           {/* Database active count */}
//           <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-lg">
//             <Database className="w-3.5 h-3.5 text-blue-600" />
//             <span className="text-slate-500 font-medium">Postgres:</span>
//             {systemStatus.database?.connected ? (
//               <span className="text-emerald-600 font-bold flex items-center">
//                 <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse"></span>
//                 pgvector
//               </span>
//             ) : (
//               <span className="text-amber-600 font-medium">Connecting...</span>
//             )}
//           </div>

//           {/* Candidate Index pool */}
//           <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-lg">
//             <Layers className="w-3.5 h-3.5 text-purple-500" />
//             <span className="text-slate-500 font-medium">Pool:</span>
//             {systemStatus.faissStatus.includes("loaded") || systemStatus.isPoolGenerated ? (
//               <span className="text-emerald-600 font-bold">100K Profiles</span>
//             ) : systemStatus.faissStatus.includes("indexing") ? (
//               <span className="text-amber-600 font-medium flex items-center animate-pulse"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Indexing...</span>
//             ) : (
//               <span className="text-slate-400">Loading Pool...</span>
//             )}
//           </div>

//           {/* API Key Status */}
//           <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-lg">
//             <Zap className={`w-3.5 h-3.5 ${systemStatus.envHasApiKey ? 'text-amber-500' : 'text-slate-400'}`} />
//             <span className="text-slate-500 font-medium">Gemini:</span>
//             {systemStatus.envHasApiKey ? (
//               <span className="text-emerald-600 font-bold">Linked</span>
//             ) : (
//               <span className="text-slate-400 font-medium">Heuristics</span>
//             )}
//           </div>

//           {/* Ingest Real PDF Resumes Button */}
//           <button
//             onClick={() => setShowUploadModal(true)}
//             className="flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg shadow-sm hover:shadow transition-all"
//           >
//             <Upload className="w-3.5 h-3.5" />
//             <span>Ingest Resumes (PDF)</span>
//           </button>
//         </div>
//       </header>


//       {/* HOW IT WORKS DIAGRAM OVERLAY */}
//       {showHowItWorks && (
//         <div className="bg-indigo-900 text-white p-5 px-6 border-b border-indigo-950 flex flex-col md:flex-row items-center justify-between gap-6 animate-fadeIn">
//           <div className="space-y-2 max-w-3xl">
//             <h3 className="font-display font-semibold text-base flex items-center gap-2">
//               <CheckCircle2 className="w-5 h-5 text-indigo-300" /> High-Performance Recruiting Pipeline Architecture
//             </h3>
//             <p className="text-xs text-indigo-100 leading-relaxed">
//               Recruiting software often buckles when matching hundreds of thousands of files. AuraTalent AI solves this by utilizing a <strong>Two-Stage Matching Architecture</strong>:
//             </p>
//             <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
//               <div className="bg-indigo-950/40 p-3 rounded-lg border border-indigo-800">
//                 <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300">Stage 1: Vector Search</span>
//                 <p className="text-[11px] text-indigo-100 mt-1 leading-normal">
//                   FAISS index screens the complete pool of 100,000 resume texts to immediately extract top candidates using sentence-transformers.
//                 </p>
//               </div>
//               <div className="bg-indigo-950/40 p-3 rounded-lg border border-indigo-800">
//                 <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300">Stage 2: Hybrid Scoring</span>
//                 <p className="text-[11px] text-indigo-100 mt-1 leading-normal">
//                   Weights combine multi-dimensional scores: semantic alignment, required skill overlap, career tenure velocity, and behavioral commitment.
//                 </p>
//               </div>
//               <div className="bg-indigo-950/40 p-3 rounded-lg border border-indigo-800">
//                 <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300">Stage 3: Generative AI Gap Analysis</span>
//                 <p className="text-[11px] text-indigo-100 mt-1 leading-normal">
//                   Gemini inspects the best fits, pinpointing exact career progress matches, highlighting key matching indicators, and detailing potential risks.
//                 </p>
//               </div>
//             </div>
//           </div>
//           <button 
//             onClick={() => setShowHowItWorks(false)}
//             className="bg-indigo-800 hover:bg-indigo-750 text-white border border-indigo-700 text-xs px-3.5 py-1.5 rounded-lg font-medium self-start sm:self-center shrink-0"
//           >
//             Got it, Hide Panel
//           </button>
//         </div>
//       )}

//       {/* DASHBOARD CONTAINER */}
//       <main className="flex-1 max-w-[1600px] w-full mx-auto p-4 lg:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 overflow-hidden" id="dashboard-main">
        
//         {/* LEFT COLUMN: CRITERIA & CONFIG (35% width) */}
//         <section className="lg:col-span-4 flex flex-col space-y-6 overflow-y-auto pr-1" id="criteria-config-section">
          
//           {/* CRITERIA SECTION */}
//           <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
//             <div className="flex justify-between items-center">
//               <h2 className="text-sm font-semibold text-slate-800 flex items-center">
//                 <Briefcase className="w-4.5 h-4.5 mr-2 text-indigo-600" /> Target Position Details
//               </h2>
//               <span className="text-[11px] text-slate-400 font-medium">Quick Presets</span>
//             </div>

//             {/* Quick Presets Select Buttons */}
//             <div className="grid grid-cols-3 gap-2">
//               {PRESETS.map((p, idx) => (
//                 <button
//                   key={idx}
//                   onClick={() => applyPreset(p)}
//                   className="text-[11px] font-semibold bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 text-slate-600 px-2 py-1.5 rounded-lg border border-slate-200 transition text-center truncate"
//                   title={p.name}
//                 >
//                   {p.name.replace("Senior ", "").replace("Staff ", "").replace("Lead ", "")}
//                 </button>
//               ))}
//             </div>

//             <div className="space-y-1.5">
//               <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Requirements Text</label>
//               <textarea
//                 value={jobDescription}
//                 onChange={(e) => setJobDescription(e.target.value)}
//                 placeholder="Paste the target job description or detailed technical requirements list here..."
//                 className="w-full h-44 bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500/25 focus:bg-white resize-none transition"
//               />
//             </div>
//           </div>

//           {/* DUAL-STAGE WEIGHTS AND PARAMS */}
//           <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-5">
//             <div className="flex justify-between items-center">
//               <h2 className="text-sm font-semibold text-slate-800 flex items-center">
//                 <Sliders className="w-4.5 h-4.5 mr-2 text-indigo-600" /> Scoring Param Matrix
//               </h2>
//               <span className="text-xs font-mono font-bold text-indigo-600 px-2.5 py-0.5 bg-indigo-50 rounded-full">Sum: 100%</span>
//             </div>
            
//             <p className="text-xs text-slate-500 leading-normal">
//               Fine-tune match emphasis. The system recalculates scores instantly using the adjusted weights.
//             </p>

//             <div className="space-y-4 pt-1">
//               {/* Semantic Weight */}
//               <div className="space-y-1">
//                 <div className="flex justify-between text-xs">
//                   <span className="font-semibold text-slate-700 flex items-center">
//                     Semantic Matching Alignment
//                     <span title="Measures deeper context alignment using text sentence-transformer embeddings." className="ml-1 text-slate-400 hover:text-indigo-600 cursor-help"><Info className="w-3.5 h-3.5" /></span>
//                   </span>
//                   <span className="font-mono text-indigo-600 font-bold">{weights.semantic}%</span>
//                 </div>
//                 <input
//                   type="range"
//                   min="0"
//                   max="100"
//                   value={weights.semantic}
//                   onChange={(e) => handleWeightChange("semantic", parseInt(e.target.value))}
//                   className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
//                 />
//               </div>

//               {/* Skills Weight */}
//               <div className="space-y-1">
//                 <div className="flex justify-between text-xs">
//                   <span className="font-semibold text-slate-700 flex items-center">
//                     Technical Skill Matrix Overlap
//                     <span title="Explicit validation against required/preferred skills parsed from requirement text." className="ml-1 text-slate-400 hover:text-indigo-600 cursor-help"><Info className="w-3.5 h-3.5" /></span>
//                   </span>
//                   <span className="font-mono text-indigo-600 font-bold">{weights.skills}%</span>
//                 </div>
//                 <input
//                   type="range"
//                   min="0"
//                   max="100"
//                   value={weights.skills}
//                   onChange={(e) => handleWeightChange("skills", parseInt(e.target.value))}
//                   className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
//                 />
//               </div>

//               {/* Career Tenure Weight */}
//               <div className="space-y-1">
//                 <div className="flex justify-between text-xs">
//                   <span className="font-semibold text-slate-700 flex items-center">
//                     Career Tenure & Stability
//                     <span title="Scored by total professional history duration, retention cycles, and rank progression speed." className="ml-1 text-slate-400 hover:text-indigo-600 cursor-help"><Info className="w-3.5 h-3.5" /></span>
//                   </span>
//                   <span className="font-mono text-indigo-600 font-bold">{weights.career}%</span>
//                 </div>
//                 <input
//                   type="range"
//                   min="0"
//                   max="100"
//                   value={weights.career}
//                   onChange={(e) => handleWeightChange("career", parseInt(e.target.value))}
//                   className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
//                 />
//               </div>

//               {/* Behavioral Weight */}
//               <div className="space-y-1">
//                 <div className="flex justify-between text-xs">
//                   <span className="font-semibold text-slate-700 flex items-center">
//                     Open Source & Engagement Rates
//                     <span title="Calculated from public GitHub stars, commits, and recruiter message response velocities." className="ml-1 text-slate-400 hover:text-indigo-600 cursor-help"><Info className="w-3.5 h-3.5" /></span>
//                   </span>
//                   <span className="font-mono text-indigo-600 font-bold">{weights.behavioral}%</span>
//                 </div>
//                 <input
//                   type="range"
//                   min="0"
//                   max="100"
//                   value={weights.behavioral}
//                   onChange={(e) => handleWeightChange("behavioral", parseInt(e.target.value))}
//                   className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
//                 />
//               </div>
//             </div>

//             {/* PIPELINE OPTIONS */}
//             <div className="border-t border-slate-100 pt-4 space-y-3.5">
//               <div className="grid grid-cols-2 gap-3.5">
//                 <div className="space-y-1">
//                   <label className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">Stage 1 Filter K</label>
//                   <select
//                     value={topKRetrieval}
//                     onChange={(e) => setTopKRetrieval(parseInt(e.target.value))}
//                     className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-700 py-2 px-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition font-medium"
//                   >
//                     <option value="500">500 candidates</option>
//                     <option value="1000">1,000 candidates</option>
//                     <option value="2000">2,000 candidates</option>
//                     <option value="5000">5,000 candidates</option>
//                   </select>
//                 </div>

//                 <div className="space-y-1">
//                   <label className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">Embedder Model</label>
//                   <div className="flex items-center space-x-1 bg-slate-50 border border-slate-200 p-0.5 rounded-xl">
//                     <button
//                       type="button"
//                       onClick={() => setUseGeminiEmbedding(false)}
//                       className={`flex-1 py-1.5 px-2 rounded-lg text-[10px] font-bold transition ${!useGeminiEmbedding ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
//                     >
//                       MiniLM
//                     </button>
//                     <button
//                       type="button"
//                       disabled={!systemStatus.envHasApiKey}
//                       onClick={() => setUseGeminiEmbedding(true)}
//                       className={`flex-1 py-1.5 px-2 rounded-lg text-[10px] font-bold transition disabled:opacity-40 disabled:cursor-not-allowed ${useGeminiEmbedding ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
//                       title={!systemStatus.envHasApiKey ? "Requires GEMINI_API_KEY environment variable" : "Use Google Cloud text-embedding-004"}
//                     >
//                       Gemini
//                     </button>
//                   </div>
//                 </div>
//               </div>
//             </div>

//             {/* MATCH ACTION BAR */}
//             <div className="pt-2">
//               <button
//                 type="button"
//                 onClick={handleRank}
//                 disabled={loading || (!systemStatus.modelStatus.includes("loaded") && !useGeminiEmbedding)}
//                 className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-100 disabled:text-slate-400 disabled:border-slate-100 text-white font-bold py-3 px-4 rounded-xl text-xs flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/15 border border-indigo-500/20 transition cursor-pointer"
//                 id="rank-button"
//               >
//                 {loading ? (
//                   <>
//                     <RefreshCw className="w-4 h-4 animate-spin text-white" />
//                     <span>Executing Dual-Stage Pipeline...</span>
//                   </>
//                 ) : (
//                   <>
//                     <Search className="w-4 h-4 text-white" />
//                     <span>Compile & Evaluate 100,000 Resumes</span>
//                   </>
//                 )}
//               </button>
//             </div>

//             {error && (
//               <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3.5 rounded-xl text-xs flex items-start space-x-2.5">
//                 <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
//                 <span className="font-medium">{error}</span>
//               </div>
//             )}
//           </div>
//         </section>

//         {/* RIGHT COLUMN: RESULTS & DEEP INSPECT SPLIT (65% width) */}
//         <section className="lg:col-span-8 flex flex-col space-y-6 overflow-hidden" id="results-section">
//           {loading ? (
//             <div className="flex-1 bg-white border border-slate-200 rounded-3xl p-8 flex flex-col items-center justify-center text-center space-y-6 shadow-sm" id="loading-panel">
//               <div className="relative">
//                 <div className="absolute inset-0 bg-indigo-500/10 rounded-full animate-ping border border-indigo-500/20"></div>
//                 <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center relative z-10">
//                   <Cpu className="w-8 h-8 text-indigo-600 animate-pulse" />
//                 </div>
//               </div>
//               <div className="space-y-2">
//                 <h3 className="font-display font-bold text-lg text-slate-800">Pruning & High-Fidelity Scoring Candidate Pool</h3>
//                 <p className="text-slate-500 text-xs max-w-sm mx-auto leading-relaxed font-medium">
//                   Stage 1 is executing fast-index vector scanning on 100,000 resume files. Stage 2 will then apply multi-dimensional scoring weights on the top {topKRetrieval} results.
//                 </p>
//               </div>
//               <div className="w-64 h-2 bg-slate-100 rounded-full overflow-hidden">
//                 <div className="h-full bg-indigo-600 rounded-full animate-loading-bar w-2/3"></div>
//               </div>
//             </div>
//           ) : results ? (
//             <div className="flex-1 flex flex-col space-y-6 overflow-hidden" id="results-active-panel">
              
//               {/* TELEMETRY BAR & DYNAMIC MATRIX COMPACT DECK */}
//               <div className="grid grid-cols-1 md:grid-cols-12 gap-4 shrink-0" id="telemetry-grid">
                
//                 {/* Processing Telemetry */}
//                 <div className="md:col-span-6 bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col justify-between space-y-3">
//                   <div className="flex justify-between items-center">
//                     <h3 className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider flex items-center font-display">
//                       <Cpu className="w-3.5 h-3.5 mr-1.5" /> Match Telemetry Analytics
//                     </h3>
//                     <span className="text-[10px] font-mono font-bold text-slate-400">FAISS Powered</span>
//                   </div>
                  
//                   <div className="grid grid-cols-3 gap-2.5">
//                     <div className="bg-slate-50/70 p-2 rounded-xl border border-slate-100 text-center">
//                       <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide">Stage 1 Seek</p>
//                       <p className="text-sm font-mono font-bold text-slate-800 mt-0.5">{results.telemetry.stage1TimeMs}ms</p>
//                     </div>
//                     <div className="bg-slate-50/70 p-2 rounded-xl border border-slate-100 text-center">
//                       <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide">Stage 2 Score</p>
//                       <p className="text-sm font-mono font-bold text-slate-800 mt-0.5">{results.telemetry.stage2TimeMs}ms</p>
//                     </div>
//                     <div className="bg-indigo-50/40 p-2 rounded-xl border border-indigo-100 text-center">
//                       <p className="text-[9px] text-indigo-500 font-bold uppercase tracking-wide">Total Time</p>
//                       <p className="text-sm font-mono font-bold text-indigo-600 mt-0.5">{results.telemetry.totalTimeMs}ms</p>
//                     </div>
//                   </div>
                  
//                   <div className="flex justify-between text-[10px] text-slate-500 font-medium font-mono border-t border-slate-100 pt-1.5">
//                     <span>Pool: {results.telemetry.totalCandidates.toLocaleString()} files</span>
//                     <span>Model: {results.telemetry.modelUsed}</span>
//                   </div>
//                 </div>

//                 {/* Extracted requirement matrices */}
//                 <div className="md:col-span-6 bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col justify-between space-y-2">
//                   <h3 className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider flex items-center font-display">
//                     <Sliders className="w-3.5 h-3.5 mr-1.5" /> Parsed Requirements Matrix
//                   </h3>
                  
//                   <div className="space-y-1 text-xs">
//                     <div className="flex items-center text-slate-600">
//                       <span className="text-slate-400 font-bold w-20">Exp Required:</span>
//                       <span className="font-bold text-slate-800 font-mono">{results.parsedFeatures.experienceYearsRequired}+ Years Professional</span>
//                     </div>
//                     <div className="flex items-center text-slate-600">
//                       <span className="text-slate-400 font-bold w-20">Req Skills:</span>
//                       <div className="flex flex-wrap gap-1 max-h-12 overflow-y-auto">
//                         {results.parsedFeatures.requiredSkills.slice(0, 3).map((s, idx) => (
//                           <span key={idx} className="bg-slate-100 text-slate-700 text-[9px] px-1.5 py-0.5 rounded-md font-bold border border-slate-200">{s}</span>
//                         ))}
//                         {results.parsedFeatures.requiredSkills.length > 3 && (
//                           <span className="text-[9px] text-slate-400 font-mono">+{results.parsedFeatures.requiredSkills.length - 3} more</span>
//                         )}
//                       </div>
//                     </div>
//                     <div className="flex items-center text-slate-600">
//                       <span className="text-slate-400 font-bold w-20">Key Vectors:</span>
//                       <div className="flex flex-wrap gap-1 max-h-12 overflow-y-auto">
//                         {results.parsedFeatures.domainKeywords.slice(0, 3).map((s, idx) => (
//                           <span key={idx} className="bg-indigo-50 text-indigo-600 text-[9px] px-1.5 py-0.5 rounded-md font-bold border border-indigo-100">{s}</span>
//                         ))}
//                       </div>
//                     </div>
//                   </div>
//                 </div>
//               </div>

//               {/* CANDIDATES GRID & PROFILE SPLIT PANEL OR SIDE-BY-SIDE COMPARISON VIEW */}
//               {compareMode ? (
//                 /* COMPARATOR MODULE */
//                 <div className="flex-1 bg-white border border-slate-200 rounded-2xl flex flex-col overflow-hidden animate-fadeIn">
//                   <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex justify-between items-center">
//                     <div>
//                       <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 font-display">
//                         <ArrowLeftRight className="w-4.5 h-4.5 text-indigo-600" /> Executive Talent Comparison Grid
//                       </h3>
//                       <p className="text-xs text-slate-500">Side-by-side performance, skill overlaps, and professional tenure metrics</p>
//                     </div>
//                     <button
//                       onClick={() => setCompareMode(false)}
//                       className="bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
//                     >
//                       <X className="w-3.5 h-3.5" />
//                       <span>Close Comparison</span>
//                     </button>
//                   </div>

//                   <div className="flex-1 overflow-x-auto p-4 lg:p-6">
//                     <div className="flex gap-6 min-w-[700px] h-full items-start">
//                       {results.topCandidates
//                         .filter(c => compareIds.includes(c.candidate_id))
//                         .map(c => {
//                           const { matched, missing } = getSkillsBreakdown(c);
//                           return (
//                             <div key={c.candidate_id} className="flex-1 bg-slate-50/50 border border-slate-200 rounded-2xl p-5 flex flex-col h-full overflow-y-auto space-y-5">
                              
//                               {/* Header Card */}
//                               <div className="space-y-2 border-b border-slate-200 pb-3">
//                                 <div className="flex justify-between items-start">
//                                   <div className="w-10 h-10 rounded-full bg-indigo-600 text-white font-bold text-sm flex items-center justify-center shadow-sm">
//                                     {c.name.split(" ").map(n => n[0]).join("")}
//                                   </div>
//                                   <div className="text-right">
//                                     <span className="font-mono text-sm font-bold text-indigo-600 bg-white border border-slate-200 px-2.5 py-1 rounded-full shadow-sm">
//                                       {c.scores.finalScore}%
//                                     </span>
//                                     <p className="text-[9px] text-slate-400 font-bold uppercase mt-1">Match Index</p>
//                                   </div>
//                                 </div>
//                                 <h4 className="font-bold text-slate-900 text-sm">{c.name}</h4>
//                                 <p className="text-xs text-indigo-600 font-semibold">{c.headline}</p>
//                                 <span className={`inline-block border text-[10px] font-bold px-2 py-0.5 rounded-md mt-1 ${getTierBadgeClass(c.scores.finalScore || 0)}`}>
//                                   {getTierName(c.scores.finalScore || 0)}
//                                 </span>
//                               </div>

//                               {/* Core metrics comparison */}
//                               <div className="space-y-3.5">
//                                 <h5 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Metrics Matrix</h5>
                                
//                                 <div className="space-y-2">
//                                   <div className="flex justify-between text-xs">
//                                     <span className="text-slate-500">Exp Years</span>
//                                     <span className="font-bold text-slate-800">{c.experience_years} Years</span>
//                                   </div>
//                                   <div className="flex justify-between text-xs">
//                                     <span className="text-slate-500">Education</span>
//                                     <span className="font-semibold text-slate-800 text-right truncate max-w-[150px]" title={c.education}>{c.education.split(",")[0]}</span>
//                                   </div>
//                                 </div>

//                                 <div className="space-y-2 pt-2 border-t border-slate-200/60">
//                                   {/* Semantic Progress */}
//                                   <div>
//                                     <div className="flex justify-between text-[11px] mb-1">
//                                       <span className="text-slate-500">Semantic Alignment</span>
//                                       <span className="font-mono font-bold text-slate-700">{c.scores.semanticScore}%</span>
//                                     </div>
//                                     <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
//                                       <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${c.scores.semanticScore}%` }}></div>
//                                     </div>
//                                   </div>

//                                   {/* Skill Progress */}
//                                   <div>
//                                     <div className="flex justify-between text-[11px] mb-1">
//                                       <span className="text-slate-500">Skill Alignment</span>
//                                       <span className="font-mono font-bold text-slate-700">{c.scores.skillScore}%</span>
//                                     </div>
//                                     <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
//                                       <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${c.scores.skillScore}%` }}></div>
//                                     </div>
//                                   </div>

//                                   {/* Stability */}
//                                   <div>
//                                     <div className="flex justify-between text-[11px] mb-1">
//                                       <span className="text-slate-500">Tenure Velocity</span>
//                                       <span className="font-mono font-bold text-slate-700">{c.scores.careerScore}%</span>
//                                     </div>
//                                     <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
//                                       <div className="h-full bg-rose-500 rounded-full" style={{ width: `${c.scores.careerScore}%` }}></div>
//                                     </div>
//                                   </div>
//                                 </div>
//                               </div>

//                               {/* Skills match overlaps */}
//                               <div className="space-y-2 pt-3 border-t border-slate-200/60">
//                                 <h5 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Required overlaps ({matched.length})</h5>
//                                 <div className="flex flex-wrap gap-1">
//                                   {matched.map((s, idx) => (
//                                     <span key={idx} className="bg-emerald-50 text-emerald-700 text-[10px] px-2 py-0.5 rounded-md font-bold border border-emerald-100">{s}</span>
//                                   ))}
//                                   {missing.map((s, idx) => (
//                                     <span key={idx} className="bg-slate-100 text-slate-400 line-through text-[10px] px-2 py-0.5 rounded-md border border-slate-200">{s}</span>
//                                   ))}
//                                 </div>
//                               </div>

//                               {/* GitHub metrics comparison */}
//                               <div className="space-y-3 pt-3 border-t border-slate-200/60">
//                                 <h5 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Public Engagement</h5>
//                                 <div className="grid grid-cols-2 gap-2 text-center">
//                                   <div className="bg-white p-2 border border-slate-200 rounded-xl">
//                                     <p className="text-[9px] text-slate-400 font-bold uppercase">GitHub Stars</p>
//                                     <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{c.behavioral_signals.github_stars}</p>
//                                   </div>
//                                   <div className="bg-white p-2 border border-slate-200 rounded-xl">
//                                     <p className="text-[9px] text-slate-400 font-bold uppercase">Response Rate</p>
//                                     <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{Math.round(c.behavioral_signals.recruiter_response_rate * 100)}%</p>
//                                   </div>
//                                 </div>
//                               </div>

//                               {/* AI Explanation / Summary block */}
//                               <div className="pt-3 border-t border-slate-200/60 space-y-1">
//                                 <h5 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Evaluation Analysis</h5>
//                                 <p className="text-xs text-slate-600 italic leading-relaxed">
//                                   "{aiExplanations[c.candidate_id] || c.reasoning || "No deep review executed."}"
//                                 </p>
//                               </div>

//                             </div>
//                           );
//                         })}
//                     </div>
//                   </div>
//                 </div>
//               ) : (
//                 /* TWO-COLUMN EXPANDED SEARCH & DETAIL SPLIT MODULE */
//                 <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-6 overflow-hidden" id="results-split-panel">
                  
//                   {/* LEFT: CANDIDATE SELECTABLE SCROLL LIST (Top 100) */}
//                   <div className="md:col-span-5 bg-white border border-slate-200 rounded-2xl flex flex-col overflow-hidden shadow-sm" id="candidates-column">
                    
//                     {/* Header search tools */}
//                     <div className="p-4 border-b border-slate-200 bg-slate-50/50 space-y-3 shrink-0">
//                       <div className="flex justify-between items-center">
//                         <div>
//                           <h3 className="font-bold text-slate-800 text-sm font-display">Ranked Matches</h3>
//                           <p className="text-[10px] text-slate-400">FAISS filtered stage 1 & 2 matches</p>
//                         </div>
//                         <button
//                           onClick={handleExportCSV}
//                           className="bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 px-2.5 py-1.5 rounded-xl text-xs font-bold flex items-center space-x-1 cursor-pointer transition shadow-sm"
//                         >
//                           <Download className="w-3.5 h-3.5" />
//                           <span>CSV</span>
//                         </button>
//                       </div>

//                       {/* Dynamic filter bar inside list */}
//                       <div className="space-y-2">
//                         <div className="relative">
//                           <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
//                           <input
//                             type="text"
//                             value={searchTerm}
//                             onChange={(e) => setSearchTerm(e.target.value)}
//                             placeholder="Filter by name, skill, title..."
//                             className="w-full bg-white border border-slate-200 text-xs rounded-xl pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/25 transition"
//                           />
//                         </div>

//                         {/* Experience and Tier Filters */}
//                         <div className="grid grid-cols-2 gap-2">
//                           <div>
//                             <select
//                               value={selectedTier}
//                               onChange={(e) => setSelectedTier(e.target.value)}
//                               className="w-full bg-white border border-slate-200 text-[11px] rounded-lg py-1 px-1.5 focus:outline-none font-semibold text-slate-600"
//                             >
//                               <option value="All">All Score Tiers</option>
//                               <option value="Excellent">Excellent (90%+)</option>
//                               <option value="High">High (75%-90%)</option>
//                               <option value="Good">Good (60%-75%)</option>
//                               <option value="General">General (&lt;60%)</option>
//                             </select>
//                           </div>
//                           <div>
//                             <select
//                               value={minExperience}
//                               onChange={(e) => setMinExperience(parseInt(e.target.value))}
//                               className="w-full bg-white border border-slate-200 text-[11px] rounded-lg py-1 px-1.5 focus:outline-none font-semibold text-slate-600"
//                             >
//                               <option value="0">Min Exp: Any</option>
//                               <option value="3">Min Exp: 3+ Yrs</option>
//                               <option value="5">Min Exp: 5+ Yrs</option>
//                               <option value="8">Min Exp: 8+ Yrs</option>
//                               <option value="10">Min Exp: 10+ Yrs</option>
//                             </select>
//                           </div>
//                         </div>
//                       </div>
//                     </div>

//                     {/* Candidates scroll container */}
//                     <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-slate-50/30" id="candidates-list-scroll">
//                       {filteredCandidates.length > 0 ? (
//                         filteredCandidates.map((c) => {
//                           const isSelected = selectedCandidate?.candidate_id === c.candidate_id;
//                           const isCompareChecked = compareIds.includes(c.candidate_id);
//                           return (
//                             <div
//                               key={c.candidate_id}
//                               className={`p-3 rounded-xl border transition-all duration-150 relative flex flex-col gap-2 ${
//                                 isSelected 
//                                   ? "bg-white border-indigo-500 shadow-md ring-1 ring-indigo-500/10" 
//                                   : "bg-white hover:bg-slate-50/50 border-slate-200/80"
//                               }`}
//                             >
                              
//                               {/* Top row */}
//                               <div className="flex items-start justify-between gap-2">
//                                 <div 
//                                   className="flex items-center space-x-2.5 min-w-0 cursor-pointer flex-1"
//                                   onClick={() => setSelectedCandidate(c)}
//                                 >
//                                   {/* Rank Tag */}
//                                   <div className={`w-6 h-6 rounded-md flex items-center justify-center font-mono text-[10px] font-bold shrink-0 ${
//                                     c.rank && c.rank <= 3 
//                                       ? "bg-indigo-600 text-white shadow-sm" 
//                                       : "bg-slate-100 text-slate-500 border border-slate-200"
//                                   }`}>
//                                     #{c.rank}
//                                   </div>
//                                   <div className="min-w-0">
//                                     <h4 className="text-xs font-bold text-slate-900 truncate">{c.name}</h4>
//                                     <p className="text-[10px] text-indigo-600 font-semibold truncate">{c.headline}</p>
//                                   </div>
//                                 </div>

//                                 <div className="flex items-center space-x-2 shrink-0">
//                                   {/* Compare Checkbox */}
//                                   <label 
//                                     className="flex items-center space-x-1 cursor-pointer"
//                                     title="Add candidate to executive side-by-side comparison"
//                                   >
//                                     <input
//                                       type="checkbox"
//                                       checked={isCompareChecked}
//                                       onChange={() => toggleCompare(c.candidate_id)}
//                                       className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5 cursor-pointer"
//                                     />
//                                     <span className="text-[9px] text-slate-400 font-bold uppercase hidden sm:inline">Compare</span>
//                                   </label>

//                                   {/* Score badge */}
//                                   <span className={`font-mono text-xs font-bold border px-1.5 py-0.5 rounded-md ${getTierBadgeClass(c.scores.finalScore || 0)}`}>
//                                     {c.scores.finalScore}%
//                                   </span>
//                                 </div>
//                               </div>

//                               {/* Body content row (Trigger select candidate) */}
//                               <div 
//                                 className="cursor-pointer space-y-1.5"
//                                 onClick={() => setSelectedCandidate(c)}
//                               >
//                                 <p className="text-[10px] text-slate-500 font-mono font-medium">
//                                   {c.experience_years}y Exp &bull; {c.education.split(",")[0]}
//                                 </p>
//                                 <p className="text-[10px] text-slate-600 italic line-clamp-1 border-t border-slate-100 pt-1.5">
//                                   "{aiExplanations[c.candidate_id] || c.reasoning}"
//                                 </p>
//                               </div>

//                             </div>
//                           );
//                         })
//                       ) : (
//                         <div className="text-center py-10 space-y-2">
//                           <AlertTriangle className="w-6 h-6 text-slate-300 mx-auto" />
//                           <p className="text-xs text-slate-400 font-bold">No matching candidates found.</p>
//                           <p className="text-[10px] text-slate-400">Try loosening your experience or search keyword filter criteria.</p>
//                         </div>
//                       )}
//                     </div>
//                   </div>

//                   {/* RIGHT: EXPANDED CANDIDATE DETAIL WORKSPACE (7% width) */}
//                   <div className="md:col-span-7 bg-white border border-slate-200 rounded-2xl flex flex-col overflow-hidden shadow-sm" id="candidate-detail-column">
//                     {selectedCandidate ? (
//                       <div className="flex-1 flex flex-col overflow-hidden animate-fadeIn">
                        
//                         {/* DETAIL HEADER CARD */}
//                         <div className="p-5 border-b border-slate-200 bg-slate-50/30 shrink-0 space-y-4">
//                           <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
//                             <div className="flex items-center space-x-3">
//                               {/* Avatar circle */}
//                               <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white font-bold text-lg flex items-center justify-center shadow-sm">
//                                 {selectedCandidate.name.split(" ").map(n => n[0]).join("")}
//                               </div>
//                               <div>
//                                 <div className="flex items-center space-x-2">
//                                   <h3 className="font-bold text-base text-slate-900 font-display">{selectedCandidate.name}</h3>
//                                   <span className="text-[9px] font-mono bg-indigo-50 text-indigo-600 px-2 py-0.5 border border-indigo-100 rounded-full">
//                                     ID: {selectedCandidate.candidate_id.substring(0, 10)}
//                                   </span>
//                                 </div>
//                                 <p className="text-xs text-indigo-600 font-semibold mt-0.5">{selectedCandidate.headline}</p>
//                                 <p className="text-[10px] text-slate-400 mt-0.5">🎓 {selectedCandidate.education}</p>
//                               </div>
//                             </div>
                            
//                             {/* Visual Score Circle badge */}
//                             <div className="flex items-center space-x-2.5 bg-white border border-slate-200 p-2 rounded-2xl shadow-sm self-start sm:self-auto">
//                               <div className="w-12 h-12 rounded-full border-4 border-indigo-500/10 border-t-indigo-600 flex items-center justify-center font-mono text-sm font-bold text-slate-800">
//                                 {selectedCandidate.scores.finalScore}%
//                               </div>
//                               <div>
//                                 <p className="text-[9px] text-slate-400 font-bold uppercase">Weighted Index</p>
//                                 <span className={`inline-block text-[10px] font-bold px-1.5 py-0.5 rounded mt-0.5 ${getTierBadgeClass(selectedCandidate.scores.finalScore || 0)}`}>
//                                   {getTierName(selectedCandidate.scores.finalScore || 0)}
//                                 </span>
//                               </div>
//                             </div>
//                           </div>

//                           {/* AI Justification / Explanation panel */}
//                           <div className="bg-white border border-indigo-100 p-3.5 rounded-2xl shadow-sm flex flex-col space-y-2">
//                             <div className="flex justify-between items-center">
//                               <span className="text-[10px] text-indigo-600 font-bold uppercase tracking-wider flex items-center font-display">
//                                 <Sparkles className="w-3.5 h-3.5 mr-1.5 text-indigo-500 animate-pulse" /> Justification Analysis
//                               </span>
//                               {!aiExplanations[selectedCandidate.candidate_id] && (
//                                 <button
//                                   onClick={() => handleExplain(selectedCandidate)}
//                                   disabled={explainingId === selectedCandidate.candidate_id}
//                                   className="text-[10px] bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-100 disabled:text-slate-400 text-white font-bold py-1 px-2.5 rounded-lg border border-indigo-500/20 flex items-center space-x-1 cursor-pointer transition shadow-sm"
//                                 >
//                                   {explainingId === selectedCandidate.candidate_id ? (
//                                     <>
//                                       <RefreshCw className="w-3 h-3 animate-spin" />
//                                       <span>Calling Gemini...</span>
//                                     </>
//                                   ) : (
//                                     <>
//                                       <Sparkles className="w-3.5 h-3.5" />
//                                       <span>Gemini Gap Evaluation</span>
//                                     </>
//                                   )}
//                                 </button>
//                               )}
//                             </div>
//                             <p className="text-xs text-slate-600 leading-relaxed italic">
//                               "{aiExplanations[selectedCandidate.candidate_id] || selectedCandidate.reasoning}"
//                             </p>
//                           </div>
//                         </div>

//                         {/* DETAIL SCROLL CONTENT PANEL */}
//                         <div className="flex-1 overflow-y-auto p-5 space-y-5">
                          
//                           {/* SCORE VECTOR CHANNELS */}
//                           <div className="space-y-2.5">
//                             <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center">
//                               <BarChart3 className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> Score Vector Breakdown
//                             </h4>
//                             <div className="grid grid-cols-2 gap-3">
//                               <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 flex justify-between items-center">
//                                 <div>
//                                   <p className="text-[9px] text-slate-400 font-bold uppercase">Semantic Alignment</p>
//                                   <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.scores.semanticScore}%</p>
//                                 </div>
//                                 <div className="w-1 h-8 bg-slate-200 rounded-full overflow-hidden">
//                                   <div className="bg-indigo-600 h-full rounded-full" style={{ height: `${selectedCandidate.scores.semanticScore}%` }}></div>
//                                 </div>
//                               </div>

//                               <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 flex justify-between items-center">
//                                 <div>
//                                   <p className="text-[9px] text-slate-400 font-bold uppercase">Technical Skill Match</p>
//                                   <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.scores.skillScore}%</p>
//                                 </div>
//                                 <div className="w-1 h-8 bg-slate-200 rounded-full overflow-hidden">
//                                   <div className="bg-emerald-500 h-full rounded-full" style={{ height: `${selectedCandidate.scores.skillScore}%` }}></div>
//                                 </div>
//                               </div>

//                               <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 flex justify-between items-center">
//                                 <div>
//                                   <p className="text-[9px] text-slate-400 font-bold uppercase">Progression Tenure</p>
//                                   <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.scores.careerScore}%</p>
//                                 </div>
//                                 <div className="w-1 h-8 bg-slate-200 rounded-full overflow-hidden">
//                                   <div className="bg-rose-500 h-full rounded-full" style={{ height: `${selectedCandidate.scores.careerScore}%` }}></div>
//                                 </div>
//                               </div>

//                               <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 flex justify-between items-center">
//                                 <div>
//                                   <p className="text-[9px] text-slate-400 font-bold uppercase">Behavioral Commitment</p>
//                                   <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.scores.behavioralScore}%</p>
//                                 </div>
//                                 <div className="w-1 h-8 bg-slate-200 rounded-full overflow-hidden">
//                                   <div className="bg-amber-500 h-full rounded-full" style={{ height: `${selectedCandidate.scores.behavioralScore}%` }}></div>
//                                 </div>
//                               </div>
//                             </div>
//                           </div>

//                           {/* RECRUITER SKILLS MATCH & GAP EVALUATOR */}
//                           <div className="space-y-3.5 pt-3 border-t border-slate-100">
//                             <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center">
//                               <Check className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> Skills catalog & requested gaps
//                             </h4>
                            
//                             {(() => {
//                               const { matched, missing, additional } = getSkillsBreakdown(selectedCandidate);
//                               return (
//                                 <div className="space-y-3 text-xs">
//                                   {/* Overlaps / Matched */}
//                                   <div className="space-y-1.5">
//                                     <p className="text-[10px] text-emerald-600 font-bold uppercase tracking-wide flex items-center gap-1">
//                                       <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Matched Skills ({matched.length})
//                                     </p>
//                                     <div className="flex flex-wrap gap-1.5">
//                                       {matched.map((s, idx) => (
//                                         <span key={idx} className="bg-emerald-50 text-emerald-700 text-xs py-1 px-2.5 rounded-lg font-bold border border-emerald-100 flex items-center">
//                                           <Check className="w-3 h-3 mr-1 text-emerald-500" /> {s}
//                                         </span>
//                                       ))}
//                                     </div>
//                                   </div>

//                                   {/* Missing / Gaps */}
//                                   {missing.length > 0 && (
//                                     <div className="space-y-1.5">
//                                       <p className="text-[10px] text-rose-600 font-bold uppercase tracking-wide flex items-center gap-1">
//                                         <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span> Target Skill Gap ({missing.length})
//                                       </p>
//                                       <div className="flex flex-wrap gap-1.5">
//                                         {missing.map((s, idx) => (
//                                           <span key={idx} className="bg-rose-50/50 text-rose-700 text-xs py-1 px-2.5 rounded-lg font-semibold border border-rose-100 flex items-center" title="Missing target required technical skill">
//                                             <X className="w-3 h-3 mr-1 text-rose-400" /> {s}
//                                           </span>
//                                         ))}
//                                       </div>
//                                     </div>
//                                   )}

//                                   {/* Additional talent skills */}
//                                   {additional.length > 0 && (
//                                     <div className="space-y-1.5">
//                                       <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wide">Additional Talent Skills ({additional.length})</p>
//                                       <div className="flex flex-wrap gap-1.5">
//                                         {additional.map((s, idx) => (
//                                           <span key={idx} className="bg-slate-50 text-slate-600 text-xs py-1 px-2.5 rounded-lg border border-slate-200">{s}</span>
//                                         ))}
//                                       </div>
//                                     </div>
//                                   )}
//                                 </div>
//                               );
//                             })()}
//                           </div>

//                           {/* PUBLIC ENGAGEMENT METRICS DECK */}
//                           <div className="space-y-2.5 pt-3 border-t border-slate-100">
//                             <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center">
//                               <Star className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> Open Source & Engagement Signals
//                             </h4>
//                             <div className="grid grid-cols-3 gap-3">
//                               <div className="bg-slate-50/50 p-3 rounded-2xl border border-slate-100 flex items-center space-x-2.5">
//                                 <Star className="w-4 h-4 text-amber-500 shrink-0" />
//                                 <div>
//                                   <p className="text-[9px] text-slate-400 font-bold uppercase">GitHub Stars</p>
//                                   <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.behavioral_signals.github_stars}</p>
//                                 </div>
//                               </div>
//                               <div className="bg-slate-50/50 p-3 rounded-2xl border border-slate-100 flex items-center space-x-2.5">
//                                 <GitCommit className="w-4 h-4 text-indigo-500 shrink-0" />
//                                 <div>
//                                   <p className="text-[9px] text-slate-400 font-bold uppercase">Commits/Year</p>
//                                   <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.behavioral_signals.github_commits_last_year}</p>
//                                 </div>
//                               </div>
//                               <div className="bg-slate-50/50 p-3 rounded-2xl border border-slate-100 flex items-center space-x-2.5">
//                                 <MessageSquare className="w-4 h-4 text-emerald-500 shrink-0" />
//                                 <div>
//                                   <p className="text-[9px] text-slate-400 font-bold uppercase">Response Rate</p>
//                                   <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{Math.round(selectedCandidate.behavioral_signals.recruiter_response_rate * 100)}%</p>
//                                 </div>
//                               </div>
//                             </div>
//                           </div>

//                           {/* WORK EXPERIENCE TIMELINE */}
//                           <div className="space-y-3 pt-3 border-t border-slate-100">
//                             <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center">
//                               <Briefcase className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> Career Milestones History
//                             </h4>
//                             <div className="relative border-l-2 border-slate-100 pl-4 ml-2.5 space-y-4">
//                               {selectedCandidate.career_history.map((job, idx) => (
//                                 <div key={idx} className="relative">
//                                   <div className="absolute -left-[21.5px] top-1 w-2.5 h-2.5 rounded-full bg-indigo-600 border-2 border-white shadow-sm"></div>
//                                   <div className="space-y-1">
//                                     <div className="flex justify-between items-start text-xs">
//                                       <h5 className="font-bold text-slate-900">{job.title}</h5>
//                                       <span className="text-[10px] text-indigo-600 font-bold font-mono">{job.company}</span>
//                                     </div>
//                                     <p className="text-xs text-slate-500 leading-relaxed font-medium">{job.description}</p>
//                                   </div>
//                                 </div>
//                               ))}
//                             </div>
//                           </div>

//                           {/* CORE CANDIDATE VECTORS */}
//                           <div className="grid grid-cols-2 gap-4 border-t border-slate-100 pt-4 text-xs font-medium text-slate-500">
//                             <div className="flex items-start space-x-2">
//                               <GraduationCap className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
//                               <div>
//                                 <p className="text-slate-400 text-[9px] font-bold uppercase">Academic Background</p>
//                                 <p className="text-slate-700 font-semibold mt-0.5">{selectedCandidate.education}</p>
//                               </div>
//                             </div>
//                             <div className="flex items-start space-x-2">
//                               <User className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
//                               <div>
//                                 <p className="text-slate-400 text-[9px] font-bold uppercase">Experience Seniority</p>
//                                 <p className="text-slate-700 font-semibold mt-0.5">{selectedCandidate.experience_years} Years Active Industry Service</p>
//                               </div>
//                             </div>
//                           </div>

//                         </div>
//                       </div>
//                     ) : (
//                       <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-400">
//                         <User className="w-8 h-8 text-slate-300 animate-pulse mb-2" />
//                         <p className="text-xs font-bold">Select a candidate to view resume detail inspection</p>
//                       </div>
//                     )}
//                   </div>

//                 </div>
//               )}

//             </div>
//           ) : (
//             <div className="flex-1 bg-white border border-slate-200 rounded-3xl p-10 flex flex-col items-center justify-center text-center space-y-4 shadow-sm" id="empty-panel">
//               <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl border border-indigo-100">
//                 <Search className="w-8 h-8" />
//               </div>
//               <div className="space-y-1.5">
//                 <h3 className="font-display font-bold text-slate-800 text-lg">No Active Pipeline Rank Results</h3>
//                 <p className="text-slate-500 text-xs max-w-sm mx-auto leading-relaxed font-medium">
//                   Select or input a job criteria matrix on the left panel, configure scoring variables, and run matching to score 100,000 resume records.
//                 </p>
//               </div>
//             </div>
//           )}
//         </section>

//       </main>

//       {/* FLOATING ACTION SHEET FOR CANDIDATE COMPARISON */}
//       {compareIds.length > 0 && (
//         <div className="fixed bottom-5 left-1/2 -translate-x-1/2 bg-[#0f172a] text-white py-3 px-6 rounded-2xl border border-slate-800 shadow-2xl flex items-center justify-between gap-6 z-50 animate-slideUp max-w-lg w-[calc(100%-2rem)]">
//           <div className="flex items-center space-x-3">
//             <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-xs">
//               {compareIds.length}
//             </div>
//             <div>
//               <p className="text-xs font-bold text-white">Candidates selected for comparison</p>
//               <p className="text-[10px] text-slate-400">Select up to 3 candidates for deep review</p>
//             </div>
//           </div>
//           <div className="flex items-center space-x-2">
//             <button
//               onClick={() => setCompareMode(true)}
//               className="bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold px-3.5 py-2 rounded-xl transition flex items-center space-x-1.5 cursor-pointer shadow-sm shadow-indigo-600/25"
//             >
//               <ArrowLeftRight className="w-3.5 h-3.5" />
//               <span>Compare Now</span>
//             </button>
//             <button
//               onClick={() => setCompareIds([])}
//               className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-bold px-3.5 py-2 rounded-xl border border-slate-700 transition cursor-pointer"
//             >
//               Clear
//             </button>
//           </div>
//         </div>
//       )}

//       {/* REAL RESUME PDF UPLOAD MODAL */}
//       <ResumeUploadModal
//         isOpen={showUploadModal}
//         onClose={() => setShowUploadModal(false)}
//         onUploadSuccess={() => {
//           fetchStatus();
//         }}
//       />

//     </div>
//   );
// }

import { useState, useEffect } from "react";
import { 
  Sparkles, 
  Sliders, 
  Search, 
  Download, 
  Cpu, 
  AlertCircle, 
  User, 
  Briefcase, 
  GraduationCap, 
  GitCommit, 
  Star, 
  MessageSquare, 
  Zap,
  Info,
  Layers,
  RefreshCw,
  Check,
  X,
  ArrowLeftRight,
  HelpCircle,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  Database,
  Upload
} from "lucide-react";
import { Candidate, PipelineResults } from "./types.ts";
import { ResumeUploadModal } from "./components/ResumeUploadModal.tsx";

const DEFAULT_JOB_DESCRIPTION = `We are seeking a Senior Machine Learning Platform Engineer to design, build, and optimize high-throughput distributed LLM retrieval systems (RAG).

Required Skills:
- PyTorch, Python, and Transformers
- Vector Databases (Pinecone, Milvus, Qdrant)
- Docker, Kubernetes, and Ray

Preferred Skills:
- Experience with MLOps pipelines (MLflow, Kubeflow)
- Deep learning performance optimization (TensorRT, vLLM)
- Strong contributions to open-source ML frameworks

Experience Required:
- 5+ years of industry experience working with production-grade ML infrastructure.`;

const PRESETS = [
  {
    name: "Senior ML Platform",
    desc: DEFAULT_JOB_DESCRIPTION,
    weights: { semantic: 45, skills: 35, career: 12, behavioral: 8 }
  },
  {
    name: "Staff Frontend Architect",
    desc: `We are looking for a Staff Frontend Architect specialized in React, Vite, and high-performance WebApps.

Required Skills:
- React, TypeScript, and state management (Zustand, Redux)
- CSS frameworks (Tailwind CSS, CSS modules)
- Build tooling optimization (Vite, Rollup, ESBuild)

Experience Required:
- 6+ years designing accessible, fluid, and scalable UI architectures.`,
    weights: { semantic: 30, skills: 50, career: 10, behavioral: 10 }
  },
  {
    name: "Lead Backend Developer",
    desc: `Seeking a Backend Technical Lead to architect performant microservices and ML inference endpoints.

Required Skills:
- Python, FastAPI, Asyncio, and Uvicorn
- SQL & NoSQL (PostgreSQL, Redis, Elasticsearch)
- System design, API security, OAuth, and Docker

Experience Required:
- 5+ years of designing distributed Python servers at high scale.`,
    weights: { semantic: 40, skills: 30, career: 20, behavioral: 10 }
  }
];

export default function App() {
  const [jobDescription, setJobDescription] = useState(DEFAULT_JOB_DESCRIPTION);
  const [topKRetrieval, setTopKRetrieval] = useState(2000);
  const [useGeminiEmbedding, setUseGeminiEmbedding] = useState(false);
  
  const [weights, setWeights] = useState({
    semantic: 50,
    skills: 25,
    career: 15,
    behavioral: 10
  });

  const [systemStatus, setSystemStatus] = useState({
    success: false,
    poolSize: 100000,
    isPoolGenerated: false,
    modelStatus: "loading",
    faissStatus: "idle",
    envHasApiKey: false,
    database: {
      connected: false,
      engine: "PostgreSQL",
      pgvector: "Initializing"
    }
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<PipelineResults | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [aiExplanations, setAiExplanations] = useState<Record<string, string>>({});
  const [explainingId, setExplainingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollingStatus, setPollingStatus] = useState(false);

  // New recruiter visual helpers
  const [searchTerm, setSearchTerm] = useState("");
  const [minExperience, setMinExperience] = useState(0);
  const [selectedTier, setSelectedTier] = useState<string>("All");
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareMode, setCompareMode] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);

  const handleWeightChange = (key: keyof typeof weights, value: number) => {
    const diff = value - weights[key];
    const otherKeys = (Object.keys(weights) as Array<keyof typeof weights>).filter(k => k !== key);
    const otherSum = otherKeys.reduce((sum, k) => sum + weights[k], 0);
    const newWeights = { ...weights };
    newWeights[key] = value;

    if (otherSum > 0) {
      otherKeys.forEach(k => {
        const share = weights[k] / otherSum;
        const subVal = Math.round(weights[k] - diff * share);
        newWeights[k] = Math.max(0, Math.min(100, subVal));
      });
    } else {
      otherKeys.forEach(k => {
        newWeights[k] = Math.max(0, Math.round((100 - value) / 3));
      });
    }

    const currentSum = Object.values(newWeights).reduce((a, b) => a + b, 0);
    if (currentSum !== 100) {
      const adjustment = 100 - currentSum;
      newWeights[otherKeys[0]] = Math.max(0, newWeights[otherKeys[0]] + adjustment);
    }
    setWeights(newWeights);
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/status");
      const contentType = res.headers.get("content-type");
      if (res.ok && contentType && contentType.includes("application/json")) {
        const data = await res.json();
        setSystemStatus({
          success: data.success,
          poolSize: data.poolSize,
          isPoolGenerated: data.isPoolGenerated,
          modelStatus: data.modelStatus,
          faissStatus: data.faissStatus,
          envHasApiKey: data.envHasApiKey,
          database: data.database || {
            connected: false,
            engine: "PostgreSQL",
            pgvector: "Unknown"
          }
        });
        setPollingStatus(data.faissStatus.includes("indexing"));
      }
    } catch (err) {
      console.error("Error fetching system status:", err);
    }
  };

  const initModel = async () => {
    try {
      await fetch("/api/init-model", { method: "POST" });
      fetchStatus();
    } catch (err) {
      console.error("Error warming model:", err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, pollingStatus ? 2000 : 8000);
    return () => clearInterval(interval);
  }, [pollingStatus]);

  const handleRank = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/rank", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jobDescriptionText: jobDescription,
          topKRetrieval,
          useGeminiEmbedding,
          weights: {
            semantic: weights.semantic / 100,
            skills: weights.skills / 100,
            career: weights.career / 100,
            behavioral: weights.behavioral / 100
          }
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to match resumes.");
      }

      const payload = await res.json();
      if (payload.success) {
        setResults(payload.data);
        if (payload.data.topCandidates && payload.data.topCandidates.length > 0) {
          setSelectedCandidate(payload.data.topCandidates[0]);
        }
        setCompareIds([]);
        setCompareMode(false);
      } else {
        throw new Error("Pipeline returned failure status.");
      }
    } catch (err: any) {
      setError(err.message || "An unexpected pipeline error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async (candidate: Candidate) => {
    if (!candidate) return;
    setExplainingId(candidate.candidate_id);
    try {
      const res = await fetch("/api/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate, jobDescriptionText: jobDescription })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          setAiExplanations(prev => ({ ...prev, [candidate.candidate_id]: data.reasoning }));
          if (selectedCandidate?.candidate_id === candidate.candidate_id) {
            setSelectedCandidate(prev => prev ? { ...prev, reasoning: data.reasoning } : null);
          }
        }
      }
    } catch (err) {
      console.error("AI deep review failed:", err);
    } finally {
      setExplainingId(null);
    }
  };

  const handleExportCSV = async () => {
    if (!results?.topCandidates) return;
    try {
      const res = await fetch("/api/export-csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidates: results.topCandidates })
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "matched_talent_export.csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error("Export failed:", err);
    }
  };

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setJobDescription(preset.desc);
    setWeights(preset.weights);
  };

  // Compute matched skills and missing skills
  const getSkillsBreakdown = (candidate: Candidate) => {
    if (!results?.parsedFeatures) return { matched: candidate.skills, missing: [], additional: [] };
    
    const required = results.parsedFeatures.requiredSkills.map(s => s.toLowerCase());
    const preferred = results.parsedFeatures.preferredSkills.map(s => s.toLowerCase());
    const allReq = [...required, ...preferred];
    
    const candSkillsLower = candidate.skills.map(s => s.toLowerCase());
    
    const matched = candidate.skills.filter(s => allReq.includes(s.toLowerCase()));
    const additional = candidate.skills.filter(s => !allReq.includes(s.toLowerCase()));
    
    // Find missing requested skills
    const missing = results.parsedFeatures.requiredSkills.filter(s => !candSkillsLower.includes(s.toLowerCase()));

    return { matched, missing, additional };
  };

  const filteredCandidates = results ? results.topCandidates.filter(c => {
    const term = searchTerm.toLowerCase();
    const matchesSearch = c.name.toLowerCase().includes(term) ||
                          c.headline.toLowerCase().includes(term) ||
                          c.skills.some(s => s.toLowerCase().includes(term));
    const matchesExp = c.experience_years >= minExperience;
    
    let matchesTier = true;
    if (selectedTier !== "All") {
      const score = c.scores.finalScore || 0;
      if (selectedTier === "Excellent") matchesTier = score >= 90;
      else if (selectedTier === "High") matchesTier = score >= 75 && score < 90;
      else if (selectedTier === "Good") matchesTier = score >= 60 && score < 75;
      else if (selectedTier === "General") matchesTier = score < 60;
    }
    
    return matchesSearch && matchesExp && matchesTier;
  }) : [];

  const toggleCompare = (id: string) => {
    if (compareIds.includes(id)) {
      setCompareIds(compareIds.filter(x => x !== id));
    } else {
      if (compareIds.length >= 3) return; // limit to 3 for clean side-by-side
      setCompareIds([...compareIds, id]);
    }
  };

  const getTierBadgeClass = (score: number) => {
    if (score >= 90) return "bg-emerald-50 text-emerald-700 border-emerald-200";
    if (score >= 75) return "bg-indigo-50 text-indigo-700 border-indigo-200";
    if (score >= 60) return "bg-sky-50 text-sky-700 border-sky-200";
    return "bg-slate-50 text-slate-700 border-slate-200";
  };

  const getTierName = (score: number) => {
    if (score >= 90) return "A+ Outstanding";
    if (score >= 75) return "A Strategic Match";
    if (score >= 60) return "B Core Match";
    return "C General Match";
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex flex-col font-sans antialiased" id="auratalent-root">
      
      {/* ENTERPRISE APP NAVBAR */}
      <header className="border-b border-slate-200 bg-white shadow-sm sticky top-0 z-40 px-6 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-4" id="header">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 bg-indigo-600 rounded-xl shadow-md shadow-indigo-600/10 text-white flex items-center justify-center">
            <Sparkles className="w-5.5 h-5.5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold text-slate-900 tracking-tight font-display">AuraTalent AI</span>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 bg-indigo-50 text-indigo-600 border border-indigo-100 rounded-full">v2.4 Hybrid Matcher</span>
            </div>
            <p className="text-xs text-slate-500 font-medium">Enterprise Candidate Dual-Stage Scoring Hub &bull; 100,000 Pool</p>
          </div>
        </div>

        {/* System Stats Indicators */}
        <div className="flex flex-wrap items-center gap-3 text-xs" id="system-status-indicator">
          
          <button 
            onClick={() => setShowHowItWorks(!showHowItWorks)}
            className="flex items-center space-x-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 px-3 py-1.5 rounded-lg border border-slate-200 transition font-medium"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>How it Works</span>
          </button>

          {/* Model status */}
          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-lg">
            <Cpu className="w-3.5 h-3.5 text-indigo-500" />
            <span className="text-slate-500 font-medium">Model:</span>
            {systemStatus.modelStatus.includes("loaded") ? (
              <span className="text-emerald-600 font-bold flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse"></span>Active</span>
            ) : systemStatus.modelStatus === "loading" ? (
              <span className="text-amber-600 font-medium flex items-center animate-pulse"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Warming...</span>
            ) : (
              <button onClick={initModel} className="text-rose-500 hover:underline font-bold">Initialize</button>
            )}
          </div>

          {/* Database active count */}
          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-lg">
            <Database className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-slate-500 font-medium">Postgres:</span>
            {systemStatus.database?.connected ? (
              <span className="text-emerald-600 font-bold flex items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse"></span>
                pgvector
              </span>
            ) : (
              <span className="text-amber-600 font-medium">Connecting...</span>
            )}
          </div>

          {/* Candidate Index pool */}
          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-lg">
            <Layers className="w-3.5 h-3.5 text-purple-500" />
            <span className="text-slate-500 font-medium">Pool:</span>
            {systemStatus.faissStatus.includes("loaded") || systemStatus.isPoolGenerated ? (
              <span className="text-emerald-600 font-bold">100K Profiles</span>
            ) : systemStatus.faissStatus.includes("indexing") ? (
              <span className="text-amber-600 font-medium flex items-center animate-pulse"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Indexing...</span>
            ) : (
              <span className="text-slate-400">Loading Pool...</span>
            )}
          </div>

          {/* API Key Status */}
          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-lg">
            <Zap className={`w-3.5 h-3.5 ${systemStatus.envHasApiKey ? 'text-amber-500' : 'text-slate-400'}`} />
            <span className="text-slate-500 font-medium">Gemini:</span>
            {systemStatus.envHasApiKey ? (
              <span className="text-emerald-600 font-bold">Linked</span>
            ) : (
              <span className="text-slate-400 font-medium">Heuristics</span>
            )}
          </div>

          {/* Ingest Real PDF Resumes Button */}
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg shadow-sm hover:shadow transition-all"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Ingest Resumes (PDF)</span>
          </button>
        </div>
      </header>


      {/* HOW IT WORKS DIAGRAM OVERLAY */}
      {showHowItWorks && (
        <div className="bg-indigo-900 text-white p-5 px-6 border-b border-indigo-950 flex flex-col md:flex-row items-center justify-between gap-6 animate-fadeIn">
          <div className="space-y-2 max-w-3xl">
            <h3 className="font-display font-semibold text-base flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-indigo-300" /> High-Performance Recruiting Pipeline Architecture
            </h3>
            <p className="text-xs text-indigo-100 leading-relaxed">
              Recruiting software often buckles when matching hundreds of thousands of files. AuraTalent AI solves this by utilizing a <strong>Two-Stage Matching Architecture</strong>:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="bg-indigo-950/40 p-3 rounded-lg border border-indigo-800">
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300">Stage 1: Vector Search</span>
                <p className="text-[11px] text-indigo-100 mt-1 leading-normal">
                  FAISS index screens the complete pool of 100,000 resume texts to immediately extract top candidates using sentence-transformers.
                </p>
              </div>
              <div className="bg-indigo-950/40 p-3 rounded-lg border border-indigo-800">
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300">Stage 2: Hybrid Scoring</span>
                <p className="text-[11px] text-indigo-100 mt-1 leading-normal">
                  Weights combine multi-dimensional scores: semantic alignment, required skill overlap, career tenure velocity, and behavioral commitment.
                </p>
              </div>
              <div className="bg-indigo-950/40 p-3 rounded-lg border border-indigo-800">
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300">Stage 3: Generative AI Gap Analysis</span>
                <p className="text-[11px] text-indigo-100 mt-1 leading-normal">
                  Gemini inspects the best fits, pinpointing exact career progress matches, highlighting key matching indicators, and detailing potential risks.
                </p>
              </div>
            </div>
          </div>
          <button 
            onClick={() => setShowHowItWorks(false)}
            className="bg-indigo-800 hover:bg-indigo-750 text-white border border-indigo-700 text-xs px-3.5 py-1.5 rounded-lg font-medium self-start sm:self-center shrink-0"
          >
            Got it, Hide Panel
          </button>
        </div>
      )}

      {/* DASHBOARD CONTAINER */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-4 lg:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 overflow-hidden" id="dashboard-main">
        
        {/* LEFT COLUMN: CRITERIA & CONFIG (35% width) */}
        <section className="lg:col-span-4 flex flex-col space-y-6 overflow-y-auto pr-1" id="criteria-config-section">
          
          {/* CRITERIA SECTION */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-sm font-semibold text-slate-800 flex items-center">
                <Briefcase className="w-4.5 h-4.5 mr-2 text-indigo-600" /> Target Position Details
              </h2>
              <span className="text-[11px] text-slate-400 font-medium">Quick Presets</span>
            </div>

            {/* Quick Presets Select Buttons */}
            <div className="grid grid-cols-3 gap-2">
              {PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => applyPreset(p)}
                  className="text-[11px] font-semibold bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 text-slate-600 px-2 py-1.5 rounded-lg border border-slate-200 transition text-center truncate"
                  title={p.name}
                >
                  {p.name.replace("Senior ", "").replace("Staff ", "").replace("Lead ", "")}
                </button>
              ))}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Requirements Text</label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the target job description or detailed technical requirements list here..."
                className="w-full h-44 bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500/25 focus:bg-white resize-none transition"
              />
            </div>
          </div>

          {/* DUAL-STAGE WEIGHTS AND PARAMS */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-5">
            <div className="flex justify-between items-center">
              <h2 className="text-sm font-semibold text-slate-800 flex items-center">
                <Sliders className="w-4.5 h-4.5 mr-2 text-indigo-600" /> Scoring Param Matrix
              </h2>
              <span className="text-xs font-mono font-bold text-indigo-600 px-2.5 py-0.5 bg-indigo-50 rounded-full">Sum: 100%</span>
            </div>
            
            <p className="text-xs text-slate-500 leading-normal">
              Fine-tune match emphasis. The system recalculates scores instantly using the adjusted weights.
            </p>

            <div className="space-y-4 pt-1">
              {/* Semantic Weight */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700 flex items-center">
                    Semantic Matching Alignment
                    <span title="Measures deeper context alignment using text sentence-transformer embeddings." className="ml-1 text-slate-400 hover:text-indigo-600 cursor-help"><Info className="w-3.5 h-3.5" /></span>
                  </span>
                  <span className="font-mono text-indigo-600 font-bold">{weights.semantic}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={weights.semantic}
                  onChange={(e) => handleWeightChange("semantic", parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                />
              </div>

              {/* Skills Weight */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700 flex items-center">
                    Technical Skill Matrix Overlap
                    <span title="Explicit validation against required/preferred skills parsed from requirement text." className="ml-1 text-slate-400 hover:text-indigo-600 cursor-help"><Info className="w-3.5 h-3.5" /></span>
                  </span>
                  <span className="font-mono text-indigo-600 font-bold">{weights.skills}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={weights.skills}
                  onChange={(e) => handleWeightChange("skills", parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                />
              </div>

              {/* Career Tenure Weight */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700 flex items-center">
                    Career Tenure & Stability
                    <span title="Scored by total professional history duration, retention cycles, and rank progression speed." className="ml-1 text-slate-400 hover:text-indigo-600 cursor-help"><Info className="w-3.5 h-3.5" /></span>
                  </span>
                  <span className="font-mono text-indigo-600 font-bold">{weights.career}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={weights.career}
                  onChange={(e) => handleWeightChange("career", parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                />
              </div>

              {/* Behavioral Weight */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700 flex items-center">
                    Open Source & Engagement Rates
                    <span title="Calculated from public GitHub stars, commits, and recruiter message response velocities." className="ml-1 text-slate-400 hover:text-indigo-600 cursor-help"><Info className="w-3.5 h-3.5" /></span>
                  </span>
                  <span className="font-mono text-indigo-600 font-bold">{weights.behavioral}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={weights.behavioral}
                  onChange={(e) => handleWeightChange("behavioral", parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                />
              </div>
            </div>

            {/* PIPELINE OPTIONS */}
            <div className="border-t border-slate-100 pt-4 space-y-3.5">
              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">Stage 1 Filter K</label>
                  <select
                    value={topKRetrieval}
                    onChange={(e) => setTopKRetrieval(parseInt(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-700 py-2 px-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition font-medium"
                  >
                    <option value="500">500 candidates</option>
                    <option value="1000">1,000 candidates</option>
                    <option value="2000">2,000 candidates</option>
                    <option value="5000">5,000 candidates</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">Embedder Model</label>
                  <div className="flex items-center space-x-1 bg-slate-50 border border-slate-200 p-0.5 rounded-xl">
                    <button
                      type="button"
                      onClick={() => setUseGeminiEmbedding(false)}
                      className={`flex-1 py-1.5 px-2 rounded-lg text-[10px] font-bold transition ${!useGeminiEmbedding ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                    >
                      MiniLM
                    </button>
                    <button
                      type="button"
                      disabled={!systemStatus.envHasApiKey}
                      onClick={() => setUseGeminiEmbedding(true)}
                      className={`flex-1 py-1.5 px-2 rounded-lg text-[10px] font-bold transition disabled:opacity-40 disabled:cursor-not-allowed ${useGeminiEmbedding ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                      title={!systemStatus.envHasApiKey ? "Requires GEMINI_API_KEY environment variable" : "Use Google Cloud text-embedding-004"}
                    >
                      Gemini
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* MATCH ACTION BAR */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleRank}
                disabled={loading || (!systemStatus.modelStatus.includes("loaded") && !useGeminiEmbedding)}
                className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-100 disabled:text-slate-400 disabled:border-slate-100 text-white font-bold py-3 px-4 rounded-xl text-xs flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/15 border border-indigo-500/20 transition cursor-pointer"
                id="rank-button"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-white" />
                    <span>Executing Dual-Stage Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 text-white" />
                    <span>Compile & Evaluate 100,000 Resumes</span>
                  </>
                )}
              </button>
            </div>

            {error && (
              <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3.5 rounded-xl text-xs flex items-start space-x-2.5">
                <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                <span className="font-medium">{error}</span>
              </div>
            )}
          </div>
        </section>

        {/* RIGHT COLUMN: RESULTS & DEEP INSPECT SPLIT (65% width) */}
        <section className="lg:col-span-8 flex flex-col space-y-6 overflow-hidden" id="results-section">
          {loading ? (
            <div className="flex-1 bg-white border border-slate-200 rounded-3xl p-8 flex flex-col items-center justify-center text-center space-y-6 shadow-sm" id="loading-panel">
              <div className="relative">
                <div className="absolute inset-0 bg-indigo-500/10 rounded-full animate-ping border border-indigo-500/20"></div>
                <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center relative z-10">
                  <Cpu className="w-8 h-8 text-indigo-600 animate-pulse" />
                </div>
              </div>
              <div className="space-y-2">
                <h3 className="font-display font-bold text-lg text-slate-800">Pruning & High-Fidelity Scoring Candidate Pool</h3>
                <p className="text-slate-500 text-xs max-w-sm mx-auto leading-relaxed font-medium">
                  Stage 1 is executing fast-index vector scanning on 100,000 resume files. Stage 2 will then apply multi-dimensional scoring weights on the top {topKRetrieval} results.
                </p>
              </div>
              <div className="w-64 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-600 rounded-full animate-loading-bar w-2/3"></div>
              </div>
            </div>
          ) : results ? (
            <div className="flex-1 flex flex-col space-y-6 overflow-hidden" id="results-active-panel">
              
              {/* TELEMETRY BAR & DYNAMIC MATRIX COMPACT DECK */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-4 shrink-0" id="telemetry-grid">
                
                {/* Processing Telemetry */}
                <div className="md:col-span-6 bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col justify-between space-y-3">
                  <div className="flex justify-between items-center">
                    <h3 className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider flex items-center font-display">
                      <Cpu className="w-3.5 h-3.5 mr-1.5" /> Match Telemetry Analytics
                    </h3>
                    <span className="text-[10px] font-mono font-bold text-slate-400">FAISS Powered</span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2.5">
                    <div className="bg-slate-50/70 p-2 rounded-xl border border-slate-100 text-center">
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide">Stage 1 Seek</p>
                      <p className="text-sm font-mono font-bold text-slate-800 mt-0.5">{results.telemetry.stage1TimeMs}ms</p>
                    </div>
                    <div className="bg-slate-50/70 p-2 rounded-xl border border-slate-100 text-center">
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide">Stage 2 Score</p>
                      <p className="text-sm font-mono font-bold text-slate-800 mt-0.5">{results.telemetry.stage2TimeMs}ms</p>
                    </div>
                    <div className="bg-indigo-50/40 p-2 rounded-xl border border-indigo-100 text-center">
                      <p className="text-[9px] text-indigo-500 font-bold uppercase tracking-wide">Total Time</p>
                      <p className="text-sm font-mono font-bold text-indigo-600 mt-0.5">{results.telemetry.totalTimeMs}ms</p>
                    </div>
                  </div>
                  
                  <div className="flex justify-between text-[10px] text-slate-500 font-medium font-mono border-t border-slate-100 pt-1.5">
                    <span>Pool: {results.telemetry.totalCandidates.toLocaleString()} files</span>
                    <span>Model: {results.telemetry.modelUsed}</span>
                  </div>
                </div>

                {/* Extracted requirement matrices */}
                <div className="md:col-span-6 bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col justify-between space-y-2">
                  <h3 className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider flex items-center font-display">
                    <Sliders className="w-3.5 h-3.5 mr-1.5" /> Parsed Requirements Matrix
                  </h3>
                  
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center text-slate-600">
                      <span className="text-slate-400 font-bold w-20">Exp Required:</span>
                      <span className="font-bold text-slate-800 font-mono">{results.parsedFeatures.experienceYearsRequired}+ Years Professional</span>
                    </div>
                    <div className="flex items-center text-slate-600">
                      <span className="text-slate-400 font-bold w-20">Req Skills:</span>
                      <div className="flex flex-wrap gap-1 max-h-12 overflow-y-auto">
                        {results.parsedFeatures.requiredSkills.slice(0, 3).map((s, idx) => (
                          <span key={idx} className="bg-slate-100 text-slate-700 text-[9px] px-1.5 py-0.5 rounded-md font-bold border border-slate-200">{s}</span>
                        ))}
                        {results.parsedFeatures.requiredSkills.length > 3 && (
                          <span className="text-[9px] text-slate-400 font-mono">+{results.parsedFeatures.requiredSkills.length - 3} more</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center text-slate-600">
                      <span className="text-slate-400 font-bold w-20">Key Vectors:</span>
                      <div className="flex flex-wrap gap-1 max-h-12 overflow-y-auto">
                        {results.parsedFeatures.domainKeywords.slice(0, 3).map((s, idx) => (
                          <span key={idx} className="bg-indigo-50 text-indigo-600 text-[9px] px-1.5 py-0.5 rounded-md font-bold border border-indigo-100">{s}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* CANDIDATES GRID & PROFILE SPLIT PANEL OR SIDE-BY-SIDE COMPARISON VIEW */}
              {compareMode ? (
                /* COMPARATOR MODULE */
                <div className="flex-1 bg-white border border-slate-200 rounded-2xl flex flex-col overflow-hidden animate-fadeIn">
                  <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex justify-between items-center">
                    <div>
                      <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2 font-display">
                        <ArrowLeftRight className="w-4.5 h-4.5 text-indigo-600" /> Executive Talent Comparison Grid
                      </h3>
                      <p className="text-xs text-slate-500">Side-by-side performance, skill overlaps, and professional tenure metrics</p>
                    </div>
                    <button
                      onClick={() => setCompareMode(false)}
                      className="bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Close Comparison</span>
                    </button>
                  </div>

                  <div className="flex-1 overflow-x-auto p-4 lg:p-6">
                    <div className="flex gap-6 min-w-[700px] h-full items-start">
                      {results.topCandidates
                        .filter(c => compareIds.includes(c.candidate_id))
                        .map(c => {
                          const { matched, missing } = getSkillsBreakdown(c);
                          return (
                            <div key={c.candidate_id} className="flex-1 bg-slate-50/50 border border-slate-200 rounded-2xl p-5 flex flex-col h-full overflow-y-auto space-y-5">
                              
                              {/* Header Card */}
                              <div className="space-y-2 border-b border-slate-200 pb-3">
                                <div className="flex justify-between items-start">
                                  <div className="w-10 h-10 rounded-full bg-indigo-600 text-white font-bold text-sm flex items-center justify-center shadow-sm">
                                    {c.name.split(" ").map(n => n[0]).join("")}
                                  </div>
                                  <div className="text-right">
                                    <span className="font-mono text-sm font-bold text-indigo-600 bg-white border border-slate-200 px-2.5 py-1 rounded-full shadow-sm">
                                      {c.scores.finalScore}%
                                    </span>
                                    <p className="text-[9px] text-slate-400 font-bold uppercase mt-1">Match Index</p>
                                  </div>
                                </div>
                                <h4 className="font-bold text-slate-900 text-sm">{c.name}</h4>
                                <p className="text-xs text-indigo-600 font-semibold">{c.headline}</p>
                                <span className={`inline-block border text-[10px] font-bold px-2 py-0.5 rounded-md mt-1 ${getTierBadgeClass(c.scores.finalScore || 0)}`}>
                                  {getTierName(c.scores.finalScore || 0)}
                                </span>
                              </div>

                              {/* Core metrics comparison */}
                              <div className="space-y-3.5">
                                <h5 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Metrics Matrix</h5>
                                
                                <div className="space-y-2">
                                  <div className="flex justify-between text-xs">
                                    <span className="text-slate-500">Exp Years</span>
                                    <span className="font-bold text-slate-800">{c.experience_years} Years</span>
                                  </div>
                                  <div className="flex justify-between text-xs">
                                    <span className="text-slate-500">Education</span>
                                    <span className="font-semibold text-slate-800 text-right truncate max-w-[150px]" title={c.education}>{c.education.split(",")[0]}</span>
                                  </div>
                                </div>

                                <div className="space-y-2 pt-2 border-t border-slate-200/60">
                                  {/* Semantic Progress */}
                                  <div>
                                    <div className="flex justify-between text-[11px] mb-1">
                                      <span className="text-slate-500">Semantic Alignment</span>
                                      <span className="font-mono font-bold text-slate-700">{c.scores.semanticScore}%</span>
                                    </div>
                                    <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${c.scores.semanticScore}%` }}></div>
                                    </div>
                                  </div>

                                  {/* Skill Progress */}
                                  <div>
                                    <div className="flex justify-between text-[11px] mb-1">
                                      <span className="text-slate-500">Skill Alignment</span>
                                      <span className="font-mono font-bold text-slate-700">{c.scores.skillScore}%</span>
                                    </div>
                                    <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${c.scores.skillScore}%` }}></div>
                                    </div>
                                  </div>

                                  {/* Stability */}
                                  <div>
                                    <div className="flex justify-between text-[11px] mb-1">
                                      <span className="text-slate-500">Tenure Velocity</span>
                                      <span className="font-mono font-bold text-slate-700">{c.scores.careerScore}%</span>
                                    </div>
                                    <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                      <div className="h-full bg-rose-500 rounded-full" style={{ width: `${c.scores.careerScore}%` }}></div>
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Skills match overlaps */}
                              <div className="space-y-2 pt-3 border-t border-slate-200/60">
                                <h5 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Required overlaps ({matched.length})</h5>
                                <div className="flex flex-wrap gap-1">
                                  {matched.map((s, idx) => (
                                    <span key={idx} className="bg-emerald-50 text-emerald-700 text-[10px] px-2 py-0.5 rounded-md font-bold border border-emerald-100">{s}</span>
                                  ))}
                                  {missing.map((s, idx) => (
                                    <span key={idx} className="bg-slate-100 text-slate-400 line-through text-[10px] px-2 py-0.5 rounded-md border border-slate-200">{s}</span>
                                  ))}
                                </div>
                              </div>

                              {/* GitHub metrics comparison */}
                              <div className="space-y-3 pt-3 border-t border-slate-200/60">
                                <h5 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Public Engagement</h5>
                                <div className="grid grid-cols-2 gap-2 text-center">
                                  <div className="bg-white p-2 border border-slate-200 rounded-xl">
                                    <p className="text-[9px] text-slate-400 font-bold uppercase">GitHub Stars</p>
                                    <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{c.behavioral_signals.github_stars}</p>
                                  </div>
                                  <div className="bg-white p-2 border border-slate-200 rounded-xl">
                                    <p className="text-[9px] text-slate-400 font-bold uppercase">Response Rate</p>
                                    <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{Math.round(c.behavioral_signals.recruiter_response_rate * 100)}%</p>
                                  </div>
                                </div>
                              </div>

                              {/* AI Explanation / Summary block */}
                              <div className="pt-3 border-t border-slate-200/60 space-y-1">
                                <h5 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Evaluation Analysis</h5>
                                <p className="text-xs text-slate-600 italic leading-relaxed">
                                  "{aiExplanations[c.candidate_id] || c.reasoning || "No deep review executed."}"
                                </p>
                              </div>

                            </div>
                          );
                        })}
                    </div>
                  </div>
                </div>
              ) : (
                /* TWO-COLUMN EXPANDED SEARCH & DETAIL SPLIT MODULE */
                <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-6 overflow-hidden" id="results-split-panel">
                  
                  {/* LEFT: CANDIDATE SELECTABLE SCROLL LIST (Top 100) */}
                  <div className="md:col-span-5 bg-white border border-slate-200 rounded-2xl flex flex-col overflow-hidden shadow-sm" id="candidates-column">
                    
                    {/* Header search tools */}
                    <div className="p-4 border-b border-slate-200 bg-slate-50/50 space-y-3 shrink-0">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-bold text-slate-800 text-sm font-display">Ranked Matches</h3>
                          <p className="text-[10px] text-slate-400">FAISS filtered stage 1 & 2 matches</p>
                        </div>
                        <button
                          onClick={handleExportCSV}
                          className="bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 px-2.5 py-1.5 rounded-xl text-xs font-bold flex items-center space-x-1 cursor-pointer transition shadow-sm"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>CSV</span>
                        </button>
                      </div>

                      {/* Dynamic filter bar inside list */}
                      <div className="space-y-2">
                        <div className="relative">
                          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                          <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Filter by name, skill, title..."
                            className="w-full bg-white border border-slate-200 text-xs rounded-xl pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/25 transition"
                          />
                        </div>

                        {/* Experience and Tier Filters */}
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <select
                              value={selectedTier}
                              onChange={(e) => setSelectedTier(e.target.value)}
                              className="w-full bg-white border border-slate-200 text-[11px] rounded-lg py-1 px-1.5 focus:outline-none font-semibold text-slate-600"
                            >
                              <option value="All">All Score Tiers</option>
                              <option value="Excellent">Excellent (90%+)</option>
                              <option value="High">High (75%-90%)</option>
                              <option value="Good">Good (60%-75%)</option>
                              <option value="General">General (&lt;60%)</option>
                            </select>
                          </div>
                          <div>
                            <select
                              value={minExperience}
                              onChange={(e) => setMinExperience(parseInt(e.target.value))}
                              className="w-full bg-white border border-slate-200 text-[11px] rounded-lg py-1 px-1.5 focus:outline-none font-semibold text-slate-600"
                            >
                              <option value="0">Min Exp: Any</option>
                              <option value="3">Min Exp: 3+ Yrs</option>
                              <option value="5">Min Exp: 5+ Yrs</option>
                              <option value="8">Min Exp: 8+ Yrs</option>
                              <option value="10">Min Exp: 10+ Yrs</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Candidates scroll container */}
                    <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-slate-50/30" id="candidates-list-scroll">
                      {filteredCandidates.length > 0 ? (
                        filteredCandidates.map((c) => {
                          const isSelected = selectedCandidate?.candidate_id === c.candidate_id;
                          const isCompareChecked = compareIds.includes(c.candidate_id);
                          return (
                            <div
                              key={c.candidate_id}
                              className={`p-3 rounded-xl border transition-all duration-150 relative flex flex-col gap-2 ${
                                isSelected 
                                  ? "bg-white border-indigo-500 shadow-md ring-1 ring-indigo-500/10" 
                                  : "bg-white hover:bg-slate-50/50 border-slate-200/80"
                              }`}
                            >
                              
                              {/* Top row */}
                              <div className="flex items-start justify-between gap-2">
                                <div 
                                  className="flex items-center space-x-2.5 min-w-0 cursor-pointer flex-1"
                                  onClick={() => setSelectedCandidate(c)}
                                >
                                  {/* Rank Tag */}
                                  <div className={`w-6 h-6 rounded-md flex items-center justify-center font-mono text-[10px] font-bold shrink-0 ${
                                    c.rank && c.rank <= 3 
                                      ? "bg-indigo-600 text-white shadow-sm" 
                                      : "bg-slate-100 text-slate-500 border border-slate-200"
                                  }`}>
                                    #{c.rank}
                                  </div>
                                  <div className="min-w-0">
                                    <h4 className="text-xs font-bold text-slate-900 truncate">{c.name}</h4>
                                    <p className="text-[10px] text-indigo-600 font-semibold truncate">{c.headline}</p>
                                  </div>
                                </div>

                                <div className="flex items-center space-x-2 shrink-0">
                                  {/* Compare Checkbox */}
                                  <label 
                                    className="flex items-center space-x-1 cursor-pointer"
                                    title="Add candidate to executive side-by-side comparison"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={isCompareChecked}
                                      onChange={() => toggleCompare(c.candidate_id)}
                                      className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5 cursor-pointer"
                                    />
                                    <span className="text-[9px] text-slate-400 font-bold uppercase hidden sm:inline">Compare</span>
                                  </label>

                                  {/* Score badge */}
                                  <span className={`font-mono text-xs font-bold border px-1.5 py-0.5 rounded-md ${getTierBadgeClass(c.scores.finalScore || 0)}`}>
                                    {c.scores.finalScore}%
                                  </span>
                                </div>
                              </div>

                              {/* Body content row (Trigger select candidate) */}
                              <div 
                                className="cursor-pointer space-y-1.5"
                                onClick={() => setSelectedCandidate(c)}
                              >
                                <p className="text-[10px] text-slate-500 font-mono font-medium">
                                  {c.experience_years}y Exp &bull; {c.education.split(",")[0]}
                                </p>
                                <p className="text-[10px] text-slate-600 italic line-clamp-1 border-t border-slate-100 pt-1.5">
                                  "{aiExplanations[c.candidate_id] || c.reasoning}"
                                </p>
                              </div>

                            </div>
                          );
                        })
                      ) : (
                        <div className="text-center py-10 space-y-2">
                          <AlertTriangle className="w-6 h-6 text-slate-300 mx-auto" />
                          <p className="text-xs text-slate-400 font-bold">No matching candidates found.</p>
                          <p className="text-[10px] text-slate-400">Try loosening your experience or search keyword filter criteria.</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* RIGHT: EXPANDED CANDIDATE DETAIL WORKSPACE (7% width) */}
                  <div className="md:col-span-7 bg-white border border-slate-200 rounded-2xl flex flex-col overflow-hidden shadow-sm" id="candidate-detail-column">
                    {selectedCandidate ? (
                      <div className="flex-1 flex flex-col overflow-hidden animate-fadeIn">
                        
                        {/* DETAIL HEADER CARD */}
                        <div className="p-5 border-b border-slate-200 bg-slate-50/30 shrink-0 space-y-4">
                          <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                            <div className="flex items-center space-x-3">
                              {/* Avatar circle */}
                              <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white font-bold text-lg flex items-center justify-center shadow-sm">
                                {selectedCandidate.name.split(" ").map(n => n[0]).join("")}
                              </div>
                              <div>
                                <div className="flex items-center space-x-2">
                                  <h3 className="font-bold text-base text-slate-900 font-display">{selectedCandidate.name}</h3>
                                  <span className="text-[9px] font-mono bg-indigo-50 text-indigo-600 px-2 py-0.5 border border-indigo-100 rounded-full">
                                    ID: {selectedCandidate.candidate_id.substring(0, 10)}
                                  </span>
                                </div>
                                <p className="text-xs text-indigo-600 font-semibold mt-0.5">{selectedCandidate.headline}</p>
                                <p className="text-[10px] text-slate-400 mt-0.5">🎓 {selectedCandidate.education}</p>
                              </div>
                            </div>
                            
                            {/* Visual Score Circle badge */}
                            <div className="flex items-center space-x-2.5 bg-white border border-slate-200 p-2 rounded-2xl shadow-sm self-start sm:self-auto">
                              <div className="w-12 h-12 rounded-full border-4 border-indigo-500/10 border-t-indigo-600 flex items-center justify-center font-mono text-sm font-bold text-slate-800">
                                {selectedCandidate.scores.finalScore}%
                              </div>
                              <div>
                                <p className="text-[9px] text-slate-400 font-bold uppercase">Weighted Index</p>
                                <span className={`inline-block text-[10px] font-bold px-1.5 py-0.5 rounded mt-0.5 ${getTierBadgeClass(selectedCandidate.scores.finalScore || 0)}`}>
                                  {getTierName(selectedCandidate.scores.finalScore || 0)}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* AI Justification / Explanation panel */}
                          <div className="bg-white border border-indigo-100 p-3.5 rounded-2xl shadow-sm flex flex-col space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-[10px] text-indigo-600 font-bold uppercase tracking-wider flex items-center font-display">
                                <Sparkles className="w-3.5 h-3.5 mr-1.5 text-indigo-500 animate-pulse" /> Justification Analysis
                              </span>
                              {!aiExplanations[selectedCandidate.candidate_id] && (
                                <button
                                  onClick={() => handleExplain(selectedCandidate)}
                                  disabled={explainingId === selectedCandidate.candidate_id}
                                  className="text-[10px] bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-100 disabled:text-slate-400 text-white font-bold py-1 px-2.5 rounded-lg border border-indigo-500/20 flex items-center space-x-1 cursor-pointer transition shadow-sm"
                                >
                                  {explainingId === selectedCandidate.candidate_id ? (
                                    <>
                                      <RefreshCw className="w-3 h-3 animate-spin" />
                                      <span>Calling Gemini...</span>
                                    </>
                                  ) : (
                                    <>
                                      <Sparkles className="w-3.5 h-3.5" />
                                      <span>Gemini Gap Evaluation</span>
                                    </>
                                  )}
                                </button>
                              )}
                            </div>
                            <p className="text-xs text-slate-600 leading-relaxed italic">
                              "{aiExplanations[selectedCandidate.candidate_id] || selectedCandidate.reasoning}"
                            </p>
                          </div>
                        </div>

                        {/* DETAIL SCROLL CONTENT PANEL */}
                        <div className="flex-1 overflow-y-auto p-5 space-y-5">
                          
                          {/* SCORE VECTOR CHANNELS */}
                          <div className="space-y-2.5">
                            <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center">
                              <BarChart3 className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> Score Vector Breakdown
                            </h4>
                            <div className="grid grid-cols-2 gap-3">
                              {selectedCandidate.cross_encoder_score !== undefined && (
                                <div className="bg-indigo-50/50 p-2.5 rounded-xl border border-indigo-100 flex justify-between items-center col-span-2">
                                  <div>
                                    <p className="text-[9px] text-indigo-700 font-bold uppercase flex items-center gap-1">
                                      <Zap className="w-3 h-3 text-indigo-600" /> Cross-Encoder Neural Score
                                    </p>
                                    <div className="flex items-baseline gap-2 mt-0.5">
                                      <span className="text-sm font-mono font-bold text-indigo-900">
                                        Logit: {selectedCandidate.cross_encoder_score}
                                      </span>
                                      {selectedCandidate.scores.relativeCrossEncoderScore !== undefined && (
                                        <span className="text-xs font-mono text-indigo-600 font-semibold">
                                          (Relative: {selectedCandidate.scores.relativeCrossEncoderScore}%)
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-[9px] text-slate-400 mt-0.5">
                                      Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (Pairwise deep relevance)
                                    </p>
                                  </div>
                                  <div className="text-right">
                                    <span className="px-2 py-0.5 bg-indigo-600 text-white text-[10px] font-mono font-bold rounded-md">
                                      Rerank #{selectedCandidate.rank}
                                    </span>
                                  </div>
                                </div>
                              )}

                              <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 flex justify-between items-center">
                                <div>
                                  <p className="text-[9px] text-slate-400 font-bold uppercase">Semantic Alignment</p>
                                  <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.scores.semanticScore}%</p>
                                </div>
                                <div className="w-1 h-8 bg-slate-200 rounded-full overflow-hidden">
                                  <div className="bg-indigo-600 h-full rounded-full" style={{ height: `${selectedCandidate.scores.semanticScore}%` }}></div>
                                </div>
                              </div>

                              <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 flex justify-between items-center">
                                <div>
                                  <p className="text-[9px] text-slate-400 font-bold uppercase">Technical Skill Match</p>
                                  <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.scores.skillScore}%</p>
                                </div>
                                <div className="w-1 h-8 bg-slate-200 rounded-full overflow-hidden">
                                  <div className="bg-emerald-500 h-full rounded-full" style={{ height: `${selectedCandidate.scores.skillScore}%` }}></div>
                                </div>
                              </div>

                              <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 flex justify-between items-center">
                                <div>
                                  <p className="text-[9px] text-slate-400 font-bold uppercase">Progression Tenure</p>
                                  <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.scores.careerScore}%</p>
                                </div>
                                <div className="w-1 h-8 bg-slate-200 rounded-full overflow-hidden">
                                  <div className="bg-rose-500 h-full rounded-full" style={{ height: `${selectedCandidate.scores.careerScore}%` }}></div>
                                </div>
                              </div>

                              <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 flex justify-between items-center">
                                <div>
                                  <p className="text-[9px] text-slate-400 font-bold uppercase">Behavioral Commitment</p>
                                  <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.scores.behavioralScore}%</p>
                                </div>
                                <div className="w-1 h-8 bg-slate-200 rounded-full overflow-hidden">
                                  <div className="bg-amber-500 h-full rounded-full" style={{ height: `${selectedCandidate.scores.behavioralScore}%` }}></div>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* RECRUITER SKILLS MATCH & GAP EVALUATOR */}
                          <div className="space-y-3.5 pt-3 border-t border-slate-100">
                            <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center">
                              <Check className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> Skills catalog & requested gaps
                            </h4>
                            
                            {(() => {
                              const { matched, missing, additional } = getSkillsBreakdown(selectedCandidate);
                              return (
                                <div className="space-y-3 text-xs">
                                  {/* Overlaps / Matched */}
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] text-emerald-600 font-bold uppercase tracking-wide flex items-center gap-1">
                                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Matched Skills ({matched.length})
                                    </p>
                                    <div className="flex flex-wrap gap-1.5">
                                      {matched.map((s, idx) => (
                                        <span key={idx} className="bg-emerald-50 text-emerald-700 text-xs py-1 px-2.5 rounded-lg font-bold border border-emerald-100 flex items-center">
                                          <Check className="w-3 h-3 mr-1 text-emerald-500" /> {s}
                                        </span>
                                      ))}
                                    </div>
                                  </div>

                                  {/* Missing / Gaps */}
                                  {missing.length > 0 && (
                                    <div className="space-y-1.5">
                                      <p className="text-[10px] text-rose-600 font-bold uppercase tracking-wide flex items-center gap-1">
                                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span> Target Skill Gap ({missing.length})
                                      </p>
                                      <div className="flex flex-wrap gap-1.5">
                                        {missing.map((s, idx) => (
                                          <span key={idx} className="bg-rose-50/50 text-rose-700 text-xs py-1 px-2.5 rounded-lg font-semibold border border-rose-100 flex items-center" title="Missing target required technical skill">
                                            <X className="w-3 h-3 mr-1 text-rose-400" /> {s}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {/* Additional talent skills */}
                                  {additional.length > 0 && (
                                    <div className="space-y-1.5">
                                      <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wide">Additional Talent Skills ({additional.length})</p>
                                      <div className="flex flex-wrap gap-1.5">
                                        {additional.map((s, idx) => (
                                          <span key={idx} className="bg-slate-50 text-slate-600 text-xs py-1 px-2.5 rounded-lg border border-slate-200">{s}</span>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              );
                            })()}
                          </div>

                          {/* PUBLIC ENGAGEMENT METRICS DECK */}
                          <div className="space-y-2.5 pt-3 border-t border-slate-100">
                            <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center">
                              <Star className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> Open Source & Engagement Signals
                            </h4>
                            <div className="grid grid-cols-3 gap-3">
                              <div className="bg-slate-50/50 p-3 rounded-2xl border border-slate-100 flex items-center space-x-2.5">
                                <Star className="w-4 h-4 text-amber-500 shrink-0" />
                                <div>
                                  <p className="text-[9px] text-slate-400 font-bold uppercase">GitHub Stars</p>
                                  <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.behavioral_signals.github_stars}</p>
                                </div>
                              </div>
                              <div className="bg-slate-50/50 p-3 rounded-2xl border border-slate-100 flex items-center space-x-2.5">
                                <GitCommit className="w-4 h-4 text-indigo-500 shrink-0" />
                                <div>
                                  <p className="text-[9px] text-slate-400 font-bold uppercase">Commits/Year</p>
                                  <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{selectedCandidate.behavioral_signals.github_commits_last_year}</p>
                                </div>
                              </div>
                              <div className="bg-slate-50/50 p-3 rounded-2xl border border-slate-100 flex items-center space-x-2.5">
                                <MessageSquare className="w-4 h-4 text-emerald-500 shrink-0" />
                                <div>
                                  <p className="text-[9px] text-slate-400 font-bold uppercase">Response Rate</p>
                                  <p className="text-xs font-mono font-bold text-slate-800 mt-0.5">{Math.round(selectedCandidate.behavioral_signals.recruiter_response_rate * 100)}%</p>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* WORK EXPERIENCE TIMELINE */}
                          <div className="space-y-3 pt-3 border-t border-slate-100">
                            <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center">
                              <Briefcase className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> Career Milestones History
                            </h4>
                            <div className="relative border-l-2 border-slate-100 pl-4 ml-2.5 space-y-4">
                              {selectedCandidate.career_history.map((job, idx) => (
                                <div key={idx} className="relative">
                                  <div className="absolute -left-[21.5px] top-1 w-2.5 h-2.5 rounded-full bg-indigo-600 border-2 border-white shadow-sm"></div>
                                  <div className="space-y-1">
                                    <div className="flex justify-between items-start text-xs">
                                      <h5 className="font-bold text-slate-900">{job.title}</h5>
                                      <span className="text-[10px] text-indigo-600 font-bold font-mono">{job.company}</span>
                                    </div>
                                    <p className="text-xs text-slate-500 leading-relaxed font-medium">{job.description}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* CORE CANDIDATE VECTORS */}
                          <div className="grid grid-cols-2 gap-4 border-t border-slate-100 pt-4 text-xs font-medium text-slate-500">
                            <div className="flex items-start space-x-2">
                              <GraduationCap className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                              <div>
                                <p className="text-slate-400 text-[9px] font-bold uppercase">Academic Background</p>
                                <p className="text-slate-700 font-semibold mt-0.5">{selectedCandidate.education}</p>
                              </div>
                            </div>
                            <div className="flex items-start space-x-2">
                              <User className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                              <div>
                                <p className="text-slate-400 text-[9px] font-bold uppercase">Experience Seniority</p>
                                <p className="text-slate-700 font-semibold mt-0.5">{selectedCandidate.experience_years} Years Active Industry Service</p>
                              </div>
                            </div>
                          </div>

                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-400">
                        <User className="w-8 h-8 text-slate-300 animate-pulse mb-2" />
                        <p className="text-xs font-bold">Select a candidate to view resume detail inspection</p>
                      </div>
                    )}
                  </div>

                </div>
              )}

            </div>
          ) : (
            <div className="flex-1 bg-white border border-slate-200 rounded-3xl p-10 flex flex-col items-center justify-center text-center space-y-4 shadow-sm" id="empty-panel">
              <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl border border-indigo-100">
                <Search className="w-8 h-8" />
              </div>
              <div className="space-y-1.5">
                <h3 className="font-display font-bold text-slate-800 text-lg">No Active Pipeline Rank Results</h3>
                <p className="text-slate-500 text-xs max-w-sm mx-auto leading-relaxed font-medium">
                  Select or input a job criteria matrix on the left panel, configure scoring variables, and run matching to score 100,000 resume records.
                </p>
              </div>
            </div>
          )}
        </section>

      </main>

      {/* FLOATING ACTION SHEET FOR CANDIDATE COMPARISON */}
      {compareIds.length > 0 && (
        <div className="fixed bottom-5 left-1/2 -translate-x-1/2 bg-[#0f172a] text-white py-3 px-6 rounded-2xl border border-slate-800 shadow-2xl flex items-center justify-between gap-6 z-50 animate-slideUp max-w-lg w-[calc(100%-2rem)]">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-xs">
              {compareIds.length}
            </div>
            <div>
              <p className="text-xs font-bold text-white">Candidates selected for comparison</p>
              <p className="text-[10px] text-slate-400">Select up to 3 candidates for deep review</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCompareMode(true)}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold px-3.5 py-2 rounded-xl transition flex items-center space-x-1.5 cursor-pointer shadow-sm shadow-indigo-600/25"
            >
              <ArrowLeftRight className="w-3.5 h-3.5" />
              <span>Compare Now</span>
            </button>
            <button
              onClick={() => setCompareIds([])}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-bold px-3.5 py-2 rounded-xl border border-slate-700 transition cursor-pointer"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* REAL RESUME PDF UPLOAD MODAL */}
      <ResumeUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUploadSuccess={() => {
          fetchStatus();
        }}
      />

    </div>
  );
}

