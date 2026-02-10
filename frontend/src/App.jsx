import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './context/LanguageContext';
import { AuthProvider } from './context/AuthContext';
import {
  HomePage,
  AboutPage,
  PartnerPage,
  ProfilePageTeacher,
  OrganizationPage,
  TeacherDashboard,
  StudentDashboard,
  ParentDashboard,
  LessonPage,
  LessonBuilder,
  TestAIPage
} from './pages';
import CRMPage from './pages/crm/CRMPage';
import Harf from './harf/Harf';
import Harfr from './rharf/Harfr';
import Eharf from './eharf/Eharf';
import LetterMemoryGame from './lessiongames/LetterMemoryGame';
import MathMonsterGame from './mathgames/MathMonsterGame';
import KidsReadingPlatformMobile from './ertak/ertak';
import SmartKidsAI from './pages/SmartKidsAI';
import MathKidsAI from './pages/MathKidsAI';
import DashboardLayout from './components/Dashboard/DashboardLayout';
import LiveQuizStudent from './pages/LiveQuizStudent';
import LiveQuizTeacher from './pages/LiveQuizTeacher';
import OlympiadPage from './pages/OlympiadPage';
import TestCreator from './test/TestCreator';
import SmartAuthPrompt from './components/Auth/SmartAuthPrompt';
import LoginModal from './components/Auth/LoginModal';
import RegisterModal from './components/Auth/RegisterModal';
import OrganizationDashboard from './pages/OrganizationDashboard';
import SecretAdminLogin from './pages/SecretAdminLogin';
import ProtectedRoute from './components/Auth/ProtectedRoute';

import ErrorBoundary from './components/Common/ErrorBoundary';
import ToastManager from './components/Common/ToastManager';

/**
 * Main App Component
 */
const App = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <LanguageProvider>
          <AuthProvider>
            <ToastManager />
            <AppRoutes />
          </AuthProvider>
        </LanguageProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

/**
 * App Routes
 */
const AppRoutes = () => {
  return (
    <Routes>
      {/* Home Page - Direct entry point */}
      <Route path="/" element={<HomePage />} />

      {/* Child Dashboard - With Navbar */}
      <Route path="/dashboard" element={<HomePage />} />

      {/* Info Pages - With Navbar */}
      <Route path="/about" element={<AboutPage />} />
      <Route path="/partners" element={<PartnerPage />} />

      {/* Profile and Dashboards - PROTECTED */}
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePageTeacher />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher-dashboard"
        element={
          <ProtectedRoute allowedRoles={['teacher', 'organization', 'moderator']}>
            <TeacherDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/parent-dashboard"
        element={
          <ProtectedRoute allowedRoles={['parent', 'organization', 'moderator']}>
            <ParentDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student-dashboard"
        element={
          <ProtectedRoute allowedRoles={['student', 'organization', 'moderator']}>
            <StudentDashboard />
          </ProtectedRoute>
        }
      />

      {/* Smart Lesson Route */}
      <Route
        path="/lesson/:id"
        element={
          <ProtectedRoute allowedRoles={['student', 'organization', 'moderator']}>
            <LessonPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/lesson-builder"
        element={
          <ProtectedRoute allowedRoles={['teacher', 'organization', 'moderator']}>
            <LessonBuilder />
          </ProtectedRoute>
        }
      />

      <Route
        path="/test-creator"
        element={
          <ProtectedRoute allowedRoles={['teacher', 'organization', 'moderator']}>
            <TestCreator />
          </ProtectedRoute>
        }
      />

      {/* Organization Page - PROTECTED */}
      <Route
        path="/organization"
        element={
          <ProtectedRoute allowedRoles={['organization', 'moderator']}>
            <OrganizationPage />
          </ProtectedRoute>
        }
      />

      {/* Harf learning page */}
      <Route path="/harf" element={<Harf />} />
      <Route path="/rharf" element={<Harfr />} />
      <Route path="/eharf" element={<Eharf />} />

      {/* Games */}
      <Route path="/games/letter-memory" element={<LetterMemoryGame />} />
      <Route path="/games/math-monster" element={<MathMonsterGame />} />
      <Route path="/ertak" element={<KidsReadingPlatformMobile />} />

      {/* SmartKids AI */}
      <Route path="/smartkids-ai" element={<SmartKidsAI />} />

      {/* Live Quiz */}
      <Route path="/join-quiz" element={
        <ProtectedRoute allowedRoles={['student', 'organization', 'moderator']}>
          <LiveQuizStudent />
        </ProtectedRoute>
      } />
      <Route path="/live-quiz/create" element={
        <ProtectedRoute allowedRoles={['teacher', 'organization', 'moderator']}>
          <LiveQuizTeacher />
        </ProtectedRoute>
      } />

      {/* Olympiad */}
      <Route path="/olympiad" element={
        <ProtectedRoute allowedRoles={['student', 'parent', 'teacher', 'organization', 'moderator']}>
          <OlympiadPage />
        </ProtectedRoute>
      } />

      {/* MathKids AI */}
      <Route path="/mathkids-ai" element={<MathKidsAI />} />

      {/* Organization Dashboard - PROTECTED */}
      <Route
        path="/organization-dashboard"
        element={
          <ProtectedRoute allowedRoles={['organization', 'moderator', 'admin']}>
            <OrganizationDashboard />
          </ProtectedRoute>
        }
      />

      {/* CRM Page - Organization/Moderator */}
      <Route
        path="/crm"
        element={
          <ProtectedRoute allowedRoles={['organization', 'moderator', 'admin']}>
            <CRMPage />
          </ProtectedRoute>
        }
      />

      {/* TestAI Platform - Teacher Only */}
      <Route
        path="/teacher/test-ai"
        element={
          <ProtectedRoute allowedRoles={['teacher', 'organization', 'moderator']}>
            <TestAIPage />
          </ProtectedRoute>
        }
      />

      {/* Secret Admin Routes - Only accessible via direct URL */}
      <Route path="/nurali" element={<SecretAdminLogin />} />
      <Route path="/hazratqul" element={<SecretAdminLogin />} />
      <Route path="/pedagog" element={<SecretAdminLogin />} />

      {/* 404 Route */}
      <Route
        path="*"
        element={
          <div className="not-found" style={{
            textAlign: 'center',
            padding: '100px 20px',
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            color: '#ffffff'
          }}>
            <h1 style={{ fontSize: '3rem', marginBottom: '20px' }}>404</h1>
            <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.7)' }}>
              Sahifa topilmadi
            </p>
          </div>
        }
      />
    </Routes>
  );
};

export default App;
