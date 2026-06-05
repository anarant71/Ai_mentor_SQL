import { useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import Editor, { type OnMount } from '@monaco-editor/react';
import api from '../api/client';
import type { TaskWithSkills, StudentSkill, ExecuteResult } from '../types';

function formatCellValue(val: unknown): string {
  if (val === null) return 'NULL';
  const str = String(val);
  if (str.length === 36 && /^[0-9a-f-]+$/i.test(str)) return str.substring(0, 8) + '...';
  if (str.length > 50) return str.substring(0, 50) + '...';
  return str;
}

function SqlResultTable({ result }: { result: ExecuteResult }) {
  if (result.error) {
    return <div className="rounded-xl border border-red-200 bg-red-50 p-4"><p className="font-mono text-sm text-red-600">{result.error}</p></div>;
  }
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
      <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
        <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Result ({result.row_count} rows, {result.execution_time_ms}ms)
        </span>
      </div>
      <div className="max-h-64 overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="border-b-2 border-gray-200 bg-gray-100">
              {result.columns.map((col) => (
                <th key={col} className="whitespace-nowrap border-r border-gray-200 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-gray-600 last:border-r-0">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row, i) => (
              <tr key={i} className={`border-b border-gray-100 last:border-b-0 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                {result.columns.map((_col, j) => (
                  <td key={j} className="whitespace-nowrap border-r border-gray-100 px-4 py-2 font-mono text-xs text-gray-700 last:border-r-0">
                    {row[j] === null ? <span className="italic text-gray-400">NULL</span> : formatCellValue(row[j])}
                  </td>
                ))}
              </tr>
            ))}
            {result.rows.length === 0 && (
              <tr><td colSpan={result.columns.length || 1} className="px-4 py-6 text-center text-sm text-gray-400">No rows returned</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function TaskBook() {
  const [searchParams, setSearchParams] = useSearchParams();
  const skillFilter = searchParams.get('skill') || '';

  const [allSkills, setAllSkills] = useState<StudentSkill[]>([]);
  const [tasks, setTasks] = useState<TaskWithSkills[]>([]);
  const [activeTask, setActiveTask] = useState<TaskWithSkills | null>(null);
  const [query, setQuery] = useState('');
  const [execResult, setExecResult] = useState<ExecuteResult | null>(null);
  const [executing, setExecuting] = useState(false);
  const [loading, setLoading] = useState(true);

  const editorRef = useRef<Parameters<OnMount>[0] | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<StudentSkill[]>('/skills/student'),
      api.get<TaskWithSkills[]>(`/tasks${skillFilter ? `?skill=${skillFilter}` : ''}`),
    ])
      .then(([skillsRes, tasksRes]) => {
        setAllSkills(skillsRes.data);
        setTasks(tasksRes.data);
        if (tasksRes.data.length > 0) setActiveTask(tasksRes.data[0]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [skillFilter]);

  const handleExecute = useCallback(async () => {
    if (!query.trim()) return;
    setExecuting(true);
    setExecResult(null);
    try {
      const res = await api.post<ExecuteResult>('/sandbox/execute', { sql: query });
      setExecResult(res.data);
    } catch (err: unknown) {
      const data = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error;
      setExecResult({ columns: [], rows: [], row_count: 0, execution_time_ms: 0, error: data?.message || 'Execution failed' });
    } finally {
      setExecuting(false);
    }
  }, [query]);

  const executeRef = useRef(handleExecute);
  executeRef.current = handleExecute;

  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor;
    editor.addCommand(2048 | 3, () => executeRef.current());
  };

  if (loading) {
    return <div className="flex justify-center py-20"><div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" /></div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Task Book</h1>
        <p className="mt-1 text-sm text-gray-500">Practice tasks by skill area</p>
      </div>

      {/* Skill filter */}
      <div className="mb-4 flex flex-wrap gap-2">
        <button
          onClick={() => setSearchParams({})}
          className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${!skillFilter ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
        >
          All
        </button>
        {allSkills.map((s) => (
          <button
            key={s.skill_code}
            onClick={() => setSearchParams({ skill: s.skill_code })}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${skillFilter === s.skill_code ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            {s.skill_icon} {s.skill_title} {Number(s.percentage) > 0 && `(${Math.round(Number(s.percentage))}%)`}
          </button>
        ))}
      </div>

      <div className="flex gap-4">
        {/* Task list */}
        <div className="w-1/3 space-y-2">
          {tasks.map((t) => (
            <button
              key={t.id}
              onClick={() => { setActiveTask(t); setQuery(''); setExecResult(null); }}
              className={`w-full rounded-lg border px-3 py-2.5 text-left text-sm transition ${activeTask?.id === t.id ? 'border-indigo-300 bg-indigo-50 shadow-sm' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}
            >
              <span className="font-medium text-gray-900">{t.title}</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {t.skills.map((sk) => (
                  <span key={sk.code} className="rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">{sk.code}</span>
                ))}
              </div>
              <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">{t.description}</p>
            </button>
          ))}
          {tasks.length === 0 && (
            <p className="py-10 text-center text-sm text-gray-400">No tasks for this skill yet.</p>
          )}
        </div>

        {/* SQL Editor */}
        <div className="flex w-2/3 flex-col gap-4">
          {activeTask && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
              <span className="text-xs font-bold uppercase tracking-wide text-amber-800">TASK</span>
              <h3 className="mt-1 text-sm font-semibold text-amber-900">{activeTask.title}</h3>
              <p className="mt-1 text-xs text-amber-800">{activeTask.description}</p>
            </div>
          )}

          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-2">
              <span className="text-xs font-medium uppercase tracking-wider text-gray-500">SQL Editor</span>
              <span className="text-xs text-gray-400">Ctrl+Enter</span>
            </div>
            <div className="min-h-[200px]">
              <Editor
                height="200px"
                defaultLanguage="sql"
                theme="vs-dark"
                value={query}
                onChange={(val) => setQuery(val ?? '')}
                onMount={handleEditorMount}
                options={{ minimap: { enabled: false }, fontSize: 14, lineNumbers: 'on', scrollBeyondLastLine: false, padding: { top: 12 }, tabSize: 2, insertSpaces: true }}
              />
            </div>
          </div>

          <button
            onClick={handleExecute}
            disabled={executing || !query.trim()}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-50"
          >
            {executing ? 'Running...' : 'Run'}
          </button>

          {execResult && <SqlResultTable result={execResult} />}
          {!execResult && (
            <div className="flex items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50/50 p-8">
              <p className="text-sm text-gray-400">Write a query and press Run</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}