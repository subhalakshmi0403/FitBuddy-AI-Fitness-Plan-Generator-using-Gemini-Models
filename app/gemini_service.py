import json
import re
from typing import Any

from google import genai
from google.genai import types

from .config import settings


class GeminiService:
    """
    Service class responsible for communication with Google Gemini.
    """

    def __init__(self):

        self.client = None

        if settings.GEMINI_API_KEY:

            self.client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

    @property
    def is_configured(self) -> bool:

        return self.client is not None

    def _generate(
        self,
        prompt: str,
        model: str,
        json_output: bool = False,
        max_output_tokens: int = 5000,
    ) -> str:

        if not self.client:

            raise RuntimeError(
                "Gemini API key is not configured."
            )

        config: dict[str, Any] = {
            "temperature": 0.7,
            "max_output_tokens": max_output_tokens,
        }

        if json_output:

            config["response_mime_type"] = (
                "application/json"
            )

        response = self.client.models.generate_content(

            model=model,

            contents=prompt,

            config=types.GenerateContentConfig(
                **config
            ),
        )

        text = (
            response.text or ""
        ).strip()

        if not text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return text

    @staticmethod
    def _clean_json(text: str) -> str:

        text = text.strip()

        text = re.sub(
            r"^```json\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"^```\s*",
            "",
            text,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        return text.strip()

    # ---------------------------------------------------------
    # WORKOUT PLAN
    # ---------------------------------------------------------

    def generate_workout(
        self,
        username: str,
        age: int,
        weight: float,
        goal: str,
        intensity: str,
    ) -> str:

        prompt = f"""
You are FitBuddy, an AI fitness planning assistant.

Create a personalized 7-day fitness plan.

User information:

Name: {username}
Age: {age}
Weight: {weight} kg
Fitness goal: {goal}
Workout intensity: {intensity}

Return VALID JSON ONLY.

Use exactly this structure:

{{
    "summary": "short plan overview",

    "days": [
        {{
            "day": "Day 1",
            "focus": "workout focus",

            "warmup": "5-10 minute warmup",

            "exercises": [
                {{
                    "name": "exercise name",
                    "sets": "3",
                    "reps_or_duration": "10 reps",
                    "rest": "60 seconds"
                }}
            ],

            "cooldown": "cooldown or recovery guidance"
        }}
    ],

    "safety_note": "short safety note"
}}

Important requirements:

1. Include exactly 7 days.
2. Include warm-up guidance.
3. Include main exercises.
4. Include sets and repetitions or duration.
5. Include rest periods.
6. Include cooldown/recovery guidance.
7. Adapt the plan to the fitness goal.
8. Adapt the plan to the selected intensity.
9. Include reasonable recovery.
10. Do not diagnose medical conditions.
11. Do not prescribe medication.
12. Do not promise guaranteed results.
13. Keep the plan practical and understandable.
"""

        if not self.is_configured:

            return self._fallback_plan(
                username,
                goal,
                intensity,
            )

        try:

            response = self._generate(
                prompt=prompt,
                model=settings.GEMINI_WORKOUT_MODEL,
                json_output=True,
                max_output_tokens=7000,
            )

            parsed = json.loads(
                self._clean_json(response)
            )

            return json.dumps(
                parsed,
                indent=2,
                ensure_ascii=False,
            )

        except Exception:

            return self._fallback_plan(
                username,
                goal,
                intensity,
            )

    # ---------------------------------------------------------
    # NUTRITION TIP
    # ---------------------------------------------------------

    def generate_nutrition_tip(
        self,
        goal: str,
    ) -> str:

        prompt = f"""
Give one concise nutrition or recovery tip.

Fitness goal:

{goal}

Requirements:

- 2-4 sentences.
- Practical.
- General wellness advice.
- Mention balanced nutrition, hydration,
  protein, fiber, sleep, or recovery where appropriate.
- Do not diagnose medical conditions.
- Do not prescribe medication.
- Do not recommend dangerous dieting.
"""

        if not self.is_configured:

            return self._fallback_tip(
                goal
            )

        try:

            return self._generate(
                prompt=prompt,
                model=settings.GEMINI_FAST_MODEL,
                max_output_tokens=300,
            )

        except Exception:

            return self._fallback_tip(
                goal
            )

    # ---------------------------------------------------------
    # UPDATE PLAN
    # ---------------------------------------------------------

    def update_workout_plan(
        self,
        original_plan: str,
        feedback: str,
        goal: str,
        intensity: str,
    ) -> str:

        prompt = f"""
You are updating a FitBuddy 7-day workout plan.

Fitness goal:

{goal}

Workout intensity:

{intensity}

Original workout plan:

{original_plan}

User feedback:

{feedback}

Create an improved 7-day plan.

Return VALID JSON ONLY.

Use this structure:

{{
    "summary": "short description of changes",

    "days": [
        {{
            "day": "Day 1",
            "focus": "workout focus",

            "warmup": "warm-up",

            "exercises": [
                {{
                    "name": "exercise name",
                    "sets": "3",
                    "reps_or_duration": "10 reps",
                    "rest": "60 seconds"
                }}
            ],

            "cooldown": "cooldown"
        }}
    ],

    "safety_note": "short safety note"
}}

Requirements:

1. Exactly 7 days.
2. Apply the user's feedback where appropriate.
3. Maintain balanced recovery.
4. Keep the selected intensity in mind.
5. Keep the original fitness goal.
6. Do not diagnose medical conditions.
7. Do not prescribe medication.
8. Do not promise guaranteed results.
"""

        if not self.is_configured:

            return self._fallback_updated_plan(
                original_plan,
                feedback,
            )

        try:

            response = self._generate(
                prompt=prompt,
                model=settings.GEMINI_WORKOUT_MODEL,
                json_output=True,
                max_output_tokens=7000,
            )

            parsed = json.loads(
                self._clean_json(response)
            )

            return json.dumps(
                parsed,
                indent=2,
                ensure_ascii=False,
            )

        except Exception:

            return self._fallback_updated_plan(
                original_plan,
                feedback,
            )

    # ---------------------------------------------------------
    # FALLBACK PLAN
    # ---------------------------------------------------------

    @staticmethod
    def _fallback_plan(
        username: str,
        goal: str,
        intensity: str,
    ) -> str:

        sets = {
            "low": "2",
            "medium": "3",
            "high": "3-4",
        }.get(
            intensity.lower(),
            "3",
        )

        days = [

            (
                "Day 1",
                "Full Body Strength",
                [
                    "Bodyweight Squat",
                    "Incline Push-up",
                    "Glute Bridge",
                ],
            ),

            (
                "Day 2",
                "Cardio and Core",
                [
                    "Brisk Walking",
                    "Dead Bug",
                    "Bird Dog",
                ],
            ),

            (
                "Day 3",
                "Upper Body",
                [
                    "Incline Push-up",
                    "Resistance Band Row",
                    "Shoulder Press",
                ],
            ),

            (
                "Day 4",
                "Recovery",
                [
                    "Easy Walking",
                    "Mobility Flow",
                    "Gentle Stretching",
                ],
            ),

            (
                "Day 5",
                "Lower Body",
                [
                    "Squat",
                    "Reverse Lunge",
                    "Calf Raise",
                ],
            ),

            (
                "Day 6",
                "Cardio and Core",
                [
                    "Cycling or Brisk Walking",
                    "Plank",
                    "Dead Bug",
                ],
            ),

            (
                "Day 7",
                "Recovery and Mobility",
                [
                    "Easy Walking",
                    "Hip Mobility",
                    "Full Body Stretching",
                ],
            ),
        ]

        plan = {

            "summary":
                f"Demo-mode fitness plan for {username} "
                f"focused on {goal} at {intensity} intensity.",

            "days": [],

            "safety_note":
                "Start comfortably and use controlled form. "
                "Stop if you experience pain, dizziness, or "
                "unusual symptoms. Seek qualified professional "
                "guidance for injuries or medical conditions.",
        }

        for day_name, focus, exercises in days:

            day = {

                "day": day_name,

                "focus": focus,

                "warmup":
                    "5-10 minutes of easy movement "
                    "and dynamic mobility.",

                "exercises": [],

                "cooldown":
                    "5-10 minutes of easy movement "
                    "and gentle stretching.",
            }

            for exercise in exercises:

                day["exercises"].append({

                    "name": exercise,

                    "sets": sets,

                    "reps_or_duration":
                        "8-12 reps or 30-60 seconds",

                    "rest":
                        "60-90 seconds",
                })

            plan["days"].append(day)

        return json.dumps(
            plan,
            indent=2,
        )

    # ---------------------------------------------------------
    # FALLBACK UPDATE
    # ---------------------------------------------------------

    @staticmethod
    def _fallback_updated_plan(
        original_plan: str,
        feedback: str,
    ) -> str:

        try:

            data = json.loads(
                original_plan
            )

            data["summary"] = (
                data.get(
                    "summary",
                    "",
                )
                + " Updated using user feedback: "
                + feedback
            )

            return json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            )

        except json.JSONDecodeError:

            return (
                original_plan
                + "\n\nUPDATED FROM FEEDBACK:\n"
                + feedback
            )

    # ---------------------------------------------------------
    # FALLBACK NUTRITION TIP
    # ---------------------------------------------------------

    @staticmethod
    def _fallback_tip(
        goal: str,
    ) -> str:

        goal_lower = goal.lower()

        if (
            "muscle" in goal_lower
            or "strength" in goal_lower
        ):

            return (
                "Include a protein-rich food in each main "
                "meal along with vegetables, whole-food "
                "carbohydrates, and adequate fluids. "
                "Consistent sleep and recovery are also "
                "important for supporting training."
            )

        if (
            "loss" in goal_lower
            or "fat" in goal_lower
        ):

            return (
                "Build meals around vegetables, a protein "
                "source, high-fiber carbohydrates, and "
                "minimally processed foods. Focus on "
                "sustainable habits rather than aggressive "
                "restriction and stay hydrated."
            )

        return (
            "Aim for balanced meals containing a protein "
            "source, vegetables or fruit, whole-food "
            "carbohydrates, and healthy fats. Stay hydrated "
            "and allow your body enough time to recover "
            "between challenging sessions."
        )


gemini_service = GeminiService()