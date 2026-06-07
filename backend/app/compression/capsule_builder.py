"""
Capsule Builder — compresses a conversation into a MemoryCapsule.
The compression engine is the core product moat.
Phase 1: rule-based extraction + optional LLM summarization.
"""
import json
import structlog
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.memory_capsule import MemoryCapsule
from app.compression.metrics import CompressionMetrics
from app.extraction.entity_extractor import EntityExtractor
from pydantic import BaseModel, Field

logger = structlog.get_logger()

# Keywords that suggest architectural decisions or important insights
DECISION_KEYWORDS = [
    "decided", "decision", "chose", "we'll use", "going with", "approach",
    "instead of", "rather than", "because", "therefore", "conclusion",
    "architecture", "design", "pattern", "should use", "must",
]

INSIGHT_KEYWORDS = [
    "important", "note:", "warning:", "issue:", "problem:", "solution",
    "discovered", "realized", "found that", "turns out", "bug",
    "fixed", "resolved",
]

class CapsuleExtractionSchema(BaseModel):
    """Pydantic schema for structured LLM extraction."""
    summary: str = Field(description="Condensed narrative summary of the workflow")
    decisions: list[str] = Field(description="Specific architectural choices made", default_factory=list)
    insights: list[str] = Field(description="Key realizations or discovered bugs", default_factory=list)
    unresolved_issues: list[str] = Field(description="Remaining tasks or open questions", default_factory=list)
    constraints: list[str] = Field(description="Hard limits like 'must be localhost-only'", default_factory=list)
    entities: list[str] = Field(description="Technologies, services, or frameworks mentioned", default_factory=list)
    risks: list[str] = Field(description="Identified risks or potential failure points", default_factory=list)
    assumptions: list[str] = Field(description="Assumptions made during the workflow", default_factory=list)
    action_items: list[str] = Field(description="Specific items that need to be acted upon", default_factory=list)
    requirements: list[str] = Field(description="Stated requirements for the project/feature", default_factory=list)
    
    quality_score: float = Field(description="Self-assessed extraction quality 1.0-10.0", default=5.0)
    confidence_score: float = Field(description="Confidence in extraction accuracy 0.0-1.0", default=0.5)


class CapsuleBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_from_conversation(
        self,
        conversation_id,
        use_llm: bool = False,
    ) -> tuple[Optional[MemoryCapsule], Optional[CompressionMetrics]]:
        """
        Build a MemoryCapsule from a conversation.
        Phase 1: rule-based extraction.
        Phase 2+: LLM-powered summarization when use_llm=True.
        """
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        conversation = result.scalars().first()

        if not conversation or not conversation.messages:
            return None, None

        log = logger.bind(conversation_id=str(conversation_id))

        # Sort messages by position
        messages = sorted(conversation.messages, key=lambda m: m.position)
        assistant_messages = [m for m in messages if m.role == "assistant"]

        if not assistant_messages:
            log.warning("no_assistant_messages_for_capsule")
            return None, None

        # Extract title
        title = conversation.title or "Untitled Conversation"

        if use_llm:
            # Phase 2: LLM Structured Extraction
            extraction = await self._run_llm_extraction(messages)
            summary = extraction.summary
            decisions = extraction.decisions
            insights = extraction.insights
            unresolved = extraction.unresolved_issues
            constraints = extraction.constraints
            
            # Hybrid Entity Extraction
            deterministic_entities = EntityExtractor.extract_deterministic_entities(" ".join([m.content for m in messages]))
            entities = EntityExtractor.merge_entities(deterministic_entities, extraction.entities)
            
            # Remove duplicates and validate outputs
            decisions = list(dict.fromkeys(extraction.decisions))
            insights = list(dict.fromkeys(extraction.insights))
            unresolved = list(dict.fromkeys(extraction.unresolved_issues))
            constraints = list(dict.fromkeys(extraction.constraints))
            risks = list(dict.fromkeys(extraction.risks))
            assumptions = list(dict.fromkeys(extraction.assumptions))
            action_items = list(dict.fromkeys(extraction.action_items))
            requirements = list(dict.fromkeys(extraction.requirements))

            # Phase 4: Composite Confidence Scoring
            # 20%: LLM Self-Assessment
            # 20%: Entity Density & Consistency
            # 30%: Source Coverage
            # 30%: Output Completeness
            llm_conf = (extraction.confidence_score) * 0.20
            
            # Entity consistency: Do LLM entities overlap with deterministic ones?
            llm_entities_set = set(e.lower() for e in extraction.entities)
            det_entities_set = set(e.lower() for e in deterministic_entities)
            overlap = len(llm_entities_set.intersection(det_entities_set))
            entity_score = (overlap / max(1, len(det_entities_set))) * 0.20 if det_entities_set else 0.20
            
            # Source Coverage proxy: Are we extracting decisions proportional to the conversation length?
            decision_density = len(decisions) / max(1, len(messages))
            source_coverage = min(decision_density * 5, 1.0) * 0.30
            
            # Completeness
            fields_populated = sum([
                1 if summary else 0,
                1 if decisions else 0,
                1 if insights else 0,
                1 if unresolved else 0,
                1 if constraints else 0,
                1 if entities else 0,
                1 if risks else 0,
                1 if assumptions else 0,
                1 if action_items else 0,
                1 if requirements else 0
            ])
            completeness = (fields_populated / 10.0) * 0.30
            
            composite_confidence = round(llm_conf + entity_score + source_coverage + completeness, 2)
            
            quality = extraction.quality_score / 10.0
            confidence = composite_confidence
            importance = quality
        else:
            # Phase 1 Fallback: Rule-based extraction
            summary = self._build_summary(messages)
            decisions = self._extract_decisions(assistant_messages)
            insights = self._extract_insights(assistant_messages)
            unresolved = []
            constraints = []
            entities = EntityExtractor.extract_deterministic_entities(" ".join([m.content for m in messages]))
            importance = self._score_importance(messages, decisions, insights)
            quality = importance * 10.0
            confidence = 1.0

        capsule = MemoryCapsule(
            project_id=conversation.project_id,
            conversation_id=conversation.id,
            title=title,
            summary=summary,
            decisions=json.dumps(decisions) if decisions else None,
            insights=json.dumps(insights) if insights else None,
            unresolved_issues=unresolved if unresolved else None,
            constraints=constraints if constraints else None,
            entities=entities if entities else None,
            risks=risks if use_llm and risks else None,
            assumptions=assumptions if use_llm and assumptions else None,
            action_items=action_items if use_llm and action_items else None,
            requirements=requirements if use_llm and requirements else None,
            importance_score=importance,
            quality_score=quality,
            confidence_score=confidence,
            source_model=None,  # Could be extracted from source metadata
        )
        self.db.add(capsule)

        # Update conversation status
        conversation.status = "compressed"
        conversation.summary = summary[:300]

        await self.db.commit()
        await self.db.refresh(capsule)

        original_tokens = sum((m.token_count or (len(m.content) // 4)) for m in messages)
        compressed_tokens = (len(title) + len(summary) + len(json.dumps(decisions)) + len(json.dumps(insights))) // 4

        metrics = CompressionMetrics(
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            compression_ratio=original_tokens / max(1, compressed_tokens),
            decision_count=len(decisions),
            insight_count=len(insights),
            quality_score=importance,
        )

        log.info("capsule_built", capsule_id=str(capsule.id), importance=importance, ratio=metrics.compression_ratio)
        return capsule, metrics

    async def _run_llm_extraction(self, messages: list) -> CapsuleExtractionSchema:
        """
        Execute LLM call to extract structured intelligence using Instructor.
        """
        from app.embeddings.factory import get_ai_provider
        provider = get_ai_provider()
        
        logger.info("llm_extraction_triggered", msg_count=len(messages))
        
        # Build prompt
        transcript = "\n".join([f"{m.role.upper()}: {m.content}" for m in messages])
        
        prompt = f"""
You are an expert system architect analyzing a developer workflow conversation.
Extract the intelligence, reasoning, and context from this transcript.
Strictly adhere to the following rules:
1. Minimize hallucination. Prefer omission over invention.
2. Require evidence-backed outputs. If a decision wasn't explicitly made, do not infer it.
3. Be highly concise but technically precise.

Transcript:
{transcript}
"""
        
        try:
            extraction = await provider.generate_structured(
                prompt=prompt,
                response_model=CapsuleExtractionSchema
            )
            return extraction
        except Exception as e:
            logger.error("llm_extraction_failed", error=str(e))
            # Fallback
            return CapsuleExtractionSchema(
                summary=f"Failed to extract structured summary due to API error: {str(e)}",
            )

    def _build_summary(self, messages: list) -> str:
        """
        Build a structured markdown summary from the conversation.
        Provides a much cleaner UI presentation.
        """
        parts = ["### Original Context\n"]

        # First user message = the task/question
        user_msgs = [m for m in messages if m.role == "user"]
        if user_msgs:
            first_user = user_msgs[0].content[:500]
            parts.append(f"> {first_user}...\n")

        parts.append("### High-Level AI Response\n")
        
        # Grab first and last assistant messages to bound the summary
        assistant_msgs = [m for m in messages if m.role == "assistant"]
        if assistant_msgs:
            first_ai = assistant_msgs[0].content[:400].strip()
            parts.append(f"**Initial Response:**\n{first_ai}...\n")
            
            if len(assistant_msgs) > 1:
                last_ai = assistant_msgs[-1].content[:400].strip()
                parts.append(f"**Final Conclusion:**\n{last_ai}...")

        return "\n".join(parts)

    def _extract_decisions(self, assistant_messages: list) -> list[str]:
        """Extract sentences containing decision keywords."""
        decisions = []
        for msg in assistant_messages:
            sentences = msg.content.split(".")
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(kw in sentence_lower for kw in DECISION_KEYWORDS):
                    cleaned = sentence.strip()
                    if len(cleaned) > 20:
                        decisions.append(cleaned)
        return decisions[:10]  # Cap at 10

    def _extract_insights(self, assistant_messages: list) -> list[str]:
        """Extract sentences containing insight keywords."""
        insights = []
        for msg in assistant_messages:
            sentences = msg.content.split(".")
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(kw in sentence_lower for kw in INSIGHT_KEYWORDS):
                    cleaned = sentence.strip()
                    if len(cleaned) > 20:
                        insights.append(cleaned)
        return insights[:10]

    def _score_importance(self, messages: list, decisions: list, insights: list) -> float:
        """
        Score the importance of this capsule from 0.0 to 1.0.
        Factors: message count, decisions found, insights found.
        """
        score = 0.3  # Base score
        score += min(len(messages) / 50, 0.3)   # More messages = more content
        score += min(len(decisions) / 10, 0.2)   # Decisions increase importance
        score += min(len(insights) / 10, 0.2)    # Insights increase importance
        return round(min(score, 1.0), 2)
