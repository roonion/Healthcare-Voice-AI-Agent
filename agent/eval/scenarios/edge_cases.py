"""
Test scenarios: Edge cases.

5 scenarios covering non-English speakers, unresponsive patients,
background noise, and unusual conversational patterns.
"""

SCENARIOS = [
    {
        "id": "edge_01_spanish_speaker",
        "description": "Spanish-speaking patient — multilingual intake",
        "patient_profile": {
            "name": "Carlos Mendoza",
            "dob": "1980-05-20",
            "language": "es",
        },
        "opening_message": "Hola, llamo porque tengo mucho dolor de estómago desde hace tres días.",
        "conversation_turns": [
            "Me llamo Carlos Mendoza. Nací el 20 de mayo de 1980.",
            "Es un dolor aquí, en la parte baja del estómago. Como un 7 de dolor.",
            "Empezó hace tres días después de comer mariscos.",
            "Tomo omeprazol para el reflujo y lisinopril para la presión.",
            "Soy alérgico a la penicilina.",
            "Tengo reflujo gástrico y presión alta.",
        ],
        "expected_outputs": {
            "patient_name": "Carlos Mendoza",
            "chief_complaint_contains": ["stomach", "estómago", "abdominal"],
            "allergies_contain": "penicillin",
            "language_detected": "es",
            "fhir_summary_language": "en",
        },
    },
    {
        "id": "edge_02_unresponsive",
        "description": "Patient becomes unresponsive mid-call",
        "patient_profile": {
            "name": "Unknown",
            "dob": "Unknown",
            "language": "en",
        },
        "opening_message": "Hello, I need to see a doctor about...",
        "conversation_turns": [
            "[SILENCE — 30 seconds]",
            "[SILENCE — 30 seconds]",
            "[SILENCE — 30 seconds]",
        ],
        "expected_outputs": {
            "should_trigger_welfare_check": True,
            "agent_response_contains": ["still there", "okay"],
            "should_escalate_to_human": True,
        },
    },
    {
        "id": "edge_03_background_noise",
        "description": "Patient in noisy environment with unclear speech",
        "patient_profile": {
            "name": "Jennifer Walsh",
            "dob": "1995-10-08",
            "language": "en",
        },
        "opening_message": "Hi... [background noise] ...calling about my... [unclear] ...ankle.",
        "conversation_turns": [
            "Jennifer... [noise] ...Walsh. October 8... [noise] ...1995.",
            "Sorry, I'm at a... [noise] ...I twisted my ankle yesterday playing basketball.",
            "Can you hear me better now? The pain is moderate, like a 5. It's swollen.",
            "I don't take any medications. No allergies.",
            "No, just the ankle thing. Otherwise healthy.",
        ],
        "expected_outputs": {
            "patient_name": "Jennifer Walsh",
            "chief_complaint_contains": "ankle",
            "agent_should_ask_for_clarification": True,
        },
    },
    {
        "id": "edge_04_rambling_patient",
        "description": "Patient who provides excessive detail and goes off-topic",
        "patient_profile": {
            "name": "Harold Peters",
            "dob": "1950-12-03",
            "language": "en",
        },
        "opening_message": "Oh hello there. You know, my daughter told me I should call. She's always worrying about me. She lives in Seattle now, did I mention that?",
        "conversation_turns": [
            "My name? Oh, Harold Peters. Born December 3, 1950. I remember because my mother always said it was the coldest day of the year.",
            "Well, it's my shoulder. The left one. Or maybe it's both. You know, when I was younger I used to play baseball and the coach always said I had a strong arm. Anyway, it's been hurting for about... let me think... two weeks? Maybe three?",
            "About a 5 I suppose. It's worse at night. My wife — God rest her soul — she used to rub my shoulders before bed.",
            "Oh let me get my pill bottles. I take... metoprolol, that's the heart one. And amlodipine. And simvastatin. And there's one more... oh yes, baby aspirin.",
            "Allergic to shellfish. Found that out the hard way at a restaurant in 1987.",
            "High blood pressure, high cholesterol, and I had a stent put in about five years ago.",
        ],
        "expected_outputs": {
            "patient_name": "Harold Peters",
            "chief_complaint_contains": "shoulder",
            "allergies_contain": "shellfish",
            "medications_contain": "metoprolol",
            "agent_should_redirect_politely": True,
        },
    },
    {
        "id": "edge_05_pediatric_parent",
        "description": "Parent calling about a sick child — heightened sensitivity",
        "patient_profile": {
            "name": "Emma (parent: Sarah Davis)",
            "dob": "2022-07-15",
            "language": "en",
        },
        "opening_message": "Hi, I'm calling about my daughter Emma. She's 3 years old and she's had a high fever since last night.",
        "conversation_turns": [
            "Her name is Emma Davis. Born July 15, 2022. I'm her mother, Sarah.",
            "Her temperature was 103.2 when I checked an hour ago. She's been cranky and not eating.",
            "She's also pulling at her right ear. She had an ear infection two months ago.",
            "She takes no regular medications. She had amoxicillin last time for the ear infection.",
            "No allergies that we know of.",
            "She was a premie — born at 34 weeks. Otherwise healthy toddler.",
        ],
        "expected_outputs": {
            "patient_name": "Emma Davis",
            "chief_complaint_contains": "fever",
            "triage_level": "urgent",
            "should_note_pediatric": True,
        },
    },
]
