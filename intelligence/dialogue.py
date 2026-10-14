"""
Jan-Vani Guided Voice Dialogue Engine.
Enforces dialogue state machine and template-based spoken replies:
- Replies reflect the citizen's own speech while spoken text stays strictly controlled.
- Templates are loaded from config/templates/<language>.json.
- Placeholders ({problem}, {place}, {duration}) are filled ONLY with values the citizen said
  or mapped from approved category list.
- Rules:
  - GREETING, THANKS, HELP, UNCLEAR, OFF_TOPIC: reply with fixed template. Create NO ticket.
  - COMPLAINT: if fields are missing, ask for one missing field at a time (max two questions).
    If all fields present, go to CONFIRM.
  - CONFIRM: read back filled template. Accept only YES or NO intents.
  - CORRECTION: update named field, then confirm again.
  - Never create a ticket from GREETING, THANKS, HELP, UNCLEAR, OFF_TOPIC, or empty transcript.
- Stores original transcript, intent, and extracted fields for every turn.
"""

import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from intelligence.intent import classify_intent
from intelligence.intent_schema import (
    IntentClassificationResult,
    ExtractedFields,
    DialogueTurnRecord,
    IntentType,
    APPROVED_CATEGORIES
)

TEMPLATES_DIR = Path(__file__).parent.parent / "config" / "templates"

class DialogueState:
    IDLE = "IDLE"
    GATHERING = "GATHERING"
    CONFIRM = "CONFIRM"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class GuidedDialogueSession:
    """
    Maintains dialogue state for a citizen across conversational turns.
    """
    def __init__(self, session_id: Optional[str] = None, language: str = "mr"):
        self.session_id = session_id or str(uuid.uuid4())
        self.language = language if language in ["mr", "hi", "en"] else "mr"
        self.state = DialogueState.IDLE
        self.fields: Dict[str, Optional[str]] = {
            "problem_category": None,
            "sub_category": None,
            "problem": None,
            "place": None,
            "duration": None
        }
        self.questions_asked = 0  # Max 2 clarification questions for complaints
        self.turns: List[DialogueTurnRecord] = []
        self.ticket_id: Optional[str] = None
        self._load_templates()

    def _load_templates(self):
        tmpl_file = TEMPLATES_DIR / f"{self.language}.json"
        if not tmpl_file.exists():
            tmpl_file = TEMPLATES_DIR / "mr.json"
        with open(tmpl_file, "r", encoding="utf-8") as f:
            self.templates = json.load(f)

    def set_language(self, language: str):
        if language in ["mr", "hi", "en"] and language != self.language:
            self.language = language
            self._load_templates()

    def _render_template(self, key: str, **kwargs) -> str:
        text = self.templates.get(key, "")
        # Safely fill kwargs without inserting None
        clean_kwargs = {k: (v if v is not None else "") for k, v in kwargs.items()}
        try:
            return text.format(**clean_kwargs)
        except Exception:
            return text

    def _build_confirm_reply(self) -> str:
        problem = self.fields.get("problem") or "नागरी समस्या"
        place = self.fields.get("place")
        duration = self.fields.get("duration")

        if place and duration:
            return self._render_template("confirm_full", problem=problem, place=place, duration=duration)
        elif place and not duration:
            return self._render_template("confirm_no_duration", problem=problem, place=place)
        elif duration and not place:
            return self._render_template("confirm_no_place", problem=problem, duration=duration)
        else:
            return self._render_template("confirm_problem_only", problem=problem)

    def process_turn(
        self,
        transcript: str,
        ward_name: str = "Dharampeth (Ward 02)",
        latitude: float = 21.1458,
        longitude: float = 79.0882
    ) -> Dict[str, Any]:
        """
        Executes one dialogue turn with the citizen.
        Returns:
            intent: strict intent classified
            spoken_reply: template-rendered controlled reply
            ticket_created: True only if CONFIRM -> YES
            ticket_id: JV- ticket ID if created, else None
            state: current dialogue state
            turns: complete turn history with transcript, intent, extracted fields
        """
        state_before = self.state
        clean_transcript = (transcript or "").strip()

        # Step 1: Strict Intent Classification
        classification = classify_intent(clean_transcript, self.language)
        intent = classification.intent
        extracted = classification.fields

        spoken_reply = ""
        ticket_created = False

        # Rule: Never create a ticket from GREETING, THANKS, HELP, UNCLEAR, OFF_TOPIC, or empty transcript
        if not clean_transcript:
            spoken_reply = self._render_template("unclear")

        elif intent == "GREETING":
            spoken_reply = self._render_template("greeting")

        elif intent == "THANKS":
            spoken_reply = self._render_template("thanks")

        elif intent == "HELP":
            spoken_reply = self._render_template("help")

        elif intent == "OFF_TOPIC":
            spoken_reply = self._render_template("off_topic")

        # In GATHERING state, the citizen is providing a requested missing field (place or duration)
        elif self.state == DialogueState.GATHERING and intent in ["UNCLEAR", "COMPLAINT"]:
            if extracted.place:
                self.fields["place"] = extracted.place
            elif not self.fields["place"] and clean_transcript:
                self.fields["place"] = clean_transcript

            if extracted.duration:
                self.fields["duration"] = extracted.duration
            elif not self.fields["duration"] and any(w in clean_transcript for w in ["दिवस", "दिन", "काल", "कल", "days", "आठवड्यापासून"]):
                self.fields["duration"] = clean_transcript

            # Check if next question is needed (max 2 questions total)
            if not self.fields["place"] and self.questions_asked < 2:
                self.questions_asked += 1
                spoken_reply = self._render_template("ask_place")
            elif not self.fields["duration"] and self.questions_asked < 2:
                self.questions_asked += 1
                spoken_reply = self._render_template("ask_duration")
            else:
                self.state = DialogueState.CONFIRM
                spoken_reply = self._build_confirm_reply()

        elif intent == "UNCLEAR":
            spoken_reply = self._render_template("unclear")

        # In CONFIRM state, accept only YES, NO, or CORRECTION
        elif self.state == DialogueState.CONFIRM:
            if intent == "YES":
                self.state = DialogueState.COMPLETED
                ticket_created = True
                self.ticket_id = f"JV-2026-{uuid.uuid4().hex[:6].upper()}"
                problem = self.fields.get("problem") or "नागरी समस्या"
                spoken_reply = self._render_template(
                    "ticket_created",
                    problem=problem,
                    ward=ward_name,
                    ticket_id=self.ticket_id
                )
            elif intent == "NO":
                self.state = DialogueState.CANCELLED
                spoken_reply = self._render_template("cancelled")
            elif intent == "CORRECTION":
                # Update corrected fields
                if extracted.place:
                    self.fields["place"] = extracted.place
                if extracted.duration:
                    self.fields["duration"] = extracted.duration
                if extracted.problem:
                    self.fields["problem"] = extracted.problem
                if extracted.problem_category:
                    self.fields["problem_category"] = extracted.problem_category

                self.state = DialogueState.CONFIRM
                spoken_reply = self._build_confirm_reply()
            else:
                # Still in confirm, re-prompt strictly for confirmation
                spoken_reply = self._build_confirm_reply()

        elif intent == "CORRECTION":
            # Update fields
            if extracted.place:
                self.fields["place"] = extracted.place
            if extracted.duration:
                self.fields["duration"] = extracted.duration
            if extracted.problem:
                self.fields["problem"] = extracted.problem
            if extracted.problem_category:
                self.fields["problem_category"] = extracted.problem_category

            self.state = DialogueState.CONFIRM
            spoken_reply = self._build_confirm_reply()

        elif intent == "COMPLAINT":
            # Update known fields from complaint
            if extracted.problem_category:
                self.fields["problem_category"] = extracted.problem_category
            if extracted.sub_category:
                self.fields["sub_category"] = extracted.sub_category
            if extracted.problem:
                self.fields["problem"] = extracted.problem
            if extracted.place:
                self.fields["place"] = extracted.place
            if extracted.duration:
                self.fields["duration"] = extracted.duration

            # Check for missing fields: ask for one missing field at a time (max 2 questions)
            if not self.fields["place"] and self.questions_asked < 2:
                self.questions_asked += 1
                self.state = DialogueState.GATHERING
                spoken_reply = self._render_template("ask_place")
            elif not self.fields["duration"] and self.questions_asked < 2:
                self.questions_asked += 1
                self.state = DialogueState.GATHERING
                spoken_reply = self._render_template("ask_duration")
            else:
                # All fields present, or max 2 questions reached -> go to CONFIRM
                self.state = DialogueState.CONFIRM
                spoken_reply = self._build_confirm_reply()

        elif self.state == DialogueState.GATHERING:
            # We asked a follow-up question (place or duration)
            if extracted.place:
                self.fields["place"] = extracted.place
            elif not self.fields["place"] and clean_transcript:
                # Citizen just said place name directly
                self.fields["place"] = clean_transcript

            if extracted.duration:
                self.fields["duration"] = extracted.duration
            elif not self.fields["duration"] and any(w in clean_transcript for w in ["दिवस", "दिन", "काल", "कल", "days"]):
                self.fields["duration"] = clean_transcript

            # Check if next question is needed (max 2 questions total)
            if not self.fields["place"] and self.questions_asked < 2:
                self.questions_asked += 1
                spoken_reply = self._render_template("ask_place")
            elif not self.fields["duration"] and self.questions_asked < 2:
                self.questions_asked += 1
                spoken_reply = self._render_template("ask_duration")
            else:
                self.state = DialogueState.CONFIRM
                spoken_reply = self._build_confirm_reply()

        else:
            # Fallback
            spoken_reply = self._render_template("unclear")

        # Step 2: Record turn in history
        turn_record = DialogueTurnRecord(
            turn_id=len(self.turns) + 1,
            transcript=clean_transcript,
            intent=intent,
            extracted_fields=self.fields.copy(),
            spoken_reply=spoken_reply,
            state_before=state_before,
            state_after=self.state,
            ticket_created=ticket_created,
            ticket_id=self.ticket_id
        )
        self.turns.append(turn_record)

        return {
            "session_id": self.session_id,
            "intent": intent,
            "confidence": classification.confidence,
            "spoken_reply": spoken_reply,
            "ticket_created": ticket_created,
            "ticket_id": self.ticket_id,
            "state": self.state,
            "extracted_fields": self.fields.copy(),
            "turn_count": len(self.turns),
            "history": [t.model_dump() for t in self.turns]
        }
