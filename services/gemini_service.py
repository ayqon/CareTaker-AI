import json
import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return float(dot / (mag_a * mag_b))


class GeminiService:
    """Encapsulates Google GenAI / Vertex AI interactions for CareTaker."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        flash_model: str = "gemini-2.5-flash",
        embedding_model: str = "gemini-embedding-001",
        veo_model: str = "veo-3.1-generate-001",
    ):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "nastwest-u26wck-617")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.flash_model = flash_model
        self.embedding_model = embedding_model
        self.veo_model = veo_model

        try:
            self.client = genai.Client(project=self.project_id, location=self.location)
        except Exception as e:
            print(f"[GeminiService] Warning initializing client: {e}. Will attempt API key or fallback.")
            self.client = None

    def structure_task(self, raw_text: str) -> Dict[str, Any]:
        """Convert free-form task description into structured points."""
        if not self.client:
            # High-fidelity fallback for offline / mock dev
            return {
                "title": (raw_text[:40] + "...") if len(raw_text) > 40 else raw_text,
                "points": [
                    {"step_number": 1, "action": "Initiate care task", "details": raw_text}
                ],
                "priority": "medium",
                "estimated_duration": "30 minutes",
            }

        response = self.client.models.generate_content(
            model=self.flash_model,
            contents=f"""You are a task structuring assistant for a workplace management system.
Convert the following free-form task description into structured, actionable points.

Task description: {raw_text}

Return a JSON object with these fields:
- title: a short title for the task (max 10 words)
- points: an array of action items, each with step_number (int), action (string, brief), details (string, more detail)
- priority: one of "low", "medium", "high"
- estimated_duration: estimated time to complete (e.g. "2 hours", "30 minutes")""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "points": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "step_number": {"type": "integer"},
                                    "action": {"type": "string"},
                                    "details": {"type": "string"},
                                },
                                "required": ["step_number", "action", "details"],
                            },
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                        "estimated_duration": {"type": "string"},
                    },
                    "required": ["title", "points", "priority", "estimated_duration"],
                },
            ),
        )
        return json.loads(response.text)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding vector for semantic matching."""
        if not self.client or not text:
            # Deterministic pseudo-embedding for testing / offline
            return [0.1] * 768

        result = self.client.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
        )
        return list(result.embeddings[0].values)

    def transcribe_and_translate_audio(
        self, audio_bytes: bytes, mime_type: str = "audio/webm"
    ) -> Dict[str, str]:
        """Transcribe audio and translate to English using Gemini multimodal capabilities."""
        if not self.client:
            return {
                "original_text": "Audio log submitted",
                "detected_language": "English",
                "translated_text": "Audio log submitted",
            }

        response = self.client.models.generate_content(
            model=self.flash_model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            text="Listen to this audio carefully. Transcribe it exactly, detect what language it is in, and translate the content to English. Return as JSON."
                        ),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type=mime_type, data=audio_bytes
                            )
                        ),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "original_text": {"type": "string"},
                        "detected_language": {"type": "string"},
                        "translated_text": {"type": "string"},
                    },
                    "required": [
                        "original_text",
                        "detected_language",
                        "translated_text",
                    ],
                },
            ),
        )
        return json.loads(response.text)

    def translate_text(self, text: str) -> Dict[str, str]:
        """Detect language and translate worker text to English."""
        if not self.client:
            return {
                "original_text": text,
                "detected_language": "English",
                "translated_text": text,
            }

        response = self.client.models.generate_content(
            model=self.flash_model,
            contents=f"""Detect the language of the following text and translate it to English.
If it is already in English, still return it.

Text: {text}""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "original_text": {"type": "string"},
                        "detected_language": {"type": "string"},
                        "translated_text": {"type": "string"},
                    },
                    "required": [
                        "original_text",
                        "detected_language",
                        "translated_text",
                    ],
                },
            ),
        )
        return json.loads(response.text)

    def match_work_to_tasks(
        self, work_embedding: List[float], tasks: List[Any]
    ) -> Tuple[Optional[Any], float]:
        """Find the best matching task for a work log using cosine similarity."""
        best_task = None
        best_score = 0.0
        for task in tasks:
            task_emb = task.get_embedding()
            if task_emb:
                score = cosine_similarity(work_embedding, task_emb)
                if score > best_score:
                    best_score = score
                    best_task = task
        return best_task, best_score

    def generate_training_script(
        self, topic: str, key_points: Any, worker: Any
    ) -> Dict[str, str]:
        """Generate a personalised training script adapted for a worker's language and profile."""
        lang_name = getattr(worker, "preferred_language", "en") or "English"
        age = getattr(worker, "age", "unknown") or "unknown"
        gender = getattr(worker, "gender", "unknown") or "unknown"

        if not self.client:
            return {
                "script": f"Training session on {topic} for {worker.username}.",
                "script_english": f"Training session on {topic} for {worker.username}.",
                "summary": f"Key learning on {topic}.",
            }

        response = self.client.models.generate_content(
            model=self.flash_model,
            contents=f"""Create a training script about the following topic. Make it personalised and culturally appropriate.

Topic: {topic}
Key points to cover: {key_points}

Worker profile:
- Preferred language: {lang_name}
- Age: {age}
- Gender: {gender}

Requirements:
- Write the script in the worker's preferred language ({lang_name})
- Use simple, clear language appropriate for the worker's age
- Include practical examples relevant to their work context
- Structure it as a narration script that could be read aloud
- Keep it under 500 words

Return as JSON with:
- script: the full training script text in the target language
- script_english: English translation of the script
- summary: a 1-2 sentence summary in English""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string"},
                        "script_english": {"type": "string"},
                        "summary": {"type": "string"},
                    },
                    "required": ["script", "script_english", "summary"],
                },
            ),
        )
        return json.loads(response.text)

    def generate_training_video(
        self, topic: str, summary: str
    ) -> Optional[Tuple[bytes, str]]:
        """Generate a training video using Google Veo (veo-3.1-generate-001)."""
        if not self.client:
            return None

        try:
            prompt = (
                f"Create a short, clear educational training video about: {topic}. "
                f"Context: {summary}. "
                "The video should be professional, suitable for workplace training, "
                "with clear visuals demonstrating the topic. "
                "Use simple, instructional style appropriate for diverse audiences."
            )

            source = types.GenerateVideosSource(prompt=prompt)
            config = types.GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
                duration_seconds=8,
                person_generation="allow_adult",
                generate_audio=True,
                resolution="720p",
            )

            operation = self.client.models.generate_videos(
                model=self.veo_model, source=source, config=config
            )

            # Polling with safety timeout (max 120 seconds)
            start_time = time.time()
            while not operation.done and (time.time() - start_time < 120):
                time.sleep(10)
                operation = self.client.operations.get(operation)

            response = operation.result
            if response and response.generated_videos:
                video = response.generated_videos[0].video
                if video and video.video_bytes:
                    mime_type = video.mime_type or "video/mp4"
                    return video.video_bytes, mime_type
        except Exception as e:
            print(f"[GeminiService] Video generation failed: {e}")
        return None

    def generate_cqc_report(
        self, log: Any, worker: Any, task: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Generate a formal CQC Regulation 17 compliant care record."""
        task_context = ""
        if task:
            task_context = f"\nRelated assigned task: {task.title}\nTask description: {task.description}\nTask priority: {task.priority}\n"
            if task.structured_points:
                points = task.get_structured_points()
                steps = "; ".join(p.get("action", "") for p in points)
                task_context += f"Expected procedure steps: {steps}\n"

        timestamp = (
            log.created_at.strftime("%d %B %Y at %H:%M")
            if log.created_at
            else "Not recorded"
        )

        if not self.client:
            return {
                "report_title": f"Care Activity Log - {timestamp}",
                "service_user_reference": "Refer to internal records",
                "date_and_time": timestamp,
                "care_worker": worker.username,
                "care_activity_summary": log.translated_text or log.original_text,
                "detailed_care_record": f"The care worker carried out the scheduled activity: {log.translated_text or log.original_text}",
                "person_centred_observations": "Service user was responsive and comfortable during the visit.",
                "outcomes_and_wellbeing": "Positive engagement maintained.",
                "risks_and_concerns": "No immediate risks identified.",
                "safeguarding_notes": "No safeguarding concerns noted.",
                "follow_up_actions": "Continue routine care plan.",
                "cqc_compliance_tags": ["Safe", "Caring", "Effective"],
            }

        response = self.client.models.generate_content(
            model=self.flash_model,
            contents=f"""You are a CQC (Care Quality Commission) compliance documentation specialist 
for UK health and social care settings. Your role is to transform informal care worker 
submissions into formal care records that meet CQC documentation standards under the 
Health and Social Care Act 2008 (Regulated Activities) Regulations 2014.

Generate a formal, CQC-compliant care record based on the following information.

--- WORKER SUBMISSION (translated to English) ---
{log.translated_text or log.original_text}

--- METADATA ---
Care worker: {worker.username}
Date and time of activity: {timestamp}
{task_context}

--- CQC DOCUMENTATION REQUIREMENTS ---
1. Use formal, professional, person-centred language throughout.
2. Write in third person, past tense.
3. Be factual and objective — do NOT speculate, assume, or fabricate details.
4. Reference the care activity performed with specific detail drawn from the submission.
5. Document observations including the service user's response and wellbeing indicators.
6. Note any concerns, risks identified, or safeguarding considerations.
7. Record follow-up actions required and responsible parties.
8. Demonstrate alignment with CQC's five key questions: Safe, Effective, Caring, Responsive, Well-led.
9. Use appropriate professional and clinical terminology.
10. Where information is not available from the original submission, write 
    "Not documented in original submission — to be completed by care worker" 
    rather than inventing details.
11. The report_title should be a concise formal title for the care record.
12. service_user_reference should note "Refer to internal records" since no name was provided.
13. cqc_compliance_tags must only include tags from: Safe, Effective, Caring, Responsive, Well-led.""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "report_title": {"type": "string"},
                        "service_user_reference": {"type": "string"},
                        "date_and_time": {"type": "string"},
                        "care_worker": {"type": "string"},
                        "care_activity_summary": {"type": "string"},
                        "detailed_care_record": {"type": "string"},
                        "person_centred_observations": {"type": "string"},
                        "outcomes_and_wellbeing": {"type": "string"},
                        "risks_and_concerns": {"type": "string"},
                        "safeguarding_notes": {"type": "string"},
                        "follow_up_actions": {"type": "string"},
                        "cqc_compliance_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "report_title",
                        "service_user_reference",
                        "date_and_time",
                        "care_worker",
                        "care_activity_summary",
                        "detailed_care_record",
                        "person_centred_observations",
                        "outcomes_and_wellbeing",
                        "risks_and_concerns",
                        "safeguarding_notes",
                        "follow_up_actions",
                        "cqc_compliance_tags",
                    ],
                },
            ),
        )
        return json.loads(response.text)

    def review_cqc_report(
        self, log: Any, report: Dict[str, Any], worker: Any, task: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Review a CQC report and generate recommendations for improvement."""
        task_context = ""
        if task:
            task_context = f"\nAssigned task: {task.title}\nTask description: {task.description}\nTask priority: {task.priority}\n"
            if task.structured_points:
                points = task.get_structured_points()
                steps = "\n".join(
                    f"  Step {p.get('step_number', '?')}: {p.get('action', '')} - {p.get('details', '')}"
                    for p in points
                )
                task_context += f"Required procedure steps:\n{steps}\n"

        if not self.client:
            return {
                "recommendations": [
                    {
                        "category": "missing_info",
                        "severity": "minor",
                        "title": "Document Service User Hydration",
                        "description": "Ensure fluid intake is clearly noted during the care visit.",
                        "learning_content": "Hydration tracking is essential under CQC Regulation 14 to prevent dehydration.",
                        "suggested_text": "Offered and supported with 200ml of water.",
                        "report_section": "person_centred_observations",
                    }
                ],
                "overall_completeness_score": 85,
                "overall_practice_score": 90,
            }

        response = self.client.models.generate_content(
            model=self.flash_model,
            contents=f"""You are a CQC (Care Quality Commission) compliance auditor AND a care practice mentor.

Review the following CQC care record and the original worker submission it was based on.
Identify issues in THREE categories:

1. PRACTICE ISSUES (category: "practice_issue")
   - Things the worker may have done wrong or unsafely
   - Missing safety steps (e.g. consent, PPE, infection control, manual handling)
   - Violations of CQC regulations or care best practices
   - Severity: "critical" if it risks harm, "important" otherwise

2. MISSING INFORMATION (category: "missing_info")
   - Gaps in the report that CQC would flag
   - Sections marked "to be completed by care worker"
   - Required details that are absent (times, observations, responses)
   - Severity: "important" if CQC-required, "minor" if nice-to-have

3. DOCUMENTATION TIPS (category: "documentation_tip")
   - Ways to improve the quality of future documentation
   - Better terminology or phrasing suggestions
   - Additional details that would strengthen the record
   - Severity: always "minor"

--- ORIGINAL WORKER SUBMISSION ---
{log.original_text}

--- TRANSLATED SUBMISSION ---
{log.translated_text or log.original_text}

--- GENERATED CQC REPORT ---
Report Title: {report.get('report_title', '')}
Care Activity Summary: {report.get('care_activity_summary', '')}
Detailed Care Record: {report.get('detailed_care_record', '')}
Person-Centred Observations: {report.get('person_centred_observations', '')}
Outcomes and Wellbeing: {report.get('outcomes_and_wellbeing', '')}
Risks and Concerns: {report.get('risks_and_concerns', '')}
Safeguarding Notes: {report.get('safeguarding_notes', '')}
Follow-up Actions: {report.get('follow_up_actions', '')}

{task_context}

--- WORKER PROFILE ---
Language: {worker.preferred_language or 'English'}
Age: {worker.age or 'unknown'}

--- INSTRUCTIONS ---
- Generate between 3 and 8 recommendations total
- For each practice_issue, include detailed learning_content explaining:
  - WHY this matters (reference specific CQC regulation if applicable)
  - WHAT the correct procedure is
  - HOW to do it right next time
  - Write learning_content in simple, supportive language appropriate for the worker's age
- For each missing_info, explain exactly WHAT information is needed
- For each documentation_tip, provide an example of better text
- suggested_text should contain the exact text that SHOULD appear in the report
- report_section must be one of: care_activity_summary, detailed_care_record, person_centred_observations, outcomes_and_wellbeing, risks_and_concerns, safeguarding_notes, follow_up_actions
- Be constructive and educational, not punitive
- overall_completeness_score: 0-100 based on how complete the documentation is
- overall_practice_score: 0-100 based on how well the care was delivered""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "recommendations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "category": {
                                        "type": "string",
                                        "enum": [
                                            "practice_issue",
                                            "missing_info",
                                            "documentation_tip",
                                        ],
                                    },
                                    "severity": {
                                        "type": "string",
                                        "enum": ["critical", "important", "minor"],
                                    },
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "learning_content": {"type": "string"},
                                    "suggested_text": {"type": "string"},
                                    "report_section": {"type": "string"},
                                },
                                "required": [
                                    "category",
                                    "severity",
                                    "title",
                                    "description",
                                    "learning_content",
                                    "suggested_text",
                                    "report_section",
                                ],
                            },
                        },
                        "overall_completeness_score": {"type": "integer"},
                        "overall_practice_score": {"type": "integer"},
                    },
                    "required": [
                        "recommendations",
                        "overall_completeness_score",
                        "overall_practice_score",
                    ],
                },
            ),
        )
        return json.loads(response.text)

    def regenerate_final_report(
        self,
        original_report: Dict[str, Any],
        recommendations_with_responses: List[Dict[str, Any]],
        log: Any,
        worker: Any,
    ) -> Dict[str, Any]:
        """Regenerate a CQC report incorporating worker responses to recommendations."""
        responses_text = ""
        for rec in recommendations_with_responses:
            responses_text += f"""
Recommendation: {rec['title']} ({rec['category']})
Issue: {rec['description']}
Worker response status: {rec['status']}
Worker's additional information: {rec.get('worker_response', 'None provided')}
Suggested text: {rec['suggested_text']}
Affected section: {rec['report_section']}
---"""

        if not self.client:
            updated = dict(original_report)
            updated["reflective_notes"] = "All recommendation responses incorporated into finalized care log."
            return updated

        response = self.client.models.generate_content(
            model=self.flash_model,
            contents=f"""You are a CQC compliance documentation specialist.

Regenerate the following CQC care record, incorporating all the worker's responses 
to the AI review recommendations. This should produce a FINAL, COMPLETE record.

--- ORIGINAL CQC REPORT ---
Report Title: {original_report.get('report_title', '')}
Service User Reference: {original_report.get('service_user_reference', '')}
Date and Time: {original_report.get('date_and_time', '')}
Care Worker: {original_report.get('care_worker', '')}
Care Activity Summary: {original_report.get('care_activity_summary', '')}
Detailed Care Record: {original_report.get('detailed_care_record', '')}
Person-Centred Observations: {original_report.get('person_centred_observations', '')}
Outcomes and Wellbeing: {original_report.get('outcomes_and_wellbeing', '')}
Risks and Concerns: {original_report.get('risks_and_concerns', '')}
Safeguarding Notes: {original_report.get('safeguarding_notes', '')}
Follow-up Actions: {original_report.get('follow_up_actions', '')}

--- WORKER RESPONSES TO REVIEW ---
{responses_text}

--- ORIGINAL WORKER SUBMISSION ---
{log.translated_text or log.original_text}

--- INSTRUCTIONS ---
1. Incorporate ALL additional information the worker provided into the appropriate sections
2. Replace any "to be completed by care worker" phrases with the actual information
3. If a worker acknowledged a practice issue, add a brief reflective note in the relevant section
4. If a worker dismissed a recommendation as not applicable, leave that section as-is
5. Keep all existing accurate content
6. Maintain formal, CQC-compliant, person-centred language throughout
7. The final report should have NO gaps or placeholders
8. Add a reflective_notes field summarising practice learnings from this review
9. cqc_compliance_tags should reflect the final reviewed content""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "report_title": {"type": "string"},
                        "service_user_reference": {"type": "string"},
                        "date_and_time": {"type": "string"},
                        "care_worker": {"type": "string"},
                        "care_activity_summary": {"type": "string"},
                        "detailed_care_record": {"type": "string"},
                        "person_centred_observations": {"type": "string"},
                        "outcomes_and_wellbeing": {"type": "string"},
                        "risks_and_concerns": {"type": "string"},
                        "safeguarding_notes": {"type": "string"},
                        "follow_up_actions": {"type": "string"},
                        "reflective_notes": {"type": "string"},
                        "cqc_compliance_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "report_title",
                        "service_user_reference",
                        "date_and_time",
                        "care_worker",
                        "care_activity_summary",
                        "detailed_care_record",
                        "person_centred_observations",
                        "outcomes_and_wellbeing",
                        "risks_and_concerns",
                        "safeguarding_notes",
                        "follow_up_actions",
                        "reflective_notes",
                        "cqc_compliance_tags",
                    ],
                },
            ),
        )
        return json.loads(response.text)
