import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../api/client';
import type { StudentSkill } from '../types';

const CATEGORY_LABELS: Record<string, string> = {
  basic: 'Basic',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
};

const CATEGORY_ORDER = ['basic', 'intermediate', 'advanced'];

function getSkillStatus(skill: StudentSkill): 'strong' | 'weak' | 'fading' | 'unstudied' {
  const pct = Number(skill.percentage);
  if (pct === 0) return 'unstudied';
  if (pct >= 70) return 'strong';
  if (skill.last_practiced_at) {
    const daysSincePractice = (Date.now() - new Date(skill.last_practiced_at).getTime()) / 86400000;
    if (daysSincePractice > 7 && pct < 70) return 'fading';
  }
  if (pct < 40) return 'weak';
  return 'strong';
}

const STATUS_STYLES: Record<string, { border: string; bg: string; text: string; badge: string; badgeBg: string; bar: string }> = {
  strong: {
    border: 'border-green-300', bg: 'bg-green-50', text: 'text-green-900',
    badge: 'text-green-700', badgeBg: 'bg-green-100', bar: 'bg-green-500',
  },
  weak: {
    border: 'border-red-300', bg: 'bg-red-50', text: 'text-red-900',
    badge: 'text-red-700', badgeBg: 'bg-red-100', bar: 'bg-red-500',
  },
  fading: {
    border: 'border-amber-300', bg: 'bg-amber-50', text: 'text-amber-900',
    badge: 'text-amber-700', badgeBg: 'bg-amber-100', bar: 'bg-amber-500',
  },
  unstudied: {
    border: 'border-gray-200', bg: 'bg-white', text: 'text-gray-900',
    badge: 'text-gray-500', badgeBg: 'bg-gray-100', bar: 'bg-gray-300',
  },
};

const STATUS_LABELS: Record<string, string> = {
  strong: 'Strong',
  weak: 'Needs practice',
  fading: 'Fading',
  unstudied: 'Not studied',
};

function formatLastPracticed(dateStr: string | null): string {
  if (!dateStr) return 'Never';
  const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
  return `${Math.floor(days / 30)} months ago`;
}

function SkillCard({ skill }: { skill: StudentSkill }) {
  const pct = Math.round(Number(skill.percentage));
  const status = getSkillStatus(skill);
  const style = STATUS_STYLES[status];

  return (
    <Link
      to={status === 'unstudied' ? '#' : `/tasks?skill=${skill.skill_code}`}
      className={`rounded-xl border-2 p-4 transition hover:shadow-md ${style.border} ${style.bg} ${status === 'unstudied' ? 'opacity-60' : ''}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{skill.skill_icon}</span>
          <div>
            <h3 className={`text-sm font-bold ${style.text}`}>{skill.skill_title}</h3>
            <span className="text-xs opacity-75 text-gray-500">{skill.skill_code}</span>
          </div>
        </div>
        <div className="text-right">
          <span className={`text-2xl font-bold ${pct === 0 ? 'text-gray-300' : style.text}`}>
            {pct === 0 ? '—' : `${pct}%`}
          </span>
          <span className={`ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium ${style.badgeBg} ${style.badge}`}>
            {STATUS_LABELS[status]}
          </span>
        </div>
      </div>
      <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-white/60">
        <div
          className={`h-full rounded-full transition-all ${style.bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-2 flex justify-between text-[10px] text-gray-500">
        <span>{skill.successful_attempts}/{skill.total_attempts} correct</span>
        <span>confidence {Math.round(Number(skill.confidence) * 100)}%</span>
        <span>{formatLastPracticed(skill.last_practiced_at)}</span>
      </div>
    </Link>
  );
}

export default function Skills() {
  const { data: skills = [], isLoading } = useQuery({
    queryKey: ['skills-student'],
    queryFn: () => api.get<StudentSkill[]>('/skills/student').then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  const strongCount = skills.filter((s) => getSkillStatus(s) === 'strong').length;
  const weakCount = skills.filter((s) => getSkillStatus(s) === 'weak').length;
  const fadingCount = skills.filter((s) => getSkillStatus(s) === 'fading').length;

  const grouped: Record<string, StudentSkill[]> = {};
  for (const s of skills) {
    const cat = s.skill_category || 'basic';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(s);
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Skill Map</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track your progress across {skills.length} SQL skill areas
          </p>
        </div>
        <div className="flex gap-3 text-xs">
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-green-500" /> {strongCount} strong
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500" /> {weakCount} weak
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> {fadingCount} fading
          </span>
        </div>
      </div>

      {CATEGORY_ORDER.map((cat) => {
        const items = grouped[cat];
        if (!items || items.length === 0) return null;
        return (
          <div key={cat} className="mb-8">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-500">
              {CATEGORY_LABELS[cat] || cat}
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {items
                .sort((a, b) => {
                  const statusOrder: Record<string, number> = { weak: 0, fading: 1, strong: 2, unstudied: 3 };
                  return statusOrder[getSkillStatus(a)] - statusOrder[getSkillStatus(b)];
                })
                .map((s) => (
                <SkillCard key={s.skill_code} skill={s} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}