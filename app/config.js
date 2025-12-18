/**
 * Config - Tệp cấu hình toàn cục cho ứng dụng
 * Thay đổi giá trị ở đây để cập nhật cài đặt
 */

// ⚠️ QUAN TRỌNG: Cập nhật IP này theo máy chạy backend
// 
// Cách tìm IP:
// 1. Trên backend, chạy: ipconfig (Windows) hoặc ifconfig (Mac/Linux)
// 2. Tìm IPv4 Address (ví dụ: 192.168.1.100)
// 3. Đặt vào BASE_URL dưới đây

export const CONFIG = {
  // ✅ URL của backend Flask
  // - Localhost: 'http://localhost:5000'
  // - Network: 'http://192.168.1.14:5000' (thay IP thành của bạn)
  BASE_URL: 'http://192.168.1.14:5000',
  
  // ⏱️ Timeout cho API calls (millisecond)
  API_TIMEOUT: 10000,
  
  // 🔍 Debug mode (hiển thị log chi tiết)
  DEBUG: true,
  
  // 📊 Số tin nhắn lịch sử mặc định
  DEFAULT_HISTORY_LIMIT: 5,
};

/**
 * Log function - Với DEBUG mode
 * @param {string} tag - Tên tag
 * @param {any} data - Dữ liệu cần log
 */
export const logDebug = (tag, data) => {
  if (CONFIG.DEBUG) {
    console.log(`[${tag}]`, data);
  }
};

export default CONFIG;
