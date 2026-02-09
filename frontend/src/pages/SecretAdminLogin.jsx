import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
    Lock, Shield, Eye, EyeOff, Users, Activity, Database, Search,
    Home, LogOut, RefreshCw, ChevronRight, AlertCircle
} from 'lucide-react';
import apiService from '../services/apiService';

/**
 * Secret Admin Dashboard
 * Routes: /nurali (CEO), /hazratqul (CTO), /pedagog (Metodist)
 * Uses backend API: /api/v1/secret/*
 */
const SecretAdminLogin = () => {
    const location = useLocation();
    const adminType = location.pathname.slice(1); // 'nurali', 'hazratqul', or 'pedagog'

    // Auth state
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [authError, setAuthError] = useState('');
    const [authLoading, setAuthLoading] = useState(false);

    // Dashboard state
    const [activeTab, setActiveTab] = useState('dashboard');
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [tables, setTables] = useState([]);
    const [selectedTable, setSelectedTable] = useState(null);
    const [tableData, setTableData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Admin config
    const adminConfig = {
        nurali: { name: 'CEO', title: 'Nurali', color: 'from-purple-600 to-pink-600' },
        hazratqul: { name: 'CTO', title: 'Hazratqul', color: 'from-blue-600 to-cyan-600' },
        pedagog: { name: 'Pedagog', title: 'Metodist', color: 'from-green-600 to-teal-600' }
    };
    const currentAdmin = adminConfig[adminType] || adminConfig.nurali;

    // Handle login
    const handleLogin = async (e) => {
        e.preventDefault();
        setAuthLoading(true);
        setAuthError('');

        try {
            const response = await fetch('/api/v1/secret/access', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    passphrase: password,
                    role: adminType
                })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('secretAdminToken', data.token);
                setIsAuthenticated(true);
            } else {
                setAuthError("Parol noto'g'ri!");
            }
        } catch (err) {
            setAuthError('Serverga ulanib bo\'lmadi');
        } finally {
            setAuthLoading(false);
        }
    };

    // Logout
    const handleLogout = () => {
        localStorage.removeItem('secretAdminToken');
        setIsAuthenticated(false);
    };

    // Helper for authenticated requests
    const authenticatedFetch = async (url) => {
        const token = localStorage.getItem('secretAdminToken');
        const response = await fetch(url, {
            headers: {
                'X-Secret-Token': token
            }
        });

        if (response.status === 403) {
            handleLogout();
            throw new Error("Session expired or access denied");
        }

        return response;
    };

    // Load dashboard data
    const loadDashboard = async () => {
        setLoading(true);
        try {
            const response = await authenticatedFetch('/api/v1/secret/dashboard');
            const data = await response.json();
            if (data.success) {
                setStats(data.data);
            }
        } catch (err) {
            setError('Dashboard yuklanmadi');
        } finally {
            setLoading(false);
        }
    };

    // Load users
    const loadUsers = async () => {
        setLoading(true);
        try {
            const response = await authenticatedFetch('/api/v1/secret/users?limit=100');
            const data = await response.json();
            if (data.success) {
                setUsers(data.data.users);
            }
        } catch (err) {
            setError('Foydalanuvchilar yuklanmadi');
        } finally {
            setLoading(false);
        }
    };

    // Smart search
    const handleSearch = async (query) => {
        setSearchQuery(query);
        if (query.length >= 3) {
            try {
                const response = await authenticatedFetch(`/api/v1/secret/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                if (data.success) {
                    setSearchResults(data.data.results);
                }
            } catch (err) {
                console.error('Search failed:', err);
            }
        } else {
            setSearchResults([]);
        }
    };

    // Load database tables
    const loadTables = async () => {
        setLoading(true);
        try {
            const response = await authenticatedFetch('/api/v1/secret/database/tables');
            const data = await response.json();
            if (data.success) {
                setTables(data.data.tables);
            }
        } catch (err) {
            setError('Jadvallar yuklanmadi');
        } finally {
            setLoading(false);
        }
    };

    // Load table data
    const loadTableData = async (tableName) => {
        setLoading(true);
        setSelectedTable(tableName);
        try {
            const response = await authenticatedFetch(`/api/v1/secret/database/table/${tableName}?limit=50`);
            const data = await response.json();
            if (data.success) {
                setTableData(data.data);
            }
        } catch (err) {
            setError('Jadval ma\'lumotlari yuklanmadi');
        } finally {
            setLoading(false);
        }
    };

    // Load data when tab changes
    useEffect(() => {
        if (!isAuthenticated) return;

        switch (activeTab) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'users':
                loadUsers();
                break;
            case 'database':
                loadTables();
                break;
        }
    }, [activeTab, isAuthenticated]);

    // Check for existing session
    useEffect(() => {
        const token = localStorage.getItem('secretAdminToken');
        if (token) {
            setIsAuthenticated(true);
        }
    }, []);

    // Login Form
    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
                <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-8 w-full max-w-md border border-white/20 shadow-2xl">
                    <div className="text-center mb-8">
                        <div className={`w-20 h-20 bg-gradient-to-br ${currentAdmin.color} rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg`}>
                            <Shield className="w-10 h-10 text-white" />
                        </div>
                        <h1 className="text-2xl font-bold text-white mb-2">
                            {currentAdmin.title} - {currentAdmin.name}
                        </h1>
                        <p className="text-white/60 text-sm">
                            Alif24 Maxfiy Boshqaruv Paneli
                        </p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div>
                            <label className="block text-white/80 text-sm mb-2">Maxfiy Parol</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Parolni kiriting"
                                    className="w-full bg-white/10 border border-white/20 rounded-lg py-3 pl-11 pr-12 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white"
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        {authError && (
                            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-300 text-sm text-center">
                                {authError}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={authLoading}
                            className={`w-full bg-gradient-to-r ${currentAdmin.color} hover:opacity-90 text-white font-semibold py-3 rounded-lg transition-all duration-300 disabled:opacity-50 shadow-lg`}
                        >
                            {authLoading ? 'Tekshirilmoqda...' : 'Kirish'}
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    // Admin Dashboard
    return (
        <div className="min-h-screen bg-slate-900 text-white">
            {/* Sidebar */}
            <div className="fixed left-0 top-0 h-full w-64 bg-slate-800 border-r border-slate-700 p-4">
                <div className={`flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r ${currentAdmin.color} mb-8`}>
                    <Shield className="w-8 h-8" />
                    <div>
                        <h2 className="font-bold">{currentAdmin.title}</h2>
                        <p className="text-xs opacity-80">{currentAdmin.name}</p>
                    </div>
                </div>

                <nav className="space-y-2">
                    {[
                        { id: 'dashboard', icon: Home, label: 'Dashboard' },
                        { id: 'users', icon: Users, label: 'Foydalanuvchilar' },
                        { id: 'search', icon: Search, label: 'Qidiruv' },
                        { id: 'database', icon: Database, label: "Ma'lumotlar bazasi" },
                    ].map(item => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === item.id
                                ? 'bg-purple-600 text-white'
                                : 'text-slate-400 hover:bg-slate-700 hover:text-white'
                                }`}
                        >
                            <item.icon className="w-5 h-5" />
                            {item.label}
                        </button>
                    ))}
                </nav>

                <button
                    onClick={handleLogout}
                    className="absolute bottom-4 left-4 right-4 flex items-center justify-center gap-2 px-4 py-3 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30 transition-all"
                >
                    <LogOut className="w-5 h-5" />
                    Chiqish
                </button>
            </div>

            {/* Main Content */}
            <div className="ml-64 p-8">
                {error && (
                    <div className="mb-4 bg-red-500/20 border border-red-500/50 rounded-lg p-4 flex items-center gap-3 text-red-300">
                        <AlertCircle className="w-5 h-5" />
                        {error}
                        <button onClick={() => setError('')} className="ml-auto text-red-300 hover:text-red-100">×</button>
                    </div>
                )}

                {loading && (
                    <div className="flex items-center justify-center py-20">
                        <RefreshCw className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                )}

                {/* Dashboard Tab */}
                {activeTab === 'dashboard' && !loading && stats && (
                    <div>
                        <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            {[
                                { label: 'Jami foydalanuvchilar', value: stats.total_users, color: 'from-purple-500 to-pink-500' },
                                { label: "O'quvchilar", value: stats.total_students, color: 'from-blue-500 to-cyan-500' },
                                { label: "O'qituvchilar", value: stats.total_teachers, color: 'from-green-500 to-teal-500' },
                                { label: 'Ota-onalar', value: stats.total_parents, color: 'from-orange-500 to-yellow-500' },
                                { label: 'Faol foydalanuvchilar', value: stats.active_users, color: 'from-indigo-500 to-purple-500' },
                                { label: "Bugun ro'yxatdan o'tgan", value: stats.new_users_today, color: 'from-pink-500 to-rose-500' },
                                { label: "Hafta davomida yangi", value: stats.new_users_week, color: 'from-teal-500 to-green-500' },
                            ].map((stat, i) => (
                                <div key={i} className={`bg-gradient-to-br ${stat.color} rounded-2xl p-6 shadow-xl`}>
                                    <p className="text-white/80 text-sm mb-1">{stat.label}</p>
                                    <p className="text-4xl font-bold">{stat.value}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Users Tab */}
                {activeTab === 'users' && !loading && (
                    <div>
                        <h1 className="text-3xl font-bold mb-8">Foydalanuvchilar</h1>
                        <div className="bg-slate-800 rounded-xl overflow-hidden">
                            <table className="w-full">
                                <thead className="bg-slate-700">
                                    <tr>
                                        <th className="text-left p-4">Ism</th>
                                        <th className="text-left p-4">Email/Telefon</th>
                                        <th className="text-left p-4">Rol</th>
                                        <th className="text-left p-4">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.map((user, i) => (
                                        <tr key={user.id || i} className="border-t border-slate-700 hover:bg-slate-700/50">
                                            <td className="p-4">{user.first_name} {user.last_name}</td>
                                            <td className="p-4 text-slate-400">{user.email || user.phone}</td>
                                            <td className="p-4">
                                                <span className="px-2 py-1 rounded bg-purple-600/30 text-purple-300 text-sm">
                                                    {user.role}
                                                </span>
                                            </td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded text-sm ${user.status === 'active' ? 'bg-green-600/30 text-green-300' : 'bg-red-600/30 text-red-300'
                                                    }`}>
                                                    {user.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Search Tab */}
                {activeTab === 'search' && (
                    <div>
                        <h1 className="text-3xl font-bold mb-8">Smart Qidiruv</h1>
                        <div className="relative mb-8">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => handleSearch(e.target.value)}
                                placeholder="Kamida 3 ta belgi kiriting..."
                                className="w-full bg-slate-800 border border-slate-700 rounded-xl py-4 pl-12 pr-4 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                        </div>

                        {searchResults.length > 0 && (
                            <div className="bg-slate-800 rounded-xl overflow-hidden">
                                {searchResults.map((result, i) => (
                                    <div key={i} className="p-4 border-b border-slate-700 last:border-0 hover:bg-slate-700/50 cursor-pointer flex items-center justify-between">
                                        <div>
                                            <span className="px-2 py-1 rounded bg-purple-600/30 text-purple-300 text-xs mr-3">
                                                {result.type}
                                            </span>
                                            <span className="font-medium">{result.title}</span>
                                            <p className="text-slate-400 text-sm mt-1">{result.subtitle}</p>
                                        </div>
                                        <ChevronRight className="w-5 h-5 text-slate-400" />
                                    </div>
                                ))}
                            </div>
                        )}

                        {searchQuery.length >= 3 && searchResults.length === 0 && (
                            <p className="text-center text-slate-400 py-8">Hech narsa topilmadi</p>
                        )}
                    </div>
                )}

                {/* Database Tab */}
                {activeTab === 'database' && !loading && (
                    <div>
                        <h1 className="text-3xl font-bold mb-8">Ma'lumotlar Bazasi</h1>

                        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                            {/* Tables List */}
                            <div className="bg-slate-800 rounded-xl p-4">
                                <h3 className="font-semibold mb-4">Jadvallar ({tables.length})</h3>
                                <div className="space-y-1 max-h-96 overflow-y-auto">
                                    {tables.map((table, i) => (
                                        <button
                                            key={i}
                                            onClick={() => loadTableData(table)}
                                            className={`w-full text-left px-3 py-2 rounded-lg transition-all text-sm ${selectedTable === table
                                                ? 'bg-purple-600 text-white'
                                                : 'text-slate-300 hover:bg-slate-700'
                                                }`}
                                        >
                                            {table}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Table Data */}
                            <div className="lg:col-span-3 bg-slate-800 rounded-xl p-4 overflow-x-auto">
                                {tableData ? (
                                    <>
                                        <h3 className="font-semibold mb-4">
                                            {tableData.table} <span className="text-slate-400 font-normal">({tableData.total} qator)</span>
                                        </h3>
                                        <table className="w-full text-sm">
                                            <thead className="bg-slate-700">
                                                <tr>
                                                    {tableData.columns.map((col, i) => (
                                                        <th key={i} className="text-left p-2 font-medium">{col}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {tableData.rows.map((row, i) => (
                                                    <tr key={i} className="border-t border-slate-700">
                                                        {tableData.columns.map((col, j) => (
                                                            <td key={j} className="p-2 text-slate-300 truncate max-w-xs">
                                                                {String(row[col] ?? '-')}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </>
                                ) : (
                                    <p className="text-slate-400 text-center py-8">Jadvalni tanlang</p>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SecretAdminLogin;
