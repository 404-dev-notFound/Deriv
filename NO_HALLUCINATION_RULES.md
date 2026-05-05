# No-Hallucination Rules Applied to All Prompts

## Overview

All LLM prompts in Stages 1-6 now include explicit anti-hallucination rules to ensure the LLM:
- Extracts ONLY information from the email thread
- Does NOT invent, assume, or speculate
- Grounds every claim in specific email citations
- Respects the scope and boundaries of the thread

---

## Stage 1: facts_and_decisions_extracted.py

**Rules Added**:
```
- Extract ONLY information explicitly stated or directly referenced in the emails.
- DO NOT hallucinate or invent decisions, risks, blockers, or questions not in the thread.
- Every item MUST be grounded in at least one email_id citation.
- If you cannot find clear evidence for something, exclude it.
- Do not assume information not present in the email content.
- Only include decisions explicitly made or clearly implied from email statements.
```

---

## Stage 2: actions_items_extracted.py

**Rules Added**:
```
- Extract ONLY actions explicitly mentioned or clearly implied in the emails.
- DO NOT hallucinate or invent actions not discussed in the thread.
- Every action MUST cite email_id_sources where it was identified.
- Do not assume future actions or goals not stated in the emails.
- Only include deadlines explicitly mentioned in the thread.
- Do not add implied deadlines - use null if not stated.
- Owners must be actual people/roles mentioned in the thread.
- Do not invent ownership or assignments not present in the emails.
```

---

## Stage 3: conflicts_identified.py

**Rules Added**:
```
- Identify ONLY conflicts explicitly present or clearly evident in the thread.
- DO NOT hallucinate or invent tensions, reversals, or dependencies not in the emails.
- Every conflict MUST cite email_id_sources showing evidence.
- "why_it_matters" must explain actual consequences described in the thread.
- Do not speculate about potential conflicts or future issues.
- Do not infer conflicts not directly stated or strongly implied.
- Each conflict must be grounded in specific email statements or exchanges.
```

---

## Stage 4: follow_ups_drafted.py

**Rules Added**:
```
- Ground ALL drafts ONLY in facts, decisions, and actions from the extracted data.
- DO NOT hallucinate commitments, timelines, or details not in the thread.
- DO NOT make promises on behalf of teams unless explicitly discussed.
- DO NOT invent implementation details, technical decisions, or solutions not mentioned.
- Every claim in drafts must be traceable to specific emails.
- Do not add false reassurances or implied guarantees.
- Stick to facts: decisions made, actions assigned, risks identified, next steps discussed.
- Priya MUST explicitly address the 5k req/min SLA - do not minimize or omit it.
```

---

## Stage 6 (Optional): optional_analyses_generated.py

### Decision Log Prompt:
```
- Only document decisions EXPLICITLY present in the extracted facts.
- DO NOT invent, assume, or hallucinate decisions not mentioned.
- "basis" must cite actual reasoning stated in the emails.
- Do not add your own interpretation of why decisions were made.
- "open_question_if_any" can only reference questions actually in the thread.
- Every decision must be grounded in email_id_sources.
```

### Health Score Prompt:
```
- Base scores ONLY on what is observable in the provided email summary.
- DO NOT hallucinate or assume behaviors not evidenced.
- "evidence" must reference actual emails, not opinions or assumptions.
- Do not infer hidden problems or implied issues.
- Scores should reflect ACTUAL clarity, velocity, acknowledgement, quality from the thread.
- Do not score generously based on best practices - score based on actual behavior in the thread.
```

### Missing Stakeholders Prompt:
```
- Identify ONLY missing stakeholders based on topics ACTUALLY discussed in the thread.
- DO NOT hallucinate missing roles or invent stakeholders you guess might be needed.
- "why_needed" must reference actual topics from the thread that concern that role.
- Only include stakeholders whose expertise is directly relevant to decisions/actions/risks in the thread.
- Do not add every possible stakeholder - only those whose absence creates a genuine gap.
- "briefing" must be based only on facts, decisions, and risks from the extracted data.
```

---

## Implementation Approach

### Each prompt now includes:

1. **CRITICAL RULES section** at the top:
   - Lists what NOT to do (no hallucination, no invention)
   - Specifies what CAN be included (only email content)
   - Defines how to ground claims (email citations)

2. **Grounding requirements**:
   - Every extracted item must cite `email_id_sources`
   - Evidence must be traceable to specific emails
   - Assumptions must be minimal or excluded

3. **Scope boundaries**:
   - No invention of commitments, timelines, people, or roles
   - No speculation about future issues
   - No inference of information not stated
   - No adding your own reasoning or interpretation

4. **Validation at output**:
   - All email_id citations are validated
   - Invalid citations cause pipeline failure
   - Ensures compliance is checked immediately

---

## Files Modified

✅ STAGES/facts_and_decisions_extracted.py
✅ STAGES/actions_items_extracted.py
✅ STAGES/conflicts_identified.py
✅ STAGES/follow_ups_drafted.py
✅ STAGES/optional_analyses_generated.py

---

## Testing

To test that hallucination rules are working:

1. **Check LLM responses** - Verify responses only cite emails that exist
2. **Validate email_id citations** - All EMAIL_X references must be in parsed_thread.json
3. **Review extracted content** - Ensure no invented decisions, actions, or conflicts
4. **Check follow-up drafts** - Verify Priya's draft addresses the actual SLA, Sarah's mentions real decisions, James's has only discussed scope

---

## Example: What Changed

### BEFORE (Generic prompt):
```
Extract decisions from the email thread.
Output JSON with decision_text, made_by, confidence.
```

### AFTER (Anti-hallucination):
```
Extract ONLY decisions explicitly stated or directly referenced in emails.
DO NOT hallucinate or invent decisions not in the thread.
Every decision MUST cite email_id_sources.
Only include decisions explicitly made or clearly implied from email statements.
```

---

## Impact

- **Eliminates false extractions** - LLM won't invent decisions/actions not in emails
- **Ensures traceability** - Every claim is grounded in specific emails
- **Maintains accuracy** - Only real content from the thread is extracted
- **Passes evaluation** - Evaluator can verify claims by checking email citations
