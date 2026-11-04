const { useState, useEffect, useCallback, createContext, useContext } = React;

// ─── API Client ─────────────────────────────────────────────────────────────
const API_BASE = '/api';

const api = {
  getToken: () => localStorage.getItem('teamr_token'),
  setToken: (token) => localStorage.setItem('teamr_token', token),
  removeToken: () => localStorage.removeItem('teamr_token'),
  getUser: () => {
    try {
      const u = localStorage.getItem('teamr_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },
  setUser: (user) => localStorage.setItem('teamr_user', JSON.stringify(user)),
  removeUser: () => localStorage.removeItem('teamr_user'),

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = { ...options.headers };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && options.body && typeof options.body === 'object') {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    if (!res.ok) {
      let errMessage = 'An error occurred';
      try {
        const data = await res.json();
        errMessage = data.detail || data.message || errMessage;
      } catch {}
      throw new Error(errMessage);
    }
    return res.json();
  }
};

// ─── Toast Context ──────────────────────────────────────────────────────────
const ToastContext = createContext(null);
function useToast() { return useContext(ToastContext); }

// ─── SVG Icons ──────────────────────────────────────────────────────────────
const Icons = {
  Building: () => <svg className="w-5 h-5 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>,
  Check: () => <svg className="w-4 h-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>,
  Trash: () => <svg className="w-4 h-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>,
  ArrowLeft: () => <svg className="w-4 h-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>,
  ThumbsUp: () => <svg className="w-4 h-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" /></svg>,
  Eye: () => <svg className="w-4 h-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>,
  Menu: () => <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" /></svg>,
  Close: () => <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>,
  Bell: () => <svg className="w-5 h-5 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>,
  Download: () => <svg className="w-4 h-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>,
  User: () => <svg className="w-4 h-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>,
  Plus: () => <svg className="w-4 h-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" /></svg>,
};

// ─── Badges ─────────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const styles = {
    'Submitted': 'bg-blue-950/40 text-blue-300 border-blue-800/50',
    'Acknowledged': 'bg-amber-950/40 text-amber-300 border-amber-800/50',
    'Assigned': 'bg-teal-950/40 text-teal-300 border-teal-800/50',
    'In Progress': 'bg-sky-950/40 text-sky-300 border-sky-800/50',
    'Resolved': 'bg-emerald-950/40 text-emerald-300 border-emerald-800/50',
    'Reopened': 'bg-rose-950/40 text-rose-300 border-rose-800/50',
    'Closed': 'bg-zinc-800/70 text-zinc-400 border-zinc-700/60',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-[11px] font-medium tracking-normal border ${styles[status] || styles['Submitted']}`}>
      {status || 'Submitted'}
    </span>
  );
}

function PriorityBadge({ priority }) {
  const styles = {
    'Low': 'bg-zinc-800/60 text-zinc-300 border-zinc-700/50',
    'Medium': 'bg-amber-950/40 text-amber-300 border-amber-800/50',
    'High': 'bg-orange-950/40 text-orange-300 border-orange-800/50',
    'Urgent': 'bg-rose-950/50 text-rose-300 border-rose-800/60',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-[11px] font-medium tracking-normal border ${styles[priority] || styles['Medium']}`}>
      {priority || 'Medium'}
    </span>
  );
}

function SeenBadge({ isSeen, isAcknowledged }) {
  if (isAcknowledged) {
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-medium tracking-normal border bg-emerald-950/40 text-emerald-300 border-emerald-800/50">
        Acknowledged
      </span>
    );
  }
  if (isSeen) {
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-medium tracking-normal border bg-sky-950/40 text-sky-300 border-sky-800/50">
        Seen by caretaker
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded text-[11px] font-medium tracking-normal border bg-zinc-800/70 text-zinc-400 border-zinc-700/50">
      Not yet seen
    </span>
  );
}

function BackButton({ label = 'Back', to = '#/board' }) {
  return (
    <a
      href={to}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-zinc-400 bg-zinc-900 border border-zinc-800 rounded hover:bg-zinc-800 hover:text-zinc-200 transition-colors duration-150 mb-4"
    >
      <Icons.ArrowLeft /> {label}
    </a>
  );
}

// ─── Navbar Component ───────────────────────────────────────────────────────
function Navbar({ user, unreadCount, onLogout }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const closeMobile = () => setMobileMenuOpen(false);

  return (
    <nav className="bg-zinc-950/95 border-b border-zinc-800/80 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <a href="#/" className="flex items-center gap-2.5 text-zinc-100 font-semibold text-sm tracking-tight">
            <span className="p-1.5 bg-blue-600 rounded text-white flex items-center justify-center">
              <Icons.Building />
            </span>
            <span className="text-zinc-100">Hostel Grievances</span>
            <span className="hidden sm:inline-block text-xs font-normal text-zinc-400 border-l border-zinc-800 pl-2 ml-1">
              IIT Patna
            </span>
          </a>

          {/* Desktop Nav Items */}
          <div className="hidden md:flex items-center gap-1">
            <a href="#/" className="px-2.5 py-1.5 rounded text-xs font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900 transition-colors duration-150">
              Home
            </a>
            <a href="#/board" className="px-2.5 py-1.5 rounded text-xs font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900 transition-colors duration-150">
              Complaint Board
            </a>

            {user?.role === 'student' && (
              <>
                <a href="#/submit" className="px-2.5 py-1.5 rounded text-xs font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900 transition-colors duration-150">
                  Submit
                </a>
                <a href="#/my-complaints" className="px-2.5 py-1.5 rounded text-xs font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900 transition-colors duration-150">
                  My Complaints
                </a>
              </>
            )}

            {user?.role === 'caretaker' && (
              <a href="#/caretaker" className="px-2.5 py-1.5 rounded text-xs font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900 transition-colors duration-150">
                My Dashboard
              </a>
            )}

            {user?.role === 'admin' && (
              <>
                <a href="#/admin" className="px-2.5 py-1.5 rounded text-xs font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900 transition-colors duration-150">
                  Admin Dashboard
                </a>
                <a href="#/submit" className="px-2.5 py-1.5 rounded text-xs font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900 transition-colors duration-150">
                  Submit
                </a>
                <a href="#/analytics" className="px-2.5 py-1.5 rounded text-xs font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-900 transition-colors duration-150">
                  Analytics
                </a>
              </>
            )}
          </div>

          {/* Right side User / Login */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <>
                <a
                  href="#/notifications"
                  className="relative p-1.5 text-zinc-400 hover:text-zinc-100 rounded hover:bg-zinc-900 transition-colors duration-150"
                  title="Notifications"
                >
                  <Icons.Bell />
                  {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 px-1 items-center justify-center rounded-full bg-blue-600 text-[10px] font-semibold text-white">
                      {unreadCount}
                    </span>
                  )}
                </a>

                <div className="flex items-center gap-2.5 pl-2.5 border-l border-zinc-800">
                  <div className="text-right">
                    <div className="text-xs font-medium text-zinc-200">{user.display_name}</div>
                    <div className="text-[10px] font-medium text-zinc-400 uppercase tracking-wider">{user.role}</div>
                  </div>
                  <button
                    onClick={onLogout}
                    className="px-2 py-1 text-xs font-medium text-zinc-400 hover:text-rose-400 bg-zinc-900 hover:bg-zinc-850 rounded border border-zinc-800 transition-colors duration-150"
                  >
                    Sign Out
                  </button>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <a
                  href="#/login"
                  className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-500 shadow-xs transition-colors duration-150"
                >
                  Sign In
                </a>
                <a
                  href="#/register"
                  className="px-3 py-1.5 text-xs font-medium text-zinc-300 bg-zinc-900 border border-zinc-800 rounded hover:bg-zinc-800 hover:text-white transition-colors duration-150"
                >
                  Register
                </a>
              </div>
            )}
          </div>

          {/* Mobile hamburger button */}
          <div className="flex md:hidden items-center gap-2">
            {user && (
              <a href="#/notifications" className="relative p-1.5 text-zinc-400 hover:text-zinc-100">
                <Icons.Bell />
                {unreadCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 px-1 items-center justify-center rounded-full bg-blue-600 text-[10px] font-semibold text-white">
                    {unreadCount}
                  </span>
                )}
              </a>
            )}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 text-zinc-400 hover:text-zinc-100 rounded focus:outline-none"
            >
              {mobileMenuOpen ? <Icons.Close /> : <Icons.Menu />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer (closes automatically when any item is clicked) */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-zinc-950 border-b border-zinc-800 px-4 pt-2 pb-5 space-y-1.5">
          {user && (
            <div className="p-3 bg-zinc-900 rounded border border-zinc-800 mb-3 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-zinc-200">{user.display_name}</div>
                <div className="text-[11px] text-zinc-400 uppercase font-medium">{user.role} ({user.hostel || 'Campus'})</div>
              </div>
              <button
                onClick={() => { onLogout(); closeMobile(); }}
                className="px-2.5 py-1 text-xs text-rose-400 bg-zinc-950 border border-zinc-800 rounded hover:bg-zinc-800"
              >
                Sign Out
              </button>
            </div>
          )}

          <a onClick={closeMobile} href="#/" className="block px-3 py-1.5 rounded text-xs font-medium text-zinc-300 hover:bg-zinc-900">
            Home
          </a>
          <a onClick={closeMobile} href="#/board" className="block px-3 py-1.5 rounded text-xs font-medium text-zinc-300 hover:bg-zinc-900">
            Complaint Board
          </a>

          {user?.role === 'student' && (
            <>
              <a onClick={closeMobile} href="#/submit" className="block px-3 py-1.5 rounded text-xs font-medium text-zinc-300 hover:bg-zinc-900">
                Submit Complaint
              </a>
              <a onClick={closeMobile} href="#/my-complaints" className="block px-3 py-1.5 rounded text-xs font-medium text-zinc-300 hover:bg-zinc-900">
                My Complaints
              </a>
            </>
          )}

          {user?.role === 'caretaker' && (
            <a onClick={closeMobile} href="#/caretaker" className="block px-3 py-1.5 rounded text-xs font-medium text-zinc-300 hover:bg-zinc-900">
              My Dashboard
            </a>
          )}

          {user?.role === 'admin' && (
            <>
              <a onClick={closeMobile} href="#/admin" className="block px-3 py-1.5 rounded text-xs font-medium text-zinc-300 hover:bg-zinc-900">
                Admin Dashboard
              </a>
              <a onClick={closeMobile} href="#/submit" className="block px-3 py-1.5 rounded text-xs font-medium text-zinc-300 hover:bg-zinc-900">
                Submit Complaint
              </a>
              <a onClick={closeMobile} href="#/analytics" className="block px-3 py-1.5 rounded text-xs font-medium text-zinc-300 hover:bg-zinc-900">
                Analytics
              </a>
            </>
          )}

          {!user && (
            <div className="pt-2 flex flex-col gap-2">
              <a
                onClick={closeMobile}
                href="#/login"
                className="w-full text-center py-2 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-500 shadow-xs"
              >
                Sign In
              </a>
              <a
                onClick={closeMobile}
                href="#/register"
                className="w-full text-center py-2 text-xs font-medium text-zinc-300 bg-zinc-900 border border-zinc-800 rounded hover:bg-zinc-800"
              >
                Create Account
              </a>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}

// ─── Home Page ──────────────────────────────────────────────────────────────
function HomePage({ user }) {
  return (
    <div className="py-8 px-4 max-w-4xl mx-auto space-y-10">
      {/* Hero */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl sm:text-4xl font-bold text-zinc-100 tracking-tight">
          Hostel Grievance Platform
        </h1>
        <p className="text-blue-400 font-medium text-sm sm:text-base">
          IIT Patna — Transparent. Accountable. Community-driven.
        </p>
        <div className="bg-zinc-900/80 border-l-2 border-blue-500 border-t border-r border-b border-zinc-800 rounded p-3.5 max-w-xl mx-auto text-left">
          <p className="text-zinc-300 italic text-xs sm:text-sm">
            "One complaint gets ignored. A hundred can't be."
          </p>
        </div>
        <p className="text-zinc-400 text-xs sm:text-sm max-w-xl mx-auto leading-relaxed">
          Consolidate recurring hostel issues into a single transparent system.
          Students support issues that matter, and caretakers are accountable for every response.
        </p>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-wrap justify-center gap-2.5">
          {!user ? (
            <>
              <a
                href="#/login"
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-xs transition-colors duration-150 shadow-xs"
              >
                Sign In
              </a>
              <a
                href="#/register"
                className="px-5 py-2 bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-800 rounded font-medium text-xs transition-colors duration-150"
              >
                Create Account
              </a>
              <a
                href="#/board"
                className="px-5 py-2 bg-zinc-900/60 hover:bg-zinc-850 text-zinc-300 border border-zinc-800/80 rounded font-medium text-xs transition-colors duration-150"
              >
                Browse Public Board
              </a>
            </>
          ) : (
            <>
              <a
                href="#/board"
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-xs transition-colors duration-150 shadow-xs"
              >
                View Complaint Board
              </a>
              {user.role === 'student' && (
                <>
                  <a
                    href="#/submit"
                    className="px-5 py-2 bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-800 rounded font-medium text-xs transition-colors duration-150"
                  >
                    Submit a Complaint
                  </a>
                  <a
                    href="#/my-complaints"
                    className="px-5 py-2 bg-zinc-900/60 hover:bg-zinc-850 text-zinc-300 border border-zinc-800/80 rounded font-medium text-xs transition-colors duration-150"
                  >
                    My Complaints
                  </a>
                </>
              )}
              {user.role === 'caretaker' && (
                <a
                  href="#/caretaker"
                  className="px-5 py-2 bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-800 rounded font-medium text-xs transition-colors duration-150"
                >
                  My Dashboard
                </a>
              )}
              {user.role === 'admin' && (
                <a
                  href="#/admin"
                  className="px-5 py-2 bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-800 rounded font-medium text-xs transition-colors duration-150"
                >
                  Admin Dashboard
                </a>
              )}
            </>
          )}
        </div>
      </div>

      {/* Feature Cards with Direct Nav Buttons */}
      <div className="space-y-3.5">
        <h2 className="text-center text-sm font-semibold text-zinc-200 uppercase tracking-wider">What you can do</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex flex-col justify-between hover:border-zinc-700 transition-colors duration-150">
            <div className="space-y-1.5">
              <h3 className="text-sm font-semibold text-zinc-100 tracking-tight">Report Issues</h3>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Submit complaints with photos, location, and optional anonymity. Get a unique tracking ID instantly.
              </p>
            </div>
            <a
              href={user ? '#/submit' : '#/login'}
              className="mt-4 block text-center py-1.5 px-3 text-xs font-medium text-zinc-200 bg-zinc-800 border border-zinc-700/60 rounded hover:bg-zinc-750 hover:text-white transition-colors duration-150"
            >
              Go to Submit
            </a>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex flex-col justify-between hover:border-zinc-700 transition-colors duration-150">
            <div className="space-y-1.5">
              <h3 className="text-sm font-semibold text-zinc-100 tracking-tight">Community Support</h3>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Upvote issues that affect you too. Multiple votes bubble grievances to caretaker priority.
              </p>
            </div>
            <a
              href="#/board"
              className="mt-4 block text-center py-1.5 px-3 text-xs font-medium text-zinc-200 bg-zinc-800 border border-zinc-700/60 rounded hover:bg-zinc-750 hover:text-white transition-colors duration-150"
            >
              Browse Complaints
            </a>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex flex-col justify-between hover:border-zinc-700 transition-colors duration-150">
            <div className="space-y-1.5">
              <h3 className="text-sm font-semibold text-zinc-100 tracking-tight">Transparent Tracking</h3>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Every grievance logs an immutable timeline — when seen, acknowledged, worked on, and resolved.
              </p>
            </div>
            <a
              href="#/board"
              className="mt-4 block text-center py-1.5 px-3 text-xs font-medium text-zinc-200 bg-zinc-800 border border-zinc-700/60 rounded hover:bg-zinc-750 hover:text-white transition-colors duration-150"
            >
              Track Statuses
            </a>
          </div>
        </div>
      </div>

      {/* How it works */}
      <div className="border-t border-zinc-800/80 pt-8 space-y-4">
        <h2 className="text-center text-sm font-semibold text-zinc-200 uppercase tracking-wider">How it works</h2>
        <div className="space-y-2 max-w-2xl mx-auto">
          {[
            'Student submits a complaint with photos and exact location details.',
            'Other students review and add their support to amplify urgency.',
            'Caretaker is assigned and automatically logs a timestamped "Seen" badge.',
            'Progress is tracked: Acknowledged → In Progress → Resolved.',
            'Student confirms resolution or reopens if the issue persists.',
          ].map((step, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-zinc-900/60 border border-zinc-800 rounded-lg">
              <span className="w-5 h-5 rounded bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs font-mono font-medium flex items-center justify-center flex-shrink-0">
                {idx + 1}
              </span>
              <span className="text-xs text-zinc-300">{step}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Board Page ─────────────────────────────────────────────────────────────
function BoardPage({ user }) {
  const [complaints, setComplaints] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [hostel, setHostel] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [sortBy, setSortBy] = useState('newest');

  const fetchComplaints = useCallback(async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams({
        search, category, hostel, status, priority, sort_by: sortBy, page: page.toString(), page_size: '10'
      });
      const data = await api.request(`/complaints?${q}`);
      setComplaints(data.complaints);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [search, category, hostel, status, priority, sortBy, page]);

  useEffect(() => {
    fetchComplaints();
  }, [fetchComplaints]);

  const handleVote = async (e, id) => {
    e.stopPropagation();
    if (!user) {
      window.location.hash = '#/login';
      return;
    }
    if (user.role !== 'student') return;
    try {
      const res = await api.request(`/complaints/${id}/vote`, { method: 'POST' });
      toast.success(res.message);
      setComplaints(prev => prev.map(c => c.id === id ? { ...c, voted: res.voted, vote_count: res.vote_count } : c));
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <div className="py-6 px-4 max-w-5xl mx-auto space-y-6">
      <BackButton label="Home" to="#/" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">Complaint Board</h1>
          <p className="text-xs text-zinc-400">
            Browse and support hostel grievances raised by the community.
          </p>
        </div>
        {user?.role === 'student' && (
          <a
            href="#/submit"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded transition-colors duration-150 shadow-xs"
          >
            <Icons.Plus /> Submit Complaint
          </a>
        )}
      </div>

      {/* Scope banner for student, caretaker, or public view */}
      {user && user.role !== 'admin' && (
        <div className="py-2.5 px-3.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-300 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span>🏛️</span>
            <span>
              Showing issues for your assigned hostel: <strong>{user.hostel || 'Hostel'}</strong> {user.block ? `(${user.block})` : ''}
            </span>
          </span>
          <span className="text-[10px] bg-zinc-800 px-2 py-0.5 rounded text-zinc-300 border border-zinc-700 font-mono">
            Restricted to your hostel
          </span>
        </div>
      )}
      {!user && (
        <div className="py-2.5 px-3.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-300 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span>🏛️</span>
            <span>
              Public Complaint Board — <strong>Boys Hostels Only</strong> (Kalam, CV Raman, Aryabhatta Blocks A, B, D)
            </span>
          </span>
          <span className="text-[10px] bg-zinc-800 px-2 py-0.5 rounded text-zinc-300 border border-zinc-700 font-medium">
            Boys Hostels
          </span>
        </div>
      )}

      {/* Filters Box */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 space-y-2.5">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <input
            type="text"
            placeholder="Search title, desc, or ID (e.g. TR-2026-0001)..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="sm:col-span-2 px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          />
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            className="px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="most_supported">Most supported</option>
            <option value="priority">Priority</option>
          </select>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-0.5">
          <select
            value={category}
            onChange={(e) => { setCategory(e.target.value); setPage(1); }}
            className="px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
          >
            <option value="">All Categories</option>
            {['Water Supply', 'Plumbing', 'Electrical', 'Washroom & Hygiene', 'Cleaning & Waste', 'Furniture & Fixtures', 'Internet & Wi-Fi', 'Safety & Security', 'Other'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          {user?.role === 'admin' ? (
            <select
              value={hostel}
              onChange={(e) => { setHostel(e.target.value); setPage(1); }}
              className="px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
            >
              <option value="">All Hostels (Admin View)</option>
              {['Aryabhatta', 'Asima', 'Kalam', 'CV Raman'].map(h => (
                <option key={h} value={h}>{h}</option>
              ))}
            </select>
          ) : !user ? (
            <select
              value={hostel}
              onChange={(e) => { setHostel(e.target.value); setPage(1); }}
              className="px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
            >
              <option value="">All Boys Hostels</option>
              <option value="Kalam">Kalam (Blocks A, B, C, D)</option>
              <option value="CV Raman">CV Raman</option>
              <option value="Aryabhatta">Aryabhatta (Blocks A, B, D)</option>
            </select>
          ) : (
            <div className="px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-300 font-medium truncate flex items-center">
              🏛️ {user.hostel} {user.block ? `(${user.block})` : ''}
            </div>
          )}

          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
          >
            <option value="">All Statuses</option>
            {['Submitted', 'Acknowledged', 'Assigned', 'In Progress', 'Resolved', 'Reopened', 'Closed'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select
            value={priority}
            onChange={(e) => { setPriority(e.target.value); setPage(1); }}
            className="px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
          >
            <option value="">All Priorities</option>
            {['Low', 'Medium', 'High', 'Urgent'].map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-zinc-400 px-1">
        <span>{total} complaint{total !== 1 ? 's' : ''} found</span>
        <span>Page {page} of {totalPages}</span>
      </div>

      {/* Complaint List */}
      {loading ? (
        <div className="py-12 text-center text-zinc-400 text-xs">Loading complaints...</div>
      ) : complaints.length === 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg py-12 text-center space-y-2">
          <p className="text-zinc-400 text-xs">No complaints match your filters.</p>
          {(category || hostel || status || priority || search) && (
            <button
              onClick={() => { setSearch(''); setCategory(''); setHostel(''); setStatus(''); setPriority(''); }}
              className="text-xs text-blue-400 hover:underline"
            >
              Reset all filters
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {complaints.map(c => (
            <div
              key={c.id}
              className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 transition-colors duration-150 space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-zinc-400">{c.complaint_number}</span>
                    {c.is_anonymous && (
                      <span className="px-1.5 py-0.2 text-[10px] bg-zinc-800 text-zinc-300 border border-zinc-700 rounded">
                        Anonymous
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-100 tracking-tight">{c.title}</h3>
                  <div className="flex flex-wrap items-center gap-2 pt-0.5">
                    <StatusBadge status={c.status} />
                    <PriorityBadge priority={c.priority} />
                    <SeenBadge isSeen={c.is_seen} isAcknowledged={c.is_acknowledged} />
                  </div>
                </div>

                <div className="text-right text-xs text-zinc-400 space-y-0.5 flex-shrink-0">
                  <div>{c.hostel} {c.block ? `· ${c.block}` : ''}</div>
                  <div className="text-zinc-500">{c.category}</div>
                  <div className="text-[11px] text-zinc-500">{c.created_at}</div>
                </div>
              </div>

              <div className="border-t border-zinc-800 pt-3 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <button
                    onClick={(e) => handleVote(e, c.id)}
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors duration-150 ${
                      c.voted
                        ? 'bg-blue-600 text-white'
                        : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-750 border border-zinc-700/60 hover:text-white'
                    }`}
                  >
                    <Icons.ThumbsUp /> {c.vote_count} {c.voted ? 'Supported' : 'Support'}
                  </button>
                  <span className="text-zinc-500 text-[11px]">Updated {c.updated_at}</span>
                </div>

                <a
                  href={`#/complaint/${c.id}`}
                  className="px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800/80 border border-zinc-700/60 rounded hover:bg-zinc-800 transition-colors duration-150"
                >
                  View Details →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            className="px-3 py-1.5 text-xs font-medium bg-zinc-900 border border-zinc-800 rounded text-zinc-300 disabled:opacity-40 hover:bg-zinc-800 hover:text-white transition-colors duration-150"
          >
            ← Previous
          </button>
          <span className="text-xs text-zinc-400">Page {page} of {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            className="px-3 py-1.5 text-xs font-medium bg-zinc-900 border border-zinc-800 rounded text-zinc-300 disabled:opacity-40 hover:bg-zinc-800 hover:text-white transition-colors duration-150"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Complaint Detail Page ──────────────────────────────────────────────────
function ComplaintDetailPage({ id, user }) {
  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');
  const [isOfficial, setIsOfficial] = useState(false);
  const [actionNotes, setActionNotes] = useState('');
  const [statusVal, setStatusVal] = useState('');
  const [reopenReason, setReopenReason] = useState('');
  const [ackNotes, setAckNotes] = useState('');
  const [ackDate, setAckDate] = useState('');
  const [photoFile, setPhotoFile] = useState(null);
  const toast = useToast();

  const fetchDetail = useCallback(async () => {
    try {
      const data = await api.request(`/complaints/${id}`);
      if (data.merged) {
        window.location.hash = `#/complaint/${data.surviving_id}`;
        return;
      }
      setComplaint(data);
      if (data.allowed_transitions?.length > 0) {
        setStatusVal(data.allowed_transitions[0]);
      }
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  const handleVote = async () => {
    if (!user || user.role !== 'student') return;
    try {
      const res = await api.request(`/complaints/${id}/vote`, { method: 'POST' });
      toast.success(res.message);
      setComplaint(c => ({ ...c, voted: res.voted, vote_count: res.vote_count }));
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    try {
      await api.request(`/complaints/${id}/comments`, {
        method: 'POST',
        body: { content: commentText.trim(), is_official: isOfficial },
      });
      setCommentText('');
      toast.success('Comment added.');
      fetchDetail();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleMarkSeen = async () => {
    try {
      const res = await api.request(`/complaints/${id}/seen`, { method: 'POST' });
      toast.success(res.message);
      fetchDetail();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleAcknowledge = async () => {
    try {
      const res = await api.request(`/complaints/${id}/acknowledge`, {
        method: 'POST',
        body: { work_notes: ackNotes, estimated_completion: ackDate || null },
      });
      toast.success(res.message);
      fetchDetail();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleStatusUpdate = async () => {
    try {
      const res = await api.request(`/complaints/${id}/status`, {
        method: 'POST',
        body: { new_status: statusVal, notes: actionNotes },
      });
      toast.success(res.message);
      setActionNotes('');
      fetchDetail();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleConfirmResolved = async () => {
    try {
      const res = await api.request(`/complaints/${id}/confirm-resolved`, { method: 'POST' });
      toast.success(res.message);
      fetchDetail();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleReopen = async () => {
    if (!reopenReason.trim()) {
      toast.error('Please enter a reason for reopening.');
      return;
    }
    try {
      const res = await api.request(`/complaints/${id}/status`, {
        method: 'POST',
        body: { new_status: 'Reopened', notes: reopenReason },
      });
      toast.success(res.message);
      setReopenReason('');
      fetchDetail();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleUploadResolutionPhoto = async (e) => {
    e.preventDefault();
    if (!photoFile) return;
    const fd = new FormData();
    fd.append('file', photoFile);
    fd.append('photo_type', 'resolution_photo');
    try {
      const res = await api.request(`/complaints/${id}/upload-photo`, {
        method: 'POST',
        body: fd,
      });
      toast.success(res.message);
      setPhotoFile(null);
      fetchDetail();
    } catch (err) {
      toast.error(err.message);
    }
  };

  if (loading) return <div className="py-12 text-center text-zinc-400 text-xs">Loading details...</div>;
  if (!complaint) return <div className="py-12 text-center text-rose-400 text-xs">Complaint not found.</div>;

  return (
    <div className="py-6 px-4 max-w-5xl mx-auto space-y-6">
      <BackButton label="Back to Board" to="#/board" />

      {/* Header */}
      <div className="space-y-2 border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-400 font-medium">{complaint.complaint_number}</span>
          {complaint.is_anonymous && (
            <span className="px-1.5 py-0.5 text-xs bg-zinc-800 text-zinc-300 border border-zinc-700 rounded">
              Anonymous Submission
            </span>
          )}
        </div>
        <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">{complaint.title}</h1>
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <StatusBadge status={complaint.status} />
          <PriorityBadge priority={complaint.priority} />
          <SeenBadge isSeen={complaint.is_seen} isAcknowledged={complaint.acknowledged_at !== null} />
        </div>
      </div>

      {/* Two Column Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Description, Photos, Location, Timeline */}
        <div className="md:col-span-2 space-y-6">
          {/* Description */}
          <div className="space-y-1.5">
            <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Description</h3>
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-xs sm:text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed">
              {complaint.description}
            </div>
          </div>

          {/* Caretaker Seen Status Callout */}
          <div className="space-y-1.5">
            <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Caretaker Status</h3>
            {complaint.is_seen ? (
              <div className="bg-zinc-900 border border-sky-900/40 rounded-lg p-4 space-y-2 text-xs">
                <div className="font-semibold text-sky-400 flex items-center gap-1.5">
                  <Icons.Eye /> Seen by Caretaker
                </div>
                <div className="text-zinc-300">
                  {complaint.caretaker_name || 'Caretaker'} first inspected this grievance on{' '}
                  <span className="font-medium text-zinc-100">{complaint.first_seen_at}</span>.
                </div>
                {complaint.acknowledged_at && (
                  <div className="text-emerald-400">
                    Acknowledged on: <span className="font-medium text-zinc-100">{complaint.acknowledged_at}</span>
                  </div>
                )}
                {complaint.work_notes && (
                  <div className="text-zinc-300 pt-1.5 border-t border-zinc-800">
                    <strong className="text-zinc-200">Work Notes:</strong> {complaint.work_notes}
                  </div>
                )}
                {complaint.estimated_completion && (
                  <div className="text-zinc-300">
                    <strong className="text-zinc-200">Estimated Completion:</strong> {complaint.estimated_completion}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-xs space-y-1">
                <div className="font-semibold text-zinc-400">Not yet seen by caretaker</div>
                <div className="text-zinc-500">No caretaker has opened this grievance yet.</div>
              </div>
            )}
          </div>

          {/* Photos */}
          {complaint.photos?.length > 0 && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Photo Evidence</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {complaint.photos.map(p => (
                  <a
                    key={p.id}
                    href={p.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden group hover:border-zinc-700 transition-colors duration-150"
                  >
                    <img src={p.url} alt={p.filename} className="w-full h-32 object-cover group-hover:opacity-90 transition-opacity" />
                    <div className="p-1.5 text-[10px] text-zinc-400 truncate">{p.filename}</div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Resolution Photos */}
          {complaint.resolution_photos?.length > 0 && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Resolution Evidence</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {complaint.resolution_photos.map(p => (
                  <a
                    key={p.id}
                    href={p.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block bg-zinc-900 border border-emerald-900/60 rounded-lg overflow-hidden group hover:border-emerald-700 transition-colors duration-150"
                  >
                    <img src={p.url} alt={p.filename} className="w-full h-32 object-cover group-hover:opacity-90 transition-opacity" />
                    <div className="p-1.5 text-[10px] text-emerald-400 truncate">{p.filename}</div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Location & Metadata Details */}
          <div className="space-y-1.5">
            <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Location & Submitter</h3>
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 text-xs divide-y divide-zinc-800">
              <div className="py-1.5 flex justify-between"><span className="text-zinc-400">Hostel</span><span className="text-zinc-100 font-medium">{complaint.hostel}</span></div>
              {complaint.block && <div className="py-1.5 flex justify-between"><span className="text-zinc-400">Block</span><span className="text-zinc-100 font-medium">{complaint.block}</span></div>}
              {complaint.floor && <div className="py-1.5 flex justify-between"><span className="text-zinc-400">Floor</span><span className="text-zinc-100 font-medium">{complaint.floor}</span></div>}
              {complaint.location_detail && <div className="py-1.5 flex justify-between"><span className="text-zinc-400">Specific Location</span><span className="text-zinc-100 font-medium">{complaint.location_detail}</span></div>}
              <div className="py-1.5 flex justify-between"><span className="text-zinc-400">Category</span><span className="text-zinc-100 font-medium">{complaint.category}</span></div>
              <div className="py-1.5 flex justify-between"><span className="text-zinc-400">Submitted by</span><span className="text-zinc-100 font-medium">{complaint.submitter_name}</span></div>
              <div className="py-1.5 flex justify-between"><span className="text-zinc-400">Created</span><span className="text-zinc-300">{complaint.created_at}</span></div>
              <div className="py-1.5 flex justify-between"><span className="text-zinc-400">Last updated</span><span className="text-zinc-300">{complaint.updated_at}</span></div>
            </div>
          </div>

          {/* Activity Timeline */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Activity Timeline</h3>
            <div className="space-y-2">
              {complaint.timeline.map((item, idx) => (
                <div key={idx} className="p-3 bg-zinc-900 border-l-2 border-zinc-700 border-t border-r border-b border-zinc-800 rounded-r text-xs space-y-1">
                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="font-medium text-zinc-100">
                      {item.old_status ? `${item.old_status} → ` : ''}{item.new_status}
                    </span>
                    <span className="text-[11px] text-zinc-500">{item.created_at}</span>
                  </div>
                  <div className="text-zinc-400">Updated by: <span className="text-zinc-300">{item.actor}</span></div>
                  {item.notes && <div className="text-zinc-300 italic pt-0.5">"{item.notes}"</div>}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Actions (Support, Caretaker Actions, Discussion) */}
        <div className="space-y-5">
          {/* Support Counter & Button */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-center space-y-2.5">
            <div className="text-2xl font-mono font-bold text-zinc-100">{complaint.vote_count}</div>
            <div className="text-xs text-zinc-400">Student Supporters</div>
            {user?.role === 'student' && (
              <button
                onClick={handleVote}
                className={`w-full py-1.5 px-3 text-xs font-medium rounded transition-colors duration-150 ${
                  complaint.voted
                    ? 'bg-zinc-800 text-zinc-300 border border-zinc-700 hover:bg-zinc-750'
                    : 'bg-blue-600 hover:bg-blue-500 text-white shadow-xs'
                }`}
              >
                {complaint.voted ? 'Remove Support' : 'Add Support'}
              </button>
            )}
          </div>

          {/* Student Resolution Actions */}
          {user?.role === 'student' && complaint.submitter_id === user.id && complaint.status === 'Resolved' && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
              <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Resolution Confirmation</h4>
              {!complaint.student_confirmed_resolved ? (
                <div className="space-y-2">
                  <button
                    onClick={handleConfirmResolved}
                    className="w-full py-1.5 px-3 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white rounded transition-colors duration-150"
                  >
                    Confirm Resolved
                  </button>
                  <div className="pt-2 border-t border-zinc-800 space-y-2">
                    <input
                      type="text"
                      placeholder="Reason to reopen..."
                      value={reopenReason}
                      onChange={(e) => setReopenReason(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
                    />
                    <button
                      onClick={handleReopen}
                      className="w-full py-1.5 px-3 text-xs font-medium text-rose-300 bg-rose-950/40 border border-rose-800/60 rounded hover:bg-rose-900/50 transition-colors duration-150"
                    >
                      Reopen Grievance
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-2.5 bg-emerald-950/30 border border-emerald-800/50 rounded text-xs text-emerald-300 text-center">
                  You confirmed this resolution. Thank you!
                </div>
              )}
            </div>
          )}

          {/* Caretaker / Admin Actions Box */}
          {user && (user.role === 'caretaker' || user.role === 'admin') && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3.5">
              <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Caretaker Controls</h4>

              {/* Mark Seen */}
              {!complaint.is_seen && (
                <button
                  onClick={handleMarkSeen}
                  className="w-full py-1.5 px-3 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded flex items-center justify-center gap-1.5 transition-colors duration-150"
                >
                  <Icons.Eye /> Mark as Seen
                </button>
              )}

              {/* Acknowledge */}
              {!complaint.acknowledged_at && (
                <div className="space-y-2 pt-2 border-t border-zinc-800">
                  <div className="text-xs font-medium text-zinc-300">Acknowledge Complaint</div>
                  <textarea
                    placeholder="Work notes (e.g. Electrician scheduled for 3 PM)..."
                    value={ackNotes}
                    onChange={(e) => setAckNotes(e.target.value)}
                    rows="2"
                    className="w-full px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
                  />
                  <input
                    type="date"
                    value={ackDate}
                    onChange={(e) => setAckDate(e.target.value)}
                    className="w-full px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
                  />
                  <button
                    onClick={handleAcknowledge}
                    className="w-full py-1.5 px-3 text-xs font-medium bg-amber-600 hover:bg-amber-500 text-white rounded transition-colors duration-150"
                  >
                    Confirm Acknowledgement
                  </button>
                </div>
              )}

              {/* Status Update */}
              {complaint.allowed_transitions?.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-zinc-800">
                  <div className="text-xs font-medium text-zinc-300">Update Status</div>
                  <select
                    value={statusVal}
                    onChange={(e) => setStatusVal(e.target.value)}
                    className="w-full px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
                  >
                    {complaint.allowed_transitions.map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                  <input
                    type="text"
                    placeholder="Status update notes..."
                    value={actionNotes}
                    onChange={(e) => setActionNotes(e.target.value)}
                    className="w-full px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
                  />
                  <button
                    onClick={handleStatusUpdate}
                    className="w-full py-1.5 px-3 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors duration-150"
                  >
                    Update Status
                  </button>
                </div>
              )}

              {/* Upload Resolution Photo */}
              {(complaint.status === 'In Progress' || complaint.status === 'Resolved') && (
                <form onSubmit={handleUploadResolutionPhoto} className="space-y-2 pt-2 border-t border-zinc-800">
                  <div className="text-xs font-medium text-zinc-300">Upload Resolution Photo</div>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setPhotoFile(e.target.files[0])}
                    className="w-full text-xs text-zinc-400 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-zinc-800 file:text-zinc-200"
                  />
                  <button
                    type="submit"
                    disabled={!photoFile}
                    className="w-full py-1.5 px-3 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white rounded transition-colors duration-150"
                  >
                    Upload Proof
                  </button>
                </form>
              )}
            </div>
          )}

          {/* Discussion / Comments Section */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3.5">
            <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Discussion</h4>
            <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
              {complaint.comments?.length === 0 ? (
                <p className="text-xs text-zinc-500 text-center py-4">No comments yet.</p>
              ) : (
                complaint.comments.map(cm => (
                  <div
                    key={cm.id}
                    className={`p-3 rounded text-xs space-y-1 border ${
                      cm.is_official
                        ? 'bg-blue-950/20 border-blue-900/40'
                        : 'bg-zinc-950/60 border-zinc-800'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-zinc-200">
                        {cm.author_name}
                        {cm.is_official && (
                          <span className="ml-1.5 px-1.5 py-0.2 text-[9px] bg-blue-600 text-white rounded font-medium">
                            Official
                          </span>
                        )}
                      </span>
                      <span className="text-[10px] text-zinc-500">{cm.created_at}</span>
                    </div>
                    <div className="text-zinc-300 whitespace-pre-wrap">{cm.content}</div>
                  </div>
                ))
              )}
            </div>

            {/* Comment Form */}
            {user ? (
              <form onSubmit={handleComment} className="space-y-2 pt-2 border-t border-zinc-800">
                <textarea
                  placeholder="Add a comment..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  rows="2"
                  className="w-full px-2.5 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600"
                />
                {(user.role === 'caretaker' || user.role === 'admin') && (
                  <label className="flex items-center gap-2 text-xs text-zinc-300">
                    <input
                      type="checkbox"
                      checked={isOfficial}
                      onChange={(e) => setIsOfficial(e.target.checked)}
                      className="rounded border-zinc-800 bg-zinc-950 text-blue-600 focus:ring-0"
                    />
                    Post as official caretaker update
                  </label>
                )}
                <button
                  type="submit"
                  className="w-full py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors duration-150 shadow-xs"
                >
                  Post Comment
                </button>
              </form>
            ) : (
              <div className="text-center pt-2">
                <a href="#/login" className="text-xs text-blue-400 hover:underline">
                  Sign in to join the discussion
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Submit Page ────────────────────────────────────────────────────────────
function SubmitPage({ user }) {
  const isStudent = user?.role === 'student';
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Water Supply');
  const [hostel, setHostel] = useState(user?.hostel || 'Aryabhatta');
  const [block, setBlock] = useState(user?.block || '');
  const [floor, setFloor] = useState('');
  const [locationDetail, setLocationDetail] = useState('');
  const [description, setDescription] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [files, setFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [createdResult, setCreatedResult] = useState(null);
  const toast = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      toast.error('Title and description are required.');
      return;
    }

    const targetHostel = isStudent ? (user?.hostel || hostel) : hostel;
    const targetBlock = isStudent ? (user?.block || block) : block;

    setSubmitting(true);
    const fd = new FormData();
    fd.append('title', title.trim());
    fd.append('description', description.trim());
    fd.append('category', category);
    fd.append('hostel', targetHostel);
    fd.append('block', targetBlock.trim());
    fd.append('floor', floor.trim());
    fd.append('location_detail', locationDetail.trim());
    fd.append('is_anonymous', isAnonymous ? 'true' : 'false');
    fd.append('priority', 'Medium');
    fd.append('is_public', 'true');

    for (let f of files) {
      fd.append('photos', f);
    }

    try {
      const res = await api.request('/complaints', { method: 'POST', body: fd });
      setCreatedResult(res);
      toast.success(res.message);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (createdResult) {
    return (
      <div className="py-12 px-4 max-w-xl mx-auto text-center space-y-6">
        <div className="w-12 h-12 bg-emerald-950/60 border border-emerald-800 text-emerald-400 rounded-full flex items-center justify-center mx-auto text-xl">
          <Icons.Check />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-xl font-bold text-zinc-100 tracking-tight">Grievance Submitted</h2>
          <p className="text-xs text-zinc-400">
            Your tracking ID is{' '}
            <span className="font-mono font-medium text-zinc-100 bg-zinc-800 border border-zinc-700 px-2 py-0.5 rounded">
              {createdResult.complaint_number}
            </span>
          </p>
        </div>

        {/* Clear direct action button */}
        <div className="pt-2 flex flex-col sm:flex-row justify-center gap-2.5">
          <a
            href={`#/complaint/${createdResult.complaint_id}`}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded transition-colors duration-150 shadow-xs"
          >
            View Complaint Details
          </a>
          <a
            href="#/board"
            className="px-5 py-2 bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-800 font-medium text-xs rounded transition-colors duration-150"
          >
            Go to Complaint Board
          </a>
          <button
            onClick={() => {
              setCreatedResult(null);
              setTitle('');
              setDescription('');
              setFiles([]);
            }}
            className="px-5 py-2 bg-zinc-900/60 hover:bg-zinc-850 text-zinc-400 hover:text-zinc-200 font-medium text-xs rounded border border-zinc-800/80 transition-colors duration-150"
          >
            Submit Another
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6 px-4 max-w-2xl mx-auto space-y-6">
      <BackButton label="Home" to="#/" />

      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">Submit a Complaint</h1>
        <p className="text-xs text-zinc-400">
          Report a hostel issue. Your complaint ID will be generated automatically.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
        {/* Allocated hostel banner for students */}
        {isStudent && (
          <div className="p-3 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-300 flex items-center gap-2">
            <span>🏛️</span>
            <span>
              You are submitting this grievance for your allocated hostel: <strong>{user?.hostel || 'Hostel'}</strong> {user?.block ? `(${user.block})` : ''}.
            </span>
          </div>
        )}

        {/* Title */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Complaint Title *</label>
          <input
            type="text"
            required
            placeholder="e.g. Water cooler not working on 2nd floor"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          />
        </div>

        {/* Category & Hostel */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-300">Category *</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
            >
              {['Water Supply', 'Plumbing', 'Electrical', 'Washroom & Hygiene', 'Cleaning & Waste', 'Furniture & Fixtures', 'Internet & Wi-Fi', 'Safety & Security', 'Other'].map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-300">
              Hostel * {isStudent && <span className="text-zinc-500 font-normal">(Allocated)</span>}
            </label>
            {isStudent ? (
              <input
                type="text"
                readOnly
                value={user?.hostel || 'Hostel'}
                className="w-full px-3 py-1.5 bg-zinc-950/60 border border-zinc-800/60 rounded text-xs text-zinc-400 cursor-not-allowed"
              />
            ) : (
              <select
                value={hostel}
                onChange={(e) => setHostel(e.target.value)}
                className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
              >
                {['Aryabhatta', 'Asima', 'Kalam', 'CV Raman'].map(h => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Block, Floor, Specific Location */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-300">
              Block / Building {isStudent && user?.block && <span className="text-zinc-500 font-normal">(Allocated)</span>}
            </label>
            {isStudent && user?.block ? (
              <input
                type="text"
                readOnly
                value={user.block}
                className="w-full px-3 py-1.5 bg-zinc-950/60 border border-zinc-800/60 rounded text-xs text-zinc-400 cursor-not-allowed"
              />
            ) : (
              <input
                type="text"
                placeholder="e.g. Block B"
                value={block}
                onChange={(e) => setBlock(e.target.value)}
                className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
              />
            )}
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-300">Floor</label>
            <input
              type="text"
              placeholder="e.g. 2nd Floor"
              value={floor}
              onChange={(e) => setFloor(e.target.value)}
              className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-300">Exact Location</label>
            <input
              type="text"
              placeholder="e.g. Near Room 214"
              value={locationDetail}
              onChange={(e) => setLocationDetail(e.target.value)}
              className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-200 focus:outline-none focus:border-zinc-600"
            />
          </div>
        </div>

        {/* Description */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Detailed Description *</label>
          <textarea
            required
            rows="4"
            placeholder="Describe the issue clearly. When did it start? How severe is it?"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          />
        </div>

        {/* Photos */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Photo Evidence (optional)</label>
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={(e) => setFiles(Array.from(e.target.files))}
            className="w-full text-xs text-zinc-400 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-750"
          />
        </div>

        {/* Anonymous Checkbox */}
        <div className="pt-1">
          <label className="flex items-center gap-2.5 p-3 bg-zinc-950 border border-zinc-800 rounded cursor-pointer">
            <input
              type="checkbox"
              checked={isAnonymous}
              onChange={(e) => setIsAnonymous(e.target.checked)}
              className="w-4 h-4 rounded border-zinc-800 bg-zinc-950 text-blue-600 focus:ring-0"
            />
            <div>
              <div className="text-xs font-medium text-zinc-200">Submit Anonymously</div>
              <div className="text-[11px] text-zinc-500">
                Your name will be hidden on the public board and timeline.
              </div>
            </div>
          </label>
        </div>

        {/* Submit Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs rounded transition-colors duration-150 shadow-xs"
          >
            {submitting ? 'Submitting...' : 'Submit Complaint'}
          </button>
        </div>
      </form>
    </div>
  );
}

// ─── My Complaints Page ─────────────────────────────────────────────────────
function MyComplaintsPage({ user }) {
  const [tab, setTab] = useState('mine');
  const [data, setData] = useState({ my_submissions: [], supported_complaints: [] });
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const fetchData = useCallback(async () => {
    try {
      const res = await api.request('/my-complaints');
      setData(res);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDelete = async (id) => {
    try {
      const res = await api.request(`/complaints/${id}`, { method: 'DELETE' });
      toast.success(res.message);
      setDeleteConfirmId(null);
      setData(d => ({
        ...d,
        my_submissions: d.my_submissions.filter(c => c.id !== id),
      }));
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <div className="py-6 px-4 max-w-5xl mx-auto space-y-6">
      <BackButton label="Home" to="#/" />

      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">My Complaints</h1>
        <p className="text-xs text-zinc-400">
          Your submissions and supported grievances, {user?.display_name}.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-zinc-800 gap-4 text-xs font-medium">
        <button
          onClick={() => setTab('mine')}
          className={`pb-2 border-b-2 transition-colors duration-150 ${
            tab === 'mine' ? 'border-blue-500 text-zinc-100' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          My Submissions ({data.my_submissions.length})
        </button>
        <button
          onClick={() => setTab('supported')}
          className={`pb-2 border-b-2 transition-colors duration-150 ${
            tab === 'supported' ? 'border-blue-500 text-zinc-100' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          Supported Issues ({data.supported_complaints.length})
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-zinc-400 text-xs">Loading complaints...</div>
      ) : tab === 'mine' ? (
        data.my_submissions.length === 0 ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg py-12 text-center space-y-3">
            <p className="text-zinc-400 text-xs">You haven't submitted any complaints yet.</p>
            <a href="#/submit" className="inline-block px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded shadow-xs transition-colors duration-150">
              Submit your first complaint
            </a>
          </div>
        ) : (
          <div className="space-y-3">
            {data.my_submissions.map(c => (
              <div key={c.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
                <div className="flex flex-col sm:flex-row justify-between gap-2">
                  <div className="space-y-1">
                    <span className="text-xs font-mono text-zinc-400">{c.complaint_number}</span>
                    <h3 className="text-sm font-semibold text-zinc-100 tracking-tight">{c.title}</h3>
                    <div className="flex flex-wrap gap-2 pt-0.5">
                      <StatusBadge status={c.status} />
                      <PriorityBadge priority={c.priority} />
                      <SeenBadge isSeen={c.is_seen} isAcknowledged={c.is_acknowledged} />
                    </div>
                  </div>
                  <div className="text-right text-xs text-zinc-400">
                    <div>{c.hostel} {c.block ? `· ${c.block}` : ''}</div>
                    <div className="text-[11px] text-zinc-500">{c.created_at}</div>
                  </div>
                </div>

                <div className="border-t border-zinc-800 pt-3 flex items-center justify-between">
                  <span className="text-xs text-zinc-400">{c.vote_count} supporter{c.vote_count !== 1 ? 's' : ''}</span>

                  <div className="flex items-center gap-2">
                    {/* Delete Option for Submitted complaints */}
                    {c.status === 'Submitted' && (
                      deleteConfirmId === c.id ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleDelete(c.id)}
                            className="px-2.5 py-1 text-xs bg-rose-600 hover:bg-rose-500 text-white font-medium rounded transition-colors duration-150"
                          >
                            Confirm Delete
                          </button>
                          <button
                            onClick={() => setDeleteConfirmId(null)}
                            className="px-2.5 py-1 text-xs bg-zinc-800 text-zinc-300 hover:bg-zinc-750 rounded transition-colors duration-150"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setDeleteConfirmId(c.id)}
                          className="px-2 py-1 text-xs text-rose-400 hover:text-rose-300 bg-zinc-950 border border-rose-900/40 rounded transition-colors duration-150"
                        >
                          <Icons.Trash /> Delete
                        </button>
                      )
                    )}

                    <a
                      href={`#/complaint/${c.id}`}
                      className="px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800/80 border border-zinc-700/60 rounded hover:bg-zinc-800 transition-colors duration-150"
                    >
                      View Details →
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        data.supported_complaints.length === 0 ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg py-12 text-center">
            <p className="text-zinc-400 text-xs">You haven't supported any complaints yet.</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {data.supported_complaints.map(c => (
              <div key={c.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 flex justify-between items-center">
                <div className="space-y-1">
                  <span className="text-xs font-mono text-zinc-400">{c.complaint_number}</span>
                  <h3 className="text-sm font-semibold text-zinc-100 tracking-tight">{c.title}</h3>
                  <div className="flex gap-2">
                    <StatusBadge status={c.status} />
                    <SeenBadge isSeen={c.is_seen} isAcknowledged={c.is_acknowledged} />
                  </div>
                </div>
                <a
                  href={`#/complaint/${c.id}`}
                  className="px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800/80 border border-zinc-700/60 rounded hover:bg-zinc-800 transition-colors duration-150"
                >
                  View →
                </a>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}

// ─── Caretaker Dashboard ────────────────────────────────────────────────────
function CaretakerDashboard({ user }) {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState('unseen');
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const fetchData = useCallback(async () => {
    try {
      const res = await api.request('/caretaker/dashboard');
      setData(res);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const markSeen = async (id) => {
    try {
      const res = await api.request(`/complaints/${id}/seen`, { method: 'POST' });
      toast.success(res.message);
      fetchData();
    } catch (err) {
      toast.error(err.message);
    }
  };

  if (loading) return <div className="py-12 text-center text-zinc-400 text-xs">Loading dashboard...</div>;
  if (!data) return null;

  const currentList = data[tab] || [];

  return (
    <div className="py-6 px-4 max-w-5xl mx-auto space-y-6">
      <BackButton label="Home" to="#/" />

      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">Caretaker Dashboard</h1>
          {user?.hostel && (
            <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
              {user.hostel} {user.block ? `(${user.block})` : ''}
            </span>
          )}
        </div>
        <p className="text-xs text-zinc-400">Welcome, {user?.display_name}. Managing grievances for {user?.hostel || 'assigned hostel'}.</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
        {[
          { label: 'Assigned', val: data.metrics.total_assigned, color: 'text-zinc-100 border-zinc-700' },
          { label: 'New / Unseen', val: data.metrics.new_unseen, color: 'text-rose-400 border-rose-900/60' },
          { label: 'Acknowledged', val: data.metrics.acknowledged, color: 'text-amber-400 border-amber-900/60' },
          { label: 'In Progress', val: data.metrics.in_progress, color: 'text-sky-400 border-sky-900/60' },
          { label: 'Overdue (>3d)', val: data.metrics.overdue, color: 'text-purple-400 border-purple-900/60' },
        ].map((m, idx) => (
          <div key={idx} className={`bg-zinc-900 border border-zinc-800 border-t-2 ${m.color} rounded-lg p-3 text-center`}>
            <div className={`text-2xl font-bold font-mono ${m.color.split(' ')[0]}`}>{m.val}</div>
            <div className="text-[11px] text-zinc-400 mt-0.5">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-zinc-800 gap-4 text-xs font-medium">
        {[
          { id: 'unseen', label: `Unseen (${data.unseen.length})` },
          { id: 'assigned', label: `Assigned (${data.assigned.length})` },
          { id: 'in_progress', label: `In Progress (${data.in_progress.length})` },
          { id: 'all', label: `All (${data.all.length})` },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`pb-2 border-b-2 transition-colors duration-150 ${
              tab === t.id ? 'border-blue-500 text-zinc-100' : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Items */}
      {currentList.length === 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg py-12 text-center text-zinc-400 text-xs">
          No complaints in this category.
        </div>
      ) : (
        <div className="space-y-2.5">
          {currentList.map(c => (
            <div key={c.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div className="space-y-1">
                <span className="text-xs font-mono text-zinc-400">{c.complaint_number}</span>
                <h3 className="text-sm font-semibold text-zinc-100 tracking-tight">{c.title}</h3>
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={c.status} />
                  <PriorityBadge priority={c.priority} />
                  <SeenBadge isSeen={c.is_seen} isAcknowledged={c.is_acknowledged} />
                </div>
              </div>

              <div className="flex items-center gap-2">
                {!c.is_seen && (
                  <button
                    onClick={() => markSeen(c.id)}
                    className="px-2.5 py-1 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors duration-150 shadow-xs"
                  >
                    Mark Seen
                  </button>
                )}
                <a
                  href={`#/complaint/${c.id}`}
                  className="px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800/80 border border-zinc-700/60 rounded hover:bg-zinc-800 transition-colors duration-150"
                >
                  Inspect →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Admin Dashboard ────────────────────────────────────────────────────────
function AdminDashboard({ user }) {
  const [tab, setTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const fetchAdminData = useCallback(async () => {
    try {
      const [ov, u, lg] = await Promise.all([
        api.request('/admin/overview'),
        api.request('/admin/users'),
        api.request('/admin/audit-logs'),
      ]);
      setOverview(ov);
      setUsers(u);
      setLogs(lg);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAdminData();
  }, [fetchAdminData]);

  if (loading) return <div className="py-12 text-center text-zinc-400 text-xs">Loading admin panel...</div>;

  return (
    <div className="py-6 px-4 max-w-5xl mx-auto space-y-6">
      <BackButton label="Home" to="#/" />

      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">Admin Dashboard</h1>
        <p className="text-xs text-zinc-400">Manage hostel complaints, assignments, users, and audit records.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-zinc-800 gap-4 text-xs font-medium">
        {['overview', 'users', 'audit'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-2 border-b-2 uppercase tracking-wider transition-colors duration-150 ${
              tab === t ? 'border-blue-500 text-zinc-100' : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'overview' && overview && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {[
              { label: 'Total Complaints', val: overview.total_complaints },
              { label: 'Unassigned', val: overview.unassigned_complaints },
              { label: 'Unseen', val: overview.unseen_complaints },
              { label: 'Registered Users', val: overview.total_users },
            ].map((m, idx) => (
              <div key={idx} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 text-center">
                <div className="text-2xl font-bold font-mono text-zinc-100">{m.val}</div>
                <div className="text-xs text-zinc-400 mt-1">{m.label}</div>
              </div>
            ))}
          </div>

          <div className="flex gap-2.5">
            <a href="#/board" className="px-3.5 py-1.5 text-xs font-medium bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-800 rounded transition-colors duration-150">
              Manage All Complaints on Board →
            </a>
            <a href="#/analytics" className="px-3.5 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors duration-150 shadow-xs">
              View Analytics & Charts →
            </a>
          </div>
        </div>
      )}

      {tab === 'users' && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-950 text-zinc-400 uppercase text-[10px] tracking-wider border-b border-zinc-800">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Name</th>
                <th className="py-2.5 px-3 font-semibold">Email</th>
                <th className="py-2.5 px-3 font-semibold">Role</th>
                <th className="py-2.5 px-3 font-semibold">Hostel</th>
                <th className="py-2.5 px-3 font-semibold">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {users.map(u => (
                <tr key={u.id} className="hover:bg-zinc-850/50 transition-colors duration-100">
                  <td className="py-2 px-3 font-medium text-zinc-100">{u.display_name}</td>
                  <td className="py-2 px-3 text-zinc-400">{u.email}</td>
                  <td className="py-2 px-3"><span className="uppercase text-[10px] font-mono font-medium text-zinc-300">{u.role}</span></td>
                  <td className="py-2 px-3 text-zinc-400">{u.hostel || '—'}</td>
                  <td className="py-2 px-3 text-zinc-500">{u.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'audit' && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-950 text-zinc-400 uppercase text-[10px] tracking-wider border-b border-zinc-800">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Timestamp</th>
                <th className="py-2.5 px-3 font-semibold">Action</th>
                <th className="py-2.5 px-3 font-semibold">Actor</th>
                <th className="py-2.5 px-3 font-semibold">Entity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {logs.map(l => (
                <tr key={l.id} className="hover:bg-zinc-850/50 transition-colors duration-100">
                  <td className="py-2 px-3 text-zinc-500">{l.created_at}</td>
                  <td className="py-2 px-3 font-mono text-zinc-300">{l.action}</td>
                  <td className="py-2 px-3 text-zinc-200 font-medium">{l.actor}</td>
                  <td className="py-2 px-3 text-zinc-500">{l.entity_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Analytics Page ─────────────────────────────────────────────────────────
function AnalyticsPage({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  useEffect(() => {
    (async () => {
      try {
        const res = await api.request('/analytics');
        setData(res);
      } catch (err) {
        toast.error(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="py-12 text-center text-zinc-400 text-xs">Loading analytics...</div>;
  if (!data) return null;

  return (
    <div className="py-6 px-4 max-w-5xl mx-auto space-y-6">
      <BackButton label="Home" to="#/" />

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">Analytics & Performance</h1>
          <p className="text-xs text-zinc-400">Real-time metrics calculated from live database records.</p>
        </div>
        <a
          href="/api/analytics/export"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded shadow-xs transition-colors duration-150"
        >
          <Icons.Download /> Download CSV Export
        </a>
      </div>

      {/* SLA Averages */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 text-center">
          <div className="text-2xl font-bold font-mono text-zinc-100">
            {data.avg_seen_hours !== null ? `${data.avg_seen_hours.toFixed(1)} hrs` : '—'}
          </div>
          <div className="text-xs text-zinc-400 mt-1">Avg Time to First Seen</div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 text-center">
          <div className="text-2xl font-bold font-mono text-zinc-100">
            {data.avg_ack_hours !== null ? `${data.avg_ack_hours.toFixed(1)} hrs` : '—'}
          </div>
          <div className="text-xs text-zinc-400 mt-1">Avg Time to Acknowledgement</div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 text-center">
          <div className="text-2xl font-bold font-mono text-zinc-100">
            {data.avg_resolution_hours !== null ? `${data.avg_resolution_hours.toFixed(1)} hrs` : '—'}
          </div>
          <div className="text-xs text-zinc-400 mt-1">Avg Time to Resolution</div>
        </div>
      </div>

      {/* Breakdowns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
          <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">By Category</h3>
          <div className="space-y-1">
            {Object.entries(data.by_category || {}).map(([cat, count]) => (
              <div key={cat} className="flex justify-between text-xs py-1.5 border-b border-zinc-800">
                <span className="text-zinc-300">{cat}</span>
                <span className="font-mono font-medium text-zinc-100">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
          <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">By Hostel</h3>
          <div className="space-y-1">
            {Object.entries(data.by_hostel || {}).map(([hst, count]) => (
              <div key={hst} className="flex justify-between text-xs py-1.5 border-b border-zinc-800">
                <span className="text-zinc-300">{hst}</span>
                <span className="font-mono font-medium text-zinc-100">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Notifications Page ─────────────────────────────────────────────────────
function NotificationsPage({ user, onRead }) {
  const [notifs, setNotifs] = useState([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const fetchNotifs = useCallback(async () => {
    try {
      const res = await api.request('/notifications');
      setNotifs(res.notifications);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifs();
  }, [fetchNotifs]);

  const handleMarkAllRead = async () => {
    try {
      await api.request('/notifications/read-all', { method: 'POST' });
      toast.success('Marked all as read.');
      setNotifs(n => n.map(x => ({ ...x, is_read: true })));
      onRead();
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <div className="py-6 px-4 max-w-2xl mx-auto space-y-4">
      <BackButton label="Home" to="#/" />

      <div className="flex items-center justify-between">
        <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">Notifications</h1>
        {notifs.some(n => !n.is_read) && (
          <button
            onClick={handleMarkAllRead}
            className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors duration-150"
          >
            Mark all as read
          </button>
        )}
      </div>

      {loading ? (
        <div className="py-12 text-center text-zinc-400 text-xs">Loading...</div>
      ) : notifs.length === 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg py-12 text-center text-zinc-400 text-xs">
          No notifications.
        </div>
      ) : (
        <div className="space-y-2">
          {notifs.map(n => (
            <div
              key={n.id}
              className={`p-3 rounded-lg border text-xs space-y-1 transition-colors duration-150 ${
                n.is_read
                  ? 'bg-zinc-900/60 border-zinc-800 text-zinc-300'
                  : 'bg-zinc-900 border-zinc-700 text-zinc-100'
              }`}
            >
              <div className="flex items-center justify-between text-[11px] text-zinc-400">
                <span>{n.created_at}</span>
                {!n.is_read && <span className="text-blue-400 font-mono font-medium uppercase text-[9px] tracking-wider">New</span>}
              </div>
              <p>{n.message}</p>
              {n.complaint_id && (
                <a
                  href={`#/complaint/${n.complaint_id}`}
                  className="inline-block pt-1 text-xs text-blue-400 hover:underline font-medium"
                >
                  View Grievance →
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Login & Register Pages ─────────────────────────────────────────────────
const BOYS_HOSTEL_CHOICES = [
  { hostel: 'Kalam', block: 'Block A', label: 'Kalam - Block A' },
  { hostel: 'Kalam', block: 'Block B', label: 'Kalam - Block B' },
  { hostel: 'Kalam', block: 'Block C', label: 'Kalam - Block C' },
  { hostel: 'Kalam', block: 'Block D', label: 'Kalam - Block D' },
  { hostel: 'CV Raman', block: '', label: 'CV Raman (CVR)' },
  { hostel: 'Aryabhatta', block: 'Block A', label: 'Aryabhatta - Block A' },
  { hostel: 'Aryabhatta', block: 'Block B', label: 'Aryabhatta - Block B' },
  { hostel: 'Aryabhatta', block: 'Block D', label: 'Aryabhatta - Block D' },
];

const GIRLS_HOSTEL_CHOICES = [
  { hostel: 'Aryabhatta', block: 'Block C', label: 'Aryabhatta - Block C' },
  { hostel: 'Asima', block: '', label: 'Asima' },
];

function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleLogin = async (e, customEmail, customPass) => {
    if (e) e.preventDefault();
    const em = customEmail || email;
    const pw = customPass || password;

    if (!em || !pw) {
      toast.error('Email and password required.');
      return;
    }

    setLoading(true);
    try {
      const res = await api.request('/auth/login', {
        method: 'POST',
        body: { email: em, password: pw },
      });
      api.setToken(res.token);
      api.setUser(res.user);
      toast.success(`Welcome back, ${res.user.display_name}!`);
      onLoginSuccess(res.user);
      window.location.hash = '#/';
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-8 px-4 max-w-md mx-auto space-y-6">
      <BackButton label="Home" to="#/" />

      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">Sign In</h1>
        <p className="text-xs text-zinc-400">Access the IIT Patna Hostel Grievance Platform</p>
      </div>

      <form onSubmit={(e) => handleLogin(e)} className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Email Address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs rounded transition-colors duration-150 shadow-xs"
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>

        <div className="text-center text-xs text-zinc-400 pt-1">
          Don't have an account?{' '}
          <a href="#/register" className="text-blue-400 hover:underline">
            Register here
          </a>
        </div>
      </form>
    </div>
  );
}

function RegisterPage({ onLoginSuccess }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [gender, setGender] = useState('Male');
  const [allocation, setAllocation] = useState(BOYS_HOSTEL_CHOICES[0].label);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const choices = gender === 'Female' ? GIRLS_HOSTEL_CHOICES : BOYS_HOSTEL_CHOICES;

  const handleGenderChange = (newGender) => {
    setGender(newGender);
    const newChoices = newGender === 'Female' ? GIRLS_HOSTEL_CHOICES : BOYS_HOSTEL_CHOICES;
    setAllocation(newChoices[0].label);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password) {
      toast.error('All fields required.');
      return;
    }

    const selectedChoice = choices.find(c => c.label === allocation) || choices[0];

    setLoading(true);
    try {
      const res = await api.request('/auth/register', {
        method: 'POST',
        body: {
          display_name: name.trim(),
          email: email.trim(),
          password,
          gender,
          hostel: selectedChoice.hostel,
          block: selectedChoice.block,
        },
      });
      api.setToken(res.token);
      api.setUser(res.user);
      toast.success('Account created successfully!');
      onLoginSuccess(res.user);
      window.location.hash = '#/';
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-8 px-4 max-w-md mx-auto space-y-6">
      <BackButton label="Sign In" to="#/login" />

      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight">Create Account</h1>
        <p className="text-xs text-zinc-400">Join as an IIT Patna student</p>
      </div>

      <form onSubmit={handleRegister} className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Full Name *</label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Email Address *</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          />
        </div>

        {/* Gender Selection */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Gender *</label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleGenderChange('Male')}
              className={`py-1.5 px-3 rounded text-xs font-medium border text-center transition-colors duration-150 ${
                gender === 'Male'
                  ? 'bg-zinc-800 border-zinc-600 text-zinc-100 font-medium'
                  : 'bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-700'
              }`}
            >
              Male (Boys Hostels)
            </button>
            <button
              type="button"
              onClick={() => handleGenderChange('Female')}
              className={`py-1.5 px-3 rounded text-xs font-medium border text-center transition-colors duration-150 ${
                gender === 'Female'
                  ? 'bg-zinc-800 border-zinc-600 text-zinc-100 font-medium'
                  : 'bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-700'
              }`}
            >
              Female (Girls Hostels)
            </button>
          </div>
        </div>

        {/* Hostel Allocation */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Allocated Hostel *</label>
          <select
            value={allocation}
            onChange={(e) => setAllocation(e.target.value)}
            className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-100 focus:outline-none focus:border-zinc-600"
          >
            {choices.map(c => (
              <option key={c.label} value={c.label}>{c.label}</option>
            ))}
          </select>
          <p className="text-[10px] text-zinc-500">
            {gender === 'Female'
              ? 'Girls Hostels: Aryabhatta Block C, Asima'
              : 'Boys Hostels: Kalam (Blocks A-D), CV Raman, Aryabhatta (Blocks A, B, D)'}
          </p>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-zinc-300">Password (min 6 chars) *</label>
          <input
            type="password"
            required
            minLength="6"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors duration-150"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs rounded transition-colors duration-150 shadow-xs"
        >
          {loading ? 'Creating...' : 'Create Student Account'}
        </button>

        <div className="text-center text-xs text-zinc-400 pt-1">
          Already registered?{' '}
          <a href="#/login" className="text-blue-400 hover:underline">
            Sign In here
          </a>
        </div>
      </form>
    </div>
  );
}

// ─── Main App Component ─────────────────────────────────────────────────────
function App() {
  const [user, setUser] = useState(() => api.getUser());
  const [unreadCount, setUnreadCount] = useState(0);
  const [toasts, setToasts] = useState([]);
  const [route, setRoute] = useState(() => window.location.hash || '#/');

  // Listen to hash changes for native back/forward button support!
  useEffect(() => {
    const handleHash = () => setRoute(window.location.hash || '#/');
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  // Toast API
  const toast = {
    show: (msg, type = 'info') => {
      const id = Date.now();
      setToasts(t => [...t, { id, msg, type }]);
      setTimeout(() => {
        setToasts(t => t.filter(x => x.id !== id));
      }, 4000);
    },
    success: (msg) => toast.show(msg, 'success'),
    error: (msg) => toast.show(msg, 'error'),
  };

  // Fetch unread notifications count if logged in
  const refreshUnread = useCallback(async () => {
    if (!user) return;
    try {
      const res = await api.request('/notifications');
      setUnreadCount(res.unread_count);
    } catch {}
  }, [user]);

  useEffect(() => {
    refreshUnread();
  }, [refreshUnread]);

  const handleLogout = async () => {
    try {
      await api.request('/auth/logout', { method: 'POST' });
    } catch {}
    api.removeToken();
    api.removeUser();
    setUser(null);
    setUnreadCount(0);
    toast.success('Signed out.');
    window.location.hash = '#/';
  };

  // Route Dispatcher
  const renderView = () => {
    if (route === '#/' || route === '') return <HomePage user={user} />;
    if (route === '#/board') return <BoardPage user={user} />;
    if (route.startsWith('#/complaint/')) {
      const id = route.replace('#/complaint/', '');
      return <ComplaintDetailPage id={id} user={user} />;
    }
    if (route === '#/submit') return <SubmitPage user={user} />;
    if (route === '#/my-complaints') return <MyComplaintsPage user={user} />;
    if (route === '#/caretaker') return <CaretakerDashboard user={user} />;
    if (route === '#/admin') return <AdminDashboard user={user} />;
    if (route === '#/analytics') return <AnalyticsPage user={user} />;
    if (route === '#/notifications') return <NotificationsPage user={user} onRead={refreshUnread} />;
    if (route === '#/login') return <LoginPage onLoginSuccess={setUser} />;
    if (route === '#/register') return <RegisterPage onLoginSuccess={setUser} />;

    return <div className="py-12 text-center text-zinc-400 text-xs">Page not found. <a href="#/" className="text-blue-400 underline">Go Home</a></div>;
  };

  return (
    <ToastContext.Provider value={toast}>
      <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-200 antialiased">
        <Navbar user={user} unreadCount={unreadCount} onLogout={handleLogout} />

        <main className="flex-1">
          {renderView()}
        </main>

        <footer className="py-6 border-t border-zinc-900 text-center text-xs text-zinc-500">
          <div>Hostel Grievance & Accountability Platform · IIT Patna</div>
          <div className="text-[11px] text-zinc-600 mt-1">Built with FastAPI & React</div>
        </footer>

        {/* Floating Toast Notification Container */}
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
          {toasts.map(t => (
            <div
              key={t.id}
              className={`p-3 rounded-lg text-xs font-medium shadow-lg pointer-events-auto border transition-all ${
                t.type === 'error'
                  ? 'bg-zinc-900 text-rose-300 border-rose-900/60'
                  : t.type === 'success'
                  ? 'bg-zinc-900 text-emerald-300 border-emerald-900/60'
                  : 'bg-zinc-900 text-zinc-200 border-zinc-800'
              }`}
            >
              {t.msg}
            </div>
          ))}
        </div>
      </div>
    </ToastContext.Provider>
  );
}

// Render the application to DOM
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
