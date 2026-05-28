document.addEventListener('DOMContentLoaded', () => {
    let isLoggedIn = false;
    let isRegisterMode = false;

    const checkBtn = document.getElementById('checkBtn');
    const newsInput = document.getElementById('newsInput');
    const resultSection = document.getElementById('resultSection');
    const latestChecksSection = document.getElementById('latestChecksSection');
    
    // Result elements
    const cardTitle = document.getElementById('cardTitle');
    const cardDesc = document.getElementById('cardDesc');
    const trustScoreText = document.getElementById('trustScoreText');
    const factualityScore = document.getElementById('factualityScore');
    const mainResultCard = document.getElementById('mainResultCard');
    
    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const analyzeIcon = document.querySelector('.analyze-icon');

    // Modals
    const loginModal = document.getElementById('loginModal');
    const analysisModal = document.getElementById('analysisModal');
    
    // Auth Elements
    const loginBtnNav = document.getElementById('loginBtnNav');
    const toggleAuthMode = document.getElementById('toggleAuthMode');
    const toggleAuthText = document.getElementById('toggleAuthText');
    const loginModalTitle = document.getElementById('loginModalTitle');
    const submitLogin = document.getElementById('submitLogin');

    // History elements
    const historyCardsContainer = document.getElementById('historyCardsContainer');

    const fetchUser = async () => {
        try {
            const res = await fetch('/me');
            const data = await res.json();
            isLoggedIn = data.logged_in;
            if (isLoggedIn) {
                loginBtnNav.textContent = "Log Out";
                fetchHistory();
            } else {
                loginBtnNav.textContent = "Log In";
                if(historyCardsContainer) {
                    historyCardsContainer.innerHTML = '<p class="subtitle" id="historyMsg" style="margin-bottom: 2rem; font-size: 1rem;">Please log in to view your recent checks.</p>';
                }
            }
        } catch (e) {
            console.error(e);
        }
    };

    fetchUser();

    const fetchHistory = async () => {
        if (!historyCardsContainer) return;
        try {
            const res = await fetch('/history');
            if (!res.ok) return;
            const data = await res.json();
            
            historyCardsContainer.innerHTML = '';
            
            if (data.history && data.history.length > 0) {
                data.history.forEach(item => {
                    const isReal = item.prediction === 'Real News';
                    
                    const card = document.createElement('div');
                    card.className = 'result-card';
                    card.innerHTML = `
                        <div class="card-header">
                            <div class="icon ${isReal ? 'verified' : 'danger'}">
                                ${isReal ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>' : 
                                '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'}
                            </div>
                            <h5>Recent Check</h5>
                        </div>
                        <p class="card-desc" style="flex: 1;">"${item.text_preview}"</p>
                        <p class="card-score" style="margin-top: 1rem;"><strong>Verdict:</strong> <br><span class="score-text ${isReal ? 'green' : 'red'}">${item.prediction}</span></p>
                        <p class="card-source" style="margin-top: 0.5rem;"><small>${new Date(item.timestamp).toLocaleString()}</small></p>
                    `;
                    historyCardsContainer.appendChild(card);
                });
            } else {
                historyCardsContainer.innerHTML = '<p class="subtitle" style="margin-bottom: 2rem; font-size: 1rem;">No history found yet. Make your first check!</p>';
            }
        } catch (e) {
            console.error(e);
        }
    };

    // Auth Modal Links
    loginBtnNav.addEventListener('click', async () => {
        if(isLoggedIn){
            await fetch('/logout', { method: 'POST' });
            isLoggedIn = false;
            loginBtnNav.textContent = "Log In";
            if(historyCardsContainer) {
                historyCardsContainer.innerHTML = '<p class="subtitle" id="historyMsg" style="margin-bottom: 2rem; font-size: 1rem;">Please log in to view your recent checks.</p>';
            }
        } else {
            loginModal.classList.remove('hidden');
        }
    });

    document.getElementById('closeLogin').addEventListener('click', () => loginModal.classList.add('hidden'));
    
    if (toggleAuthMode) {
        toggleAuthMode.addEventListener('click', (e) => {
            e.preventDefault();
            isRegisterMode = !isRegisterMode;
            if (isRegisterMode) {
                loginModalTitle.textContent = "Register for TruthGuard";
                submitLogin.textContent = "Sign Up";
                toggleAuthText.textContent = "Already have an account? ";
                toggleAuthMode.textContent = "Log In";
            } else {
                loginModalTitle.textContent = "Log In to TruthGuard";
                submitLogin.textContent = "Sign In";
                toggleAuthText.textContent = "Don't have an account? ";
                toggleAuthMode.textContent = "Register";
            }
        });
    }

    submitLogin.addEventListener('click', async () => {
        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value.trim();
        
        if (!email || !password) {
            alert('Please fill in both fields.');
            return;
        }
        
        const endpoint = isRegisterMode ? '/register' : '/login';
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await response.json();
            
            if (response.ok) {
                alert(data.message);
                loginModal.classList.add('hidden');
                
                // Refresh user state
                fetchUser();
                
                document.getElementById('loginEmail').value = '';
                document.getElementById('loginPassword').value = '';
            } else {
                alert(data.error);
            }
        } catch (error) {
            alert("Error connecting to backend");
        }
    });

    const contactBtn = document.getElementById('contactBtn');
    if (contactBtn) {
        contactBtn.addEventListener('click', async () => {
            const msg = prompt("Enter your message to the TruthGuard team:");
            if (!msg) return;
            
            try {
                const response = await fetch('/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: isLoggedIn ? 'Logged-in User' : 'Anonymous', message: msg })
                });
                const data = await response.json();
                
                if (response.ok) {
                    alert("Thank you! " + data.message);
                } else {
                    alert(data.error);
                }
            } catch (error) {
                alert("Error sending message.");
            }
        });
    }

    // Analysis Modal Links
    const setupAnalysisTriggers = () => {
        document.querySelectorAll('.analysis-modal-trigger').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                analysisModal.classList.remove('hidden');
            });
        });
    };
    setupAnalysisTriggers();

    document.getElementById('closeAnalysis').addEventListener('click', () => analysisModal.classList.add('hidden'));
    document.getElementById('ackAnalysis').addEventListener('click', () => analysisModal.classList.add('hidden'));

    checkBtn.addEventListener('click', async () => {
        const text = newsInput.value.trim();
        if (!text) {
            alert('Please enter a URL or headline to analyze.');
            return;
        }

        btnText.textContent = 'Analyzing...';
        loader.classList.remove('hidden');
        analyzeIcon.classList.add('hidden');
        checkBtn.disabled = true;

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text })
            });

            const data = await response.json();

            if (response.ok) {
                latestChecksSection.classList.add('hidden');
                resultSection.classList.remove('hidden');

                if (data.prediction === 'Real News') {
                    cardTitle.textContent = 'News Content: Verified True';
                    cardDesc.textContent = 'Independent analysis confirms the reliability of this text based on our ML model.';
                    trustScoreText.innerHTML = `${data.confidence} Reliability - Green`;
                    trustScoreText.className = 'score-text green';
                    factualityScore.textContent = 'High Factuality';
                    factualityScore.className = 'indicator-score factuality green';
                    mainResultCard.querySelector('.icon').className = 'icon verified';
                    mainResultCard.querySelector('svg').innerHTML = '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>';
                } else {
                    cardTitle.textContent = 'News Content: Detected Fake';
                    cardDesc.textContent = 'Information could not be corroborated and shows patterns of misinformation.';
                    trustScoreText.innerHTML = `${data.confidence} Reliability - Red`;
                    trustScoreText.className = 'score-text red';
                    factualityScore.textContent = 'Low Factuality';
                    factualityScore.className = 'indicator-score factuality red';
                    mainResultCard.querySelector('.icon').className = 'icon danger';
                    mainResultCard.querySelector('svg').innerHTML = '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>';
                }

                setupAnalysisTriggers();
                
                if(isLoggedIn) {
                    fetchHistory();
                }
            } else {
                alert(data.error || 'An error occurred during prediction.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to connect to the server.');
        } finally {
            btnText.textContent = 'Analyze Now';
            loader.classList.add('hidden');
            analyzeIcon.classList.remove('hidden');
            checkBtn.disabled = false;
        }
    });

    newsInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            checkBtn.click();
        }
    });
});