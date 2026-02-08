import React, { useState } from 'react';
import { 
  Users, 
  BookOpen, 
  ClipboardList, 
  BarChart3, 
  MessageSquare, 
  Settings,
  Plus,
  FileText,
  Calendar,
  Award,
  Video,
  Bell,
  Menu,
  X,
  ChevronRight,
  Home,
  Upload,
  Download,
  CheckCircle,
  Clock,
  UserPlus,
  Folder,
  TrendingUp
} from 'lucide-react';
import TestAIPage from '../modules/testai/pages/TestAIPage';

const TeacherDashboard = () => {
  const [activeSection, setActiveSection] = useState('home');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Menu kategoriyalari
  const menuCategories = [
    {
      id: 'class-management',
      title: 'Sinf Ma\'muriyati',
      icon: Users,
      color: 'bg-blue-500',
      items: [
        { id: 'create-class', label: 'Sinf Yaratish', icon: Plus },
        { id: 'manage-students', label: 'O\'quvchilarni Boshqarish', icon: UserPlus },
        { id: 'parents-connection', label: 'Ota-onalar Bilan Bog\'lanish', icon: Users },
      ]
    },
    {
      id: 'academic',
      title: 'Akademik Reja',
      icon: BookOpen,
      color: 'bg-green-500',
      items: [
        { id: 'topic-plans', label: 'Mavzu Rejalari', icon: Calendar },
        { id: 'lesson-materials', label: 'Dars Materiallari', icon: Upload },
        { id: 'resource-library', label: 'Resurslar Kutubxonasi', icon: Folder },
        { id: 'final-exam', label: 'Yakuniy Nazorat', icon: Award },
      ]
    },
    {
      id: 'homework',
      title: 'Uy Vazifasi',
      icon: ClipboardList,
      color: 'bg-purple-500',
      items: [
        { id: 'create-task', label: 'Topshiriq Yaratish', icon: Plus },
        { id: 'auto-send', label: 'Avtomatik Yuborish', icon: Upload },
        { id: 'collect-grade', label: 'Yig\'ish va Baholash', icon: CheckCircle },
        { id: 'plagiarism', label: 'Plagiatni Tekshirish', icon: FileText },
      ]
    },
    {
      id: 'assessment',
      title: 'Baholash va Monitoring',
      icon: BarChart3,
      color: 'bg-orange-500',
      items: [
        { id: 'journal', label: 'Elektron Jurnal', icon: BookOpen },
        { id: 'statistics', label: 'Statistika va Hisobotlar', icon: TrendingUp },
        { id: 'attendance', label: 'Davomat Nazorati', icon: Clock },
        { id: 'certificates', label: 'Sertifikat Yaratish', icon: Award },
      ]
    },
    {
      id: 'communication',
      title: 'Aloqa va Hamkorlik',
      icon: MessageSquare,
      color: 'bg-pink-500',
      items: [
        { id: 'announcements', label: 'E\'lonlar Paneli', icon: Bell },
        { id: 'forums', label: 'Muhokama Forumlari', icon: MessageSquare },
        { id: 'private-messages', label: 'Shaxsiy Xabarlar', icon: MessageSquare },
        { id: 'video-conference', label: 'Videokonferensiya', icon: Video },
      ]
    },
    {
      id: 'personalization',
      title: 'Shaxsiylashtirish',
      icon: Settings,
      color: 'bg-indigo-500',
      items: [
        { id: 'individual-plans', label: 'Individual Rejalar', icon: FileText },
        { id: 'goals', label: 'Maqsadlar', icon: TrendingUp },
      ]
    },
    {
      id: 'system',
      title: 'Tizim va Yordam',
      icon: Settings,
      color: 'bg-gray-500',
      items: [
        { id: 'notifications', label: 'Bildirishnomalar', icon: Bell },
        { id: 'profile', label: 'Profil Sozlamalari', icon: Settings },
        { id: 'help', label: 'Yordam Markazi', icon: MessageSquare },
        { id: 'test-ai', label: 'Test AI', icon: FileText },
      ]
    }
  ];

  const renderContent = () => {
    // Test AI sahifasini ko'rsatish
    if (activeSection === 'test-ai') {
      return <TestAIPage />;
    }

    // Boshqa sahifalar uchun placeholder
    return (
      <div className="p-4">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">
            {menuCategories
              .flatMap(cat => cat.items)
              .find(item => item.id === activeSection)?.label || 'Bosh Sahifa'}
          </h2>
          <p className="text-gray-600 mb-4">
            Bu yerda "{activeSection}" uchun kontent bo'ladi.
          </p>
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
            <p className="text-sm text-blue-700">
              💡 Har bir bo'lim uchun alohida komponent yaratib, bu yerga import qilishingiz mumkin.
            </p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="bg-white shadow-md sticky top-0 z-50">
        <div className="flex items-center justify-between p-4">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <h1 className="text-lg font-bold text-gray-800">O'qituvchi Paneli</h1>
          <button className="p-2 hover:bg-gray-100 rounded-lg relative">
            <Bell size={24} />
            <span className="absolute top-1 right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              3
            </span>
          </button>
        </div>
      </div>

      {/* Sidebar Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 h-full w-80 bg-white shadow-lg z-50 transform transition-transform duration-300 overflow-y-auto ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800">Menu</h2>
            <button onClick={() => setIsSidebarOpen(false)}>
              <X size={24} />
            </button>
          </div>
          
          {/* Home button */}
          <button
            onClick={() => {
              setActiveSection('home');
              setIsSidebarOpen(false);
            }}
            className={`w-full flex items-center gap-3 p-3 rounded-lg mb-2 ${
              activeSection === 'home' ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'
            }`}
          >
            <Home size={20} />
            <span className="font-medium">Bosh Sahifa</span>
          </button>
        </div>

        {/* Menu Categories */}
        <div className="p-4 space-y-4">
          {menuCategories.map((category) => (
            <div key={category.id} className="space-y-2">
              <div className="flex items-center gap-2 text-gray-500 text-sm font-semibold uppercase">
                <category.icon size={16} />
                <span>{category.title}</span>
              </div>
              
              <div className="space-y-1">
                {category.items.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveSection(item.id);
                      setIsSidebarOpen(false);
                    }}
                    className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors ${
                      activeSection === item.id
                        ? `${category.color} text-white`
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon size={18} />
                      <span className="text-sm font-medium">{item.label}</span>
                    </div>
                    <ChevronRight size={16} />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="pb-20">
        {renderContent()}
      </div>

      {/* Bottom Navigation (Mobile) */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-40">
        <div className="grid grid-cols-5 gap-1 p-2">
          {[
            { id: 'home', icon: Home, label: 'Bosh' },
            { id: 'class-management', icon: Users, label: 'Sinf' },
            { id: 'homework', icon: ClipboardList, label: 'Vazifa' },
            { id: 'assessment', icon: BarChart3, label: 'Baholash' },
            { id: 'communication', icon: MessageSquare, label: 'Aloqa' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                if (item.id === 'home') {
                  setActiveSection('home');
                } else {
                  setActiveSection(item.id);
                  setIsSidebarOpen(true);
                }
              }}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg ${
                activeSection === item.id
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-600'
              }`}
            >
              <item.icon size={20} />
              <span className="text-xs font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;