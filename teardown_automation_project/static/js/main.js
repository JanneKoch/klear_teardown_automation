document.addEventListener('DOMContentLoaded', function() {
    // UI Elements
    const singleModeBtn = document.getElementById('singleModeBtn');
    const batchModeBtn = document.getElementById('batchModeBtn');
    const csvModeBtn = document.getElementById('csvModeBtn');
    
    const singleMode = document.getElementById('singleMode');
    const batchMode = document.getElementById('batchMode');
    const csvMode = document.getElementById('csvMode');
    
    const singleForm = document.getElementById('singleForm');
    const singleSubmitBtn = document.getElementById('singleSubmitBtn');
    
    const companiesList = document.getElementById('companiesList');
    const addCompanyBtn = document.getElementById('addCompanyBtn');
    const clearAllBtn = document.getElementById('clearAllBtn');
    const batchSubmitBtn = document.getElementById('batchSubmitBtn');
    const concurrencyLimit = document.getElementById('concurrencyLimit');
    
    const csvFile = document.getElementById('csvFile');
    const csvPreview = document.getElementById('csvPreview');
    const csvSubmitBtn = document.getElementById('csvSubmitBtn');
    const downloadSampleCsv = document.getElementById('downloadSampleCsv');
    
    const progressContainer = document.getElementById('progressContainer');

    // State
    let batchCompanies = [];
    let csvCompanies = [];
    let batchProcessor = null;

    // Debug: Check which elements exist
    console.log('Elements found:', {
        singleMode: !!singleMode,
        batchMode: !!batchMode,
        csvMode: !!csvMode,
        progressContainer: !!progressContainer,
        singleModeBtn: !!singleModeBtn,
        batchModeBtn: !!batchModeBtn,
        csvModeBtn: !!csvModeBtn
    });

    // Initialize
    switchMode('single');
    if (typeof addCompanyRow === 'function') addCompanyRow(); // Add initial row for batch mode

    // Event Listeners (with null checks)
    if (singleModeBtn) singleModeBtn.addEventListener('click', () => switchMode('single'));
    if (batchModeBtn) batchModeBtn.addEventListener('click', () => switchMode('batch'));
    if (csvModeBtn) csvModeBtn.addEventListener('click', () => switchMode('csv'));

    if (singleForm) singleForm.addEventListener('submit', handleSingleSubmit);
    if (addCompanyBtn) addCompanyBtn.addEventListener('click', addCompanyRow);
    if (clearAllBtn) clearAllBtn.addEventListener('click', clearAllCompanies);
    if (batchSubmitBtn) batchSubmitBtn.addEventListener('click', startBatchProcessing);
    
    if (csvFile) csvFile.addEventListener('change', handleCsvFile);
    if (csvSubmitBtn) csvSubmitBtn.addEventListener('click', startCsvProcessing);
    if (downloadSampleCsv) downloadSampleCsv.addEventListener('click', downloadSampleCsvFile);

    // Mode Switching
    function switchMode(mode) {
        // Update button states
        document.querySelectorAll('.btn-group .btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Hide all modes (with null checks)
        if (singleMode) singleMode.style.display = 'none';
        if (batchMode) batchMode.style.display = 'none';
        if (csvMode) csvMode.style.display = 'none';
        if (progressContainer) progressContainer.style.display = 'none';

        // Show selected mode
        switch(mode) {
            case 'single':
                if (singleMode) singleMode.style.display = 'block';
                if (singleModeBtn) singleModeBtn.classList.add('active');
                break;
            case 'batch':
                if (batchMode) batchMode.style.display = 'block';
                if (batchModeBtn) batchModeBtn.classList.add('active');
                if (typeof updateBatchSubmitButton === 'function') updateBatchSubmitButton();
                break;
            case 'csv':
                if (csvMode) csvMode.style.display = 'block';
                if (csvModeBtn) csvModeBtn.classList.add('active');
                break;
        }
    }

    // Single Mode
    async function handleSingleSubmit(e) {
        e.preventDefault();
        
        const companyName = document.getElementById('singleCompanyName').value.trim();
        const companyUrl = document.getElementById('singleCompanyUrl').value.trim();
        
        if (!companyName || !companyUrl) {
            showAlert('Please fill in both company name and website URL.', 'danger');
            return;
        }

        setSingleFormState(false);
        showProgress('single', [{name: companyName, url: companyUrl, status: 'starting'}]);

        try {
            const jobId = await startSingleJob(companyName, companyUrl);
            await monitorSingleJob(jobId, companyName);
        } catch (error) {
            showAlert(`Error: ${error.message}`, 'danger');
            setSingleFormState(true);
        }
    }

    function setSingleFormState(enabled) {
        singleSubmitBtn.disabled = !enabled;
        document.getElementById('singleCompanyName').disabled = !enabled;
        document.getElementById('singleCompanyUrl').disabled = !enabled;
        singleSubmitBtn.textContent = enabled ? 'Generate Teardown' : 'Processing...';
    }

    // Batch Mode
    function addCompanyRow() {
        const rowId = 'company-' + Date.now();
        const row = document.createElement('div');
        row.className = 'company-row mb-2';
        row.id = rowId;
        row.innerHTML = `
            <div class="row g-2">
                <div class="col-md-5">
                    <input type="text" class="form-control company-name" placeholder="Company Name" required>
                </div>
                <div class="col-md-6">
                    <input type="url" class="form-control company-url" placeholder="https://company.com" required>
                </div>
                <div class="col-md-1">
                    <button type="button" class="btn btn-outline-danger btn-sm remove-company" data-row-id="${rowId}">
                        ×
                    </button>
                </div>
            </div>
        `;
        
        companiesList.appendChild(row);
        
        // Add event listeners
        row.querySelector('.remove-company').addEventListener('click', function() {
            removeCompanyRow(this.dataset.rowId);
        });
        
        row.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', updateBatchSubmitButton);
        });
        
        updateBatchSubmitButton();
    }

    function removeCompanyRow(rowId) {
        const row = document.getElementById(rowId);
        if (row && companiesList.children.length > 1) {
            row.remove();
            updateBatchSubmitButton();
        }
    }

    function clearAllCompanies() {
        companiesList.innerHTML = '';
        addCompanyRow();
        updateBatchSubmitButton();
    }

    function updateBatchSubmitButton() {
        const companies = getBatchCompanies();
        batchSubmitBtn.disabled = companies.length === 0;
        batchSubmitBtn.textContent = companies.length > 0 ? 
            `Start Batch Processing (${companies.length} companies)` : 
            'Add companies to start';
    }

    function getBatchCompanies() {
        const companies = [];
        const rows = companiesList.querySelectorAll('.company-row');
        
        rows.forEach(row => {
            const nameInput = row.querySelector('.company-name');
            const urlInput = row.querySelector('.company-url');
            
            const name = nameInput.value.trim();
            const url = urlInput.value.trim();
            
            if (name && url) {
                companies.push({ name, url });
            }
        });
        
        return companies;
    }

    async function startBatchProcessing() {
        const companies = getBatchCompanies();
        if (companies.length === 0) {
            showAlert('Please add at least one company.', 'warning');
            return;
        }

        const maxConcurrent = 1; // Force sequential processing
        
        batchSubmitBtn.disabled = true;
        showProgress('batch', companies.map(c => ({...c, status: 'pending'})));

        try {
            batchProcessor = new BatchProcessor(companies, maxConcurrent);
            await batchProcessor.start();
            
            if (document.getElementById('autoRedirect').checked) {
                setTimeout(() => {
                    window.location.href = '/teardowns';
                }, 3000);
            }
        } catch (error) {
            showAlert(`Batch processing error: ${error.message}`, 'danger');
        } finally {
            batchSubmitBtn.disabled = false;
        }
    }

    // CSV Mode
    function handleCsvFile(event) {
        const file = event.target.files[0];
        if (!file) {
            csvPreview.innerHTML = 'Select a CSV file to preview companies';
            csvSubmitBtn.disabled = true;
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const csv = e.target.result;
                const lines = csv.split('\n').filter(line => line.trim());
                
                if (lines.length < 2) {
                    throw new Error('CSV must have at least a header and one data row');
                }

                const headers = lines[0].split(',').map(h => h.trim());
                if (!headers.includes('company_name') || !headers.includes('company_url')) {
                    throw new Error('CSV must have company_name and company_url columns');
                }

                csvCompanies = [];
                let previewHtml = '<table class="table table-sm"><thead><tr>';
                headers.forEach(header => {
                    previewHtml += `<th>${header}</th>`;
                });
                previewHtml += '</tr></thead><tbody>';

                for (let i = 1; i < Math.min(lines.length, 11); i++) {
                    const values = lines[i].split(',').map(v => v.trim());
                    const nameIndex = headers.indexOf('company_name');
                    const urlIndex = headers.indexOf('company_url');
                    
                    if (values[nameIndex] && values[urlIndex]) {
                        csvCompanies.push({
                            name: values[nameIndex],
                            url: values[urlIndex]
                        });
                    }

                    previewHtml += '<tr>';
                    values.forEach(value => {
                        previewHtml += `<td>${escapeHtml(value)}</td>`;
                    });
                    previewHtml += '</tr>';
                }

                previewHtml += '</tbody></table>';
                if (lines.length > 11) {
                    previewHtml += `<small class="text-muted">... and ${lines.length - 6} more rows</small>`;
                }

                csvPreview.innerHTML = previewHtml;
                csvSubmitBtn.disabled = csvCompanies.length === 0;
                csvSubmitBtn.textContent = `Process ${csvCompanies.length} Companies`;

            } catch (error) {
                csvPreview.innerHTML = `<div class="text-danger">Error: ${error.message}</div>`;
                csvSubmitBtn.disabled = true;
            }
        };
        reader.readAsText(file);
    }

    async function startCsvProcessing() {
        if (csvCompanies.length === 0) {
            showAlert('No valid companies found in CSV.', 'warning');
            return;
        }

        const maxConcurrent = 1; // Force sequential processing for CSV
        
        csvSubmitBtn.disabled = true;
        showProgress('csv', csvCompanies.map(c => ({...c, status: 'pending'})));

        try {
            batchProcessor = new BatchProcessor(csvCompanies, maxConcurrent);
            await batchProcessor.start();
            
            setTimeout(() => {
                window.location.href = '/teardowns';
            }, 3000);
        } catch (error) {
            showAlert(`CSV processing error: ${error.message}`, 'danger');
        } finally {
            csvSubmitBtn.disabled = false;
        }
    }

    function downloadSampleCsvFile(e) {
        e.preventDefault();
        const csvContent = `company_name,company_url
Solestial,https://solestial.com
SpaceX,https://spacex.com
Relativity Space,https://relativityspace.com
Rocket Lab,https://rocketlabusa.com
Planet Labs,https://planet.com`;

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'sample_companies.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Batch Processor Class
    class BatchProcessor {
        constructor(companies, maxConcurrent = 1) {
            this.companies = companies.map((c, i) => ({
                ...c,
                id: `batch_${Date.now()}_${i}`,
                status: 'pending',
                jobId: null,
                error: null
            }));
            this.maxConcurrent = maxConcurrent;
            this.activeJobs = new Set();
            this.completedCount = 0;
            this.running = false;
        }

        async start() {
            this.running = true;
            
            // Start initial batch
            await this.processNext();
            
            // Monitor until all complete
            while (this.running && this.completedCount < this.companies.length) {
                await this.sleep(2000);
                await this.updateJobStatuses();
                await this.processNext();
            }
        }

        async processNext() {
            while (this.activeJobs.size < this.maxConcurrent && this.running) {
                const nextCompany = this.companies.find(c => c.status === 'pending');
                if (!nextCompany) break;

                try {
                    nextCompany.status = 'starting';
                    this.updateProgress();
                    
                    const jobId = await startSingleJob(nextCompany.name, nextCompany.url);
                    nextCompany.jobId = jobId;
                    nextCompany.status = 'running';
                    this.activeJobs.add(nextCompany.id);
                    
                    this.updateProgress();
                } catch (error) {
                    nextCompany.status = 'failed';
                    nextCompany.error = error.message;
                    this.completedCount++;
                    this.updateProgress();
                }
            }
        }

        async updateJobStatuses() {
            const activeCompanies = this.companies.filter(c => c.status === 'running');
            
            for (const company of activeCompanies) {
                try {
                    const response = await fetch(`/api/job_status/${company.jobId}`);
                    const jobData = await response.json();
                    
                    if (response.ok) {
                        if (jobData.status === 'completed') {
                            company.status = 'completed';
                            this.activeJobs.delete(company.id);
                            this.completedCount++;
                        } else if (jobData.status === 'failed') {
                            company.status = 'failed';
                            company.error = jobData.error_message || 'Unknown error';
                            this.activeJobs.delete(company.id);
                            this.completedCount++;
                        }
                        // 'running' and 'pending' statuses remain unchanged
                    }
                } catch (error) {
                    console.error(`Error checking job ${company.jobId}:`, error);
                }
            }
            
            this.updateProgress();
        }

        updateProgress() {
            showProgress('batch', this.companies);
        }

        sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
    }

    // Utility Functions
    async function startSingleJob(companyName, companyUrl) {
        const response = await fetch('/api/start_teardown', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: companyName,
                company_url: companyUrl
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to start teardown');
        }

        return data.job_id;
    }

    async function monitorSingleJob(jobId, companyName) {
        while (true) {
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            const response = await fetch(`/api/job_status/${jobId}`);
            const jobData = await response.json();
            
            if (!response.ok) {
                throw new Error('Failed to check job status');
            }
            
            showProgress('single', [{
                name: companyName,
                status: jobData.status,
                error: jobData.error_message
            }]);
            
            if (jobData.status === 'completed') {
                setTimeout(() => {
                    window.location.href = '/teardowns';
                }, 2000);
                break;
            } else if (jobData.status === 'failed') {
                setSingleFormState(true);
                throw new Error(jobData.error_message || 'Job failed');
            }
        }
    }

    function showProgress(mode, companies) {
        const completed = companies.filter(c => c.status === 'completed').length;
        const failed = companies.filter(c => c.status === 'failed').length;
        const running = companies.filter(c => c.status === 'running').length;
        const total = companies.length;
        
        const progressPercent = Math.round(((completed + failed) / total) * 100);
        
        let progressHtml = `
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">${mode === 'single' ? 'Processing' : 'Batch Processing'} Progress</h5>
                </div>
                <div class="card-body">
                    <div class="progress mb-3" style="height: 25px;">
                        <div class="progress-bar ${progressPercent === 100 ? 'bg-success' : ''}" 
                             role="progressbar" style="width: ${progressPercent}%">
                            ${progressPercent}% (${completed + failed}/${total})
                        </div>
                    </div>
                    <div class="company-list" style="max-height: 300px; overflow-y: auto;">
        `;
        
        companies.forEach(company => {
            const statusClass = {
                'pending': 'secondary',
                'starting': 'info',
                'running': 'primary',
                'completed': 'success',
                'failed': 'danger'
            }[company.status] || 'secondary';
            
            const statusText = {
                'pending': 'Pending',
                'starting': 'Starting...',
                'running': 'Running',
                'completed': 'Completed',
                'failed': 'Failed'
            }[company.status] || company.status;
            
            progressHtml += `
                <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                    <div>
                        <strong>${escapeHtml(company.name)}</strong>
                        <br><small class="text-muted">${escapeHtml(company.url)}</small>
                        ${company.error ? `<br><small class="text-danger">${escapeHtml(company.error)}</small>` : ''}
                    </div>
                    <span class="badge bg-${statusClass}">${statusText}</span>
                </div>
            `;
        });
        
        progressHtml += `
                    </div>
                    <div class="mt-3 text-center">
                        <small class="text-muted">
                            ${completed} completed, ${failed} failed, ${running} running
                            ${mode !== 'single' ? ` • <a href="/teardowns" target="_blank">View results</a>` : ''}
                        </small>
                    </div>
                </div>
            </div>
        `;
        
        progressContainer.innerHTML = progressHtml;
        progressContainer.style.display = 'block';
    }

    function showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        progressContainer.innerHTML = alertHtml;
        progressContainer.style.display = 'block';
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = progressContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});