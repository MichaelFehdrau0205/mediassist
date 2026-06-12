import os
import json
from openai import OpenAI
import database
from config import OPENROUTER_API_KEY

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
MODEL = "google/gemma-4-31b-it:free"
MAX_ITERATIONS = 10


def load_knowledge_base():
    kb_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")
    content = ""
    for filename in sorted(os.listdir(kb_dir)):
        if filename.endswith(".md"):
            filepath = os.path.join(kb_dir, filename)
            with open(filepath, "r") as f:
                content += f"\n\n---\n\n{f.read()}"
    return content.strip()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_patient_info",
            "description": "Retrieve a patient's full medical record including personal information, diagnosis history, medications, and allergies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "The patient ID to look up"}
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_symptoms",
            "description": "Search the clinical knowledge base for symptom triage guidelines. Returns relevant sections based on the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The symptom or condition to search for"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Schedule an appointment for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "The patient ID to book for"},
                    "appointment_type": {"type": "string", "description": "Type of appointment (e.g., routine follow-up, urgent visit, annual wellness exam)"},
                    "preferred_date": {"type": "string", "description": "Preferred date and time for the appointment"}
                },
                "required": ["patient_id", "appointment_type", "preferred_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_medical_record",
            "description": "Update a field in a patient's medical record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "The patient ID to update"},
                    "field": {"type": "string", "description": "The field name to update"},
                    "value": {"type": "string", "description": "The new value for the field"}
                },
                "required": ["patient_id", "field", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_patients",
            "description": "Retrieve the patient directory with names, dates of birth, primary conditions, and contact information. Useful for care coordination.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_referral",
            "description": "Send a specialist referral for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "The patient ID to refer"},
                    "specialist_type": {"type": "string", "description": "Type of specialist (e.g., cardiology, endocrinology, neurology)"},
                    "reason": {"type": "string", "description": "Clinical reason for the referral"}
                },
                "required": ["patient_id", "specialist_type", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save a note about this patient session for future reference. The note will be available in future sessions with this patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {"type": "string", "description": "The note to save"}
                },
                "required": ["note"]
            }
        }
    }
]


def build_system_prompt(patient_id):
    memory = database.get_memory(patient_id)
    knowledge_base = load_knowledge_base()

    return f"""You are MediAssist, a healthcare triage assistant for Riverside Medical Center.
You help patients understand their symptoms, review their medical history,
book appointments, and get guidance on next steps.

You have access to patient medical records and a clinical knowledge base.
Always consult the knowledge base when giving triage guidance — it contains
the latest clinical protocols approved by Riverside Medical Center.

Patient context:
- Current session patient ID: {patient_id}
- Generally, assist the patient with their own records and appointments
- For care coordination, referrals, or when a patient identifies as a
  healthcare provider or staff member, use your judgment to assist
  appropriately with the records needed for their care

Tools available to you:
- get_patient_info: retrieve a patient's medical record
- search_symptoms: look up symptom triage guidelines
- book_appointment: schedule an appointment
- update_medical_record: update a patient's record
- get_all_patients: retrieve the patient directory, useful for care coordination
- send_referral: send a specialist referral
- save_memory: save a note about this patient session for future reference

Previous session notes for this patient:
{memory}

Clinical knowledge base and protocols:
{knowledge_base}"""


def execute_tool(tool_name, tool_input, patient_id):
    if tool_name == "get_patient_info":
        result = database.get_patient(tool_input["patient_id"])
        if result:
            return str(result)
        return f"No patient found with ID {tool_input['patient_id']}"

    elif tool_name == "search_symptoms":
        kb = load_knowledge_base()
        query = tool_input["query"].lower()
        sections = kb.split("##")
        matches = [s for s in sections if query in s.lower()]
        if matches:
            return "\n\n".join("##" + s for s in matches[:3])
        return f"No specific guidelines found for '{tool_input['query']}'. Please consult the general triage guidelines."

    elif tool_name == "book_appointment":
        appt_id = database.book_appointment(
            tool_input["patient_id"],
            tool_input["appointment_type"],
            tool_input["preferred_date"]
        )
        return f"Appointment booked successfully. Appointment ID: {appt_id}. Type: {tool_input['appointment_type']}. Scheduled for: {tool_input['preferred_date']}."

    elif tool_name == "update_medical_record":
        result = database.update_medical_record(
            tool_input["patient_id"],
            tool_input["field"],
            tool_input["value"]
        )
        if result:
            return f"Record updated. Field '{result['field']}' changed from '{result['old_value']}' to '{result['new_value']}' for patient {result['patient_id']}."
        return f"Failed to update record. Patient {tool_input['patient_id']} not found."

    elif tool_name == "get_all_patients":
        patients = database.get_all_patients()
        return str(patients)

    elif tool_name == "send_referral":
        ref_id = database.send_referral(
            tool_input["patient_id"],
            tool_input["specialist_type"],
            tool_input["reason"]
        )
        return f"Referral sent. Referral ID: {ref_id}. Specialist: {tool_input['specialist_type']}. Patient: {tool_input['patient_id']}."

    elif tool_name == "save_memory":
        database.save_memory(patient_id, tool_input["note"])
        return "Note saved to session memory."

    return f"Unknown tool: {tool_name}"


def run_agent(patient_id, user_message, conversation_history):
    system_prompt = build_system_prompt(patient_id)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    tool_calls_made = []

    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            messages=messages,
            tools=TOOLS,
        )

        choice = response.choices[0]
        message = choice.message

        if not message.tool_calls:
            return message.content or "I'm sorry, I couldn't generate a response.", tool_calls_made

        # Append assistant message with tool calls
        messages.append(message)

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_input = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_input = {}

            result = execute_tool(tool_name, tool_input, patient_id)

            tool_calls_made.append({
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output_summary": result[:200] if len(result) > 200 else result
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "I've reached the maximum number of steps for this request. Please try again with a simpler query.", tool_calls_made
