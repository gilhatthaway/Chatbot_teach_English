import React, { useState } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, StyleSheet, 
  Image, ScrollView, Alert, KeyboardAvoidingView, Platform, ActivityIndicator 
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import ChatView from './ChatView';
import GenerateLessonView from './GenerateLessonView';
import { loginUser, registerUser } from './api';


// --- 2. COMPONENT MÀN HÌNH LOGIN (Kết nối API) ---
const LoginView = ({ onLoginSuccess }) => {
  const [isLoginTab, setIsLoginTab] = useState(true); 
  const [email, setEmail] = useState('admin@gmail.com');
  const [password, setPassword] = useState('bao123');
  const [username, setUsername] = useState('admin');
  const [loading, setLoading] = useState(false);

  const handleAuth = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Thông báo", "Vui lòng nhập Email và Mật khẩu");
      return;
    }

    setLoading(true);
    try {
      if (isLoginTab) {
        // Đăng nhập
        const result = await loginUser(email, password);
        if (result && result.id_nguoi_dung) {
          Alert.alert("✅ Thành công", "Đăng nhập thành công!");
          onLoginSuccess(result.id_nguoi_dung, result.ten_dang_nhap || "User");
        } else {
          Alert.alert("❌ Lỗi", result?.message || "Email hoặc mật khẩu không đúng");
        }
      } else {
        // Đăng ký
        if (!username.trim()) {
          Alert.alert("Thông báo", "Vui lòng nhập tên đăng nhập");
          setLoading(false);
          return;
        }
        const result = await registerUser(username, email, password);
        if (result && result.status === 'success') {
          Alert.alert("✅ Thành công", "Đăng ký thành công! Vui lòng xác thực OTP");
          setIsLoginTab(true);
        } else {
          Alert.alert("❌ Lỗi", result?.message || "Đăng ký thất bại");
        }
      }
    } catch (error) {
      Alert.alert(
        "❌ Lỗi",
        "Không thể kết nối tới server. Vui lòng kiểm tra:\n- Server đã khởi động?\n- IP address có đúng không?",
        [{ text: "OK" }]
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.loginContainer}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.loginScrollContent} showsVerticalScrollIndicator={false}>
          <View style={styles.loginHeader}>
            <Text style={styles.appTitle}>🤖 AI English</Text>
            <Text style={styles.appSlogan}>Unlock Your English Potential with Your Personal AI Tutor</Text>
            <Image 
              source={{ uri: 'https://cdn3d.iconscout.com/3d/premium/thumb/cute-robot-say-hello-5592591-4654769.png' }} 
              style={styles.robotImage} 
            />
          </View>
          <View style={styles.loginCard}>
            <View style={styles.tabContainer}>
              <TouchableOpacity style={[styles.tab, isLoginTab && styles.activeTab]} onPress={() => setIsLoginTab(true)}>
                <Text style={[styles.tabText, isLoginTab && styles.activeTabText]}>Đăng nhập</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.tab, !isLoginTab && styles.activeTab]} onPress={() => setIsLoginTab(false)}>
                <Text style={[styles.tabText, !isLoginTab && styles.activeTabText]}>Đăng ký</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.formTitle}>{isLoginTab ? "Welcome Back!" : "Join Us Today!"}</Text>
            <View style={styles.inputGroup}>
              {!isLoginTab && (
                <View style={styles.inputWrapper}>
                  <Text style={styles.inputIcon}>👤</Text>
                  <TextInput 
                    style={styles.input} placeholder="Tên đăng nhập" placeholderTextColor="#aaa"
                    value={username} onChangeText={setUsername}
                    autoCapitalize="none"
                  />
                </View>
              )}
              <View style={styles.inputWrapper}>
                <Text style={styles.inputIcon}>📧</Text>
                <TextInput 
                  style={styles.input} placeholder="Email" placeholderTextColor="#aaa"
                  value={email} onChangeText={setEmail}
                  keyboardType="email-address" autoCapitalize="none"
                />
              </View>
              <View style={styles.inputWrapper}>
                <Text style={styles.inputIcon}>🔒</Text>
                <TextInput 
                  style={styles.input} placeholder="Mật khẩu" placeholderTextColor="#aaa"
                  value={password} onChangeText={setPassword}
                  secureTextEntry={true} 
                />
              </View>
            </View>
            <TouchableOpacity 
              style={[styles.submitBtn, loading && styles.submitBtnDisabled]} 
              onPress={handleAuth}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Text style={styles.submitBtnText}>{isLoginTab ? "Log In" : "Sign Up"}</Text>
              )}
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// --- 3. COMPONENT MÀN HÌNH HOME ---
const HomeView = ({ onLogout, onNavigateChat, onNavigateGenerateLesson, userName = "User" }) => {
  const handleLogoutPress = () => {
    Alert.alert("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất?", [
      { text: "Hủy", style: "cancel" },
      { text: "Đồng ý", onPress: onLogout }
    ]);
  };

  // Component thẻ tính năng có thêm prop onPress
  const FeatureCard = ({ icon, title, description, onPress }) => (
    <TouchableOpacity style={styles.homeCard} onPress={onPress}>
      <Text style={styles.cardIcon}>{icon}</Text>
      <Text style={styles.cardTitle}>{title}</Text>
      <Text style={styles.cardDesc}>{description}</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.homeContainer}>
      <View style={styles.topBar}>
        <Text style={styles.adminText}>Xin chào, {userName}</Text>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogoutPress}>
          <Text style={styles.logoutText}>Đăng xuất</Text>
        </TouchableOpacity>
      </View>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.heroSection}>
          <Text style={styles.heroTitle}>Chào mừng đến với{'\n'}AI Learning Hub</Text>
          <Text style={styles.heroSubtitle}>Học tiếng Anh và trò chuyện cùng AI dễ dàng</Text>
        </View>
        <View style={styles.featureContainer}>
          <FeatureCard 
            icon="📚" 
            title="Tạo Bài Học Mới" 
            description="Tạo bài tập tiếng Anh từ AI" 
            onPress={onNavigateGenerateLesson} 
          />
          <FeatureCard icon="🎤" title="Trợ lý giọng nói AI" description="Nói chuyện và luyện phát âm với AI" />
          <FeatureCard 
            icon="💬" 
            title="Chatbot với AI" 
            description="Trò chuyện tự nhiên để luyện tiếng Anh" 
            onPress={onNavigateChat} 
          />
        </View>
        <View style={styles.footer}>
          <Text style={styles.footerText}>✨ Được hỗ trợ bởi công nghệ AI tiên tiến ✨</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// --- 4. MAIN APP (Quản lý điều hướng các màn hình) ---
const MainApp = () => {
  // state: 'login' | 'home' | 'chat' | 'lessonStats' | 'generateLesson'
  const [currentScreen, setCurrentScreen] = useState('login');
  const [userId, setUserId] = useState(null);
  const [userName, setUserName] = useState('User');

  const handleLoginSuccess = (id, name) => {
    setUserId(id);
    setUserName(name);
    setCurrentScreen('home');
  };

  const handleLogout = () => {
    setUserId(null);
    setUserName('User');
    setCurrentScreen('login');
  };
  
  if (currentScreen === 'login') {
    return <LoginView onLoginSuccess={handleLoginSuccess} />;
  }

  if (currentScreen === 'chat') {
    return <ChatView onBack={() => setCurrentScreen('home')} onLogout={handleLogout} userId={userId} />;
  }

  if (currentScreen === 'generateLesson') {
    return <GenerateLessonView onBack={() => setCurrentScreen('home')} onLogout={handleLogout} userId={userId} />;
  }
  // Mặc định là màn hình Home
  return (
    <HomeView 
      onLogout={handleLogout} 
      onNavigateChat={() => setCurrentScreen('chat')}
      onNavigateGenerateLesson={() => setCurrentScreen('generateLesson')}
      userName={userName}
    />
  );
};

// --- STYLE CHUNG ---
const styles = StyleSheet.create({
  // === Style LOGIN ===
  loginContainer: { flex: 1, backgroundColor: '#0f2540' },
  loginScrollContent: { flexGrow: 1, justifyContent: 'center', padding: 20 },
  loginHeader: { alignItems: 'center', marginBottom: 20 },
  appTitle: { fontSize: 28, fontWeight: 'bold', color: '#00a8ff', marginBottom: 5 },
  appSlogan: { color: '#cfd8dc', textAlign: 'center', marginBottom: 15 },
  robotImage: { width: 120, height: 120 },
  loginCard: { backgroundColor: 'white', borderRadius: 20, padding: 20, elevation: 5 },
  tabContainer: { flexDirection: 'row', borderBottomWidth: 1, borderColor: '#eee', marginBottom: 20 },
  tab: { flex: 1, paddingVertical: 10, alignItems: 'center', borderBottomWidth: 2, borderColor: 'transparent' },
  activeTab: { borderColor: '#00a8ff' },
  tabText: { color: '#999', fontWeight: '600' },
  activeTabText: { color: '#0f2540', fontWeight: 'bold' },
  formTitle: { fontSize: 18, fontWeight: 'bold', textAlign: 'center', marginBottom: 20, color: '#333' },
  inputGroup: { gap: 15, marginBottom: 20 },
  inputWrapper: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f1f2f6', borderRadius: 8, paddingHorizontal: 10, height: 50 },
  inputIcon: { fontSize: 18, marginRight: 10 },
  input: { flex: 1, color: '#333' },
  submitBtn: { backgroundColor: '#00a8ff', borderRadius: 8, height: 50, justifyContent: 'center', alignItems: 'center' },
  submitBtnDisabled: { opacity: 0.5, backgroundColor: '#66c2ff' },
  submitBtnText: { color: 'white', fontSize: 16, fontWeight: 'bold' },

  // === Style HOME ===
  homeContainer: { flex: 1, backgroundColor: '#00a8ff' },
  topBar: { flexDirection: 'row', justifyContent: 'flex-end', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 15 },
  adminText: { color: 'white', fontSize: 14, fontWeight: '600', marginRight: 15 },
  logoutBtn: { backgroundColor: '#ff4757', paddingHorizontal: 15, paddingVertical: 8, borderRadius: 20, elevation: 3 },
  logoutText: { color: 'white', fontWeight: 'bold', fontSize: 12 },
  scrollContent: { paddingBottom: 30 },
  heroSection: { alignItems: 'center', marginVertical: 30, paddingHorizontal: 20 },
  heroTitle: { fontSize: 28, fontWeight: '800', color: 'white', textAlign: 'center', marginBottom: 10, lineHeight: 36 },
  heroSubtitle: { fontSize: 16, color: 'rgba(255, 255, 255, 0.9)', textAlign: 'center' },
  featureContainer: { paddingHorizontal: 20, gap: 20 },
  homeCard: { backgroundColor: 'white', borderRadius: 20, padding: 25, alignItems: 'center', elevation: 5, shadowColor: "#000", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.1, shadowRadius: 10 },
  cardIcon: { fontSize: 50, marginBottom: 15 },
  cardTitle: { fontSize: 20, fontWeight: '700', color: '#2f3542', marginBottom: 8, textAlign: 'center' },
  cardDesc: { fontSize: 14, color: '#747d8c', textAlign: 'center', lineHeight: 20 },
  footer: { marginTop: 40, alignItems: 'center' },
  footerText: { color: 'rgba(255, 255, 255, 0.8)', fontSize: 13, fontStyle: 'italic' },
});

export default MainApp;