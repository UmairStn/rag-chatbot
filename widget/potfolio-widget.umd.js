/**
 * RAG Chatbot Widget v1.0.0 - Portfolio Theme
 * Embeddable chat widget for RAG-powered chatbot with portfolio aesthetic
 */

(function(global) {
  'use strict';

  // Use the window object injected by the server
  const config = global.RAGChatBot || {
    apiUrl: 'http://localhost:3000',
    clientId: 'default'
  };

  const styles = `
    .rag-chat-widget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; position: fixed; bottom: 24px; right: 24px; z-index: 9999; }
    .rag-chat-bubble { width: 64px; height: 64px; border-radius: 12px; background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 8px 24px rgba(26, 188, 156, 0.3); font-size: 28px; border: none; }
    .rag-chat-bubble:hover { transform: scale(1.08); box-shadow: 0 12px 32px rgba(26, 188, 156, 0.4); }
    .rag-chat-window { position: absolute; bottom: 88px; right: 0; width: 400px; height: 650px; background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%); border-radius: 16px; display: none; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.4); animation: slideUp 0.3s ease; border: 1px solid rgba(26, 188, 156, 0.2); }
    .rag-chat-window.open { display: flex; }
    .rag-chat-header { background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%); color: white; padding: 24px; border-radius: 16px 16px 0 0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(26, 188, 156, 0.2); }
    .rag-chat-header h3 { margin: 0; font-size: 18px; font-weight: 700; letter-spacing: 0.5px; }
    .rag-chat-messages { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; background: transparent; }
    .rag-chat-messages::-webkit-scrollbar { width: 6px; }
    .rag-chat-messages::-webkit-scrollbar-track { background: transparent; }
    .rag-chat-messages::-webkit-scrollbar-thumb { background: rgba(26, 188, 156, 0.3); border-radius: 3px; }
    .rag-chat-messages::-webkit-scrollbar-thumb:hover { background: rgba(26, 188, 156, 0.5); }
    .rag-chat-message { display: flex; gap: 12px; margin-bottom: 8px; animation: fadeIn 0.3s ease; }
    .rag-chat-message.user { justify-content: flex-end; }
    .rag-chat-message-content { max-width: 85%; padding: 12px 16px; border-radius: 12px; word-wrap: break-word; line-height: 1.5; font-size: 14px; }
    .rag-chat-message-content strong { font-weight: 700; }
    .rag-chat-message-content .rag-chat-paragraph { margin: 0 0 8px 0; }
    .rag-chat-message-content .rag-chat-paragraph:last-child { margin-bottom: 0; }
    .rag-chat-message-content .rag-chat-paragraph--spacer { height: 8px; }
    .rag-chat-message-content .rag-chat-bullets { margin: 8px 0; padding-left: 20px; }
    .rag-chat-message-content .rag-chat-bullets li { margin: 6px 0; }
    .rag-chat-message-content a { color: #1abc9c; text-decoration: none; font-weight: 600; transition: color 0.2s; word-break: break-all; }
    .rag-chat-message-content a:hover { color: #16a085; text-decoration: underline; }
    .rag-chat-message.user .rag-chat-message-content { background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%); color: white; }
    .rag-chat-message.bot .rag-chat-message-content { background: rgba(26, 188, 156, 0.1); color: #e0e0e0; border: 1px solid rgba(26, 188, 156, 0.2); }
    .rag-chat-products-section { background: rgba(26, 188, 156, 0.08); border: 1px solid rgba(26, 188, 156, 0.3); border-radius: 10px; padding: 12px 14px; margin-top: 12px; }
    .rag-chat-products-header { font-weight: 700; color: #1abc9c; margin-bottom: 10px; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    .rag-chat-product-item { margin-bottom: 10px; font-size: 13px; line-height: 1.6; }
    .rag-chat-product-item:last-child { margin-bottom: 0; }
    .rag-chat-product-link { color: #1abc9c; text-decoration: none; word-break: break-all; transition: color 0.2s; font-weight: 500; }
    .rag-chat-product-link:hover { color: #16a085; text-decoration: underline; }
    .rag-chat-input-area { padding: 16px; border-top: 1px solid rgba(26, 188, 156, 0.1); display: flex; gap: 10px; background: rgba(26, 188, 156, 0.03); }
    .rag-chat-input { flex: 1; border: 1px solid rgba(26, 188, 156, 0.3); border-radius: 8px; padding: 12px 16px; font-size: 14px; outline: none; background: rgba(26, 188, 156, 0.05); color: #e0e0e0; transition: all 0.2s; }
    .rag-chat-input::placeholder { color: rgba(224, 224, 224, 0.4); }
    .rag-chat-input:focus { border-color: #1abc9c; background: rgba(26, 188, 156, 0.08); box-shadow: 0 0 12px rgba(26, 188, 156, 0.2); }
    .rag-chat-send { background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%); border: none; color: white; width: 44px; height: 44px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; transition: all 0.2s; flex-shrink: 0; }
    .rag-chat-send:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(26, 188, 156, 0.3); }
    .rag-chat-send:active { transform: translateY(0); }
    .rag-chat-send:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
    .rag-chat-close { background: rgba(26, 188, 156, 0.2); border: none; color: white; cursor: pointer; padding: 6px 8px; border-radius: 6px; font-size: 20px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
    .rag-chat-close:hover { background: rgba(26, 188, 156, 0.3); }
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  `;

  const html = `
    <div class="rag-chat-widget">
      <div class="rag-chat-bubble" id="rag-chat-toggle">💬</div>
      <div class="rag-chat-window" id="rag-chat-window">
        <div class="rag-chat-header">
          <h3>Assistant</h3>
          <button class="rag-chat-close" id="rag-chat-close">&times;</button>
        </div>
        <div class="rag-chat-messages" id="rag-chat-messages">
          <div class="rag-chat-message bot">
            <div class="rag-chat-message-content">👋 Hello! How can I assist you today?</div>
          </div>
        </div>
        <div class="rag-chat-input-area">
          <input type="text" class="rag-chat-input" id="rag-chat-input" placeholder="Type your message...">
          <button class="rag-chat-send" id="rag-chat-send">➤</button>
        </div>
      </div>
    </div>
  `;

  function init() {
    const style = document.createElement('style');
    style.textContent = styles;
    document.head.appendChild(style);

    const widget = document.createElement('div');
    widget.innerHTML = html;
    document.body.appendChild(widget);

    const toggle = document.getElementById('rag-chat-toggle');
    const close = document.getElementById('rag-chat-close');
    const window = document.getElementById('rag-chat-window');
    const input = document.getElementById('rag-chat-input');
    const send = document.getElementById('rag-chat-send');
    const messages = document.getElementById('rag-chat-messages');

    toggle.onclick = () => window.classList.toggle('open');
    close.onclick = () => window.classList.remove('open');
    send.onclick = sendMessage;
    input.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };

    function sendMessage() {
      const input = document.getElementById('rag-chat-input');
      const msg = input.value.trim();
      if (!msg) return;

      addMessage(msg, 'user');
      input.value = '';

      // Call the Proxy (3000) not the Backend (8000)
      fetch(`${config.apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: msg, 
          client_id: config.clientId 
        })
      })
      .then(r => r.json())
      .then(data => {
        console.log('API Response:', data);
        if (data.status === 'success') {
          console.log('Product Links:', data.product_links);
          addMessage(data.answer, 'bot', data.product_links);
        } else {
          addMessage('Error: ' + (data.message || 'Unknown error'), 'bot');
        }
      })
      .catch(err => {
        console.error('Fetch error:', err);
        addMessage('❌ Connection error', 'bot');
      });
    }

    function addMessage(text, sender, productLinks) {
      const el = document.createElement('div');
      el.className = `rag-chat-message ${sender}`;
      const contentHTML = `<div class="rag-chat-message-content">${formatMessage(text)}${productLinks && productLinks.length > 0 ? formatProductLinks(productLinks) : ''}</div>`;
      el.innerHTML = contentHTML;
      messages.appendChild(el);
      messages.scrollTop = messages.scrollHeight;
    }

    function formatMessage(text) {
      if (!text) return '';
      const normalized = String(text).replace(/\s+(?=\d+\.)/g, '\n');
      const lines = normalized.split(/\r?\n/);
      const htmlParts = [];
      let listBuffer = [];

      const flushList = () => {
        if (!listBuffer.length) return;
        htmlParts.push(`<ul class="rag-chat-bullets">${listBuffer.map(item => `<li>${item}</li>`).join('')}</ul>`);
        listBuffer = [];
      };

      lines.forEach((line) => {
        const match = line.match(/^\s*[\*\-•]\s+(.*)$/);
        if (match) {
          listBuffer.push(escapeHtml(match[1]));
          return;
        }
        flushList();
        const numbered = line.match(/^\s*(\d+)\.\s+(.*)$/);
        if (numbered) {
          htmlParts.push(`<div class="rag-chat-paragraph"><strong>${escapeHtml(numbered[1])}.</strong> ${linkify(escapeHtml(numbered[2]))}</div>`);
          return;
        }
        if (line.trim() === '') {
          htmlParts.push('<div class="rag-chat-paragraph rag-chat-paragraph--spacer"></div>');
        } else {
          htmlParts.push(`<div class="rag-chat-paragraph">${linkify(escapeHtml(line))}</div>`);
        }
      });

      flushList();
      return htmlParts.join('').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    }

    function linkify(text) {
      return text.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    }

    function formatProductLinks(links) {
      if (!links || links.length === 0) return '';
      
      const productItems = links.map((url, index) => {
        return `<div class="rag-chat-product-item"><strong>${index + 1}.</strong> <a href="${escapeHtml(url)}" class="rag-chat-product-link" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a></div>`;
      }).join('');

      return `<div class="rag-chat-products-section"><div class="rag-chat-products-header">🔗 Resources</div>${productItems}</div>`;
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})(window);
