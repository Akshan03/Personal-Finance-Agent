import autogen
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.models.transaction import Transaction, TransactionCategory
from app.utils.llm_config import get_groq_config

# Configuration for the fraud detection agent
FRAUD_AGENT_CONFIG = {
    "name": "Fraud Detective",
    "description": "I analyze financial transactions to identify potentially fraudulent activities."
    # llm_config is now handled dynamically through get_groq_config
}

class FraudDetectionAgent:
    """Agent responsible for analyzing transactions and detecting potential fraud."""
    
    def __init__(self, model_config=None):
        """Initialize the fraud detection agent with optional model configuration."""
        # Use Groq configuration with low temperature for more deterministic fraud detection
        config = model_config or get_groq_config(temperature=0.1).dict()
        
        # Create the Autogen assistant agent
        self.agent = autogen.AssistantAgent(
            name=FRAUD_AGENT_CONFIG["name"],
            system_message=self._build_system_message(),
            llm_config=config
        )
        
        # User proxy agent to interact with the assistant
        self.user_proxy = autogen.UserProxyAgent(
            name="Finance System",
            is_termination_msg=lambda x: "FRAUD_ANALYSIS_COMPLETE" in x.get("content", ""),
            human_input_mode="NEVER"  # No human input needed, system-to-system communication
        )
    
    def _build_system_message(self) -> str:
        """Build the system message that defines the behavior of the fraud detection agent."""
        return f"""You are {FRAUD_AGENT_CONFIG['name']}, {FRAUD_AGENT_CONFIG['description']}
        
        You will be presented with a list of financial transactions. Your task is to:
        
        1. Identify any suspicious or potentially fraudulent transactions based on:
           - Unusual transaction amounts (much larger than typical)
           - Suspicious timing (late night, multiple rapid transactions)
           - Unusual categories compared to user history
           - Geographic anomalies (if location data available)
        
        2. Explain in simple terms why each flagged transaction might be suspicious
        
        3. Rate each suspicious transaction on a risk scale (Low, Medium, High)
        
        4. Provide recommendations on what actions the user should take
        
        Always format your final response with:
        FRAUD_ANALYSIS_COMPLETE to signal the end of your analysis.
        """
    
    def analyze_transactions(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze a list of transactions to detect potential fraud."""
        if not transactions:
            return {
                "status": "completed",
                "message": "No transactions provided for analysis.",
                "suspicious_transactions": []
            }
        
        # Simple rule-based checks (baseline before using the LLM)
        suspicious_transactions = self._rule_based_detection(transactions)
        
        # If we have suspicious transactions from rules, we can enhance the analysis with the LLM
        if suspicious_transactions or len(transactions) > 10:
            transactions_formatted = self._format_transactions_for_llm(transactions)
            
            # Create a prompt with the formatted transactions
            prompt = f"""Here are the user's recent transactions:
            
            {transactions_formatted}
            
            Some transactions may have already been flagged as suspicious based on rules:
            {self._format_suspicious_for_llm(suspicious_transactions) if suspicious_transactions else "None flagged by rules yet."}
            
            Please analyze the transactions and identify any potentially fraudulent activity.
            Include the transaction IDs in your analysis and explain why you've flagged each one.
            """
            
            # Initialize chat with the user proxy (system-to-system, no human needed)
            self.user_proxy.initiate_chat(
                self.agent,
                message=prompt
            )
            
            # Extract the fraud analysis results from the agent's response
            last_message = self.user_proxy.chat_messages[self.agent.name][-1]["content"]
            
            # Process the agent's response and merge with rule-based results
            llm_results = self._process_llm_response(last_message)
            final_results = self._merge_detection_results(suspicious_transactions, llm_results)
            
            return {
                "status": "completed",
                "message": "Fraud analysis completed.",
                "suspicious_transactions": final_results
            }
        
        # If too few transactions or no suspicious ones detected by rules, 
        # just return the rule-based results
        return {
            "status": "completed",
            "message": "Fraud analysis completed using rule-based detection only.",
            "suspicious_transactions": suspicious_transactions
        }
    
    def _rule_based_detection(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """Simple rule-based fraud detection as a first pass."""
        suspicious = []
        if len(transactions) < 2:
            return suspicious  # Need more data for meaningful analysis
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([
            {
                "id": t.id,
                "amount": t.amount,
                "category": str(t.category.value) if hasattr(t.category, "value") else str(t.category),
                "timestamp": t.timestamp
            } 
            for t in transactions
        ])
        
        # Sort by timestamp for time-based analysis
        df = df.sort_values(by="timestamp")
        
        # 1. Check for unusually large transactions
        if len(df) > 3:  # Need enough data for statistical outlier detection
            mean_amount = df["amount"].mean()
            std_amount = df["amount"].std() if len(df) > 5 else mean_amount * 0.5
            threshold = mean_amount + 3 * std_amount  # 3 standard deviations
            
            outliers = df[df["amount"] > threshold]
            for _, row in outliers.iterrows():
                suspicious.append({
                    "transaction_id": row["id"],
                    "reason": f"Unusually large amount (${row['amount']:.2f})",
                    "risk_level": "Medium",
                    "detection_method": "rule-based"
                })
        
        # 2. Check for rapid succession transactions
        if len(df) > 3:
            df["time_diff"] = df["timestamp"].diff().dt.total_seconds() / 60  # minutes
            rapid_txns = df[(df["time_diff"] < 10) & (df["time_diff"] > 0)]  # Less than 10 minutes apart
            
            for _, row in rapid_txns.iterrows():
                suspicious.append({
                    "transaction_id": row["id"],
                    "reason": f"Transaction made very quickly after previous one ({row['time_diff']:.1f} minutes)",
                    "risk_level": "Low",
                    "detection_method": "rule-based"
                })
        
        return suspicious
    
    def _format_transactions_for_llm(self, transactions: List[Transaction]) -> str:
        """Format transaction data for LLM consumption."""
        formatted = "ID | Amount | Category | Date | Time\n"
        formatted += "--- | --- | --- | --- | ---\n"
        
        for t in transactions:
            date_str = t.timestamp.strftime("%Y-%m-%d")
            time_str = t.timestamp.strftime("%H:%M:%S")
            formatted += f"{t.id} | ${t.amount:.2f} | {t.category.value if hasattr(t.category, 'value') else t.category} | {date_str} | {time_str}\n"
        
        return formatted
    
    def _format_suspicious_for_llm(self, suspicious: List[Dict[str, Any]]) -> str:
        """Format suspicious transactions for LLM consumption."""
        if not suspicious:
            return "No suspicious transactions detected by rules."
        
        formatted = "Transaction ID | Reason | Risk Level\n"
        formatted += "--- | --- | ---\n"
        
        for t in suspicious:
            formatted += f"{t['transaction_id']} | {t['reason']} | {t['risk_level']}\n"
        
        return formatted
    
    def _process_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Process the LLM's response to extract structured fraud detection results."""
        suspicious = []
        
        # Simplified parsing - in production, would use more robust methods
        if "no suspicious transactions" in response.lower():
            return suspicious
        
        # Extract transaction IDs and reasons - this is a simple approach
        # In production, you'd want more robust parsing
        lines = response.split("\n")
        current_id = None
        current_reason = ""
        current_risk = "Medium"  # Default
        
        for line in lines:
            line = line.strip()
            
            # Check for transaction ID mentions
            if "transaction" in line.lower() and "id" in line.lower() and any(char.isdigit() for char in line):
                # Save previous transaction if there was one
                if current_id is not None:
                    suspicious.append({
                        "transaction_id": current_id,
                        "reason": current_reason.strip(),
                        "risk_level": current_risk,
                        "detection_method": "llm"
                    })
                
                # Extract new ID from line - simplified approach
                for word in line.split():
                    if word.isdigit():
                        current_id = int(word)
                        break
                current_reason = ""
                current_risk = "Medium"  # Reset to default
            
            # Check for risk level mentions
            elif "risk" in line.lower():
                if "high" in line.lower():
                    current_risk = "High"
                elif "medium" in line.lower():
                    current_risk = "Medium"
                elif "low" in line.lower():
                    current_risk = "Low"
            
            # Otherwise, add to the reason
            elif current_id is not None:
                current_reason += " " + line
        
        # Add the last transaction if there is one
        if current_id is not None:
            suspicious.append({
                "transaction_id": current_id,
                "reason": current_reason.strip(),
                "risk_level": current_risk,
                "detection_method": "llm"
            })
        
        return suspicious
    
    def _merge_detection_results(self, rule_based: List[Dict[str, Any]], llm_based: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge results from rule-based and LLM-based detection."""
        merged = []
        transaction_ids_added = set()
        
        # Add all rule-based detections
        for detection in rule_based:
            merged.append(detection)
            transaction_ids_added.add(detection["transaction_id"])
        
        # Add LLM detections if not already added
        for detection in llm_based:
            if detection["transaction_id"] not in transaction_ids_added:
                merged.append(detection)
                transaction_ids_added.add(detection["transaction_id"])
        
        return merged