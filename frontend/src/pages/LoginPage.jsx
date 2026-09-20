import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { 
  Building2, 
  Lock, 
  User, 
  ArrowRight, 
  ShieldCheck, 
  AlertCircle, 
  Sparkles,
  Layers,
  KeyRound,
  Eye,
  EyeOff
} from 'lucide-react';
import { useAuth, SEED_USERS, ROLE_HOME_ROUTES } from '../context/AuthContext';
import { Badge } from '../components/common/Badge';

export const LoginPage = () => {
  const { login, isAuthenticated, role } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [forgotPasswordNotice, setForgotPasswordNotice] = useState(false);

  // If already authenticated, redirect to role home
  React.useEffect(() => {
    if (isAuthenticated && role) {
      const destination = location.state?.from?.pathname || ROLE_HOME_ROUTES[role] || '/analyst';
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, role, navigate, location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setForgotPasswordNotice(false);

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username/email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await login(username, password);
      if (res.success) {
        const dest = ROLE_HOME_ROUTES[res.role] || '/analyst';
        navigate(dest, { replace: true });
      }
    } catch (err) {
      setError(err.message || 'Invalid username or password. Please verify credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = (seedUser) => {
    setUsername(seedUser.username);
    setPassword(seedUser.password);
    setError(null);
    setForgotPasswordNotice(false);
  };

  return (
    <div className="min-h-screen w-screen bg-[#07090e] flex flex-col justify-between text-slate-100 select-none overflow-x-hidden relative">
      {/* Background Ambient Grid Glow */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b0a_1px,transparent_1px),linear-gradient(to_bottom,#1e293b0a_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none"></div>
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Header */}
      <header className="h-16 px-8 flex items-center justify-between z-10 border-b border-white/5 bg-slate-950/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-lg shadow-cyan-500/10">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-wider text-white uppercase font-mono">
                UrbanSim <span className="text-cyan-400">Civic AI</span>
              </h1>
              <Badge variant="primary" size="xs">Mumbai BMC</Badge>
            </div>
            <p className="text-[10px] text-slate-400 font-mono tracking-wide">
              GIS Urban Intelligence & Participatory Planning Platform
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Security Protocol: RBAC Active</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex items-center justify-center p-6 z-10">
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
          
          {/* Left Hero Card */}
          <div className="md:col-span-5 space-y-4">
            <div className="space-y-2">
              <Badge variant="primary" size="sm" className="mb-2">Unified Access Gateway</Badge>
              <h2 className="text-2xl font-bold tracking-tight text-white font-sans">
                Mumbai Urban Intelligence Command Center
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed font-sans">
                Secure GIS intelligence, civic participation, and multi-domain spatial decision support across Mumbai's 24 BMC administrative wards.
              </p>
            </div>

            {/* Role Capability Checklist */}
            <div className="space-y-2 pt-2 border-t border-white/10 text-xs font-mono">
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span><strong>Citizen</strong>: Public GIS & Civic Complaints</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                <span><strong>Urban Analyst</strong>: 12 Lenses, ML & Scenarios</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span><strong>Urban Authority</strong>: Operations & Ward Queues</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                <span><strong>System Admin</strong>: Users, Audit Logs & Models</span>
              </div>
            </div>
          </div>

          {/* Right Login Form Card */}
          <div className="md:col-span-7">
            <div className="p-6 md:p-8 rounded-2xl bg-slate-900/90 border border-slate-700/80 shadow-2xl backdrop-blur-xl space-y-6 relative overflow-hidden">
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
                    Authenticate Session
                  </h3>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                    Enter credentials to unlock your authorized workspace
                  </p>
                </div>
                <KeyRound className="w-5 h-5 text-cyan-400 opacity-80" />
              </div>

              {/* Error Alert */}
              {error && (
                <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-500/40 flex items-start gap-2.5 text-xs text-rose-300 font-sans">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Forgot Password Notice */}
              {forgotPasswordNotice && (
                <div className="p-3 rounded-xl bg-amber-950/60 border border-amber-500/40 flex items-start gap-2.5 text-xs text-amber-300 font-sans">
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block">Password Reset Notice:</span>
                    For development demonstration, select any demo account below or contact your System Administrator at <code className="text-white bg-black/40 px-1 py-0.5 rounded">admin@urbansim.local</code>.
                  </div>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4 font-sans">
                <div className="space-y-1.5">
                  <label className="text-[11px] font-mono uppercase tracking-wider text-slate-300 block">
                    Email / Username
                  </label>
                  <div className="flex items-center bg-slate-950/80 border border-slate-700/90 rounded-xl px-3 py-2.5 focus-within:border-cyan-500 focus-within:ring-1 focus-within:ring-cyan-500/40 transition-all">
                    <User className="w-4 h-4 text-slate-400 mr-2.5 shrink-0" />
                    <input
                      type="text"
                      placeholder="e.g. analyst or citizen"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-full font-mono"
                      autoFocus
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-mono uppercase tracking-wider text-slate-300 block">
                      Password
                    </label>
                    <button
                      type="button"
                      onClick={() => setForgotPasswordNotice(true)}
                      className="text-[10px] text-cyan-400 hover:text-cyan-300 font-mono hover:underline"
                    >
                      Forgot password?
                    </button>
                  </div>
                  <div className="flex items-center bg-slate-950/80 border border-slate-700/90 rounded-xl px-3 py-2.5 focus-within:border-cyan-500 focus-within:ring-1 focus-within:ring-cyan-500/40 transition-all">
                    <Lock className="w-4 h-4 text-slate-400 mr-2.5 shrink-0" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-full font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-slate-400 hover:text-slate-200 p-1"
                    >
                      {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-all disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <span>Authenticating...</span>
                  ) : (
                    <>
                      <span>Sign In to Workspace</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>

                {/* Real Citizen Registration Link */}
                <div className="pt-2 text-center">
                  <span className="text-xs text-slate-400">New to UrbanSim? </span>
                  <Link
                    to="/register"
                    className="text-xs font-bold text-emerald-400 hover:text-emerald-300 font-mono hover:underline"
                  >
                    Create a Citizen Account &rarr;
                  </Link>
                </div>
              </form>

              {/* Demo Quick-Login Switcher Card */}
              <div className="pt-4 border-t border-white/10 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-cyan-400" />
                    Demo Role Accounts (1-Click Fill)
                  </span>
                  <span className="text-[9px] text-slate-500 font-mono">Dev Test Mode</span>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  {SEED_USERS.map((seed) => (
                    <button
                      key={seed.username}
                      type="button"
                      onClick={() => handleQuickLogin(seed)}
                      className={`p-2 rounded-lg border text-left transition-all hover:scale-[1.02] ${
                        username === seed.username 
                          ? 'bg-slate-800 border-cyan-500/60 ring-1 ring-cyan-500/30' 
                          : 'bg-slate-950/60 border-white/5 hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-white font-mono capitalize">
                          {seed.username}
                        </span>
                        <span className={`text-[9px] px-1.5 py-0.2 rounded border font-mono ${seed.badgeColor}`}>
                          {seed.role.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-[9px] text-slate-400 line-clamp-1 font-sans">
                        {seed.description}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="h-10 px-8 flex items-center justify-between text-[11px] font-mono text-slate-500 border-t border-white/5 bg-slate-950/40">
        <span>UrbanSim Civic AI | Brihanmumbai Municipal Corporation (BMC) GIS Platform</span>
        <span>Relative Percentile-Normalized Analytical System</span>
      </footer>
    </div>
  );
};
