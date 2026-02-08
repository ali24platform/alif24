import React, { useState, useEffect, useRef, useCallback } from "react";
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";
import { Mic, StopCircle, BookOpen, CheckCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';


const API_BASE = import.meta.env.VITE_API_URL 
  ? import.meta.env.VITE_API_URL.replace('/v1', '/smartkids') 
  : "https://alif-24.vercel.app/api/v1/smartkids";

const STORY_API_BASE = import.meta.env.VITE_API_URL 
  ? import.meta.env.VITE_API_URL.replace('/v1', '/story') 
  : "https://alif-24.vercel.app/api/v1/story";

export default function StoryReader({ storyText, age = 7 }) {
  const { user: authUser } = useAuth();
  const [isReading, setIsReading] = useState(false);
  const [readingFinished, setReadingFinished] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [loadingQuestion, setLoadingQuestion] = useState(false);
  const [questionCount, setQuestionCount] = useState(0);
  const [childAnswer, setChildAnswer] = useState("");
  const [childAudioText, setChildAudioText] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [audioQueue, setAudioQueue] = useState([]);
  const [isMainTextFinished, setIsMainTextFinished] = useState(false);
  const [isQuestioningFinished, setIsQuestioningFinished] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState(""); // Keyingi savol uchun
  
  // Self Reading States
  const [isSelfReading, setIsSelfReading] = useState(false);
  const [selfReadText, setSelfReadText] = useState("");
  const [showSelfReadModal, setShowSelfReadModal] = useState(false);
  const [analyzingReading, setAnalyzingReading] = useState(false);
  const [readingAnalysisResult, setReadingAnalysisResult] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const [facingMode, setFacingMode] = useState("environment");
  const [capturedImage, setCapturedImage] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const synthesizerRef = useRef(null);
  const recognizerRef = useRef(null);
  const speechConfigRef = useRef(null);
  const isSpeakingRef = useRef(false);
  const mainTextFlagRef = useRef(false);
  const timerRef = useRef(null);
  const detectedLanguageRef = useRef(null);
  const [languageError, setLanguageError] = useState(null);

  // Tilni aniqlash funksiyasi
  const detectLanguage = (text) => {
    if (!text || !text.trim()) return null;
    
    const sample = text.substring(0, 1000).toLowerCase(); // Birinchi 1000 belgini tekshiramiz
    
    // Rus xarakterli harflar (ё, ы, э, ю, я)
    const russianSpecific = /[ёыэюя]/;
    const russianSpecificCount = (sample.match(/[ёыэюя]/g) || []).length;
    
    // Rus kiril harflar (umumiy)
    const russianCyrillic = /[а-яё]/;
    const russianCount = (sample.match(/[а-яё]/g) || []).length;
    
    // O'zbek xarakterli harflar (lotin: o', g', sh, ch, ng; kiril: ў, қ, ғ, ҳ)
    const uzbekSpecific = /[o'g'ўқғҳ]/;
    const uzbekSpecificCount = (sample.match(/[o'g'ўқғҳ]/gi) || []).length;
    
    // O'zbek kiril harflar (ў, қ, ғ, ҳ bilan)
    const uzbekKiril = /[а-яёўқғҳ]/;
    const uzbekKirilCount = (sample.match(/[а-яёўқғҳ]/g) || []).length;
    
    // Ingliz harflar
    const englishCount = (sample.match(/[a-z]/g) || []).length;
    
    // Ingliz xarakterli so'zlar (kengaytirilgan ro'yxat)
    const englishWords = /\b(the|and|is|are|was|were|this|that|with|from|have|has|will|would|could|should|what|where|when|why|how|can|may|must|been|being|had|has|have|do|does|did|an|as|at|be|by|for|in|of|on|to|he|she|it|we|they|you|i|american|industrialist|business|magnate|founder|company|credited|pioneer|making|automobiles|affordable|middle|class|through|system|known|awarded|patent|transmission|mechanism|model|other|ford|motor|fordism)\b/i;
    const englishWordMatches = (sample.match(englishWords) || []).length;
    
    // Ingliz xarakterli strukturalar
    const englishPatterns = /\b(was an|is a|are a|he is|she is|it is|we are|they are|you are|i am|has been|have been|will be|would be|could be|should be|the [a-z]+|an [a-z]+|a [a-z]+)\b/i;
    const englishPatternMatches = (sample.match(englishPatterns) || []).length;
    
    // Harflar sonini hisoblash
    const totalLetters = sample.replace(/[^а-яёa-zўқғҳ]/g, '').length;
    
    console.log("🔍 Til aniqlash statistikasi:", {
      russianSpecificCount,
      russianCount,
      uzbekSpecificCount,
      uzbekKirilCount,
      englishCount,
      englishWordMatches,
      englishPatternMatches,
      totalLetters,
      sample: sample.substring(0, 100)
    });
    
    if (totalLetters === 0) return null;
    
    // 1. INGLIZ TILINI BIRINCHI TEKSHIRISH (eng muhim)
    // Agar faqat lotin harflari bo'lsa va ingliz so'zlari ko'p bo'lsa
    if (russianCount === 0 && uzbekKirilCount === 0 && englishCount > 0) {
      console.log("🇺🇸 Faqat lotin harflari bor, ingliz so'zlarini tekshiramiz");
      // Ingliz so'zlari yoki strukturalari mavjudligini tekshiramiz
      if (englishWordMatches >= 2 || englishPatternMatches >= 1) {
        console.log("🇺🇸 Ingliz tili aniqlandi (so'zlar/strukturalar asosida)");
        return { code: 'en-US', voice: 'en-US-JennyNeural', name: 'Ingliz' };
      }
      // Agar lotin harflari 70% dan ko'p bo'lsa va kiril harflar yo'q bo'lsa
      if (englishCount / totalLetters > 0.7) {
        console.log("🇺🇸 Ingliz tili aniqlandi (harflar nisbati asosida)");
        return { code: 'en-US', voice: 'en-US-JennyNeural', name: 'Ingliz' };
      }
    }
    
    // 2. Rus tilini aniqlash (rus xarakterli harflar bor va kiril harflar ko'p)
    if (russianSpecificCount > 0 || (russianCount > 50 && russianCount / totalLetters > 0.5)) {
      console.log("🇷🇺 Rus tili aniqlandi");
      return { code: 'ru-RU', voice: 'ru-RU-DariyaNeural', name: 'Rus' };
    }
    
    // 3. O'zbek tilini aniqlash (o'zbek xarakterli harflar bor)
    if (uzbekSpecificCount > 0) {
      console.log("🇺🇿 O'zbek tili aniqlandi (xarakterli harflar)");
      return { code: 'uz-UZ', voice: 'uz-UZ-MadinaNeural', name: "O'zbek" };
    }
    
    // 4. O'zbek kiril (rus xarakterli harflar yo'q, lekin kiril harflar bor)
    if (uzbekKirilCount > 0 && russianSpecificCount === 0 && uzbekKirilCount / totalLetters > 0.3) {
      console.log("🇺🇿 O'zbek kiril tili aniqlandi");
      return { code: 'uz-UZ', voice: 'uz-UZ-MadinaNeural', name: "O'zbek" };
    }
    
    // 5. O'zbek lotin (o'zbek xarakterli harflar yo'q, lekin lotin harflar ko'p va ingliz so'zlari kam)
    if (englishCount > 0 && englishWordMatches < 1 && englishPatternMatches === 0 && uzbekSpecificCount === 0 && englishCount / totalLetters > 0.5) {
      console.log("🇺🇿 O'zbek lotin tili aniqlandi");
      return { code: 'uz-UZ', voice: 'uz-UZ-MadinaNeural', name: "O'zbek" };
    }
    
    // 6. Agar aniq aniqlanmasa, eng ko'p bo'lgan tilni qaytaramiz
    if (russianCount > englishCount && russianCount > uzbekKirilCount) {
      console.log("🇷🇺 Rus tili aniqlandi (nisbat bo'yicha)");
      return { code: 'ru-RU', voice: 'ru-RU-DariyaNeural', name: 'Rus' };
    } else if (englishCount > uzbekKirilCount && (englishWordMatches > 0 || englishPatternMatches > 0)) {
      console.log("🇺🇸 Ingliz tili aniqlandi (nisbat bo'yicha)");
      return { code: 'en-US', voice: 'en-US-JennyNeural', name: 'Ingliz' };
    } else if (uzbekKirilCount > 0 || (englishCount > 0 && englishWordMatches === 0 && englishPatternMatches === 0)) {
      console.log("🇺🇿 O'zbek tili aniqlandi (nisbat bo'yicha)");
      return { code: 'uz-UZ', voice: 'uz-UZ-MadinaNeural', name: "O'zbek" };
    }
    
    console.log("❌ Til aniqlanmadi");
    return null;
  };

  // Speech Config'ni yaratish va tilni sozlash (backend'dan token olish)
  useEffect(() => {
    const initSpeechConfig = async () => {
      if (!speechConfigRef.current) {
        try {
          console.log('🎤 Fetching speech token from backend...');
          
          // Backend'dan token olish
          const apiBase = import.meta.env.VITE_API_URL 
            ? import.meta.env.VITE_API_URL.replace('/v1', '/smartkids') 
            : "https://alif-24.vercel.app/api/v1/smartkids";
            
          const response = await fetch(`${apiBase}/speech-token`);
          
          if (!response.ok) {
            throw new Error(`Failed to get token: ${response.status}`);
          }
          
          const data = await response.json();
          console.log('✅ Got speech token from backend');
          
          // Token bilan config yaratish
          speechConfigRef.current = SpeechSDK.SpeechConfig.fromAuthorizationToken(
            data.token,
            data.region
          );
          
          // Matn tilini aniqlash va sozlash
          if (storyText) {
            const langInfo = detectLanguage(storyText);
            if (langInfo) {
              detectedLanguageRef.current = langInfo;
              speechConfigRef.current.speechRecognitionLanguage = langInfo.code;
              speechConfigRef.current.speechSynthesisVoiceName = langInfo.voice;
              console.log(`✅ Til aniqlandi: ${langInfo.name} (${langInfo.code})`);
              setLanguageError(null);
            } else {
              setLanguageError("Qo'llab-quvvatlanmaydigan til. Faqat o'zbek, rus va ingliz tillari qo'llab-quvvatlanadi.");
              console.warn('⚠️ Til aniqlanmadi');
            }
          } else {
            // Default: O'zbek tili
            speechConfigRef.current.speechRecognitionLanguage = "uz-UZ";
            speechConfigRef.current.speechSynthesisVoiceName = "uz-UZ-MadinaNeural";
            detectedLanguageRef.current = { code: 'uz-UZ', voice: 'uz-UZ-MadinaNeural', name: "O'zbek" };
          }
          
        } catch (error) {
          console.error('❌ Failed to initialize speech config:', error);
        }
      }
    };
    
    initSpeechConfig();
  }, [storyText]);

  // Camera Functions
  const startCamera = async () => {
    try {
      const constraints = {
        video: {
          facingMode: facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      setShowCamera(true);
    } catch (error) {
      console.error('Kamera ochishda xatolik:', error);
      alert('Kamera ochishda xatolik yuz berdi. Iltimos, kamera ruxsatini yoqing.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowCamera(false);
    setCapturedImage(null);
  };

  const switchCamera = async () => {
    const newFacingMode = facingMode === "user" ? "environment" : "user";
    setFacingMode(newFacingMode);
    
    if (streamRef.current) {
      stopCamera();
      setTimeout(() => {
        startCamera();
      }, 100);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const context = canvas.getContext('2d');
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      const imageData = canvas.toDataURL('image/jpeg', 0.9);
      setCapturedImage(imageData);
      
      stopCamera();
    }
  };

  // Birinchi savolni yuklash funksiyasi (useCallback bilan)
  const loadFirstQuestion = useCallback(async () => {
    setLoadingQuestion(true);
    try {
      const res = await fetch(`${STORY_API_BASE}/next-question`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          story_text: storyText, 
          age: age,
          conversation_history: [],
          question_number: 1,
          language: detectedLanguageRef.current?.code || 'uz-UZ'
        }),
      });
      const data = await res.json();
      if (data.question) {
        setCurrentQuestion(data.question);
        setQuestionCount(1);
        console.log("✅ Birinchi savol yuklandi:", data.question);
        console.log("🌐 Til uchun savol yuklandi:", detectedLanguageRef.current?.code || 'uz-UZ');
        // Birinchi savolni ham avtomatik ovoz bilan aytamiz
        // Lekin audio queue bo'sh bo'lganda qo'shamiz (useEffect orqali boshqariladi)
      }
    } catch (err) {
      console.error("Savol yuklanmadi:", err);
      window.appAlert("Savol yuklanmadi");
    } finally {
      setLoadingQuestion(false);
    }
  }, [storyText, age]);

  // Tahlilni saqlash funksiyasi (useCallback)
  const saveSession = useCallback(async () => {
    try {
      // Tahlillardan ballarni hisoblash
      const totalWords = storyText.split(/\s+/).length;
      const speechErrorsCount = analyses.reduce((sum, a) => {
        return sum + (a?.speech_errors?.length || 0);
      }, 0);
      
      // O'rtacha ballarni hisoblash
      const pronunciationScore = readingAnalysisResult?.analysis?.accuracy_score || 75;
      const fluencyScore = readingAnalysisResult?.analysis?.fluency_feedback ? 80 : 70;
      const comprehensionScore = analyses.length > 0 ? 
        analyses.reduce((sum, a) => {
          const score = a?.meaning_analysis?.includes('to\'g\'ri') ? 90 : 
                       a?.meaning_analysis?.includes('yaxshi') ? 80 : 70;
          return sum + score;
        }, 0) / analyses.length : 0;
      
      const answerQualityScore = analyses.length > 0 ?
        analyses.reduce((sum, a) => {
          const score = a?.thinking_assessment?.includes('juda yaxshi') ? 95 :
                       a?.thinking_assessment?.includes('yaxshi') ? 85 : 70;
          return sum + score;
        }, 0) / analyses.length : 0;

      // Auth context-dan user_id olish
      const userId = authUser?.id || localStorage.getItem('user_id') || 'test-user-id';
      
      console.log("👤 User ID:", userId);

      const analysisData = {
        user_id: userId,
        story_title: `Ertak ${new Date().toLocaleDateString()}`,
        total_words_read: totalWords,
        reading_time_seconds: Math.floor((Date.now() - (conversationHistory[0]?.timestamp || Date.now())) / 1000),
        speech_errors: speechErrorsCount,
        pronunciation_score: pronunciationScore,
        fluency_score: fluencyScore,
        comprehension_score: comprehensionScore,
        expression_quality: answerQualityScore,
        total_questions: questionCount,
        correct_answers: analyses.filter(a => 
          a?.meaning_analysis?.includes('to\'g\'ri')
        ).length,
        answer_quality_score: answerQualityScore,
        conversation_history: conversationHistory.slice(0, 10), // Oxirgi 10 ta
        detailed_analysis: {
          analyses: analyses,
          reading_result: readingAnalysisResult
        },
        ai_feedback: `${questionCount} ta savolga javob berdi. Nutq xatolari: ${speechErrorsCount}.`
      };

      console.log("📤 Tahlil yuborilmoqda:", analysisData);

      // Tahlilni saqlash
      const res = await fetch(`${STORY_API_BASE}/save-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(analysisData),
      });
      
      if (!res.ok) {
        throw new Error(`Server xatosi: ${res.status}`);
      }
      
      const data = await res.json();
      if (data.analysis_id) {
        console.log("✅ Tahlil saqlandi:", data.analysis_id);
      } else {
        console.error("❌ Tahlilni saqlashda xatolik:", data);
      }
    } catch (err) {
      console.error("❌ Saqlash xatosi:", err);
    }
  }, [storyText, analyses, readingAnalysisResult, questionCount, conversationHistory]);

  // Matnni gaplarga bo'lish funksiyasi (butun matnni bir qism sifatida qaytaradi)
  const splitTextToSentences = (text) => {
    if (!text) return [];
    // Butun matnni bir qism sifatida qaytaramiz (to'xtashsiz o'qish uchun)
    return [text];
  };

  // TTS bilan matn aytish (useCallback bilan)
  const speakText = useCallback(async (text) => {
    if (!speechConfigRef.current || isSpeakingRef.current) return;
    
    isSpeakingRef.current = true;
    setIsSpeaking(true);
    
    // Standart AudioConfig (karnayga chiqarish)
    const audioConfig = SpeechSDK.AudioConfig.fromDefaultSpeakerOutput();
    
    // Yangi sintezator yaratamiz
    const synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfigRef.current, audioConfig);
    synthesizerRef.current = synthesizer;
    
    synthesizer.speakTextAsync(
      text,
      (result) => {
        if (result.reason === SpeechSDK.ResultReason.SynthesizingAudioCompleted) {
          console.log("📝 Sintez tugadi. Audio uzunligi (ticks):", result.audioDuration);
          
          // Audio davomiyligini hisoblash (10,000,000 ticks = 1 sekund)
          // Qisqa bufer qo'shamiz (100ms) - to'xtashsiz o'qish uchun
          const durationInSeconds = result.audioDuration / 10000000;
          const waitTimeMs = (durationInSeconds * 1000) + 100;
          
          console.log(`⏳ Kutish vaqti: ${waitTimeMs}ms (${durationInSeconds}s)`);
          
          // Audio butunlay tugashini kutish uchun taymer
          if (timerRef.current) clearTimeout(timerRef.current);
          
          timerRef.current = setTimeout(() => {
            console.log("✅ Audio jismonan tugadi (Timer Finished):", text.substring(0, 30));
            
            isSpeakingRef.current = false;
            setIsSpeaking(false);
            
            if (synthesizerRef.current) {
              synthesizerRef.current.close();
              synthesizerRef.current = null;
            }
            
            // Navbatdan olib tashlash
            setAudioQueue(prev => prev.slice(1));
          }, waitTimeMs);
          
        } else {
          console.error("⚠️ Sintez bekor qilindi:", result.errorDetails);
          isSpeakingRef.current = false;
          setIsSpeaking(false);
          if (synthesizerRef.current) {
            synthesizerRef.current.close();
            synthesizerRef.current = null;
          }
        }
      },
      (err) => {
        console.error("TTS xatosi:", err);
        isSpeakingRef.current = false;
        setIsSpeaking(false);
        if (synthesizerRef.current) {
          synthesizerRef.current.close();
          synthesizerRef.current = null;
        }
      }
    );
  }, []); // Removed specific deps as they are refs or stable

  // Audio navbatini boshqarish
  useEffect(() => {
    if (audioQueue.length > 0 && !isSpeakingRef.current) {
      const nextText = audioQueue[0];
      speakText(nextText);
    } else if (audioQueue.length === 0 && pendingQuestion && !isSpeakingRef.current) {
      // Audio queue bo'sh bo'lganda va pending savol bo'lsa, uni qo'shamiz
      console.log("✅ Audio tugadi, keyingi savolni qo'shyapman:", pendingQuestion);
      setAudioQueue([pendingQuestion]);
      setPendingQuestion("");
    }
  }, [audioQueue, speakText, pendingQuestion]);

  // Hikoya tugaganini aniqlash (Audioqueue bo'sh va o'qish rejimi yoqilgan bo'lsa)
  useEffect(() => {
    if (isReading && audioQueue.length === 0 && !isSpeaking && !isSpeakingRef.current) {
      // Faqat rostan ham tugagan bo'lsa (loopga tushmaslik uchun)
       console.log("🎯 Asosiy matn o'qib bo'lindi. Savol berishga o'tamiz...");
       setIsReading(false);
       setIsMainTextFinished(true); // Bu Question useEffectini ishga tushiradi
       mainTextFlagRef.current = true;
       loadFirstQuestion();
    }
  }, [audioQueue, isReading, isSpeaking, loadFirstQuestion]);
  
  // Savol-javob tugagandan keyin avtomatik saqlash
  useEffect(() => {
    if (isQuestioningFinished && analyses.length > 0) {
      console.log("✅ Savol-javoblar tugadi. Hisobot avtomatik saqlanmoqda...");
      saveSession();
    }
  }, [isQuestioningFinished, analyses, saveSession]);

  // Savolni audio queue'ga qo'shish (asosiy matn tugagandan keyin)
  useEffect(() => {
    if (isMainTextFinished && !isReading && currentQuestion && audioQueue.length === 0 && !isSpeaking) {
      console.log("⏳ Asosiy matn to'liq o'qib bo'lindi, savolni queue'ga qo'shyapman:", currentQuestion);
      setAudioQueue([currentQuestion]);
      setReadingFinished(true);  // ✅ Savol ko'rsatiladi
      setIsMainTextFinished(false); // Flag'ni tozalaymiz
    }
  }, [isMainTextFinished, isReading, currentQuestion, audioQueue, isSpeaking]);

  const startReading = async () => {
    // Tilni tekshirish
    if (!storyText || !storyText.trim()) {
      window.appAlert("Matn topilmadi.");
      return;
    }
    
    // Tilni aniqlash va sozlash
    const langInfo = detectLanguage(storyText);
    if (!langInfo) {
      window.appAlert("Qo'llab-quvvatlanmaydigan til. Faqat o'zbek, rus va ingliz tillari qo'llab-quvvatlanadi.");
      setLanguageError("Qo'llab-quvvatlanmaydigan til. Faqat o'zbek, rus va ingliz tillari qo'llab-quvvatlanadi.");
      return;
    }
    
    // Speech config'ni yangilash
    if (speechConfigRef.current) {
      detectedLanguageRef.current = langInfo;
      speechConfigRef.current.speechRecognitionLanguage = langInfo.code;
      speechConfigRef.current.speechSynthesisVoiceName = langInfo.voice;
      console.log(`✅ Til sozlandi: ${langInfo.name} (${langInfo.code})`);
      setLanguageError(null);
    }
    
    setIsReading(true);
    setIsMainTextFinished(false);
    mainTextFlagRef.current = false;
    setReadingFinished(false);
    setCurrentQuestion("");
    setReadingAnalysisResult(null);
    
    // Matnni gaplarga bo'lamiz
    const sentences = splitTextToSentences(storyText);
    console.log(`🚀 O'qish boshlandi, matn ${sentences.length} ta qismga bo'lindi (Til: ${langInfo.name})`);
    setAudioQueue(sentences);
  };

  // --- Self Reading Functions ---

  const startSelfReadingListener = () => {
    if (!speechConfigRef.current) {
        window.appAlert("Ovozli aloqa sozlanmagan. Iltimos sahifani yangilang.");
        return;
    }
    
    // Tilni tekshirish
    if (!detectedLanguageRef.current) {
      const langInfo = detectLanguage(storyText);
      if (!langInfo) {
        window.appAlert("Qo'llab-quvvatlanmaydigan til. Faqat o'zbek, rus va ingliz tillari qo'llab-quvvatlanadi.");
        return;
      }
      detectedLanguageRef.current = langInfo;
      speechConfigRef.current.speechRecognitionLanguage = langInfo.code;
      speechConfigRef.current.speechSynthesisVoiceName = langInfo.voice;
    }
    
    // Stop any existing recognizer
    if (recognizerRef.current) {
        try {
            recognizerRef.current.stopContinuousRecognitionAsync();
            recognizerRef.current.close();
        } catch(e) { console.error(e); }
        recognizerRef.current = null;
    }

    const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
    const recognizer = new SpeechSDK.SpeechRecognizer(speechConfigRef.current, audioConfig);
    recognizerRef.current = recognizer;

    recognizer.recognizing = (s, e) => {
        // Real-time intermediate results logic if needed
        // console.log("Recognizing:", e.result.text);
    };

    recognizer.recognized = (s, e) => {
        if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
            console.log("Self read recognized segment:", e.result.text);
            setSelfReadText(prev => prev + " " + e.result.text);
        }
    };
    
    recognizer.canceled = (s, e) => {
        console.log(`Canceled: Reason=${e.reason}`);
        if (e.reason === SpeechSDK.CancellationReason.Error) {
            console.log(`ErrorDetails=${e.errorDetails}`);
        }
    };

    recognizer.startContinuousRecognitionAsync();
    setIsListening(true);
  };

  const stopSelfReadingListener = () => {
      if (recognizerRef.current) {
          recognizerRef.current.stopContinuousRecognitionAsync(() => {
              recognizerRef.current.close();
              recognizerRef.current = null;
          });
      }
      setIsListening(false);
  };

  const startSelfReadingMode = () => {
      // Initialize states
      setIsSelfReading(true);
      setSelfReadText("");
      setReadingAnalysisResult(null);
      setShowSelfReadModal(true);
      
      // Auto start mic after short delay to allow UI to render
      setTimeout(() => {
          startSelfReadingListener();
      }, 500);
  };

  const finishSelfReading = async () => {
      stopSelfReadingListener();
      
      // Check if text is too short
      if (selfReadText.trim().length < 5) {
          // alert("O'qilgan matn juda qisqa bo'ldi. Baribir davom etamizmi?");
          // For now, proceed.
      }
      
      setAnalyzingReading(true);
      try {
           const res = await fetch(`${STORY_API_BASE}/analyze-reading`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                  story_text: storyText,
                  spoken_text: selfReadText,
                  age: age,
                  language: detectedLanguageRef.current?.code || 'uz-UZ'
                }),
           });
           
           if (!res.ok) throw new Error("Analysis failed");
           
           const data = await res.json();
           if (data.analysis) {
               setReadingAnalysisResult(data.analysis);
           }
      } catch (e) {
          console.error("Reading analysis error:", e);
      } finally {
          setAnalyzingReading(false);
      }
  };

  const closeSelfReadingAndStartQuestions = () => {
      setShowSelfReadModal(false);
      setIsSelfReading(false);
      setReadingFinished(true); // Manually finish reading
      setCurrentQuestion(""); // Reset questions if needed or load first
      loadFirstQuestion();
      
      // Self-reading tahlilini saqlash
      if (readingAnalysisResult) {
        console.log("✅ O'zini o'qish tahlili avtomatik saqlanmoqda...");
        saveSession();
      }
  };

  // --- End Self Reading Functions ---

  // Savol aytish
  const speakQuestion = async (questionText) => {
    setAudioQueue(prev => [...prev, questionText]);
  };

  // STT - Mikrofondan eshitishni boshlash (mousedown/touchstart)
  const startListening = () => {
    // Agar ruxsatlar yo'q bo'lsa
    if (!speechConfigRef.current) {
      window.appAlert("Ovozli aloqa sozlanmagan. Iltimos sahifani yangilang.");
      return;
    }

    // Agar TTS gapirayotgan bo'lsa, ishga tushirmaymiz
    if (isSpeakingRef.current) {
      window.appAlert("Audio eshitilmoqda. Iltimos kuting.");
      return;
    }

    // Agar allaqachon eshitilayotgan bo'lsa, hech narsa qilmaymiz
    if (isListening) return;
    
    setIsListening(true);
    // Yangi javob uchun tozalaymiz
    setChildAnswer("");
    setChildAudioText("");
    
    const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
    const recognizer = new SpeechSDK.SpeechRecognizer(speechConfigRef.current, audioConfig);
    recognizerRef.current = recognizer;
    
    let accumulatedText = "";
    
    // Real-time intermediate results
    recognizer.recognizing = (s, e) => {
      if (e.result.text) {
        accumulatedText = e.result.text;
        setChildAudioText(accumulatedText);
      }
    };
    
    // Final recognized results
    recognizer.recognized = (s, e) => {
      if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech && e.result.text) {
        accumulatedText = e.result.text;
        setChildAudioText(accumulatedText);
        setChildAnswer(accumulatedText);
      }
    };
    
    recognizer.canceled = (s, e) => {
      console.log(`Canceled: Reason=${e.reason}`);
      if (e.reason === SpeechSDK.CancellationReason.Error) {
        console.log(`ErrorDetails=${e.errorDetails}`);
        window.appAlert("Mikrofon xatosi yuz berdi.");
      }
      setIsListening(false);
      if (recognizerRef.current) {
        recognizerRef.current.close();
        recognizerRef.current = null;
      }
    };
    
    // Continuous recognition boshlash
    recognizer.startContinuousRecognitionAsync(
      () => {
        console.log("✅ Continuous recognition boshlandi");
      },
      (err) => {
        console.error("STT xatosi:", err);
        setIsListening(false);
        if (recognizerRef.current) {
          recognizerRef.current.close();
          recognizerRef.current = null;
        }
      }
    );
  };

  // STT - Mikrofondan eshitishni to'xtatish va avtomatik tahlilga yuborish (mouseup/touchend)
  const stopListening = () => {
    if (!isListening || !recognizerRef.current) return;
    
    // Recognition'ni to'xtatish
    recognizerRef.current.stopContinuousRecognitionAsync(
      () => {
        console.log("✅ Continuous recognition to'xtatildi");
        
        // Final text'ni olish
        const finalText = childAudioText || childAnswer;
        
        // Recognizer'ni yopish
        if (recognizerRef.current) {
          recognizerRef.current.close();
          recognizerRef.current = null;
        }
        
        setIsListening(false);
        
        // Agar text bo'sh bo'lmasa, avtomatik tahlilga yuborish
        if (finalText && finalText.trim()) {
          console.log("📤 Avtomatik tahlilga yuborilmoqda:", finalText);
          submitAnswerWithSTT(finalText.trim());
        } else {
          console.log("⚠️ Hech narsa eshitilmadi");
          window.appAlert("Hech narsa eshitilmadi. Iltimos qayta urinib ko'ring.");
        }
      },
      (err) => {
        console.error("STT to'xtatish xatosi:", err);
        setIsListening(false);
        if (recognizerRef.current) {
          recognizerRef.current.close();
          recognizerRef.current = null;
        }
      }
    );
  };

  const submitAnswerWithSTT = async (answerText) => {
    if (!answerText.trim()) return;
    
    setLoadingChat(true);
    setAnalysisResult(null);
    
    try {
      // 1. Tahlil qilish
      const analyzeRes = await fetch(`${STORY_API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story_text: storyText,
          question: currentQuestion,
          child_answer: answerText,
          child_audio_text: childAudioText || answerText,
          language: detectedLanguageRef.current?.code || 'uz-UZ'
        }),
      });
      const analyzeData = await analyzeRes.json();
      if (analyzeData.analysis) {
        setAnalysisResult(analyzeData.analysis);
        setAnalyses(prev => [...prev, { question: currentQuestion, analysis: analyzeData.analysis }]);
      }

      // 2. AI rag'batlantirish javobi
      const chatRes = await fetch(`${STORY_API_BASE}/chat-and-ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story_text: storyText,
          question: currentQuestion,
          child_answer: answerText,
          conversation_history: conversationHistory,
          language: detectedLanguageRef.current?.code || 'uz-UZ'
        }),
      });
      const chatData = await chatRes.json();
      if (chatData.ai_response) {
        setAiResponse(chatData.ai_response);
        // AI javobni audio navbatiga qo'shamiz
        setAudioQueue(prev => [...prev, chatData.ai_response]);
        
        // Suhbat tarixini yangilash
        const newHistory = [
          ...conversationHistory,
          { role: "user", content: currentQuestion + " " + answerText },
          { role: "assistant", content: chatData.ai_response },
        ];
        setConversationHistory(newHistory);
        
        // 3. Keyingi savolni yuklash (maksimum 3 ta savol)
        if (questionCount < 3) {
          await loadNextQuestion(newHistory);
        } else {
          // Barcha savollar tugadi
          setIsQuestioningFinished(true);
        }
      }
    } catch (err) {
      console.error("Suhbat xatosi:", err);
      window.appAlert("Suhbatda xatolik yuz berdi");
    } finally {
      setLoadingChat(false);
    }
  };

  const loadNextQuestion = async (history) => {
    setLoadingQuestion(true);
    try {
      const nextQuestionNum = questionCount + 1;
      const res = await fetch(`${STORY_API_BASE}/next-question`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          story_text: storyText, 
          age: age,
          conversation_history: history,
          question_number: nextQuestionNum,
          language: detectedLanguageRef.current?.code || 'uz-UZ'
        }),
      });
      const data = await res.json();
      if (data.question) {
        setCurrentQuestion(data.question);
        setQuestionCount(nextQuestionNum);
        console.log(`✅ ${nextQuestionNum}-savol yuklandi:`, data.question);
        console.log("🌐 Til uchun keyingi savol yuklandi:", detectedLanguageRef.current?.code || 'uz-UZ');
        // ⚠️ Savolni darhol queue'ga qo'shmaymiz, pending qilamiz
        // Audio queue bo'sh bo'lganda avtomatik qo'shiladi
        setPendingQuestion(data.question);
      }
    } catch (err) {
      console.error("Keyingi savol yuklanmadi:", err);
      window.appAlert("Keyingi savol yuklanmadi");
      setIsQuestioningFinished(true);
    } finally {
      setLoadingQuestion(false);
    }
  };

  const nextQuestion = () => {
    // Keyingi savolga o'tish - AI javobidan keyin
    setChildAnswer("");
    setChildAudioText("");
    setAiResponse("");
    setAnalysisResult(null);
    // Savolni qayta aytish (agar kerak bo'lsa)
    // Audio queue'da allaqachon bor, shuning uchun hech narsa qilmaslik kerak
  };

  // ⏸️ Pauzani boshlash
  const pauseReading = () => {
    if (synthesizerRef.current) {
      console.log("⏸️ Pauzada...");
      synthesizerRef.current.close();
      synthesizerRef.current = null;
    }
    // Taymerni to'xtatish (muhim: aks holda keyingi matnga o'tib ketadi)
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    
    isSpeakingRef.current = false;
    setIsSpeaking(false);
  };

  // ▶️ Davom ettirish
  const resumeReading = () => {
    if (audioQueue.length > 0) {
      console.log("▶️ Davom ettirilmoqda...");
      isSpeakingRef.current = false;
      setIsSpeaking(false);
      // Bu yerda speakText ni chaqirish shart emas, chunki useEffect
      // (!isSpeakingRef.current && audioQueue.length > 0) ni ko'rib o'zi chaqiradi
      // Yoki majburan chaqiramiz:
      speakText(audioQueue[0]);
    }
  };

  // 🔄 Qayta o'qishni boshlash
  const restartReading = () => {
    console.log("🔄 Qayta o'qishni boshlash...");
    if (synthesizerRef.current) {
      synthesizerRef.current.close();
      synthesizerRef.current = null;
    }
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    isSpeakingRef.current = false;
    startReading();
  };

  // Audio'ni to'xtatish funksiyasi
  const stopAudio = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (synthesizerRef.current) {
      synthesizerRef.current.close();
      synthesizerRef.current = null;
    }
    isSpeakingRef.current = false;
    setIsSpeaking(false);
    setAudioQueue([]); // Navbatni tozalash
  };

  return (
    <div style={{ lineHeight: "2em", fontFamily: "sans-serif", paddingBottom: "70px" }}>
      {/* Til xatosi ko'rsatish */}
      {languageError && (
        <div style={{
          marginBottom: 20,
          padding: "15px",
          backgroundColor: "#ffebee",
          borderRadius: "5px",
          border: "2px solid #f44336",
          color: "#c62828"
        }}>
          <strong>⚠️ {languageError}</strong>
        </div>
      )}
      
      {/* Aniqlangan til ma'lumoti */}
      {detectedLanguageRef.current && !languageError && (
        <div style={{
          marginBottom: 10,
          padding: "10px 15px",
          backgroundColor: "#e3f2fd",
          borderRadius: "5px",
          border: "1px solid #2196F3",
          color: "#1976d2",
          fontSize: "14px"
        }}>
          🌐 Aniqlangan til: <strong>{detectedLanguageRef.current.name}</strong>
        </div>
      )}
      
      {!readingFinished && (
        <div style={{ marginBottom: 20, display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button 
            onClick={() => {
              if (!isReading && audioQueue.length === 0) {
                startReading();
              } else if (isSpeaking) {
                pauseReading();
              } else {
                resumeReading();
              }
            }} 
            style={{ 
              padding: "10px 20px",
              fontSize: "16px",
              backgroundColor: (!isReading && audioQueue.length === 0) ? "#4CAF50" : (isSpeaking ? "#ff9800" : "#2196F3"),
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
              minWidth: "160px",
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px"
            }}
          >
            {(!isReading && audioQueue.length === 0) ? "🔊 O'qishni boshla" : (isSpeaking ? "⏸️ Pauza" : "▶️ Davom ettirish")}
          </button>

          {(!isReading && audioQueue.length === 0) && (
            <>
              <button 
                  onClick={startSelfReadingMode}
                  style={{
                      padding: "10px 20px",
                      fontSize: "16px",
                      backgroundColor: "#FF5722",
                      color: "white",
                      border: "none",
                      borderRadius: "5px",
                      cursor: "pointer",
                      minWidth: "160px",
                      fontWeight: "bold",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "8px"
                  }}
              >
                  <BookOpen size={20} />
                  O'zim o'qiyman
              </button>

             
            </>
          )}


        </div>
      )}

      {isSpeaking && audioQueue.length > 0 && (
        <div style={{ 
          marginBottom: 10, 
          padding: "10px", 
          backgroundColor: "#e3f2fd", 
          borderRadius: "5px",
          border: "1px solid #2196F3"
        }}>
          <p style={{ margin: 0, color: "#1976d2" }}>
            🗣️ Gapirilmoqda... ({audioQueue.length} qoldi)
          </p>
        </div>
      )}

      <div style={{ 
        fontSize: "1.2em", 
        overflowWrap: "break-word",
        wordBreak: "break-word", 
    marginBottom: 20, 
    lineHeight: "1.8",
    padding: "15px",
    backgroundColor: "#f8f9fa",
    borderRadius: "10px",
    border: "1px solid #dee2e6"
  }}>
    {storyText}
  </div>

  {readingFinished && !isQuestioningFinished && (
    <div style={{ marginTop: 30, padding: 20, backgroundColor: "#f5f5f5", borderRadius: "10px" }}>
      {loadingQuestion ? (
        <p>🔄 Savol yaratilmoqda...</p>
      ) : currentQuestion ? (
        <div>
          <h3 style={{ color: "#333", marginBottom: 15 }}>
            ❓ Savol {questionCount}:
          </h3>
          <p style={{ fontSize: "1.1em", marginBottom: 20, fontWeight: "bold", color: "#555" }}>
            {currentQuestion}
          </p>
          
          <div style={{ marginBottom: 15 }}>
            {/* Eshitilayotgan matn ko'rsatiladi */}
            {isListening && (
              <div style={{
                padding: "15px",
                fontSize: "18px",
                backgroundColor: "#fff3cd",
                borderRadius: "5px",
                border: "2px solid #ff9800",
                marginBottom: 10,
                minHeight: "60px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "10px"
              }}>
                <div style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  backgroundColor: "#f44336",
                  animation: "pulse 1s infinite"
                }}></div>
                <span style={{ fontWeight: "bold", color: "#856404" }}>
                  {childAudioText || "Eshitilmoqda..."}
                </span>
              </div>
            )}
            
            {!isListening && childAudioText && (
              <div style={{
                padding: "15px",
                fontSize: "16px",
                backgroundColor: "#e3f2fd",
                borderRadius: "5px",
                border: "1px solid #2196F3",
                marginBottom: 10,
                color: "#1976d2"
              }}>
                🎤 Eshitildi: "{childAudioText}"
              </div>
            )}
            
            {loadingChat && (
              <div style={{
                padding: "15px",
                fontSize: "16px",
                backgroundColor: "#f5f5f5",
                borderRadius: "5px",
                border: "1px solid #ddd",
                marginBottom: 10,
                textAlign: "center",
                color: "#666"
              }}>
                🔄 Tahlil qilinmoqda...
              </div>
            )}
          </div>
          
          <div style={{ display: "flex", gap: 10, marginBottom: 15, flexWrap: "wrap", justifyContent: "center" }}>
            <button
              onMouseDown={startListening}
              onMouseUp={stopListening}
              onMouseLeave={stopListening}
              onTouchStart={(e) => {
                e.preventDefault();
                startListening();
              }}
              onTouchEnd={(e) => {
                e.preventDefault();
                stopListening();
              }}
              disabled={isSpeakingRef.current || loadingChat}
              style={{
                padding: "15px 30px",
                fontSize: "18px",
                backgroundColor: isListening ? "#f44336" : "#ff9800",
                color: "white",
                border: "none",
                borderRadius: "50px",
                cursor: (isSpeakingRef.current || loadingChat) ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                justifyContent: "center",
                fontWeight: "bold",
                boxShadow: isListening ? "0 4px 15px rgba(244, 67, 54, 0.4)" : "0 4px 15px rgba(255, 152, 0, 0.3)",
                transition: "all 0.2s",
                userSelect: "none",
                WebkitUserSelect: "none"
              }}
            >
              {isListening ? (
                <>
                  <div style={{
                    width: "12px",
                    height: "12px",
                    borderRadius: "50%",
                    backgroundColor: "white",
                    animation: "pulse 1s infinite"
                  }}></div>
                 
                </>
              ) : (
                <>
                  <Mic size={24} />
                  
                </>
              )}
            </button>
          </div>

          {analysisResult && (
            <div style={{ marginTop: 20, padding: 15, backgroundColor: "#fff3cd", borderRadius: "5px", border: "1px solid #ffc107" }}>
              <h4 style={{ marginTop: 0, color: "#856404" }}>📊 Tahlil natijalari:</h4>
              
              {analysisResult.speech_errors && analysisResult.speech_errors.length > 0 && (
                <div style={{ marginBottom: 10 }}>
                  <strong>🔤 Nutq xatolari:</strong>
                  <ul style={{ margin: "5px 0", paddingLeft: 20 }}>
                    {analysisResult.speech_errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {analysisResult.thinking_assessment && (
                <div style={{ marginBottom: 10 }}>
                  <strong>💭 Fikrlash baholash:</strong>
                  <p style={{ margin: "5px 0" }}>{analysisResult.thinking_assessment}</p>
                </div>
              )}
              
              {analysisResult.meaning_analysis && (
                <div style={{ marginBottom: 10 }}>
                  <strong>📝 Ma'no tahlili:</strong>
                  <p style={{ margin: "5px 0" }}>{analysisResult.meaning_analysis}</p>
                </div>
              )}
              
              {analysisResult.character_recall && (
                <div style={{ marginBottom: 10 }}>
                  <strong>👥 Qahramonlarni eslash:</strong>
                  <p style={{ margin: "5px 0" }}>{analysisResult.character_recall}</p>
                </div>
              )}
              
              {analysisResult.character_distinction && (
                <div style={{ marginBottom: 10 }}>
                  <strong>⚖️ Qahramonlarni ajratish:</strong>
                  <p style={{ margin: "5px 0" }}>{analysisResult.character_distinction}</p>
                </div>
              )}
            </div>
          )}
          
          {aiResponse && (
            <div style={{ marginTop: 20, padding: 15, backgroundColor: "#e3f2fd", borderRadius: "5px" }}>
              <p style={{ margin: 0, color: "#1976d2" }}>{aiResponse}</p>
              {!loadingQuestion && questionCount < 3 && (
                <button
                  onClick={nextQuestion}
                  disabled={isSpeakingRef.current || loadingQuestion}
                  style={{
                    marginTop: 15,
                    padding: "8px 16px",
                    fontSize: "14px",
                    backgroundColor: (isSpeakingRef.current || loadingQuestion) ? "#ccc" : "#4CAF50",
                    color: "white",
                    border: "none",
                    borderRadius: "5px",
                    cursor: (isSpeakingRef.current || loadingQuestion) ? "not-allowed" : "pointer"
                  }}
                >
                  ➡️ Keyingi savol
                </button>
              )}
            </div>
          )}
        </div>
      ) : null}
    </div>
  )}

  {isQuestioningFinished && (
    <div style={{ marginTop: 30, padding: 20, backgroundColor: "#e8f5e9", borderRadius: "10px", textAlign: "center" }}>
      <h3 style={{ color: "#4CAF50", marginBottom: 15 }}>🎉 Rahmat!</h3>
      <p style={{ fontSize: "18px", marginBottom: 10 }}>Siz ajoyib javob berdingiz! Ertakni juda yaxshi tushundingiz.</p>
      <p style={{ color: "#666", marginBottom: 20 }}>Yana o'qimoqchimisiz?</p>
      
      <button
        onClick={() => {
          window.location.reload();
        }}
        style={{
          padding: "12px 24px",
          fontSize: "16px",
          backgroundColor: "#4CAF50",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          fontWeight: "bold"
        }}
      >
        📄 Yangi fayl yuklash
      </button>
    </div>
  )}

  {/* Camera Modal */}
  {showCamera && (
    <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'black',
        zIndex: 2000,
        display: 'flex',
        flexDirection: 'column'
    }}>
      {!capturedImage ? (
        <>
          <video 
            ref={videoRef}
            autoPlay
            playsInline
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />
          
          <div style={{
            position: 'absolute',
            top: 20,
            right: 20,
            display: 'flex',
            gap: '10px'
          }}>
            <button
              onClick={switchCamera}
              style={{
                padding: '15px',
                backgroundColor: 'rgba(255,255,255,0.3)',
                border: 'none',
                borderRadius: '50%',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <RotateCw size={24} color="white" />
            </button>
            
            <button
              onClick={stopCamera}
              style={{
                padding: '15px',
                backgroundColor: 'rgba(255,255,255,0.3)',
                border: 'none',
                borderRadius: '50%',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <X size={24} color="white" />
            </button>
          </div>

          <button
            onClick={capturePhoto}
            style={{
              position: 'absolute',
              bottom: 40,
              left: '50%',
              transform: 'translateX(-50%)',
              width: '80px',
              height: '80px',
              backgroundColor: 'white',
              border: '5px solid rgba(255,255,255,0.5)',
              borderRadius: '50%',
              cursor: 'pointer',
              boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
            }}
          >
            <Camera size={32} color="black" />
          </button>
        </>
      ) : (
        <>
          <img 
            src={capturedImage}
            alt="Captured"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain'
            }}
          />
          
          <div style={{
            position: 'absolute',
            bottom: 40,
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '20px'
          }}>
            <button
              onClick={retakePhoto}
              style={{
                padding: '15px 30px',
                fontSize: '18px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '50px',
                cursor: 'pointer',
                fontWeight: 'bold',
                boxShadow: '0 4px 15px rgba(244, 67, 54, 0.3)'
              }}
            >
              🔄 Qayta
            </button>
            
            <button
              onClick={savePhoto}
              style={{
                padding: '15px 30px',
                fontSize: '18px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '50px',
                cursor: 'pointer',
                fontWeight: 'bold',
                boxShadow: '0 4px 15px rgba(76, 175, 80, 0.3)'
              }}
            >
              💾 Saqlash
            </button>
          </div>
        </>
      )}
    </div>
  )}

  {/* Hidden canvas for photo capture */}
  <canvas ref={canvasRef} style={{ display: 'none' }} />

  {/* Self Reading Modal */}
  {showSelfReadModal && (
    <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.9)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
    }}>
        <div style={{
            backgroundColor: 'white',
            borderRadius: '20px',
            padding: '30px',
            maxWidth: '800px',
            width: '100%',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            overflowY: 'auto'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ margin: 0, color: '#333' }}>📖 Matnni o'qing</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {isListening && <div style={{ color: 'red', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'red', animation: 'pulse 1s infinite' }}></div>
                        Eshitilmoqda...
                    </div>}
                    <button
                        onClick={() => {
                            setShowSelfReadModal(false);
                            setIsSelfReading(false);
                            setIsListening(false);
                            if (speechRecognizerRef.current) {
                                speechRecognizerRef.current.stopContinuousRecognitionAsync(() => {
                                    speechRecognizerRef.current.close();
                                    speechRecognizerRef.current = null;
                                });
                            }
                        }}
                        style={{
                            background: 'none',
                            border: 'none',
                            fontSize: '24px',
                            cursor: 'pointer',
                            color: '#666',
                            padding: '5px'
                        }}
                    >
                        ❌
                    </button>
                </div>
            </div>

            <div style={{
                fontSize: '24px',
                lineHeight: '1.6',
                padding: '20px',
                backgroundColor: '#fafafa',
                borderRadius: '10px',
                border: '1px solid #eee',
                whiteSpace: 'pre-wrap'
            }}>
                {storyText}
            </div>

            {!readingAnalysisResult ? (
                <div style={{ display: 'flex', justifyContent: 'center', gap: '20px' }}>
                    {analyzingReading ? (
                         <div style={{ textAlign: 'center' }}>
                             <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                             <p>AI o'qishni tahlil qilmoqda...</p>
                         </div>
                    ) : (
                        isListening ? (
                            <button
                                onClick={finishSelfReading}
                                style={{
                                    padding: '15px 40px',
                                    fontSize: '20px',
                                    backgroundColor: '#f44336',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '50px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    fontWeight: 'bold',
                                    boxShadow: '0 4px 15px rgba(244, 67, 54, 0.3)'
                                }}
                            >
                                <StopCircle size={24} />
                                Tugatdim
                            </button>
                        ) : (
                            <button
                                onClick={startSelfReadingListener}
                                style={{
                                    padding: '15px 40px',
                                    fontSize: '20px',
                                    backgroundColor: '#4CAF50',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '50px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    fontWeight: 'bold',
                                    boxShadow: '0 4px 15px rgba(76, 175, 80, 0.3)'
                                }}
                            >
                                <Mic size={24} />
                                Davom ettirish
                            </button>
                        )
                    )}
                </div>
            ) : (
                <div style={{ animation: 'fadeIn 0.5s ease-in' }}>
                    <h3 style={{ color: '#2196F3', textAlign: 'center' }}>📊 Tahlil Natijasi</h3>
                    <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                        gap: '15px',
                        margin: '20px 0'
                    }}>
                         <div style={{ padding: '15px', background: '#e3f2fd', borderRadius: '10px' }}>
                             <strong>Aniqlik:</strong>
                             <div style={{ fontSize: '24px', color: '#1976d2', fontWeight: 'bold' }}>
                                 {readingAnalysisResult.accuracy_score || 0}%
                             </div>
                         </div>
                         <div style={{ padding: '15px', background: '#fff3cd', borderRadius: '10px' }}>
                             <strong>Talaffuz:</strong>
                             <p style={{ margin: '5px 0', fontSize: '14px' }}>{readingAnalysisResult.pronunciation_feedback}</p>
                         </div>
                         <div style={{ padding: '15px', background: '#e8f5e9', borderRadius: '10px' }}>
                             <strong>Ravonlik:</strong>
                             <p style={{ margin: '5px 0', fontSize: '14px' }}>{readingAnalysisResult.fluency_feedback}</p>
                         </div>
                    </div>
                    
                    <div style={{ textAlign: 'center' }}>
                        <button
                            onClick={closeSelfReadingAndStartQuestions}
                            style={{
                                padding: '15px 40px',
                                fontSize: '20px',
                                backgroundColor: '#2196F3',
                                color: 'white',
                                border: 'none',
                                borderRadius: '50px',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                fontWeight: 'bold',
                                margin: '0 auto'
                            }}
                        >
                            <CheckCircle size={24} />
                            Savollar bilan davom etish
                        </button>
                    </div>
                </div>
            )}
        </div>
    </div>
  )}

  <style>{`
    @keyframes loading {
      0% { width: 0%; }
      50% { width: 50%; }
      100% { width: 100%; }
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
  `}</style>
</div>

);
}