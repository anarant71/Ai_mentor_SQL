import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { user } = useAuth();

  if (!user) {
    return <p className="py-10 text-center text-gray-400">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Profile</h1>
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100 text-xl font-bold text-indigo-600">
          {user.display_name.charAt(0).toUpperCase()}
        </div>
        <dl className="space-y-3">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">Name</dt>
            <dd className="mt-0.5 text-sm font-medium text-gray-900">{user.display_name}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">Email</dt>
            <dd className="mt-0.5 text-sm text-gray-700">{user.email}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}