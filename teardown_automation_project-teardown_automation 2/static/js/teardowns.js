document.addEventListener('DOMContentLoaded', function() {
    const teardownsList = document.getElementById('teardownsList');
    const emptyState = document.getElementById('emptyState');
    const teardownModal = new bootstrap.Modal(document.getElementById('teardownModal'));
    const teardownModalTitle = document.getElementById('teardownModalTitle');
    const teardownContent = document.getElementById('teardownContent');
    
    // Updated to handle both download buttons
    const downloadMdBtn = document.getElementById('downloadMdBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    
    // Fallback for old single download button (if it exists)
    const downloadBtn = document.getElementById('downloadBtn');

    let currentTeardown = null;

    // Load teardowns on page load
    loadTeardowns();

    // Auto-refresh every 30 seconds to catch new teardowns
    setInterval(loadTeardowns, 30000);

    async function loadTeardowns() {
        try {
            const response = await fetch('/api/teardowns');
            const teardowns = await response.json();
            
            if (!response.ok) {
                throw new Error('Failed to load teardowns');
            }
            
            displayTeardowns(teardowns);
            
        } catch (error) {
            console.error('Error loading teardowns:', error);
            showError('Failed to load teardowns');
        }
    }

    function displayTeardowns(teardowns) {
        if (teardowns.length === 0) {
            teardownsList.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        
        // Sort by creation date (newest first)
        teardowns.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        teardownsList.innerHTML = teardowns.map(teardown => createTeardownCard(teardown)).join('');
        
        // Add click handlers for viewing teardowns
        document.querySelectorAll('.teardown-card').forEach(card => {
            card.addEventListener('click', function(e) {
                // Don't open modal if clicking on download buttons
                if (e.target.closest('.download-buttons')) {
                    return;
                }
                const teardownId = this.dataset.teardownId;
                openTeardown(teardownId);
            });
        });

        // Add click handlers for card download buttons
        document.querySelectorAll('.card-download-md').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const teardownId = this.dataset.teardownId;
                downloadTeardown(teardownId, 'md');
            });
        });

        document.querySelectorAll('.card-download-pdf').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const teardownId = this.dataset.teardownId;
                downloadTeardown(teardownId, 'pdf');
            });
        });
    }

    function createTeardownCard(teardown) {
        const createdDate = new Date(teardown.created_at).toLocaleDateString();
        const completedDate = new Date(teardown.completed_at).toLocaleDateString();
        
        return `
            <div class="card teardown-card shadow-sm mb-3" data-teardown-id="${teardown.id}" style="cursor: pointer;">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <h5 class="card-title mb-2">${escapeHtml(teardown.company_name)}</h5>
                            <a href="${escapeHtml(teardown.company_url)}" 
                               class="company-url" 
                               target="_blank" 
                               onclick="event.stopPropagation()">
                                ${escapeHtml(teardown.company_url)}
                            </a>
                            <div class="teardown-meta mt-2">
                                <small>
                                    <i class="bi bi-calendar"></i> Created: ${createdDate} | 
                                    Completed: ${completedDate}
                                </small>
                            </div>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="badge bg-success mb-2">Completed</span>
                            <div class="download-buttons mt-2">
                                <button class="btn btn-primary btn-sm card-download-md" 
                                        data-teardown-id="${teardown.id}"
                                        title="Download Markdown">
                                    <i class="bi bi-download"></i> MD
                                </button>
                                <button class="btn btn-danger btn-sm card-download-pdf" 
                                        data-teardown-id="${teardown.id}"
                                        title="Download PDF">
                                    <i class="bi bi-file-pdf"></i> PDF
                                </button>
                            </div>
                            <div class="mt-1">
                                <small class="text-muted">Click card to view</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async function openTeardown(teardownId) {
        try {
            const response = await fetch(`/api/teardown/${teardownId}`);
            const teardown = await response.json();
            
            if (!response.ok) {
                throw new Error(teardown.error || 'Failed to load teardown');
            }
            
            currentTeardown = teardown;
            teardownModalTitle.textContent = `${teardown.company_name} - Teardown Analysis`;
            
            // Convert markdown to HTML
            const htmlContent = marked.parse(teardown.content);
            teardownContent.innerHTML = htmlContent;
            
            teardownModal.show();
            
        } catch (error) {
            console.error('Error loading teardown:', error);
            showError('Failed to load teardown details');
        }
    }

    // Download functionality for modal buttons
    if (downloadMdBtn) {
        downloadMdBtn.addEventListener('click', function() {
            if (!currentTeardown) return;
            downloadTeardown(currentTeardown.id, 'md');
        });
    }

    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', function() {
            if (!currentTeardown) return;
            downloadTeardown(currentTeardown.id, 'pdf');
        });
    }

    // Fallback for old single download button
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            if (!currentTeardown) return;
            
            // Old blob-based download for backward compatibility
            const blob = new Blob([currentTeardown.content], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentTeardown.company_name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_teardown.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    // Unified download function
    function downloadTeardown(teardownId, format) {
        // Show loading state on buttons
        const buttons = document.querySelectorAll(`[data-teardown-id="${teardownId}"]`);
        buttons.forEach(btn => {
            if (btn.classList.contains(`card-download-${format}`) || 
                (format === 'md' && btn.id === 'downloadMdBtn') ||
                (format === 'pdf' && btn.id === 'downloadPdfBtn')) {
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i class="bi bi-hourglass-split"></i> ...';
                btn.disabled = true;
                
                // Reset after 3 seconds
                setTimeout(() => {
                    btn.innerHTML = originalHtml;
                    btn.disabled = false;
                }, 3000);
            }
        });

        // Determine download URL
        let downloadUrl;
        if (format === 'pdf') {
            downloadUrl = `/api/teardown/${teardownId}/download_pdf`;
        } else {
            downloadUrl = `/api/teardown/${teardownId}/download`;
        }

        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = ''; // Let server determine filename
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Show success message
        showSuccess(`${format.toUpperCase()} download started`);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showError(message) {
        // Create a temporary alert
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('.container').insertBefore(alert, document.querySelector('.container').firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    function showSuccess(message) {
        // Create a temporary success alert
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            <i class="bi bi-check-circle-fill me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('.container').insertBefore(alert, document.querySelector('.container').firstChild);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 3000);
    }
});