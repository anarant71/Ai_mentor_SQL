import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navLinks = [
    { to: '/', label: 'Lessons' },
    { to: '/skills', label: 'Skills' },
    { to: '/mistakes', label: 'Mistakes' },
    { to: '/tasks', label: 'Tasks' },
    { to: '/profile', label: 'Profile' },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
          <Link to="/" className="text-lg font-bold text-indigo-600">
            AI Mentor
          </Link>
          <nav className="flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`text-sm font-medium ${
                  location.pathname === link.to
                    ? 'text-indigo-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {link.label}
              </Link>
            ))}
            <span className="text-sm text-gray-400">{user?.display_name}</span>
            <button
              onClick={logout}
              className="text-sm text-gray-500 hover:text-red-600"
            >
              Log out
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        {children}
      </main>
    </div>
  );
}