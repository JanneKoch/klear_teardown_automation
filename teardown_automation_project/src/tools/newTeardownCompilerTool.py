# Final version - Fast execution + Proper answer persistence
import os
import json
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOpenAI
from crewai.tools import tool
from utils import sanitize_filename

class RAGTeardownCompiler(BaseModel):
    """
    Fast execution with proper answer persistence using JSON intermediate storage.
    """
    company_name: str
    template_path: str
    klear_context_path: Optional[str] = None
    example_teardown_path: Optional[str] = None
    questions_path: str = "template/question.json"
    output_folder: str 
    llm: Optional[object] = None

    def _load_text_file(self, path: str) -> str:
        """Loads a single text file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return ""

    def _load_company_data(self) -> List[Dict[str, str]]:
        """Loads individual files from the output folder."""
        print(f"🔍 Loading data from: {self.output_folder}")
        contents = []
        
        if not os.path.exists(self.output_folder):
            print(f"Warning: Output folder {self.output_folder} doesn't exist")
            os.makedirs(self.output_folder, exist_ok=True)
            return contents
            
        if not os.path.isdir(self.output_folder):
            print(f"Error: {self.output_folder} is not a directory")
            return contents
            
        files_in_folder = os.listdir(self.output_folder)
        print(f"Files in folder: {files_in_folder}")
            
        for filename in files_in_folder:
            if filename.endswith(".txt"):
                file_path = os.path.join(self.output_folder, filename)
                try:
                    if os.path.isfile(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            if content:
                                contents.append({
                                    "filename": filename, 
                                    "data": content,
                                    "size": len(content)
                                })
                                print(f"Loaded {filename}: {len(content)} characters")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"Total loaded: {len(contents)} data files")
        return contents

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)."""
        return len(text) // 4

    def _chunk_data_smartly(self, company_data: List[Dict], klear_context: str, max_tokens: int = 12000) -> List[str]:
        """Smart chunking that prioritizes relevant data."""
        if not company_data:
            return ["No company data available"]
            
        chunks = []
        base_prompt_tokens = 1000
        available_tokens = max_tokens - base_prompt_tokens
        
        if klear_context:
            available_tokens -= self._estimate_tokens(klear_context)
        
        # Sort files by relevance
        priority_order = ['website', 'company', 'homepage', 'news', 'space', 'contract', 'global']
        
        def get_priority(filename):
            filename_lower = filename.lower()
            for i, keyword in enumerate(priority_order):
                if keyword in filename_lower:
                    return i
            return len(priority_order)
        
        sorted_data = sorted(company_data, key=lambda x: get_priority(x['filename']))
        
        # Create chunks
        current_chunk = []
        current_tokens = 0
        
        for file_data in sorted_data:
            file_tokens = self._estimate_tokens(file_data['data'])
            
            if file_tokens > available_tokens:
                # Truncate large files
                truncated_data = file_data['data'][:available_tokens * 4]
                chunk_content = f"--- {file_data['filename']} (truncated) ---\n{truncated_data}"
                chunks.append(chunk_content)
                continue
            
            if current_tokens + file_tokens > available_tokens and current_chunk:
                # Save current chunk and start new one
                chunk_content = "\n\n".join(current_chunk)
                chunks.append(chunk_content)
                current_chunk = []
                current_tokens = 0
            
            # Add file to current chunk
            file_content = f"--- {file_data['filename']} ---\n{file_data['data']}"
            current_chunk.append(file_content)
            current_tokens += file_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunks.append(chunk_content)
        
        print(f"Created {len(chunks)} data chunks")
        return chunks if chunks else ["No company data available"]

    def _load_questions(self) -> list:
        """Loads questions from the JSON file."""
        try:
            with open(self.questions_path, "r", encoding="utf-8") as f:
                questions = json.load(f)
                print(f"Loaded {len(questions)} questions")
                return questions
        except Exception as e:
            print(f"Error loading questions: {e}")
            return []

    def _answer_question_with_chunks(self, question: Dict, chunks: List[str], klear_context: str) -> str:
        """Answer a question using multiple chunks if needed."""
        if self.llm is None:
            self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        
        q_id = question.get("id")
        print(f"🤖 Processing question: {q_id}")
        
        # Add Klear context for relevant questions
        klear_section = f"\nKlear Context:\n{klear_context}" if 'klear' in q_id and klear_context else ""
        
        # Use first chunk for simple questions
        if q_id in ['the_company_name', 'company_description', 'industry']:
            chunk = chunks[0] if chunks else "No data available"
            prompt = f"""You are a company research analyst for {self.company_name}.

Your task: {question['instruction']}

Company Data:
{chunk}
{klear_section}

Instructions:
- Answer only the specific question asked
- Be precise and professional  
- If information is not available, state "Information not available"

Question: {question['title']}
Answer:"""
            
            try:
                response = self.llm.invoke(prompt).content.strip()
                print(f"✅ Got answer for {q_id}: {len(response)} chars")
                return response
            except Exception as e:
                print(f"❌ Error processing {q_id}: {e}")
                return f"Error processing question: {e}"
        
        # For complex questions, combine insights
        combined_insights = []
        
        for i, chunk in enumerate(chunks):
            prompt = f"""You are a company research analyst for {self.company_name}.

Your task: {question['instruction']}

Company Data (Part {i+1}/{len(chunks)}):
{chunk}
{klear_section}

Instructions:
- Extract only information relevant to: {question['title']}
- Be precise and concise
- If no relevant information is found, say "No relevant information"

Question: {question['title']}
Relevant Information:"""

            try:
                response = self.llm.invoke(prompt).content.strip()
                if response and "no relevant information" not in response.lower():
                    combined_insights.append(response)
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
                continue
        
        # Synthesize final answer
        if combined_insights:
            synthesis_prompt = f"""Based on the following information about {self.company_name}, provide a comprehensive answer to: {question['title']}

Task: {question['instruction']}

Information gathered:
{chr(10).join(combined_insights)}

Provide a final, synthesized answer:"""
            
            try:
                final_response = self.llm.invoke(synthesis_prompt).content.strip()
                print(f"✅ Got synthesized answer for {q_id}: {len(final_response)} chars")
                return final_response
            except Exception as e:
                print(f"❌ Error synthesizing {q_id}: {e}")
                return f"Error synthesizing answer: {e}"
        else:
            return "Information not available"

    def _save_answer_to_json(self, question_id: str, answer: str):
        """Save individual answers to JSON files - fast and atomic."""
        safe_name = sanitize_filename(self.company_name)
        answer_file = os.path.join(self.output_folder, f"{safe_name}_{question_id}.json")
        
        try:
            answer_data = {
                "question_id": question_id,
                "answer": answer,
                "timestamp": time.time(),
                "company_name": self.company_name
            }
            
            with open(answer_file, "w", encoding="utf-8") as f:
                json.dump(answer_data, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Saved {question_id} to JSON file")
            
        except Exception as e:
            print(f"❌ Error saving {question_id} to JSON: {e}")

    def _compile_final_teardown(self):
        """Compile all JSON answers into the final teardown markdown file."""
        safe_name = sanitize_filename(self.company_name)
        output_path = os.path.join(self.output_folder, f"{safe_name}_teardown.md")
        
        # Load all answer JSON files
        answers = {}
        for filename in os.listdir(self.output_folder):
            if filename.startswith(f"{safe_name}_") and filename.endswith(".json") and not filename.endswith("_teardown.json"):
                try:
                    with open(os.path.join(self.output_folder, filename), "r", encoding="utf-8") as f:
                        answer_data = json.load(f)
                        question_id = answer_data.get("question_id")
                        answer = answer_data.get("answer", "")
                        if question_id:
                            answers[question_id] = answer
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"🔄 Compiling teardown with {len(answers)} answers")
        
        # Load questions to maintain proper order
        questions = self._load_questions()
        
        # Build the final markdown
        markdown_content = f"# Company Teardown: {self.company_name}\n\n"
        
        for q in questions:
            q_id = q.get("id")
            if q_id:
                answer = answers.get(q_id, "#")  # Use # as placeholder if no answer
                markdown_content += f"## {q_id}\n{answer}\n\n"
        
        # Write the final teardown
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"✅ Final teardown compiled: {output_path}")
        except Exception as e:
            print(f"❌ Error writing final teardown: {e}")

    def run(self, question_id: Optional[str] = None) -> str:
        """Runs the teardown compiler for a specific question."""
        
        print(f"🚀 RAGTeardownCompiler starting for question: {question_id}")
        start_time = time.time()
        
        # Load data
        company_data = self._load_company_data()
        klear_context = self._load_text_file(self.klear_context_path) if self.klear_context_path else ""
        questions = self._load_questions()
        
        if not questions:
            return "No questions loaded"

        # Create chunks
        chunks = self._chunk_data_smartly(company_data, klear_context)
        
        if question_id:
            # Process specific question
            question = next((q for q in questions if q.get("id") == question_id), None)
            if not question:
                return f"Question {question_id} not found"
            
            try:
                answer = self._answer_question_with_chunks(question, chunks, klear_context)
                
                # Save answer to JSON (fast, atomic)
                self._save_answer_to_json(question_id, answer)
                
                # Recompile the final teardown with all available answers
                self._compile_final_teardown()
                
                elapsed = time.time() - start_time
                print(f"🎉 Completed {question_id} in {elapsed:.2f}s")
                
                return answer
                
            except Exception as e:
                error_msg = f"Error processing question: {e}"
                print(f"❌ {error_msg}")
                self._save_answer_to_json(question_id, error_msg)
                self._compile_final_teardown()
                return error_msg
        else:
            return "No question_id provided"


@tool
def compile_teardown_rag(company_name: str, output_folder: str, question_id: str = None) -> str:
    """Fast RAG teardown compiler with proper answer persistence."""
    
    print(f"🔧 TOOL: Processing '{question_id}' for {company_name}")
    
    # Validate inputs
    if not company_name or not output_folder:
        error = f"Missing required params: company_name='{company_name}', output_folder='{output_folder}'"
        print(f"❌ TOOL: {error}")
        return error
    
    # Ensure folder exists
    if not os.path.exists(output_folder):
        print(f"🔧 TOOL: Creating folder: {output_folder}")
        os.makedirs(output_folder, exist_ok=True)
    
    # Create and run compiler
    try:
        compiler = RAGTeardownCompiler(
            company_name=company_name,
            template_path="template/research_template.txt",
            klear_context_path="template/klear_context.txt",
            example_teardown_path="template/example_teardown.txt",
            questions_path="template/question.json",
            output_folder=output_folder
        )
        
        result = compiler.run(question_id=question_id)
        print(f"🔧 TOOL: Success! Result length: {len(result)}")
        return result
        
    except Exception as e:
        error_msg = f"Error in compiler: {e}"
        print(f"❌ TOOL: {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg