// API 配置
// 根据环境动态选择 API URL
// 如果是外网访问，直接用外网地址；本地开发用代理
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'

export const API_BASE_URL = isLocalhost ? '' : `${window.location.protocol}//${window.location.hostname}:8000`
export const WS_BASE_URL = isLocalhost ? `ws://${window.location.host}` : `ws://${window.location.hostname}:8000`
