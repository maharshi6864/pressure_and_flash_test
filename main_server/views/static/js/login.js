document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('errorMessage');

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });
        
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('token', data.access_token);
            
            // Parse JWT to get role, username, and name
            const payload = JSON.parse(atob(data.access_token.split('.')[1]));
            localStorage.setItem('role', payload.role || 'user');
            localStorage.setItem('username', payload.sub);
            localStorage.setItem('name', payload.name || payload.sub);
            
            window.location.href = '/manage-proofs';
        } else {
            errorMsg.classList.remove('d-none');
        }
    } catch (err) {
        console.error(err);
        errorMsg.classList.remove('d-none');
        errorMsg.innerText = "Network error occurred.";
    }
});
