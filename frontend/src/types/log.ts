export interface LogEntry {
  created_at: string | null;
  message: string;
}

export interface JobLogData {
  lines: string[];
  entries: LogEntry[];
  status: string | null;
  jobId: string | null;
}
