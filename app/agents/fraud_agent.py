import os
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.config import settings
from app.models.transaction import Transaction, TransactionCategory

# Configuration for the fraud detection agent
FRAUD_AGENT_CONFIG = {
    "name": "Fraud Detective",
    "description": "I analyze financial transactions to identify potentially fraudulent activities."
}

class FraudDetectionAgent:
    """Agent responsible for analyzing transactions and detecting potential fraud."""
    
    def __init__(self):
        """Initialize the fraud detection agent"""
        # Set up API credentials
        self.groq_api_key = os.getenv("GROQ_API_KEY", settings.groq_api_key)
        self.groq_model = os.getenv("GROQ_MODEL", settings.groq_model)
        
        # Create a dedicated OpenAI client for Groq
        from openai import OpenAI
        self.client = OpenAI(
            api_key=self.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
    
    def _build_system_message(self) -> str:
        """Build the system message that defines the behavior of the fraud detection agent."""
        return f"""You are {FRAUD_AGENT_CONFIG['name']}, {FRAUD_AGENT_CONFIG['description']}

        When analyzing transactions:
        1. Look for patterns of unusual spending or activity
        2. Identify amounts that are outliers compared to the user's usual spending
        3. Notice rapid sequences of transactions that may indicate card theft
        4. Be attentive to unusual merchant categories or locations
        5. Check for transactions that don't match the user's typical behavior
        
        Your task is to review financial transactions and identify potentially fraudulent activity.
        Explain your reasoning clearly and assign a risk score from 1-10 to each suspicious transaction.
        
        Format your response as a valid JSON object.
        """
    
    def analyze_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a list of transactions to detect potential fraud.
        
        Args:
            transactions: List of transaction dictionaries to analyze
            
        Returns:
            Dictionary with suspicious transactions and analysis
        """
        # Prepare transactions for analysis
        transactions_df = pd.DataFrame(transactions)
        
        # Perform rule-based screening (basic checks)
        suspicious_transactions = self._rule_based_screening(transactions_df)
        
        if not suspicious_transactions:
            return {
                "suspicious_transactions": [],
                "analysis": "No suspicious transactions detected."
            }
        
        # Format the transactions for the analysis
        transaction_text = self._format_transactions_for_analysis(suspicious_transactions)
        
        # Run the AI analysis
        prompt = f"""You are a financial fraud detection expert specializing in personal finance.

        Analyze these potentially suspicious transactions and identify any that appear fraudulent. 
        For each suspicious transaction, explain why it might be fraudulent and assign a risk score from 1-10.

        Transactions to analyze:
        {transaction_text}

        Respond with your analysis in this JSON format:
        {{
            "potentially_fraudulent": [list of transaction IDs that appear fraudulent],
            "analysis": {{
                "transaction_id": {{
                    "risk_score": number,
                    "explanation": "detailed explanation"
                }}
            }},
            "summary": "A brief executive summary of your findings."
        }}

        Your response must be valid JSON.
        """
        
        # Use the OpenAI client directly with the Groq API
        try:
            response = self.client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": self._build_system_message()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Keep temperature low for consistent results
            )
            
            # Extract the response content
            response_content = response.choices[0].message.content
            
            # Clean up potential formatting issues with the JSON response
            analysis_json = self._extract_json_from_response(response_content)
            
            # Return results
            return {
                "suspicious_transactions": suspicious_transactions,
                "analysis": analysis_json
            }
            
        except Exception as e:
            # Log the error and return a friendly error message
            print(f"Error in fraud detection API call: {str(e)}")
            return {
                "suspicious_transactions": suspicious_transactions,
                "analysis": {
                    "error": "An error occurred during fraud analysis. Please try again later.",
                    "technical_details": str(e)
                }
            }
    
    def _rule_based_screening(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Simple rule-based fraud detection to identify suspicious transactions.
        
        Args:
            df: DataFrame of transactions to analyze
            
        Returns:
            List of suspicious transaction dictionaries
        """
        suspicious = []
        
        if len(df) < 2:
            return suspicious  # Need more data for meaningful analysis
        
        # Ensure we have the required columns
        required_columns = ['id', 'amount', 'category', 'timestamp', 'description']
        for col in required_columns:
            if col not in df.columns:
                if col == 'description':
                    df['description'] = 'No description available'
                else:
                    print(f"Missing required column: {col}")
                    return suspicious  # Can't analyze without essential data
        
        # Convert timestamp to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp for time-based analysis
        df = df.sort_values(by="timestamp")
        
        # 1. Check for unusually large transactions
        if len(df) > 3:  # Need enough data for statistical outlier detection
            mean_amount = df["amount"].mean()
            std_amount = df["amount"].std() if len(df) > 5 else mean_amount * 0.5
            threshold = mean_amount + 3 * std_amount  # 3 standard deviations
            
            outliers = df[df["amount"] > threshold]
            for _, row in outliers.iterrows():
                suspicious.append(row.to_dict())
        
        # 2. Check for rapid succession transactions
        if len(df) > 3:
            df["time_diff"] = df["timestamp"].diff().dt.total_seconds() / 60  # minutes
            rapid_txns = df[(df["time_diff"] < 10) & (df["time_diff"] > 0)]  # Less than 10 minutes apart
            
            for _, row in rapid_txns.iterrows():
                # Add transaction if not already in suspicious list
                if not any(s['id'] == row['id'] for s in suspicious):
                    suspicious.append(row.to_dict())
                    
        # 3. Check for unusual merchants/categories
        unusual_categories = ['gambling', 'adult', 'cryptocurrency', 'wire_transfer']
        unusual_txns = df[df['category'].str.lower().isin(unusual_categories)]
        
        for _, row in unusual_txns.iterrows():
            if not any(s['id'] == row['id'] for s in suspicious):
                suspicious.append(row.to_dict())
                
        return suspicious
    
    def _format_transactions_for_analysis(self, transactions: List[Dict[str, Any]]) -> str:
        """
        Format transaction dictionaries for LLM analysis.
        
        Args:
            transactions: List of transaction dictionaries to format
            
        Returns:
            Formatted transaction text for the LLM
        """
        formatted = []
        
        for i, txn in enumerate(transactions):
            # Handle timestamp formatting
            timestamp = txn.get('timestamp', 'Unknown date')
            if not isinstance(timestamp, str):
                try:
                    timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    timestamp = str(timestamp)
                    
            # Format each transaction
            txn_string = f"Transaction #{i+1} (ID: {txn.get('id', 'Unknown ID')}):\n"
            txn_string += f"  - Amount: ${txn.get('amount', 0):.2f}\n"
            txn_string += f"  - Category: {txn.get('category', 'Uncategorized')}\n"
            txn_string += f"  - Date: {timestamp}\n"
            txn_string += f"  - Description: {txn.get('description', 'No description')}\n"
            formatted.append(txn_string)
        
        return "\n".join(formatted)
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from the LLM response, handling common formatting issues.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            Parsed JSON as a dictionary
        """
        try:
            # Handle common JSON extraction issues
            # 1. Check for code blocks (```json ... ```)
            if '```' in response:
                # Extract content between ``` markers
                blocks = response.split('```')
                for i, block in enumerate(blocks):
                    if i % 2 == 1:  # This is inside a code block
                        # Remove 'json' prefix if present
                        if block.lower().startswith('json\n'):
                            block = block[4:].strip()
                        try:
                            return json.loads(block.strip())
                        except:
                            continue  # Try next block if this one fails
            
            # 2. Direct JSON parsing
            try:
                return json.loads(response)
            except:
                pass
            
            # 3. Find content between curly braces
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx+1]
                return json.loads(json_str)
                
            # If we couldn't parse it, return a basic structure with the raw response
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response
            }
                
        except Exception as e:
            # Return error information
            return {
                "error": f"JSON parsing error: {str(e)}",
                "raw_response": response
            }