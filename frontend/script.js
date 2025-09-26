const API_BASE = 'http://localhost:8000';

// Tab functionality
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab and activate button
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
    
    // Hide results
    hideResults();
}

// File upload handlers
function setupFileUpload(uploadId, fileId, buttonId) {
    const uploadArea = document.getElementById(uploadId);
    const fileInput = document.getElementById(fileId);
    const button = document.getElementById(buttonId);
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            fileInput.files = files;
            handleFileSelect(uploadArea, button, files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(uploadArea, button, e.target.files[0]);
        }
    });
}

function handleFileSelect(uploadArea, button, file) {
    uploadArea.classList.add('has-file');
    uploadArea.querySelector('.upload-text p').textContent = `Selected: ${file.name}`;
    button.disabled = false;
}

// API calls
async function signPDF() {
    const fileInput = document.getElementById('sign-file');
    const file = fileInput.files[0];
    
    if (!file) return;
    
    showLoading();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/sign`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const uuid = response.headers.get('X-InkCrypt-UUID');
            
            // Download signed file
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `signed_${file.name}`;
            a.click();
            URL.revokeObjectURL(url);
            
            showResults({
                success: true,
                title: '✅ PDF Signed Successfully',
                message: 'Your PDF has been digitally signed and is ready for download.',
                details: { uuid: uuid }
            });
        } else {
            throw new Error('Signing failed');
        }
    } catch (error) {
        showResults({
            success: false,
            title: '❌ Signing Failed',
            message: error.message
        });
    } finally {
        hideLoading();
    }
}

async function verifyPDF() {
    const fileInput = document.getElementById('verify-file');
    const file = fileInput.files[0];
    
    if (!file) return;
    
    showLoading();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/verify`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.valid) {
            showResults({
                success: true,
                title: '✅ Document Verified',
                message: result.reason,
                details: {
                    uuid: result.uuid,
                    signed_at: result.signed_at,
                    signer: result.signer,
                    confidence: result.confidence
                }
            });
        } else {
            showResults({
                success: false,
                title: result.confidence === 'REVOKED' ? '⚠️ Document Revoked' : '❌ Verification Failed',
                message: result.reason,
                details: { confidence: result.confidence }
            });
        }
    } catch (error) {
        showResults({
            success: false,
            title: '❌ Verification Error',
            message: error.message
        });
    } finally {
        hideLoading();
    }
}

async function revokeDocument() {
    const uuidInput = document.getElementById('revoke-uuid');
    const uuid = uuidInput.value.trim();
    
    if (!uuid) {
        showResults({
            success: false,
            title: '❌ Invalid UUID',
            message: 'Please enter a valid document UUID'
        });
        return;
    }
    
    showLoading();
    
    const formData = new FormData();
    formData.append('uuid', uuid);
    
    try {
        const response = await fetch(`${API_BASE}/revoke`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showResults({
                success: true,
                title: '✅ Document Revoked',
                message: result.message,
                details: { uuid: uuid }
            });
            uuidInput.value = '';
        } else {
            throw new Error(result.detail || 'Revocation failed');
        }
    } catch (error) {
        showResults({
            success: false,
            title: '❌ Revocation Failed',
            message: error.message
        });
    } finally {
        hideLoading();
    }
}

// UI helpers
function showResults(result) {
    const resultsDiv = document.getElementById('results');
    const contentDiv = document.getElementById('result-content');
    
    resultsDiv.className = `results ${result.success ? 'success' : 'error'}`;
    
    let html = `<h4>${result.title}</h4><p>${result.message}</p>`;
    
    if (result.details) {
        html += '<div class="result-details">';
        for (const [key, value] of Object.entries(result.details)) {
            html += `<p><strong>${key.replace('_', ' ').toUpperCase()}:</strong> ${value}</p>`;
        }
        html += '</div>';
    }
    
    contentDiv.innerHTML = html;
    resultsDiv.classList.remove('hidden');
    
    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

function hideResults() {
    document.getElementById('results').classList.add('hidden');
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupFileUpload('sign-upload', 'sign-file', 'sign-btn');
    setupFileUpload('verify-upload', 'verify-file', 'verify-btn');
    
    document.getElementById('sign-btn').addEventListener('click', signPDF);
    document.getElementById('verify-btn').addEventListener('click', verifyPDF);
    document.getElementById('revoke-btn').addEventListener('click', revokeDocument);
});