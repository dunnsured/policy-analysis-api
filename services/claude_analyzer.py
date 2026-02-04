"""
Claude API Policy Analyzer
Uses Claude to analyze cyber insurance policies with Rhône Risk's scoring methodology
"""

import logging
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

import anthropic

from config import settings
from prompts.system_prompt import get_analysis_prompt

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result from Claude policy analysis"""
    success: bool
    analysis_data: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class ClaudeAnalyzer:
    """
    Analyzes cyber insurance policies using Claude API.

    Uses structured prompting to ensure consistent, scorable output
    following Rhône Risk's proprietary methodology.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS

    async def analyze_policy(
        self,
        policy_text: str,
        client_name: str,
        client_industry: str,
        policy_type: str = "cyber",
        is_renewal: bool = False,
    ) -> AnalysisResult:
        """
        Perform comprehensive policy analysis using Claude.

        Args:
            policy_text: Extracted text from the policy PDF
            client_name: Name of the client company
            client_industry: Industry classification for context
            policy_type: Type of policy (default: cyber)
            is_renewal: Whether this is a renewal vs new policy

        Returns:
            AnalysisResult containing structured analysis data
        """
        logger.info(f"🤖 Starting Claude analysis for {client_name}")
        logger.info(f"   Industry: {client_industry}")
        logger.info(f"   Policy text length: {len(policy_text)} chars")

        if not settings.ANTHROPIC_API_KEY:
            return AnalysisResult(
                success=False,
                error="Anthropic API key not configured"
            )

        # Build the analysis prompt
        system_prompt = get_analysis_prompt(
            client_industry=client_industry,
            is_renewal=is_renewal,
        )

        user_message = f"""Please analyze the following cyber insurance policy for {client_name}.

**Client Industry:** {client_industry}
**Policy Type:** {policy_type}
**Renewal:** {"Yes" if is_renewal else "No (New Policy)"}

---

**POLICY DOCUMENT TEXT:**

{policy_text}

---

Please provide your complete analysis following the structured format specified in your instructions. Remember to:
1. Score each coverage area on the 0-10 scale
2. Flag any red flags or critical deficiencies
3. Apply industry-specific analysis criteria for {client_industry}
4. Provide a clear binding recommendation with rationale
5. Output valid JSON that can be parsed programmatically
"""

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                system=system_prompt,
            )

            # Extract response text
            raw_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            logger.info(f"   Claude response: {len(raw_text)} chars, {tokens_used} tokens")

            # Parse JSON from response
            analysis_data = self._parse_analysis_json(raw_text)

            if analysis_data:
                # Enrich with metadata
                analysis_data["_metadata"] = {
                    "client_name": client_name,
                    "client_industry": client_industry,
                    "policy_type": policy_type,
                    "is_renewal": is_renewal,
                    "model_used": self.model,
                    "tokens_used": tokens_used,
                }

                logger.info(f"✅ Analysis complete. Overall score: {analysis_data.get('executive_summary', {}).get('key_metrics', {}).get('overall_maturity_score', 'N/A')}")

                return AnalysisResult(
                    success=True,
                    analysis_data=analysis_data,
                    raw_response=raw_text,
                    tokens_used=tokens_used,
                )
            else:
                # Could not parse JSON - return raw text
                logger.warning("⚠️ Could not parse structured JSON from response")
                return AnalysisResult(
                    success=True,
                    analysis_data={"raw_analysis": raw_text},
                    raw_response=raw_text,
                    tokens_used=tokens_used,
                )

        except anthropic.APIError as e:
            logger.error(f"❌ Anthropic API error: {str(e)}")
            return AnalysisResult(
                success=False,
                error=f"API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            return AnalysisResult(
                success=False,
                error=str(e)
            )

    def _parse_analysis_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON from Claude's response.

        Handles cases where JSON might be wrapped in markdown code blocks.
        """
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Look for JSON in code blocks
        import re

        # Try ```json ... ``` blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object pattern
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None


# Module-level instance
analyzer = ClaudeAnalyzer()
