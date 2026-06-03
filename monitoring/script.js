// 配置
const CONFIG = {
  // 本地状态数据文件（由 GitHub Actions 定时更新）
  statusDataUrl: './status.json',
  // 更新间隔（毫秒）
  updateInterval: 5 * 60 * 1000, // 5 分钟
};

// 状态映射
const STATUS_MAP = {
  0: { name: '暂停', icon: '⏸️', class: 'paused' },
  1: { name: '正常', icon: '✅', class: 'up' },
  2: { name: '异常', icon: '❌', class: 'down' },
  8: { name: '异常', icon: '❌', class: 'down' },
  9: { name: '异常', icon: '❌', class: 'down' },
};

// 获取状态数据
async function fetchStatus() {
  try {
    const response = await fetch(CONFIG.statusDataUrl);
    const data = await response.json();

    // 转换为显示器格式
    const monitors = data.monitors.map(monitor => ({
      name: monitor.friendly_name,
      status: monitor.status === 1 ? 'up' : monitor.status === 2 ? 'down' : 'paused',
      lastCheck: new Date(monitor.last_check * 1000).toISOString(),
    }));

    return monitors;
  } catch (error) {
    console.error('获取状态失败:', error);
    return [];
  }
}

// 更新当前状态显示
function updateCurrentStatus(monitors) {
  const container = document.getElementById('current-status');

  if (monitors.length === 0) {
    container.innerHTML = '<div class="status-card loading"><div class="status-icon">⚠️</div><div class="status-name">无法获取状态</div></div>';
    return;
  }

  container.innerHTML = monitors.map(monitor => {
    const statusInfo = STATUS_MAP[monitor.status] || STATUS_MAP[0];
    return `
      <div class="status-card ${statusInfo.class}">
        <div class="status-icon">${statusInfo.icon}</div>
        <div class="status-name">${monitor.name}</div>
        <div class="status-detail">${statusInfo.name}</div>
      </div>
    `;
  }).join('');
}

// 更新事件列表
function updateEvents(monitors) {
  const container = document.getElementById('events-list');

  if (monitors.length === 0) {
    container.innerHTML = '<div class="event-item loading">暂无事件数据</div>';
    return;
  }

  // 生成模拟事件（实际应从 API 获取）
  const events = monitors.map(monitor => {
    const statusInfo = STATUS_MAP[monitor.status] || STATUS_MAP[0];
    const time = new Date(monitor.lastCheck).toLocaleString('zh-CN');
    return `
      <div class="event-item">
        <div class="event-time">${time}</div>
        <div class="event-message">${monitor.name}: ${statusInfo.name}</div>
      </div>
    `;
  }).join('');

  container.innerHTML = events;
}

// 更新最后更新时间
function updateLastUpdate() {
  const element = document.getElementById('last-update');
  element.textContent = new Date().toLocaleString('zh-CN');
}

// 初始化
async function init() {
  const monitors = await fetchStatus();
  updateCurrentStatus(monitors);
  updateEvents(monitors);
  updateLastUpdate();

  // 定时更新
  setInterval(async () => {
    const monitors = await fetchStatus();
    updateCurrentStatus(monitors);
    updateEvents(monitors);
    updateLastUpdate();
  }, CONFIG.updateInterval);
}

// 启动
init();
