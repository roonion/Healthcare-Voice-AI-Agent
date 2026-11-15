"""
Test scenarios: Memory continuity.

5 scenarios testing the agent's ability to remember returning patients,
handle mid-call dropouts, and maintain context across sessions.
"""

SCENARIOS = [
    {
        "id": "memory_01_returning_patient",
        "description": "Patient calls back after previous visit — agent should remember",
        "prior_memory": {
            "patient_name": "Maria Garcia",
            "caller_phone": "+15551234567",
            "previous_visits": [
                {
                    "date": "2026-04-10",
                    "complaint": "right knee pain after jogging",
                    "allergies": ["sulfa drugs"],
                    "medications": ["lisinopril"],
                    "triage": "routine",
                }
            ],
        },
        "opening_message": "Hi, I'm calling back. I came in about my knee last week but it's gotten worse.",
        "expected_outputs": {
            "should_greet_by_name": True,
            "should_reference_previous_visit": True,
            "should_know_allergies": True,
        },
    },
    {
        "id": "memory_02_add_allergy",
        "description": "Returning patient adds new allergy information",
        "prior_memory": {
            "patient_name": "James Chen",
            "caller_phone": "+15559876543",
            "previous_visits": [
                {
                    "date": "2026-04-08",
                    "complaint": "persistent headaches",
                    "allergies": [],
                    "medications": ["metformin", "atorvastatin"],
                }
            ],
        },
        "opening_message": "Hi, I called earlier this week about headaches. I forgot to mention — I found out I'm allergic to ibuprofen.",
        "expected_outputs": {
            "should_reference_headache_visit": True,
            "should_record_new_allergy": True,
            "updated_allergies": ["ibuprofen"],
        },
    },
    {
        "id": "memory_03_dropped_call_resume",
        "description": "Call dropped mid-intake — patient calls back to resume",
        "prior_memory": {
            "patient_name": "Robert Williams",
            "caller_phone": "+15552468000",
            "previous_visits": [
                {
                    "date": "2026-04-14",
                    "complaint": "lower back pain",
                    "partial_intake": True,
                    "collected_so_far": {
                        "demographics": True,
                        "chief_complaint": True,
                        "medications": False,
                        "allergies": False,
                    },
                }
            ],
        },
        "opening_message": "Hi, sorry — we got disconnected. I was in the middle of telling you about my back pain.",
        "expected_outputs": {
            "should_acknowledge_disconnection": True,
            "should_resume_from_medications": True,
            "should_not_re_ask_demographics": True,
        },
    },
    {
        "id": "memory_04_multiple_visits",
        "description": "Patient with multiple prior visits — comprehensive memory",
        "prior_memory": {
            "patient_name": "Aisha Johnson",
            "caller_phone": "+15553691215",
            "previous_visits": [
                {
                    "date": "2026-02-15",
                    "complaint": "annual physical",
                    "allergies": ["penicillin"],
                    "medications": ["birth control"],
                },
                {
                    "date": "2026-03-20",
                    "complaint": "sinus infection",
                    "prescribed": "azithromycin",
                },
            ],
        },
        "opening_message": "Hi, I'm calling because I'm having stomach problems.",
        "expected_outputs": {
            "should_greet_by_name": True,
            "should_know_allergy_to_penicillin": True,
            "should_know_current_medication": True,
        },
    },
    {
        "id": "memory_05_preference_recall",
        "description": "Agent remembers patient communication preferences",
        "prior_memory": {
            "patient_name": "Harold Peters",
            "caller_phone": "+15557778888",
            "previous_visits": [
                {
                    "date": "2026-04-07",
                    "complaint": "shoulder pain",
                    "notes": "Patient prefers afternoon appointments. Speak slowly — hard of hearing.",
                }
            ],
        },
        "opening_message": "Hello? Is this the doctor's office? I need to come back in about my shoulder.",
        "expected_outputs": {
            "should_greet_by_name": True,
            "should_reference_shoulder": True,
            "scheduling_should_prefer_afternoon": True,
        },
    },
]
