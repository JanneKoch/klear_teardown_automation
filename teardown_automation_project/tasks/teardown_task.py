from crewai import Task
from src.agents.agent import teardown_agent
import json
import logging

logging.basicConfig(level=logging.INFO)

# Load questions
with open("template/question.json", "r") as f:
    questions = json.load(f)

teardown_tasks = []

for q in questions:
    if not isinstance(q, dict):
        logging.error(f"Expected a dictionary but got: {type(q)}. Data: {q}")
        continue

    required_keys = ['title', 'instruction', 'id']
    if any(key not in q for key in required_keys):
        logging.warning(f"⚠️ Missing key(s) in: {q}")
        continue

    try:
        # Fixed: Use a lambda to capture the question_id properly
        task = Task(
            description=f"Answer the following question about the company: {q['title']}\n\nDetailed instruction: {q['instruction']}\n\nUse the compile_teardown_rag tool to generate a comprehensive answer based on all available company data.",
            expected_output=f"A detailed answer to the question '{q['title']}' based on the scraped company data.",
            agent=teardown_agent,
            # Pass the context properly 
            context_variables={
                "question_id": q["id"],
                "question_title": q["title"],
                "question_instruction": q["instruction"]
            }
        )
        teardown_tasks.append(task)
        logging.info(f"✅ Created task for question: {q['id']}")
        
    except Exception as e:
        logging.error(f"Error creating task for question ID {q.get('id', 'Unknown')}: {e}")

logging.info(f"✅ Created {len(teardown_tasks)} teardown tasks.")
