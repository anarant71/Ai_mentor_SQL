import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Editor, { type OnMount } from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '../api/client';
import type { Task, TaskDetail, ExecuteResult, Lesson, SubmitResultEnhanced } from '../types';

function StageSeparator({ label }: { label: string }) {
  return (
    <div className="my-4 flex items-center gap-3">
      <div className="h-px flex-1 bg-gray-200" />
      <span className="text-xs font-medium uppercase tracking-widest text-gray-400">{label}</span>
      <div className="h-px flex-1 bg-gray-200" />
    </div>
  );
}

function TaskBlock({ children }: { children: React.ReactNode }) {
  return (
    <div className="my-4 rounded-xl border-2 border-amber-400 bg-amber-50 p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-xl">🎯</span>
        <span className="font-bold uppercase tracking-wide text-amber-800">ЗАДАНИЕ</span>
      </div>
      {children}
    </div>
  );
}

function formatCellValue(val: unknown): string {
  if (val === null) return 'NULL';
  const str = String(val);
  // Truncate UUIDs for readability
  if (str.length === 36 && /^[0-9a-f-]+$/i.test(str)) {
    return str.substring(0, 8) + '...';
  }
  if (str.length > 50) return str.substring(0, 50) + '...';
  return str;
}

function SqlResultTable({ result }: { result: ExecuteResult }) {
  if (result.error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4">
        <p className="font-mono text-sm text-red-600">{result.error}</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
      <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
        <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Result ({result.row_count} rows, {result.execution_time_ms}ms)
        </span>
      </div>
      <div className="max-h-64 overflow-auto">
        <div className="inline-block min-w-full align-middle">
          <table className="min-w-full text-left text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="border-b-2 border-gray-200 bg-gray-100">
                {result.columns.map((col) => (
                  <th
                    key={col}
                    className="whitespace-nowrap border-r border-gray-200 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-gray-600 last:border-r-0"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.rows.map((row, i) => (
                <tr
                  key={i}
                  className={`border-b border-gray-100 transition-colors last:border-b-0 hover:bg-indigo-50 ${
                    i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                  }`}
                >
                  {result.columns.map((_col, j) => (
                    <td
                      key={j}
                      className="whitespace-nowrap border-r border-gray-100 px-4 py-2 font-mono text-xs text-gray-700 last:border-r-0"
                    >
                      {row[j] === null ? (
                        <span className="italic text-gray-400">NULL</span>
                      ) : (
                        formatCellValue(row[j])
                      )}
                    </td>
                  ))}
                </tr>
              ))}
              {result.rows.length === 0 && (
                <tr>
                  <td
                    colSpan={result.columns.length || 1}
                    className="px-4 py-6 text-center text-sm text-gray-400"
                  >
                    No rows returned
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default function LessonPage() {
  const { slug } = useParams<{ slug: string }>();
  const queryClient = useQueryClient();
  const [activeTask, setActiveTask] = useState<TaskDetail | null>(null);
  const [query, setQuery] = useState('');
  const [execResult, setExecResult] = useState<ExecuteResult | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitResultEnhanced | null>(null);
  const [executing, setExecuting] = useState(false);
  const [completed, setCompleted] = useState(false);
  const executeRef = useRef<() => void>(() => {});

  const { data: lesson, isLoading, error: lessonError } = useQuery({
    queryKey: ['lesson', slug],
    queryFn: () => api.get<{
      slug: string; title: string; module_number: number; lesson_number: number;
      module_title: string; summary: string; difficulty: number; estimated_minutes: number; content: string;
      roadmap_status: string | null;
    }>(`/lessons/${slug}`).then((r) => r.data),
    enabled: !!slug,
  });

  const { data: tasks = [] } = useQuery({
    queryKey: ['lesson-tasks', slug],
    queryFn: () => api.get<Task[]>(`/lessons/${slug}/tasks`).then((r) => r.data),
    enabled: !!slug,
  });

  const { data: allLessons = [] } = useQuery({
    queryKey: ['lessons'],
    queryFn: () => api.get<Lesson[]>('/lessons').then((r) => r.data),
  });

  const content = lesson?.content ?? '';
  const isLocked = lesson?.roadmap_status === 'locked';

  const nextLesson = allLessons.length > 0 && lesson
    ? allLessons[allLessons.findIndex((l) => l.slug === slug) + 1] ?? null
    : null;

  // Auto-select first task
  useEffect(() => {
    if (tasks.length > 0 && !activeTask) {
      loadTaskDetail(tasks[0].id);
    }
  }, [tasks, activeTask]);

  // Mark lesson as in_progress on first load (skip locked)
  useEffect(() => {
    if (slug && lesson && !isLocked) {
      api.post(`/lessons/${slug}/progress?status=in_progress`).catch(() => {});
    }
  }, [slug, lesson, isLocked]);

  async function loadTaskDetail(taskId: string) {
    try {
      const res = await api.get<TaskDetail>(`/tasks/${taskId}`);
      setActiveTask(res.data);
    } catch {
      const t = tasks.find((t) => t.id === taskId);
      if (t) {
        setActiveTask({
          id: t.id, lesson_id: '', slug: t.slug,
          title: t.title, description: t.description || '',
          instructions: '', expected_result_text: null, hint: null,
          difficulty: t.difficulty, validation_strategy: t.validation_strategy,
        });
      }
    }
  }

  const handleExecute = useCallback(async () => {
    if (!query.trim()) return;
    setExecuting(true);
    setExecResult(null);
    setSubmitResult(null);
    try {
      const res = await api.post<ExecuteResult>('/sandbox/execute', { sql: query });
      setExecResult(res.data);
    } catch (err: unknown) {
      const data = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error;
      setExecResult({
        columns: [], rows: [], row_count: 0, execution_time_ms: 0,
        error: data?.message || 'Execution failed',
      });
    } finally {
      setExecuting(false);
    }
  }, [query]);

  executeRef.current = handleExecute;

  const submitMutation = useMutation({
    mutationFn: (sql_text: string) =>
      api.post<SubmitResultEnhanced>(`/tasks/${activeTask?.id}/submit`, { sql_text }),
    onSuccess: (res) => {
      setSubmitResult(res.data);
      if (res.data.is_correct) {
        setCompleted(true);
        api.post(`/lessons/${slug}/progress?status=completed`).catch(() => {});
        queryClient.invalidateQueries({ queryKey: ['lessons'] });
      }
    },
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error;
      setSubmitResult({
        submission_id: '', attempt_number: 0, is_correct: false,
        score: 0, feedback: data?.message || 'Check failed',
      });
    },
  });

  const handleEditorMount: OnMount = (editor) => {
    editor.addCommand(2048 | 3, () => {
      executeRef.current();
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  if (lessonError || !lesson) {
    return (
      <div className="py-20 text-center">
        <p className="text-red-600">{lessonError?.message || 'Lesson not found'}</p>
        <Link to="/" className="mt-4 inline-block text-sm text-indigo-600 hover:underline">
          Back to lessons
        </Link>
      </div>
    );
  }

  if (isLocked) {
    return (
      <div className="flex h-[calc(100vh-5rem)] items-center justify-center">
        <div className="max-w-md text-center">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gray-100">
            <svg className="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="mb-2 text-2xl font-bold text-gray-900">{lesson.title}</h1>
          <p className="mb-6 text-gray-500">Этот урок заблокирован. Сначала завершите предыдущие уроки.</p>
          <Link
            to="/"
            className="inline-block rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-700"
          >
            К списку уроков
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-5rem)] gap-4">
      {/* Left column — lesson content */}
      <div className="w-1/2 overflow-y-auto rounded-xl border border-gray-200 bg-white p-6">
        <Link to="/" className="mb-4 inline-block text-sm text-indigo-600 hover:underline">
          &larr; Back to lessons
        </Link>
        <div className="mb-4 flex items-center gap-2">
          <h1 className="text-xl font-bold text-gray-900">{lesson.title}</h1>
          {completed && (
            <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
              Completed
            </span>
          )}
        </div>

        <StageSeparator label="Теория" />
        <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-a:text-indigo-600 prose-code:rounded prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-pre:bg-gray-900 prose-pre:text-green-400">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        </div>

        {/* Task selection */}
        {tasks.length > 0 && (
          <div className="mt-6">
            <StageSeparator label="Задания" />
            <div className="space-y-2">
              {tasks.map((task) => (
                <button
                  key={task.id}
                  onClick={() => {
                    loadTaskDetail(task.id);
                    setExecResult(null);
                    setSubmitResult(null);
                  }}
                  className={`w-full rounded-lg border px-3 py-2.5 text-left text-sm transition ${
                    activeTask?.id === task.id
                      ? 'border-indigo-300 bg-indigo-50 shadow-sm'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{task.title}</span>
                    <DifficultyBadge difficulty={task.difficulty} />
                  </div>
                  {task.description && (
                    <p className="mt-0.5 text-xs leading-relaxed text-gray-500">{task.description}</p>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Task detail with ЗАДАНИЕ block */}
        {activeTask && activeTask.instructions && (
          <TaskBlock>
            <h3 className="mb-2 text-sm font-semibold text-amber-900">{activeTask.title}</h3>
            <div className="prose prose-xs prose-amber text-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {activeTask.instructions}
              </ReactMarkdown>
            </div>
            {activeTask.hint && (
              <details className="mt-3">
                <summary className="cursor-pointer text-xs font-medium text-amber-700 hover:text-amber-800">
                  Подсказка
                </summary>
                <div className="mt-2 rounded-lg border border-amber-200 bg-amber-100/50 p-3">
                  <p className="whitespace-pre-wrap font-mono text-xs text-amber-900">{activeTask.hint}</p>
                </div>
              </details>
            )}
          </TaskBlock>
        )}

        {/* Submit result in left column */}
        {submitResult && (
          <div className={`mt-4 rounded-xl border px-4 py-3 ${
            submitResult.is_correct
              ? 'border-green-200 bg-green-50'
              : 'border-red-200 bg-red-50'
          }`}>
            <div className="flex items-center gap-2">
              <span className={`text-lg ${submitResult.is_correct ? '' : ''}`}>
                {submitResult.is_correct ? '✅' : '❌'}
              </span>
              <p className={`text-sm font-medium ${
                submitResult.is_correct ? 'text-green-800' : 'text-red-800'
              }`}>
                {submitResult.is_correct ? 'Верно!' : 'Есть ошибки'}
                {submitResult.attempt_number > 0 && (
                  <span className="ml-2 font-normal text-gray-500">
                    (попытка #{submitResult.attempt_number})
                  </span>
                )}
              </p>
            </div>
            <p className="mt-1 text-sm leading-relaxed text-gray-700">{submitResult.feedback}</p>
            {submitResult.differences && submitResult.differences.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-xs leading-relaxed text-red-700">
                {submitResult.differences.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            )}
            {submitResult.skill_updates && submitResult.skill_updates.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {submitResult.skill_updates.map((su) => (
                  <span key={su.code} className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-medium text-indigo-700">
                    {su.code}: {Math.round(su.score * 100)}%
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Next lesson button */}
        {completed && nextLesson && (
          <div className="mt-6">
            <StageSeparator label="Далее" />
            <Link
              to={`/lessons/${nextLesson.slug}`}
              className="flex items-center justify-between rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm transition hover:border-indigo-300 hover:bg-indigo-100"
            >
              <div>
                <span className="text-xs font-medium uppercase tracking-wider text-indigo-500">Следующий урок</span>
                <p className="mt-0.5 font-medium text-indigo-900">{nextLesson.title}</p>
              </div>
              <span className="text-lg text-indigo-600">&rarr;</span>
            </Link>
          </div>
        )}
      </div>

      {/* Right column — SQL editor + results */}
      <div className="flex w-1/2 flex-col gap-4">
        <StageSeparator label="Редактор SQL" />
        <div className="flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white">
          <div className="flex items-center justify-between border-b border-gray-100 px-4 py-2">
            <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
              SQL Editor
            </span>
            <span className="text-xs text-gray-400">Ctrl+Enter для запуска</span>
          </div>
          <div className="min-h-[250px] flex-1">
            <Editor
              height="100%"
              defaultLanguage="sql"
              theme="vs-dark"
              value={query}
              onChange={(val) => setQuery(val ?? '')}
              onMount={handleEditorMount}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                padding: { top: 12 },
                tabSize: 2,
                insertSpaces: true,
              }}
            />
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleExecute}
            disabled={executing || !query.trim()}
            className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
          >
            {executing ? 'Выполняется...' : 'Выполнить'}
          </button>
          <button
            onClick={() => submitMutation.mutate(query)}
            disabled={submitMutation.isPending || !activeTask || !query.trim()}
            className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitMutation.isPending ? 'Проверка...' : 'Отправить'}
          </button>
        </div>

        {/* Results table */}
        <StageSeparator label="Результат" />
        {execResult && <SqlResultTable result={execResult} />}
        {!execResult && !submitResult && (
          <div className="flex items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50/50 p-8">
            <p className="text-sm text-gray-400">Напиши запрос и нажми «Выполнить»</p>
          </div>
        )}
      </div>
    </div>
  );
}

function DifficultyBadge({ difficulty }: { difficulty: number }) {
  const labels: Record<number, string> = { 1: 'easy', 2: 'medium', 3: 'hard', 4: 'hard', 5: 'hard' };
  const colors: Record<number, string> = {
    1: 'bg-green-100 text-green-700',
    2: 'bg-yellow-100 text-yellow-700',
    3: 'bg-red-100 text-red-700',
    4: 'bg-red-100 text-red-700',
    5: 'bg-red-100 text-red-700',
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors[difficulty] || colors[1]}`}>
      {labels[difficulty] || 'easy'}
    </span>
  );
}