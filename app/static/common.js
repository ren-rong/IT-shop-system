// 公共辅助：token 管理 + 统一 fetch（自动携带鉴权头）
const TOKEN_KEY = 'ecommerce_token';
const USER_KEY = 'ecommerce_user';

function getToken() { return localStorage.getItem(TOKEN_KEY); }
function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function setUser(u) { localStorage.setItem(USER_KEY, u); }
function getUser() { return localStorage.getItem(USER_KEY); }

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  location.href = 'login.html';
}

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = 'Bearer ' + token;
  options.headers = Object.assign(headers, options.headers || {});
  const resp = await fetch(path, options);
  let data = null;
  try { data = await resp.json(); } catch (e) { data = null; }
  if (resp.status === 401) {
    logout();
    throw new Error('未登录或登录已过期');
  }
  return { httpStatus: resp.status, body: data };
}

// 通用导航栏
function navBar(active) {
  const items = [
    ['goods.html', '商品管理'],
    ['orders.html', '订单管理'],
    ['users.html', '用户管理']
  ];
  const links = items.map(i =>
    `<a href="${i[0]}" class="${active === i[0] ? 'active' : ''}">${i[1]}</a>`
  ).join('');
  return `<div class="nav">
    <span class="logo">电商后台</span>
    <div class="nav-links">${links}</div>
    <span class="welcome">欢迎，${getUser() || ''}</span>
    <button id="logout-btn" class="btn-sm" onclick="logout()">退出登录</button>
  </div>`;
}

function requireLogin() {
  if (!getToken()) { location.href = 'login.html'; }
}
