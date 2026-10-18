// export interface CareerHistoryItem {
//   title: string;
//   company: string;
//   description: string;
// }

// export interface BehavioralSignals {
//   github_stars: number;
//   github_commits_last_year: number;
//   recruiter_response_rate: number;
// }

// export interface CandidateScores {
//   semanticScore: number;
//   skillScore: number;
//   careerScore: number;
//   behavioralScore: number;
//   finalScore?: number;
// }

// export interface Candidate {
//   candidate_id: string;
//   name: string;
//   headline: string;
//   experience_years: number;
//   education: string;
//   skills: string[];
//   scores: CandidateScores;
//   behavioral_signals: BehavioralSignals;
//   career_history: CareerHistoryItem[];
//   rank?: number;
//   reasoning?: string;
// }

// export interface PipelineTelemetry {
//   totalCandidates: number;
//   stage1CandidatesCount: number;
//   stage1TimeMs: number;
//   stage2TimeMs: number;
//   totalTimeMs: number;
//   modelUsed: string;
//   weights: {
//     semantic: number;
//     skills: number;
//     career: number;
//     behavioral: number;
//   };
// }

// export interface PipelineResults {
//   topCandidates: Candidate[];
//   parsedFeatures: {
//     text: string;
//     requiredSkills: string[];
//     preferredSkills: string[];
//     experienceYearsRequired: number;
//     domainKeywords: string[];
//   };
//   telemetry: PipelineTelemetry;
// }

export interface CareerHistoryItem {
  title: string;
  company: string;
  description: string;
}

export interface BehavioralSignals {
  github_stars: number;
  github_commits_last_year: number;
  recruiter_response_rate: number;
}

export interface CandidateScores {
  semanticScore: number;
  skillScore: number;
  careerScore: number;
  behavioralScore: number;
  crossEncoderScore?: number;
  rawCrossEncoderScore?: number;
  relativeCrossEncoderScore?: number;
  finalScore?: number;
}

export interface Candidate {
  candidate_id: string;
  name: string;
  headline: string;
  experience_years: number;
  education: string;
  skills: string[];
  scores: CandidateScores;
  behavioral_signals: BehavioralSignals;
  career_history: CareerHistoryItem[];
  cross_encoder_score?: number;
  raw_cross_encoder_score?: number;
  relative_cross_encoder_score?: number;
  rrf_score?: number;
  rank?: number;
  reasoning?: string;
}

export interface PipelineTelemetry {
  totalCandidates: number;
  stage1CandidatesCount: number;
  stage1TimeMs: number;
  stage2TimeMs: number;
  stage3CandidatesCount?: number;
  stage3RerankTimeMs?: number;
  phase5RerankLatencyMs?: number;
  rerankerModel?: string;
  totalTimeMs: number;
  modelUsed: string;
  weights: {
    semantic: number;
    skills: number;
    career: number;
    behavioral: number;
  };
}

export interface PipelineResults {
  topCandidates: Candidate[];
  parsedFeatures: {
    text: string;
    requiredSkills: string[];
    preferredSkills: string[];
    experienceYearsRequired: number;
    domainKeywords: string[];
  };
  telemetry: PipelineTelemetry;
}

