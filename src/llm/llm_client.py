import os
import re
from typing import Optional

class OpenAIEngine:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        self.model = model
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("Warning: openai package is not installed. Falling back to offline local engine.")
        else:
            print("Warning: OPENAI_API_KEY not found. Using offline local engine response generation.")

    def _extract_context_and_question(self, prompt: str) -> tuple[str, str]:
        start_marker = "[VERIFIED DATABASE CONTEXT]"
        end_marker = "[USER QUESTION]"
        if start_marker in prompt and end_marker in prompt:
            context = prompt.split(start_marker)[1].split(end_marker)[0].strip()
            question = prompt.split(end_marker)[1].strip()
            return context, question
        return prompt, ""

    def _contains_keyword(self, text: str, keywords: list[str]) -> bool:
        return any(re.search(r"\b" + re.escape(keyword) + r"\b", text, re.I) for keyword in keywords)

    def _find_relevant_lines(self, text: str, keywords: list[str]) -> list[str]:
        lines = [line.strip() for line in re.split(r"\n", text) if line.strip()]
        matches = [line for line in lines if self._contains_keyword(line, keywords)]
        return matches

    def _find_general_matches(self, text: str, question: str, max_results: int = 5) -> list[str]:
        query_tokens = [token for token in re.findall(r"\w+", question.lower()) if len(token) > 3]
        lines = [line.strip() for line in re.split(r"\n", text) if line.strip()]
        scored = []
        for line in lines:
            score = sum(1 for token in query_tokens if re.search(r"\b" + re.escape(token) + r"\b", line, re.I))
            if score > 0:
                scored.append((score, line))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [line for _, line in scored[:max_results]]

    def _summarize_from_context(self, context: str, question: str) -> str:
        question_lower = question.lower()
        if not context:
            return "🤖 [LOCAL ENGINE]: No retrieved context was available to answer the question."

        weather_keywords = ["weather", "sunny", "cloud", "rain", "forecast", "temperature", "precipitation"]
        tyre_keywords = ["tyre", "tire", "compound", "soft", "medium", "hard", "pit", "pit stop", "strategy"]
        result_keywords = ["result", "podium", "finished", "won", "winner", "position", "points", "race"]
        pole_keywords = ["pole", "qualifying", "grid", "pole position"]
        lap_keywords = ["lap", "fastest", "laptime", "lap time", "pace"]

        year_match = re.search(r"\b(20[2-9]\d)\b", question_lower)
        if year_match:
            year = year_match.group(1)
            year_lines = [line for line in context.splitlines() if year in line]
            if year_lines:
                context = "\n".join(year_lines)
            elif year == "2026":
                return (
                    "🤖 [LOCAL ENGINE]: The scraped page is about the 2025 Spanish Grand Prix and does not contain 2026 predictions or results. "
                    "Please ingest a 2026-specific source for that information."
                )

        if any(keyword in question_lower for keyword in ["weather", "forecast", "temperature", "precipitation", "sunny", "rain"]):
            weather_lines = self._find_relevant_lines(context, weather_keywords)
            if weather_lines:
                return (
                    "Weather information found in the retrieved content:\n\n"
                    + "\n".join(weather_lines[:3])
                )
            return "🤖 [LOCAL ENGINE]: I could not find specific weather forecast information in the retrieved page."

        if any(keyword in question_lower for keyword in ["tyre", "tire", "compound", "pit", "strategy"]):
            tyre_lines = self._find_relevant_lines(context, tyre_keywords)
            if tyre_lines:
                return (
                    "Tyre strategy information found in the retrieved content:\n\n"
                    + "\n".join(tyre_lines[:4])
                )
            return "🤖 [LOCAL ENGINE]: I could not find specific tyre strategy information in the retrieved page."

        if any(keyword in question_lower for keyword in ["result", "podium", "finished", "won", "winner", "position"]):
            result_lines = self._find_relevant_lines(context, result_keywords)
            if result_lines:
                return (
                    "Race result information from the retrieved content:\n\n"
                    + "\n".join(result_lines[:5])
                )

        if any(keyword in question_lower for keyword in ["pole", "qualifying", "grid"]):
            pole_lines = self._find_relevant_lines(context, pole_keywords)
            if pole_lines:
                return (
                    "Pole position / qualifying information from the retrieved content:\n\n"
                    + "\n".join(pole_lines[:5])
                )

        if any(keyword in question_lower for keyword in ["lap", "fastest", "laptime", "pace"]):
            lap_lines = self._find_relevant_lines(context, lap_keywords)
            if lap_lines:
                return (
                    "Lap time and pace information from the retrieved content:\n\n"
                    + "\n".join(lap_lines[:5])
                )

        general_matches = self._find_general_matches(context, question)
        if general_matches:
            return (
                "I found the following relevant snippets from the scraped content:\n\n"
                + "\n".join(general_matches)
            )

        top_lines = [line.strip() for line in context.splitlines() if line.strip()][:5]
        if top_lines:
            return (
                "🤖 [LOCAL ENGINE]: I could not find a precise answer in the retrieved page. "
                "Here are the most relevant snippets:\n\n"
                + "\n".join(top_lines)
            )

        return "🤖 [LOCAL ENGINE]: The retrieved context did not contain usable information for this query."

    def generate_response(self, prompt: str) -> str:
        """Sends the prompt to OpenAI if possible; otherwise uses a local fallback."""
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Error contacting OpenAI API: {str(e)}"

        context, question = self._extract_context_and_question(prompt)
        return self._summarize_from_context(context, question)
