// Dashboard interactivity for product, interval, and Telegram settings management

// Utility: fetch JSON
async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// Product management
async function loadProducts() {
  const products = await fetchJSON('/api/products');
  return products; // Just return the data, don't render
}

async function refreshProducts() {
  // This function both loads and renders products
  await renderProducts();
}

async function addProduct(product) {
  await fetchJSON('/api/products', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(product)
  });
  await refreshProducts();
}

async function updateProduct(idx, product) {
  await fetchJSON(`/api/products/${idx}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(product)
  });
  await refreshProducts();
}

async function deleteProduct(idx) {
  await fetchJSON(`/api/products/${idx}`, { method: 'DELETE' });
  await refreshProducts();
}

// Interval management
async function loadInterval() {
  const data = await fetchJSON('/api/interval');
  // TODO: Render interval in the DOM
}

async function updateInterval(interval) {
  await fetchJSON('/api/interval', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ interval })
  });
  await loadInterval();
}

// Telegram settings
async function loadTelegram() {
  const data = await fetchJSON('/api/telegram');
  // TODO: Render Telegram settings in the DOM
}

async function updateTelegram(token, chat_id) {
  await fetchJSON('/api/telegram', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, chat_id })
  });
  await loadTelegram();
}

// Notification settings
async function loadNotifications() {
  const data = await fetchJSON('/api/notifications');
  return data;
}

async function updateNotifications(mode) {
  await fetchJSON('/api/notifications', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notification_mode: mode })
  });
  await loadNotifications();
}

document.addEventListener('DOMContentLoaded', () => {
  // Tab switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  tabBtns.forEach(btn => {
    btn.onclick = () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(tc => tc.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    };
  });

  // Elements
  const productList = document.getElementById('product-list');
  const addProductForm = document.getElementById('add-product-form');
  const intervalForm = document.getElementById('interval-form');
  const intervalInput = document.getElementById('interval-input');
  const intervalCurrent = document.getElementById('interval-current');
  const telegramForm = document.getElementById('telegram-form');
  const telegramToken = document.getElementById('telegram-token');
  const telegramChatId = document.getElementById('telegram-chat-id');
  const telegramCurrent = document.getElementById('telegram-current');
  const notificationsForm = document.getElementById('notifications-form');
  const notificationsCurrent = document.getElementById('notifications-current');
  const productTemplate = document.getElementById('product-item-template');
  const watcherStatus = document.getElementById('watcher-status');
  const startWatcherBtn = document.getElementById('start-watcher-btn');
  const stopWatcherBtn = document.getElementById('stop-watcher-btn');
  const mainWatcherStatus = document.getElementById('main-watcher-status');

  let editingIdx = null;

  // Show loading state
  function showLoading(element, message = 'Loading...') {
    element.innerHTML = `<div class="loading" style="text-align:center;padding:2rem;">${message}</div>`;
  }

  // Show error state
  function showError(element, message) {
    element.innerHTML = `<div class="error" style="text-align:center;padding:2rem;">⚠ ${message}</div>`;
  }

  // Show success notification
  function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 1rem 1.5rem;
      background: ${type === 'success' ? 'linear-gradient(135deg, #22c55e, #16a34a)' : 'linear-gradient(135deg, #ef4444, #dc2626)'};
      color: white;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      z-index: 1000;
      animation: slideIn 0.3s ease;
      font-weight: 500;
    `;
    document.body.appendChild(notification);
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease forwards';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  // Format countdown seconds into readable time
  function formatCountdown(seconds) {
    if (seconds <= 0) return 'now';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  // Add CSS animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
  `;
  document.head.appendChild(style);

  // Render products with live prices
  async function renderProducts() {
    showLoading(productList, 'Loading products...');
    
    try {
      const products = await fetchJSON('/api/products');
      productList.innerHTML = '';
      
      if (!products.length) {
        productList.innerHTML = '<div style="text-align:center;padding:3rem;color:#a0aec0;"><h3>No products being watched</h3><p>Add your first product below to get started!</p></div>';
        return;
      }
      
      // Process products sequentially to avoid race conditions
      for (let idx = 0; idx < products.length; idx++) {
        const product = products[idx];
        const node = productTemplate.content.cloneNode(true);
        const li = node.querySelector('li');
        li.querySelector('.product-name').textContent = product.name || 'Unnamed Product';
        li.querySelector('.product-target').textContent = `Target: €${product.target_price.toLocaleString()}`;
        
        // Set product link
        const link = li.querySelector('.product-link');
        link.href = product.url;
        link.textContent = 'View Listing';
        
        // Add the product to DOM immediately so it's visible
        productList.appendChild(node);
        
        // Setup edit/delete handlers
        li.querySelector('.edit-btn').onclick = () => {
          addProductForm.url.value = product.url;
          addProductForm.target_price.value = product.target_price;
          addProductForm.name.value = product.name || '';
          editingIdx = idx;
          const submitBtn = addProductForm.querySelector('.add-btn');
          const btnText = submitBtn.querySelector('.btn-text');
          const btnIcon = submitBtn.querySelector('.btn-icon');
          btnText.textContent = 'Save Changes';
          btnIcon.textContent = '✓';
          submitBtn.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
          
          // Scroll to form
          addProductForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
          addProductForm.url.focus();
        };
        
        // Delete with confirmation
        li.querySelector('.delete-btn').onclick = async () => {
          const productName = product.name || 'this product';
          if (confirm(`Are you sure you want to remove "${productName}"?\n\nThis action cannot be undone.`)) {
            try {
              await deleteProduct(idx);
              showNotification(`Removed ${productName}`);
            } catch (error) {
              showNotification('Failed to remove product', 'error');
            }
          }
        };
        
        // Fetch live price asynchronously (doesn't block product display)
        const lastSpan = li.querySelector('.product-last');
        lastSpan.innerHTML = '<span class="loading">⏳ Checking price...</span>';
        
        // Use setTimeout to make price fetching non-blocking
        setTimeout(async () => {
          try {
            const res = await fetchJSON('/api/price', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ url: product.url })
            });
            
            if (res.error) {
              // Check if watcher is running to provide better error message
              try {
                const watcherStatus = await fetchJSON('/api/watcher/status');
                if (!watcherStatus.is_running) {
                  lastSpan.innerHTML = '<span class="error">⏸ Watcher turned off</span>';
                } else {
                  lastSpan.innerHTML = '<span class="error">✗ Unable to fetch</span>';
                }
              } catch {
                lastSpan.innerHTML = '<span class="error">✗ Unable to fetch</span>';
              }
            } else {
              const currentPrice = res.price;
              const isBelowTarget = currentPrice < product.target_price;  // Changed from <= to <
              
              lastSpan.innerHTML = `
                <span class="price-indicator ${isBelowTarget ? 'below-target' : 'above-target'}">
                  €${currentPrice.toLocaleString()}
                </span>
              `;
              
              // Add visual indicator to card
              if (isBelowTarget) {
                li.classList.add('price-alert');
                showNotification(`${product.name || 'Product'} dropped below target price: €${currentPrice}!`);
              }
            }
          } catch (error) {
            // Check if it's a connection issue or watcher is off
            try {
              const watcherStatus = await fetchJSON('/api/watcher/status');
              if (!watcherStatus.is_running) {
                lastSpan.innerHTML = '<span class="error">⏸ Watcher turned off</span>';
              } else {
                lastSpan.innerHTML = '<span class="error">✗ Connection failed</span>';
              }
            } catch {
              lastSpan.innerHTML = '<span class="error">✗ Connection failed</span>';
            }
          }
        }, idx * 1000); // Stagger price checks to avoid overwhelming FlareSolverr
      }
    } catch (error) {
      showError(productList, 'Failed to load products. Please refresh the page.');
    }
  }

  // Add or edit product with better feedback
  addProductForm.onsubmit = async e => {
    e.preventDefault();
    const submitBtn = addProductForm.querySelector('.add-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnIcon = submitBtn.querySelector('.btn-icon');
    const originalText = btnText.textContent;
    const originalIcon = btnIcon.textContent;
    
    // Basic validation
    const url = addProductForm.url.value.trim();
    const targetPrice = parseFloat(addProductForm.target_price.value);
    const name = addProductForm.name.value.trim();
    
    if (!url || !targetPrice || targetPrice <= 0) {
      showNotification('Please fill in all required fields with valid values', 'error');
      return;
    }
    
    if (!url.includes('vaurioajoneuvo.fi')) {
      if (!confirm('This URL doesn\'t appear to be from vaurioajoneuvo.fi. Continue anyway?')) {
        return;
      }
    }
    
    // Show loading state
    btnText.textContent = 'Saving...';
    btnIcon.textContent = '...';
    submitBtn.disabled = true;
    
    try {
      const product = { url, target_price: targetPrice, name };
      
      if (editingIdx !== null) {
        await updateProduct(editingIdx, product);
        showNotification(`Updated ${name || 'product'} successfully!`);
        editingIdx = null;
        btnText.textContent = 'Add Product';
        btnIcon.textContent = '+';
        submitBtn.style.background = 'linear-gradient(135deg, #2563eb, #3b82f6)';
      } else {
        await addProduct(product);
        showNotification(`Added ${name || 'new product'} to watchlist!`);
      }
      
      addProductForm.reset();
    } catch (error) {
      showNotification('Failed to save product. Please try again.', 'error');
    } finally {
      submitBtn.disabled = false;
      if (editingIdx === null) {
        btnText.textContent = originalText;
        btnIcon.textContent = originalIcon;
      }
    }
  };

  // Interval management with validation
  async function renderInterval() {
    try {
      const data = await fetchJSON('/api/interval');
      intervalCurrent.innerHTML = `<strong>Current interval:</strong> ${data.interval || '60 seconds (default)'}`;
      intervalInput.value = data.interval || '60';
    } catch (error) {
      intervalCurrent.innerHTML = '<span class="error">Failed to load interval setting</span>';
    }
  }
  
  intervalForm.onsubmit = async e => {
    e.preventDefault();
    const submitBtn = intervalForm.querySelector('button[type="submit"]');
    const interval = intervalInput.value.trim();
    
    // Basic validation
    if (!interval) {
      showNotification('Please enter an interval', 'error');
      return;
    }
    
    submitBtn.textContent = '⏳ Updating...';
    submitBtn.disabled = true;
    
    try {
      await updateInterval(interval);
      await renderInterval();
      // Reconfigure auto-refresh with new interval
      await setupAutoRefresh();
      showNotification('Interval updated successfully!');
    } catch (error) {
      showNotification('Failed to update interval', 'error');
    } finally {
      submitBtn.textContent = 'Update Interval';
      submitBtn.disabled = false;
    }
  };

  // Telegram settings with better feedback
  async function renderTelegram() {
    try {
      const data = await fetchJSON('/api/telegram');
      const tokenStatus = data.telegram_token ? '✓ Set' : '✗ Not set';
      const chatIdStatus = data.telegram_chat_id ? `✓ ${data.telegram_chat_id}` : '✗ Not set';
      
      telegramCurrent.innerHTML = `
        <div><strong>Bot Token:</strong> ${tokenStatus}</div>
        <div><strong>Chat ID:</strong> ${chatIdStatus}</div>
        ${!data.telegram_token || !data.telegram_chat_id ? '<div class="error">⚠ Telegram notifications are disabled</div>' : '<div class="success">✓ Telegram notifications are enabled</div>'}
      `;
      
      // Hide credentials in input fields for security
      telegramToken.value = data.telegram_token ? '••••••••••••••••' : '';
      telegramChatId.value = data.telegram_chat_id ? '••••••••••••••••' : '';
      
      // Store actual values for comparison when updating
      telegramToken.dataset.actualValue = data.telegram_token || '';
      telegramChatId.dataset.actualValue = data.telegram_chat_id || '';
    } catch (error) {
      telegramCurrent.innerHTML = '<span class="error">Failed to load Telegram settings</span>';
    }
  }

  // Notification settings with better feedback
  async function renderNotifications() {
    try {
      const data = await fetchJSON('/api/notifications');
      const modeDescriptions = {
        'below_target': 'Only when price drops below target',
        'any_change': 'On any price change (up or down)',
        'both': 'Both price changes and below target alerts',
        'none': 'Never (monitoring only, no notifications)'
      };
      
      const currentMode = data.notification_mode || 'below_target';
      const description = modeDescriptions[currentMode] || 'Unknown mode';
      
      console.log('Notification data received:', data); // Debug log
      console.log('Current mode:', currentMode); // Debug log
      
      notificationsCurrent.innerHTML = `
        <div><strong>Current mode:</strong> ${description}</div>
        <div class="mode-info" style="margin-top: 0.5rem; font-size: 0.9rem; color: #6b7280;">
          ${currentMode === 'any_change' ? 'You\'ll get notified of all price movements' : ''}
          ${currentMode === 'below_target' ? 'You\'ll only get target price alerts' : ''}
          ${currentMode === 'both' ? 'You\'ll get all price changes AND target alerts' : ''}
          ${currentMode === 'none' ? 'No notifications (monitoring only)' : ''}
        </div>
      `;
      
      document.getElementById('notification-mode').value = currentMode;
    } catch (error) {
      console.error('Failed to load notification settings:', error); // Debug log
      notificationsCurrent.innerHTML = '<span class="error">Failed to load notification settings</span>';
    }
  }

  // Watcher control functions
  async function renderWatcherStatus() {
    try {
      const data = await fetchJSON('/api/watcher/status');
      const isRunning = data.is_running;
      
      // Update main status indicator
      if (mainWatcherStatus) {
        const statusDot = mainWatcherStatus.querySelector('.status-dot');
        const statusText = mainWatcherStatus.querySelector('.status-text');
        
        if (isRunning) {
          statusDot.className = 'status-dot running';
          
          // Show countdown if available
          if (data.countdown !== undefined) {
            const countdown = formatCountdown(data.countdown);
            statusText.textContent = `Active (${countdown})`;
          } else {
            statusText.textContent = 'Watcher Active';
          }
        } else {
          statusDot.className = 'status-dot stopped';
          statusText.textContent = 'Watcher Stopped';
        }
      }
      
      // Update settings page status
      if (watcherStatus) {
        let statusHTML = `
          <div><strong>Status:</strong> ${isRunning ? '<span class="success">Running</span>' : '<span class="error">Stopped</span>'}</div>
        `;
        
        if (isRunning && data.countdown !== undefined) {
          const countdown = formatCountdown(data.countdown);
          const intervalText = data.interval ? `${data.interval}s` : 'unknown';
          statusHTML += `
            <div style="margin-top: 0.5rem;"><strong>Next check in:</strong> <span class="countdown">${countdown}</span></div>
            <div style="margin-top: 0.25rem; font-size: 0.85rem; color: #6b7280;">Interval: ${intervalText}</div>
          `;
        }
        
        statusHTML += `
          <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #6b7280;">
            ${isRunning ? 'The watcher is actively monitoring your products and will send Telegram notifications when target prices are reached.' : 'The watcher is stopped. Products are not being monitored for price changes.'}
          </div>
        `;
        
        watcherStatus.innerHTML = statusHTML;
        
        if (startWatcherBtn) startWatcherBtn.disabled = isRunning;
        if (stopWatcherBtn) stopWatcherBtn.disabled = !isRunning;
      }
    } catch (error) {
      if (mainWatcherStatus) {
        mainWatcherStatus.querySelector('.status-text').textContent = 'Status Unknown';
      }
      if (watcherStatus) {
        watcherStatus.innerHTML = '<span class="error">Failed to load watcher status</span>';
      }
    }
  }

  async function startWatcher() {
    const originalText = startWatcherBtn.textContent;
    startWatcherBtn.textContent = '⏳ Starting...';
    startWatcherBtn.disabled = true;
    
    try {
      await fetchJSON('/api/watcher/start', { method: 'POST' });
      showNotification('Watcher started successfully!');
      await renderWatcherStatus();
    } catch (error) {
      showNotification('Failed to start watcher', 'error');
    } finally {
      startWatcherBtn.textContent = originalText;
      startWatcherBtn.disabled = false;
    }
  }

  async function stopWatcher() {
    const originalText = stopWatcherBtn.textContent;
    stopWatcherBtn.textContent = '⏳ Stopping...';
    stopWatcherBtn.disabled = true;
    
    try {
      await fetchJSON('/api/watcher/stop', { method: 'POST' });
      showNotification('Watcher stopped successfully!');
      await renderWatcherStatus();
    } catch (error) {
      showNotification('Failed to stop watcher', 'error');
    } finally {
      stopWatcherBtn.textContent = originalText;
      stopWatcherBtn.disabled = false;
    }
  }

  // Event listeners for watcher control
  startWatcherBtn.onclick = startWatcher;
  stopWatcherBtn.onclick = stopWatcher;
  
  telegramForm.onsubmit = async e => {
    e.preventDefault();
    const submitBtn = telegramForm.querySelector('button[type="submit"]');
    
    // Use actual values if fields haven't been changed, otherwise use new values
    const token = telegramToken.value === '••••••••••••••••' ? 
      telegramToken.dataset.actualValue : telegramToken.value.trim();
    const chatId = telegramChatId.value === '••••••••••••••••' ? 
      telegramChatId.dataset.actualValue : telegramChatId.value.trim();
    
    submitBtn.textContent = '⏳ Updating...';
    submitBtn.disabled = true;
    
    try {
      await updateTelegram(token, chatId);
      await renderTelegram();
      showNotification('Telegram settings updated!');
    } catch (error) {
      showNotification('Failed to update Telegram settings', 'error');
    } finally {
      submitBtn.textContent = 'Update Telegram';
      submitBtn.disabled = false;
    }
  };

  // Clear masked values when user starts typing
  telegramToken.addEventListener('focus', function() {
    if (this.value === '••••••••••••••••') {
      this.value = '';
    }
  });

  telegramChatId.addEventListener('focus', function() {
    if (this.value === '••••••••••••••••') {
      this.value = '';
    }
  });

  notificationsForm.onsubmit = async e => {
    e.preventDefault();
    const submitBtn = notificationsForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Updating...';
    
    try {
      const mode = document.getElementById('notification-mode').value;
      await updateNotifications(mode);
      await renderNotifications();
      showNotification('Notification settings updated!');
    } catch (error) {
      showNotification('Failed to update notification settings', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Update Notifications';
    }
  };

  // Add keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to submit forms
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const activeForm = document.activeElement.closest('form');
      if (activeForm) {
        activeForm.dispatchEvent(new Event('submit'));
      }
    }
    
    // Escape to cancel editing
    if (e.key === 'Escape' && editingIdx !== null) {
      editingIdx = null;
      const submitBtn = addProductForm.querySelector('.add-btn');
      const btnText = submitBtn.querySelector('.btn-text');
      const btnIcon = submitBtn.querySelector('.btn-icon');
      btnText.textContent = 'Add Product';
      btnIcon.textContent = '+';
      submitBtn.style.background = 'linear-gradient(135deg, #2563eb, #3b82f6)';
      addProductForm.reset();
    }
  });
  
  // Function to parse interval string into milliseconds
  function parseIntervalToMs(intervalStr) {
    try {
      const s = String(intervalStr).trim().toLowerCase();
      
      // Handle random intervals like "random:60-300" - use average
      if (s.startsWith('random:')) {
        const rangePart = s.substring(7);
        if (rangePart.includes('-')) {
          const [min, max] = rangePart.split('-').map(x => parseInt(x.trim()));
          const avgSeconds = Math.floor((min + max) / 2);
          return avgSeconds * 1000;
        } else {
          // Single value after random: - use average of 60 and that value
          const maxSeconds = parseInt(rangePart.trim());
          const avgSeconds = Math.floor((60 + maxSeconds) / 2);
          return avgSeconds * 1000;
        }
      }
      
      // Handle minute notation
      if (s.endsWith('m') || s.endsWith('min')) {
        const minutes = parseInt(s.replace(/m(in)?$/, ''));
        return minutes * 60 * 1000;
      }
      
      // Handle plain seconds
      const seconds = parseInt(s);
      return seconds * 1000;
      
    } catch (error) {
      console.warn('[Auto-refresh] Failed to parse interval, using 60s default:', error);
      return 60 * 1000; // Default to 60 seconds
    }
  }

  // Setup dynamic auto-refresh based on watcher interval
  let autoRefreshInterval = null;
  let autoRefreshCountdown = null;
  let nextAutoRefreshTime = null;
  
  async function setupAutoRefresh() {
    try {
      const intervalData = await fetchJSON('/api/interval');
      const intervalStr = intervalData.interval || '60';
      const refreshMs = parseIntervalToMs(intervalStr);
      
      console.log(`[Auto-refresh] Setting up refresh every ${refreshMs/1000}s (from interval: ${intervalStr})`);
      
      // Clear existing intervals if any
      if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
      }
      if (autoRefreshCountdown) {
        clearInterval(autoRefreshCountdown);
      }
      
      // Set next refresh time
      nextAutoRefreshTime = Date.now() + refreshMs;
      console.log(`[Auto-refresh] Next refresh at: ${new Date(nextAutoRefreshTime).toLocaleTimeString()}`);
      
      // Set new auto-refresh interval
      autoRefreshInterval = setInterval(() => {
        if (document.visibilityState === 'visible') {
          console.log('[Auto-refresh] Refreshing products...');
          refreshProducts();
          nextAutoRefreshTime = Date.now() + refreshMs; // Reset countdown
        }
      }, refreshMs);
      
      // Update auto-refresh countdown every second
      autoRefreshCountdown = setInterval(() => {
        updateAutoRefreshCountdown();
      }, 1000);
      
      // Initialize countdown display immediately
      updateAutoRefreshCountdown();
      
    } catch (error) {
      console.warn('[Auto-refresh] Failed to get interval, using 60s default:', error);
      // Fallback to 60 second refresh
      const fallbackMs = 60 * 1000;
      nextAutoRefreshTime = Date.now() + fallbackMs;
      
      autoRefreshInterval = setInterval(() => {
        if (document.visibilityState === 'visible') {
          console.log('[Auto-refresh] Refreshing products (fallback)...');
          refreshProducts();
          nextAutoRefreshTime = Date.now() + fallbackMs;
        }
      }, fallbackMs);
      
      autoRefreshCountdown = setInterval(() => {
        updateAutoRefreshCountdown();
      }, 1000);
      
      // Initialize countdown display immediately
      updateAutoRefreshCountdown();
    }
  }
  
  function updateAutoRefreshCountdown() {
    if (!nextAutoRefreshTime) {
      console.debug('[Auto-refresh] No next refresh time set');
      return;
    }
    
    const remaining = Math.max(0, Math.floor((nextAutoRefreshTime - Date.now()) / 1000));
    const autoRefreshElement = document.getElementById('auto-refresh-countdown');
    
    if (!autoRefreshElement) {
      console.warn('[Auto-refresh] Countdown element not found');
      return;
    }
    
    if (remaining > 0) {
      autoRefreshElement.textContent = `Auto-refresh in: ${formatCountdown(remaining)}`;
      autoRefreshElement.style.display = 'flex';
    } else {
      autoRefreshElement.textContent = 'Refreshing now...';
      autoRefreshElement.style.display = 'flex';
    }
  }
  
  // Initial load with staggered timing for better UX
  renderProducts();
  setTimeout(renderInterval, 100);
  setTimeout(renderTelegram, 200);
  setTimeout(renderNotifications, 250);
  setTimeout(renderWatcherStatus, 300);
  
  // Setup auto-refresh after initial load
  setTimeout(setupAutoRefresh, 500);
  
  // Auto-refresh watcher status every 5 seconds for countdown updates
  setInterval(() => {
    if (document.visibilityState === 'visible') {
      renderWatcherStatus();
    }
  }, 5 * 1000);
}); 