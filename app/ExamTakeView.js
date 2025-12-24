import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  FlatList,
  RadioButton,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getExamsList, getExamDetail, submitExam } from './api';

// --- EXAM LIST VIEW (Danh sách bài kiểm tra) ---
const ExamListView = ({ onSelectExam, onBack }) => {
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchExams();
  }, []);

  const fetchExams = async () => {
    try {
      setLoading(true);
      const data = await getExamsList();
      setExams(data || []);
      if (!data || data.length === 0) {
        setError('Chưa có bài kiểm tra nào');
      }
    } catch (err) {
      setError('Lỗi khi tải danh sách bài kiểm tra: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const ExamCard = ({ exam }) => (
    <TouchableOpacity
      style={styles.examCard}
      onPress={() => onSelectExam(exam.id_kt)}
    >
      <View style={styles.examCardContent}>
        <Text style={styles.examTitle}>{exam.tieu_de}</Text>
        <Text style={styles.examDesc}>{exam.mo_ta}</Text>
        <View style={styles.examMeta}>
          <Text style={styles.examMeta}>📝 {exam.so_cau} câu hỏi</Text>
          <Text style={styles.examDate}>📅 {exam.ngay_tao?.substring(0, 10)}</Text>
        </View>
      </View>
      <Text style={styles.arrowIcon}>→</Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onBack}>
            <Text style={styles.backBtn}>← Quay lại</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Bài kiểm tra</Text>
        </View>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#00a8ff" />
          <Text style={styles.loadingText}>Đang tải bài kiểm tra...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onBack}>
            <Text style={styles.backBtn}>← Quay lại</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Bài kiểm tra</Text>
        </View>
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>❌ {error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={fetchExams}>
            <Text style={styles.retryBtnText}>Thử lại</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack}>
          <Text style={styles.backBtn}>← Quay lại</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Bài kiểm tra ({exams.length})</Text>
      </View>
      {exams.length === 0 ? (
        <View style={styles.centerContent}>
          <Text style={styles.emptyText}>📭 Chưa có bài kiểm tra nào</Text>
        </View>
      ) : (
        <FlatList
          data={exams}
          keyExtractor={(item) => item.id_kt.toString()}
          renderItem={({ item }) => <ExamCard exam={item} />}
          contentContainerStyle={styles.examList}
          scrollEnabled={true}
        />
      )}
    </SafeAreaView>
  );
};

// --- EXAM DETAIL VIEW (Chi tiết bài kiểm tra) ---
const ExamDetailView = ({ examId, onBack, userId }) => {
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchExamDetail();
  }, [examId]);

  const fetchExamDetail = async () => {
    try {
      setLoading(true);
      const data = await getExamDetail(examId);
      setExam(data);
      // Khởi tạo câu trả lời
      const initialAnswers = {};
      data.cau_hoi?.forEach((q) => {
        initialAnswers[q.id_cauhoi] = null;
      });
      setAnswers(initialAnswers);
    } catch (err) {
      Alert.alert('Lỗi', 'Không thể tải bài kiểm tra: ' + err.message);
      onBack();
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId, answerId) => {
    setAnswers({
      ...answers,
      [questionId]: answerId,
    });
  };

  const handleSubmit = async () => {
    // Kiểm tra trả lời hết hết
    const unanswered = exam.cau_hoi?.filter((q) => answers[q.id_cauhoi] === null);
    if (unanswered?.length > 0) {
      Alert.alert(
        'Chưa hoàn thành',
        `Vui lòng trả lời tất cả ${unanswered.length} câu hỏi`,
      );
      return;
    }

    Alert.alert('Xác nhận nộp bài', 'Bạn chắc chắn muốn nộp bài không?', [
      { text: 'Hủy', onPress: () => {} },
      {
        text: 'Nộp bài',
        onPress: async () => {
          setSubmitting(true);
          try {
            // Chuẩn bị dữ liệu nộp - tương ứng với format backend
            const bai_lam = exam.cau_hoi?.map((q) => ({
              id_cauhoi: q.id_cauhoi,
              dap_an_da_chon: Array.isArray(answers[q.id_cauhoi]) 
                ? answers[q.id_cauhoi] 
                : (answers[q.id_cauhoi] ? [answers[q.id_cauhoi]] : []),
              tra_loi_tu_luan: typeof answers[q.id_cauhoi] === 'string' 
                ? answers[q.id_cauhoi] 
                : '',
            }));

            const result = await submitExam(userId, examId, bai_lam);
            Alert.alert(
              '✅ Nộp bài thành công',
              `Điểm của bạn: ${result.diem}/10\nSố câu đúng: ${result.so_cau_dung}/${result.tong_cau}`,
              [{ text: 'OK', onPress: onBack }],
            );
          } catch (err) {
            Alert.alert('Lỗi', 'Không thể nộp bài: ' + err.message);
          } finally {
            setSubmitting(false);
          }
        },
      },
    ]);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onBack}>
            <Text style={styles.backBtn}>← Quay lại</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Đang tải...</Text>
        </View>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#00a8ff" />
        </View>
      </SafeAreaView>
    );
  }

  if (!exam) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onBack}>
            <Text style={styles.backBtn}>← Quay lại</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Lỗi</Text>
        </View>
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>❌ Không tìm thấy bài kiểm tra</Text>
        </View>
      </SafeAreaView>
    );
  }

  const QuestionCard = ({ question, index }) => (
    <View style={styles.questionCard}>
      <Text style={styles.questionNumber}>Câu {index + 1}</Text>
      <Text style={styles.questionText}>{question.noi_dung}</Text>
      <View style={styles.difficultyBadge}>
        <Text style={styles.difficultyText}>
          {question.muc_do === 'de' && '⭐ Dễ'}
          {question.muc_do === 'trung_binh' && '⭐⭐ Trung bình'}
          {question.muc_do === 'kho' && '⭐⭐⭐ Khó'}
        </Text>
      </View>

      {question.loai_cau_hoi === 'trac_nghiem' ? (
        <View style={styles.answerContainer}>
          {question.dap_an?.map((ans) => (
            <TouchableOpacity
              key={ans.id_dapan}
              style={[
                styles.answerOption,
                answers[question.id_cauhoi] === ans.id_dapan && styles.selectedAnswer,
              ]}
              onPress={() => handleAnswerChange(question.id_cauhoi, ans.id_dapan)}
            >
              <View style={styles.radioOption}>
                <View
                  style={[
                    styles.radioCircle,
                    answers[question.id_cauhoi] === ans.id_dapan && styles.radioSelected,
                  ]}
                />
              </View>
              <Text
                style={[
                  styles.answerText,
                  answers[question.id_cauhoi] === ans.id_dapan && styles.selectedAnswerText,
                ]}
              >
                {ans.noi_dung}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      ) : (
        <View style={styles.essayAnswerContainer}>
          <Text style={styles.essayLabel}>Câu trả lời tự luận:</Text>
          <Text style={styles.essayAnswer}>{question.dap_an?.[0]?.noi_dung || 'N/A'}</Text>
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack}>
          <Text style={styles.backBtn}>← Quay lại</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{exam.tieu_de}</Text>
      </View>

      <ScrollView contentContainerStyle={styles.detailContent}>
        {exam.mo_ta && (
          <View style={styles.descriptionBox}>
            <Text style={styles.descriptionText}>{exam.mo_ta}</Text>
          </View>
        )}

        {exam.cau_hoi?.map((q, idx) => (
          <QuestionCard key={q.id_cauhoi} question={q} index={idx} />
        ))}

        <View style={styles.submissionInfo}>
          <Text style={styles.submissionText}>
            Đã trả lời: {Object.values(answers).filter((a) => a !== null).length}/
            {exam.cau_hoi?.length || 0}
          </Text>
        </View>
      </ScrollView>

      <View style={styles.submitContainer}>
        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.submitBtnText}>✓ Nộp bài</Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

// --- MAIN COMPONENT ---
const ExamTakeView = ({ onBack, userId }) => {
  const [view, setView] = useState('list'); // 'list' | 'detail'
  const [selectedExamId, setSelectedExamId] = useState(null);

  const handleSelectExam = (examId) => {
    setSelectedExamId(examId);
    setView('detail');
  };

  const handleBackFromDetail = () => {
    setView('list');
    setSelectedExamId(null);
  };

  if (view === 'detail' && selectedExamId) {
    return (
      <ExamDetailView
        examId={selectedExamId}
        onBack={handleBackFromDetail}
        userId={userId}
      />
    );
  }

  return <ExamListView onSelectExam={handleSelectExam} onBack={onBack} />;
};

// --- STYLES ---
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#00a8ff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backBtn: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  headerTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1,
    textAlign: 'center',
    marginLeft: -50,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 15,
    color: '#666',
    fontSize: 16,
  },
  errorText: {
    color: '#d63031',
    fontSize: 16,
    textAlign: 'center',
    marginHorizontal: 20,
  },
  emptyText: {
    color: '#999',
    fontSize: 18,
  },
  retryBtn: {
    marginTop: 20,
    backgroundColor: '#00a8ff',
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryBtnText: {
    color: 'white',
    fontWeight: '600',
  },

  // EXAM LIST
  examList: {
    padding: 15,
  },
  examCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  examCardContent: {
    flex: 1,
  },
  examTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2f3542',
    marginBottom: 5,
  },
  examDesc: {
    fontSize: 13,
    color: '#636e72',
    marginBottom: 10,
    lineHeight: 18,
  },
  examMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    fontSize: 12,
    color: '#a29bfe',
  },
  examDate: {
    fontSize: 12,
    color: '#a29bfe',
  },
  arrowIcon: {
    fontSize: 24,
    color: '#00a8ff',
    marginLeft: 10,
  },

  // EXAM DETAIL
  detailContent: {
    padding: 15,
    paddingBottom: 100,
  },
  descriptionBox: {
    backgroundColor: '#e8f5e9',
    borderLeftColor: '#4caf50',
    borderLeftWidth: 4,
    padding: 12,
    borderRadius: 8,
    marginBottom: 20,
  },
  descriptionText: {
    color: '#2e7d32',
    fontSize: 14,
    lineHeight: 20,
  },
  questionCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  questionNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: '#00a8ff',
    marginBottom: 8,
  },
  questionText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#2f3542',
    marginBottom: 10,
    lineHeight: 22,
  },
  difficultyBadge: {
    backgroundColor: '#fff3cd',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    marginBottom: 12,
    alignSelf: 'flex-start',
  },
  difficultyText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#856404',
  },
  answerContainer: {
    gap: 10,
  },
  answerOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#e9ecef',
  },
  selectedAnswer: {
    backgroundColor: '#e3f2fd',
    borderColor: '#00a8ff',
  },
  radioOption: {
    marginRight: 12,
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#ccc',
  },
  radioSelected: {
    backgroundColor: '#00a8ff',
    borderColor: '#00a8ff',
  },
  answerText: {
    flex: 1,
    fontSize: 14,
    color: '#495057',
  },
  selectedAnswerText: {
    color: '#00a8ff',
    fontWeight: '600',
  },
  essayAnswerContainer: {
    backgroundColor: '#f1f3f5',
    padding: 12,
    borderRadius: 8,
    marginTop: 10,
  },
  essayLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#868e96',
    marginBottom: 8,
  },
  essayAnswer: {
    fontSize: 14,
    color: '#2f3542',
    lineHeight: 20,
  },
  submissionInfo: {
    backgroundColor: '#cfe9f3',
    padding: 12,
    borderRadius: 8,
    marginTop: 15,
    alignItems: 'center',
  },
  submissionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0c5aa0',
  },
  submitContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'white',
    padding: 15,
    borderTopWidth: 1,
    borderTopColor: '#eee',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  submitBtn: {
    backgroundColor: '#00a8ff',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    elevation: 3,
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitBtnText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default ExamTakeView;
