// State Management
let currentPage = 1;
const limit = 20;
let totalPages = 1;
let currentFilters = {
    q: '',
    title: '',
    location: '',
    yoe_min: 0,
    yoe_max: 20
};

// Global Current Time (aligned with rank.py config)
const CURRENT_TIME = new Date("2026-06-18");

// DOM Elements
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const filterToggleBtn = document.getElementById('filter-toggle-btn');
const toggleIcon = document.querySelector('.toggle-icon');
const advancedFiltersPanel = document.getElementById('advanced-filters-panel');

const filterTitle = document.getElementById('filter-title');
const filterLoc = document.getElementById('filter-loc');
const filterYoeMin = document.getElementById('filter-yoe-min');
const filterYoeMax = document.getElementById('filter-yoe-max');
const yoeValSpan = document.getElementById('yoe-val');
const resetFiltersBtn = document.getElementById('reset-filters-btn');

const candidateListContainer = document.getElementById('candidate-list-container');
const resultsCount = document.getElementById('results-count');
const telemetryStats = document.getElementById('telemetry-stats');

const pagerPrev = document.getElementById('pager-prev');
const pagerNext = document.getElementById('pager-next');
const pagerInfo = document.getElementById('pager-info');

const showcaseContainer = document.getElementById('showcase-content-container');
const directIdInput = document.getElementById('direct-id-input');
const directIdBtn = document.getElementById('direct-id-btn');

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    loadCandidates();
    setupEventListeners();
});

function setupEventListeners() {
    // Search Action
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // Toggle Advanced Filters
    filterToggleBtn.addEventListener('click', () => {
        const isOpen = advancedFiltersPanel.classList.toggle('open');
        toggleIcon.classList.toggle('open', isOpen);
    });

    // YoE Sliders Sync
    const updateYoeLabel = () => {
        const minVal = parseFloat(filterYoeMin.value);
        const maxVal = parseFloat(filterYoeMax.value);
        if (minVal > maxVal) {
            // Swap if they cross
            const temp = filterYoeMin.value;
            filterYoeMin.value = filterYoeMax.value;
            filterYoeMax.value = temp;
        }
        yoeValSpan.innerText = `${filterYoeMin.value} - ${filterYoeMax.value}`;
    };
    filterYoeMin.addEventListener('input', updateYoeLabel);
    filterYoeMax.addEventListener('input', updateYoeLabel);

    // Apply filters on slider mouseup or change
    filterYoeMin.addEventListener('change', handleSearch);
    filterYoeMax.addEventListener('change', handleSearch);
    filterTitle.addEventListener('input', debounce(handleSearch, 400));
    filterLoc.addEventListener('input', debounce(handleSearch, 400));

    // Reset Filters
    resetFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        filterTitle.value = '';
        filterLoc.value = '';
        filterYoeMin.value = 0;
        filterYoeMax.value = 20;
        yoeValSpan.innerText = '0 - 20';
        handleSearch();
    });

    // Pagination
    pagerPrev.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadCandidates();
        }
    });
    pagerNext.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadCandidates();
        }
    });

    // Direct Load
    directIdBtn.addEventListener('click', handleDirectLoad);
    directIdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleDirectLoad();
    });
}

// Helper Debounce Function
function debounce(func, delay) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

// Fetch Backend Statistics
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const json = await res.json();
        if (json.success) {
            telemetryStats.innerHTML = `
                <span class="stat-badge">
                    Indexed: <strong>${json.total_candidates.toLocaleString()}</strong> candidates (${json.file_size_mb} MB pool)
                </span>
            `;
        }
    } catch (e) {
        console.error("Error fetching server stats:", e);
        telemetryStats.innerHTML = `
            <span class="stat-badge loading-pulse">Offline / Error Connecting</span>
        `;
    }
}

// Handle Search Event
function handleSearch() {
    currentPage = 1;
    currentFilters.q = searchInput.value.trim();
    currentFilters.title = filterTitle.value.trim();
    currentFilters.location = filterLoc.value.trim();
    currentFilters.yoe_min = parseFloat(filterYoeMin.value);
    currentFilters.yoe_max = parseFloat(filterYoeMax.value);
    loadCandidates();
}

// Load List of Candidates from Server
async function loadCandidates() {
    candidateListContainer.innerHTML = `
        <div class="list-loader">
            <div class="spinner"></div>
            <p>Scanning candidate directory...</p>
        </div>
    `;

    const params = new URLSearchParams({
        q: currentFilters.q,
        title: currentFilters.title,
        location: currentFilters.location,
        yoe_min: currentFilters.yoe_min,
        yoe_max: currentFilters.yoe_max,
        page: currentPage,
        limit: limit
    });

    try {
        const res = await fetch(`/api/search?${params.toString()}`);
        const data = await res.json();
        
        if (data.success) {
            renderList(data.results);
            totalPages = data.pages || 1;
            resultsCount.innerText = `${data.total.toLocaleString()} found`;
            updatePaginationUI(data.total);
        } else {
            candidateListContainer.innerHTML = `<p class="list-loader">Search failed: ${data.error}</p>`;
        }
    } catch (e) {
        console.error("Error querying candidates:", e);
        candidateListContainer.innerHTML = `<p class="list-loader">Error connecting to server</p>`;
    }
}

// Render the Sidebar List
function renderList(candidates) {
    if (!candidates || candidates.length === 0) {
        candidateListContainer.innerHTML = `
            <div class="list-loader">
                <p>No candidates found matching the filters.</p>
            </div>
        `;
        return;
    }

    candidateListContainer.innerHTML = '';
    candidates.forEach(c => {
        const card = document.createElement('div');
        card.className = 'candidate-item-card';
        card.dataset.id = c.id;
        card.innerHTML = `
            <div class="row-header">
                <span class="item-name">${c.name}</span>
                <span class="item-id">${c.id}</span>
            </div>
            <div class="item-title">${c.title}</div>
            <div class="item-meta">
                <span>Exp: ${c.yoe} yrs</span>
                <span>${c.location}</span>
            </div>
        `;
        card.addEventListener('click', () => {
            document.querySelectorAll('.candidate-item-card').forEach(el => el.classList.remove('active'));
            card.classList.add('active');
            loadProfile(c.id);
        });
        candidateListContainer.appendChild(card);
    });
}

// Update Pagination controls
function updatePaginationUI(total) {
    pagerPrev.disabled = currentPage === 1;
    pagerNext.disabled = currentPage >= totalPages;
    pagerInfo.innerText = `Page ${currentPage} of ${totalPages || 1}`;
}

// Handle Direct Search Box Load
function handleDirectLoad() {
    const rawId = directIdInput.value.trim().toUpperCase();
    if (!rawId) return;
    
    // Check pattern matches CAND_xxxxxxx
    if (/^CAND_\d{7}$/.test(rawId)) {
        loadDirectId(rawId);
    } else {
        alert("Please enter a valid Candidate ID, e.g. CAND_0000042");
    }
}

// Helper to directly fetch and load an ID
function loadDirectId(id) {
    directIdInput.value = id;
    loadProfile(id);
}

// Fetch and Render Detailed Profile
async function loadProfile(id) {
    showcaseContainer.innerHTML = `
        <div class="list-loader" style="margin-top: 100px;">
            <div class="spinner"></div>
            <p>Retrieving record ${id} from disk...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/candidate?id=${id}`);
        const json = await res.json();
        
        if (json.success) {
            renderProfile(json.data);
        } else {
            showcaseContainer.innerHTML = `
                <div class="welcome-card card" style="border-color: var(--danger);">
                    <div class="welcome-graphic">⚠️</div>
                    <h2>Candidate Not Found</h2>
                    <p>${json.error}</p>
                    <button class="btn btn-primary" onclick="resetShowcase()">Return Home</button>
                </div>
            `;
        }
    } catch (e) {
        console.error("Error loading candidate profile:", e);
        showcaseContainer.innerHTML = `<p class="list-loader">Failed to connect. Please make sure backend is running.</p>`;
    }
}

function resetShowcase() {
    showcaseContainer.innerHTML = `
        <div class="welcome-card card">
            <div class="welcome-graphic">🎯</div>
            <h2>Candidate Profile Visualizer</h2>
            <p>Select a candidate from the directory list, or enter a specific candidate ID below to load their profile directly from the dataset.</p>
            <div class="direct-search-box">
                <input type="text" id="direct-id-input" placeholder="e.g. CAND_0000042">
                <button class="btn btn-primary" id="direct-id-btn">Load Profile</button>
            </div>
            <div class="quick-links">
                <p>Try searching these sample IDs:</p>
                <div class="quick-tags">
                    <span class="quick-tag" onclick="loadDirectId('CAND_0000001')">CAND_0000001</span>
                    <span class="quick-tag" onclick="loadDirectId('CAND_0000002')">CAND_0000002</span>
                    <span class="quick-tag" onclick="loadDirectId('CAND_0000004')">CAND_0000004</span>
                    <span class="quick-tag" onclick="loadDirectId('CAND_0000025')">CAND_0000025</span>
                </div>
            </div>
        </div>
    `;
    // Re-attach input event listener for direct load inside welcome view
    document.getElementById('direct-id-btn').addEventListener('click', handleDirectLoad);
    document.getElementById('direct-id-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleDirectLoad();
    });
}

// Client-Side Trap/Honeypot Scanner
function auditHoneypotSignals(c) {
    const alerts = [];
    const prof = c.profile || {};
    const history = c.career_history || [];
    const skills = c.skills || [];
    const yoe = parseFloat(prof.years_of_experience || 0);

    // 1. Check YoE vs Career Dates Span
    let earliestStart = null;
    history.forEach(job => {
        if (job.start_date) {
            const dt = new Date(job.start_date);
            if (!isNaN(dt.getTime())) {
                if (earliestStart === null || dt < earliestStart) {
                    earliestStart = dt;
                }
            }
        }
    });

    if (earliestStart) {
        const spanMs = CURRENT_TIME.getTime() - earliestStart.getTime();
        const spanYears = spanMs / (1000 * 60 * 60 * 24 * 365.25);
        if (yoe > spanYears + 2.0) {
            alerts.push(`Years of Experience (${yoe} yrs) exceeds chronological career span (${spanYears.toFixed(1)} yrs) by more than 2.0 years.`);
        }
    }

    // 2. Check Job Duration Mismatch
    history.forEach(job => {
        if (job.start_date) {
            const startDt = new Date(job.start_date);
            let endDt = CURRENT_TIME;
            if (job.end_date) {
                const checkEnd = new Date(job.end_date);
                if (!isNaN(checkEnd.getTime())) {
                    endDt = checkEnd;
                }
            }
            const calcDurMonths = (endDt.getTime() - startDt.getTime()) / (1000 * 60 * 60 * 24 * 30.4);
            const recordedDur = parseFloat(job.duration_months || 0);
            
            if (recordedDur > calcDurMonths + 3.0) {
                alerts.push(`Job duration mismatch at "${job.company}": Profile lists ${recordedDur} months, but calendar dates calculate to only ${calcDurMonths.toFixed(1)} months.`);
            }
            if (recordedDur < 0 || calcDurMonths < 0) {
                alerts.push(`Negative job duration detected at "${job.company}" (listed: ${recordedDur} months, calculated: ${calcDurMonths.toFixed(1)} months).`);
            }
        }
    });

    // 3. Expert skills with 0 duration
    const expertZeroSkills = [];
    skills.forEach(s => {
        const profLevel = s.proficiency || '';
        const duration = parseInt(s.duration_months);
        if (profLevel.toLowerCase().trim() === 'expert' && (isNaN(duration) || duration === 0)) {
            expertZeroSkills.push(s.name);
        }
    });
    if (expertZeroSkills.length >= 4) {
        alerts.push(`Expert proficiency stated for 4+ skills with 0 months of actual usage duration: [${expertZeroSkills.join(', ')}].`);
    }

    // 4. expected_salary_range_inr_lpa validation
    const signals = c.redrob_signals || {};
    const salary = signals.expected_salary_range_inr_lpa || {};
    if (salary.min && salary.max && parseFloat(salary.min) > parseFloat(salary.max)) {
        alerts.push(`Salary range limits are inverted (Min LPA: ${salary.min} > Max LPA: ${salary.max}).`);
    }

    return {
        isHoneypot: alerts.length > 0,
        reasons: alerts
    };
}

// Render Candidate Data
function renderProfile(c) {
    const prof = c.profile || {};
    const signals = c.redrob_signals || {};
    const history = c.career_history || [];
    const skills = c.skills || [];
    const edu = c.education || [];
    const certs = c.certifications || [];
    const langs = c.languages || [];

    const initials = prof.anonymized_name ? prof.anonymized_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'C';

    // Perform Honeypot scan
    const audit = auditHoneypotSignals(c);

    // Build Sieve Alert Banner
    let sieveHtml = '';
    if (audit.isHoneypot) {
        sieveHtml = `
            <div class="sieve-banner danger grid-span-full">
                <span class="sieve-icon">🚫</span>
                <div class="sieve-details">
                    <h3>Honeypot Flag Triggered (Trap Profile)</h3>
                    <p>The anomaly screening engine has flagged this candidate's history. Submitting this candidate to the evaluation portal will incur heavy point penalties.</p>
                    <ul>
                        ${audit.reasons.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    } else {
        sieveHtml = `
            <div class="sieve-banner success grid-span-full">
                <span class="sieve-icon">✅</span>
                <div class="sieve-details">
                    <h3>Clean Profile Audit</h3>
                    <p>Heuristics scan complete. No critical timeline conflicts, overlapping dates, or zero-duration expert skills anomalies were detected.</p>
                </div>
            </div>
        `;
    }

    // Work Mode formatting
    const workModeLabels = {
        'onsite': 'Onsite',
        'remote': 'Remote',
        'hybrid': 'Hybrid',
        'flexible': 'Flexible'
    };
    const workMode = workModeLabels[signals.preferred_work_mode] || signals.preferred_work_mode || 'Not specified';

    // Build profile details structure
    showcaseContainer.innerHTML = `
        <div class="profile-grid">
            <!-- Profile Banner -->
            <div class="profile-banner card grid-span-full">
                <div class="banner-identity">
                    <div class="avatar-circle">${initials}</div>
                    <div class="identity-details">
                        <h2>${prof.anonymized_name}</h2>
                        <div class="headline">${prof.headline || 'Product Specialist'}</div>
                        <div class="meta-row">
                            <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> ${prof.location}, ${prof.country}</span>
                            <span>&bull;</span>
                            <span>🏢 ${prof.current_company || 'Unknown Company'} (${prof.current_company_size || 'Unknown Size'})</span>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <span class="badge badge-yoe">${prof.years_of_experience || '0'} Years Exp</span>
                    <span class="badge badge-country">${prof.current_industry || 'Industry'}</span>
                </div>
            </div>

            <!-- Sieve Banner -->
            ${sieveHtml}

            <!-- Left Grid: Overview & Timeline -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <!-- Summary Card -->
                <div class="profile-card card">
                    <h3><span class="card-icon">📝</span> Summary</h3>
                    <p class="summary-text">${prof.summary || 'No summary listed.'}</p>
                </div>

                <!-- Career Timeline -->
                <div class="profile-card card">
                    <h3><span class="card-icon">💼</span> Experience Timeline</h3>
                    <div class="timeline-container">
                        ${history.map(job => {
                            const isCurrent = job.is_current || job.end_date === null;
                            return `
                                <div class="timeline-item ${isCurrent ? 'current' : ''}">
                                    <div class="timeline-dot"></div>
                                    <div class="job-card">
                                        <div class="job-header">
                                            <div class="job-role">
                                                <h4>${job.title}</h4>
                                                <p>${job.company}</p>
                                            </div>
                                            <div class="job-dates">
                                                <span class="badge ${isCurrent ? 'badge-yoe' : 'badge-country'}">${job.start_date} &rarr; ${job.end_date || 'Present'}</span>
                                                <span class="job-duration">${job.duration_months} months</span>
                                            </div>
                                        </div>
                                        <div class="job-meta-details">
                                            <span>Sector: ${job.industry || 'Unknown'}</span>
                                            <span>&bull;</span>
                                            <span>Scale: ${job.company_size || 'Unknown size'}</span>
                                        </div>
                                        <p class="job-desc">${job.description || 'No job description provided.'}</p>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>

            <!-- Right Grid: Skills, Education, Signals -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <!-- Redrob Signals -->
                <div class="profile-card card">
                    <h3><span class="card-icon">⚡</span> Redrob Platform Signals</h3>
                    <div class="signals-grid">
                        <div class="signal-tile">
                            <span class="signal-label">Profile Completeness</span>
                            <span class="signal-value ${signals.profile_completeness_score > 70 ? 'highlight-success' : 'highlight-warning'}">${signals.profile_completeness_score}%</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">Active Status</span>
                            <span class="signal-value">${signals.open_to_work_flag ? 'Open To Work' : 'Not Looking'}</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">Notice Period</span>
                            <span class="signal-value ${signals.notice_period_days <= 30 ? 'highlight-success' : (signals.notice_period_days <= 60 ? 'highlight-warning' : '')}">${signals.notice_period_days} Days</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">Preferred Mode</span>
                            <span class="signal-value">${workMode}</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">Expected Salary</span>
                            <span class="signal-value">${signals.expected_salary_range_inr_lpa ? `${signals.expected_salary_range_inr_lpa.min} - ${signals.expected_salary_range_inr_lpa.max} LPA` : 'NDA'}</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">Willing to Relocate</span>
                            <span class="signal-value">${signals.willing_to_relocate ? 'Yes' : 'No'}</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">Recruiter Response Rate</span>
                            <span class="signal-value ${signals.recruiter_response_rate > 0.6 ? 'highlight-success' : (signals.recruiter_response_rate < 0.3 ? 'highlight-danger' : 'highlight-warning')}">${signals.recruiter_response_rate ? Math.round(signals.recruiter_response_rate * 100) : 0}%</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">GitHub Activity Score</span>
                            <span class="signal-value ${signals.github_activity_score > 50 ? 'highlight-success' : (signals.github_activity_score === -1 ? '' : 'highlight-warning')}">${signals.github_activity_score === -1 ? 'None Linked' : signals.github_activity_score}</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">Interview Completion</span>
                            <span class="signal-value">${signals.interview_completion_rate ? Math.round(signals.interview_completion_rate * 100) : 0}%</span>
                        </div>
                        <div class="signal-tile">
                            <span class="signal-label">Last Active Date</span>
                            <span class="signal-value">${signals.last_active_date || 'N/A'}</span>
                        </div>
                    </div>
                </div>

                <!-- Skills -->
                <div class="profile-card card">
                    <h3><span class="card-icon">🛠️</span> Verified Skills</h3>
                    <div class="skills-container">
                        ${skills.sort((a,b) => {
                            const pOrder = { 'expert': 4, 'advanced': 3, 'intermediate': 2, 'beginner': 1 };
                            return (pOrder[b.proficiency] || 0) - (pOrder[a.proficiency] || 0);
                        }).map(s => `
                            <div class="skill-row">
                                <div class="skill-name-wrap">
                                    <span class="skill-title">${s.name}</span>
                                    <span class="skill-info-sub">Endorsements: ${s.endorsements || 0} &bull; Used: ${s.duration_months || 0} months</span>
                                </div>
                                <div class="skill-tags">
                                    <span class="proficiency-tag proficiency-${s.proficiency || 'beginner'}">${s.proficiency || 'beginner'}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Education -->
                <div class="profile-card card">
                    <h3><span class="card-icon">🎓</span> Academic Credentials</h3>
                    <div class="education-container">
                        ${edu.map(e => `
                            <div class="education-item">
                                <div class="edu-main">
                                    <h4>${e.degree} in ${e.field_of_study}</h4>
                                    <p class="edu-school">${e.institution}</p>
                                    <p>Grade: ${e.grade || 'N/A'}</p>
                                </div>
                                <div class="edu-tags">
                                    <span class="tier-badge tier-${e.tier || 'unknown'}">${e.tier ? e.tier.replace('_', ' ') : 'unknown'}</span>
                                    <span class="job-duration" style="font-size:10px;">${e.start_year} - ${e.end_year}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Certifications & Languages -->
                ${certs.length > 0 || langs.length > 0 ? `
                    <div class="profile-card card">
                        <h3><span class="card-icon">📜</span> Credentials & Languages</h3>
                        
                        ${certs.length > 0 ? `
                            <h4 style="font-size:12px; text-transform:uppercase; color:var(--text-muted); margin-bottom:8px; font-weight:600;">Certifications</h4>
                            <div class="badge-container" style="margin-bottom: 16px;">
                                ${certs.map(cert => `
                                    <div class="credential-tag">
                                        <span class="title">${cert.name}</span>
                                        <span class="sub">${cert.issuer} (${cert.year})</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}

                        ${langs.length > 0 ? `
                            <h4 style="font-size:12px; text-transform:uppercase; color:var(--text-muted); margin-bottom:8px; font-weight:600;">Languages</h4>
                            <div class="badge-container">
                                ${langs.map(l => `
                                    <div class="credential-tag">
                                        <span class="title">${l.language}</span>
                                        <span class="sub">${l.proficiency}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}
