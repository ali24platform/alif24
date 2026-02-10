import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import {
  Users,
  BookOpen,
  TrendingUp,
  Award,
  Calendar,
  Settings,
  LogOut,
  Shield,
  GraduationCap,
  Home,
  FileText,
  Bell,
  BarChart3
} from 'lucide-react';

const DashboardLayout = ({ children }) => {
  const { user, logout, isSuperAdmin, isAdmin, isTeacher, isParent, isStudent, isOrganization } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();

  const getNavigation = () => {
    if (isSuperAdmin || isAdmin) {
      return [
        { icon: <Home className="w-5 h-5" />, label: t('home') || 'Bosh sahifa', href: '/organization-dashboard' },
        { icon: <TrendingUp className="w-5 h-5" />, label: 'CRM Lidlar', href: '/crm' },
        { icon: <Users className="w-5 h-5" />, label: t('nav_users') || 'Foydalanuvchilar', href: '/organization-dashboard' },
        { icon: <BarChart3 className="w-5 h-5" />, label: t('nav_analytics') || 'Statistika', href: '/organization-dashboard' },
      ];
    }

    if (isOrganization) {
      return [
        { icon: <Home className="w-5 h-5" />, label: "Bosh sahifa", href: '/organization-dashboard' },
        { icon: <TrendingUp className="w-5 h-5" />, label: 'CRM / Lidlar', href: '/crm' },
        { icon: <Users className="w-5 h-5" />, label: "O'qituvchilar", href: '/organization-dashboard' },
        { icon: <BookOpen className="w-5 h-5" />, label: "Materiallar", href: '/organization-dashboard' },
      ];
    }

    if (isTeacher) {
      return [
        { icon: <Home className="w-5 h-5" />, label: t('home') || 'Bosh sahifa', href: '/teacher-dashboard' },
        { icon: <BookOpen className="w-5 h-5" />, label: t('nav_my_courses') || 'Darslarim', href: '/lesson-builder' },
        { icon: <FileText className="w-5 h-5" />, label: t('nav_assignments') || 'Testlar', href: '/teacher/test-ai' },
        { icon: <GraduationCap className="w-5 h-5" />, label: "O'quvchilar", href: '/teacher-dashboard' },
        { icon: <Calendar className="w-5 h-5" />, label: t('calendar') || 'Jadval', href: '/teacher-dashboard' },
      ];
    }

    if (isParent) {
      return [
        { icon: <Home className="w-5 h-5" />, label: t('home') || 'Bosh sahifa', href: '/parent-dashboard' },
        { icon: <GraduationCap className="w-5 h-5" />, label: "Farzandlarim", href: '/parent-dashboard' },
        { icon: <BarChart3 className="w-5 h-5" />, label: "Hisobotlar", href: '/parent-dashboard' },
        { icon: <Bell className="w-5 h-5" />, label: "Bildirishnomalar", href: '/parent-dashboard' },
      ];
    }

    if (isStudent) {
      return [
        { icon: <Home className="w-5 h-5" />, label: t('home') || 'Bosh sahifa', href: '/student-dashboard' },
        { icon: <BookOpen className="w-5 h-5" />, label: "Darslarim", href: '/student-dashboard' },
        { icon: <Award className="w-5 h-5" />, label: "Yutuqlarim", href: '/student-dashboard' },
        { icon: <BarChart3 className="w-5 h-5" />, label: "Statistika", href: '/student-dashboard' },
      ];
    }

    return [];
  };

  const getRoleInfo = () => {
    if (isOrganization) {
      return {
        label: "Ta'lim tashkiloti",
        icon: <Shield className="w-6 h-6" />,
        color: 'bg-purple-100 text-purple-800'
      };
    }
    if (isSuperAdmin) {
      return {
        label: 'Super Admin',
        icon: <Shield className="w-6 h-6" />,
        color: 'bg-purple-100 text-purple-800'
      };
    }
    if (isAdmin) {
      return {
        label: 'Admin',
        icon: <Shield className="w-6 h-6" />,
        color: 'bg-blue-100 text-blue-800'
      };
    }
    if (isTeacher) {
      return {
        label: t('auth_role_teacher'),
        icon: <GraduationCap className="w-6 h-6" />,
        color: 'bg-green-100 text-green-800'
      };
    }
    if (isParent) {
      return {
        label: t('auth_role_parent'),
        icon: <Users className="w-6 h-6" />,
        color: 'bg-orange-100 text-orange-800'
      };
    }
    if (isStudent) {
      return {
        label: t('auth_role_student'),
        icon: <BookOpen className="w-6 h-6" />,
        color: 'bg-indigo-100 text-indigo-800'
      };
    }
    return { label: 'User', icon: <Users className="w-6 h-6" />, color: 'bg-gray-100 text-gray-800' };
  };

  const navigation = getNavigation();
  const roleInfo = getRoleInfo();

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-lg">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className={`p-2 rounded-full ${roleInfo.color}`}>
              {roleInfo.icon}
            </div>
            <div>
              <div className="font-semibold text-gray-900">{user?.first_name} {user?.last_name}</div>
              <div className="text-sm text-gray-500">{roleInfo.label}</div>
            </div>
          </div>

          <nav className="space-y-1">
            {navigation.map((item, index) => (
              <button
                key={index}
                onClick={() => navigate(item.href)}
                className={`flex items-center gap-3 px-4 py-3 w-full text-left rounded-lg transition-colors ${
                  location.pathname === item.href
                    ? 'bg-indigo-50 text-indigo-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="absolute bottom-0 w-64 p-6 border-t">
          <button
            onClick={logout}
            className="flex items-center gap-3 w-full px-4 py-3 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>{t('logout')}</span>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="px-6 py-4 flex items-center justify-between">
            <h1 className="text-xl font-semibold text-gray-900">
              {roleInfo.label} paneli
            </h1>
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-indigo-600">
                    {user?.first_name?.[0]}{user?.last_name?.[0]}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
