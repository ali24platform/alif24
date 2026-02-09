import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Lock, Play, CheckCircle, RefreshCcw, Award } from 'lucide-react';
import studentService from '../services/studentService';
import { useAuth } from '../context/AuthContext';

const LessonPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();

    const [lesson, setLesson] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [locked, setLocked] = useState(false);

    // Quiz State
    const [answers, setAnswers] = useState({});
    const [submitting, setSubmitting] = useState(false);
    const [quizResult, setQuizResult] = useState(null); // { success, coins_earned, etc }
    const [showSuccessModal, setShowSuccessModal] = useState(false);

    useEffect(() => {
        fetchLesson();
    }, [id]);

    const fetchLesson = async () => {
        setLoading(true);
        setError(null);
        setLocked(false);
        try {
            const data = await studentService.getLesson(id);
            setLesson(data.data);
        } catch (err) {
            if (err.status === 403) {
                setLocked(true);
                setError(err.message);
            } else {
                setError("Darsni yuklashda xatolik yuz berdi");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleOptionSelect = (questionId, optionKey) => {
        setAnswers(prev => ({
            ...prev,
            [questionId]: optionKey
        }));
    };

    const handleSubmitQuiz = async () => {
        if (!lesson.quiz) return;

        // Validate all questions answered
        const unanswered = lesson.quiz.questions.some(q => !answers[String(q.id)]);
        if (unanswered) {
            alert("Iltimos, barcha savollarga javob bering!");
            return;
        }

        setSubmitting(true);
        try {
            const result = await studentService.completeLesson(id, answers);
            setQuizResult(result);
            if (result.success) {
                setShowSuccessModal(true);
            } else {
                alert(result.message || "Xato javoblar bor. Qayta urinib ko'ring!");
                setAnswers({}); // Reset or keep? Let's keep for review if we had functionality
            }
        } catch (err) {
            alert("Xatolik yuz berdi: " + err.message);
        } finally {
            setSubmitting(false);
        }
    };

    const handleNextLesson = () => {
        // Navigate to next lesson logic or dashboard
        // For now, back to dashboard
        navigate('/student-dashboard');
    };

    // --- RENDER STATES ---

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (locked) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
                <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center">
                    <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Lock className="w-10 h-10 text-red-500" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">Dars Yopilgan</h2>
                    <p className="text-gray-500 mb-6">{error || "Avvalgi darsni yakunlang"}</p>
                    <button
                        onClick={() => navigate('/student-dashboard')}
                        className="w-full py-3 bg-gray-800 text-white rounded-xl hover:bg-gray-900 transition"
                    >
                        Dashboardga qaytish
                    </button>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-xl text-red-600 mb-4">{error}</h2>
                    <button onClick={fetchLesson} className="px-4 py-2 bg-blue-600 text-white rounded">Qayta urinish</button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            {/* Header */}
            <div className="bg-white shadow-sm sticky top-0 z-10">
                <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
                    <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
                        <ArrowLeft className="w-6 h-6 text-gray-600" />
                    </button>
                    <h1 className="font-bold text-gray-800 truncate px-4">{lesson.title}</h1>
                    <div className="w-10"></div> {/* Spacer */}
                </div>
            </div>

            <div className="max-w-3xl mx-auto px-4 pt-6 space-y-8">

                {/* Video Section */}
                <div className="bg-black rounded-2xl overflow-hidden shadow-lg aspect-video relative group">
                    {lesson.video_url ? (
                        <iframe
                            src={lesson.video_url.replace('watch?v=', 'embed/')}
                            className="w-full h-full"
                            title={lesson.title}
                            allowFullScreen
                        />
                    ) : (
                        <div className="w-full h-full flex flex-col items-center justify-center text-white/50">
                            <Play className="w-16 h-16 mb-4 opacity-50" />
                            <p>Video mavjud emas</p>
                        </div>
                    )}
                </div>

                {/* Content / Description */}
                <div className="bg-white p-6 rounded-2xl shadow-sm prose max-w-none">
                    <h2 className="text-xl font-bold mb-4">Dars haqida</h2>
                    <div dangerouslySetInnerHTML={{ __html: lesson.description }} />
                </div>

                {/* Quiz Section */}
                {lesson.quiz && (
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-blue-100">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <CheckCircle className="text-blue-600" />
                                Test Topshirish
                            </h2>
                            <span className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
                                {lesson.quiz.questions.length} ta savol
                            </span>
                        </div>

                        <div className="space-y-8">
                            {lesson.quiz.questions.map((q, index) => (
                                <div key={q.id} className="p-4 bg-gray-50 rounded-xl">
                                    <h3 className="font-semibold text-gray-800 mb-4 flex gap-3">
                                        <span className="flex-shrink-0 w-6 h-6 bg-gray-200 text-gray-600 text-sm rounded-full flex items-center justify-center">
                                            {index + 1}
                                        </span>
                                        {q.question}
                                    </h3>
                                    <div className="space-y-3 pl-9">
                                        {q.options.map((opt, optIndex) => {
                                            // Find key for this option (A, B, C...) based on index?
                                            // The backend usually sends options as array. 
                                            // We need to match the backend expectation. 
                                            // Current TeacherTest logic uses list of strings.
                                            // And maps A->0, B->1 etc.
                                            // BUT `answers` in completeLesson expects keys?
                                            // Wait, StudentService._grade_quiz expects: 
                                            // answers.get(q_id) == q.correct_answer (which is a string value "Option B")

                                            // Let's assume options are simple strings and correct_answer matches one of them.
                                            return (
                                                <label
                                                    key={optIndex}
                                                    className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${answers[String(q.id)] === opt
                                                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                                                            : 'border-gray-200 hover:border-gray-300'
                                                        }`}
                                                >
                                                    <input
                                                        type="radio"
                                                        name={`question-${q.id}`}
                                                        className="hidden"
                                                        onChange={() => handleOptionSelect(String(q.id), opt)} // Assuming backend verifies precise string match? 
                                                    // Re-checking backend logic: 
                                                    // if submitted == correct:
                                                    // correct is stored as "Option content" in simple mode
                                                    // Yes, let's look at `test_builder_service.py`
                                                    // "correct_answer": item["correct_answer"] (String value)
                                                    />
                                                    <div className={`w-4 h-4 rounded-full border mr-3 flex items-center justify-center ${answers[String(q.id)] === opt ? 'border-blue-500' : 'border-gray-400'
                                                        }`}>
                                                        {answers[String(q.id)] === opt && <div className="w-2 h-2 bg-blue-500 rounded-full" />}
                                                    </div>
                                                    <span>{opt}</span>
                                                </label>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="mt-8 pt-6 border-t">
                            <button
                                onClick={handleSubmitQuiz}
                                disabled={submitting}
                                className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition transform active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {submitting ? (
                                    <RefreshCcw className="animate-spin w-5 h-5" />
                                ) : (
                                    <>Testni Yakunlash</>
                                )}
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Success Modal */}
            {showSuccessModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-3xl p-8 max-w-sm w-full text-center shadow-2xl relative overflow-hidden">
                        {/* Confetti effect background (optional CSS) */}
                        <div className="absolute inset-0 bg-gradient-to-b from-yellow-50 to-transparent pointer-events-none"></div>

                        <div className="w-24 h-24 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6 relative z-10">
                            <Award className="w-12 h-12 text-yellow-600" />
                        </div>

                        <h2 className="text-3xl font-bold text-gray-800 mb-2 relative z-10">Tabriklaymiz!</h2>
                        <p className="text-gray-600 mb-6 relative z-10">Siz darsni muvaffaqiyatli yakunladingiz.</p>

                        {quizResult && quizResult.coins_earned > 0 && (
                            <div className="bg-yellow-50 py-3 rounded-xl mb-6 border border-yellow-100 relative z-10">
                                <p className="text-sm text-yellow-800 font-medium">Siz ishlagan tangalar:</p>
                                <p className="text-2xl font-bold text-yellow-600">+{quizResult.coins_earned} 🟡</p>
                            </div>
                        )}

                        <button
                            onClick={handleNextLesson}
                            className="w-full py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-black transition relative z-10"
                        >
                            Keyingi Dars
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LessonPage;
