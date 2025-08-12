from flask import Flask, render_template, request, jsonify, make_response
import os
import threading
import time
from datetime import datetime
import json

app = Flask(__name__)

# Store job status and results
jobs = {}
teardowns = []

class TeardownJob:
    def __init__(self, job_id, company_name, company_url):
        self.job_id = job_id
        self.company_name = company_name
        self.company_url = company_url
        self.status = "running"
        self.start_time = datetime.now()
        self.result = None
        self.error = None

def run_demo_teardown(job_id, company_name, company_url):
    """Demo version that simulates the crew.ai teardown process"""
    job = jobs[job_id]
    
    try:
        # Simulate processing time
        time.sleep(10)  # 10 seconds for demo
        
        # Create demo teardown content
        demo_content = f"""# {company_name} - Company Teardown Analysis

## **Company Name**
- {company_name}

## **Company Description**
- Technology company focused on innovative solutions
- Website: {company_url}

## **Industry**
- Technology/Software

## **Revenue/Size**
- Estimated revenue: $10M - $50M annually
- Employee count: 50-200 employees

## **Leadership Team (CEO, CFO, CTO, Founder)**
- CEO: [Name not available in demo]
- CTO: [Name not available in demo]
- Founder: [Name not available in demo]

## **Stage**
- Growth stage company with established market presence

## **Recent News/Media, Blogs**
- Active in industry publications
- Regular blog updates on company website
- Participation in industry conferences

## **How can Klear help this company?**
- Klear can support {company_name}'s growth through strategic partnerships
- Supply chain optimization opportunities
- Financial planning and analysis support
- Marketing automation and customer acquisition strategies

## **Strategic Approach in Supporting Company**
- Focus on scalable solutions that match company growth trajectory
- Leverage existing technology stack for integration opportunities
- Provide expertise in areas where company may lack internal resources

*Note: This is a demo teardown. The full version would include comprehensive research from multiple sources.*
"""
        
        # Store the teardown
        teardown_data = {
            'id': job_id,
            'company_name': company_name,
            'company_url': company_url,
            'content': demo_content,
            'created_at': job.start_time.isoformat(),
            'completed_at': datetime.now().isoformat()
        }
        teardowns.append(teardown_data)
        
        job.status = "completed"
        job.result = teardown_data
            
    except Exception as e:
        job.status = "error"
        job.error = str(e)

@app.route('/')
def index():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/teardowns')
def teardowns_page():
    return render_template('teardowns.html', teardowns=teardowns)

@app.route('/api/start_teardown', methods=['POST'])
def start_teardown():
    data = request.json
    company_name = data.get('company_name', '').strip()
    company_url = data.get('company_url', '').strip()
    
    if not company_name or not company_url:
        return jsonify({'error': 'Company name and URL are required'}), 400
    
    # Generate job ID
    job_id = f"job_{int(time.time())}"
    
    # Create job
    job = TeardownJob(job_id, company_name, company_url)
    jobs[job_id] = job
    
    # Start background thread
    thread = threading.Thread(target=run_demo_teardown, args=(job_id, company_name, company_url))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': f'Teardown analysis started for {company_name}'
    })

@app.route('/api/job_status/<job_id>')
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    response = {
        'job_id': job_id,
        'status': job.status,
        'company_name': job.company_name,
        'start_time': job.start_time.isoformat()
    }
    
    if job.status == "completed" and job.result:
        response['result'] = job.result
    elif job.status == "error":
        response['error'] = job.error
    
    return jsonify(response)

@app.route('/api/teardowns')
def get_teardowns():
    return jsonify(teardowns)

@app.route('/api/teardown/<teardown_id>')
def get_teardown(teardown_id):
    teardown = next((t for t in teardowns if t['id'] == teardown_id), None)
    if not teardown:
        return jsonify({'error': 'Teardown not found'}), 404
    return jsonify(teardown)

if __name__ == '__main__':
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    print("🚀 Starting Company Teardown Generator (Demo Mode)")
    print("📱 Open your browser to: http://localhost:9000")
    print("⏱️  Demo teardowns take ~10 seconds to complete")
    app.run(debug=True, host='0.0.0.0', port=9000)