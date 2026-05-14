/**
 * RAG Chatbot Widget v1.0.0
 * Embeddable chat widget for RAG-powered chatbot
 */

(function(global) {
  'use strict';

  // Use the window object injected by the server
  const config = global.RAGChatBot || {
    apiUrl: 'http://localhost:3000',
    clientId: 'default'
  };

  const styles = `
    .rag-chat-widget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; position: fixed; bottom: 20px; right: 20px; z-index: 9999; }
    .rag-chat-bubble { width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #5B7CFF 0%, #6C5CE7 100%); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-size: 28px; }
    .rag-chat-bubble:hover { transform: scale(1.1); }
    .rag-chat-window { position: absolute; bottom: 80px; right: 0; width: 380px; height: 600px; background: white; border-radius: 12px; display: none; flex-direction: column; box-shadow: 0 5px 40px rgba(0,0,0,0.16); animation: slideUp 0.3s ease; }
    .rag-chat-window.open { display: flex; }
    .rag-chat-header { background: linear-gradient(135deg, #5B7CFF 0%, #6C5CE7 100%); color: white; padding: 20px; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .rag-chat-header h3 { margin: 0; font-size: 16px; }
    .rag-chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; background: #f5f5f5; }
    .rag-chat-message { display: flex; gap: 10px; margin-bottom: 10px; }
    .rag-chat-message.user { justify-content: flex-end; }
    .rag-chat-message-content { max-width: 80%; padding: 10px 15px; border-radius: 12px; word-wrap: break-word; line-height: 1.5; font-size: 14px; }
    .rag-chat-message-content strong { font-weight: 700; }
    .rag-chat-message-content .rag-chat-paragraph { margin: 0 0 6px 0; }
    .rag-chat-message-content .rag-chat-paragraph:last-child { margin-bottom: 0; }
    .rag-chat-message-content .rag-chat-paragraph--spacer { height: 8px; }
    .rag-chat-message-content .rag-chat-bullets { margin: 6px 0; padding-left: 18px; }
    .rag-chat-message-content .rag-chat-bullets li { margin: 4px 0; }
    .rag-chat-message-content a { color: #5B7CFF; text-decoration: underline; word-break: break-all; }
    .rag-chat-message-content a:hover { color: #4A90E2; }
    .rag-chat-message.user .rag-chat-message-content { background: linear-gradient(135deg, #5B7CFF 0%, #6C5CE7 100%); color: white; }
    .rag-chat-message.bot .rag-chat-message-content { background: white; color: #333; border: 1px solid #e0e0e0; }
    .rag-chat-products-section { background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px 12px; margin-top: 12px; }
    .rag-chat-products-header { font-weight: 700; color: #5B7CFF; margin-bottom: 10px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .rag-chat-product-item { margin-bottom: 8px; font-size: 12px; line-height: 1.5; }
    .rag-chat-product-item:last-child { margin-bottom: 0; }
    .rag-chat-product-link { color: #5B7CFF; text-decoration: none; word-break: break-all; transition: color 0.2s; }
    .rag-chat-product-link:hover { color: #6C5CE7; text-decoration: underline; }
    .rag-chat-input-area { padding: 15px; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; }
    .rag-chat-input { flex: 1; border: 1px solid #e0e0e0; border-radius: 24px; padding: 10px 16px; font-size: 14px; outline: none; }
    .rag-chat-input:focus { border-color: #5B7CFF; }
    .rag-chat-send { background: linear-gradient(135deg, #5B7CFF 0%, #6C5CE7 100%); border: none; color: white; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px; transition: 0.2s; }
    .rag-chat-send:hover { transform: scale(1.05); }
    .rag-chat-send:disabled { opacity: 0.6; cursor: not-allowed; }
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
  `;

  const html = `
    <div class="rag-chat-widget">
      <div class="rag-chat-bubble" id="rag-chat-toggle">💬</div>
      <div class="rag-chat-window" id="rag-chat-window">
        <div class="rag-chat-header">
          <h3>SettleUp Assistant</h3>
          <button id="rag-chat-close" style="background: rgba(255,255,255,0.2); border: none; color: white; cursor: pointer; padding: 5px 8px; border-radius: 4px; font-size: 20px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;">&times;</button>
        </div>
        <div class="rag-chat-messages" id="rag-chat-messages">
          <div class="rag-chat-message bot">
            <div class="rag-chat-message-content">👋 Hi! Welcome to SettleUp. Let me help you find your ideal rental property!</div>
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

      return `<div class="rag-chat-products-section"><div class="rag-chat-products-header">🔗 Product Links</div>${productItems}</div>`;
    }

    function extractProductName(url) {
      try {
        // Extract product slug from URL (e.g., /products/aspor-a337-30000-mah-22-5w-power-bank)
        let slug = '';
        
        // Try different URL patterns
        const patterns = [
          /\/products\/([^/?#]+)/,  // /products/name
          /\/items\/([^/?#]+)/,      // /items/name
          /\/product\/([^/?#]+)/,    // /product/name
          /\/items?=([^/?#&]+)/,     // ?item=name
        ];
        
        for (let pattern of patterns) {
          const match = url.match(pattern);
          if (match && match[1]) {
            slug = match[1];
            break;
          }
        }
        
        if (slug) {
          // Convert slug to readable name: replace hyphens with spaces, title case
          return slug
            .split('-')
            .map(word => {
              // Handle numbers specially (don't capitalize mid-word numbers)
              if (/^\d+$/.test(word)) return word;
              return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
            })
            .join(' ');
        }
      } catch (e) {
        // Fallback if regex fails
      }
      // Fallback: use the domain or a generic label
      try {
        const domain = new URL(url).hostname;
        return `Product from ${domain}`;
      } catch (e) {
        return 'View Product';
      }
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
