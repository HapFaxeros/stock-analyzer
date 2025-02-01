async function sendMessage() {
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    const symbol = window.location.pathname.split('/').pop();
    
    const question = input.value;
    if (!question) return;
    
    messages.innerHTML += `<div class="user-message">${question}</div>`;
    input.value = '';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                question: question
            })
        });
        
        const data = await response.json();
        messages.innerHTML += `<div class="ai-message">${data.response}</div>`;
        messages.scrollTop = messages.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
    }
} 