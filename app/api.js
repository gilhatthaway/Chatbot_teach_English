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
/**
 * GET CHAT HISTORY - Lấy lịch sử chat
 * @param {number} id_nguoi_dung - ID người dùng
 * @param {number} limit - Số tin nhắn lấy (mặc định 5)
 * @returns {Promise} - Danh sách lịch sử chat
 */
export const getChatHistory = async (id_nguoi_dung, limit = 5) => {
  try {
    const response = await fetch(
      `${BASE_URL}/api/user/ai_chat_history/${id_nguoi_dung}?limit=${limit}`,
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
    return data.history || [];
  } catch (error) {
    console.error('❌ Lỗi khi lấy lịch sử chat:', error);
    throw error;
  }
};

/**
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

/**
 * GET EXAMS LIST API - Lấy danh sách bài kiểm tra
 * @returns {Promise} - Danh sách bài kiểm tra
 */
export const getExamsList = async () => {
  try {
    logDebug('getExamsList', {});
    
    const response = await fetch(`${BASE_URL}/api/exams`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    logDebug('getExamsList response', data);
    return data?.exams || data || [];
  } catch (error) {
    console.error('❌ Lỗi khi lấy danh sách bài kiểm tra:', error);
    throw error;
  }
};

/**
 * GET EXAM DETAIL API - Lấy chi tiết bài kiểm tra
 * @param {number} id_kt - ID bài kiểm tra
 * @returns {Promise} - Chi tiết bài kiểm tra kèm câu hỏi
 */
export const getExamDetail = async (id_kt) => {
  try {
    logDebug('getExamDetail', { id_kt });
    
    const response = await fetch(`${BASE_URL}/exams/${id_kt}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    logDebug('getExamDetail response', data);
    return data?.exam || data;
  } catch (error) {
    console.error('❌ Lỗi khi lấy chi tiết bài kiểm tra:', error);
    throw error;
  }
};

/**
 * SUBMIT EXAM API - Nộp bài kiểm tra
 * @param {number} id_nguoi_dung - ID người dùng
 * @param {number} id_kt - ID bài kiểm tra
 * @param {array} bai_lam - Danh sách câu trả lời
 * @returns {Promise} - Kết quả chấm điểm
 */
export const submitExam = async (id_nguoi_dung, id_kt, bai_lam) => {
  try {
    logDebug('submitExam', { id_nguoi_dung, id_kt });
    
    const response = await fetch(`${BASE_URL}/exam/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id_nguoi_dung: id_nguoi_dung,
        id_kt: id_kt,
        bai_lam: bai_lam,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    logDebug('submitExam response', data);
    return data;
  } catch (error) {
    console.error('❌ Lỗi khi nộp bài kiểm tra:', error);
    throw error;
  }
};

/**
 * GET EXAM HISTORY API - Lấy lịch sử làm bài kiểm tra của user
 * @param {number} id_nguoi_dung - ID người dùng
 * @param {number} limit - Số lượng bài cần lấy (mặc định 10)
 * @returns {Promise} - Danh sách lịch sử làm bài
 */
export const getExamHistory = async (id_nguoi_dung, limit = 10) => {
  try {
    logDebug('getExamHistory', { id_nguoi_dung, limit });
    
    const response = await fetch(
      `${BASE_URL}/exam/history/${id_nguoi_dung}?limit=${limit}`,
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
    logDebug('getExamHistory response', data);
    return data?.data || [];
  } catch (error) {
    console.error('❌ Lỗi khi lấy lịch sử làm bài:', error);
    throw error;
  }
};

export default {
  sendChatMessage,
  loginUser,
  registerUser,
  getChatHistory,
  generateLesson,
  getExamsList,
  getExamDetail,
  submitExam,
  getExamHistory,
};
