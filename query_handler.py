"""
Query dataset using Qwen 7B.
Allows questions like:
- "How many policies have customers over 50?"
- "What's the average premium for age 30-40?"
"""

import pandas as pd
from ollama_client import query_qwen


class DatasetQueryHandler:
    """Handler for dataset questions via Qwen."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with dataset.
        
        Args:
            df: Policy DataFrame from pipeline._get_dataset()
        """
        self.df = df
        self.dataset_summary = self._build_summary()
    
    def _build_summary(self) -> str:
        """Build dataset summary for Qwen context."""
        
        summary = f"""DATASET SUMMARY:
- Total Policies: {len(self.df):,}
- Columns: {', '.join(self.df.columns.tolist())}
- Age Range: {self.df['customer_age'].min()}-{self.df['customer_age'].max()} years
- Avg Age: {self.df['customer_age'].mean():.1f} years
- Avg Base Rate: ${self.df['base_rate'].mean():.2f}
- Min Base Rate: ${self.df['base_rate'].min():.2f}
- Max Base Rate: ${self.df['base_rate'].max():.2f}

Data is real insurance policy information. Answer specific questions about this dataset."""
        
        return summary
    
    def answer_dataset_query(self, query: str) -> str:
        """
        Answer questions about the dataset using Qwen.
        
        Args:
            query: User question about the dataset
        
        Returns:
            Answer with specific data points
        """
        
        # First, try pandas operations for accuracy
        computed_answer = self._compute_answer(query)
        
        if computed_answer:
            return computed_answer
        
        # Fall back to Qwen for complex questions
        context = f"""{self.dataset_summary}

You are a data analyst expert in insurance. Answer questions about this insurance dataset.
Cite specific numbers from the dataset when possible.
If you can't answer from the data, say "I don't have enough information about that."
Keep answers concise (2-3 sentences)."""
        
        return query_qwen(
            prompt=query,
            system_context=context,
            temperature=0.2
        )
    
    def _compute_answer(self, query: str) -> str:
        """Try to extract answer from dataset using pandas."""
        
        query_lower = query.lower()
        
        # "How many policies?"
        if "how many" in query_lower and "polic" in query_lower:
            return f"📊 There are **{len(self.df):,} policies** in the dataset."
        
        # "Average age?" / "Mean age?"
        if "average age" in query_lower or "mean age" in query_lower:
            avg_age = self.df['customer_age'].mean()
            return f"📊 Average customer age: **{avg_age:.1f} years**"
        
        # "Age range?"
        if "age range" in query_lower:
            min_age = self.df['customer_age'].min()
            max_age = self.df['customer_age'].max()
            return f"📊 Customer ages range from **{min_age} to {max_age} years**"
        
        # "Average base rate?" / "Avg premium?"
        if "average base rate" in query_lower or "avg premium" in query_lower or "average premium" in query_lower:
            avg_rate = self.df['base_rate'].mean()
            return f"📊 Average base rate: **${avg_rate:.2f}**"
        
        # "Policies over age 50?" / "Age 50+" / "Customers over 50?"
        if ("over 50" in query_lower or "age 50" in query_lower or "above 50" in query_lower) and ("polic" in query_lower or "customer" in query_lower):
            count = len(self.df[self.df['customer_age'] > 50])
            pct = (count / len(self.df)) * 100
            return f"📊 **{count:,} policies** ({pct:.1f}%) have customers over 50 years old"
        
        # "Youngest?" / "Oldest?"
        if "youngest" in query_lower or "minimum age" in query_lower:
            min_age = self.df['customer_age'].min()
            return f"📊 Youngest customer: **{min_age} years old**"
        
        if "oldest" in query_lower or "maximum age" in query_lower:
            max_age = self.df['customer_age'].max()
            return f"📊 Oldest customer: **{max_age} years old**"
        
        # "Highest premium?" / "Most expensive?"
        if "highest" in query_lower and ("premium" in query_lower or "rate" in query_lower):
            max_rate = self.df['base_rate'].max()
            return f"📊 Highest base rate: **${max_rate:.2f}**"
        
        # "Lowest premium?"
        if "lowest" in query_lower and ("premium" in query_lower or "rate" in query_lower):
            min_rate = self.df['base_rate'].min()
            return f"📊 Lowest base rate: **${min_rate:.2f}**"
        
        return None  # No direct match, use Qwen
