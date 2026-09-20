import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Building2, 
  Lock, 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  ShieldCheck, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle, 
  Eye, 
  EyeOff, 
  Sparkles,
  HeartHandshake
} from 'lucide-react';
import { useAuth, ROLE_HOME_ROUTES } from '../context/AuthContext';
import { Badge } from '../components/common/Badge';
import { WARD_NAMES } from '../constants';

export const RegisterPage = () => {
  const { register, isAuthenticated, role } = useAuth();
  const navigate = useNavigate();

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    username: '',
    phone: '',
    ward: 'GS',
    address: '',
    password: '',
    confirmPassword: '',
    agreeTerms: true
  });

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // If already authenticated, redirect to role workspace
  React.useEffect(() => {
    if (isAuthenticated && role) {
      navigate(ROLE_HOME_ROUTES[role] || '/citizen', { replace: true });
    }
  }, [isAuthenticated, role, navigate]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.name.trim() || !formData.email.trim() || !formData.username.trim() || !formData.password) {
      setError('Please fill in all required fields.');
      return;
    }

    const cleanUser = formData.username.trim().toLowerCase();
    const reservedUsers = ['admin', 'analyst', 'authority', 'citizen', 'system', 'root'];
    if (reservedUsers.includes(cleanUser)) {
      setError(`The username '${formData.username}' is a reserved system role. Please choose a unique citizen username (such as 'karthik', 'karthikeyan', or 'karthik_mumbai').`);
      return;
    }

    if (formData.username.length < 3) {
      setError('Username must be at least 3 characters.');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match. Please re-enter.');
      return;
    }

    if (!formData.agreeTerms) {
      setError('Please accept the Citizen Participation Agreement.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await register({
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        username: cleanUser,
        password: formData.password,
        ward: formData.ward,
        phone: formData.phone.trim() || null,
        address: formData.address.trim() || null
      });

      if (res.success) {
        navigate('/citizen', { replace: true });
      }
    } catch (err) {
      setError(err.message || 'Registration failed. Please verify your details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-[#07090e] flex flex-col justify-between text-slate-100 select-none overflow-x-hidden relative py-8 px-4">
      {/* Background Ambient Glows */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b0a_1px,transparent_1px),linear-gradient(to_bottom,#1e293b0a_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none"></div>
      <div className="absolute top-1/4 right-1/3 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-10 left-10 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Header */}
      <header className="max-w-4xl mx-auto w-full flex items-center justify-between z-10 mb-6 pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/10">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-wider text-white uppercase font-mono">
                UrbanSim <span className="text-emerald-400">Citizen Registration</span>
              </h1>
              <Badge variant="success" size="xs">Mumbai BMC</Badge>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Public Participatory Urban Intelligence &amp; Civic Grievance Platform
            </p>
          </div>
        </div>

        <Link
          to="/login"
          className="text-xs text-cyan-400 hover:text-cyan-300 font-mono flex items-center gap-1 hover:underline"
        >
          <span>Existing User? Sign In</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </header>

      {/* Main Registration Card */}
      <main className="max-w-4xl mx-auto w-full z-10 flex-1 flex flex-col justify-center">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/80 rounded-2xl p-6 sm:p-8 shadow-2xl">
          
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white font-sans flex items-center gap-2">
              <HeartHandshake className="w-5 h-5 text-emerald-400" />
              Create Your Verified Mumbai Citizen Account
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Your registration records will be stored directly into the UrbanSim secure database. As a registered citizen, you can track local ward indicators, discover public amenities, and submit geo-tagged civic grievances.
            </p>
          </div>

          {/* Error Message Box */}
          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2.5 animate-fadeIn">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* SECTION 1: CITIZEN PERSONAL INFO */}
            <div>
              <h3 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <User className="w-3.5 h-3.5 text-cyan-400" />
                1. Citizen Identification
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Full Name <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="e.g., Aarav Sharma"
                    required
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all font-sans"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Username (Unique) <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    placeholder="e.g., aarav_worli"
                    required
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Email Address <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-3" />
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="citizen@mumbai.in"
                      required
                      className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg pl-9 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all font-sans"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Mobile / Phone (For Grievance SMS Updates)
                  </label>
                  <div className="relative">
                    <Phone className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-3" />
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      placeholder="+91 98200 12345"
                      className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg pl-9 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all font-sans"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* SECTION 2: RESIDENTIAL BMC WARD */}
            <div>
              <h3 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                2. Residential BMC Ward &amp; Locality
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Primary BMC Ward <span className="text-rose-400">*</span>
                  </label>
                  <select
                    name="ward"
                    value={formData.ward}
                    onChange={handleChange}
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500 transition-all font-mono"
                  >
                    {Object.entries(WARD_NAMES).map(([code, name]) => (
                      <option key={code} value={code}>
                        Ward {code} &mdash; {name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Locality / Street Address (Optional)
                  </label>
                  <input
                    type="text"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    placeholder="e.g., Near Worli Sea Face, Mumbai 400018"
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all font-sans"
                  />
                </div>
              </div>
            </div>

            {/* SECTION 3: SECURITY CREDENTIALS */}
            <div>
              <h3 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Lock className="w-3.5 h-3.5 text-amber-400" />
                3. Security Password
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Password (Min 6 chars) <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="••••••••"
                      required
                      className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Confirm Password <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="••••••••"
                    required
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all font-mono"
                  />
                </div>
              </div>
            </div>

            {/* AGREEMENT & CONSENT */}
            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800 flex items-start gap-3">
              <input
                type="checkbox"
                id="agreeTerms"
                name="agreeTerms"
                checked={formData.agreeTerms}
                onChange={handleChange}
                className="mt-0.5 w-4 h-4 rounded text-emerald-500 bg-slate-900 border-slate-700 focus:ring-emerald-500 focus:ring-offset-slate-900"
              />
              <label htmlFor="agreeTerms" className="text-xs text-slate-400 leading-relaxed">
                I agree to the <strong className="text-slate-200">UrbanSim Civic AI Data Transparency &amp; Public Grievance Charter</strong>. I understand that my registered complaints will be routed to the respective BMC Ward Officer and resolved with public tracking indicators.
              </label>
            </div>

            {/* SUBMIT BUTTON */}
            <div className="flex items-center justify-between pt-2">
              <Link
                to="/login"
                className="text-xs text-slate-400 hover:text-slate-200 font-mono"
              >
                &larr; Return to Sign In
              </Link>

              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 flex items-center gap-2 transition-all disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
                    <span>Creating Database Record...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Create Citizen Account &amp; Access GIS</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-4xl mx-auto w-full text-center text-[11px] text-slate-500 font-mono mt-6">
        UrbanSim Civic AI &bull; Mumbai BMC 24 Wards Intelligence Network &bull; Database: SQLite Persistent Storage
      </footer>
    </div>
  );
};
