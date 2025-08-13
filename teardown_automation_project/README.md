# Company Teardown Automation

An AI-powered web application that generates comprehensive company teardown reports using crew.ai agents. Features both single company processing and advanced bulk processing capabilities with real-time progress tracking.

## Features

### Core Features
- **Modern Web UI**: Clean interface with three processing modes (Single/Batch/CSV)
- **AI-Powered Research**: Uses crew.ai agents to scrape, analyze, and compile company data
- **Multi-Source Analysis**: Gathers data from company websites and other sources
- **Structured Reports**: Generates markdown and pdf teardown reports with strategic insights
- **Report Management**: View, download, and manage all generated teardowns

### Bulk Processing Features ✨
- **Batch Mode**: Process multiple companies manually with UI controls
- **CSV Import**: Upload CSV files for bulk company processing (currently will process 10 companies)
- **Sequential Processing**: Stable one-at-a-time job processing
- **Real-Time Progress**: Live progress tracking with detailed status updates
- **Client-Side Orchestration**: Efficient job management without server-side queues
- **Job Management**: Individual job status monitoring and error handling

## Prerequisites

- **Python 3.10+** (Required for crew.ai 0.148.0)
- **OpenAI API Key** (Required for AI analysis)
- **SerpAI API Key** (Required for web scraping)

## Installation

### 1. Check Python Version
```bash
python3 --version
# If you have Python 3.9 or lower, install Python 3.11+
# On macOS with Homebrew: brew install python@3.11
```

### 2. Clone and Setup
```bash
git clone <repository-url>
cd teardown_automation_project
```

### 3. Quick Setup (Recommended)
```bash
# Run the setup script (troubleshoot this)
chmod +x setup.sh
./setup.sh 
```

### 3. Manual Installation
```bash
# Use Python 3.11 (or your Python 3.10+ version)
python3.11 -m pip install -r requirements.txt

# Or install manually:
python3.11 -m pip install crewai==0.148.0 flask beautifulsoup4 requests langchain langchain-openai langchain-community faiss-cpu
```

### 4. Set Up OpenAI API Key and Serp API Key
**Important**: You must replace the placeholder API key with your own in a .env file. Make sure to place it into a .gitignore. 

1. Get your OpenAI API key from https://platform.openai.com/api-keys
2. Get your Serp API key from https://serpapi.com/
3. Connect your API keys by establishing a secure .env file


### 5. Template Files
The required template files are already included:
- `template/research_template.txt` - Defines the teardown report structure
- `template/klear_context.txt` - Provides company context for strategic analysis
- `template/questions.json` - Defines instructions for each question
- `template/example_teardown.txt` - Provides a complete teardown example

You can customize these files to modify the analysis questions and company context.

## Usage

### Start the Web Application
```bash
python3.11 app.py
```

The app will start on `http://localhost:8080`

### Processing Modes

#### 1. Single Company Mode
- Enter company name and website URL
- Click "Generate Teardown" for immediate processing
- Real-time status updates during processing

#### 2. Batch Mode ✨
- Click "Batch" tab in the header
- Add multiple companies using "+ Add Company" button
- Sequential processing (one company at a time for stability)
- Click "Start Batch Processing" to begin
- Monitor real-time progress for all companies

#### 3. CSV Import Mode ✨
- Click "CSV" tab in the header
- Upload CSV file with `company_name,company_url` columns
- Preview companies before processing
- Automatic batch processing with progress tracking
- Download sample CSV for format reference

### Processing Workflow
1. **Input**: Company information via any of the three modes
2. **AI Processing**: Crew.ai agents execute in sequence:
   - Company website scraper
   - SpaceNews article finder
   - USASpending API scraper
   - GlobalNewsWire article finder
   - SerpAPI scraper
   - Data processor and report compiler
3. **Results**: View completed teardowns with real-time updates
4. **Management**: Download, view, and organize all reports

### Demo Mode (No API Key Required)
For testing the UI without crew.ai:
```bash
python3.11 app_demo.py
```

### System Cleanup ✨
Reset the system to clean state (removes all data):

**Quick cleanup:**
```bash
./cleanup.sh
```

**Detailed cleanup with confirmation:**
```bash
python3 cleanup.py
```

Both scripts will remove:
- All teardown jobs and database records
- All generated files
- Python cache files
- Job-specific output folders

### CSV Format for Bulk Import
Your CSV file should have these columns:
```csv
company_name,company_url
Solestial,https://solestial.com
SpaceX,https://spacex.com
Relativity Space,https://relativityspace.com
```

Download a sample CSV from the app interface for the correct format.

## Architecture

### Backend Components
- **Flask Application**: Main web server with API endpoints
- **Database Layer**: SQLite database for jobs and teardowns
- **Job Management**: Individual job tracking with status updates
- **File System**: Job-based folder structure for organized output

### AI Agents
- **Company News Agent**: Scrapes company websites for information
- **SpaceNews Agent**: Finds relevant industry articles
- **Contract Agent**: Finds relevant US government contracts 
- **GlobalNewsWire Agent**: Finds relevant industry articles
- **SerpAPI Agent**: Finds relevant industry articles
- **Teardown Agent**: Generates structured teardown reports

### Frontend Architecture ✨
- **Mode Switching**: Dynamic UI for Single/Batch/CSV modes
- **Batch Processor**: Client-side job orchestration and management
- **Progress Tracking**: Real-time status updates via API polling
- **Sequential Control**: Stable one-at-a-time processing
- **Error Handling**: Comprehensive error reporting and recovery

### Bulk Processing Workflow
1. **Client-Side Orchestration**: JavaScript manages job queue sequentially
2. **API Integration**: RESTful endpoints for job creation and status
3. **Real-Time Updates**: Polling-based progress tracking every 2 seconds
4. **Job Isolation**: Each job gets dedicated folders and database records
5. **Status Management**: Comprehensive job lifecycle (pending → running → completed/failed)

## Configuration

### Research Template
Edit `template/research_template.txt` to customize teardown questions:
```markdown
**company Name**
**company description**
**industry**
**revenue/Size**
**leadership team(CEO, CFO, CTO, Founder)**
**how can Klear help this company?**
```

### Klear Context
Add company context in `template/klear_context.txt` for strategic analysis.

## Troubleshooting

### Common Issues

**"Task object has no field 'inputs'"**
- This is fixed in the current version - tasks no longer use the `inputs` field

**"AuthenticationError: OpenAI API key"**
- Ensure your OpenAI API key is set in `app.py`
- Verify the key is valid and has sufficient credits

**"Port already in use"**
- Kill existing processes: `lsof -ti:8080 | xargs kill -9`
- Or change the port in `app.py`

**Import errors with CrewAI**
- Ensure you're using Python 3.10+ (required for CrewAI 0.148.0)
- Install with correct Python version: `python3.11 -m pip install crewai==0.148.0`

**Bulk processing issues**
- Check browser console for JavaScript errors
- Verify API endpoints are responding (check Network tab)
- Use cleanup scripts to reset system state

**"Elements found: {singleMode: false, ...}"**
- This indicates the HTML template isn't loading properly
- Clear browser cache and refresh
- Restart the Flask application

### File Structure
```
teardown_automation_project/
├── app.py                # Main Flask application (with bulk processing)
├── app_demo.py           # Demo version (no API key needed)
├── main.py               # Original crew.ai script
├── cleanup.py            # Comprehensive cleanup script
├── cleanup.sh            # Quick cleanup script
├── requirements.txt      # Python dependencies
├── models.py             # Database models (jobs, teardowns)
├── database.py           # Database operations
├── utils.py              # Utility functions
├── src/
│   ├── agents/
│   │   └── agent.py      # Crew.ai agent definitions
│   └── tools/            # Custom tools for agents
├── tasks/                # Crew.ai task definitions
├── templates/
│   ├── index.html        # Main UI with bulk processing modes
│   └── teardowns.html    # Results page
├── static/
│   ├── css/              # Stylesheets
│   └── js/
│       └── main.js       # Bulk processing JavaScript
│       └── teardown.js   # Bulk processing JavaScript
├── template/             # Research/Context/Example templates
├── output/               # Job-specific output folders
│   └── job_*/            # Individual job folders
└── teardown_app.db       # SQLite database
```

## API Endpoints

The application provides RESTful API endpoints for bulk processing:

### Job Management
- `POST /api/start_teardown` - Start a new teardown job
- `GET /api/job_status/<job_id>` - Get job status and progress
- `GET /api/jobs` - List all jobs

### Teardown Management  
- `GET /api/teardowns` - List all completed teardowns
- `GET /api/teardown/<teardown_id>` - Get specific teardown
- `GET /api/teardown/<teardown_id>/download` - Download teardown file

### Example API Usage
```javascript
// Start a teardown job
const response = await fetch('/api/start_teardown', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        company_name: 'Solestial',
        company_url: 'https://solestial.com'
    })
});
const { job_id } = await response.json();

// Check job status
const statusResponse = await fetch(`/api/job_status/${job_id}`);
const jobData = await statusResponse.json();
```

## Development

### Adding New Agents
1. Create agent in `src/agents/agent.py`
2. Create corresponding task in `tasks/`
3. Create corresponding tool in `src/tools/`
4. Add to crew in `app.py`

### Customizing Reports
1. Modify `template/research_template.txt` and `template/question.json`
2. Update company context `template/klear_context.txt`
3. Adjust prompt styles for different analysis types

### Extending Bulk Processing
1. Modify `static/js/main.js` for frontend changes
2. Update API endpoints in `app.py` for backend changes
3. Adjust database models in `models.py` for data structure changes

## License