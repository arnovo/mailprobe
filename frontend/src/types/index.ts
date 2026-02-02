export type { JobLogData, LogEntry } from './log';

/**
 * Verification signals returned by the API.
 * Used for displaying detailed verification status in UI.
 */
export interface VerificationSignals {
  mx_found: boolean;
  spf_present: boolean;
  dmarc_present: boolean;
  catch_all: boolean | null;
  smtp_attempted: boolean;
  smtp_blocked: boolean;
  provider: string;
  web_mentioned: boolean;
  signals: string[];
  reason: string;
}

/**
 * Known email provider identifiers.
 */
export type EmailProvider = 
  | 'google' 
  | 'microsoft' 
  | 'ionos' 
  | 'barracuda' 
  | 'proofpoint' 
  | 'mimecast' 
  | 'ovh' 
  | 'zoho' 
  | 'yahoo' 
  | 'icloud' 
  | 'other';

