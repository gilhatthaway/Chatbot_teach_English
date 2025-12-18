/**
 * API Service - Kết nối với Backend Python Flask
 * Import config từ config.js để thay đổi BASE_URL
 */

import { CONFIG, logDebug } from './config';

// ⚠️ QUAN TRỌNG: Thay đổi IP trong config.js
const BASE_URL = CONFIG.BASE_URL;

/**
 * CHAT API - Gửi tin nhắn tới AI
 * @param {number} id_nguoi_dung - ID người dùng
 * @param {string} message - Tin nhắn từ người dùng
 * @returns {Promise} - Phản hồi từ API
 */
export const sendChatMessage = async (id_nguoi_dung, message) => {
  try {
    logDebug('sendChatMessage', { id_nguoi_dung, message });
    
    const response = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id_nguoi_dung: id_nguoi_dung,
        message: message,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    logDebug('sendChatMessage response', data);
    return data;
  } catch (error) {
    console.error('❌ Lỗi khi gửi chat:', error);
    throw error;
  }
};

/**
 * LOGIN API - Đăng nhập người dùng
 * @param {string} email - Email người dùng
 * @param {string} mat_khau - Mật khẩu
 * @returns {Promise} - Thông tin người dùng
 */
export const loginUser = async (email, mat_khau) => {
  try {
    const response = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        mat_khau: mat_khau,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('❌ Lỗi khi đăng nhập:', error);
    throw error;
  }
};

/**
 * REGISTER API - Đăng ký tài khoản mới
 * @param {string} ten_dang_nhap - Tên đăng nhập
 * @param {string} email - Email
 * @param {string} mat_khau - Mật khẩu
 * @returns {Promise}
 */
export const registerUser = async (ten_dang_nhap, email, mat_khau) => {
  try {
    const response = await fetch(`${BASE_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ten_dang_nhap: ten_dang_nhap,
        email: email,
        mat_khau: mat_khau,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('❌ Lỗi khi đăng ký:', error);
    throw error;
  }
};

/**
 * GET CHAT HISTORY - Lấy lịch sử chat
 * @param {number} id_nguoi_dung - ID người dùng
 * @param {number} limit - Số tin nhắn lấy (mặc định 5)
 * @returns {Promise} - Danh sách lịch sử chat
 */
export const getChatHistory = async (id_nguoi_dung, limit = 5) => {
  try {
    const response = await fetch(
      `${BASE_URL}/chat/history/${id_nguoi_dung}?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('❌ Lỗi khi lấy lịch sử chat:', error);
    throw error;
  }
};

/**
 * GENERATE LESSON - Tạo bài học từ AI
 * @param {number} id_nguoi_dung - ID người dùng
 * @param {string} topic - Chủ đề bài học
 * @returns {Promise}
 */
export const generateLesson = async (id_nguoi_dung, topic) => {
  try {
    const response = await fetch(
      `${BASE_URL}/generate/lesson/${encodeURIComponent(topic)}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id_nguoi_dung: id_nguoi_dung,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('❌ Lỗi khi tạo bài học:', error);
    throw error;
  }
};

export default {
  sendChatMessage,
  loginUser,
  registerUser,
  getChatHistory,
  generateLesson,
};
