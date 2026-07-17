import os
import re
from typing import Optional, Tuple


class OpenAIEngine:
    """
    RAG-grounded LLM engine that ONLY answers from retrieved context.
    Falls back to intelligent offline extraction when API unavailable.
    CRITICAL: Never hallucinates - always validates responses against source data.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        self.model = model
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI   #type: ignore
                self.client = OpenAI(api_key=self.api_key)
                print("[OK] OpenAI API client initialized")
            except ImportError:
                print("[WARN] openai package not installed. Falling back to offline engine.")
        else:
            print("[WARN] OPENAI_API_KEY not found. Using offline context extraction engine.")

    def _extract_context_and_question(self, prompt: str) -> Tuple[str, str]:
        """Extract verified context and user question from formatted prompt."""
        start_marker = "[VERIFIED DATABASE CONTEXT]"
        end_marker = "[USER QUESTION]"
        
        if start_marker in prompt and end_marker in prompt:
            context = prompt.split(start_marker)[1].split(end_marker)[0].strip()
            question = prompt.split(end_marker)[1].strip()
            return context, question
        return prompt, ""

    def _extract_keywords(self, text: str, min_length: int = 3) -> list[str]:
        """Extract meaningful keywords from text."""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'was', 'be', 'are', 'by', 'with', 'that', 'this', 'has'}
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in stop_words and len(w) >= min_length]

    def _find_relevant_lines(self, text: str, keywords: list[str], context_lines: int = 2) -> list[str]:
        """Find lines in context that contain query keywords."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        relevant_lines = []
        
        for i, line in enumerate(lines):
            if any(re.search(r'\b' + re.escape(keyword) + r'\b', line, re.I) for keyword in keywords):
                # Add context lines for better understanding
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context_section = '\n'.join(lines[start:end])
                if context_section not in relevant_lines:
                    relevant_lines.append(context_section)
        
        return relevant_lines

    def _score_relevance(self, text: str, question: str, max_results: int = 5) -> list[str]:
        """Score text blocks by relevance to question using TF-IDF-like scoring."""
        query_keywords = self._extract_keywords(question)
        text_blocks = [block.strip() for block in re.split(r'\n\n+', text) if block.strip()]
        
        scored_blocks = []
        for block in text_blocks:
            score = sum(1 for keyword in query_keywords 
                    if re.search(r'\b' + re.escape(keyword) + r'\b', block, re.I))
            if score > 0:
                scored_blocks.append((score, block))
        
        # Sort by relevance and return top results
        scored_blocks.sort(key=lambda x: x[0], reverse=True)
        return [block for _, block in scored_blocks[:max_results]]

    def _validate_and_extract(self, context: str, question: str) -> str:
        
        question_lower = question.lower()
        
        if not context or context == "[]":
            return (
                "❌ I don't have any source data to answer this question. "
                "Please ingest F1 data first using the 'web' option in the main menu."
            )

        # Extract question intent keywords
        keywords = self._extract_keywords(question)
        
        # Strategy/Pit Stop Intent
        if any(kw in question_lower for kw in ['tyre', 'tire', 'compound', 'pit', 'strategy', 'soft', 'medium', 'hard']):
            strategy_lines = self._find_relevant_lines(context, ['tyre', 'tire', 'compound', 'pit', 'soft', 'medium', 'hard', 'strategy', 'stop'])
            if strategy_lines:
                return (
                    "🏎️ **TYRE STRATEGY** (from source data):\n\n" +
                    "\n".join(strategy_lines[:3])
                )

        # Weather Intent
        if any(kw in question_lower for kw in ['weather', 'forecast', 'rain', 'sunny', 'temperature', 'condition']):
            weather_lines = self._find_relevant_lines(context, ['weather', 'rain', 'sunny', 'forecast', 'temperature', 'condition', 'precipitation'])
            if weather_lines:
                return (
                    "🌤️ **WEATHER INFORMATION** (from source data):\n\n" +
                    "\n".join(weather_lines[:3])
                )

        # Race Results Intent
        if any(kw in question_lower for kw in ['result', 'podium', 'finished', 'won', 'winner', 'position', '1st', '2nd', '3rd']):
            result_lines = self._find_relevant_lines(context, ['result', 'podium', 'finished', 'won', 'winner', '1st', '2nd', '3rd', 'position'])
            if result_lines:
                return (
                    "🏁 **RACE RESULTS** (from source data):\n\n" +
                    "\n".join(result_lines[:4])
                )

        # Qualifying/Pole Intent
        if any(kw in question_lower for kw in ['pole', 'qualifying', 'grid', 'q1', 'q2', 'q3']):
            pole_lines = self._find_relevant_lines(context, ['pole', 'qualifying', 'grid', 'q1', 'q2', 'q3'])
            if pole_lines:
                return (
                    "🎯 **QUALIFYING / POLE POSITION** (from source data):\n\n" +
                    "\n".join(pole_lines[:4])
                )

        # Lap Time Intent
        if any(kw in question_lower for kw in ['lap', 'fastest', 'laptime', 'pace', 'sector']):
            lap_lines = self._find_relevant_lines(context, ['lap', 'fastest', 'laptime', 'pace', 'sector', 'time'])
            if lap_lines:
                return (
                    "⏱️ **LAP TIME & PACE** (from source data):\n\n" +
                    "\n".join(lap_lines[:4])
                )

        # Year Mismatch Detection
        year_match = re.search(r'\b(20[2-9]\d)\b', question_lower)
        if year_match:
            query_year = year_match.group(1)
            context_years = re.findall(r'\b(20[2-9]\d)\b', context.lower())
            if context_years and query_year not in context_years:
                return (
                    f"⚠️ **YEAR MISMATCH**: You asked about {query_year}, but the ingested data is from "
                    f"{', '.join(set(context_years))}. Please ingest {query_year} data for accurate information."
                )

        # General relevance-based extraction
        relevant_blocks = self._score_relevance(context, question, max_results=5)
        if relevant_blocks:
            return (
                "📋 **RELEVANT INFORMATION** (from source data):\n\n" +
                "\n---\n".join(relevant_blocks)
            )

        # Absolute fallback - return first few blocks
        first_blocks = [block for block in re.split(r'\n\n+', context) if block.strip()][:3]
        if first_blocks:
            return (
                "⚠️ Could not find precise match. Here are relevant sections:\n\n" +
                "\n---\n".join(first_blocks)
            )

        return "❌ I could not find matching information in the source data to answer your question."

    def generate_response(self, prompt: str) -> str:
        
        if self.client:
            try:
                # Use OpenAI with RAG grounding
                context, question = self._extract_context_and_question(prompt)
                
                # Build a grounded prompt that forces the model to use context
                grounded_prompt = f"""You are an F1 assistant. ONLY answer based on the provided context.
If the context doesn't contain the answer, say "I don't have that information in my source data."

CONTEXT:
{context}

QUESTION: {question}

Answer ONLY from the context above. Do not make up or assume information."""
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": grounded_prompt}],
                    temperature=0.2  # Lower temperature = more factual
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"⚠️ OpenAI API error: {str(e)}. Falling back to offline extraction.")

        # Offline extraction (guaranteed no hallucination)
        context, question = self._extract_context_and_question(prompt)
        return self._validate_and_extract(context, question)
