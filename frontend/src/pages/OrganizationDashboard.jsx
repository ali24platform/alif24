import React, { useState, useEffect } from 'react';
import {
    Users, TrendingUp, BookOpen, Activity,
    Search, Filter, RefreshCw, Eye, Lock,
    FileText, Calendar, Plus, Trash2, Upload, MessageSquare
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import organizationService from '../services/organizationService';
import crmService from '../services/crmService';
import CRMBoard from '../components/crm/CRMBoard';

const OrganizationDashboard = () => {
    const { user, logout } = useAuth();
    const [stats, setStats] = useState(null);
    const [usersList, setUsersList] = useState([]);
    const [teachers, setTeachers] = useState([]);
    const [materials, setMaterials] = useState([]);
    const [analyses, setAnalyses] = useState([]);
    const [leads, setLeads] = useState([]); // CRM Leads

    const [activeTab, setActiveTab] = useState('stats');
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState('');

    // Modal states
    const [showAddTeacherModal, setShowAddTeacherModal] = useState(false);
    const [teacherIdToAdd, setTeacherIdToAdd] = useState('');

    const [showInviteStudentModal, setShowInviteStudentModal] = useState(false);
    const [inviteStudentData, setInviteStudentData] = useState({ name: '', phone: '', email: '' });

    const [showUploadModal, setShowUploadModal] = useState(false);
    const [uploadTitle, setUploadTitle] = useState('');
    const [uploadFileUrl, setUploadFileUrl] = useState('');

    // Load Data
    const loadData = async () => {
        setLoading(true);
        try {
            const [statsData, teachersData, materialsData, usersData, leadsData] = await Promise.all([
                organizationService.getStats().catch(err => null),
                organizationService.getTeachers().catch(err => []),
                organizationService.getMaterials().catch(err => []),
                organizationService.getUsers().catch(err => ({ users: [] })),
                crmService.getLeads().catch(err => [])
            ]);

            if (statsData) setStats(statsData);
            if (teachersData) setTeachers(teachersData);
            if (materialsData) setMaterials(materialsData);
            if (usersData && usersData.users) setUsersList(usersData.users);
            if (leadsData) setLeads(leadsData);

            // Analysis data (mock or fetch if available)
            // const analysesData = await organizationService.getReadingAnalyses();
            // setAnalyses(analysesData.analyses || []);

        } catch (error) {
            console.error('Load error:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    // Handlers
    const handleInviteStudent = async (e) => {
        e.preventDefault();
        try {
            await organizationService.inviteStudent(inviteStudentData);
            setShowInviteStudentModal(false);
            setInviteStudentData({ name: '', phone: '', email: '' });
            loadData();
            alert("O'quvchi muvaffaqiyatli taklif qilindi. Login ma'lumotlari yuborildi.");
        } catch (error) {
            alert("Xatolik: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleCRMStatusChange = async (leadId, newStatus) => {
        try {
            await crmService.updateLead(leadId, { status: newStatus });
            setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: newStatus } : l));
        } catch (error) {
            console.error("CRM Update failed", error);
            loadData();
        }
    };

    const handleCRMDelete = async (leadId) => {
        if (!window.confirm("O'chirmoqchimisiz?")) return;
        try {
            await crmService.deleteLead(leadId);
            setLeads(prev => prev.filter(l => l.id !== leadId));
        } catch (error) {
            alert("O'chirib bo'lmadi");
        }
    };

    const handleAddTeacher = async (e) => {
        e.preventDefault();
        try {
            await organizationService.addTeacher(teacherIdToAdd);
            setShowAddTeacherModal(false);
            setTeacherIdToAdd('');
            loadData(); // Refresh
            alert('Teacher added successfully');
        } catch (error) {
            alert('Error adding teacher: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleRemoveTeacher = async (id) => {
        if (!window.confirm('Are you sure you want to remove this teacher?')) return;
        try {
            await organizationService.removeTeacher(id);
            loadData();
        } catch (error) {
            alert('Error removing teacher');
        }
    };

    const handleUploadMaterial = async (e) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append('title', uploadTitle);
            formData.append('file_url', uploadFileUrl);

            await organizationService.uploadMaterial(formData);
            setShowUploadModal(false);
            setUploadTitle('');
            setUploadFileUrl('');
            loadData();
            alert('Material uploaded successfully');
        } catch (error) {
            alert('Error uploading material');
        }
    };

    // Filter Users
    const filteredUsers = usersList.filter(u => {
        const matchesSearch = u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            u.email.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesRole = !roleFilter || u.role === roleFilter;
        return matchesSearch && matchesRole;
    });

    const getRoleName = (role) => {
        const roles = {
            'student': 'O‘quvchi',
            'teacher': 'O‘qituvchi',
            'parent': 'Ota-ona',
            'organization': 'Ta’lim tashkiloti',
            'moderator': 'Moderator'
        };
        return roles[role] || role;
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Ta’lim tashkiloti Paneli</h1>
                            <p className="text-sm text-gray-600">{user?.name} | {user?.email}</p>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={loadData}
                                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
                            >
                                <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                                Yangilash
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Tabs */}
                <div className="bg-white rounded-lg shadow-sm mb-6">
                    <div className="border-b border-gray-200">
                        <nav className="flex gap-8 px-6 overflow-x-auto">
                            {[
                                { key: 'stats', label: 'Statistika', icon: TrendingUp },
                                { key: 'crm', label: 'CRM / Lidlar', icon: MessageSquare }, // New CRM Tab
                                { key: 'teachers', label: 'O‘qituvchilar', icon: Users },
                                { key: 'materials', label: 'Content Box', icon: BookOpen },
                                { key: 'schedule', label: 'Dars Jadvali', icon: Calendar },
                                { key: 'users', label: 'Barcha Foydalanuvchilar', icon: Users },
                            ].map(tab => (
                                <button
                                    key={tab.key}
                                    onClick={() => setActiveTab(tab.key)}
                                    className={`flex items-center gap-2 py-4 px-2 border-b-2 font-medium transition-colors whitespace-nowrap ${activeTab === tab.key
                                        ? 'border-blue-500 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700'
                                        }`}
                                >
                                    <tab.icon size={20} />
                                    {tab.label}
                                </button>
                            ))}
                        </nav>
                    </div>
                </div>

                {/* --- STATS TAB --- */}
                {activeTab === 'stats' && stats && (
                    <div className="space-y-6">
                        {/* Users Stats */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-6">📊 Umumiy Statistika</h2>
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                <StatCard label="Jami Foydalanuvchilar" value={stats.users?.total || 0} icon="👥" color="blue" />
                                <StatCard label="Faol Lidlar" value={leads.length} icon="📈" color="orange" />
                                <StatCard label="O'quvchilar" value={stats.users?.students || 0} icon="👨‍🎓" color="green" />
                                <StatCard label="O'qituvchilar" value={stats.users?.teachers || 0} icon="👨‍🏫" color="purple" />
                            </div>
                        </div>

                        {/* Quick CRM View */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h3 className="text-lg font-bold mb-4">So'nggi Lidlar</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="text-left text-xs uppercase text-gray-500 bg-gray-50">
                                            <th className="p-3">Ism</th>
                                            <th className="p-3">Telefon</th>
                                            <th className="p-3">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {leads.slice(0, 5).map(lead => (
                                            <tr key={lead.id} className="border-t">
                                                <td className="p-3">{lead.first_name} {lead.last_name}</td>
                                                <td className="p-3">{lead.phone}</td>
                                                <td className="p-3">
                                                    <span className={`px-2 py-1 rounded text-xs ${lead.status === 'new' ? 'bg-blue-100 text-blue-800' :
                                                        lead.status === 'won' ? 'bg-green-100 text-green-800' : 'bg-gray-100'
                                                        }`}>{lead.status}</span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* --- CRM TAB --- */}
                {activeTab === 'crm' && (
                    <div className="h-[calc(100vh-200px)]">
                        <CRMBoard
                            leads={leads}
                            onStatusChange={handleCRMStatusChange}
                            onEdit={(lead) => console.log("Edit lead", lead)} // TODO: Implement full edit
                            onDelete={handleCRMDelete}
                        />
                    </div>
                )}

                {/* --- TEACHERS TAB --- */}
                {activeTab === 'teachers' && (
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-gray-900">Mening O'qituvchilarim</h2>
                            <button
                                onClick={() => setShowAddTeacherModal(true)}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                            >
                                <Plus size={18} /> O'qituvchi Qo'shish
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ism</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Malaka</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                        <th className="px-6 py-3 text-right">Amallar</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {teachers.map(teacher => (
                                        <tr key={teacher.id}>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="text-sm font-medium text-gray-900">
                                                    {teacher.user?.first_name} {teacher.user?.last_name}
                                                </div>
                                                <div className="text-xs text-gray-500">{teacher.user?.email}</div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {teacher.qualification || '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                                                    {teacher.verification_status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <button
                                                    onClick={() => handleRemoveTeacher(teacher.id)}
                                                    className="text-red-600 hover:text-red-900"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {teachers.length === 0 && (
                                <div className="text-center p-8 text-gray-500">O'qituvchilar ro'yxati bo'sh</div>
                            )}
                        </div>
                    </div>
                )}

                {/* --- MATERIALS TAB --- */}
                {activeTab === 'materials' && (
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-gray-900">Content Box</h2>
                            <button
                                onClick={() => setShowUploadModal(true)}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                            >
                                <Upload size={18} /> Material Yuklash
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {materials.map(material => (
                                <div key={material.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                                            <FileText size={24} />
                                        </div>
                                        <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">
                                            {material.category || 'Fayl'}
                                        </span>
                                    </div>
                                    <h3 className="font-semibold text-gray-900 mb-1">{material.title}</h3>
                                    <p className="text-sm text-gray-500 mb-3 line-clamp-2">{material.description}</p>
                                    <a
                                        href={material.file_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                                    >
                                        <Eye size={14} /> Ko'rish
                                    </a>
                                </div>
                            ))}
                        </div>
                        {materials.length === 0 && (
                            <div className="text-center p-8 text-gray-500">Materiallar yuklanmagan</div>
                        )}
                    </div>
                )}

                {/* --- SCHEDULE TAB --- */}
                {activeTab === 'schedule' && (
                    <div className="bg-white rounded-lg shadow-sm p-6 text-center">
                        <div className="flex flex-col items-center justify-center py-12">
                            <Calendar size={64} className="text-gray-300 mb-4" />
                            <h3 className="text-lg font-medium text-gray-900">Dars Jadvali</h3>
                            <p className="text-gray-500 mb-6">Sinf xonalari bo'yicha dars jadvallarini boshqarish.</p>
                            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                                Jadval Yaratish (Tez orada)
                            </button>
                        </div>
                    </div>
                )}

                {/* --- USERS TAB --- */}
                {activeTab === 'users' && (
                    <div className="bg-white rounded-lg shadow-sm">
                        <div className="p-6 border-b border-gray-200">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-lg font-bold">Foydalanuvchilar</h2>
                                <button
                                    onClick={() => setShowInviteStudentModal(true)}
                                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
                                >
                                    <Plus size={18} /> O'quvchi Taklif Qilish
                                </button>
                            </div>
                            <div className="flex flex-col md:flex-row gap-4">
                                <div className="flex-1 relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                    <input
                                        type="text"
                                        placeholder="Qidirish..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                                <select
                                    value={roleFilter}
                                    onChange={(e) => setRoleFilter(e.target.value)}
                                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">Barcha rollar</option>
                                    <option value="student">O'quvchilar</option>
                                    <option value="teacher">O'qituvchilar</option>
                                    <option value="parent">Ota-onalar</option>
                                </select>
                            </div>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ism</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Holat</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {filteredUsers.map(u => (
                                        <tr key={u.id}>
                                            <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                                                {u.name || (u.first_name + ' ' + u.last_name)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-gray-500">{u.email}</td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs rounded-full ${u.role === 'student' ? 'bg-blue-100 text-blue-800' :
                                                    u.role === 'teacher' ? 'bg-purple-100 text-purple-800' : 'bg-gray-100'
                                                    }`}>
                                                    {getRoleName(u.role)}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                                                    Faol
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* --- MODALS --- */}
                {showAddTeacherModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <h3 className="text-lg font-bold mb-4">O'qituvchi Qo'shish</h3>
                            <form onSubmit={handleAddTeacher}>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium mb-1">O'qituvchi ID</label>
                                    <input
                                        type="text"
                                        value={teacherIdToAdd}
                                        onChange={e => setTeacherIdToAdd(e.target.value)}
                                        className="w-full border rounded p-2"
                                        required
                                        placeholder="UUID..."
                                    />
                                    <p className="text-xs text-gray-500 mt-1">
                                        * Kelajakda qidiruv tizimi qo'shiladi
                                    </p>
                                </div>
                                <div className="flex justify-end gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setShowAddTeacherModal(false)}
                                        className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
                                    >
                                        Bekor qilish
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                    >
                                        Qo'shish
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {showUploadModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <h3 className="text-lg font-bold mb-4">Material Yuklash</h3>
                            <form onSubmit={handleUploadMaterial}>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium mb-1">Nomi</label>
                                    <input
                                        type="text"
                                        value={uploadTitle}
                                        onChange={e => setUploadTitle(e.target.value)}
                                        className="w-full border rounded p-2"
                                        required
                                    />
                                </div>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium mb-1">Fayl URL</label>
                                    <input
                                        type="text"
                                        value={uploadFileUrl}
                                        onChange={e => setUploadFileUrl(e.target.value)}
                                        className="w-full border rounded p-2"
                                        required
                                        placeholder="https://..."
                                    />
                                </div>
                                <div className="flex justify-end gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setShowUploadModal(false)}
                                        className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
                                    >
                                        Bekor qilish
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                    >
                                        Yuklash
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {/* Invite Student Modal */}
                {showInviteStudentModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <h3 className="text-lg font-bold mb-4">O'quvchi Taklif Qilish</h3>
                            <p className="text-sm text-gray-500 mb-4">
                                O'quvchi ma'lumotlarini kiriting. Tizim avtomatik ravishda login va parolni SMS/Email orqali yuboradi.
                            </p>
                            <form onSubmit={handleInviteStudent}>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium mb-1">Ism va Familiya</label>
                                    <input
                                        type="text"
                                        value={inviteStudentData.name}
                                        onChange={e => setInviteStudentData({ ...inviteStudentData, name: e.target.value })}
                                        className="w-full border rounded p-2"
                                        required
                                        placeholder="Ali Valiyev"
                                    />
                                </div>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium mb-1">Telefon Raqami (Login bo'ladi)</label>
                                    <input
                                        type="tel"
                                        value={inviteStudentData.phone}
                                        onChange={e => setInviteStudentData({ ...inviteStudentData, phone: e.target.value })}
                                        className="w-full border rounded p-2"
                                        required
                                        placeholder="+998901234567"
                                    />
                                </div>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium mb-1">Email (Ixtiyoriy)</label>
                                    <input
                                        type="email"
                                        value={inviteStudentData.email}
                                        onChange={e => setInviteStudentData({ ...inviteStudentData, email: e.target.value })}
                                        className="w-full border rounded p-2"
                                        placeholder="student@example.com"
                                    />
                                </div>
                                <div className="flex justify-end gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setShowInviteStudentModal(false)}
                                        className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
                                    >
                                        Bekor qilish
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                                    >
                                        Taklif Qilish
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const StatCard = ({ label, value, icon, color }) => {
    const colors = {
        blue: 'bg-blue-50 text-blue-600',
        green: 'bg-green-50 text-green-600',
        purple: 'bg-purple-50 text-purple-600',
        orange: 'bg-orange-50 text-orange-600',
    };

    return (
        <div className={`rounded-xl p-6 ${colors[color] || colors.blue}`}>
            <div className="text-3xl mb-2">{icon}</div>
            <div className="text-3xl font-bold mb-1">{value}</div>
            <div className="text-sm font-medium opacity-80">{label}</div>
        </div>
    );
};

export default OrganizationDashboard;

