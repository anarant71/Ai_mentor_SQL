import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { Lesson, StudentSkill, SkillAnalysis } from '../types';

function analyzeSkills(skills: StudentSkill[]): SkillAnalysis {
  const now = Date.now();
  const DAY_MS = 86400000;
  const FADE_DAYS = 7;

  const strong: StudentSkill[] = [];
  const weak: StudentSkill[] = [];
  const fading: StudentSkill[] = [];
  const unstudied: StudentSkill[] = [];
  let totalPct = 0;
  let studiedCount = 0;

  for (const s of skills) {
    const pct = Number(s.percentage);
    totalPct += pct;

    if (pct === 0) {
      unstudied.push(s);
      continue;
    }

    studiedCount++;
    if (pct >= 70) {
      strong.push(s);
    } else if (pct < 40) {
      weak.push(s);
    }

    if (s.last_practiced_at) {
      const practiced = new Date(s.last_practiced_at).getTime();
      if (now - practiced > FADE_DAYS * DAY_MS && pct > 0 && pct < 70) {
        fading.push(s);
      }
    }
  }

  const overall_level = skills.length > 0 ? Math.round(totalPct / skills.length) : 0;
  const level_label =
    overall_level >= 80 ? 'advanced' :
    overall_level >= 60 ? 'strong_middle' :
    overall_level >= 40 ? 'middle' :
    overall_level >= 20 ? 'junior' :
    'beginner';

  return { overall_level, level_label, studied_count: studiedCount, strong, weak, fading, unstudied };
}

const LEVEL_LABELS: Record<string, string> = {
  beginner: 'Beginner',
  junior: 'Junior',
  middle: 'Middle',
  strong_middle: 'Strong Middle',
  advanced: 'Advanced',
};

const LEVEL_COLORS: Record<string, string> = {
  beginner: 'bg-red-500',
  junior: 'bg-orange-500',
  middle: 'bg-yellow-500',
  strong_middle: 'bg-green-500',
  advanced: 'bg-indigo-500',
};

export default function Dashboard() {
  const { data: lessons = [], isLoading: lessonsLoading } = useQuery({
    queryKey: ['lessons'],
    queryFn: () => api.get<Lesson[]>('/lessons').then((r) => r.data),
  });

  const { data: skills = [], isLoading: skillsLoading } = useQuery({
    queryKey: ['skills-student'],
    queryFn: () => api.get<StudentSkill[]>('/skills/student').then((r) => r.data),
  });

  const analysis = useMemo(() => analyzeSkills(skills), [skills]);

  if (lessonsLoading || skillsLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  const completedCount = lessons.filter((l) => l.status === 'completed').length;
  const nextLesson = lessons.find(
    (l) => (l.status === 'not_started' || l.status === 'in_progress') && l.roadmap_status !== 'locked'
  );
  const allCompleted = lessons.length > 0 && completedCount === lessons.length;

  return (
    <div>
      {/* Overall level card */}
      {skills.length > 0 && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-gray-500">Your level</span>
              <h2 className="mt-1 text-lg font-semibold text-gray-900">
                {LEVEL_LABELS[analysis.level_label] || analysis.level_label}
              </h2>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <span className="block text-2xl font-bold text-indigo-600">{analysis.overall_level}%</span>
                <span className="text-xs text-gray-500">overall</span>
              </div>
              <div className={`h-12 w-12 rounded-full ${LEVEL_COLORS[analysis.level_label] || 'bg-gray-400'} flex items-center justify-center`}>
                <span className="text-lg font-bold text-white">{analysis.studied_count}</span>
              </div>
            </div>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">
            <div
              className={`h-full rounded-full transition-all ${LEVEL_COLORS[analysis.level_label] || 'bg-gray-400'}`}
              style={{ width: `${analysis.overall_level}%` }}
            />
          </div>
          <div className="mt-2 flex justify-between text-xs text-gray-500">
            <span>{analysis.strong.length} strong</span>
            <span>{analysis.weak.length} need practice</span>
            <span>{analysis.unstudied.length} unstudied</span>
          </div>
        </div>
      )}

      {/* Continue learning card */}
      {nextLesson && (
        <div className="mb-6 rounded-xl border border-indigo-200 bg-indigo-50 p-5">
          <span className="text-xs font-medium uppercase tracking-wider text-indigo-500">Continue learning</span>
          <h2 className="mt-1 text-lg font-semibold text-indigo-900">{nextLesson.title}</h2>
          <div className="mt-3 flex items-center gap-2">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-indigo-200">
              <div
                className="h-full rounded-full bg-indigo-600 transition-all"
                style={{ width: `${(completedCount / lessons.length) * 100}%` }}
              />
            </div>
            <span className="shrink-0 text-xs font-medium text-indigo-600">
              {completedCount}/{lessons.length}
            </span>
          </div>
          <Link
            to={`/lessons/${nextLesson.slug}`}
            className="mt-3 inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Continue <span className="text-lg leading-none">&rarr;</span>
          </Link>
        </div>
      )}

      {allCompleted && (
        <div className="mb-6 rounded-xl border border-green-200 bg-green-50 p-5 text-center">
          <span className="text-2xl">🎉</span>
          <h2 className="mt-1 text-lg font-semibold text-green-900">All lessons completed!</h2>
          <p className="mt-1 text-sm text-green-700">Great job finishing the course.</p>
        </div>
      )}

      {/* Weak spots */}
      {analysis.weak.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-3 text-lg font-bold text-gray-900">Needs practice</h2>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
            {analysis.weak.map((s) => (
              <Link
                key={s.skill_code}
                to={`/tasks?skill=${s.skill_code}`}
                className="rounded-xl border border-red-200 bg-red-50 p-3 transition hover:shadow-md"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{s.skill_icon}</span>
                  <span className="truncate text-xs font-medium text-red-800">{s.skill_title}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-red-200">
                  <div
                    className="h-full rounded-full bg-red-500 transition-all"
                    style={{ width: `${Number(s.percentage)}%` }}
                  />
                </div>
                <span className="mt-1 block text-right text-[10px] font-medium text-red-600">
                  {Math.round(Number(s.percentage))}%
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Fading skills */}
      {analysis.fading.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-3 text-lg font-bold text-gray-900">Fading — time to review</h2>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
            {analysis.fading.map((s) => (
              <Link
                key={s.skill_code}
                to={`/tasks?skill=${s.skill_code}`}
                className="rounded-xl border border-amber-200 bg-amber-50 p-3 transition hover:shadow-md"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{s.skill_icon}</span>
                  <span className="truncate text-xs font-medium text-amber-800">{s.skill_title}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-amber-200">
                  <div
                    className="h-full rounded-full bg-amber-500 transition-all"
                    style={{ width: `${Number(s.percentage)}%` }}
                  />
                </div>
                <span className="mt-1 block text-right text-[10px] font-medium text-amber-600">
                  {Math.round(Number(s.percentage))}%
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Skills overview */}
      {skills.filter((s) => Number(s.percentage) > 0).length > 0 && (
        <div className="mb-6">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">Skills</h2>
            <Link to="/skills" className="text-sm text-indigo-600 hover:underline">
              View all &rarr;
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
            {skills
              .filter((s) => Number(s.percentage) > 0)
              .slice(0, 5)
              .map((s) => {
                const pct = Number(s.percentage);
                return (
                <div key={s.skill_code} className="rounded-xl border border-gray-200 bg-white p-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{s.skill_icon}</span>
                    <span className="truncate text-xs font-medium text-gray-700">{s.skill_title}</span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-100">
                    <div
                      className={`h-full rounded-full transition-all ${
                        pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="mt-1 block text-right text-[10px] font-medium text-gray-500">{Math.round(pct)}%</span>
                </div>
                );
              })}
          </div>
        </div>
      )}

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Lessons</h1>
        <p className="mt-1 text-sm text-gray-500">
          {completedCount} of {lessons.length} completed
        </p>
      </div>

      <div className="space-y-3">
        {lessons.map((lesson) => {
          const isLocked = lesson.roadmap_status === 'locked';
          return isLocked ? (
          <div
            key={lesson.slug}
            className="flex cursor-not-allowed items-center gap-4 rounded-xl border border-gray-100 bg-white p-4 opacity-60 shadow-sm"
          >
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
              lesson.status === 'completed'
                ? 'bg-green-100 text-green-700'
                : isLocked
                  ? 'bg-gray-100 text-gray-400'
                  : 'bg-gray-100 text-gray-500'
            }`}>
              {lesson.status === 'completed' ? '✓' : isLocked ? '🔒' : lesson.lesson_number}
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-semibold text-gray-900">
                {lesson.title}
                {lesson.status === 'in_progress' && (
                  <span className="ml-2 rounded-full bg-yellow-100 px-2 py-0.5 text-[10px] font-medium text-yellow-700">
                    In progress
                  </span>
                )}
              </h2>
              <p className="mt-0.5 text-sm text-gray-500 truncate">{lesson.module_title}</p>
            </div>
            <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${
              lesson.status === 'completed'
                ? 'bg-green-100 text-green-700'
                : lesson.status === 'in_progress'
                  ? 'bg-yellow-100 text-yellow-700'
                  : isLocked
                    ? 'bg-gray-100 text-gray-400'
                    : 'bg-gray-100 text-gray-500'
            }`}>
              {lesson.status === 'completed' ? 'Completed' : lesson.status === 'in_progress' ? 'In progress' : isLocked ? 'Locked' : 'Not started'}
            </span>
          </div>
          ) : (
          <Link
            key={lesson.slug}
            to={`/lessons/${lesson.slug}`}
            className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-indigo-300 hover:shadow-md"
          >
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
              lesson.status === 'completed'
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500'
            }`}>
              {lesson.status === 'completed' ? '✓' : lesson.lesson_number}
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-semibold text-gray-900">
                {lesson.title}
                {lesson.status === 'in_progress' && (
                  <span className="ml-2 rounded-full bg-yellow-100 px-2 py-0.5 text-[10px] font-medium text-yellow-700">
                    In progress
                  </span>
                )}
              </h2>
              <p className="mt-0.5 text-sm text-gray-500 truncate">{lesson.module_title}</p>
            </div>
            <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${
              lesson.status === 'completed'
                ? 'bg-green-100 text-green-700'
                : lesson.status === 'in_progress'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-500'
            }`}>
              {lesson.status === 'completed' ? 'Completed' : lesson.status === 'in_progress' ? 'In progress' : 'Not started'}
            </span>
          </Link>
          );
        })}

        {lessons.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-400">No lessons available yet.</p>
        )}
      </div>
    </div>
  );
}