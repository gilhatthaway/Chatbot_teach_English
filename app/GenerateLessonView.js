import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  Alert,
  ActivityIndicator,
  FlatList,
} from 'react-native';
import { CONFIG, logDebug } from './config';
import { generateLesson } from './api';

/**
 * GenerateLessonView - Tạo bài tập/bài học từ AI
 * Tương tự lesson.html nhưng cho React Native
 */
const GenerateLessonView = ({ onBack, onLogout, userId = 1 }) => {
  const [topic, setTopic] = useState('');
  const [lessonData, setLessonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('vocabulary');
  const scrollViewRef = useRef();

  const handleGenerateLesson = async () => {
    if (!topic.trim()) {
      Alert.alert('⚠️ Thông báo', 'Vui lòng nhập chủ đề bài học');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setLessonData(null);

      logDebug('GenerateLesson', { userId, topic });
      const response = await generateLesson(userId, topic);

      logDebug('Response from backend:', response);

      // Parse dữ liệu từ backend
      let parsedLesson = null;

      // Nếu response là object chứa bài học trực tiếp (không có wrapper)
      if (response && (response.topic || response.vocabulary)) {
        parsedLesson = normalizeLessonData(response, topic);
      } 
      // Nếu có wrapper lesson
      else if (response && response.lesson) {
        if (typeof response.lesson === 'string') {
          parsedLesson = normalizeLessonData(JSON.parse(response.lesson), topic);
        } else {
          parsedLesson = normalizeLessonData(response.lesson, topic);
        }
      }

      if (parsedLesson) {
        setLessonData(parsedLesson);
        Alert.alert('✅ Bài học đã được tạo!', 'Nội dung bài học từ AI sẵn sàng học.');
      } else {
        throw new Error('Không thể parse dữ liệu bài học');
      }
    } catch (err) {
      console.error('❌ Lỗi tạo bài học:', err);
      setError(err.message || 'Không thể tạo bài học. Vui lòng thử lại.');
      Alert.alert('❌ Lỗi', err.message || 'Không thể kết nối tới server');
    } finally {
      setLoading(false);
    }
  };

  // Function để normalize dữ liệu từ backend
  const normalizeLessonData = (data, fallbackTopic = "") => {
    try {
      return {
        topic: data.topic || fallbackTopic,
        vocabulary: (data.vocabulary || []).map((v) => ({
          word: v.word || '',
          pronunciation: v.pronunciation || '',
          meaning: v.english_meaning || v.meaning || '',
          example: v.example || '',
        })),
        examples: (data.example_sentences || data.examples || []).map((ex) => ({
          english: ex.english || '',
          vietnamese: ex.translation || ex.vietnamese || '',
        })),
        conversation: (data.conversation || []).map((msg) => ({
          speaker: msg.speaker === 'Person A' ? 'Person A' : msg.speaker === 'Person B' ? 'Person B' : msg.speaker || 'Speaker',
          text: msg.text || msg.english_line || msg.content || '',
          vietnamese: msg.vietnamese || msg.vietnamese_translation || '',
        })),
        exercises: (data.exercises || []).map((ex) => {
          // Normalize exercise types
          let normalizedType = ex.type;
          if (ex.type === 'fill_in_blank') normalizedType = 'fill';
          if (ex.type === 'sentence_order') normalizedType = 'order';
          if (ex.type === 'make_sentence') normalizedType = 'make';

          const baseExercise = {
            type: normalizedType,
            question: ex.question || '',
            correct_answer: ex.answer || '',
          };

          if (normalizedType === 'fill') {
            // Xử lý options - có thể là array of strings hoặc array of objects
            let options = ex.options || [];
            if (options.length > 0 && typeof options[0] === 'object') {
              options = options.map(opt => opt.text || opt.value || opt.label || '');
            }
            
            return {
              ...baseExercise,
              sentence: ex.sentence || ex.sentence_with_blank || '',
              options: options,
            };
          } else if (normalizedType === 'order') {
            return {
              ...baseExercise,
              words: ex.scrambled || [],
            };
          } else if (normalizedType === 'make') {
            return {
              ...baseExercise,
              target: ex.word || '',
              hint: ex.example || '',
            };
          }

          return baseExercise;
        }),
      };
    } catch (parseError) {
      console.error('❌ Lỗi parse dữ liệu:', parseError);
      return null;
    }
  };

  // Component: Vocabulary Section
  const VocabularySection = () => {
    if (!lessonData?.vocabulary) return null;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📚 Từ Vựng</Text>
        {lessonData.vocabulary.map((vocab, index) => (
          <View key={index} style={styles.vocabularyItem}>
            <Text style={styles.vocabWord}>{vocab.word}</Text>
            <Text style={styles.vocabPronunciation}>
              /{vocab.pronunciation}/
            </Text>
            <Text style={styles.vocabMeaning}>{vocab.meaning}</Text>
            <Text style={styles.vocabExample}>
              Ví dụ: {vocab.example}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  // Component: Examples Section
  const ExamplesSection = () => {
    if (!lessonData?.examples) return null;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>💡 Ví Dụ</Text>
        {lessonData.examples.map((example, index) => (
          <View key={index} style={styles.exampleItem}>
            <Text style={styles.exampleEnglish}>{example.english}</Text>
            <Text style={styles.exampleVietnamese}>{example.vietnamese}</Text>
          </View>
        ))}
      </View>
    );
  };

  // Component: Conversation Section
  const ConversationSection = () => {
    if (!lessonData?.conversation) return null;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🗣️ Hội Thoại</Text>
        {lessonData.conversation.map((msg, index) => (
          <View key={index} style={styles.conversationItem}>
            <Text style={styles.speakerName}>{msg.speaker}</Text>
            <Text style={styles.conversationEnglish}>{msg.text}</Text>
            {msg.vietnamese && (
              <Text style={styles.conversationVietnamese}>{msg.vietnamese}</Text>
            )}
          </View>
        ))}
      </View>
    );
  };

  // Component: Exercise Item
  const ExerciseItem = ({ exercise, index }) => {
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [isCorrect, setIsCorrect] = useState(null);

    const handleCheckAnswer = (answer) => {
      setSelectedAnswer(answer);
      const correct = answer === exercise.correct_answer;
      setIsCorrect(correct);
      if (correct) {
        Alert.alert('✅ Chính xác!', 'Bạn trả lời đúng.');
      } else {
        Alert.alert(
          '❌ Sai rồi!',
          `Đáp án đúng là: ${exercise.correct_answer}`
        );
      }
    };

    return (
      <View style={styles.exerciseItem}>
        <Text style={styles.exerciseNumber}>
          Bài {index + 1}: {exercise.type === 'fill' ? '📝 Điền từ' : exercise.type === 'order' ? '🔢 Sắp xếp' : '✍️ Viết câu'}
        </Text>
        <Text style={styles.exerciseQuestion}>{exercise.question}</Text>

        {exercise.type === 'fill' && exercise.options && (
          <View style={styles.optionsContainer}>
            {exercise.options.map((option, idx) => (
              <TouchableOpacity
                key={idx}
                style={[
                  styles.optionButton,
                  selectedAnswer === option && styles.optionSelected,
                  isCorrect === true &&
                    selectedAnswer === option &&
                    styles.optionCorrect,
                  isCorrect === false &&
                    selectedAnswer === option &&
                    styles.optionIncorrect,
                ]}
                onPress={() => handleCheckAnswer(option)}
              >
                <Text
                  style={[
                    styles.optionText,
                    selectedAnswer === option &&
                      styles.optionTextSelected,
                  ]}
                >
                  {option}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {exercise.type === 'fill' && exercise.sentence && (
          <Text style={styles.sentenceContext}>
            📖 Câu: {exercise.sentence}
          </Text>
        )}

        {exercise.type === 'order' && exercise.words && (
          <View style={styles.wordsContainer}>
            <Text style={styles.instructionText}>
              Sắp xếp các từ để tạo thành câu:
            </Text>
            <Text style={styles.wordsList}>{exercise.words.join(' ')}</Text>
            <Text style={styles.hintText}>
              Đáp án: {exercise.correct_answer}
            </Text>
          </View>
        )}

        {exercise.type === 'make' && (
          <View style={styles.makeSentenceContainer}>
            <Text style={styles.instructionText}>
              Viết câu sử dụng từ/cụm từ:
            </Text>
            <Text style={styles.targetWord}>{exercise.target}</Text>
            <Text style={styles.hintText}>
              Gợi ý: {exercise.hint}
            </Text>
          </View>
        )}
      </View>
    );
  };

  // Component: Exercises Section
  const ExercisesSection = () => {
    if (!lessonData?.exercises) return null;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>✏️ Bài Tập</Text>
        {lessonData.exercises.map((exercise, index) => (
          <ExerciseItem key={index} exercise={exercise} index={index} />
        ))}
      </View>
    );
  };

  const handleLogout = () => {
    Alert.alert('Đăng xuất', 'Bạn có chắc chắn muốn đăng xuất?', [
      { text: 'Hủy', style: 'cancel' },
      { text: 'Đồng ý', onPress: onLogout },
    ]);
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={onBack}>
          <Text style={styles.backBtnText}>⬅ Quay lại</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>📚 Tạo Bài Học</Text>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutBtnText}>Đăng xuất</Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        ref={scrollViewRef}
        showsVerticalScrollIndicator={false}
      >
        {/* Topic Input Section */}
        <View style={styles.inputSection}>
          <Text style={styles.inputLabel}>📖 Nhập Chủ Đề Bài Học</Text>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="Ví dụ: Family, Weather, Food..."
              value={topic}
              onChangeText={setTopic}
              editable={!loading}
              placeholderTextColor="#999"
            />
            <TouchableOpacity
              style={[styles.generateBtn, loading && styles.generateBtnDisabled]}
              onPress={handleGenerateLesson}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Text style={styles.generateBtnText}>Tạo Bài ✨</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>

        {/* Loading State */}
        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007bff" />
            <Text style={styles.loadingText}>Đang tạo bài học...</Text>
          </View>
        )}

        {/* Error State */}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>❌ {error}</Text>
          </View>
        )}

        {/* Lesson Data */}
        {lessonData && (
          <>
            {/* Topic Display */}
            <View style={styles.topicBox}>
              <Text style={styles.topicTitle}>Chủ Đề: {topic}</Text>
            </View>

            {/* Tab Navigation */}
            <View style={styles.tabContainer}>
              <TouchableOpacity
                style={[
                  styles.tab,
                  activeTab === 'vocabulary' && styles.tabActive,
                ]}
                onPress={() => setActiveTab('vocabulary')}
              >
                <Text
                  style={[
                    styles.tabText,
                    activeTab === 'vocabulary' && styles.tabTextActive,
                  ]}
                >
                  📚 Từ Vựng
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.tab,
                  activeTab === 'examples' && styles.tabActive,
                ]}
                onPress={() => setActiveTab('examples')}
              >
                <Text
                  style={[
                    styles.tabText,
                    activeTab === 'examples' && styles.tabTextActive,
                  ]}
                >
                  💡 Ví Dụ
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.tab,
                  activeTab === 'conversation' && styles.tabActive,
                ]}
                onPress={() => setActiveTab('conversation')}
              >
                <Text
                  style={[
                    styles.tabText,
                    activeTab === 'conversation' && styles.tabTextActive,
                  ]}
                >
                  🗣️ Hội Thoại
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.tab,
                  activeTab === 'exercises' && styles.tabActive,
                ]}
                onPress={() => setActiveTab('exercises')}
              >
                <Text
                  style={[
                    styles.tabText,
                    activeTab === 'exercises' && styles.tabTextActive,
                  ]}
                >
                  ✏️ Bài Tập
                </Text>
              </TouchableOpacity>
            </View>

            {/* Tab Content */}
            <View style={styles.tabContent}>
              {activeTab === 'vocabulary' && <VocabularySection />}
              {activeTab === 'examples' && <ExamplesSection />}
              {activeTab === 'conversation' && <ConversationSection />}
              {activeTab === 'exercises' && <ExercisesSection />}
            </View>
          </>
        )}

        {/* Empty State */}
        {!lessonData && !loading && !error && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              Nhập chủ đề và nhấn "Tạo Bài" để bắt đầu học
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  // Container
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },

  // Header
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#007bff',
    paddingHorizontal: 15,
    paddingVertical: 12,
    elevation: 3,
  },
  backBtn: {
    backgroundColor: '#0056b3',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  backBtnText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 12,
  },
  headerTitle: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  logoutBtn: {
    backgroundColor: '#dc3545',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  logoutBtnText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 12,
  },

  // Content
  content: {
    flex: 1,
    padding: 15,
  },

  // Input Section
  inputSection: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    marginBottom: 20,
    elevation: 2,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  inputContainer: {
    flexDirection: 'row',
    gap: 10,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#333',
  },
  generateBtn: {
    backgroundColor: '#28a745',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  generateBtnDisabled: {
    opacity: 0.5,
  },
  generateBtnText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },

  // Loading
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    marginTop: 15,
    color: '#6c757d',
    fontSize: 14,
  },

  // Error
  errorContainer: {
    backgroundColor: '#f8d7da',
    borderWidth: 1,
    borderColor: '#f5c6cb',
    borderRadius: 8,
    padding: 12,
    marginBottom: 15,
  },
  errorText: {
    color: '#721c24',
    fontSize: 14,
  },

  // Empty State
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 50,
  },
  emptyText: {
    color: '#6c757d',
    fontSize: 14,
    textAlign: 'center',
  },

  // Topic Box
  topicBox: {
    backgroundColor: '#e7f3ff',
    borderLeftWidth: 4,
    borderLeftColor: '#007bff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 15,
  },
  topicTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0056b3',
  },

  // Tab Navigation
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderRadius: 8,
    marginBottom: 15,
    elevation: 1,
    overflow: 'hidden',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    alignItems: 'center',
    borderBottomWidth: 3,
    borderBottomColor: '#f0f0f0',
  },
  tabActive: {
    borderBottomColor: '#007bff',
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6c757d',
  },
  tabTextActive: {
    color: '#007bff',
  },

  // Tab Content
  tabContent: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 15,
    marginBottom: 30,
  },

  // Section
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },

  // Vocabulary
  vocabularyItem: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  vocabWord: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007bff',
  },
  vocabPronunciation: {
    fontSize: 12,
    color: '#e53e3e',
    marginTop: 4,
  },
  vocabMeaning: {
    fontSize: 13,
    color: '#333',
    marginTop: 6,
  },
  vocabExample: {
    fontSize: 12,
    color: '#6c757d',
    marginTop: 6,
    fontStyle: 'italic',
  },

  // Examples
  exampleItem: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  exampleEnglish: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  exampleVietnamese: {
    fontSize: 13,
    color: '#6c757d',
    marginTop: 6,
  },

  // Conversation
  conversationLine: {
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
  },
  speakerA: {
    backgroundColor: '#d1ecf1',
    marginRight: 20,
  },
  speakerB: {
    backgroundColor: '#d4edda',
    marginLeft: 20,
  },
  conversationItem: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#007bff',
  },
  speakerName: {
    fontWeight: 'bold',
    fontSize: 12,
    marginBottom: 4,
    color: '#007bff',
  },
  conversationText: {
    fontSize: 13,
    color: '#333',
  },
  conversationEnglish: {
    fontSize: 13,
    color: '#333',
    fontWeight: '500',
    marginBottom: 4,
  },
  conversationVietnamese: {
    fontSize: 12,
    color: '#6c757d',
    fontStyle: 'italic',
    marginTop: 6,
  },

  // Exercise
  exerciseItem: {
    backgroundColor: '#fff9e6',
    borderRadius: 8,
    padding: 12,
    marginBottom: 15,
  },
  exerciseNumber: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  exerciseQuestion: {
    fontSize: 13,
    color: '#333',
    marginBottom: 12,
    lineHeight: 18,
  },
  optionsContainer: {
    gap: 8,
  },
  optionButton: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 6,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: 'white',
  },
  optionSelected: {
    borderColor: '#007bff',
    backgroundColor: '#e7f3ff',
  },
  optionCorrect: {
    borderColor: '#28a745',
    backgroundColor: '#d4edda',
  },
  optionIncorrect: {
    borderColor: '#dc3545',
    backgroundColor: '#f8d7da',
  },
  optionText: {
    fontSize: 13,
    color: '#333',
    fontWeight: '500',
  },
  optionTextSelected: {
    color: '#007bff',
  },
  sentenceContext: {
    fontSize: 13,
    color: '#6c757d',
    fontStyle: 'italic',
    backgroundColor: '#f0f0f0',
    padding: 10,
    borderRadius: 6,
    marginTop: 10,
  },
  wordsContainer: {
    backgroundColor: 'white',
    borderRadius: 6,
    padding: 12,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  instructionText: {
    fontSize: 12,
    color: '#6c757d',
    marginBottom: 8,
  },
  wordsList: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  hintText: {
    fontSize: 12,
    color: '#6c757d',
    fontStyle: 'italic',
  },
  targetWord: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#007bff',
    marginVertical: 8,
  },
  makeSentenceContainer: {
    backgroundColor: 'white',
    borderRadius: 6,
    padding: 12,
    borderWidth: 1,
    borderColor: '#ddd',
  },
});

export default GenerateLessonView;
