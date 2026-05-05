"""
Pydantic models for all data structures.
These ensure type safety and validation of all extracted data.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# Email Models
# ============================================================================

class Email(BaseModel):
    """Represents a single parsed email."""
    email_id: str = Field(..., description="Unique email identifier (EMAIL_1, EMAIL_2, etc.)")
    from_: str = Field(..., alias="from", description="Sender email address")
    to: List[str] = Field(..., description="List of recipient email addresses")
    date: str = Field(..., description="Date/time of email")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body text")
    reply_to_inferred: Optional[str] = Field(None, description="Inferred reply-to email_id")

    class Config:
        populate_by_name = True


class ParsedThread(BaseModel):
    """Complete parsed email thread."""
    emails: List[Email] = Field(..., description="All parsed emails")
    conversation_graph: Optional[dict] = Field(None, description="Reply chain graph")
    subthreads: Optional[List[dict]] = Field(None, description="Identified sub-threads")


# ============================================================================
# Stage 1 Models: Facts & Decisions
# ============================================================================

class ConfidenceLevel(str, Enum):
    CONFIRMED = "confirmed"
    IMPLIED = "implied"
    ASSUMED = "assumed"


class Decision(BaseModel):
    """Decision extracted from email thread."""
    decision_id: str = Field(..., description="Unique decision identifier")
    decision_text: str = Field(..., description="What was decided")
    made_by: str = Field(..., description="Who made the decision")
    date: str = Field(..., description="When decision was made")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")
    email_id_sources: List[str] = Field(..., description="Supporting email IDs")

    @validator('email_id_sources')
    def validate_email_ids(cls, v):
        if not v:
            raise ValueError("email_id_sources must not be empty")
        return v


class RiskSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Risk(BaseModel):
    """Risk identified in email thread."""
    risk_id: str = Field(..., description="Unique risk identifier")
    risk_text: str = Field(..., description="Description of the risk")
    raised_by: str = Field(..., description="Who raised this risk")
    severity: RiskSeverity = Field(..., description="Risk severity level")
    email_id_sources: List[str] = Field(..., description="Supporting email IDs")

    @validator('email_id_sources')
    def validate_email_ids(cls, v):
        if not v:
            raise ValueError("email_id_sources must not be empty")
        return v


class OpenQuestion(BaseModel):
    """Unresolved question from email thread."""
    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="The question")
    related_emails: List[str] = Field(..., description="Related email IDs")


class Blocker(BaseModel):
    """Blocker preventing progress."""
    blocker_id: str = Field(..., description="Unique blocker identifier")
    blocker: str = Field(..., description="What is blocking progress")
    impact: str = Field(..., description="Impact of the blocker")
    email_id_sources: List[str] = Field(..., description="Supporting email IDs")

    @validator('email_id_sources')
    def validate_email_ids(cls, v):
        if not v:
            raise ValueError("email_id_sources must not be empty")
        return v


class FactsAndDecisions(BaseModel):
    """Stage 1 output: All extracted facts and decisions."""
    decisions: List[Decision] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    open_questions: List[OpenQuestion] = Field(default_factory=list)
    blockers: List[Blocker] = Field(default_factory=list)


# ============================================================================
# Stage 2 Models: Action Items
# ============================================================================

class ActionStatus(str, Enum):
    CONFIRMED = "confirmed"
    REQUESTED = "requested"
    IMPLIED = "implied"
    COMPLETED = "completed"
    PENDING = "pending"


class ActionItem(BaseModel):
    """Action item extracted from email thread."""
    action_id: str = Field(..., description="Unique action identifier")
    owner: str = Field(..., description="Person or role responsible")
    action: str = Field(..., description="Description of the action")
    deadline_if_stated: Optional[str] = Field(None, description="Deadline if mentioned")
    status: ActionStatus = Field(..., description="Current status of action")
    email_id_sources: List[str] = Field(..., description="Supporting email IDs")
    completion_email_id: Optional[str] = Field(None, description="Email ID where completed")

    @validator('email_id_sources')
    def validate_email_ids(cls, v):
        if not v:
            raise ValueError("email_id_sources must not be empty")
        return v


class ActionItems(BaseModel):
    """Stage 2 output: All extracted action items."""
    action_items: List[ActionItem] = Field(default_factory=list)


# ============================================================================
# Stage 3 Models: Conflicts
# ============================================================================

class ConflictType(str, Enum):
    INTERPERSONAL_TENSION = "interpersonal_tension"
    UNRESOLVED_DEPENDENCY = "unresolved_dependency"
    DECISION_REVERSAL = "decision_reversal"
    UNADDRESSED_RISK = "unaddressed_risk"
    BLOCKED_ACTION = "blocked_action"


class Conflict(BaseModel):
    """Conflict or tension identified in email thread."""
    conflict_id: str = Field(..., description="Unique conflict identifier")
    type: ConflictType = Field(..., description="Type of conflict")
    description: str = Field(..., description="Description of the conflict")
    severity: RiskSeverity = Field(..., description="Severity level")
    email_id_sources: List[str] = Field(..., description="Supporting email IDs")
    why_it_matters: str = Field(..., description="Why this conflict matters")

    @validator('email_id_sources')
    def validate_email_ids(cls, v):
        if not v:
            raise ValueError("email_id_sources must not be empty")
        return v


class Conflicts(BaseModel):
    """Stage 3 output: All identified conflicts."""
    conflicts: List[Conflict] = Field(default_factory=list)


# ============================================================================
# Stage 4 Models: Follow-up Drafts
# ============================================================================

class FollowUpDraft(BaseModel):
    """Draft follow-up communication."""
    draft_id: str = Field(..., description="Unique draft identifier")
    recipient: str = Field(..., description="Intended recipient")
    from_: str = Field(..., alias="from", description="Sender name")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body text")
    grounded_in_email_ids: List[str] = Field(..., description="Supporting email IDs")
    key_constraints_addressed: List[str] = Field(..., description="Key constraints addressed")

    @validator('grounded_in_email_ids')
    def validate_email_ids(cls, v):
        if not v:
            raise ValueError("grounded_in_email_ids must not be empty")
        return v

    class Config:
        populate_by_name = True


class FollowUpDrafts(BaseModel):
    """Stage 4 output: All follow-up drafts."""
    follow_up_drafts: List[FollowUpDraft] = Field(default_factory=list)


# ============================================================================
# Stage 5 Models: Executive Summary
# ============================================================================

class ExecutiveSummary(BaseModel):
    """Stage 5 output: Executive summary."""
    summary_type: str = Field(default="executive")
    generated_deterministically: bool = Field(default=True)
    sections: dict = Field(..., description="Summary sections")


# ============================================================================
# Stage 6 Models: Optional Analyses
# ============================================================================

class DecisionLogEntry(BaseModel):
    """Decision log entry."""
    decision_id: str
    date: str
    decision_text: str
    made_by: str
    basis: str
    open_question_if_any: Optional[str]
    email_id_sources: List[str]


class DecisionLog(BaseModel):
    """Stage 6 optional output: Decision log."""
    decisions: List[DecisionLogEntry] = Field(default_factory=list)


class HealthScoreDimension(BaseModel):
    """Single health score dimension."""
    score: int = Field(..., ge=1, le=5, description="Score 1-5")
    evidence: str = Field(..., description="Evidence from thread")


class ThreadHealthScore(BaseModel):
    """Stage 6 optional output: Thread health score."""
    clarity_of_ownership: HealthScoreDimension
    decision_velocity: HealthScoreDimension
    risk_acknowledgement: HealthScoreDimension
    communication_quality: HealthScoreDimension
    overall_health: int = Field(..., ge=1, le=5)
    summary: str


class MissingStakeholder(BaseModel):
    """Missing stakeholder identification."""
    role: str = Field(..., description="Role/team name")
    why_needed: str = Field(..., description="Why needed based on thread")
    relevant_topics: List[str] = Field(..., description="Relevant topics from thread")
    briefing: str = Field(..., description="What they need to know")


class MissingStakeholders(BaseModel):
    """Stage 6 optional output: Missing stakeholders."""
    missing_stakeholders: List[MissingStakeholder] = Field(default_factory=list)


# ============================================================================
# LLM Call Log Models
# ============================================================================

class LLMCallLog(BaseModel):
    """Log entry for each LLM call."""
    stage: str = Field(..., description="Pipeline stage")
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    provider: str = Field(..., description="LLM provider (anthropic/openrouter)")
    model: str = Field(..., description="Model name/ID")
    prompt_hash: str = Field(..., description="SHA256 hash of prompt")
    input_artifacts: List[str] = Field(..., description="Input files used")
    output_artifact: str = Field(..., description="Output file generated")
    status: str = Field(default="success", description="Call status")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Pipeline State Models
# ============================================================================

class PipelineState(BaseModel):
    """Current pipeline state."""
    current_stage: str = Field(..., description="Current stage name")
    completed_stages: List[str] = Field(default_factory=list, description="Completed stages")
    failed_stages: List[str] = Field(default_factory=list, description="Failed stages")
    artifacts: dict = Field(default_factory=dict, description="Generated artifacts")
    llm_calls: int = Field(default=0, description="Number of LLM calls made")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
