import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';
import type { StudentMistake } from '../types';

const STATUS_LABELS: Record<string, string> = {
  new: 'New',
  active: 'Active',
  training: 'Training',
  resolved: 'Resolved',
  ignored: 'Ignored',
};

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-blue-100 text-blue-800',
  active: 'bg-red-100 text-red-800',
  training: 'bg-amber-100 text-amber-800',
  resolved: 'bg-green-100 text-green-800',
  ignored: 'bg-gray-100 text-gray-500',
};

const SEVERITY_LABELS: Record<number, string> = {
  1: 'trivial',
  2: 'minor',
  3: 'major',
  4: 'critical',
  5: 'blocker',
};

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const days = Math.floor((Date.now() - d.getTime()) / 86400000);
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} days ago`;
  return d.toLocaleDateString('ru-RU');
}

export default function Mistakes() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: mistakes = [], isLoading } = useQuery({
    queryKey: ['mistakes', statusFilter],
    queryFn: () => {
      const url = statusFilter ? `/mistakes?status=${statusFilter}` : '/mistakes';
      return api.get<StudentMistake[]>(url).then((r) => r.data);
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (skillCode: string) => api.post(`/mistakes/resolve?skill_code=${skillCode}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mistakes'] }),
  });

  const activeCount = mistakes.filter((m) => m.status === 'active').length;
  const newCount = mistakes.filter((m) => m.status === 'new').length;
  const trainingCount = mistakes.filter((m) => m.status === 'training').length;

  const groupedBySkill: Record<string, StudentMistake[]> = {};
  for (const m of mistakes) {
    const key = m.mistake_code || 'other';
    if (!groupedBySkill[key]) groupedBySkill[key] = [];
    groupedBySkill[key].push(m);
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mistakes</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track and fix common SQL mistakes
          </p>
        </div>
        <div className="flex gap-3 text-xs">
          {newCount > 0 && (
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-blue-500" /> {newCount} new
            </span>
          )}
          {activeCount > 0 && (
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-red-500" /> {activeCount} active
            </span>
          )}
          {trainingCount > 0 && (
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-amber-500" /> {trainingCount} in training
            </span>
          )}
        </div>
      </div>

      {/* Filter */}
      <div className="mb-4 flex flex-wrap gap-2">
        {['', 'new', 'active', 'training', 'resolved', 'ignored'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
              statusFilter === s
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {s ? STATUS_LABELS[s] : 'All'}
          </button>
        ))}
      </div>

      {Object.keys(groupedBySkill).length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50/50 py-16">
          <span className="text-4xl">🎉</span>
          <h2 className="mt-3 text-lg font-semibold text-gray-900">No mistakes found</h2>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter ? `No ${STATUS_LABELS[statusFilter]?.toLowerCase()} mistakes.` : 'Keep up the good work!'}
          </p>
        </div>
      )}

      <div className="space-y-3">
        {Object.entries(groupedBySkill).map(([code, items]) => {
          const unresolved = items.filter((m) => m.status !== 'resolved' && m.status !== 'ignored');
          const maxSeverity = Math.max(...items.map((m) => m.severity));

          return (
            <div key={code} className="overflow-hidden rounded-xl border border-gray-200 bg-white">
              <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50 px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs font-mono font-medium text-indigo-700">
                    {code}
                  </span>
                  <span className="text-sm text-gray-500">{items.length} occurrence{items.length > 1 ? 's' : ''}</span>
                  {items[0]?.mistake_title && (
                    <span className="text-sm font-medium text-gray-700">{items[0].mistake_title}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    SEVERITY_LABELS[maxSeverity] === 'blocker' || SEVERITY_LABELS[maxSeverity] === 'critical'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {SEVERITY_LABELS[maxSeverity] || 'unknown'}
                  </span>
                  {unresolved.length > 0 && (
                    <button
                      onClick={() => resolveMutation.mutate(code)}
                      className="rounded-lg border border-green-300 bg-green-50 px-3 py-1 text-xs font-medium text-green-700 transition hover:bg-green-100"
                    >
                      Resolve all
                    </button>
                  )}
                </div>
              </div>

              <div className="divide-y divide-gray-100">
                {items.map((m) => (
                  <div key={m.id} className="flex items-center gap-4 px-4 py-3">
                    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_COLORS[m.status] || ''}`}>
                      {STATUS_LABELS[m.status] || m.status}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900">{m.title}</p>
                      {m.details && (
                        <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">{m.details}</p>
                      )}
                    </div>
                    <div className="flex shrink-0 items-center gap-3 text-xs text-gray-400">
                      <span>{m.repeat_count}x</span>
                      <span>{formatDate(m.last_seen_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
