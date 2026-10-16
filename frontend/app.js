/**
 * Enterprise Knowledge Navigator - Full-Stack Single Page Application Controller
 * Handles Public Landing Page, Authentication & Role Verification,
 * Role-Based Dashboards (Admin, Worker, Analyst), Document Ingestion,
 * Grounded RAG Assistant, Interactive D3.js Knowledge Graph, and Quality Benchmarks.
 */

document.addEventListener('DOMContentLoaded', () => {

  // ============================================================================
  // GLOBAL STATE
  // ============================================================================
  let currentUser = null;
  let authToken = localStorage.getItem('ek_token');

  // Top-Level View Containers
  const landingView = document.getElementById('landingView');
  const authView = document.getElementById('authView');
  const authenticatedAppView = document.getElementById('authenticatedAppView');

  // Auth Cards
  const loginCard = document.getElementById('loginCard');
  const signupCard = document.getElementById('signupCard');
  const forgotPasswordCard = document.getElementById('forgotPasswordCard');

  // App Views & Nav
  const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
  const appViews = document.querySelectorAll('.app-view');
  const headerTitle = document.getElementById('headerViewTitle');
  const headerSubtitle = document.getElementById('headerViewSubtitle');
  const headerBreadcrumb = document.getElementById('headerBreadcrumb');

  const viewTitles = {
    dashboard: { title: "Executive Dashboard", subtitle: "Enterprise Knowledge Discovery & Grounded Retrieval System" },
    assistant: { title: "Search & Ask AI", subtitle: "Factual Retrieval-Augmented Generation & GraphRAG Synthesis" },
    documents: { title: "Document Library & Ingestion", subtitle: "Multi-Format Enterprise File Processing & Extraction Pipeline" },
    collections: { title: "Collections & Folders", subtitle: "Department, Project & Security Domain Document Categorization" },
    search: { title: "Hybrid Search & Retrieval", subtitle: "Multi-Mode Vector Similarity & Lexical Keyword Search" },
    saved: { title: "Saved Insights & Bookmarks", subtitle: "Bookmarked Answers, Citations, Annotations & Knowledge Snippets" },
    history: { title: "Search History & Telemetry", subtitle: "Chronological Search Audit Trail & Retrieved Document Chunks" },
    graph: { title: "Enterprise Knowledge Graph", subtitle: "Interactive Semantic Entity & Relationship Topology" },
    evaluation: { title: "Quality Evaluation & Benchmarks", subtitle: "Quantitative Precision@K, MRR, Grounding & Latency Telemetry" },
    reports: { title: "Reports & Data Export Center", subtitle: "Export Document Registry, Evaluation Benchmarks & Operational Logs" },
    users: { title: "User Management & Access Control", subtitle: "Provision Accounts, Assign Roles & Review Active Sessions" },
    roles: { title: "Roles & Permissions Matrix", subtitle: "Fine-Grained Capability & Access Control Rules" },
    audit: { title: "Operational Audit Logs", subtitle: "Cryptographically Verified Activity & Security Logs" },
    system: { title: "System Architecture & Health", subtitle: "FastAPI Health, Persistence Validation & ML Diagnostic Lab" },
    notifications: { title: "Platform Notifications", subtitle: "Real-Time Ingestion, Evaluation & Security Event Stream" },
    profile: { title: "Personal Profile & Preferences", subtitle: "Account Credentials, Verified Role & Interface Customization" }
  };

  // ============================================================================
  // 1. APPLICATION LIFECYCLE & ROUTING
  // ============================================================================

  function navigateTo(path, push = true) {
    if (push && window.location.pathname !== path) {
      history.pushState(null, '', path);
    }
    renderRoute(path);
  }

  function renderRoute(targetPath) {
    const path = (targetPath || window.location.pathname).toLowerCase();
    
    if (path === '/dashboard' || path === '/app/dashboard' || window.location.hash === '#dashboard') {
      if (currentUser) {
        showAuthenticatedApp();
      } else {
        navigateTo('/login', false);
        const loginFeedback = document.getElementById('loginFeedback');
        if (loginFeedback) {
          loginFeedback.className = 'alert-box alert-info';
          loginFeedback.textContent = 'Please sign in to access your authorized workspace.';
          loginFeedback.style.display = 'block';
        }
      }
    } else if (path === '/login' || window.location.hash === '#login') {
      if (currentUser) {
        navigateTo('/dashboard', false);
      } else {
        showAuthView('login');
      }
    } else if (path === '/signup' || path === '/register' || window.location.hash === '#signup' || window.location.hash === '#register') {
      if (currentUser) {
        navigateTo('/dashboard', false);
      } else {
        showAuthView('signup');
      }
    } else {
      // Default: Public landing page at '/' or '/app/'
      showLandingView();
    }
  }

  window.addEventListener('popstate', () => {
    renderRoute(window.location.pathname);
  });

  async function initApp() {
    if (authToken) {
      try {
        const res = await fetch('/api/v1/auth/me', {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (res.ok) {
          currentUser = await res.json();
        } else {
          // Token invalid or expired
          localStorage.removeItem('ek_token');
          authToken = null;
          currentUser = null;
        }
      } catch (err) {
        console.error('Session validation error:', err);
      }
    }

    // Determine initial view based on browser URL
    const currentPath = window.location.pathname.toLowerCase();
    if (currentPath === '/dashboard') {
      if (currentUser) {
        showAuthenticatedApp();
      } else {
        navigateTo('/login', false);
        const loginFeedback = document.getElementById('loginFeedback');
        if (loginFeedback) {
          loginFeedback.className = 'alert-box alert-info';
          loginFeedback.textContent = 'Please sign in to access your authorized workspace.';
          loginFeedback.style.display = 'block';
        }
      }
    } else if (currentPath === '/login') {
      if (currentUser) {
        navigateTo('/dashboard', false);
      } else {
        showAuthView('login');
      }
    } else if (currentPath === '/signup' || currentPath === '/register') {
      if (currentUser) {
        navigateTo('/dashboard', false);
      } else {
        showAuthView('signup');
      }
    } else {
      // First screen for root URL '/' is ALWAYS the public landing page!
      showLandingView();
    }
  }

  function showLandingView() {
    landingView.style.display = 'flex';
    authView.style.display = 'none';
    authenticatedAppView.style.display = 'none';

    // Update navigation elements based on auth status
    const unauthNavBtns = document.getElementById('unauthNavBtns');
    const authNavBtns = document.getElementById('authNavBtns');
    const navUserChip = document.getElementById('navUserChip');
    const unauthHeroBtns = document.getElementById('unauthHeroBtns');
    const authHeroBtns = document.getElementById('authHeroBtns');

    if (currentUser) {
      if (unauthNavBtns) unauthNavBtns.style.display = 'none';
      if (authNavBtns) authNavBtns.style.display = 'flex';
      if (navUserChip) navUserChip.textContent = `${currentUser.full_name} (${formatRoleName(currentUser.role)})`;
      if (unauthHeroBtns) unauthHeroBtns.style.display = 'none';
      if (authHeroBtns) authHeroBtns.style.display = 'flex';
    } else {
      if (unauthNavBtns) unauthNavBtns.style.display = 'flex';
      if (authNavBtns) authNavBtns.style.display = 'none';
      if (unauthHeroBtns) unauthHeroBtns.style.display = 'flex';
      if (authHeroBtns) authHeroBtns.style.display = 'none';
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function showAuthView(mode = 'login') {
    landingView.style.display = 'none';
    authView.style.display = 'flex';
    authenticatedAppView.style.display = 'none';

    if (mode === 'signup') {
      loginCard.style.display = 'none';
      signupCard.style.display = 'block';
      if (forgotPasswordCard) forgotPasswordCard.style.display = 'none';
    } else if (mode === 'forgot') {
      loginCard.style.display = 'none';
      signupCard.style.display = 'none';
      if (forgotPasswordCard) forgotPasswordCard.style.display = 'block';
    } else {
      loginCard.style.display = 'block';
      signupCard.style.display = 'none';
      if (forgotPasswordCard) forgotPasswordCard.style.display = 'none';
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function showAuthenticatedApp() {
    landingView.style.display = 'none';
    authView.style.display = 'none';
    authenticatedAppView.style.display = 'flex';

    if (currentUser && currentUser.role === 'admin') {
      await fetchAllRoles();
    }

    applyRolePermissions(currentUser.role);
    switchView('dashboard');
    loadDashboardMetrics();
    loadSystemHealth();
    fetchUnreadNotificationsCount();
  }

  // ============================================================================
  // 2. LANDING PAGE INTERACTIONS & LIVE SHOWCASE
  // ============================================================================

  // Landing Page Buttons
  const navLoginBtn = document.getElementById('navLoginBtn');
  const navGetStartedBtn = document.getElementById('navGetStartedBtn');
  const navGoDashboardBtn = document.getElementById('navGoDashboardBtn');
  const navLogoutBtn = document.getElementById('navLogoutBtn');
  const heroGetStartedBtn = document.getElementById('heroGetStartedBtn');
  const heroSignInBtn = document.getElementById('heroSignInBtn');
  const heroGoDashboardBtn = document.getElementById('heroGoDashboardBtn');
  const ctaGetStartedBtn = document.getElementById('ctaGetStartedBtn');
  const ctaLoginBtn = document.getElementById('ctaLoginBtn');
  const authBackToLanding = document.getElementById('authBackToLanding');
  const brandLogoBtn = document.getElementById('brandLogoBtn');
  const sidebarBrandBtn = document.getElementById('sidebarBrandBtn');

  if (navLoginBtn) navLoginBtn.addEventListener('click', () => navigateTo('/login'));
  if (heroSignInBtn) heroSignInBtn.addEventListener('click', () => navigateTo('/login'));
  if (ctaLoginBtn) ctaLoginBtn.addEventListener('click', () => navigateTo('/login'));

  if (navGetStartedBtn) navGetStartedBtn.addEventListener('click', () => navigateTo('/signup'));
  if (heroGetStartedBtn) heroGetStartedBtn.addEventListener('click', () => navigateTo('/signup'));
  if (ctaGetStartedBtn) ctaGetStartedBtn.addEventListener('click', () => navigateTo('/signup'));

  if (navGoDashboardBtn) navGoDashboardBtn.addEventListener('click', () => navigateTo('/dashboard'));
  if (heroGoDashboardBtn) heroGoDashboardBtn.addEventListener('click', () => navigateTo('/dashboard'));
  if (navLogoutBtn) navLogoutBtn.addEventListener('click', logout);

  if (authBackToLanding) authBackToLanding.addEventListener('click', (e) => { e.preventDefault(); navigateTo('/'); });
  if (brandLogoBtn) brandLogoBtn.addEventListener('click', (e) => { e.preventDefault(); navigateTo('/'); });
  if (sidebarBrandBtn) sidebarBrandBtn.addEventListener('click', (e) => { e.preventDefault(); navigateTo('/'); });

  // Footer Links
  const footLinkDash = document.getElementById('footLinkDash');
  const footLinkSearch = document.getElementById('footLinkSearch');
  const footLinkRag = document.getElementById('footLinkRag');
  const footLinkGraph = document.getElementById('footLinkGraph');
  [footLinkDash, footLinkSearch, footLinkRag, footLinkGraph].forEach(link => {
    if (link) link.addEventListener('click', (e) => {
      e.preventDefault();
      if (currentUser) {
        navigateTo('/dashboard');
      } else {
        navigateTo('/login');
      }
    });
  });

  // Hero Interactive Showcase Tabs
  const showcaseTabs = document.querySelectorAll('.showcase-tab');
  const showcaseQueryText = document.getElementById('showcaseQueryText');
  const showcaseAnswerText = document.getElementById('showcaseAnswerText');
  const showcaseCitationPill = document.getElementById('showcaseCitationPill');
  const showcaseGraphPill = document.getElementById('showcaseGraphPill');

  const showcaseSamples = {
    encryption: {
      query: "What encryption standard is mandated for enterprise data at rest?",
      answer: "All enterprise data at rest must employ AES-256 encryption without exception. Access to production databases requires hardware-based multi-factor authentication, and the Cloud Architecture Council conducts biannual vulnerability assessments.",
      citation: "📄 test_governance_manual.docx (Page 1)",
      graph: "Marcus Brody ➔ [DIRECTS] ➔ Enterprise Security Division"
    },
    leadership: {
      query: "Who directs the Enterprise Security Division and what policies do they establish?",
      answer: "Dr. Marcus Brody directs the Enterprise Security Division. The division establishes operational governance policies for PostgreSQL databases, Redis caching layers, and Docker container deployments across the cloud infrastructure.",
      citation: "📄 test_governance_manual.docx (Page 1)",
      graph: "Enterprise Security Division ➔ [GOVERNS] ➔ PostgreSQL & Redis"
    },
    remote: {
      query: "What is the policy for employees working remotely?",
      answer: "Employees are permitted to work remotely up to two days per week subject to direct manager approval. Full healthcare coverage includes comprehensive medical examinations, hospitalization, and prescription benefits.",
      citation: "📄 architecture_overview.txt (Page 1)",
      graph: "Remote Work Policy ➔ [GOVERNS] ➔ Telecommuting Guidelines"
    }
  };

  showcaseTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      showcaseTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const qKey = tab.getAttribute('data-q');
      const data = showcaseSamples[qKey];
      if (data) {
        showcaseQueryText.textContent = data.query;
        showcaseAnswerText.textContent = data.answer;
        showcaseCitationPill.textContent = data.citation;
        showcaseGraphPill.textContent = data.graph;
      }
    });
  });

  // ============================================================================
  // 3. AUTHENTICATION (LOGIN, SIGN UP, DEMO PILLS)
  // ============================================================================

  const switchToSignUpLink = document.getElementById('switchToSignUpLink');
  const switchToLoginLink = document.getElementById('switchToLoginLink');
  if (switchToSignUpLink) switchToSignUpLink.addEventListener('click', (e) => { e.preventDefault(); navigateTo('/signup'); });
  if (switchToLoginLink) switchToLoginLink.addEventListener('click', (e) => { e.preventDefault(); navigateTo('/login'); });

  // Demo Credentials Pills
  const demoAdminBtn = document.getElementById('demoAdminBtn');
  const demoWorkerBtn = document.getElementById('demoWorkerBtn');
  const demoAnalystBtn = document.getElementById('demoAnalystBtn');
  const loginEmail = document.getElementById('loginEmail');
  const loginPassword = document.getElementById('loginPassword');
  const roleTabs = document.querySelectorAll('.role-tab');
  const roleDescText = document.getElementById('roleDescText');

  const roleDescriptions = {
    admin: "Full system administration, user provisioning, and technical telemetry.",
    knowledge_worker: "Search enterprise repository, ask questions, and explore citations.",
    analyst: "Explore knowledge graph topology, evaluate benchmarks, and review analytics."
  };

  function selectRoleTab(role) {
    roleTabs.forEach(t => {
      if (t.getAttribute('data-role') === role) {
        t.classList.add('active');
      } else {
        t.classList.remove('active');
      }
    });
    if (roleDescText && roleDescriptions[role]) {
      roleDescText.textContent = roleDescriptions[role];
    }
  }

  roleTabs.forEach(tab => {
    tab.addEventListener('click', () => selectRoleTab(tab.getAttribute('data-role')));
  });

  if (demoAdminBtn) {
    demoAdminBtn.addEventListener('click', () => {
      loginEmail.value = 'admin@eknavigator.com';
      loginPassword.value = 'Admin@123456';
      selectRoleTab('admin');
    });
  }

  if (demoWorkerBtn) {
    demoWorkerBtn.addEventListener('click', () => {
      loginEmail.value = 'worker@eknavigator.com';
      loginPassword.value = 'Worker@123456';
      selectRoleTab('knowledge_worker');
    });
  }

  if (demoAnalystBtn) {
    demoAnalystBtn.addEventListener('click', () => {
      loginEmail.value = 'analyst@eknavigator.com';
      loginPassword.value = 'Analyst@123456';
      selectRoleTab('analyst');
    });
  }

  // Password Visibility Toggle
  const toggleLoginPasswordBtn = document.getElementById('toggleLoginPasswordBtn');
  if (toggleLoginPasswordBtn) {
    toggleLoginPasswordBtn.addEventListener('click', () => {
      loginPassword.type = loginPassword.type === 'password' ? 'text' : 'password';
    });
  }

  const toggleSignupPasswordBtn = document.getElementById('toggleSignupPasswordBtn');
  const signupPassword = document.getElementById('signupPassword');
  if (toggleSignupPasswordBtn) {
    toggleSignupPasswordBtn.addEventListener('click', () => {
      signupPassword.type = signupPassword.type === 'password' ? 'text' : 'password';
    });
  }

  // Password Strength Checker
  if (signupPassword) {
    signupPassword.addEventListener('input', () => {
      const val = signupPassword.value;
      const bar = document.getElementById('strengthBar');
      const text = document.getElementById('strengthText');
      if (!bar || !text) return;

      if (!val) {
        bar.className = 'strength-bar';
        text.textContent = 'Password Strength: None';
        return;
      }

      let score = 0;
      if (val.length >= 8) score++;
      if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;

      if (score <= 1) {
        bar.className = 'strength-bar weak';
        text.textContent = 'Password Strength: Weak';
      } else if (score === 2) {
        bar.className = 'strength-bar fair';
        text.textContent = 'Password Strength: Fair';
      } else if (score === 3) {
        bar.className = 'strength-bar good';
        text.textContent = 'Password Strength: Good';
      } else {
        bar.className = 'strength-bar strong';
        text.textContent = 'Password Strength: Strong';
      }
    });
  }

  // ============================================================================
  // FORGOT PASSWORD / OTP RECOVERY WIZARD (3-Step Real Backend Verification)
  // ============================================================================
  const forgotPasswordLink = document.getElementById('forgotPasswordLink');
  const fpCancelLink = document.getElementById('fpCancelLink');
  const fpRequestForm = document.getElementById('fpRequestForm');
  const fpVerifyForm = document.getElementById('fpVerifyForm');
  const fpResetForm = document.getElementById('fpResetForm');
  const fpSuccessCard = document.getElementById('fpSuccessCard');
  const fpDoneLoginBtn = document.getElementById('fpDoneLoginBtn');
  const fpResendBtn = document.getElementById('fpResendBtn');

  let fpRequestId = null;
  let fpResetToken = null;
  let fpCountdownInterval = null;
  let fpCooldownSeconds = 60;
  let fpTargetMethod = 'email';
  let fpTargetValue = '';

  function resetFpWizard() {
    if (fpCountdownInterval) clearInterval(fpCountdownInterval);
    fpRequestId = null;
    fpResetToken = null;
    fpCooldownSeconds = 60;
    
    if (fpRequestForm) fpRequestForm.style.display = 'block';
    if (fpVerifyForm) fpVerifyForm.style.display = 'none';
    if (fpResetForm) fpResetForm.style.display = 'none';
    if (fpSuccessCard) fpSuccessCard.style.display = 'none';
    
    const reqFb = document.getElementById('fpRequestFeedback');
    const verFb = document.getElementById('fpVerifyFeedback');
    const rstFb = document.getElementById('fpResetFeedback');
    if (reqFb) reqFb.style.display = 'none';
    if (verFb) verFb.style.display = 'none';
    if (rstFb) rstFb.style.display = 'none';

    setFpStepper(1);
  }

  function setFpStepper(step) {
    const node1 = document.getElementById('stepNode1');
    const node2 = document.getElementById('stepNode2');
    const node3 = document.getElementById('stepNode3');
    const line1 = document.getElementById('stepLine1');
    const line2 = document.getElementById('stepLine2');

    if (node1) node1.className = step >= 1 ? 'step-node active' : 'step-node';
    if (node2) node2.className = step >= 2 ? 'step-node active' : 'step-node';
    if (node3) node3.className = step >= 3 ? 'step-node active' : 'step-node';
    if (line1) line1.style.backgroundColor = step >= 2 ? 'var(--primary)' : 'var(--border-color)';
    if (line2) line2.style.backgroundColor = step >= 3 ? 'var(--primary)' : 'var(--border-color)';
  }

  function startFpCooldown(seconds = 60) {
    if (fpCountdownInterval) clearInterval(fpCountdownInterval);
    fpCooldownSeconds = seconds;
    const timerDisplay = document.getElementById('fpTimerDisplay');
    const countdownEl = document.getElementById('fpCountdown');
    if (fpResendBtn) fpResendBtn.disabled = true;
    if (timerDisplay) timerDisplay.style.display = 'inline';
    if (countdownEl) countdownEl.textContent = fpCooldownSeconds;

    fpCountdownInterval = setInterval(() => {
      fpCooldownSeconds--;
      if (countdownEl) countdownEl.textContent = fpCooldownSeconds;
      if (fpCooldownSeconds <= 0) {
        clearInterval(fpCountdownInterval);
        if (fpResendBtn) fpResendBtn.disabled = false;
        if (timerDisplay) timerDisplay.style.display = 'none';
      }
    }, 1000);
  }

  if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener('click', (e) => {
      e.preventDefault();
      resetFpWizard();
      showAuthView('forgot');
    });
  }

  if (fpCancelLink) {
    fpCancelLink.addEventListener('click', (e) => {
      e.preventDefault();
      showAuthView('login');
    });
  }

  if (fpDoneLoginBtn) {
    fpDoneLoginBtn.addEventListener('click', () => {
      showAuthView('login');
    });
  }

  // Delivery Channel Radio Toggles
  const lblEmail = document.getElementById('lblMethodEmail');
  const lblSms = document.getElementById('lblMethodSms');
  const grpEmail = document.getElementById('fpTargetEmailGroup');
  const grpSms = document.getElementById('fpTargetPhoneGroup');

  if (lblEmail && lblSms) {
    lblEmail.addEventListener('click', () => {
      lblEmail.classList.add('active');
      lblSms.classList.remove('active');
      fpTargetMethod = 'email';
      if (grpEmail) grpEmail.style.display = 'block';
      if (grpSms) grpSms.style.display = 'none';
      const rEmail = lblEmail.querySelector('input');
      if (rEmail) rEmail.checked = true;
    });

    lblSms.addEventListener('click', () => {
      lblSms.classList.add('active');
      lblEmail.classList.remove('active');
      fpTargetMethod = 'sms';
      if (grpEmail) grpEmail.style.display = 'none';
      if (grpSms) grpSms.style.display = 'block';
      const rSms = lblSms.querySelector('input');
      if (rSms) rSms.checked = true;
    });
  }

  // Step 1: Request OTP
  if (fpRequestForm) {
    fpRequestForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fb = document.getElementById('fpRequestFeedback');
      const btn = document.getElementById('fpRequestSubmitBtn');
      fb.style.display = 'none';
      btn.disabled = true;
      btn.innerHTML = '<span>Requesting Passcode...</span>';

      const emailVal = document.getElementById('fpIdentifierEmail').value.trim();
      const phoneVal = document.getElementById('fpIdentifierPhone').value.trim();
      fpTargetValue = fpTargetMethod === 'email' ? emailVal : phoneVal;

      try {
        const res = await fetch('/api/v1/auth/forgot-password/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: fpTargetMethod === 'email' ? emailVal : undefined,
            phone_number: fpTargetMethod === 'sms' ? phoneVal : undefined,
            delivery_method: fpTargetMethod
          })
        });

        const data = await res.json();
        btn.disabled = false;
        btn.innerHTML = '<span>Send Verification Code</span> →';

        if (res.ok) {
          fpRequestId = data.request_id;
          document.getElementById('fpMaskedTarget').textContent = data.masked_destination || fpTargetValue;
          fpRequestForm.style.display = 'none';
          fpVerifyForm.style.display = 'block';
          setFpStepper(2);
          startFpCooldown(data.cooldown_seconds || 60);

          const verFb = document.getElementById('fpVerifyFeedback');
          if (verFb) {
            verFb.className = 'alert-box alert-info';
            verFb.textContent = data.message || 'Passcode dispatched. Please check your messages.';
            verFb.style.display = 'block';
          }
        } else {
          fb.className = 'alert-box alert-error';
          fb.textContent = data.detail || 'Failed to request OTP code.';
          fb.style.display = 'block';
        }
      } catch (err) {
        btn.disabled = false;
        btn.innerHTML = '<span>Send Verification Code</span> →';
        fb.className = 'alert-box alert-error';
        fb.textContent = `Network error: ${err.message}`;
        fb.style.display = 'block';
      }
    });
  }

  // Resend OTP Button
  if (fpResendBtn) {
    fpResendBtn.addEventListener('click', async () => {
      fpResendBtn.disabled = true;
      const verFb = document.getElementById('fpVerifyFeedback');
      try {
        const res = await fetch('/api/v1/auth/forgot-password/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: fpTargetMethod === 'email' ? fpTargetValue : undefined,
            phone_number: fpTargetMethod === 'sms' ? fpTargetValue : undefined,
            delivery_method: fpTargetMethod
          })
        });
        const data = await res.json();
        if (res.ok) {
          fpRequestId = data.request_id;
          startFpCooldown(data.cooldown_seconds || 60);
          if (verFb) {
            verFb.className = 'alert-box alert-success';
            verFb.textContent = 'New 6-digit passcode dispatched.';
            verFb.style.display = 'block';
          }
        } else {
          if (verFb) {
            verFb.className = 'alert-box alert-error';
            verFb.textContent = data.detail || 'Could not resend passcode.';
            verFb.style.display = 'block';
          }
        }
      } catch (err) {
        if (verFb) {
          verFb.className = 'alert-box alert-error';
          verFb.textContent = err.message;
          verFb.style.display = 'block';
        }
      }
    });
  }

  // Step 2: Verify OTP
  if (fpVerifyForm) {
    fpVerifyForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fb = document.getElementById('fpVerifyFeedback');
      const btn = document.getElementById('fpVerifySubmitBtn');
      const otpInput = document.getElementById('fpOtpInput');
      const otpCode = otpInput.value.trim();

      if (otpCode.length !== 6) {
        fb.className = 'alert-box alert-error';
        fb.textContent = 'Please enter a valid 6-digit numeric passcode.';
        fb.style.display = 'block';
        return;
      }

      fb.style.display = 'none';
      btn.disabled = true;
      btn.innerHTML = '<span>Verifying Passcode...</span>';

      try {
        const res = await fetch('/api/v1/auth/forgot-password/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            reset_request_id: fpRequestId,
            otp_code: otpCode
          })
        });

        const data = await res.json();
        btn.disabled = false;
        btn.innerHTML = '<span>Verify Passcode & Proceed</span> →';

        if (res.ok) {
          fpResetToken = data.reset_token;
          fpVerifyForm.style.display = 'none';
          fpResetForm.style.display = 'block';
          setFpStepper(3);

          const rstFb = document.getElementById('fpResetFeedback');
          if (rstFb) {
            rstFb.className = 'alert-box alert-info';
            rstFb.textContent = 'Identity verified. You may now specify your new password.';
            rstFb.style.display = 'block';
          }
        } else {
          fb.className = 'alert-box alert-error';
          fb.textContent = data.detail || 'Invalid verification passcode.';
          fb.style.display = 'block';
        }
      } catch (err) {
        btn.disabled = false;
        btn.innerHTML = '<span>Verify Passcode & Proceed</span> →';
        fb.className = 'alert-box alert-error';
        fb.textContent = `Network error: ${err.message}`;
        fb.style.display = 'block';
      }
    });
  }

  // Step 3: Reset Password
  if (fpResetForm) {
    fpResetForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fb = document.getElementById('fpResetFeedback');
      const btn = document.getElementById('fpResetSubmitBtn');
      const newPwd = document.getElementById('fpNewPassword').value;
      const confirmPwd = document.getElementById('fpConfirmPassword').value;

      if (newPwd !== confirmPwd) {
        fb.className = 'alert-box alert-error';
        fb.textContent = 'Passwords do not match. Please verify.';
        fb.style.display = 'block';
        return;
      }

      if (newPwd.length < 8) {
        fb.className = 'alert-box alert-error';
        fb.textContent = 'Password must be at least 8 characters long.';
        fb.style.display = 'block';
        return;
      }

      fb.style.display = 'none';
      btn.disabled = true;
      btn.innerHTML = '<span>Updating Credentials...</span>';

      try {
        const res = await fetch('/api/v1/auth/forgot-password/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            reset_token: fpResetToken,
            new_password: newPwd,
            confirm_password: confirmPwd
          })
        });

        const data = await res.json();
        btn.disabled = false;
        btn.innerHTML = '<span>Update Password</span>';

        if (res.ok) {
          fpResetForm.style.display = 'none';
          fpSuccessCard.style.display = 'block';
        } else {
          fb.className = 'alert-box alert-error';
          fb.textContent = data.detail || 'Failed to update password.';
          fb.style.display = 'block';
        }
      } catch (err) {
        btn.disabled = false;
        btn.innerHTML = '<span>Update Password</span>';
        fb.className = 'alert-box alert-error';
        fb.textContent = `Network error: ${err.message}`;
        fb.style.display = 'block';
      }
    });
  }

  // Login Form Submission
  const loginForm = document.getElementById('loginForm');
  const loginFeedback = document.getElementById('loginFeedback');
  const loginSubmitBtn = document.getElementById('loginSubmitBtn');

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      loginFeedback.style.display = 'none';
      loginSubmitBtn.disabled = true;
      loginSubmitBtn.innerHTML = '<span>Signing In...</span>';

      try {
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: loginEmail.value.trim(),
            password: loginPassword.value,
            remember_me: document.getElementById('loginRememberMe').checked
          })
        });

        const data = await res.json();
        if (res.ok) {
          authToken = data.access_token;
          currentUser = data.user;
          localStorage.setItem('ek_token', authToken);
          loginFeedback.className = 'alert-box alert-success';
          loginFeedback.textContent = `✓ Authenticated as ${currentUser.full_name} (${formatRoleName(currentUser.role)})`;
          loginFeedback.style.display = 'block';

          setTimeout(() => {
            navigateTo('/dashboard');
            loginSubmitBtn.disabled = false;
            loginSubmitBtn.innerHTML = '<span>Sign In</span>';
            loginFeedback.style.display = 'none';
          }, 450);
        } else {
          loginFeedback.className = 'alert-box alert-error';
          loginFeedback.textContent = data.detail || 'Authentication failed. Please verify credentials.';
          loginFeedback.style.display = 'block';
          loginSubmitBtn.disabled = false;
          loginSubmitBtn.innerHTML = '<span>Sign In</span>';
        }
      } catch (err) {
        loginFeedback.className = 'alert-box alert-error';
        loginFeedback.textContent = `Network error: ${err.message}`;
        loginFeedback.style.display = 'block';
        loginSubmitBtn.disabled = false;
        loginSubmitBtn.innerHTML = '<span>Sign In</span>';
      }
    });
  }

  // Sign Up Form Submission
  const signupForm = document.getElementById('signupForm');
  const signupFeedback = document.getElementById('signupFeedback');
  const signupSubmitBtn = document.getElementById('signupSubmitBtn');

  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      signupFeedback.style.display = 'none';

      const pwd = signupPassword.value;
      const confirmPwd = document.getElementById('signupConfirmPassword').value;
      if (pwd !== confirmPwd) {
        signupFeedback.className = 'alert-box alert-error';
        signupFeedback.textContent = 'Passwords do not match. Please re-enter.';
        signupFeedback.style.display = 'block';
        return;
      }

      if (pwd.length < 8) {
        signupFeedback.className = 'alert-box alert-error';
        signupFeedback.textContent = 'Password must be at least 8 characters long.';
        signupFeedback.style.display = 'block';
        return;
      }

      signupSubmitBtn.disabled = true;
      signupSubmitBtn.innerHTML = '<span>Creating Account...</span>';

      try {
        const phoneInput = document.getElementById('signupPhone');
        const res = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: document.getElementById('signupFullName').value.trim(),
            email: document.getElementById('signupEmail').value.trim(),
            phone_number: phoneInput ? phoneInput.value.trim() || undefined : undefined,
            password: pwd,
            organization: document.getElementById('signupOrg').value.trim(),
            role: document.getElementById('signupRoleSelect').value
          })
        });

        const data = await res.json();
        if (res.ok) {
          authToken = data.access_token;
          currentUser = data.user;
          localStorage.setItem('ek_token', authToken);
          signupFeedback.className = 'alert-box alert-success';
          signupFeedback.textContent = `✓ Account created successfully! Redirecting to console...`;
          signupFeedback.style.display = 'block';

          setTimeout(() => {
            navigateTo('/dashboard');
            signupSubmitBtn.disabled = false;
            signupSubmitBtn.innerHTML = '<span>Create Account</span>';
            signupFeedback.style.display = 'none';
          }, 500);
        } else {
          signupFeedback.className = 'alert-box alert-error';
          signupFeedback.textContent = data.detail || 'Registration failed.';
          signupFeedback.style.display = 'block';
          signupSubmitBtn.disabled = false;
          signupSubmitBtn.innerHTML = '<span>Create Account</span>';
        }
      } catch (err) {
        signupFeedback.className = 'alert-box alert-error';
        signupFeedback.textContent = `Network error: ${err.message}`;
        signupFeedback.style.display = 'block';
        signupSubmitBtn.disabled = false;
        signupSubmitBtn.innerHTML = '<span>Create Account</span>';
      }
    });
  }

  // Logout Actions
  function logout() {
    localStorage.removeItem('ek_token');
    authToken = null;
    currentUser = null;
    navigateTo('/');
  }

  const sidebarLogoutBtn = document.getElementById('sidebarLogoutBtn');
  const topLogoutBtn = document.getElementById('topLogoutBtn');
  if (sidebarLogoutBtn) sidebarLogoutBtn.addEventListener('click', logout);
  if (topLogoutBtn) topLogoutBtn.addEventListener('click', logout);

  // ============================================================================
  // 4. ROLE-BASED DASHBOARD PERMISSIONS
  // ============================================================================

  window.allRoles = [];

  function formatRoleName(role) {
    if (!role) return 'Enterprise User';
    if (role === 'admin') return 'Administrator';
    if (role === 'knowledge_worker') return 'Knowledge Worker';
    if (role === 'analyst') return 'Knowledge Analyst';
    if (window.allRoles && window.allRoles.length) {
      const found = window.allRoles.find(r => r.id === role || r.name.toLowerCase() === role.toLowerCase());
      if (found) return found.name;
    }
    return role.replace(/^role_/, '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  function applyRolePermissions(role) {
    const roleBadge = document.getElementById('sidebarRoleBadge');
    const userName = document.getElementById('sidebarUserName');
    const userEmail = document.getElementById('sidebarUserEmail');
    const userAvatar = document.getElementById('sidebarUserAvatar');
    const welcomeHeadline = document.getElementById('welcomeHeadline');
    const welcomeDesc = document.getElementById('welcomeDescription');
    const bannerQuickBtn = document.getElementById('bannerQuickActionBtn');

    if (currentUser) {
      if (roleBadge) roleBadge.textContent = formatRoleName(role);
      if (userName) userName.textContent = currentUser.full_name;
      if (userEmail) userEmail.textContent = currentUser.email;
      if (userAvatar) userAvatar.textContent = (currentUser.full_name || 'U').charAt(0).toUpperCase();
    }

    const userPerms = (currentUser && currentUser.permissions) ? currentUser.permissions : [];
    const isAdmin = role === 'admin' || userPerms.includes('system_admin');
    const isAnalyst = role === 'analyst' || (!isAdmin && (userPerms.includes('knowledge_graph') || userPerms.includes('evaluation')));
    const isWorker = !isAdmin && !isAnalyst;

    // Nav Item Filtering
    const workerItems = document.querySelectorAll('.role-item-worker');
    const analystItems = document.querySelectorAll('.role-item-analyst');
    const adminItems = document.querySelectorAll('.role-item-admin');

    if (isAdmin) {
      workerItems.forEach(el => el.style.display = 'flex');
      analystItems.forEach(el => el.style.display = 'flex');
      adminItems.forEach(el => el.style.display = 'flex');
      if (welcomeHeadline) welcomeHeadline.textContent = `Welcome back, ${currentUser.full_name} (Administrator)`;
      if (welcomeDesc) welcomeDesc.textContent = "Full platform administration, user provisioning, custom role governance, and technical telemetry active.";
      if (bannerQuickBtn) {
        bannerQuickBtn.textContent = "+ Provision User";
        bannerQuickBtn.onclick = () => switchView('users');
      }
    } else if (isAnalyst) {
      workerItems.forEach(el => el.style.display = 'none');
      analystItems.forEach(el => el.style.display = 'flex');
      adminItems.forEach(el => el.style.display = 'none');
      if (welcomeHeadline) welcomeHeadline.textContent = `Welcome back, ${currentUser.full_name} (${formatRoleName(role)})`;
      if (welcomeDesc) welcomeDesc.textContent = "Analyze knowledge graph relationships, explore topology, and review quality benchmarks.";
      if (bannerQuickBtn) {
        bannerQuickBtn.textContent = "Explore Graph";
        bannerQuickBtn.onclick = () => switchView('graph');
      }
    } else {
      workerItems.forEach(el => el.style.display = 'flex');
      analystItems.forEach(el => el.style.display = 'none');
      adminItems.forEach(el => el.style.display = 'none');
      if (welcomeHeadline) welcomeHeadline.textContent = `Welcome back, ${currentUser.full_name}`;
      if (welcomeDesc) welcomeDesc.textContent = "Explore enterprise documents, ask grounded questions, and review verified page citations.";
      if (bannerQuickBtn) {
        bannerQuickBtn.textContent = "Ask Assistant";
        bannerQuickBtn.onclick = () => switchView('assistant');
      }
    }

    // Role-tailored overview containers on Overview dashboard
    const adminDash = document.getElementById('adminDashboardContainer');
    const analystDash = document.getElementById('analystDashboardContainer');
    const workerDash = document.getElementById('workerDashboardContainer');

    if (adminDash) adminDash.style.display = isAdmin ? 'block' : 'none';
    if (analystDash) analystDash.style.display = isAnalyst ? 'block' : 'none';
    if (workerDash) workerDash.style.display = isWorker ? 'block' : 'none';
  }

  // ============================================================================
  // 5. AUTHENTICATED APPLICATION NAVIGATION & HEADER CONTROLS
  // ============================================================================

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = item.getAttribute('data-view');
      switchView(targetView);
    });
  });

  // Knowledge Base Group Subitems
  const navSubitems = document.querySelectorAll('.sidebar-nav .nav-subitem');
  navSubitems.forEach(sub => {
    sub.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = sub.getAttribute('data-view');
      switchView(targetView);

      if (sub.id === 'subitemUploadDocs') {
        const dropzone = document.getElementById('uploadDropzone');
        if (dropzone) dropzone.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else if (sub.id === 'subitemStatusDocs') {
        const table = document.getElementById('documentsTableBody');
        if (table) table.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  });

  // Collapsible Knowledge Base Toggle
  const kbGroupToggle = document.getElementById('kbGroupToggle');
  const kbSubitems = document.getElementById('kbSubitems');
  if (kbGroupToggle && kbSubitems) {
    kbGroupToggle.addEventListener('click', () => {
      const isCollapsed = kbSubitems.classList.toggle('collapsed');
      kbGroupToggle.classList.toggle('collapsed', isCollapsed);
      kbGroupToggle.setAttribute('aria-expanded', !isCollapsed);
    });
  }

  // Mobile Drawer Toggle
  const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const appSidebar = document.getElementById('appSidebar');

  if (mobileSidebarToggle && appSidebar) {
    mobileSidebarToggle.addEventListener('click', () => {
      appSidebar.classList.toggle('mobile-open');
    });
  }
  if (closeSidebarBtn && appSidebar) {
    closeSidebarBtn.addEventListener('click', () => {
      appSidebar.classList.remove('mobile-open');
    });
  }

  // Global Quick Search Bar
  const topQuickSearchInput = document.getElementById('topQuickSearchInput');
  if (topQuickSearchInput) {
    topQuickSearchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const q = topQuickSearchInput.value.trim();
        if (q) {
          const searchInput = document.getElementById('searchInput');
          if (searchInput) searchInput.value = q;
          switchView('search');
          executeSearch();
        }
      }
    });
  }

  // Top Bar User Dropdown Menu
  const userDropdownBtn = document.getElementById('userDropdownBtn');
  const userDropdownMenu = document.getElementById('userDropdownMenu');

  if (userDropdownBtn && userDropdownMenu) {
    userDropdownBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdownMenu.style.display = userDropdownMenu.style.display === 'none' ? 'block' : 'none';
    });

    document.addEventListener('click', (e) => {
      if (!userDropdownMenu.contains(e.target) && e.target !== userDropdownBtn) {
        userDropdownMenu.style.display = 'none';
      }
    });

    const menuItemProfile = document.getElementById('menuItemProfile');
    const menuItemNotif = document.getElementById('menuItemNotif');
    const menuItemAudit = document.getElementById('menuItemAudit');
    const menuItemLogout = document.getElementById('menuItemLogout');

    if (menuItemProfile) menuItemProfile.addEventListener('click', () => { userDropdownMenu.style.display = 'none'; switchView('profile'); });
    if (menuItemNotif) menuItemNotif.addEventListener('click', () => { userDropdownMenu.style.display = 'none'; switchView('notifications'); });
    if (menuItemAudit) menuItemAudit.addEventListener('click', () => { userDropdownMenu.style.display = 'none'; switchView('audit'); });
    if (menuItemLogout) menuItemLogout.addEventListener('click', () => { userDropdownMenu.style.display = 'none'; logout(); });
  }

  let currentActiveView = 'dashboard';

  function switchView(viewName) {
    currentActiveView = viewName;
    navItems.forEach(i => i.classList.remove('active'));
    navSubitems.forEach(s => s.classList.remove('active'));
    appViews.forEach(v => v.classList.remove('active'));

    const activeNav = document.querySelector(`.sidebar-nav .nav-item[data-view="${viewName}"]`);
    const activeView = document.getElementById(`view-${viewName}`);

    if (activeNav) activeNav.classList.add('active');
    if (activeView) activeView.classList.add('active');

    // Handle view-saved tab switching when navigating to 'saved' or 'history'
    if (viewName === 'history') {
      const activeSavedView = document.getElementById('view-saved');
      if (activeSavedView) activeSavedView.classList.add('active');
      const histTab = document.getElementById('tabSearchHistoryBtn');
      if (histTab) histTab.click();
    } else if (viewName === 'saved') {
      const savedTab = document.getElementById('tabSavedAnswersBtn');
      if (savedTab) savedTab.click();
    }

    if (viewTitles[viewName]) {
      headerTitle.textContent = viewTitles[viewName].title;
      if (headerSubtitle) headerSubtitle.textContent = viewTitles[viewName].subtitle;
      headerBreadcrumb.textContent = viewTitles[viewName].title;
    }

    // Close mobile drawer on navigation
    if (appSidebar) appSidebar.classList.remove('mobile-open');

    // Update Top User Details
    if (currentUser) {
      const initial = (currentUser.full_name || 'U').charAt(0).toUpperCase();
      const topAvatar = document.getElementById('topUserAvatar');
      const topName = document.getElementById('topUserName');
      const dropName = document.getElementById('dropdownName');
      const dropRole = document.getElementById('dropdownRole');
      const dropEmail = document.getElementById('dropdownEmail');

      if (topAvatar) topAvatar.textContent = initial;
      if (topName) topName.textContent = currentUser.full_name;
      if (dropName) dropName.textContent = currentUser.full_name;
      if (dropRole) dropRole.textContent = formatRoleName(currentUser.role);
      if (dropEmail) dropEmail.textContent = currentUser.email;
    }

    // Trigger View-Specific Data Loaders
    if (viewName === 'dashboard') loadDashboardMetrics();
    if (viewName === 'documents') loadDocumentsList();
    if (viewName === 'collections') loadCollections();
    if (viewName === 'saved' || viewName === 'history') loadSavedData();
    if (viewName === 'graph') loadKnowledgeGraph();
    if (viewName === 'evaluation') loadEvaluationHistory();
    if (viewName === 'reports') loadReportsData();
    if (viewName === 'users') loadUsersTable();
    if (viewName === 'roles') {
      loadCustomRoles();
      loadRolesMatrix();
    }
    if (viewName === 'audit') loadAuditLogs();
    if (viewName === 'system') loadSystemHealth();
    if (viewName === 'notifications') loadNotifications();
    if (viewName === 'profile') loadUserProfile();
  }

  // Header and user pill shortcuts
  const topNotifBtn = document.getElementById('topNotifBtn');
  const sidebarUserPill = document.querySelector('.sidebar-user-pill');

  if (topNotifBtn) topNotifBtn.addEventListener('click', () => switchView('notifications'));
  if (sidebarUserPill) sidebarUserPill.addEventListener('click', () => switchView('profile'));


  // ============================================================================
  // 6. DASHBOARD METRICS
  // ============================================================================

  async function loadDashboardMetrics() {
    try {
      const res = await fetch('/api/v1/navigator/dashboard/metrics');
      if (res.ok) {
        const data = await res.json();
        const setTxt = (id, val) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val;
        };

        // Shared / Worker Elements
        setTxt('dashTotalDocs', data.total_documents);
        setTxt('dashIndexedDocs', `${data.indexed_documents} Indexed`);
        setTxt('dashTotalChunks', data.total_chunks);
        setTxt('dashTotalEntities', data.total_entities);
        setTxt('dashTotalRelations', `${data.total_relations} Relations`);

        // Admin Overview Elements
        setTxt('adminDashTotalDocs', data.total_documents);
        setTxt('adminDashIndexedDocs', `${data.indexed_documents} Indexed`);
        setTxt('adminDashTotalChunks', data.total_chunks);

        // Analyst Overview Elements
        setTxt('analystDashEntities', data.total_entities);
        setTxt('analystDashRelations', `${data.total_relations} Relations`);

        if (data.latest_precision !== null) {
          const pStr = `${(data.latest_precision * 100).toFixed(1)}%`;
          setTxt('dashPrecision', pStr);
          setTxt('analystDashPrecision', pStr);
        }
        if (data.latest_mrr !== null) {
          const mStr = `MRR: ${data.latest_mrr.toFixed(3)}`;
          setTxt('dashMrr', mStr);
          setTxt('analystDashMrr', mStr);
        }
      }

      // Enrich admin telemetry
      if (currentUser && authToken) {
        const userPerms = currentUser.permissions || [];
        const isAdmin = currentUser.role === 'admin' || userPerms.includes('system_admin');
        if (isAdmin) {
          try {
            const [hRes, aRes] = await Promise.all([
              fetch('/api/v1/auth/admin/system-health', { headers: { 'Authorization': `Bearer ${authToken}` } }),
              fetch('/api/v1/auth/admin/audit-logs?limit=50', { headers: { 'Authorization': `Bearer ${authToken}` } })
            ]);
            if (hRes.ok) {
              const hData = await hRes.json();
              const elUsers = document.getElementById('adminDashTotalUsers');
              if (elUsers && hData.metrics) elUsers.textContent = hData.metrics.registered_users || 0;
            }
            if (aRes.ok) {
              const aData = await aRes.json();
              const elAudits = document.getElementById('adminDashTotalAudits');
              if (elAudits) elAudits.textContent = aData.length || 0;
            }
            const elRoles = document.getElementById('adminDashTotalRoles');
            if (elRoles && window.allRoles) {
              const roleCount = window.allRoles.length || 3;
              elRoles.textContent = `${roleCount} Role${roleCount === 1 ? '' : 's'}`;
            }
          } catch (e) {}
        }
      }

      await loadRecentDocsTable();
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
    }
  }

  const bannerUploadBtn = document.getElementById('bannerUploadBtn');
  const dashUploadBtn = document.getElementById('dashUploadBtn');
  function navigateToUpload() {
    switchView('documents');
    const dropzone = document.getElementById('uploadDropzone');
    if (dropzone) {
      dropzone.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
  if (bannerUploadBtn) bannerUploadBtn.addEventListener('click', navigateToUpload);
  if (dashUploadBtn) dashUploadBtn.addEventListener('click', navigateToUpload);

  // Dashboard Instant Knowledge Search Bar
  const dashSearchInput = document.getElementById('dashSearchInput');
  const dashSearchModeSelect = document.getElementById('dashSearchModeSelect');
  const dashExecuteSearchBtn = document.getElementById('dashExecuteSearchBtn');
  const dashAskAiBtn = document.getElementById('dashAskAiBtn');

  if (dashExecuteSearchBtn) {
    dashExecuteSearchBtn.addEventListener('click', () => {
      const q = dashSearchInput ? dashSearchInput.value.trim() : '';
      if (!q) return;
      const searchInput = document.getElementById('searchInput');
      const searchModeSelect = document.getElementById('searchModeSelect');
      if (searchInput) searchInput.value = q;
      if (searchModeSelect && dashSearchModeSelect) searchModeSelect.value = dashSearchModeSelect.value;
      switchView('search');
      executeSearch();
    });
  }

  if (dashSearchInput) {
    dashSearchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        if (dashExecuteSearchBtn) dashExecuteSearchBtn.click();
      }
    });
  }

  if (dashAskAiBtn) {
    dashAskAiBtn.addEventListener('click', () => {
      const q = dashSearchInput ? dashSearchInput.value.trim() : '';
      if (!q) {
        switchView('assistant');
        return;
      }
      const askInput = document.getElementById('askInput');
      if (askInput) askInput.value = q;
      switchView('assistant');
      executeAsk();
    });
  }

  async function loadRecentDocsTable() {
    try {
      const res = await fetch('/api/v1/navigator/documents');
      if (res.ok) {
        const data = await res.json();
        const tbody = document.getElementById('dashRecentDocsTable');
        if (!data.documents || data.documents.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No documents uploaded yet.</td></tr>';
          return;
        }
        tbody.innerHTML = data.documents.slice(0, 6).map(doc => {
          const isErr = doc.status === 'error' || doc.status === 'failed';
          const statusBadge = isErr
            ? `<span class="badge-tag tag-danger">${escapeHtml(doc.status)}</span>`
            : `<span class="badge-tag tag-success">${escapeHtml(doc.status)}</span>`;
          const actionsHtml = isErr
            ? `<div style="display: flex; gap: 0.35rem; align-items: center;">
                 <button class="btn btn-warning btn-sm" onclick="window.explainDocIssue('${doc.id}')" title="Diagnose Issue">Issue Details</button>
                 <button class="btn btn-secondary btn-sm" onclick="window.reprocessDoc('${doc.id}')" title="Retry Extraction">Retry</button>
               </div>`
            : `<div style="display: flex; gap: 0.35rem; align-items: center;">
                 <button class="btn btn-secondary btn-sm" onclick="window.previewDoc('${doc.id}', 1)" title="Preview Pages">Preview</button>
                 <button class="btn btn-outline btn-sm" onclick="window.downloadDoc('${doc.id}', '${escapeHtml(doc.filename)}')" title="Download File">Download</button>
               </div>`;

          return `
            <tr>
              <td><strong>${escapeHtml(doc.filename)}</strong></td>
              <td><span class="badge-tag tag-primary">${escapeHtml(doc.file_type)}</span></td>
              <td>${(doc.file_size_bytes / 1024).toFixed(1)} KB</td>
              <td>${doc.page_count}</td>
              <td>${doc.chunk_count}</td>
              <td>${doc.entity_count}</td>
              <td>${statusBadge}</td>
              <td>${actionsHtml}</td>
            </tr>
          `;
        }).join('');
      } else {
        const tbody = document.getElementById('dashRecentDocsTable');
        if (tbody) tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--danger);">Failed to load recent activity.</td></tr>';
      }
    } catch (e) {
      console.error(e);
      const tbody = document.getElementById('dashRecentDocsTable');
      if (tbody) tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--danger);">Error loading recent documents: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  const dashReloadTableBtn = document.getElementById('dashReloadTableBtn');
  if (dashReloadTableBtn) {
    dashReloadTableBtn.addEventListener('click', async () => {
      if (dashReloadTableBtn.disabled) return;
      dashReloadTableBtn.disabled = true;
      const originalHtml = dashReloadTableBtn.innerHTML;
      dashReloadTableBtn.innerHTML = '<span class="is-spinning">⟳</span> Refreshing...';
      try {
        await loadDashboardMetrics();
      } catch (e) {
        console.error('Failed to reload dashboard table:', e);
      } finally {
        dashReloadTableBtn.disabled = false;
        dashReloadTableBtn.innerHTML = originalHtml;
      }
    });
  }

  // ============================================================================
  // 7. GROUNDED AI ASSISTANT & RAG
  // ============================================================================

  const askInput = document.getElementById('askInput');
  const askSubmitBtn = document.getElementById('askSubmitBtn');
  const assistantGraphRagToggle = document.getElementById('assistantGraphRagToggle');
  const assistantResponseCard = document.getElementById('assistantResponseCard');
  const chatQuestionText = document.getElementById('chatQuestionText');
  const chatAnswerText = document.getElementById('chatAnswerText');
  const chatCitationsList = document.getElementById('chatCitationsList');
  const chatGraphSection = document.getElementById('chatGraphSection');
  const chatGraphList = document.getElementById('chatGraphList');
  const chatModeBadge = document.getElementById('chatModeBadge');
  const copyAnswerBtn = document.getElementById('copyAnswerBtn');

  // Suggested pills
  const sugPills = document.querySelectorAll('.sug-pill');
  sugPills.forEach(pill => {
    pill.addEventListener('click', () => {
      askInput.value = pill.getAttribute('data-query');
      executeAsk();
    });
  });

  if (askSubmitBtn) {
    askSubmitBtn.addEventListener('click', executeAsk);
    askInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') executeAsk(); });
  }

  async function executeAsk() {
    const question = askInput.value.trim();
    if (!question) return;

    assistantResponseCard.style.display = 'block';
    chatQuestionText.textContent = question;
    chatAnswerText.textContent = "Querying vector index, exploring GraphRAG relations, and synthesizing grounded answer...";
    chatCitationsList.innerHTML = "";
    chatGraphSection.style.display = "none";
    chatModeBadge.textContent = "Processing...";

    try {
      const res = await fetch('/api/v1/navigator/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
        },
        body: JSON.stringify({
          question: question,
          enable_graphrag: assistantGraphRagToggle.checked,
          top_k: 4
        })
      });
      const data = await res.json();
      if (res.ok) {
        const engineLabel = data.synthesis_engine === 'groq_llm_verified'
          ? 'Cloud LLM (Groq Llama-3.3-70B)'
          : (data.synthesis_engine === 'graphrag_extractive_verified' ? 'Graph Relational Extractive' : 'Local Deterministic Extractive');
        if (data.verification_status === 'verified') {
          chatModeBadge.innerHTML = `<span style="color: #047857; font-weight: 600;">✓ Verified (${Math.round((data.claim_support_rate || 1.0) * 100)}% Grounded)</span> • ${escapeHtml(data.retrieval_mode)} <span style="font-size: 0.72rem; color: var(--text-muted); padding: 1px 6px; border: 1px solid var(--border-color); border-radius: 4px; margin-left: 4px;">${engineLabel}</span>`;
        } else if (data.verification_status === 'abstained') {
          chatModeBadge.innerHTML = `<span style="color: #b45309; font-weight: 600;">⚠ Abstained (Missing Evidence)</span> <span style="font-size: 0.72rem; color: var(--text-muted); padding: 1px 6px; border: 1px solid var(--border-color); border-radius: 4px; margin-left: 4px;">${engineLabel}</span>`;
        } else if (data.verification_status === 'refused') {
          chatModeBadge.innerHTML = `<span style="color: #b91c1c; font-weight: 600;">🛡 Security Refusal</span>`;
        } else {
          chatModeBadge.textContent = data.retrieval_mode;
        }

        chatAnswerText.textContent = data.answer;

        if (data.sources && data.sources.length > 0) {
          chatCitationsList.innerHTML = data.sources.map(s => `
            <span class="citation-pill" onclick="window.openCitationPreview('${escapeHtml(s.filename)}', ${s.page_number})" title="Click to view extracted Page ${s.page_number} text. Verified database chunk.">
              📄 ${escapeHtml(s.filename)} (Page ${s.page_number}) ${s.verified ? '<span style="color: #047857; font-weight: 600;">✓ Verified</span>' : ''} ↗
            </span>
          `).join('');
        } else {
          chatCitationsList.innerHTML = '<span style="font-size: 0.8rem; color: var(--text-muted);">No direct document citations</span>';
        }

        if (data.graph_evidence && data.graph_evidence.length > 0) {
          chatGraphSection.style.display = "block";
          chatGraphList.innerHTML = data.graph_evidence.map(g => `
            <li><strong>${escapeHtml(g.source)}</strong> ➔ [<em>${escapeHtml(g.relation)}</em>] ➔ <strong>${escapeHtml(g.target)}</strong> <span style="color: var(--text-muted); font-size: 0.78rem;">(${escapeHtml(g.provenance)})</span></li>
          `).join('');
        }

        currentAssistantPayload = {
          question: question,
          answer: data.answer,
          mode: data.retrieval_mode || 'rag',
          confidence_score: data.confidence_score || 0.95,
          citations: data.sources || [],
          entities: (data.graph_evidence || []).map(g => ({ name: g.source, category: 'RELATION' })),
          user_notes: ''
        };
        const saveAnswerBtn = document.getElementById('saveAnswerBtn');
        if (saveAnswerBtn) {
          saveAnswerBtn.textContent = '⭐ Save';
          saveAnswerBtn.disabled = false;
        }
      } else {
        chatAnswerText.textContent = `Error: ${data.detail || 'Assistant query failed'}`;
      }
    } catch (e) {
      chatAnswerText.textContent = `Connection error: ${e.message}`;
    }
  }

  let currentAssistantPayload = null;
  const saveAnswerBtn = document.getElementById('saveAnswerBtn');
  if (saveAnswerBtn) {
    saveAnswerBtn.addEventListener('click', async () => {
      if (!currentAssistantPayload) return;
      saveAnswerBtn.disabled = true;
      saveAnswerBtn.textContent = 'Saving...';
      try {
        const res = await fetch('/api/v1/workspace/saved-answers', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
          },
          body: JSON.stringify(currentAssistantPayload)
        });
        if (res.ok) {
          saveAnswerBtn.textContent = '✓ Saved!';
          setTimeout(() => { saveAnswerBtn.textContent = '⭐ Saved'; }, 2000);
          fetchUnreadNotificationsCount();
        } else {
          saveAnswerBtn.textContent = 'Failed';
          saveAnswerBtn.disabled = false;
        }
      } catch (err) {
        saveAnswerBtn.textContent = 'Error';
        saveAnswerBtn.disabled = false;
      }
    });
  }

  if (copyAnswerBtn) {
    copyAnswerBtn.addEventListener('click', () => {
      const text = chatAnswerText.textContent;
      if (navigator.clipboard && text) {
        navigator.clipboard.writeText(text);
        copyAnswerBtn.textContent = '✓ Copied';
        setTimeout(() => copyAnswerBtn.textContent = '📋 Copy', 2000);
      }
    });
  }

  // ============================================================================
  // 8. DOCUMENT LIBRARY
  // ============================================================================

  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('fileUploadInput');
  const uploadFeedback = document.getElementById('uploadFeedback');
  const reloadDocsBtn = document.getElementById('reloadDocsBtn');
  const docFilterInput = document.getElementById('docFilterInput');
  const docStatusFilter = document.getElementById('docStatusFilter');
  const docFormatFilter = document.getElementById('docFormatFilter');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.style.borderColor = 'var(--primary)'; });
    dropzone.addEventListener('dragleave', () => { dropzone.style.borderColor = 'var(--border-color)'; });
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--border-color)';
      if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) handleFileUpload(fileInput.files[0]);
    });
  }

  async function handleFileUpload(file) {
    if (!file) return;
    const allowed = ['.pdf', '.docx', '.txt'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      uploadFeedback.style.display = 'block';
      uploadFeedback.className = 'alert-box alert-error';
      uploadFeedback.innerHTML = `Unsupported format "${escapeHtml(ext)}". Supported formats: PDF, DOCX, TXT.`;
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      uploadFeedback.style.display = 'block';
      uploadFeedback.className = 'alert-box alert-error';
      uploadFeedback.innerHTML = `File size (${(file.size / (1024*1024)).toFixed(1)} MB) exceeds 25 MB enterprise limit.`;
      return;
    }

    const tracker = document.getElementById('uploadPipelineTracker');
    const nameLabel = document.getElementById('uploadFileNameLabel');
    const stageBadge = document.getElementById('uploadStageBadge');
    const stageDetail = document.getElementById('uploadStageDetail');

    function setStage(stageNum, badgeText, detailText) {
      if (!tracker) return;
      tracker.style.display = 'block';
      if (nameLabel) nameLabel.textContent = `Ingesting: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      if (stageBadge) stageBadge.textContent = badgeText;
      if (stageDetail) stageDetail.textContent = detailText;
      for (let i = 1; i <= 5; i++) {
        const step = document.getElementById(`pipeStep${i}`);
        if (step) {
          if (i <= stageNum) step.classList.add('active');
          else step.classList.remove('active');
        }
      }
    }

    uploadFeedback.style.display = 'none';
    setStage(1, 'Stage 1/5: Validating', 'Validating file format header, mime type, and security policies...');

    const t2 = setTimeout(() => {
      setStage(2, 'Stage 2/5: Extracting', 'Parsing text stream, headings, and document structure...');
    }, 400);

    const t3 = setTimeout(() => {
      setStage(3, 'Stage 3/5: Chunking', 'Tokenizing content into overlapping semantic passages (500 tokens / 50 overlap)...');
    }, 900);

    const t4 = setTimeout(() => {
      setStage(4, 'Stage 4/5: Indexing', 'Computing TF-IDF vector weights, BM25 indices, and extracting knowledge graph entities...');
    }, 1500);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/v1/navigator/documents/upload', {
        method: 'POST',
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) },
        body: formData
      });
      clearTimeout(t2); clearTimeout(t3); clearTimeout(t4);
      const data = await res.json();
      if (res.ok) {
        setStage(5, 'Completed', 'Document fully indexed and ready for hybrid search & assistant Q&A.');
        setTimeout(() => { if (tracker) tracker.style.display = 'none'; }, 4000);

        uploadFeedback.style.display = 'block';
        uploadFeedback.className = 'alert-box alert-success';
        uploadFeedback.innerHTML = `✓ Document '<strong>${escapeHtml(data.filename)}</strong>' successfully indexed! (${data.chunk_count} chunks, ${data.entity_count} entities extracted)`;
        loadDocumentsList();
        loadDashboardMetrics();
      } else {
        if (tracker) tracker.style.display = 'none';
        uploadFeedback.style.display = 'block';
        uploadFeedback.className = 'alert-box alert-error';
        uploadFeedback.innerHTML = `✗ Ingestion Error: ${escapeHtml(data.detail || 'Upload failed')}`;
        loadDocumentsList();
        loadDashboardMetrics();
      }
    } catch (err) {
      clearTimeout(t2); clearTimeout(t3); clearTimeout(t4);
      if (tracker) tracker.style.display = 'none';
      uploadFeedback.style.display = 'block';
      uploadFeedback.className = 'alert-box alert-error';
      uploadFeedback.innerHTML = `✗ Upload connection error: ${escapeHtml(err.message)}`;
    }
  }

  window.cachedDocuments = [];

  async function loadDocumentsList() {
    const tbody = document.getElementById('documentsTableBody');
    try {
      const res = await fetch('/api/v1/navigator/documents');
      if (res.ok) {
        const data = await res.json();
        let docs = data.documents || [];
        window.cachedDocuments = docs;

        // Populate search document scope dropdown
        const scopeSelect = document.getElementById('searchDocScopeSelect');
        if (scopeSelect) {
          const currentVal = scopeSelect.value;
          const indexedDocs = docs.filter(d => d.status === 'indexed');
          scopeSelect.innerHTML = '<option value="">All Documents (Entire Repo)</option>' +
            indexedDocs.map(d => `<option value="${d.id}" ${d.id === currentVal ? 'selected' : ''}>${escapeHtml(d.filename)}</option>`).join('');
        }

        // Apply text filter
        if (docFilterInput && docFilterInput.value.trim()) {
          const term = docFilterInput.value.trim().toLowerCase();
          docs = docs.filter(d => d.filename.toLowerCase().includes(term));
        }

        // Apply status filter
        if (docStatusFilter && docStatusFilter.value !== 'all') {
          if (docStatusFilter.value === 'indexed') {
            docs = docs.filter(d => d.status === 'indexed');
          } else if (docStatusFilter.value === 'error') {
            docs = docs.filter(d => d.status === 'error' || d.status === 'failed');
          }
        }

        // Apply format filter
        if (docFormatFilter && docFormatFilter.value !== 'all') {
          const fmt = docFormatFilter.value.toUpperCase();
          docs = docs.filter(d => (d.file_type || '').toUpperCase() === fmt);
        }

        if (docs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No documents matching selected filters.</td></tr>';
          return;
        }

        tbody.innerHTML = docs.map(doc => {
          const isErr = doc.status === 'error' || doc.status === 'failed';
          const statusBadge = isErr
            ? `<span class="badge-tag tag-danger">${escapeHtml(doc.status)}</span>`
            : `<span class="badge-tag tag-success">${escapeHtml(doc.status)}</span>`;

          const actionsHtml = isErr
            ? `<div style="display: flex; gap: 0.35rem; align-items: center;">
                 <button class="btn btn-warning btn-sm" onclick="window.explainDocIssue('${doc.id}')" title="Diagnose Extraction Failure">Explain Issue</button>
                 <button class="btn btn-secondary btn-sm" onclick="window.reprocessDoc('${doc.id}')" title="Retry Extraction & Indexing">Retry</button>
                 <button class="btn btn-outline btn-sm" onclick="window.downloadDoc('${doc.id}', '${escapeHtml(doc.filename)}')" title="Download Original File">Download</button>
                 <button class="btn btn-danger btn-sm" onclick="window.deleteDoc('${doc.id}')" title="Delete Document">Delete</button>
               </div>`
            : `<div style="display: flex; gap: 0.35rem; align-items: center;">
                 <button class="btn btn-secondary btn-sm" onclick="window.previewDoc('${doc.id}', 1)" title="Preview Document Pages">Preview</button>
                 <button class="btn btn-primary btn-sm" onclick="window.searchInDocument('${doc.id}', '${escapeHtml(doc.filename)}')" title="Search within this document">🔍 Search</button>
                 <button class="btn btn-outline btn-sm" onclick="window.downloadDoc('${doc.id}', '${escapeHtml(doc.filename)}')" title="Download Original File">Download</button>
                 <button class="btn btn-danger btn-sm" onclick="window.deleteDoc('${doc.id}')" title="Delete Document">Delete</button>
               </div>`;

          return `
            <tr>
              <td><strong>${escapeHtml(doc.filename)}</strong></td>
              <td><span class="badge-tag tag-primary">${escapeHtml(doc.file_type)}</span></td>
              <td>${(doc.file_size_bytes / 1024).toFixed(1)} KB</td>
              <td>${doc.page_count}</td>
              <td>${doc.chunk_count}</td>
              <td>${doc.entity_count}</td>
              <td>${statusBadge}</td>
              <td>${actionsHtml}</td>
            </tr>
          `;
        }).join('');
      } else {
        if (tbody) tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--danger);">Failed to load documents list from server.</td></tr>';
      }
    } catch (e) {
      console.error(e);
      if (tbody) tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--danger);">Error loading documents: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  window.searchInDocument = function(docId, filename) {
    switchView('search');
    const scopeSelect = document.getElementById('searchDocScopeSelect');
    if (scopeSelect) scopeSelect.value = docId;
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.value = '';
      searchInput.placeholder = `Search within "${filename}"...`;
      searchInput.focus();
    }
  };

  // Document Preview Modal State
  let activePreviewDoc = null;
  let activePreviewPage = 1;

  window.previewDoc = async function(docId, targetPage = 1) {
    const modal = document.getElementById('documentPreviewModal');
    const titleEl = document.getElementById('docPreviewTitle');
    const metaEl = document.getElementById('docPreviewMeta');
    const contentEl = document.getElementById('docPreviewContent');
    const curPageEl = document.getElementById('currentPageNum');
    const totPageEl = document.getElementById('totalPagesNum');

    if (!modal) return;
    modal.style.display = 'flex';
    contentEl.textContent = 'Loading extracted text blocks...';

    try {
      const res = await fetch(`/api/v1/navigator/documents/${docId}/preview`, {
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
      });
      if (!res.ok) {
        contentEl.textContent = 'Failed to load document preview.';
        return;
      }
      const data = await res.json();
      activePreviewDoc = data;
      activePreviewPage = Math.max(1, Math.min(targetPage, data.page_count || 1));

      titleEl.textContent = data.filename;
      metaEl.textContent = `${data.file_type.toUpperCase()} • ${(data.file_size_bytes / 1024).toFixed(1)} KB • ${data.chunk_count} Chunks • SHA-256: ${data.sha256.substring(0, 16)}...`;
      totPageEl.textContent = data.page_count;

      renderActivePreviewPage();
    } catch (err) {
      contentEl.textContent = 'Preview error: ' + err.message;
    }
  };

  function renderActivePreviewPage() {
    if (!activePreviewDoc) return;
    const contentEl = document.getElementById('docPreviewContent');
    const curPageEl = document.getElementById('currentPageNum');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    curPageEl.textContent = activePreviewPage;
    if (prevBtn) prevBtn.disabled = activePreviewPage <= 1;
    if (nextBtn) nextBtn.disabled = activePreviewPage >= activePreviewDoc.page_count;

    const pageObj = (activePreviewDoc.pages || []).find(p => p.page_number === activePreviewPage);
    if (pageObj && pageObj.text.trim()) {
      contentEl.textContent = pageObj.text;
    } else {
      contentEl.textContent = `[Page ${activePreviewPage} has no extractable text or content]`;
    }
  }

  const prevPageBtn = document.getElementById('prevPageBtn');
  const nextPageBtn = document.getElementById('nextPageBtn');
  if (prevPageBtn) {
    prevPageBtn.addEventListener('click', () => {
      if (activePreviewDoc && activePreviewPage > 1) {
        activePreviewPage--;
        renderActivePreviewPage();
      }
    });
  }
  if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => {
      if (activePreviewDoc && activePreviewPage < activePreviewDoc.page_count) {
        activePreviewPage++;
        renderActivePreviewPage();
      }
    });
  }

  const closeDocPreviewBtn = document.getElementById('closeDocPreviewBtn');
  const closeDocPreviewFooterBtn = document.getElementById('closeDocPreviewFooterBtn');
  const downloadDocModalBtn = document.getElementById('downloadDocModalBtn');

  if (closeDocPreviewBtn) closeDocPreviewBtn.addEventListener('click', () => {
    document.getElementById('documentPreviewModal').style.display = 'none';
  });
  if (closeDocPreviewFooterBtn) closeDocPreviewFooterBtn.addEventListener('click', () => {
    document.getElementById('documentPreviewModal').style.display = 'none';
  });
  if (downloadDocModalBtn) {
    downloadDocModalBtn.addEventListener('click', () => {
      if (activePreviewDoc) {
        window.downloadDoc(activePreviewDoc.document_id, activePreviewDoc.filename);
      }
    });
  }

  window.downloadDoc = function(docId, filename) {
    const downloadUrl = `/api/v1/navigator/documents/${docId}/download`;
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename || 'document';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  window.openCitationPreview = async function(filename, pageNumber) {
    let docs = window.cachedDocuments || [];
    if (docs.length === 0) {
      try {
        const res = await fetch('/api/v1/navigator/documents');
        if (res.ok) {
          const data = await res.json();
          docs = data.documents || [];
          window.cachedDocuments = docs;
        }
      } catch (e) {}
    }
    const found = docs.find(d => d.filename.toLowerCase() === filename.toLowerCase());
    if (found) {
      window.previewDoc(found.id, pageNumber);
    } else {
      alert(`Document '${filename}' (Page ${pageNumber}) was verified from index citation.`);
    }
  };

  window.deleteDoc = async function(docId) {
    if (!confirm('Are you sure you want to delete this document and remove all associated chunks and graph references?')) return;
    try {
      const res = await fetch(`/api/v1/navigator/documents/${docId}`, {
        method: 'DELETE',
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
      });
      if (res.ok) {
        loadDocumentsList();
        loadDashboardMetrics();
      } else {
        alert('Failed to delete document');
      }
    } catch (e) {
      alert(e.message);
    }
  };

  let activeErrorDocId = null;

  window.explainDocIssue = function(docId) {
    const doc = (window.cachedDocuments || []).find(d => d.id === docId);
    activeErrorDocId = docId;
    const modal = document.getElementById('documentErrorModal');
    if (!modal) return;

    const fnEl = document.getElementById('docErrorFileName');
    const sumEl = document.getElementById('docErrorSummaryText');
    const techEl = document.getElementById('docErrorTechnicalDetail');
    const resList = document.getElementById('docErrorResolutionList');
    const fb = document.getElementById('reprocessFeedback');
    if (fb) fb.style.display = 'none';

    const fn = doc ? doc.filename : 'Document';
    if (fnEl) fnEl.textContent = `${fn} (${doc ? (doc.file_size_bytes/1024).toFixed(1) : 0} KB)`;

    const errMsg = (doc && doc.error_message) ? doc.error_message : '';

    if (fn.toLowerCase().includes('zero_text') || fn.toLowerCase().includes('blank') || errMsg.toLowerCase().includes('no extractable text') || errMsg.toLowerCase().includes('scanned') || errMsg.toLowerCase().includes('empty')) {
      if (sumEl) sumEl.textContent = 'Extraction Limitation: Scanned Image or Zero Digital Text Layer';
      if (techEl) techEl.textContent = `The file was stored securely, but text extraction engines (PyPDF2) retrieved 0 characters. This occurs when a PDF contains pure rasterized images without an underlying OCR text layer. Diagnostic message: "${errMsg || 'PDF document contains no extractable text. Scanned image-only PDFs require OCR processing.'}"`;
      if (resList) resList.innerHTML = `
        <li><strong>OCR Pre-Processing:</strong> Run Optical Character Recognition (OCR) using tools such as Tesseract OCR or Adobe Acrobat to create an embedded text layer before uploading.</li>
        <li><strong>Native Text Export:</strong> Re-export the source document directly as a digital PDF from Microsoft Word, Google Docs, or LaTeX.</li>
        <li><strong>Action:</strong> If you updated the underlying file, click "Reprocess Document" below; otherwise delete this entry to keep the repository clean.</li>
      `;
    } else if (errMsg.toLowerCase().includes('xref') || errMsg.toLowerCase().includes('eof') || errMsg.toLowerCase().includes('corrupt') || errMsg.toLowerCase().includes('syntaxerror')) {
      if (sumEl) sumEl.textContent = 'File Structure Defect: Damaged or Truncated PDF Cross-Reference Table';
      if (techEl) techEl.textContent = `The PDF parser detected an invalid file trailer or truncated cross-reference table. Diagnostic message: "${errMsg}"`;
      if (resList) resList.innerHTML = `
        <li>Re-save the file in standard PDF reader (e.g. Chrome, Acrobat, Preview) to regenerate valid trailer and xref tables.</li>
        <li>Re-upload the repaired document via the upload dropzone.</li>
      `;
    } else {
      if (sumEl) sumEl.textContent = `Processing Status: ${errMsg ? 'Extraction Exception' : 'Pending Processing'}`;
      if (techEl) techEl.textContent = errMsg ? `Diagnostic message from ingestion engine: "${errMsg}"` : 'This document is pending processing or encountered an unhandled exception.';
      if (resList) resList.innerHTML = `
        <li>Click "Reprocess Document" below to run a fresh extraction, chunking, and indexing pipeline pass.</li>
        <li>Ensure the document is a supported format (PDF, DOCX, TXT) up to 25 MB.</li>
      `;
    }

    modal.style.display = 'flex';
  };

  const closeDocErrorModalBtn = document.getElementById('closeDocErrorModalBtn');
  const closeDocErrorModalFooterBtn = document.getElementById('closeDocErrorModalFooterBtn');
  if (closeDocErrorModalBtn) closeDocErrorModalBtn.onclick = () => { document.getElementById('documentErrorModal').style.display = 'none'; };
  if (closeDocErrorModalFooterBtn) closeDocErrorModalFooterBtn.onclick = () => { document.getElementById('documentErrorModal').style.display = 'none'; };

  const docErrorDeleteBtn = document.getElementById('docErrorDeleteBtn');
  if (docErrorDeleteBtn) {
    docErrorDeleteBtn.onclick = async () => {
      if (!activeErrorDocId) return;
      if (confirm('Permanently remove this document from the enterprise repository?')) {
        document.getElementById('documentErrorModal').style.display = 'none';
        await window.deleteDoc(activeErrorDocId);
      }
    };
  }

  const docErrorDownloadBtn = document.getElementById('docErrorDownloadBtn');
  if (docErrorDownloadBtn) {
    docErrorDownloadBtn.onclick = () => {
      if (!activeErrorDocId) return;
      const doc = (window.cachedDocuments || []).find(d => d.id === activeErrorDocId);
      window.downloadDoc(activeErrorDocId, doc ? doc.filename : 'document.pdf');
    };
  }

  const docErrorRetryBtn = document.getElementById('docErrorRetryBtn');
  if (docErrorRetryBtn) {
    docErrorRetryBtn.onclick = () => {
      if (activeErrorDocId) window.reprocessDoc(activeErrorDocId, true);
    };
  }

  window.reprocessDoc = async function(docId, fromModal = false) {
    const fb = document.getElementById('reprocessFeedback');
    if (fb && fromModal) {
      fb.style.display = 'block';
      fb.className = 'alert-box';
      fb.innerHTML = '⚡ Reprocessing document (extracting, chunking, indexing)...';
    }
    try {
      const res = await fetch(`/api/v1/navigator/documents/${docId}/reprocess`, {
        method: 'POST',
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
      });
      const data = await res.json();
      if (res.ok) {
        if (fb && fromModal) {
          fb.className = 'alert-box alert-success';
          fb.innerHTML = `✓ Reprocessed successfully: ${data.chunk_count} chunks, ${data.entity_count} entities extracted.`;
        } else {
          alert(`Document reprocessed: ${data.chunk_count} chunks indexed.`);
        }
        loadDocumentsList();
        loadDashboardMetrics();
      } else {
        if (fb && fromModal) {
          fb.className = 'alert-box alert-error';
          fb.innerHTML = `✗ Reprocessing failed: ${escapeHtml(data.detail || 'Could not extract text')}`;
        } else {
          alert(`Reprocess failed: ${data.detail || 'Could not extract text'}`);
        }
        loadDocumentsList();
        loadDashboardMetrics();
      }
    } catch (err) {
      if (fb && fromModal) {
        fb.className = 'alert-box alert-error';
        fb.innerHTML = `✗ Reprocessing error: ${escapeHtml(err.message)}`;
      } else {
        alert(`Reprocess connection error: ${err.message}`);
      }
    }
  };

  if (reloadDocsBtn) {
    reloadDocsBtn.addEventListener('click', async () => {
      if (reloadDocsBtn.disabled) return;
      reloadDocsBtn.disabled = true;
      const originalHtml = reloadDocsBtn.innerHTML;
      reloadDocsBtn.innerHTML = '<span class="is-spinning">⟳</span> Reloading...';
      try {
        await loadDocumentsList();
      } catch (e) {
        console.error('Failed to reload documents list:', e);
      } finally {
        reloadDocsBtn.disabled = false;
        reloadDocsBtn.innerHTML = originalHtml;
      }
    });
  }
  if (docFilterInput) docFilterInput.addEventListener('input', loadDocumentsList);
  if (docStatusFilter) docStatusFilter.addEventListener('change', loadDocumentsList);
  if (docFormatFilter) docFormatFilter.addEventListener('change', loadDocumentsList);

  // ============================================================================
  // 9. HYBRID SEARCH
  // ============================================================================

  const searchInput = document.getElementById('searchInput');
  const searchModeSelect = document.getElementById('searchModeSelect');
  const searchDocScopeSelect = document.getElementById('searchDocScopeSelect');
  const searchTopKSelect = document.getElementById('searchTopKSelect');
  const executeSearchBtn = document.getElementById('executeSearchBtn');
  const clearSearchBtn = document.getElementById('clearSearchBtn');
  const exportSearchResultsBtn = document.getElementById('exportSearchResultsBtn');
  const searchResultsCard = document.getElementById('searchResultsCard');
  const searchResultsList = document.getElementById('searchResultsList');
  const searchCountSubtitle = document.getElementById('searchCountSubtitle');

  window.lastSearchResults = [];

  if (executeSearchBtn) {
    executeSearchBtn.addEventListener('click', executeSearch);
    if (searchInput) searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') executeSearch(); });
  }

  if (clearSearchBtn) {
    clearSearchBtn.addEventListener('click', () => {
      if (searchInput) {
        searchInput.value = '';
        searchInput.placeholder = 'Enter keywords or natural-language search query...';
      }
      if (searchDocScopeSelect) searchDocScopeSelect.value = '';
      if (searchResultsCard) searchResultsCard.style.display = 'none';
      if (searchResultsList) searchResultsList.innerHTML = '';
      window.lastSearchResults = [];
    });
  }

  if (exportSearchResultsBtn) {
    exportSearchResultsBtn.addEventListener('click', () => {
      if (!window.lastSearchResults || window.lastSearchResults.length === 0) {
        alert('No search results to export.');
        return;
      }
      const blob = new Blob([JSON.stringify({
        query: searchInput ? searchInput.value : '',
        timestamp: new Date().toISOString(),
        total_found: window.lastSearchResults.length,
        results: window.lastSearchResults
      }, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `search_results_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  async function executeSearch() {
    const q = searchInput.value.trim();
    if (!q) return;

    const docScope = searchDocScopeSelect ? searchDocScopeSelect.value : null;
    const topK = searchTopKSelect ? parseInt(searchTopKSelect.value) || 5 : 5;

    searchCountSubtitle.textContent = "Searching...";
    searchResultsCard.style.display = 'block';
    searchResultsList.innerHTML = '<p style="color: var(--text-muted); padding: 1rem 0;">🔍 Querying enterprise vector space & keyword indexes...</p>';
    if (executeSearchBtn) executeSearchBtn.disabled = true;

    try {
      const res = await fetch('/api/v1/navigator/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          mode: searchModeSelect.value,
          top_k: topK,
          document_id: docScope || undefined
        })
      });
      const data = await res.json();
      if (res.ok) {
        window.lastSearchResults = data.results || [];
        const scopeLabel = docScope ? ' (Scoped to Document)' : '';
        searchCountSubtitle.textContent = `${data.total_found} relevant passages retrieved via ${data.mode.toUpperCase()}${scopeLabel}`;

        if (!data.results || data.results.length === 0) {
          searchResultsList.innerHTML = `
            <div style="background: var(--bg-lavender); border: 1px dashed var(--border-color); border-radius: 8px; padding: 2rem; text-align: center;">
              <p style="color: var(--text-muted); margin-bottom: 0.75rem;">No matching passages found for "${escapeHtml(q)}".</p>
              <div style="display: flex; justify-content: center; gap: 0.5rem;">
                <button class="btn btn-secondary btn-sm" onclick="document.getElementById('searchModeSelect').value='keyword'; executeSearch();">Try Exact Keyword Search</button>
                <button class="btn btn-primary btn-sm" onclick="switchView('assistant'); document.getElementById('askInput').value='${escapeHtml(q)}'; executeAsk();">Ask AI Assistant</button>
              </div>
            </div>
          `;
          return;
        }

        searchResultsList.innerHTML = data.results.map((item, idx) => `
          <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; padding: 1.15rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
              <div>
                <span style="font-weight: 700; color: var(--primary);">#${idx + 1} ${escapeHtml(item.filename)}</span>
                <span style="color: var(--text-muted); font-size: 0.82rem; margin-left: 0.5rem;">Page ${item.page_number} (Chunk ${item.chunk_index})</span>
              </div>
              <span class="badge-tag tag-primary">Score: ${item.score} (${item.retrieval_mode})</span>
            </div>
            <p style="font-size: 0.9rem; line-height: 1.6; color: var(--text-main); margin-bottom: 0.85rem;">${escapeHtml(item.content)}</p>
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 0.65rem;">
              <button class="btn btn-secondary btn-sm preview-search-doc-btn" onclick="window.previewDoc('${item.document_id}', ${item.page_number})">📄 View Source Page</button>
              <button class="btn btn-outline btn-sm ask-about-chunk-btn" onclick="window.askAboutChunk('${escapeHtml(item.filename)}', '${encodeURIComponent(item.content)}')">💬 Ask AI About This</button>
              <button class="btn btn-outline btn-sm copy-chunk-btn" onclick="navigator.clipboard.writeText('${escapeHtml(item.content)}'); this.textContent='✓ Copied'; setTimeout(() => this.textContent='📋 Copy', 1500);">📋 Copy</button>
              <button class="btn btn-outline btn-sm bookmark-chunk-btn" onclick="window.bookmarkSearchPassage('${escapeHtml(item.filename)}', ${item.page_number}, '${encodeURIComponent(item.content)}')">⭐ Bookmark</button>
            </div>
          </div>
        `).join('');
      } else {
        searchResultsList.innerHTML = `<p style="color: var(--danger);">Search Error: ${escapeHtml(data.detail)}</p>`;
      }
    } catch (e) {
      searchResultsList.innerHTML = `<p style="color: var(--danger);">Network Error: ${escapeHtml(e.message)}</p>`;
    } finally {
      if (executeSearchBtn) executeSearchBtn.disabled = false;
    }
  }

  window.askAboutChunk = function(filename, encodedContent) {
    const text = decodeURIComponent(encodedContent);
    const excerpt = text.length > 160 ? text.substring(0, 160) + '...' : text;
    const askInput = document.getElementById('askInput');
    if (askInput) {
      askInput.value = `Regarding ${filename}: "${excerpt}"`;
    }
    switchView('assistant');
    executeAsk();
  };

  window.bookmarkSearchPassage = async function(filename, pageNumber, encodedContent) {
    const content = decodeURIComponent(encodedContent);
    try {
      const res = await fetch('/api/v1/workspace/saved-answers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
        },
        body: JSON.stringify({
          question: `Verified Passage from ${filename} (Page ${pageNumber})`,
          answer: content,
          mode: 'search_passage',
          citations: [{ filename: filename, page_number: pageNumber, chunk_index: 0 }],
          user_notes: `Saved from Hybrid Search results on ${new Date().toLocaleDateString()}`
        })
      });
      if (res.ok) {
        alert('Passage bookmarked to Saved Answers successfully!');
      } else {
        alert('Failed to bookmark passage.');
      }
    } catch (e) {
      alert('Error bookmarking passage: ' + e.message);
    }
  };

  // ============================================================================
  // 10. KNOWLEDGE GRAPH EXPLORATION (D3.JS)
  // ============================================================================

  const reloadGraphBtn = document.getElementById('reloadGraphBtn');
  const graphCategorySelect = document.getElementById('graphCategorySelect');
  const graphSearchInput = document.getElementById('graphSearchInput');
  const graphNodeDetails = document.getElementById('graphNodeDetails');
  const nodeDetailName = document.getElementById('nodeDetailName');
  const nodeDetailCategory = document.getElementById('nodeDetailCategory');
  const nodeDetailMentions = document.getElementById('nodeDetailMentions');
  const closeGraphDetailBtn = document.getElementById('closeGraphDetailBtn');
  const searchGraphEntityBtn = document.getElementById('searchGraphEntityBtn');
  const askGraphEntityBtn = document.getElementById('askGraphEntityBtn');

  if (reloadGraphBtn) {
    reloadGraphBtn.addEventListener('click', async () => {
      if (reloadGraphBtn.disabled) return;
      reloadGraphBtn.disabled = true;
      const originalHtml = reloadGraphBtn.innerHTML;
      reloadGraphBtn.innerHTML = '<span class="is-spinning">⟳</span> Reloading...';
      try {
        await loadKnowledgeGraph();
      } catch (e) {
        console.error('Failed to reload knowledge graph:', e);
      } finally {
        reloadGraphBtn.disabled = false;
        reloadGraphBtn.innerHTML = originalHtml;
      }
    });
  }
  if (graphCategorySelect) graphCategorySelect.addEventListener('change', loadKnowledgeGraph);

  if (closeGraphDetailBtn) {
    closeGraphDetailBtn.addEventListener('click', () => {
      if (graphNodeDetails) graphNodeDetails.style.display = 'none';
    });
  }

  if (searchGraphEntityBtn) {
    searchGraphEntityBtn.addEventListener('click', () => {
      const name = nodeDetailName ? nodeDetailName.textContent.trim() : '';
      if (!name) return;
      const searchInput = document.getElementById('searchInput');
      if (searchInput) searchInput.value = name;
      switchView('search');
      executeSearch();
    });
  }

  if (askGraphEntityBtn) {
    askGraphEntityBtn.addEventListener('click', () => {
      const name = nodeDetailName ? nodeDetailName.textContent.trim() : '';
      if (!name) return;
      const askInput = document.getElementById('askInput');
      if (askInput) askInput.value = `What information and connected relationships are documented for ${name}?`;
      switchView('assistant');
      executeAsk();
    });
  }

  window.currentGraphNodes = [];

  if (graphSearchInput) {
    graphSearchInput.addEventListener('input', () => {
      const q = graphSearchInput.value.trim().toLowerCase();
      if (!q || !window.currentGraphNodes) return;
      const match = window.currentGraphNodes.find(n => n.label.toLowerCase().includes(q));
      if (match && graphNodeDetails) {
        graphNodeDetails.style.display = 'block';
        if (nodeDetailName) nodeDetailName.textContent = match.label;
        if (nodeDetailCategory) nodeDetailCategory.textContent = match.category;
        if (nodeDetailMentions) nodeDetailMentions.textContent = match.mentions || 1;
      }
    });
  }

  async function loadKnowledgeGraph() {
    const cat = graphCategorySelect ? graphCategorySelect.value : '';
    const url = cat ? `/api/v1/navigator/graph?category=${encodeURIComponent(cat)}` : '/api/v1/navigator/graph';

    try {
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        window.currentGraphNodes = data.nodes || [];
        renderD3Graph(data.nodes, data.edges);
      } else {
        const svg = d3.select("#graphSvg");
        svg.selectAll("*").remove();
        svg.append("text")
          .attr("x", "50%")
          .attr("y", "50%")
          .attr("text-anchor", "middle")
          .attr("fill", "#dc2626")
          .text("Failed to load knowledge graph from server.");
      }
    } catch (e) {
      console.error('Failed to load graph data:', e);
      const svg = d3.select("#graphSvg");
      svg.selectAll("*").remove();
      svg.append("text")
        .attr("x", "50%")
        .attr("y", "50%")
        .attr("text-anchor", "middle")
        .attr("fill", "#dc2626")
        .text(`Error loading graph: ${e.message}`);
    }
  }

  function renderD3Graph(nodesData, edgesData) {
    const svg = d3.select("#graphSvg");
    svg.selectAll("*").remove();

    if (!nodesData || nodesData.length === 0) {
      svg.append("text")
        .attr("x", "50%")
        .attr("y", "50%")
        .attr("text-anchor", "middle")
        .attr("fill", "#64748b")
        .text("Knowledge Graph empty. Ingest documents to extract entities and relations.");
      return;
    }

    const container = document.getElementById("d3GraphContainer");
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 520;

    const g = svg.append("g");
    svg.call(d3.zoom().on("zoom", (event) => g.attr("transform", event.transform)));

    const colorMap = {
      PERSON: "#7667D8",
      ORG: "#4F6BED",
      TECH: "#9B8EF2",
      POLICY: "#16835D",
      PRODUCT: "#3B57DB"
    };

    const simulation = d3.forceSimulation(nodesData)
      .force("link", d3.forceLink(edgesData).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-240))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = g.append("g")
      .selectAll("line")
      .data(edgesData)
      .enter().append("line")
      .attr("stroke", "#E6E8F2")
      .attr("stroke-width", 1.5);

    const linkText = g.append("g")
      .selectAll("text")
      .data(edgesData)
      .enter().append("text")
      .attr("font-size", "9px")
      .attr("fill", "#687086")
      .attr("text-anchor", "middle")
      .text(d => d.relation);

    const node = g.append("g")
      .selectAll("circle")
      .data(nodesData)
      .enter().append("circle")
      .attr("r", 0)
      .attr("fill", d => colorMap[d.category] || "#7667D8")
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        if (graphNodeDetails) {
          graphNodeDetails.style.display = 'block';
          nodeDetailName.textContent = d.label;
          nodeDetailCategory.textContent = d.category;
          nodeDetailMentions.textContent = d.mentions || 1;
        }
      })
      .call(d3.drag()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        })
      );

    node.transition()
      .duration(450)
      .attr("r", d => 6 + Math.min(10, (d.mentions || 1) * 2));

    const labels = g.append("g")
      .selectAll("text")
      .data(nodesData)
      .enter().append("text")
      .attr("font-size", "11px")
      .attr("font-weight", "500")
      .attr("dx", 12)
      .attr("dy", 4)
      .attr("fill", "#0f172a")
      .text(d => d.label);

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      linkText
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

      labels
        .attr("x", d => d.x)
        .attr("y", d => d.y);
    });
  }

  // ============================================================================
  // 11. EVALUATION & BENCHMARKS
  // ============================================================================

  const runEvalSuiteBtn = document.getElementById('runEvalSuiteBtn');
  if (runEvalSuiteBtn) {
    runEvalSuiteBtn.addEventListener('click', async () => {
      runEvalSuiteBtn.textContent = 'Running Benchmark...';
      runEvalSuiteBtn.disabled = true;
      try {
        const res = await fetch('/api/v1/navigator/evaluate/run?k=3', { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          document.getElementById('evalPrecisionVal').textContent = `${(data.precision_at_k * 100).toFixed(1)}%`;
          document.getElementById('evalRecallVal').textContent = `${(data.recall_at_k * 100).toFixed(1)}%`;
          document.getElementById('evalMrrVal').textContent = data.mrr_score.toFixed(3);
          document.getElementById('evalLatencyVal').textContent = data.average_latency_ms.toFixed(1);
          document.getElementById('evalGroundednessVal').textContent = `${(data.groundedness_score * 100).toFixed(1)}%`;
          loadEvaluationHistory();
          loadDashboardMetrics();
        }
      } catch (e) {
        alert('Evaluation failed: ' + e.message);
      } finally {
        runEvalSuiteBtn.textContent = 'Run Evaluation Suite';
        runEvalSuiteBtn.disabled = false;
      }
    });
  }

  async function loadEvaluationHistory() {
    try {
      const res = await fetch('/api/v1/navigator/evaluate/history');
      if (res.ok) {
        const data = await res.json();
        const tbody = document.getElementById('evalHistoryTableBody');
        if (!data || data.length === 0) {
          if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No evaluation runs executed yet.</td></tr>';
          return;
        }
        tbody.innerHTML = data.map(r => `
          <tr>
            <td><code>${r.run_id}</code></td>
            <td>${new Date(r.timestamp).toLocaleTimeString()}</td>
            <td>${r.query_count} queries</td>
            <td><strong>${(r.precision_at_k * 100).toFixed(1)}%</strong></td>
            <td>${(r.recall_at_k * 100).toFixed(1)}%</td>
            <td>${r.mrr_score.toFixed(3)}</td>
            <td>${r.average_latency_ms} ms</td>
          </tr>
        `).join('');
      } else {
        const tbody = document.getElementById('evalHistoryTableBody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--danger);">Failed to load evaluation history.</td></tr>';
      }
    } catch (e) {
      console.error(e);
      const tbody = document.getElementById('evalHistoryTableBody');
      if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--danger);">Error loading history: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  const reloadEvalBtn = document.getElementById('reloadEvalBtn');
  if (reloadEvalBtn) {
    reloadEvalBtn.addEventListener('click', async () => {
      if (reloadEvalBtn.disabled) return;
      reloadEvalBtn.disabled = true;
      const originalHtml = reloadEvalBtn.innerHTML;
      reloadEvalBtn.innerHTML = '<span class="is-spinning">⟳</span> Refreshing...';
      try {
        await loadEvaluationHistory();
      } catch (e) {
        console.error('Failed to reload evaluation history:', e);
      } finally {
        reloadEvalBtn.disabled = false;
        reloadEvalBtn.innerHTML = originalHtml;
      }
    });
  }

  // ============================================================================
  // 12. USER MANAGEMENT (ADMIN ONLY)
  // ============================================================================

  const openProvisionUserModalBtn = document.getElementById('openProvisionUserModalBtn');
  const provisionUserModal = document.getElementById('provisionUserModal');
  const closeProvisionModalBtn = document.getElementById('closeProvisionModalBtn');
  const cancelProvisionBtn = document.getElementById('cancelProvisionBtn');
  const provisionUserForm = document.getElementById('provisionUserForm');
  const provFeedback = document.getElementById('provFeedback');

  window.allRoles = [];

  async function fetchAllRoles() {
    if (!authToken || !currentUser || currentUser.role !== 'admin') return [];
    try {
      const res = await fetch('/api/v1/auth/admin/roles', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        window.allRoles = await res.json();
        return window.allRoles;
      }
    } catch (e) {
      console.error('Failed to fetch roles:', e);
    }
    return window.allRoles || [];
  }

  if (openProvisionUserModalBtn) {
    openProvisionUserModalBtn.addEventListener('click', async () => {
      provisionUserModal.style.display = 'flex';
      provFeedback.style.display = 'none';
      provisionUserForm.reset();

      // Populate roles dropdown dynamically with active system and custom roles
      const provRoleSelect = document.getElementById('provRole');
      if (provRoleSelect) {
        await fetchAllRoles();
        if (window.allRoles && window.allRoles.length > 0) {
          provRoleSelect.innerHTML = window.allRoles.map(r => `
            <option value="${escapeHtml(r.id)}">${r.is_builtin ? (r.id === 'admin' ? 'Administrator' : (r.id === 'analyst' ? 'Analyst' : 'Knowledge Worker')) : `🛡️ ${escapeHtml(r.name)}`}</option>
          `).join('');
        }
      }
    });
  }
  if (closeProvisionModalBtn) closeProvisionModalBtn.addEventListener('click', () => provisionUserModal.style.display = 'none');
  if (cancelProvisionBtn) cancelProvisionBtn.addEventListener('click', () => provisionUserModal.style.display = 'none');

  if (provisionUserForm) {
    provisionUserForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      provFeedback.style.display = 'none';

      try {
        const res = await fetch('/api/v1/auth/users/provision', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            full_name: document.getElementById('provFullName').value.trim(),
            email: document.getElementById('provEmail').value.trim(),
            password: document.getElementById('provPassword').value,
            role: document.getElementById('provRole').value,
            organization: document.getElementById('provOrg').value.trim()
          })
        });
        const data = await res.json();
        if (res.ok) {
          provFeedback.className = 'alert-box alert-success';
          provFeedback.textContent = `✓ User ${data.email} provisioned successfully!`;
          provFeedback.style.display = 'block';
          setTimeout(() => {
            provisionUserModal.style.display = 'none';
            loadUsersTable();
            loadCustomRoles();
          }, 800);
        } else {
          provFeedback.className = 'alert-box alert-error';
          provFeedback.textContent = data.detail || 'Provisioning failed.';
          provFeedback.style.display = 'block';
        }
      } catch (err) {
        provFeedback.className = 'alert-box alert-error';
        provFeedback.textContent = err.message;
        provFeedback.style.display = 'block';
      }
    });
  }

  async function loadUsersTable() {
    if (!authToken || !currentUser || currentUser.role !== 'admin') return;
    const tbody = document.getElementById('usersTableBody');
    try {
      await fetchAllRoles();
      const res = await fetch('/api/v1/auth/users', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        const users = await res.json();
        tbody.innerHTML = users.map(u => {
          const roleOptions = (window.allRoles && window.allRoles.length > 0)
            ? window.allRoles.map(r => `<option value="${escapeHtml(r.id)}" ${u.role === r.id ? 'selected' : ''}>${r.is_builtin ? (r.id === 'admin' ? '👑 Admin' : (r.id === 'analyst' ? '🔬 Analyst' : '💼 Worker')) : `🛡️ ${escapeHtml(r.name)}`}</option>`).join('')
            : `<option value="admin" ${u.role === 'admin' ? 'selected' : ''}>👑 Admin</option>
               <option value="knowledge_worker" ${u.role === 'knowledge_worker' ? 'selected' : ''}>💼 Worker</option>
               <option value="analyst" ${u.role === 'analyst' ? 'selected' : ''}>🔬 Analyst</option>`;

          const roleBadgeClass = u.role === 'admin' ? 'tag-danger' : (u.role === 'analyst' ? 'tag-secondary' : (u.role === 'knowledge_worker' ? 'tag-primary' : 'tag-warning'));

          return `
            <tr>
              <td><strong>${escapeHtml(u.full_name)}</strong></td>
              <td>${escapeHtml(u.email)}</td>
              <td><span class="badge-tag ${roleBadgeClass}">${formatRoleName(u.role)}</span></td>
              <td>${escapeHtml(u.organization || '—')}</td>
              <td><span class="badge-tag ${u.is_active ? 'tag-success' : 'tag-warning'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
              <td>${u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
              <td>
                ${u.id === currentUser.id ? '<span style="color: var(--text-muted); font-size: 0.78rem;">Current Account</span>' : `
                  <div style="display: flex; gap: 0.35rem; align-items: center; flex-wrap: wrap;">
                    <select class="select-input" onchange="window.changeUserRole('${u.id}', this.value)" style="font-size: 0.75rem; padding: 0.2rem 0.4rem; min-width: 110px;" title="Change User Role">
                      ${roleOptions}
                    </select>
                    <button class="btn btn-secondary btn-sm" onclick="window.toggleUserActive('${u.id}', ${!u.is_active})" title="${u.is_active ? 'Deactivate Account' : 'Activate Account'}">
                      ${u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="window.adminResetPassword('${u.id}', '${escapeHtml(u.full_name)}')" title="Reset User Password">
                      🔑 Reset
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="window.adminDeleteUser('${u.id}', '${escapeHtml(u.email)}')" title="Delete Account">
                      🗑️
                    </button>
                  </div>
                `}
              </td>
            </tr>
          `;
        }).join('');
      } else {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--danger);">Failed to load user accounts.</td></tr>';
      }
    } catch (e) {
      console.error('Failed to load users table:', e);
      if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--danger);">Error loading users: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  const reloadUsersBtn = document.getElementById('reloadUsersBtn');
  if (reloadUsersBtn) {
    reloadUsersBtn.addEventListener('click', async () => {
      if (reloadUsersBtn.disabled) return;
      reloadUsersBtn.disabled = true;
      const originalHtml = reloadUsersBtn.innerHTML;
      reloadUsersBtn.innerHTML = '<span class="is-spinning">⟳</span> Refreshing...';
      try {
        await loadUsersTable();
      } catch (e) {
        console.error('Failed to reload users table:', e);
      } finally {
        reloadUsersBtn.disabled = false;
        reloadUsersBtn.innerHTML = originalHtml;
      }
    });
  }

  window.toggleUserActive = async function(userId, newStatus) {
    try {
      const res = await fetch(`/api/v1/auth/users/${userId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ is_active: newStatus })
      });
      if (res.ok) {
        loadUsersTable();
        loadCustomRoles();
      } else {
        const data = await res.json();
        alert(data.detail || 'Failed to update user status.');
      }
    } catch (e) {
      alert(e.message);
    }
  };

  window.changeUserRole = async function(userId, newRole) {
    try {
      const res = await fetch(`/api/v1/auth/users/${userId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ role: newRole })
      });
      if (res.ok) {
        loadUsersTable();
        loadCustomRoles();
      } else {
        const data = await res.json();
        alert(data.detail || 'Failed to update user role.');
      }
    } catch (e) {
      alert(e.message);
    }
  };

  window.adminResetPassword = async function(userId, userName) {
    const newPwd = prompt(`Enter new password for ${userName} (minimum 6 characters):`);
    if (!newPwd) return;
    if (newPwd.length < 6) {
      alert('Password must be at least 6 characters.');
      return;
    }
    try {
      const res = await fetch(`/api/v1/auth/users/${userId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ new_password: newPwd })
      });
      if (res.ok) {
        alert(`Password for ${userName} updated successfully.`);
      } else {
        const data = await res.json();
        alert(data.detail || 'Failed to reset password.');
      }
    } catch (e) {
      alert(e.message);
    }
  };

  window.adminDeleteUser = async function(userId, userEmail) {
    if (!confirm(`Are you sure you want to permanently delete account ${userEmail}?`)) return;
    try {
      const res = await fetch(`/api/v1/auth/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      if (res.ok) {
        loadUsersTable();
        loadCustomRoles();
      } else {
        const data = await res.json();
        alert(data.detail || 'Failed to delete user.');
      }
    } catch (e) {
      alert(e.message);
    }
  };

  // ============================================================================
  // 12B. CUSTOM ROLE MANAGEMENT & ROLES/PERMISSIONS MATRIX (ADMIN ONLY)
  // ============================================================================

  async function loadCustomRoles() {
    const tbody = document.getElementById('customRolesTableBody');
    if (!tbody || !authToken || !currentUser || currentUser.role !== 'admin') return;

    try {
      const roles = await fetchAllRoles();
      if (!roles || !roles.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No roles configured.</td></tr>';
        return;
      }

      tbody.innerHTML = roles.map(r => {
        const isBuiltin = r.is_builtin;
        const classBadge = isBuiltin
          ? '<span class="badge-tag tag-primary">Built-in System</span>'
          : '<span class="badge-tag tag-success">Custom Role</span>';

        const capCount = (r.capabilities && r.capabilities.length) || 0;
        const capTooltip = (r.capabilities && r.capabilities.length) ? escapeHtml(r.capabilities.join(', ')) : 'None';
        const userCount = r.assigned_count || 0;
        const userBadge = `<span class="badge-tag ${userCount > 0 ? 'tag-info' : 'tag-secondary'}">${userCount} user${userCount === 1 ? '' : 's'}</span>`;

        const actions = isBuiltin
          ? '<span style="color: var(--text-muted); font-size: 0.78rem;">Protected System Role</span>'
          : `<div style="display: flex; gap: 0.35rem; align-items: center;">
               <button class="btn btn-secondary btn-sm" onclick="window.openEditCustomRoleModal('${r.id}')" title="Edit Role Capabilities">✏️ Edit</button>
               <button class="btn btn-danger btn-sm" onclick="window.deleteCustomRole('${r.id}', '${escapeHtml(r.name)}')" title="Delete Custom Role">🗑️ Delete</button>
             </div>`;

        return `
          <tr>
            <td>
              <strong>${escapeHtml(r.name)}</strong>
              <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">${escapeHtml(r.id)}</div>
            </td>
            <td>${classBadge}</td>
            <td style="max-width: 260px; font-size: 0.85rem;">${escapeHtml(r.description || '—')}</td>
            <td>
              <span title="${capTooltip}" style="cursor: help; text-decoration: underline dotted;">
                ${capCount} capabilities ℹ️
              </span>
            </td>
            <td>${userBadge}</td>
            <td>${actions}</td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.error('Failed to load custom roles table:', e);
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--danger);">Error loading roles: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  async function loadRolesMatrix() {
    const tbody = document.getElementById('rolesMatrixTableBody');
    const headerRow = document.getElementById('rolesMatrixHeaderRow');
    if (!tbody || !authToken) return;

    try {
      await fetchAllRoles();
      const customRoles = (window.allRoles || []).filter(r => !r.is_builtin);

      // Dynamically update header row to include any custom roles
      if (headerRow) {
        headerRow.innerHTML = `
          <th>Capability / Resource</th>
          <th style="text-align: center;">👑 Administrator</th>
          <th style="text-align: center;">💼 Knowledge Worker</th>
          <th style="text-align: center;">🔬 Analyst</th>
          ${customRoles.map(cr => `<th style="text-align: center;">🛡️ ${escapeHtml(cr.name)}</th>`).join('')}
        `;
      }

      const res = await fetch('/api/v1/auth/admin/roles-permissions', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        const matrix = await res.json();
        tbody.innerHTML = matrix.map(m => {
          const customCells = customRoles.map(cr => {
            const hasPerm = Boolean(m[cr.id]);
            return `<td style="text-align: center;">${hasPerm ? '✅ <span style="color: var(--success); font-weight: 600;">Permitted</span>' : '❌ <span style="color: var(--text-muted);">Restricted</span>'}</td>`;
          }).join('');

          return `
            <tr>
              <td>
                <strong>${escapeHtml(m.capability)}</strong>
                <div style="font-size: 0.78rem; color: var(--text-muted);">${escapeHtml(m.description)}</div>
              </td>
              <td style="text-align: center;">${m.admin ? '✅ <span style="color: var(--success); font-weight: 600;">Full Access</span>' : '❌ <span style="color: var(--text-muted);">Restricted</span>'}</td>
              <td style="text-align: center;">${m.knowledge_worker ? '✅ <span style="color: var(--success); font-weight: 600;">Permitted</span>' : '❌ <span style="color: var(--text-muted);">Restricted</span>'}</td>
              <td style="text-align: center;">${m.analyst ? '✅ <span style="color: var(--success); font-weight: 600;">Permitted</span>' : '❌ <span style="color: var(--text-muted);">Restricted</span>'}</td>
              ${customCells}
            </tr>
          `;
        }).join('');
      } else {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--danger);">Failed to load role permissions matrix.</td></tr>';
      }
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--danger);">Error: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  // Custom Role Modal Event Handlers
  const openCreateRoleModalBtn = document.getElementById('openCreateRoleModalBtn');
  const reloadCustomRolesBtn = document.getElementById('reloadCustomRolesBtn');
  const reloadRolesBtn = document.getElementById('reloadRolesBtn');
  const customRoleModal = document.getElementById('customRoleModal');
  const closeCustomRoleModalBtn = document.getElementById('closeCustomRoleModalBtn');
  const cancelCustomRoleBtn = document.getElementById('cancelCustomRoleBtn');
  const customRoleForm = document.getElementById('customRoleForm');
  const roleModalFeedback = document.getElementById('roleModalFeedback');

  if (openCreateRoleModalBtn) {
    openCreateRoleModalBtn.addEventListener('click', () => {
      if (!customRoleModal) return;
      document.getElementById('customRoleModalRoleId').value = '';
      document.getElementById('customRoleModalTitle').textContent = 'Create Custom Enterprise Role';
      document.getElementById('customRoleModalSubtitle').textContent = 'Assign granular capabilities across platform functions.';
      document.getElementById('roleModalName').value = '';
      document.getElementById('roleModalDesc').value = '';

      // Default permissions: ingestion, search, Q&A, profile
      const defaultPerms = ['doc_ingestion', 'search_retrieval', 'qa_citations', 'profile_settings'];
      document.querySelectorAll('input[name="rolePerm"]').forEach(cb => {
        cb.checked = defaultPerms.includes(cb.value);
      });

      if (roleModalFeedback) roleModalFeedback.style.display = 'none';
      customRoleModal.style.display = 'flex';
    });
  }

  if (reloadCustomRolesBtn) {
    reloadCustomRolesBtn.addEventListener('click', async () => {
      if (reloadCustomRolesBtn.disabled) return;
      reloadCustomRolesBtn.disabled = true;
      const originalHtml = reloadCustomRolesBtn.innerHTML;
      reloadCustomRolesBtn.innerHTML = '<span class="is-spinning">⟳</span> Refreshing...';
      try {
        await Promise.all([loadCustomRoles(), loadRolesMatrix()]);
      } catch (e) {
        console.error('Failed to reload custom roles:', e);
      } finally {
        reloadCustomRolesBtn.disabled = false;
        reloadCustomRolesBtn.innerHTML = originalHtml;
      }
    });
  }

  if (reloadRolesBtn) {
    reloadRolesBtn.addEventListener('click', async () => {
      if (reloadRolesBtn.disabled) return;
      reloadRolesBtn.disabled = true;
      const originalHtml = reloadRolesBtn.innerHTML;
      reloadRolesBtn.innerHTML = '<span class="is-spinning">⟳</span> Refreshing...';
      try {
        await Promise.all([loadCustomRoles(), loadRolesMatrix()]);
      } catch (e) {
        console.error('Failed to reload roles matrix:', e);
      } finally {
        reloadRolesBtn.disabled = false;
        reloadRolesBtn.innerHTML = originalHtml;
      }
    });
  }

  if (closeCustomRoleModalBtn) {
    closeCustomRoleModalBtn.addEventListener('click', () => {
      if (customRoleModal) customRoleModal.style.display = 'none';
    });
  }

  if (cancelCustomRoleBtn) {
    cancelCustomRoleBtn.addEventListener('click', () => {
      if (customRoleModal) customRoleModal.style.display = 'none';
    });
  }

  window.openEditCustomRoleModal = function(roleId) {
    const role = (window.allRoles || []).find(r => r.id === roleId);
    if (!role || !customRoleModal) return;
    document.getElementById('customRoleModalRoleId').value = role.id;
    document.getElementById('customRoleModalTitle').textContent = `Edit Custom Role: ${role.name}`;
    document.getElementById('customRoleModalSubtitle').textContent = `Modify description and granular capabilities for role ID: ${role.id}`;
    document.getElementById('roleModalName').value = role.name;
    document.getElementById('roleModalDesc').value = role.description || '';

    const assignedCaps = role.capabilities || [];
    document.querySelectorAll('input[name="rolePerm"]').forEach(cb => {
      cb.checked = assignedCaps.includes(cb.value);
    });

    if (roleModalFeedback) roleModalFeedback.style.display = 'none';
    customRoleModal.style.display = 'flex';
  };

  window.deleteCustomRole = async function(roleId, roleName) {
    if (!confirm(`Are you sure you want to delete the custom role "${roleName}" (${roleId})? This action cannot be undone.`)) return;
    try {
      const res = await fetch(`/api/v1/auth/admin/roles/${roleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      const data = await res.json();
      if (res.ok) {
        await loadCustomRoles();
        await loadRolesMatrix();
      } else {
        alert(data.detail || 'Failed to delete role.');
      }
    } catch (e) {
      alert(e.message);
    }
  };

  if (customRoleForm) {
    customRoleForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const roleId = document.getElementById('customRoleModalRoleId').value.trim();
      const name = document.getElementById('roleModalName').value.trim();
      const description = document.getElementById('roleModalDesc').value.trim();
      const capabilities = Array.from(document.querySelectorAll('input[name="rolePerm"]:checked')).map(cb => cb.value);

      if (!name) {
        if (roleModalFeedback) {
          roleModalFeedback.className = 'alert-box alert-error';
          roleModalFeedback.textContent = 'Role name is required.';
          roleModalFeedback.style.display = 'block';
        }
        return;
      }

      if (capabilities.length === 0) {
        if (roleModalFeedback) {
          roleModalFeedback.className = 'alert-box alert-error';
          roleModalFeedback.textContent = 'Please select at least one permission capability.';
          roleModalFeedback.style.display = 'block';
        }
        return;
      }

      try {
        const isEdit = Boolean(roleId);
        const url = isEdit ? `/api/v1/auth/admin/roles/${roleId}` : '/api/v1/auth/admin/roles';
        const method = isEdit ? 'PUT' : 'POST';

        const res = await fetch(url, {
          method: method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            name: name,
            description: description,
            capabilities: capabilities
          })
        });

        const data = await res.json();
        if (res.ok) {
          if (roleModalFeedback) {
            roleModalFeedback.className = 'alert-box alert-success';
            roleModalFeedback.textContent = `✓ Role "${data.name}" saved successfully!`;
            roleModalFeedback.style.display = 'block';
          }
          await loadCustomRoles();
          await loadRolesMatrix();
          setTimeout(() => {
            if (customRoleModal) customRoleModal.style.display = 'none';
          }, 700);
        } else {
          if (roleModalFeedback) {
            roleModalFeedback.className = 'alert-box alert-error';
            roleModalFeedback.textContent = data.detail || 'Failed to save role.';
            roleModalFeedback.style.display = 'block';
          }
        }
      } catch (err) {
        if (roleModalFeedback) {
          roleModalFeedback.className = 'alert-box alert-error';
          roleModalFeedback.textContent = err.message;
          roleModalFeedback.style.display = 'block';
        }
      }
    });
  }

  let cachedAuditLogs = [];

  async function loadAuditLogs() {
    const tbody = document.getElementById('auditLogsTableBody');
    if (!tbody || !authToken) return;

    try {
      const res = await fetch('/api/v1/auth/admin/audit-logs?limit=50', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        cachedAuditLogs = await res.json();
        renderAuditLogsTable();
      } else {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--danger);">Failed to load operational audit logs.</td></tr>';
      }
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--danger);">Error: ${e.message}</td></tr>`;
    }
  }

  function renderAuditLogsTable() {
    const tbody = document.getElementById('auditLogsTableBody');
    if (!tbody) return;

    const searchInput = document.getElementById('auditSearchInput');
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

    let list = cachedAuditLogs;
    if (query) {
      list = list.filter(l =>
        (l.action && l.action.toLowerCase().includes(query)) ||
        (l.actor_email && l.actor_email.toLowerCase().includes(query)) ||
        (l.resource_type && l.resource_type.toLowerCase().includes(query)) ||
        (l.status && l.status.toLowerCase().includes(query)) ||
        (l.details && l.details.toLowerCase().includes(query))
      );
    }

    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No audit events matching criteria.</td></tr>';
      return;
    }

    tbody.innerHTML = list.map(l => `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 0.78rem;">${escapeHtml(l.created_at || '-')}</td>
        <td><strong>${escapeHtml(l.actor_email || 'System')}</strong></td>
        <td><span class="badge-tag tag-primary">${escapeHtml(l.action)}</span></td>
        <td>${escapeHtml(l.resource_type)} ${l.resource_id ? `<span style="font-size: 0.75rem; color: var(--text-muted);">(${escapeHtml(l.resource_id)})</span>` : ''}</td>
        <td><span class="badge-tag ${l.status === 'SUCCESS' ? 'tag-success' : 'tag-danger'}">${escapeHtml(l.status)}</span></td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(l.ip_address || 'Localhost')} ${l.details ? `— ${escapeHtml(l.details)}` : ''}</td>
      </tr>
    `).join('');
  }

  const reloadAuditBtn = document.getElementById('reloadAuditBtn');
  const auditSearchInput = document.getElementById('auditSearchInput');
  if (reloadAuditBtn) {
    reloadAuditBtn.addEventListener('click', async () => {
      if (reloadAuditBtn.disabled) return;
      reloadAuditBtn.disabled = true;
      const originalHtml = reloadAuditBtn.innerHTML;
      reloadAuditBtn.innerHTML = '<span class="is-spinning">⟳</span> Refreshing...';
      try {
        await loadAuditLogs();
      } catch (e) {
        console.error('Failed to reload audit logs:', e);
      } finally {
        reloadAuditBtn.disabled = false;
        reloadAuditBtn.innerHTML = originalHtml;
      }
    });
  }
  if (auditSearchInput) auditSearchInput.addEventListener('input', renderAuditLogsTable);

  // ============================================================================
  // 13. SYSTEM TELEMETRY & ML LAB (ADMIN ONLY)
  // ============================================================================

  async function loadSystemHealth() {
    try {
      const res = await fetch('/api/v1/health');
      if (res.ok) {
        const data = await res.json();
        const dot = document.getElementById('sidebarDot');
        const statusText = document.getElementById('sidebarStatus');
        const fastApiStatus = document.getElementById('sysFastApiStatus');
        const dbStatus = document.getElementById('sysDbStatus');
        const storageStatus = document.getElementById('sysStorageStatus');

        if (dot) dot.className = data.status === 'healthy' ? 'status-dot online' : 'status-dot';
        if (statusText) statusText.textContent = data.status === 'healthy' ? 'System Operational' : 'Degraded';
        if (fastApiStatus) fastApiStatus.textContent = 'Online';
        if (dbStatus) dbStatus.textContent = data.database_connected ? 'Connected' : 'Disconnected';
        if (storageStatus) storageStatus.textContent = data.storage_directories_ready ? 'Verified' : 'Unavailable';
      }
    } catch (e) {
      console.error('Failed to probe health endpoint:', e);
    }
  }

  const sysTestSimBtn = document.getElementById('sysTestSimBtn');
  const sysTestClusterBtn = document.getElementById('sysTestClusterBtn');
  const sysMlOutput = document.getElementById('sysMlOutput');

  if (sysTestSimBtn) {
    sysTestSimBtn.addEventListener('click', async () => {
      sysMlOutput.textContent = "Calculating Scikit-Learn TF-IDF Cosine Similarity...";
      try {
        const res = await fetch('/api/v1/ml/similarity', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: "data encryption standards",
            documents: [
              "All enterprise data at rest must employ AES-256 encryption.",
              "Quarterly enterprise financial audit reports positive growth."
            ]
          })
        });
        const data = await res.json();
        sysMlOutput.textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        sysMlOutput.textContent = "Error: " + e.message;
      }
    });
  }

  if (sysTestClusterBtn) {
    sysTestClusterBtn.addEventListener('click', async () => {
      sysMlOutput.textContent = "Fitting Scikit-Learn K-Means centroids across document vectors...";
      try {
        const res = await fetch('/api/v1/ml/cluster', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            documents: [
              "Python machine learning artificial intelligence neural models.",
              "FastAPI rest api async backend database service.",
              "Deep learning convolutional transformer architectures.",
              "Relational database sqlite postgresql migrations and schemas."
            ],
            num_clusters: 2
          })
        });
        const data = await res.json();
        sysMlOutput.textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        sysMlOutput.textContent = "Error: " + e.message;
      }
    });
  }

  // ============================================================================
  // 14. COLLECTIONS & FOLDERS MODULE
  // ============================================================================

  let currentActiveCollection = null;

  async function loadCollections() {
    const grid = document.getElementById('collectionsGrid');
    if (!grid) return;
    grid.innerHTML = '<div style="color: var(--text-muted); padding: 1.5rem;">Loading collections...</div>';

    try {
      const res = await fetch('/api/v1/workspace/collections');
      if (res.ok) {
        const collections = await res.json();
        renderCollections(collections);
      } else {
        grid.innerHTML = '<div style="color: var(--danger);">Failed to load collections.</div>';
      }
    } catch (e) {
      grid.innerHTML = `<div style="color: var(--danger);">Connection error: ${e.message}</div>`;
    }
  }

  function renderCollections(collections) {
    const grid = document.getElementById('collectionsGrid');
    if (!collections || collections.length === 0) {
      grid.innerHTML = '<div style="color: var(--text-muted); padding: 1rem;">No document collections created yet. Click "➕ New Collection" to organize your repository.</div>';
      return;
    }

    grid.innerHTML = collections.map(c => `
      <div class="collection-card" data-col-id="${c.id}" style="border-top: 4px solid ${c.color || '#7667D8'};">
        <div class="collection-header-row">
          <span class="collection-icon-wrap">${c.icon || '📁'}</span>
          <span class="collection-count-pill">${c.document_count} ${c.document_count === 1 ? 'doc' : 'docs'}</span>
        </div>
        <div class="collection-title">${escapeHtml(c.name)}</div>
        <div class="collection-desc">${escapeHtml(c.description || 'No description provided.')}</div>
        <button class="btn btn-outline btn-sm btn-block view-col-btn" data-col-id="${c.id}">
          Open Folder →
        </button>
      </div>
    `).join('');

    // Wire open folder buttons
    grid.querySelectorAll('.view-col-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const colId = btn.getAttribute('data-col-id');
        const col = collections.find(c => c.id === colId);
        if (col) openCollectionDetail(col);
      });
    });

    grid.querySelectorAll('.collection-card').forEach(card => {
      card.addEventListener('click', () => {
        const colId = card.getAttribute('data-col-id');
        const col = collections.find(c => c.id === colId);
        if (col) openCollectionDetail(col);
      });
    });
  }

  async function openCollectionDetail(col) {
    currentActiveCollection = col;
    const detailCard = document.getElementById('collectionDetailCard');
    const title = document.getElementById('activeColTitle');
    const desc = document.getElementById('activeColDesc');
    const tableBody = document.getElementById('colDocsTable');

    detailCard.style.display = 'block';
    title.textContent = `${col.icon || '📁'} ${col.name}`;
    desc.textContent = col.description || 'Enterprise document collection';
    tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Loading collection documents...</td></tr>';

    try {
      const res = await fetch('/api/v1/navigator/documents');
      if (res.ok) {
        const data = await res.json();
        const allDocs = data.documents || [];
        const memberDocs = allDocs.filter(d => (col.document_ids || []).includes(d.id));

        if (memberDocs.length === 0) {
          tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No documents mapped to this collection yet. Click "📁 Add Documents" above.</td></tr>';
        } else {
          tableBody.innerHTML = memberDocs.map(d => `
            <tr>
              <td><strong>${escapeHtml(d.filename)}</strong></td>
              <td><span class="file-badge ${d.file_type.toLowerCase()}">${d.file_type}</span></td>
              <td>${formatBytes(d.file_size_bytes)}</td>
              <td>${d.chunk_count}</td>
              <td>
                <button class="btn btn-outline btn-sm remove-doc-col-btn" data-doc-id="${d.id}" style="color: var(--danger); border-color: #fecaca;">
                  Remove
                </button>
              </td>
            </tr>
          `).join('');

          tableBody.querySelectorAll('.remove-doc-col-btn').forEach(b => {
            b.addEventListener('click', async () => {
              const docId = b.getAttribute('data-doc-id');
              await removeDocFromCollection(col.id, docId);
            });
          });
        }
      }
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="5" style="color: var(--danger);">Error: ${e.message}</td></tr>`;
    }

    detailCard.scrollIntoView({ behavior: 'smooth' });
  }

  // Create Collection Modal
  const openCreateColModalBtn = document.getElementById('openCreateColModalBtn');
  const createCollectionModal = document.getElementById('createCollectionModal');
  const closeCreateColModalBtn = document.getElementById('closeCreateColModalBtn');
  const cancelCreateColBtn = document.getElementById('cancelCreateColBtn');
  const createCollectionForm = document.getElementById('createCollectionForm');
  const createColFeedback = document.getElementById('createColFeedback');

  if (openCreateColModalBtn) openCreateColModalBtn.addEventListener('click', () => {
    createCollectionForm.reset();
    createColFeedback.style.display = 'none';
    createCollectionModal.style.display = 'flex';
  });

  const closeCreateModal = () => { if (createCollectionModal) createCollectionModal.style.display = 'none'; };
  if (closeCreateColModalBtn) closeCreateColModalBtn.addEventListener('click', closeCreateModal);
  if (cancelCreateColBtn) cancelCreateColBtn.addEventListener('click', closeCreateModal);

  if (createCollectionForm) {
    createCollectionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('newColName').value.trim();
      const desc = document.getElementById('newColDesc').value.trim();
      const color = document.getElementById('newColColor').value;
      const icon = document.getElementById('newColIcon').value;

      try {
        const res = await fetch('/api/v1/workspace/collections', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
          },
          body: JSON.stringify({ name, description: desc, color, icon })
        });
        const data = await res.json();
        if (res.ok) {
          closeCreateModal();
          loadCollections();
          fetchUnreadNotificationsCount();
        } else {
          createColFeedback.className = 'alert-box alert-error';
          createColFeedback.textContent = data.detail || 'Failed to create collection.';
          createColFeedback.style.display = 'block';
        }
      } catch (err) {
        createColFeedback.className = 'alert-box alert-error';
        createColFeedback.textContent = `Error: ${err.message}`;
        createColFeedback.style.display = 'block';
      }
    });
  }

  // Delete Collection
  const deleteColBtn = document.getElementById('deleteColBtn');
  if (deleteColBtn) {
    deleteColBtn.addEventListener('click', async () => {
      if (!currentActiveCollection) return;
      if (!confirm(`Are you sure you want to delete the collection '${currentActiveCollection.name}'? (Documents will remain in your library)`)) return;

      try {
        const res = await fetch(`/api/v1/workspace/collections/${currentActiveCollection.id}`, {
          method: 'DELETE',
          headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
        });
        if (res.ok) {
          document.getElementById('collectionDetailCard').style.display = 'none';
          currentActiveCollection = null;
          loadCollections();
          fetchUnreadNotificationsCount();
        }
      } catch (err) {
        alert('Failed to delete collection: ' + err.message);
      }
    });
  }

  // Manage Collection Documents Modal
  const assignDocsBtn = document.getElementById('assignDocsBtn');
  const manageCollectionDocsModal = document.getElementById('manageCollectionDocsModal');
  const closeManageColDocsModalBtn = document.getElementById('closeManageColDocsModalBtn');
  const cancelManageColDocsBtn = document.getElementById('cancelManageColDocsBtn');
  const saveColDocsBtn = document.getElementById('saveColDocsBtn');
  const availableDocsCheckboxList = document.getElementById('availableDocsCheckboxList');
  const manageColDocsFeedback = document.getElementById('manageColDocsFeedback');

  if (assignDocsBtn) {
    assignDocsBtn.addEventListener('click', async () => {
      if (!currentActiveCollection) return;
      document.getElementById('manageColDocsModalTitle').textContent = `Assign Documents to '${currentActiveCollection.name}'`;
      manageColDocsFeedback.style.display = 'none';
      availableDocsCheckboxList.innerHTML = '<div style="padding: 1rem; color: var(--text-muted);">Loading repository documents...</div>';
      manageCollectionDocsModal.style.display = 'flex';

      try {
        const res = await fetch('/api/v1/navigator/documents');
        if (res.ok) {
          const data = await res.json();
          const docs = data.documents || [];
          if (docs.length === 0) {
            availableDocsCheckboxList.innerHTML = '<div style="padding: 1rem; color: var(--text-muted);">No documents available in repository.</div>';
          } else {
            const currentIds = currentActiveCollection.document_ids || [];
            availableDocsCheckboxList.innerHTML = docs.map(d => `
              <label class="checkbox-label" style="padding: 0.35rem 0.5rem; background: #ffffff; border-radius: 4px; border: 1px solid var(--border-color);">
                <input type="checkbox" class="col-doc-checkbox" value="${d.id}" ${currentIds.includes(d.id) ? 'checked' : ''} />
                <span><strong>${escapeHtml(d.filename)}</strong> <span style="font-size: 0.75rem; color: var(--text-muted);">(${d.file_type}, ${d.chunk_count} chunks)</span></span>
              </label>
            `).join('');
          }
        }
      } catch (e) {
        availableDocsCheckboxList.innerHTML = `<div style="color: var(--danger);">Error: ${e.message}</div>`;
      }
    });
  }

  const closeManageModal = () => { if (manageCollectionDocsModal) manageCollectionDocsModal.style.display = 'none'; };
  if (closeManageColDocsModalBtn) closeManageColDocsModalBtn.addEventListener('click', closeManageModal);
  if (cancelManageColDocsBtn) cancelManageColDocsBtn.addEventListener('click', closeManageModal);

  if (saveColDocsBtn) {
    saveColDocsBtn.addEventListener('click', async () => {
      if (!currentActiveCollection) return;
      const selected = Array.from(document.querySelectorAll('.col-doc-checkbox:checked')).map(cb => cb.value);

      try {
        const res = await fetch(`/api/v1/workspace/collections/${currentActiveCollection.id}/documents`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
          },
          body: JSON.stringify({ document_ids: selected })
        });
        if (res.ok) {
          closeManageModal();
          const colsRes = await fetch('/api/v1/workspace/collections');
          if (colsRes.ok) {
            const cols = await colsRes.json();
            const updated = cols.find(c => c.id === currentActiveCollection.id);
            if (updated) openCollectionDetail(updated);
            renderCollections(cols);
          }
        } else {
          manageColDocsFeedback.className = 'alert-box alert-error';
          manageColDocsFeedback.textContent = 'Failed to assign documents.';
          manageColDocsFeedback.style.display = 'block';
        }
      } catch (err) {
        manageColDocsFeedback.className = 'alert-box alert-error';
        manageColDocsFeedback.textContent = err.message;
        manageColDocsFeedback.style.display = 'block';
      }
    });
  }

  async function removeDocFromCollection(colId, docId) {
    try {
      const res = await fetch(`/api/v1/workspace/collections/${colId}/documents/${docId}`, {
        method: 'DELETE',
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
      });
      if (res.ok) {
        const colsRes = await fetch('/api/v1/workspace/collections');
        if (colsRes.ok) {
          const cols = await colsRes.json();
          const updated = cols.find(c => c.id === colId);
          if (updated) openCollectionDetail(updated);
          renderCollections(cols);
        }
      }
    } catch (e) {
      alert('Error removing document: ' + e.message);
    }
  }


  // ============================================================================
  // 15. SAVED INSIGHTS & SEARCH HISTORY MODULE
  // ============================================================================

  const tabSavedAnswersBtn = document.getElementById('tabSavedAnswersBtn');
  const tabSearchHistoryBtn = document.getElementById('tabSearchHistoryBtn');
  const savedAnswersTabContent = document.getElementById('savedAnswersTabContent');
  const searchHistoryTabContent = document.getElementById('searchHistoryTabContent');
  const exportSavedAnswersBtn = document.getElementById('exportSavedAnswersBtn');

  if (exportSavedAnswersBtn) {
    exportSavedAnswersBtn.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/v1/workspace/saved-answers', {
          headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
        });
        if (res.ok) {
          const answers = await res.json();
          if (!answers || answers.length === 0) {
            alert('No saved bookmarks to export.');
            return;
          }
          const blob = new Blob([JSON.stringify(answers, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `saved_knowledge_insights_${new Date().toISOString().slice(0, 10)}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } else {
          alert('Failed to retrieve saved answers for export.');
        }
      } catch (err) {
        alert('Export error: ' + err.message);
      }
    });
  }

  if (tabSavedAnswersBtn && tabSearchHistoryBtn) {
    tabSavedAnswersBtn.addEventListener('click', () => {
      tabSavedAnswersBtn.classList.add('active');
      tabSearchHistoryBtn.classList.remove('active');
      savedAnswersTabContent.style.display = 'block';
      searchHistoryTabContent.style.display = 'none';
      loadSavedAnswers();
    });

    tabSearchHistoryBtn.addEventListener('click', () => {
      tabSearchHistoryBtn.classList.add('active');
      tabSavedAnswersBtn.classList.remove('active');
      searchHistoryTabContent.style.display = 'block';
      savedAnswersTabContent.style.display = 'none';
      loadSearchHistory();
    });
  }

  async function loadSavedData() {
    await Promise.all([loadSavedAnswers(), loadSearchHistory()]);
  }

  async function loadSavedAnswers() {
    const list = document.getElementById('savedAnswersList');
    if (!list) return;
    list.innerHTML = '<div style="color: var(--text-muted); padding: 1.5rem; text-align: center;">Loading bookmarked answers...</div>';

    try {
      const res = await fetch('/api/v1/workspace/saved-answers', {
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
      });
      if (res.ok) {
        const answers = await res.json();
        renderSavedAnswers(answers);
      } else {
        list.innerHTML = '<div style="color: var(--danger); padding: 1rem;">Failed to load saved answers.</div>';
      }
    } catch (e) {
      list.innerHTML = `<div style="color: var(--danger); padding: 1rem;">Error: ${e.message}</div>`;
    }
  }

  function renderSavedAnswers(answers) {
    const list = document.getElementById('savedAnswersList');
    if (!answers || answers.length === 0) {
      list.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">No bookmarked answers yet. In the Grounded AI Assistant, click "⭐ Save" to bookmark answers with verifiable citations.</div>';
      return;
    }

    list.innerHTML = answers.map(a => `
      <div class="saved-answer-card">
        <div class="saved-card-header">
          <div>
            <div class="saved-card-title">❓ ${escapeHtml(a.question)}</div>
            <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.2rem;">
              Bookmarked on ${a.created_at ? new Date(a.created_at).toLocaleString() : 'Recently'}
            </div>
          </div>
          <div class="saved-card-meta">
            <span class="badge-tag tag-primary">${a.mode.toUpperCase()}</span>
            <button class="btn btn-outline btn-sm copy-saved-btn" data-text="${encodeURIComponent(a.answer)}" title="Copy answer">📋 Copy</button>
            <button class="btn btn-outline btn-sm delete-saved-btn" data-id="${a.id}" style="color: var(--danger); border-color: #fecaca;" title="Remove bookmark">🗑️</button>
          </div>
        </div>

        <div class="saved-card-answer">${escapeHtml(a.answer)}</div>

        ${a.citations && a.citations.length > 0 ? `
          <div style="margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center;">
            <strong style="font-size: 0.78rem; color: var(--text-muted);">Citations:</strong>
            ${a.citations.map(c => `<span class="citation-pill" style="font-size: 0.75rem; cursor: pointer;" onclick="window.openCitationPreview('${escapeHtml(c.filename)}', ${c.page_number || 1})" title="Click to view verified source document and page">📄 ${escapeHtml(c.filename)} (p.${c.page_number || 1})</span>`).join('')}
          </div>
        ` : ''}

        <div class="saved-notes-box">
          <div>
            <strong style="color: var(--text-main);">Note:</strong>
            <span id="note-text-${a.id}" style="color: var(--text-muted); margin-left: 0.35rem;">
              ${a.user_notes ? escapeHtml(a.user_notes) : '<em>No annotation added.</em>'}
            </span>
          </div>
          <button class="btn btn-outline btn-sm edit-note-btn" data-id="${a.id}" style="font-size: 0.75rem; padding: 0.2rem 0.5rem;">
            ✏️ Edit Note
          </button>
        </div>
      </div>
    `).join('');

    // Wire copy buttons
    list.querySelectorAll('.copy-saved-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = decodeURIComponent(btn.getAttribute('data-text'));
        if (navigator.clipboard) {
          navigator.clipboard.writeText(text);
          btn.textContent = '✓ Copied';
          setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000);
        }
      });
    });

    // Wire delete buttons
    list.querySelectorAll('.delete-saved-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        if (!confirm('Remove this saved answer from bookmarks?')) return;
        try {
          const res = await fetch(`/api/v1/workspace/saved-answers/${id}`, {
            method: 'DELETE',
            headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
          });
          if (res.ok) loadSavedAnswers();
        } catch (e) {
          alert('Failed to delete bookmark: ' + e.message);
        }
      });
    });

    // Wire edit note buttons
    list.querySelectorAll('.edit-note-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        const currentText = document.getElementById(`note-text-${id}`).textContent.trim();
        const note = prompt('Enter your personal note or audit reference for this answer:', currentText.includes('No annotation') ? '' : currentText);
        if (note !== null) {
          try {
            const res = await fetch(`/api/v1/workspace/saved-answers/${id}/note`, {
              method: 'PATCH',
              headers: {
                'Content-Type': 'application/json',
                ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
              },
              body: JSON.stringify({ user_notes: note })
            });
            if (res.ok) loadSavedAnswers();
          } catch (e) {
            alert('Error updating note: ' + e.message);
          }
        }
      });
    });
  }

  async function loadSearchHistory() {
    const tableBody = document.getElementById('searchHistoryTable');
    if (!tableBody) return;

    try {
      const res = await fetch('/api/v1/workspace/search-history?limit=30', {
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
      });
      if (res.ok) {
        const history = await res.json();
        if (history.length === 0) {
          tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No search queries recorded yet.</td></tr>';
          return;
        }

        tableBody.innerHTML = history.map(h => `
          <tr>
            <td><strong>${escapeHtml(h.query_text)}</strong></td>
            <td><span class="badge-tag tag-primary">${h.search_mode.toUpperCase()}</span></td>
            <td>${h.result_count} items</td>
            <td>${Number(h.top_score).toFixed(3)}</td>
            <td style="font-size: 0.8rem; color: var(--text-muted);">${h.created_at ? new Date(h.created_at).toLocaleTimeString() : '-'}</td>
            <td>
              <button class="btn btn-outline btn-sm rerun-search-btn" data-query="${escapeHtml(h.query_text)}" data-mode="${h.search_mode}">
                Re-run 🔍
              </button>
            </td>
          </tr>
        `).join('');

        tableBody.querySelectorAll('.rerun-search-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            const mode = btn.getAttribute('data-mode');
            const searchInput = document.getElementById('searchInput');
            const modeSelect = document.getElementById('searchModeSelect');
            if (searchInput) searchInput.value = query;
            if (modeSelect) modeSelect.value = mode;
            switchView('search');
            executeSearch();
          });
        });
      }
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="6" style="color: var(--danger);">Error: ${e.message}</td></tr>`;
    }
  }

  const clearSearchHistBtn = document.getElementById('clearSearchHistBtn');
  if (clearSearchHistBtn) {
    clearSearchHistBtn.addEventListener('click', async () => {
      if (!confirm('Clear all search history records?')) return;
      try {
        const res = await fetch('/api/v1/workspace/search-history', {
          method: 'DELETE',
          headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
        });
        if (res.ok) loadSearchHistory();
      } catch (e) {
        alert('Failed to clear search history: ' + e.message);
      }
    });
  }


  // ============================================================================
  // 16. NOTIFICATIONS CENTER MODULE
  // ============================================================================

  async function fetchUnreadNotificationsCount() {
    const badge = document.getElementById('notifBadge');
    if (!badge || !authToken) return;

    try {
      const res = await fetch('/api/v1/workspace/notifications', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.unread_count > 0) {
          badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
          badge.style.display = 'inline-block';
        } else {
          badge.style.display = 'none';
        }
      }
    } catch (e) {
      // Polling error ignored
    }
  }

  async function loadNotifications() {
    const list = document.getElementById('notificationsFullList');
    if (!list) return;
    list.innerHTML = '<div style="color: var(--text-muted); padding: 1.5rem; text-align: center;">Loading notifications...</div>';

    try {
      const res = await fetch('/api/v1/workspace/notifications', {
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
      });
      if (res.ok) {
        const data = await res.json();
        renderNotifications(data.items);
        fetchUnreadNotificationsCount();
      } else {
        list.innerHTML = '<div style="color: var(--danger); padding: 1rem;">Failed to load notifications.</div>';
      }
    } catch (e) {
      list.innerHTML = `<div style="color: var(--danger); padding: 1rem;">Error: ${e.message}</div>`;
    }
  }

  function getCategoryIcon(cat) {
    if (cat === 'ingestion') return '📁';
    if (cat === 'evaluation') return '📈';
    if (cat === 'security') return '🛡️';
    return '⚙️';
  }

  function renderNotifications(items) {
    const list = document.getElementById('notificationsFullList');
    if (!items || items.length === 0) {
      list.innerHTML = '<div style="color: var(--text-muted); padding: 2rem; text-align: center;">No notifications currently present. Platform alerts will appear here in real-time.</div>';
      return;
    }

    list.innerHTML = items.map(n => `
      <div class="notification-row ${n.is_read ? 'read' : 'unread'}" data-id="${n.id}">
        <span class="notif-category-icon">${getCategoryIcon(n.category)}</span>
        <div class="notif-body">
          <div class="notif-title">${escapeHtml(n.title)}</div>
          <div class="notif-message">${escapeHtml(n.message)}</div>
          <div class="notif-meta">
            <span>${n.created_at ? new Date(n.created_at).toLocaleString() : 'Just now'}</span>
            <span>•</span>
            <span style="text-transform: capitalize;">${n.category}</span>
          </div>
        </div>
        ${!n.is_read ? '<span class="unread-dot" title="Unread notification"></span>' : ''}
      </div>
    `).join('');

    list.querySelectorAll('.notification-row.unread').forEach(row => {
      row.addEventListener('click', async () => {
        const id = row.getAttribute('data-id');
        try {
          await fetch(`/api/v1/workspace/notifications/${id}/read`, {
            method: 'PATCH',
            headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
          });
          row.classList.remove('unread');
          const dot = row.querySelector('.unread-dot');
          if (dot) dot.remove();
          fetchUnreadNotificationsCount();
        } catch (e) {}
      });
    });
  }

  const markAllNotifsReadBtn = document.getElementById('markAllNotifsReadBtn');
  if (markAllNotifsReadBtn) {
    markAllNotifsReadBtn.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/v1/workspace/notifications/mark-all-read', {
          method: 'POST',
          headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
        });
        if (res.ok) {
          loadNotifications();
        }
      } catch (e) {
        alert('Failed to mark all as read: ' + e.message);
      }
    });
  }


  // ============================================================================
  // 17. PERSONAL PROFILE & PREFERENCES MODULE
  // ============================================================================

  const tabEditProfileBtn = document.getElementById('tabEditProfileBtn');
  const tabChangePwdBtn = document.getElementById('tabChangePwdBtn');
  const tabPreferencesBtn = document.getElementById('tabPreferencesBtn');
  const editProfileForm = document.getElementById('editProfileForm');
  const changePasswordForm = document.getElementById('changePasswordForm');
  const preferencesForm = document.getElementById('preferencesForm');

  if (tabEditProfileBtn && tabChangePwdBtn && tabPreferencesBtn) {
    tabEditProfileBtn.addEventListener('click', () => {
      tabEditProfileBtn.classList.add('active');
      tabChangePwdBtn.classList.remove('active');
      tabPreferencesBtn.classList.remove('active');
      editProfileForm.style.display = 'block';
      changePasswordForm.style.display = 'none';
      preferencesForm.style.display = 'none';
    });

    tabChangePwdBtn.addEventListener('click', () => {
      tabChangePwdBtn.classList.add('active');
      tabEditProfileBtn.classList.remove('active');
      tabPreferencesBtn.classList.remove('active');
      editProfileForm.style.display = 'none';
      changePasswordForm.style.display = 'block';
      preferencesForm.style.display = 'none';
    });

    tabPreferencesBtn.addEventListener('click', () => {
      tabPreferencesBtn.classList.add('active');
      tabEditProfileBtn.classList.remove('active');
      tabChangePwdBtn.classList.remove('active');
      editProfileForm.style.display = 'none';
      changePasswordForm.style.display = 'none';
      preferencesForm.style.display = 'block';
    });
  }

  async function loadUserProfile() {
    if (!authToken) return;

    try {
      const res = await fetch('/api/v1/workspace/profile/me', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        document.getElementById('profBigAvatar').textContent = (data.full_name || 'U').charAt(0).toUpperCase();
        document.getElementById('profCardName').textContent = data.full_name;
        document.getElementById('profCardEmail').textContent = data.email;
        document.getElementById('profCardRole').textContent = formatRoleName(data.role);
        document.getElementById('profCardOrg').textContent = data.organization;
        document.getElementById('profCardId').textContent = data.id;
        document.getElementById('profCardCreated').textContent = data.created_at ? new Date(data.created_at).toLocaleDateString() : 'N/A';
        document.getElementById('profCardLastLogin').textContent = data.last_login_at ? new Date(data.last_login_at).toLocaleString() : 'Active session';

        if (document.getElementById('profCardPhone')) {
          document.getElementById('profCardPhone').textContent = data.phone_number || 'Not provided';
        }
        if (document.getElementById('profEditPhone')) {
          document.getElementById('profEditPhone').value = data.phone_number || '';
        }
        if (document.getElementById('profCardStatus')) {
          document.getElementById('profCardStatus').textContent = data.is_verified ? 'Active & Verified' : 'Active (Pending Verification)';
          document.getElementById('profCardStatus').style.color = data.is_verified ? 'var(--success)' : 'var(--warning)';
        }

        document.getElementById('profEditName').value = data.full_name;
        document.getElementById('profEditOrg').value = data.organization;

        if (data.preferences) {
          const pref = data.preferences;
          if (document.getElementById('prefDefaultMode')) document.getElementById('prefDefaultMode').value = pref.default_search_mode || 'hybrid';
          if (document.getElementById('prefTopK')) document.getElementById('prefTopK').value = pref.default_top_k || 5;
          if (document.getElementById('prefGraphRag')) document.getElementById('prefGraphRag').checked = pref.graphrag_enabled !== false;
          if (document.getElementById('prefCompactView')) document.getElementById('prefCompactView').checked = !!pref.compact_table_view;
        }
      }
    } catch (e) {
      console.error('Failed to load user profile:', e);
    }
  }

  if (editProfileForm) {
    editProfileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const profFeedback = document.getElementById('profFeedback');
      profFeedback.style.display = 'none';

      const full_name = document.getElementById('profEditName').value.trim();
      const organization = document.getElementById('profEditOrg').value.trim();
      const phone_number = document.getElementById('profEditPhone') ? document.getElementById('profEditPhone').value.trim() : null;

      try {
        const res = await fetch('/api/v1/workspace/profile/update', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
          },
          body: JSON.stringify({ full_name, organization, phone_number })
        });
        const data = await res.json();
        if (res.ok) {
          currentUser.full_name = full_name;
          currentUser.organization = organization;
          applyRolePermissions(currentUser.role);
          profFeedback.className = 'alert-box alert-success';
          profFeedback.textContent = '✓ Profile updated successfully!';
          profFeedback.style.display = 'block';
          loadUserProfile();
          fetchUnreadNotificationsCount();
        } else {
          profFeedback.className = 'alert-box alert-error';
          profFeedback.textContent = data.detail || 'Failed to update profile.';
          profFeedback.style.display = 'block';
        }
      } catch (err) {
        profFeedback.className = 'alert-box alert-error';
        profFeedback.textContent = err.message;
        profFeedback.style.display = 'block';
      }
    });
  }

  if (changePasswordForm) {
    changePasswordForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pwdFeedback = document.getElementById('pwdFeedback');
      pwdFeedback.style.display = 'none';

      const current_password = document.getElementById('pwdCurrent').value;
      const new_password = document.getElementById('pwdNew').value;
      const confirm_password = document.getElementById('pwdConfirm').value;

      if (new_password !== confirm_password) {
        pwdFeedback.className = 'alert-box alert-error';
        pwdFeedback.textContent = 'New password and confirmation do not match.';
        pwdFeedback.style.display = 'block';
        return;
      }

      try {
        const res = await fetch('/api/v1/workspace/profile/change-password', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
          },
          body: JSON.stringify({ current_password, new_password })
        });
        const data = await res.json();
        if (res.ok) {
          pwdFeedback.className = 'alert-box alert-success';
          pwdFeedback.textContent = '✓ Password changed successfully!';
          pwdFeedback.style.display = 'block';
          changePasswordForm.reset();
          fetchUnreadNotificationsCount();
        } else {
          pwdFeedback.className = 'alert-box alert-error';
          pwdFeedback.textContent = data.detail || 'Password change failed.';
          pwdFeedback.style.display = 'block';
        }
      } catch (err) {
        pwdFeedback.className = 'alert-box alert-error';
        pwdFeedback.textContent = err.message;
        pwdFeedback.style.display = 'block';
      }
    });
  }

  if (preferencesForm) {
    preferencesForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const prefFeedback = document.getElementById('prefFeedback');
      prefFeedback.style.display = 'none';

      const default_search_mode = document.getElementById('prefDefaultMode').value;
      const default_top_k = parseInt(document.getElementById('prefTopK').value, 10);
      const graphrag_enabled = document.getElementById('prefGraphRag').checked;
      const compact_table_view = document.getElementById('prefCompactView').checked;

      try {
        const res = await fetch('/api/v1/workspace/profile/preferences', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
          },
          body: JSON.stringify({
            default_search_mode,
            default_top_k,
            graphrag_enabled,
            compact_table_view
          })
        });
        if (res.ok) {
          prefFeedback.className = 'alert-box alert-success';
          prefFeedback.textContent = '✓ Preferences saved!';
          prefFeedback.style.display = 'block';

          const assistantGraphRagToggle = document.getElementById('assistantGraphRagToggle');
          if (assistantGraphRagToggle) assistantGraphRagToggle.checked = graphrag_enabled;
          const searchModeSelect = document.getElementById('searchModeSelect');
          if (searchModeSelect) searchModeSelect.value = default_search_mode;
        } else {
          prefFeedback.className = 'alert-box alert-error';
          prefFeedback.textContent = 'Failed to save preferences.';
          prefFeedback.style.display = 'block';
        }
      } catch (err) {
        prefFeedback.className = 'alert-box alert-error';
        prefFeedback.textContent = err.message;
        prefFeedback.style.display = 'block';
      }
    });
  }


  // ============================================================================
  // 18. REPORTS & DATA EXPORT CENTER MODULE
  // ============================================================================

  function loadReportsData() {
    // Export module ready
  }

  async function downloadExportFile(url, filename) {
    try {
      const res = await fetch(url, {
        headers: { ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) }
      });
      if (!res.ok) {
        alert('Failed to generate export file. Server returned: ' + res.status);
        return;
      }
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      alert('Export download error: ' + err.message);
    }
  }

  const exportDocsCsvBtn = document.getElementById('exportDocsCsvBtn');
  const exportDocsJsonBtn = document.getElementById('exportDocsJsonBtn');
  if (exportDocsCsvBtn) exportDocsCsvBtn.addEventListener('click', () => downloadExportFile('/api/v1/workspace/reports/export/documents?format=csv', 'documents_inventory.csv'));
  if (exportDocsJsonBtn) exportDocsJsonBtn.addEventListener('click', () => downloadExportFile('/api/v1/workspace/reports/export/documents?format=json', 'documents_inventory.json'));

  const exportEvalCsvBtn = document.getElementById('exportEvalCsvBtn');
  const exportEvalJsonBtn = document.getElementById('exportEvalJsonBtn');
  if (exportEvalCsvBtn) exportEvalCsvBtn.addEventListener('click', () => downloadExportFile('/api/v1/workspace/reports/export/evaluations?format=csv', 'evaluation_benchmarks.csv'));
  if (exportEvalJsonBtn) exportEvalJsonBtn.addEventListener('click', () => downloadExportFile('/api/v1/workspace/reports/export/evaluations?format=json', 'evaluation_benchmarks.json'));

  const exportLogsCsvBtn = document.getElementById('exportLogsCsvBtn');
  const exportLogsJsonBtn = document.getElementById('exportLogsJsonBtn');
  if (exportLogsCsvBtn) exportLogsCsvBtn.addEventListener('click', () => downloadExportFile('/api/v1/workspace/reports/export/audit-logs?format=csv', 'system_audit_logs.csv'));
  if (exportLogsJsonBtn) exportLogsJsonBtn.addEventListener('click', () => downloadExportFile('/api/v1/workspace/reports/export/audit-logs?format=json', 'system_audit_logs.json'));


  // ============================================================================
  // 19. UTILITIES & INITIAL LOAD
  // ============================================================================

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  let isRefreshingGlobal = false;

  async function handleGlobalRefresh() {
    if (isRefreshingGlobal) return;
    isRefreshingGlobal = true;

    const refreshBtn = document.getElementById('refreshAllBtn');
    const refreshSpan = refreshBtn ? refreshBtn.querySelector('span') : null;

    if (refreshBtn) {
      refreshBtn.disabled = true;
      if (refreshSpan) refreshSpan.classList.add('is-spinning');
    }

    try {
      // 1. Always refresh global status & notifications
      const globalTasks = [
        loadSystemHealth(),
        fetchUnreadNotificationsCount()
      ];

      // 2. Dispatch refresh for the specific active view so the user's visible page updates
      let activeViewTask = null;
      switch (currentActiveView) {
        case 'dashboard':
          activeViewTask = loadDashboardMetrics();
          break;
        case 'documents':
          activeViewTask = loadDocumentsList();
          break;
        case 'collections':
          activeViewTask = loadCollections();
          break;
        case 'saved':
        case 'history':
          activeViewTask = loadSavedData();
          break;
        case 'graph':
          activeViewTask = loadKnowledgeGraph();
          break;
        case 'evaluation':
          activeViewTask = loadEvaluationHistory();
          break;
        case 'reports':
          activeViewTask = loadReportsData();
          break;
        case 'users':
          activeViewTask = loadUsersTable();
          break;
        case 'roles':
          activeViewTask = Promise.all([loadCustomRoles(), loadRolesMatrix()]);
          break;
        case 'audit':
          activeViewTask = loadAuditLogs();
          break;
        case 'system':
          activeViewTask = loadSystemHealth();
          break;
        case 'notifications':
          activeViewTask = loadNotifications();
          break;
        case 'profile':
          activeViewTask = loadUserProfile();
          break;
        default:
          activeViewTask = loadDashboardMetrics();
          break;
      }

      await Promise.all([...globalTasks, activeViewTask]);
    } catch (err) {
      console.error('Global refresh error:', err);
    } finally {
      if (refreshBtn) {
        refreshBtn.disabled = false;
        if (refreshSpan) refreshSpan.classList.remove('is-spinning');
      }
      isRefreshingGlobal = false;
    }
  }

  const refreshAllBtn = document.getElementById('refreshAllBtn');
  if (refreshAllBtn) {
    refreshAllBtn.addEventListener('click', handleGlobalRefresh);
  }

  // Kickstart application
  initApp();
});
