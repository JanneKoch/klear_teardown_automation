#!/usr/bin/env python3.11
from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import utils
import threading
import time
from datetime import datetime
from crewai import Crew, Task
import tempfile
from dotenv import load_dotenv

#pdf download imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import re

REPORTLAB_AVAILABLE = True  # Since the imports worked, ReportLab is available

# Set OpenAI API key as environment variable
load_dotenv()

# Import crew components
from src.agents.agent import spacenews_agent, companynews_agent, contract_agent, globalnewswire_agent, serpapi_agent, teardown_agent
from src.tools.newTeardownCompilerTool import compile_teardown_rag

# Import simplified infrastructure
from database import Database
from models import TeardownJob, Teardown, JobStatus
from utils import (
    generate_job_id, generate_unique_id,
    create_job_folders, get_teardown_path, ensure_directories_exist, sanitize_filename 
)

app = Flask(__name__)

# Initialize database and ensure directories exist
db = Database()
ensure_directories_exist()

# Store active jobs (for thread management)
active_jobs = {}

def run_single_teardown(job: TeardownJob):
    try:
        # Update job status to running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        db.update_job(job)
        
        # Create job-specific folders (KEEP THIS AS IS)
        output_folder = create_job_folders(job.id)
        job.output_folder = output_folder
        db.update_job(job)

        print(f"Company Name: {job.company_name}")
        print(f"Output Folder: {output_folder}")  # Should be something like "output/job_20250807_115103_121af0e2"
        
        # ===== THE KEY CHANGE: Pass output_folder to ALL tasks =====
        
        # Create dynamic tasks with job-specific output folder
        dynamic_companynews_task = Task(
            description=f"Scrape {job.company_name}'s website ({job.company_url}) and extract all useful text-based content. Save files to {output_folder}.",
            expected_output="A .txt file with structured information scraped from the company's homepage and subpages.",
            agent=companynews_agent,
            # ADD THIS - pass the job-specific folder to the agent
            inputs={
                "company_name": job.company_name,
                "company_url": job.company_url,
                "output_folder": output_folder  # <-- This ensures data goes to job-specific folder
            }
        )
        
        dynamic_spacenews_task = Task(
            description=f"Find the most interesting recent developments about {job.company_name} in the space sector and compile them in a txt file. Save files to {output_folder}.",
            expected_output="A .txt file with recent space industry news related to the company.",
            agent=spacenews_agent,
            inputs={
                "company_name": job.company_name,
                "output_folder": output_folder  # <-- Job-specific folder
            }
        )
        
        dynamic_government_contract_task = Task(
            description=f"Use the USAspending API to find government contracts awarded to {job.company_name} and save them to a text file. Save files to {output_folder}.",
            expected_output="A .txt file with recent contract/award news.",
            agent=contract_agent,
            inputs={
                "company_name": job.company_name,
                "output_folder": output_folder  # <-- Job-specific folder
            }
        )
        
        # Import globalnewswire task and modify it to use job-specific folder
        from tasks.globalnewswire_task import globalnewswire_task
        
        # You might need to create a dynamic globalnewswire task too:
        dynamic_globalnewswire_task = Task(
            description=f"Find the most interesting recent developments about {job.company_name} in the deep tech sector and compile them in a txt file. Save files to {output_folder}.",
            expected_output="A .txt file with recent deep tech industry news related to the company.",
            agent=globalnewswire_agent,
            inputs={
                "company_name": job.company_name,
                "output_folder": output_folder  # <-- Job-specific folder
            }
        )

        from tasks.serpapi_task import serpapi_task

        dynamic_serpapi_task = Task(
            description=f"Find the most interesting recent developments about {job.company_name} on the internet and compile them in a txt file. Save files to {output_folder}.",
            expected_output="A .txt file with recent news related to the company.",
            agent=serpapi_agent,
            inputs={
                "company_name": job.company_name,
                "output_folder": output_folder  # <-- Job-specific folder
            }
        )
        
        # Create teardown tasks with job-specific folder
        print(f"DEBUG: Loading questions from template/question.json")
        with open("template/question.json", "r") as f:
            questions = json.load(f)

        print(f"DEBUG: Loaded {len(questions)} questions")

        teardown_tasks_individual = []

        for i, q in enumerate(questions):
            print(f"DEBUG: Creating task {i+1} for question: {q.get('id', 'NO_ID')}")
            task = Task(
                description=f"Use the compile_teardown_rag tool to answer this specific question about {job.company_name}: {q['title']}. Question ID: {q['id']}. Instruction: {q['instruction']}",
                expected_output=f"A comprehensive answer to question '{q['title']}' saved to the teardown file.",
                agent=teardown_agent,
                inputs={
                    "company_name": job.company_name,
                    "output_folder": output_folder,  # <-- Job-specific folder
                    "question_id": q["id"]
                }
            )
            teardown_tasks_individual.append(task)

        print(f"DEBUG: Created {len(teardown_tasks_individual)} teardown tasks")
        
        # Create and run crew with job-specific tasks
        all_tasks = [
            dynamic_companynews_task, 
            dynamic_spacenews_task, 
            dynamic_government_contract_task,
            dynamic_globalnewswire_task,
            dynamic_serpapi_task  # Use the dynamic version
        ] + teardown_tasks_individual
        
        crew = Crew(
            agents=[companynews_agent, spacenews_agent, contract_agent, globalnewswire_agent, serpapi_agent, teardown_agent],
            tasks=all_tasks,
            verbose=True
        )
        
        # Run crew with job-specific inputs
        inputs = {
            "company_name": job.company_name,
            "company_url": job.company_url,
            "output_folder": output_folder,  # <-- Pass job-specific folder to all tasks
        }
        
        print(f"🚀 Starting crew with {len(all_tasks)} tasks")
        print(f"📁 All tasks will use folder: {output_folder}")
        result = crew.kickoff(inputs=inputs)
        
        # === ADD DEBUGGING HERE ===
        print("=" * 50)
        print("DEBUG: CREW RESULT")
        print("=" * 50)
        print(f"Crew result type: {type(result)}")
        print(f"Crew result: {result}")
        print("=" * 50)
        
        # Check what files are in the output folder
        print(f"Files in output folder {output_folder}:")
        if os.path.exists(output_folder):
            for file in os.listdir(output_folder):
                file_path = os.path.join(output_folder, file)
                file_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                print(f"  - {file} ({file_size} bytes)")
                
                # If it's the teardown file, show its content
                if file.endswith("_teardown.md"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"    Content preview: {content[:200]}...")
        else:
            print("  Output folder doesn't exist!")
        
        print("=" * 50)
        
        # Read the complete teardown file
        safe_name = sanitize_filename(job.company_name)
        teardown_path = os.path.join(output_folder, f"{safe_name}_teardown.md")
        
        if os.path.exists(teardown_path):
            with open(teardown_path, 'r', encoding='utf-8') as f:
                teardown_content = f.read()
                print(f"DEBUG: Teardown file exists, content length: {len(teardown_content)}")
                print(f"DEBUG: First 500 characters:\n{teardown_content[:500]}")
        else:
            teardown_content = f"# Company Teardown: {job.company_name}\n\nTeardown file not generated properly."
            print(f"DEBUG: Teardown file does not exist at {teardown_path}")
        
        print(f"✅ Teardown completed. File size: {len(teardown_content)} characters")
        

        # Read the complete teardown file
        safe_name = sanitize_filename(job.company_name)
        teardown_path = os.path.join(output_folder, f"{safe_name}_teardown.md")
        
        if os.path.exists(teardown_path):
            with open(teardown_path, 'r', encoding='utf-8') as f:
                teardown_content = f.read()
        else:
            teardown_content = f"# Company Teardown: {job.company_name}\n\nTeardown file not generated properly."
        
        print(f"✅ Teardown completed. File size: {len(teardown_content)} characters")
        
        # Create teardown record
        teardown = Teardown(
            id=generate_unique_id(),
            job_id=job.id,
            company_name=job.company_name,
            company_url=job.company_url,
            content=teardown_content,
            created_at=datetime.now(),
            file_path=teardown_path
        )
        
        db.create_teardown(teardown)
        
        # Update job status to completed
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        db.update_job(job)
        
        print(f"✅ Teardown completed for {job.company_name}")
            
    except Exception as e:
        # Update job status to failed
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now()
        job.error_message = str(e)
        db.update_job(job)
        
        print(f"❌ Teardown failed for {job.company_name}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up from active jobs
        if job.id in active_jobs:
            del active_jobs[job.id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/teardowns')
def teardowns_page():
    teardowns = db.get_all_teardowns()
    return render_template('teardowns.html', teardowns=teardowns)

@app.route('/api/start_teardown', methods=['POST'])
def start_teardown():
    data = request.json
    # Check if the data is properly parsed as a dictionary
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format. Expected a JSON object'}), 400
    
    # Log the incoming data for debugging
    print(f"Incoming data: {data}")
    
    company_name = data.get('company_name', '').strip()
    company_url = data.get('company_url', '').strip()
    
    if not company_name or not company_url:
        return jsonify({'error': 'Company name and URL are required'}), 400

    
    if not company_name or not company_url:
        return jsonify({'error': 'Company name and URL are required'}), 400
    
    # Create job
    job = TeardownJob(
        id=generate_job_id(),
        company_name=company_name,
        company_url=company_url,
        status=JobStatus.PENDING,
        created_at=datetime.now()
    )
    
    db.create_job(job)
    
    # Start background thread
    thread = threading.Thread(target=run_single_teardown, args=(job,))
    thread.daemon = True
    thread.start()
    
    # Store active job reference
    active_jobs[job.id] = thread
    
    return jsonify({
        'job_id': job.id,
        'status': 'started',
        'message': f'Teardown analysis started for {company_name}'
    })

@app.route('/api/job_status/<job_id>')
def job_status(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    response = job.to_dict()
    
    # Add teardown if completed
    if job.status == JobStatus.COMPLETED:
        teardown = db.get_teardown_by_job(job_id)
        if teardown:
            response['teardown'] = teardown.to_dict()
    
    return jsonify(response)

@app.route('/api/teardowns')
def get_teardowns():
    teardowns = db.get_all_teardowns()
    return jsonify([teardown.to_dict() for teardown in teardowns])

@app.route('/api/teardown/<teardown_id>')
def get_teardown(teardown_id):
    teardown = db.get_teardown(teardown_id)
    if not teardown:
        return jsonify({'error': 'Teardown not found'}), 404
    return jsonify(teardown.to_dict())

@app.route('/api/teardown/<teardown_id>/download')
def download_teardown(teardown_id):
    teardown = db.get_teardown(teardown_id)
    if not teardown:
        return jsonify({'error': 'Teardown not found'}), 404
    
    # Create a temporary file for download
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(teardown.content)
        temp_path = f.name
    
    filename = f"{teardown.company_name.replace(' ', '_').lower()}_teardown.md"
    return send_file(temp_path, as_attachment=True, download_name=filename)

@app.route('/api/jobs')
def get_jobs():
    """Get all jobs for monitoring"""
    jobs = db.get_all_jobs()
    return jsonify([job.to_dict() for job in jobs])

@app.route('/api/teardown/<teardown_id>/download_pdf')
def download_teardown_pdf(teardown_id):
    print(f"PDF download requested for teardown: {teardown_id}")
    
    # Check if ReportLab is available
    if not REPORTLAB_AVAILABLE:
        return jsonify({'error': 'PDF generation not available. Please install reportlab.'}), 500
    
    # Get teardown from database
    teardown = db.get_teardown(teardown_id)
    if not teardown:
        print(f"Teardown not found: {teardown_id}")
        return jsonify({'error': 'Teardown not found'}), 404
    
    print(f"Found teardown for: {teardown.company_name}")
    
    try:
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        print(f"Creating PDF at: {temp_path}")
        
        # Create PDF document with tighter margins
        doc = SimpleDocTemplate(temp_path, pagesize=A4, 
                              rightMargin=60, leftMargin=60, 
                              topMargin=60, bottomMargin=60)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create compact custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,  # Reduced from 24
            spaceAfter=15,  # Reduced from 30
            spaceBefore=0,
            textColor=HexColor('#2c3e50'),
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,  # Reduced from 16
            spaceAfter=6,  # Reduced from 12
            spaceBefore=12,  # Reduced from 20
            textColor=HexColor('#34495e'),
            leftIndent=0
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,  # Reduced from 11
            spaceAfter=4,  # Reduced from 12
            spaceBefore=0,
            textColor=HexColor('#333333'),
            leftIndent=0
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=9,  # Smaller info text
            spaceAfter=3,
            spaceBefore=0,
            textColor=HexColor('#666666'),
            alignment=1  # Center alignment
        )
        
        # Build the PDF content
        story = []
        
        # Add compact header
        story.append(Paragraph(f"Company Teardown Report", title_style))
        story.append(Paragraph(f"{teardown.company_name}", heading_style))
        story.append(Spacer(1, 8))  # Reduced spacing
        story.append(Paragraph(f"Generated: {teardown.created_at.strftime('%B %d, %Y')}", info_style))
        story.append(Paragraph(f"Website: {teardown.company_url}", info_style))
        story.append(Spacer(1, 15))  # Reduced from 30
        
        # Parse markdown content with compact formatting
        lines = teardown.content.split('\n')
        current_section_content = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('# '):
                # Skip main title as we already added it
                continue
                
            elif line.startswith('## '):
                # Add any pending content from previous section
                if current_section_content:
                    content_text = '\n'.join(current_section_content).strip()
                    if content_text and content_text != '#' and content_text != 'Information not available':
                        # Clean up the content
                        content_text = content_text.replace('#', '').strip()
                        if content_text:
                            story.append(Paragraph(content_text, body_style))
                    current_section_content = []
                
                # Add heading with reduced spacing
                heading_text = line[3:].strip()
                story.append(Paragraph(heading_text, heading_style))
                
            elif line.startswith('### '):
                # Sub-heading - treat as bold text to save space
                subheading_text = line[4:].strip()
                subheading_style = ParagraphStyle(
                    'SubHeading',
                    parent=body_style,
                    fontSize=10,
                    spaceBefore=4,
                    spaceAfter=2,
                    textColor=HexColor('#34495e')
                )
                story.append(Paragraph(f"<b>{subheading_text}</b>", subheading_style))
                
            elif line.startswith('- ') or line.startswith('* '):
                # Bullet point
                bullet_text = line[2:].strip()
                current_section_content.append(f"• {bullet_text}")
                
            elif line.strip() == '':
                # Empty line - add current content and minimal space
                if current_section_content:
                    content_text = '\n'.join(current_section_content).strip()
                    if content_text and content_text != '#' and content_text != 'Information not available':
                        content_text = content_text.replace('#', '').strip()
                        if content_text:
                            story.append(Paragraph(content_text, body_style))
                    current_section_content = []
                
            else:
                # Regular text
                if line.strip() and line.strip() != '#':
                    current_section_content.append(line)
        
        # Add any remaining content
        if current_section_content:
            content_text = '\n'.join(current_section_content).strip()
            if content_text and content_text != '#' and content_text != 'Information not available':
                content_text = content_text.replace('#', '').strip()
                if content_text:
                    story.append(Paragraph(content_text, body_style))
        
        # Add compact footer
        story.append(Spacer(1, 20))  # Reduced spacing
        story.append(Paragraph("This report was generated automatically using company teardown analysis.", info_style))
        
        # Build PDF
        print("Building PDF...")
        doc.build(story)
        print("PDF built successfully")
        
        # Verify file exists
        if not os.path.exists(temp_path):
            print("Error: PDF file was not created")
            return jsonify({'error': 'PDF generation failed'}), 500
        
        file_size = os.path.getsize(temp_path)
        print(f"PDF file size: {file_size} bytes")
        
        if file_size == 0:
            print("Error: PDF file is empty")
            return jsonify({'error': 'PDF generation failed - empty file'}), 500
        
        filename = f"{teardown.company_name.replace(' ', '_').lower()}_teardown.pdf"
        print(f"Sending PDF as: {filename}")
        
        return send_file(temp_path, as_attachment=True, download_name=filename, mimetype='application/pdf')
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Starting Company Teardown Generator (Simplified)")
    print("📱 Open your browser to: http://localhost:8080")
    print("⚡ UI-controlled batch processing")
    
    app.run(debug=True, host='0.0.0.0', port=8080)