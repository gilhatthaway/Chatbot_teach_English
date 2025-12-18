import React, { useState, useRef, useEffect } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, StyleSheet, 
  Image, ScrollView, KeyboardAvoidingView, Platform, Alert, ActivityIndicator
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { sendChatMessage, getChatHistory } from './api';

const ChatView = ({ onBack, onLogout, userId = 1 }) => {
  const [messages, setMessages] = useState([
    { id: 1, text: "Xin chào! Tôi là AI Assistant. Tôi có thể giúp gì cho bạn hôm nay? 😊", sender: 'bot' }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollViewRef = useRef();

  // Load lịch sử chat khi component mount
  useEffect(() => {
    loadChatHistory();
  }, [userId]);

  const loadChatHistory = async () => {
    try {
      const history = await getChatHistory(userId, 10);
      // Cập nhật messages từ lịch sử nếu có dữ liệu
      if (history && history.length > 0) {
        const formattedMessages = history.map((msg, index) => ({
          id: index,
          text: msg.text || msg.noi_dung || "",
          sender: msg.sender === 'user' ? 'user' : msg.role === 'user' ? 'user' : 'bot'
        }));
        // Giữ tin nhắn khởi tạo nếu không có lịch sử
        if (formattedMessages.length > 0) {
          setMessages(formattedMessages);
        }
      }
    } catch (error) {
      console.log('Không thể tải lịch sử chat (có thể server chưa khởi động)');
    }
  };

  const handleSend = async () => {
    if (inputText.trim() && !loading) {
      const userMessage = inputText.trim();
      
      // 1. Thêm tin nhắn của người dùng ngay lập tức
      const newUserMsg = { 
        id: Date.now(), 
        text: userMessage, 
        sender: 'user' 
      };
      setMessages(prev => [...prev, newUserMsg]);
      setInputText('');
      setLoading(true);

      try {
        // 2. Gửi tin nhắn tới AI backend
        const response = await sendChatMessage(userId, userMessage);
        
        // 3. Xử lý phản hồi từ server
        let botReply = "Tôi không hiểu câu hỏi của bạn. Vui lòng thử lại.";
        
        if (response) {
          // Kiểm tra các trường phản hồi từ API
          if (response.response_english) {
            botReply = response.response_english;
            
            // Thêm giải thích tiếng Việt nếu có
            if (response.explanation_vietnamese) {
              botReply += "\n\n📝 Giải thích: " + response.explanation_vietnamese;
            }
            
            // Thêm sửa lỗi nếu có
            if (response.correction) {
              botReply += "\n\n✏️ Sửa lỗi: " + response.correction;
            }
          } else if (response.message) {
            botReply = response.message;
          }
        }
        
        // 4. Thêm tin nhắn từ bot
        const botMsg = { 
          id: Date.now() + 1, 
          text: botReply, 
          sender: 'bot' 
        };
        setMessages(prev => [...prev, botMsg]);
        
      } catch (error) {
        console.error('Lỗi chat:', error);
        Alert.alert(
          "❌ Lỗi",
          "Không kết nối được tới server. Vui lòng kiểm tra:\n- Server Python đã khởi động?\n- IP address có đúng không?",
          [{ text: "OK" }]
        );
        
        // Thêm tin nhắn lỗi
        const errorMsg = { 
          id: Date.now() + 1, 
          text: "❌ Lỗi kết nối. Vui lòng thử lại.", 
          sender: 'bot' 
        };
        setMessages(prev => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <SafeAreaView style={styles.chatContainer}>
      {/* Header Tổng */}
      <View style={styles.chatMainHeader}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <Text style={styles.backButtonText}>⬅ Trang chủ</Text>
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={styles.headerEmoji}>🤖</Text>
          <Text style={styles.headerTitle}>AI Chat Assistant</Text>
          <Text style={styles.headerSubtitle}>Trò chuyện thông minh, trải nghiệm tuyệt vời</Text>
        </View>
        <View style={{ width: 80 }} /> {/* Dummy view để cân giữa tiêu đề */}
      </View>

      {/* Khung Chat Trắng */}
      <View style={styles.whiteChatBox}>
        {/* Header con bên trong (Thông tin AI & Admin) */}
        <View style={styles.innerHeader}>
          <View style={styles.botInfo}>
            <Image 
              source={{ uri: 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png' }} 
              style={styles.smallBotAvatar} 
            />
            <View>
              <Text style={styles.botName}>AI Teacher 😎</Text>
              <Text style={styles.botStatus}>Đang hoạt động</Text>
            </View>
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>👤 admin</Text>
            <TouchableOpacity style={styles.miniLogoutBtn} onPress={onLogout}>
              <Text style={styles.miniLogoutText}>Đăng xuất</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Danh sách tin nhắn */}
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1 }}>
          <ScrollView 
            style={styles.messageArea}
            ref={scrollViewRef}
            onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
          >
            {messages.map((msg) => (
              <View key={msg.id} style={[
                styles.messageBubble, 
                msg.sender === 'user' ? styles.userBubble : styles.botBubble
              ]}>
                {msg.sender === 'bot' && (
                   <Image source={{ uri: 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png' }} style={styles.msgAvatar} />
                )}
                <View style={[styles.bubbleTextWrapper, msg.sender === 'user' ? styles.userTextWrapper : styles.botTextWrapper]}>
                  <Text style={styles.messageText}>{msg.text}</Text>
                </View>
              </View>
            ))}
            {loading && (
              <View style={[styles.messageBubble, styles.botBubble]}>
                <Image source={{ uri: 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png' }} style={styles.msgAvatar} />
                <View style={[styles.bubbleTextWrapper, styles.botTextWrapper]}>
                  <ActivityIndicator size="small" color="#0084ff" />
                </View>
              </View>
            )}
          </ScrollView>

          {/* Ô nhập liệu */}
          <View style={styles.inputArea}>
            <TextInput
              style={styles.chatInput}
              placeholder="Nhập tin nhắn của bạn..."
              value={inputText}
              onChangeText={setInputText}
              editable={!loading}
            />
            <TouchableOpacity 
              style={[styles.sendButton, loading && styles.sendButtonDisabled]} 
              onPress={handleSend}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Text style={styles.sendButtonText}>Gửi ✈️</Text>
              )}
            </TouchableOpacity>
          </View>
          
          <Text style={styles.chatFooterText}>Trải nghiệm chatbot thông minh</Text>
        </KeyboardAvoidingView>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  chatContainer: { flex: 1, backgroundColor: '#0085d6' },
  chatMainHeader: { alignItems: 'center', paddingVertical: 10, paddingHorizontal: 15, flexDirection: 'row', justifyContent: 'space-between' },
  backButton: { backgroundColor: '#0062cc', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 8 },
  backButtonText: { color: 'white', fontWeight: 'bold', fontSize: 12 },
  headerTitleContainer: { alignItems: 'center', flex: 1 },
  headerEmoji: { fontSize: 24, marginBottom: 2 },
  headerTitle: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  headerSubtitle: { color: '#e1f5fe', fontSize: 11 },
  
  whiteChatBox: { 
    flex: 1, backgroundColor: '#f0f2f5', margin: 15, borderRadius: 15, overflow: 'hidden',
    shadowColor: "#000", shadowOffset: { width: 0, height: 5 }, shadowOpacity: 0.2, shadowRadius: 10, elevation: 8 
  },
  innerHeader: { 
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', 
    backgroundColor: '#007bff', padding: 15 
  },
  botInfo: { flexDirection: 'row', alignItems: 'center' },
  smallBotAvatar: { width: 35, height: 35, borderRadius: 20, backgroundColor: 'white', marginRight: 10 },
  botName: { color: 'white', fontWeight: 'bold', fontSize: 14 },
  botStatus: { color: '#d1e7ff', fontSize: 10 },
  userInfo: { flexDirection: 'row', alignItems: 'center' },
  userName: { color: 'white', marginRight: 10, fontWeight: '600' },
  miniLogoutBtn: { backgroundColor: '#ff5252', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 5 },
  miniLogoutText: { color: 'white', fontSize: 10, fontWeight: 'bold' },

  messageArea: { flex: 1, padding: 15 },
  messageBubble: { maxWidth: '80%', padding: 12, borderRadius: 15, marginBottom: 15, flexDirection: 'row', alignItems: 'flex-end' },
  botBubble: { alignSelf: 'flex-start' },
  userBubble: { alignSelf: 'flex-end', flexDirection: 'row-reverse' },
  msgAvatar: { width: 30, height: 30, borderRadius: 15, marginRight: 8 },
  bubbleTextWrapper: { borderRadius: 15, padding: 12 },
  botTextWrapper: { backgroundColor: '#e4e6eb' },
  userTextWrapper: { backgroundColor: '#0084ff' },
  messageText: { fontSize: 14, color: '#333', lineHeight: 20 },
  
  inputArea: { 
    flexDirection: 'row', padding: 10, backgroundColor: 'white', 
    borderTopWidth: 1, borderTopColor: '#ddd', alignItems: 'center' 
  },
  chatInput: { 
    flex: 1, height: 45, borderWidth: 1, borderColor: '#0084ff', 
    borderRadius: 25, paddingHorizontal: 15, backgroundColor: 'white', marginRight: 10 
  },
  sendButton: { backgroundColor: '#0084ff', paddingVertical: 12, paddingHorizontal: 20, borderRadius: 25 },
  sendButtonDisabled: { opacity: 0.5, backgroundColor: '#99c9ff' },
  sendButtonText: { color: 'white', fontWeight: 'bold' },
  chatFooterText: { textAlign: 'center', fontSize: 10, color: '#888', paddingBottom: 10, backgroundColor: 'white' },
});

export default ChatView;
