export interface FraudScanResult {
  message: string;
  suspicious_transactions_found: number;
  details: FraudDetection[];
  last_scan_time?: string;
}

export interface FraudDetection {
  transaction_id: string;
  reason: string;
  risk_level?: 'Low' | 'Medium' | 'High';
}
