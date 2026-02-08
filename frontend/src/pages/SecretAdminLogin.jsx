import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, User, Shield, Eye, EyeOff } from 'lucide-react';

/**
 * Secret Admin Login Page
 * Routes: /nurali (CEO), /hazratqul (CTO), /pedagog (Metodist)
 * Password: alif_rahbariyat26!
 */
const SecretAdminLogin = () => {
    const { adminType } = useParams();
    const navigate = useNavigate();
    const { login } = useAuth();

    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Admin configuration
    const adminConfig = {
        nurali: { name: 'CEO', title: 'Nurali', role: 'moderator', email: 'nurali@alif24.uz' },
        hazratqul: { name: 'CTO', title: 'Hazratqul', role: 'moderator', email: 'hazratqul@alif24.uz' },
        pedagog: { name: 'Pedagog Metodist', title: 'Pedagog', role: 'moderator', email: 'pedagog@alif24.uz' }
    };

    const currentAdmin = adminConfig[adminType] || adminConfig.nurali;
    const ADMIN_PASSWORD = 'alif_rahbariyat26!';

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (password !== ADMIN_PASSWORD) {
            setError("Parol noto'g'ri!");
            setLoading(false);
            return;
        }

        try {
            // Login with hardcoded admin credentials
            await login(currentAdmin.email, ADMIN_PASSWORD);
            navigate('/crm');
        } catch (err) {
            // If login fails, try direct localStorage approach for demo
            const mockUser = {
                id: `admin-${adminType}`,
                email: currentAdmin.email,
                first_name: currentAdmin.title,
                last_name: currentAdmin.name,
                role: currentAdmin.role
            };

            localStorage.setItem('user', JSON.stringify(mockUser));
            localStorage.setItem('accessToken', 'admin-demo-token-' + Date.now());
            localStorage.setItem('refreshToken', 'admin-refresh-' + Date.now());

            // Force page reload to apply auth state
            window.location.href = '/crm';
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-8 w-full max-w-md border border-white/20 shadow-2xl">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                        <Shield className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">
                        {currentAdmin.name} Kirish
                    </h1>
                    <p className="text-white/60 text-sm">
                        Alif24 Boshqaruv Paneli
                    </p>
                </div>

                {/* Login Form */}
                <form onSubmit={handleLogin} className="space-y-6">
                    {/* Username (readonly) */}
                    <div>
                        <label className="block text-white/80 text-sm mb-2">Foydalanuvchi</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
                            <input
                                type="text"
                                value={currentAdmin.title}
                                readOnly
                                className="w-full bg-white/10 border border-white/20 rounded-lg py-3 pl-11 pr-4 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div>
                        <label className="block text-white/80 text-sm mb-2">Parol</label>
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

                    {/* Error Message */}
                    {error && (
                        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-300 text-sm text-center">
                            {error}
                        </div>
                    )}

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 rounded-lg transition-all duration-300 disabled:opacity-50 shadow-lg"
                    >
                        {loading ? 'Kirish...' : 'Kirish'}
                    </button>
                </form>

                {/* Footer */}
                <p className="text-center text-white/40 text-xs mt-6">
                    Bu sahifa faqat rahbariyat uchun
                </p>
            </div>
        </div>
    );
};

export default SecretAdminLogin;
