"""
Test scenarios: Normal intake flows.

5 scenarios covering straightforward symptom collection with varying
patient profiles, complaint types, and conversational styles.
"""

SCENARIOS = [
    {
        "id": "normal_01_knee_pain",
        "description": "Adult patient with knee pain — standard intake flow",
        "patient_profile": {
            "name": "Maria Garcia",
            "dob": "1985-03-15",
            "language": "en",
        },
        "opening_message": "Hi, I'm calling because I've been having pain in my right knee for about a week now.",
        "conversation_turns": [
            "My name is Maria Garcia. Date of birth March 15, 1985.",
            "It's a sharp pain, especially when I climb stairs. I'd say it's about a 6 out of 10.",
            "It started last Monday after I went jogging. It's been getting worse.",
            "I take lisinopril for blood pressure and a daily multivitamin.",
            "I'm allergic to sulfa drugs. I get a rash.",
            "I had ACL surgery on the same knee about ten years ago.",
        ],
        "expected_outputs": {
            "patient_name": "Maria Garcia",
            "chief_complaint_contains": "knee",
            "allergies_contain": "sulfa",
            "medications_contain": "lisinopril",
            "triage_level": "routine",
        },
    },
    {
        "id": "normal_02_headache",
        "description": "Patient with persistent headaches — detailed symptom capture",
        "patient_profile": {
            "name": "James Chen",
            "dob": "1972-08-22",
            "language": "en",
        },
        "opening_message": "I've been getting these really bad headaches almost every day for the past two weeks.",
        "conversation_turns": [
            "James Chen, born August 22, 1972.",
            "They're mostly on the right side, behind my eye. Throbbing. Maybe a 7 out of 10.",
            "Usually worse in the morning. Light bothers me when it's bad.",
            "I take metformin for type 2 diabetes and atorvastatin for cholesterol.",
            "No allergies that I know of.",
            "I've had migraines before, maybe 10 years ago, but they went away.",
        ],
        "expected_outputs": {
            "patient_name": "James Chen",
            "chief_complaint_contains": "headache",
            "allergies_contain": None,
            "medications_contain": "metformin",
            "triage_level": "urgent",
        },
    },
    {
        "id": "normal_03_skin_rash",
        "description": "Patient with new skin rash — potential vision scenario",
        "patient_profile": {
            "name": "Aisha Johnson",
            "dob": "1990-11-04",
            "language": "en",
        },
        "opening_message": "I noticed a rash on my forearm about three days ago and it seems to be spreading.",
        "conversation_turns": [
            "Aisha Johnson. November 4, 1990.",
            "It's red, slightly raised, and itchy. Started as a small patch but now it's about the size of my palm.",
            "It's on my left forearm. No pain, just itching. I'd say the discomfort is a 4.",
            "I started a new laundry detergent last week, could that be it?",
            "I take birth control pills and that's it.",
            "I'm allergic to penicillin — I get hives.",
            "No other medical conditions.",
        ],
        "expected_outputs": {
            "patient_name": "Aisha Johnson",
            "chief_complaint_contains": "rash",
            "allergies_contain": "penicillin",
            "triage_level": "routine",
        },
    },
    {
        "id": "normal_04_back_pain",
        "description": "Elderly patient with chronic back pain flare-up",
        "patient_profile": {
            "name": "Robert Williams",
            "dob": "1948-06-30",
            "language": "en",
        },
        "opening_message": "My lower back has been acting up something terrible. I can barely get out of bed.",
        "conversation_turns": [
            "Robert Williams, June 30, 1948. I'm 77.",
            "Lower back, both sides. Dull ache that gets sharp when I twist. Maybe an 8.",
            "I've had back problems for years but this flare started four days ago when I lifted a heavy box.",
            "Let me think... I take metoprolol, warfarin, gabapentin, and omeprazole.",
            "Allergic to codeine — it makes me very nauseous. And latex.",
            "I have atrial fibrillation, osteoarthritis, and I had a hip replacement in 2019.",
        ],
        "expected_outputs": {
            "patient_name": "Robert Williams",
            "chief_complaint_contains": "back",
            "allergies_contain": "codeine",
            "medications_contain": "warfarin",
            "triage_level": "urgent",
        },
    },
    {
        "id": "normal_05_sore_throat",
        "description": "Young adult with sore throat and mild fever",
        "patient_profile": {
            "name": "Emily Park",
            "dob": "2001-01-12",
            "language": "en",
        },
        "opening_message": "I've had a sore throat since yesterday and I think I have a fever.",
        "conversation_turns": [
            "Emily Park, January 12, 2001.",
            "My throat hurts when I swallow. I checked my temperature and it was 100.4. Discomfort is about a 5.",
            "Started yesterday afternoon. I also feel really tired.",
            "I don't take any medications regularly. Just ibuprofen when I need it.",
            "No allergies.",
            "I'm generally healthy. No major medical history.",
        ],
        "expected_outputs": {
            "patient_name": "Emily Park",
            "chief_complaint_contains": "throat",
            "triage_level": "routine",
        },
    },
]
