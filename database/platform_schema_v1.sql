-- =============================================================================
-- platform_schema_v1.sql  —  MVP 0.1 Platform Database Schema
-- =============================================================================
-- Описание: Схема БД для платформы AI-Mentor (MVP 0.1).
-- Технология: PostgreSQL 16+
-- Таблицы:   users, student_profiles, lessons, tasks, submissions, lesson_progress
-- Версия:    1.0
-- =============================================================================

BEGIN;

-- =============================================================================
-- 1. Расширения
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================================================
-- 2. Функция-триггер для автоматического обновления updated_at
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
    LANGUAGE plpgsql
    SET search_path TO ''
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION set_updated_at() IS
    'Триггерная функция: автоматически проставляет now() в колонку updated_at при UPDATE.';

-- =============================================================================
-- 3. Таблицы
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 3.1. users  —  Пользователи платформы
-- ---------------------------------------------------------------------------

CREATE TABLE users (
    id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    email           text         NOT NULL,
    password_hash   text         NOT NULL,
    display_name    text         NOT NULL,
    role            text         NOT NULL DEFAULT 'student',
    status          text         NOT NULL DEFAULT 'active',
    created_at      timestamptz  NOT NULL DEFAULT now(),
    updated_at      timestamptz  NOT NULL DEFAULT now()
);

COMMENT ON TABLE users IS
    'Пользователи платформы. Студенты и администраторы.';

COMMENT ON COLUMN users.id IS 'Уникальный идентификатор пользователя (UUID v4).';
COMMENT ON COLUMN users.email IS 'Email пользователя. Используется для входа. Должен быть уникальным.';
COMMENT ON COLUMN users.password_hash IS 'Хэш пароля (bcrypt). Никогда не храним пароль в открытом виде.';
COMMENT ON COLUMN users.display_name IS 'Отображаемое имя. Например: "Руслан".';
COMMENT ON COLUMN users.role IS 'Роль: student — студент, admin — администратор.';
COMMENT ON COLUMN users.status IS 'Статус: active — активен, blocked — заблокирован.';
COMMENT ON COLUMN users.created_at IS 'Дата и время регистрации.';
COMMENT ON COLUMN users.updated_at IS 'Дата и время последнего обновления записи.';

-- Ограничения users
ALTER TABLE users
    ADD CONSTRAINT email_unique UNIQUE (email);

ALTER TABLE users
    ADD CONSTRAINT role_check CHECK (role IN ('student', 'admin'));

ALTER TABLE users
    ADD CONSTRAINT users_status_check CHECK (status IN ('active', 'blocked'));

ALTER TABLE users
    ADD CONSTRAINT email_format_check CHECK (email ~* '^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$');

ALTER TABLE users
    ADD CONSTRAINT display_name_length_check CHECK (char_length(display_name) BETWEEN 1 AND 100);

-- Индексы users
CREATE INDEX idx_users_status ON users (status);
CREATE INDEX idx_users_role ON users (role);

-- Триггер users
CREATE TRIGGER trg_users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 3.2. student_profiles  —  Профили студентов (дополнительные настройки)
-- ---------------------------------------------------------------------------

CREATE TABLE student_profiles (
    id                      uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 uuid         NOT NULL,
    learning_goal           text,
    current_level           text         NOT NULL DEFAULT 'beginner',
    preferred_language      text         NOT NULL DEFAULT 'ru',
    weekly_study_minutes    integer      NOT NULL DEFAULT 0,
    timezone                text         NOT NULL DEFAULT 'Asia/Almaty',
    created_at              timestamptz  NOT NULL DEFAULT now(),
    updated_at              timestamptz  NOT NULL DEFAULT now()
);

COMMENT ON TABLE student_profiles IS
    'Профили студентов. Дополнительные настройки и предпочтения.';

COMMENT ON COLUMN student_profiles.id IS 'Уникальный идентификатор профиля (UUID v4).';
COMMENT ON COLUMN student_profiles.user_id IS 'Ссылка на пользователя (users). Один пользователь = один профиль.';
COMMENT ON COLUMN student_profiles.learning_goal IS 'Цель обучения (свободный текст). Например: "Научиться писать SQL-запросы для работы с себестоимостью".';
COMMENT ON COLUMN student_profiles.current_level IS 'Текущий уровень: beginner, intermediate, advanced.';
COMMENT ON COLUMN student_profiles.preferred_language IS 'Предпочитаемый язык интерфейса: ru, kk, en.';
COMMENT ON COLUMN student_profiles.weekly_study_minutes IS 'Целевое время занятий в минутах в неделю.';
COMMENT ON COLUMN student_profiles.timezone IS 'Часовой пояс студента. Используется для напоминаний.';
COMMENT ON COLUMN student_profiles.created_at IS 'Дата и время создания профиля.';
COMMENT ON COLUMN student_profiles.updated_at IS 'Дата и время последнего обновления профиля.';

-- Ограничения student_profiles
ALTER TABLE student_profiles
    ADD CONSTRAINT user_id_unique UNIQUE (user_id);

ALTER TABLE student_profiles
    ADD CONSTRAINT fk_student_profiles_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE;

ALTER TABLE student_profiles
    ADD CONSTRAINT current_level_check
    CHECK (current_level IN ('beginner', 'intermediate', 'advanced'));

ALTER TABLE student_profiles
    ADD CONSTRAINT weekly_study_minutes_check
    CHECK (weekly_study_minutes >= 0);

ALTER TABLE student_profiles
    ADD CONSTRAINT timezone_not_empty_check
    CHECK (char_length(timezone) > 0);

-- Индексы student_profiles
CREATE INDEX idx_student_profiles_current_level ON student_profiles (current_level);

-- Триггер student_profiles
CREATE TRIGGER trg_student_profiles_set_updated_at
    BEFORE UPDATE ON student_profiles
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 3.3. lessons  —  Уроки курса
-- ---------------------------------------------------------------------------

CREATE TABLE lessons (
    id                  uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    module_number       integer      NOT NULL,
    lesson_number       integer      NOT NULL,
    slug                text         NOT NULL,
    title               text         NOT NULL,
    module_title        text         NOT NULL,
    summary             text         NOT NULL,
    content_path        text         NOT NULL,
    difficulty          integer      NOT NULL DEFAULT 1,
    estimated_minutes   integer      NOT NULL DEFAULT 15,
    status              text         NOT NULL DEFAULT 'published',
    created_at          timestamptz  NOT NULL DEFAULT now(),
    updated_at          timestamptz  NOT NULL DEFAULT now()
);

COMMENT ON TABLE lessons IS
    'Уроки курса. Содержат метаданные и путь к Markdown-файлу с контентом.';

COMMENT ON COLUMN lessons.id IS 'Уникальный идентификатор урока (UUID v4).';
COMMENT ON COLUMN lessons.module_number IS 'Номер модуля (0 — Block 0, 1-10 — модули курса).';
COMMENT ON COLUMN lessons.lesson_number IS 'Номер урока внутри курса (1-50).';
COMMENT ON COLUMN lessons.slug IS 'URL-идентификатор урока (например, lesson-01).';
COMMENT ON COLUMN lessons.title IS 'Название урока (например, "Что такое база данных и PostgreSQL").';
COMMENT ON COLUMN lessons.module_title IS 'Название модуля (например, "Блок 0. Введение в базу данных").';
COMMENT ON COLUMN lessons.summary IS 'Краткое описание урока (1-2 предложения).';
COMMENT ON COLUMN lessons.content_path IS 'Путь к Markdown-файлу с контентом урока (например, lessons/lesson_01.md).';
COMMENT ON COLUMN lessons.difficulty IS 'Сложность урока: 1 — начальный, 5 — экспертный.';
COMMENT ON COLUMN lessons.estimated_minutes IS 'Примерное время выполнения урока в минутах.';
COMMENT ON COLUMN lessons.status IS 'Статус: published — опубликован, draft — черновик, archived — архивный.';
COMMENT ON COLUMN lessons.created_at IS 'Дата и время создания урока.';
COMMENT ON COLUMN lessons.updated_at IS 'Дата и время последнего обновления урока.';

-- Ограничения lessons
ALTER TABLE lessons
    ADD CONSTRAINT slug_unique UNIQUE (slug);

ALTER TABLE lessons
    ADD CONSTRAINT module_lesson_unique UNIQUE (module_number, lesson_number);

ALTER TABLE lessons
    ADD CONSTRAINT content_path_unique UNIQUE (content_path);

ALTER TABLE lessons
    ADD CONSTRAINT lessons_difficulty_check CHECK (difficulty BETWEEN 1 AND 5);

ALTER TABLE lessons
    ADD CONSTRAINT estimated_minutes_check CHECK (estimated_minutes > 0);

ALTER TABLE lessons
    ADD CONSTRAINT lessons_status_check CHECK (status IN ('published', 'draft', 'archived'));

ALTER TABLE lessons
    ADD CONSTRAINT module_number_check CHECK (module_number BETWEEN 0 AND 10);

ALTER TABLE lessons
    ADD CONSTRAINT lesson_number_check CHECK (lesson_number BETWEEN 1 AND 50);

-- Индексы lessons
CREATE INDEX idx_lessons_status ON lessons (status);
CREATE INDEX idx_lessons_module_lesson ON lessons (module_number, lesson_number);
CREATE INDEX idx_lessons_difficulty ON lessons (difficulty);

-- Триггер lessons
CREATE TRIGGER trg_lessons_set_updated_at
    BEFORE UPDATE ON lessons
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 3.4. tasks  —  Задания (SQL-задачи) для уроков
-- ---------------------------------------------------------------------------

CREATE TABLE tasks (
    id                      uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id               uuid,
    slug                    text         NOT NULL,
    title                   text         NOT NULL,
    description             text         NOT NULL,
    instructions            text         NOT NULL,
    expected_result_text    text,
    hint                    text,
    expected_answer_sql     text         NOT NULL,
    validation_strategy     text         NOT NULL DEFAULT 'exact_match',
    difficulty              integer      NOT NULL DEFAULT 1,
    status                  text         NOT NULL DEFAULT 'published',
    created_at              timestamptz  NOT NULL DEFAULT now(),
    updated_at              timestamptz  NOT NULL DEFAULT now()
);

COMMENT ON TABLE tasks IS
    'Практические SQL-задания. Каждое задание принадлежит одному уроку.';

COMMENT ON COLUMN tasks.id IS 'Уникальный идентификатор задания (UUID v4).';
COMMENT ON COLUMN tasks.lesson_id IS 'Ссылка на урок (lessons), к которому относится задание.';
COMMENT ON COLUMN tasks.slug IS 'URL-идентификатор задания (например, task-01-01).';
COMMENT ON COLUMN tasks.title IS 'Название задания (например, "Найди активные модели кресел").';
COMMENT ON COLUMN tasks.description IS 'Условие задачи для студента (что нужно сделать).';
COMMENT ON COLUMN tasks.instructions IS 'Подробная инструкция к заданию (как подойти к решению).';
COMMENT ON COLUMN tasks.expected_result_text IS 'Текстовое описание ожидаемого результата (для студента).';
COMMENT ON COLUMN tasks.hint IS 'Подсказка для студента (показывается по запросу).';
COMMENT ON COLUMN tasks.expected_answer_sql IS 'Эталонный SQL-запрос для автоматической проверки.';
COMMENT ON COLUMN tasks.validation_strategy IS 'Стратегия проверки: exact_match, sql_result, ai, manual.';
COMMENT ON COLUMN tasks.difficulty IS 'Сложность задания: 1 — начальный, 5 — экспертный.';
COMMENT ON COLUMN tasks.status IS 'Статус: published — опубликован, draft — черновик, archived — архивный.';
COMMENT ON COLUMN tasks.created_at IS 'Дата и время создания задания.';
COMMENT ON COLUMN tasks.updated_at IS 'Дата и время последнего обновления задания.';

-- Ограничения tasks
ALTER TABLE tasks
    ADD CONSTRAINT slug_unique UNIQUE (slug);

ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_lesson
    FOREIGN KEY (lesson_id) REFERENCES lessons(id)
    ON DELETE CASCADE;

ALTER TABLE tasks
    ADD CONSTRAINT validation_strategy_check
    CHECK (validation_strategy IN ('exact_match', 'sql_result', 'ai', 'manual'));

ALTER TABLE tasks
    ADD CONSTRAINT tasks_difficulty_check CHECK (difficulty BETWEEN 1 AND 5);

ALTER TABLE tasks
    ADD CONSTRAINT tasks_status_check CHECK (status IN ('published', 'draft', 'archived'));

ALTER TABLE tasks
    ADD CONSTRAINT expected_answer_sql_not_empty_check
    CHECK (char_length(expected_answer_sql) > 0);

-- Индексы tasks
CREATE INDEX idx_tasks_lesson_id ON tasks (lesson_id);
CREATE INDEX idx_tasks_status ON tasks (status);
CREATE INDEX idx_tasks_difficulty ON tasks (difficulty);

-- Триггер tasks
CREATE TRIGGER trg_tasks_set_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 3.5. submissions  —  Попытки выполнения заданий
-- ---------------------------------------------------------------------------

CREATE TABLE submissions (
    id                  uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          uuid         NOT NULL,
    task_id             uuid         NOT NULL,
    attempt_number      integer      NOT NULL,
    sql_text            text         NOT NULL,
    execution_status    text         NOT NULL DEFAULT 'submitted',
    execution_result    jsonb,
    error_text          text,
    score               numeric(4,3),
    feedback            text,
    is_correct          boolean,
    started_at          timestamptz  NOT NULL DEFAULT now(),
    submitted_at        timestamptz  NOT NULL DEFAULT now(),
    reviewed_at         timestamptz
);

COMMENT ON TABLE submissions IS
    'Попытки выполнения заданий. Каждая строка — одна попытка студента.';

COMMENT ON COLUMN submissions.id IS 'Уникальный идентификатор попытки (UUID v4).';
COMMENT ON COLUMN submissions.student_id IS 'Ссылка на студента (users).';
COMMENT ON COLUMN submissions.task_id IS 'Ссылка на задание (tasks).';
COMMENT ON COLUMN submissions.attempt_number IS 'Номер попытки (1, 2, 3...). Сбрасывается при смене задания.';
COMMENT ON COLUMN submissions.sql_text IS 'SQL-запрос, который отправил студент.';
COMMENT ON COLUMN submissions.execution_status IS 'Статус выполнения: submitted, syntax_error, executed, reviewed, accepted, rejected.';
COMMENT ON COLUMN submissions.execution_result IS 'Результат выполнения запроса (JSON: колонки + строки).';
COMMENT ON COLUMN submissions.error_text IS 'Текст ошибки (если запрос не выполнился).';
COMMENT ON COLUMN submissions.score IS 'Оценка от 0 до 1 (0.000 — 1.000).';
COMMENT ON COLUMN submissions.feedback IS 'Текстовый фидбек (для AI Mentor в будущем).';
COMMENT ON COLUMN submissions.is_correct IS 'Флаг корректности: true — верно, false — неверно, NULL — ещё не проверено.';
COMMENT ON COLUMN submissions.started_at IS 'Время начала выполнения задания.';
COMMENT ON COLUMN submissions.submitted_at IS 'Время отправки на проверку.';
COMMENT ON COLUMN submissions.reviewed_at IS 'Время проверки (когда выставлен is_correct).';

-- Ограничения submissions
ALTER TABLE submissions
    ADD CONSTRAINT fk_submissions_student
    FOREIGN KEY (student_id) REFERENCES users(id)
    ON DELETE CASCADE;

ALTER TABLE submissions
    ADD CONSTRAINT fk_submissions_task
    FOREIGN KEY (task_id) REFERENCES tasks(id)
    ON DELETE RESTRICT;

ALTER TABLE submissions
    ADD CONSTRAINT attempt_number_positive_check
    CHECK (attempt_number > 0);

ALTER TABLE submissions
    ADD CONSTRAINT score_range_check
    CHECK (score IS NULL OR (score >= 0 AND score <= 1));

ALTER TABLE submissions
    ADD CONSTRAINT execution_status_check
    CHECK (execution_status IN ('submitted', 'syntax_error', 'executed', 'reviewed', 'accepted', 'rejected'));

ALTER TABLE submissions
    ADD CONSTRAINT sql_text_not_empty_check
    CHECK (char_length(sql_text) > 0);

-- Индексы submissions
CREATE INDEX idx_submissions_student_id ON submissions (student_id);
CREATE INDEX idx_submissions_task_id ON submissions (task_id);
CREATE INDEX idx_submissions_student_task ON submissions (student_id, task_id);
CREATE INDEX idx_submissions_execution_status ON submissions (execution_status);
CREATE INDEX idx_submissions_is_correct ON submissions (is_correct) WHERE is_correct IS NOT NULL;
CREATE INDEX idx_submissions_submitted_at ON submissions (submitted_at DESC);

-- ---------------------------------------------------------------------------
-- 3.6. lesson_progress  —  Прогресс студентов по урокам
-- ---------------------------------------------------------------------------

CREATE TABLE lesson_progress (
    id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      uuid         NOT NULL,
    lesson_id       uuid         NOT NULL,
    status          text         NOT NULL DEFAULT 'not_started',
    started_at      timestamptz,
    completed_at    timestamptz,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    updated_at      timestamptz  NOT NULL DEFAULT now()
);

COMMENT ON TABLE lesson_progress IS
    'Прогресс студентов по урокам. Каждая строка — статус прохождения урока студентом.';

COMMENT ON COLUMN lesson_progress.id IS 'Уникальный идентификатор записи прогресса (UUID v4).';
COMMENT ON COLUMN lesson_progress.student_id IS 'Ссылка на студента (users).';
COMMENT ON COLUMN lesson_progress.lesson_id IS 'Ссылка на урок (lessons).';
COMMENT ON COLUMN lesson_progress.status IS 'Статус: not_started, in_progress, completed, skipped.';
COMMENT ON COLUMN lesson_progress.started_at IS 'Время начала изучения урока.';
COMMENT ON COLUMN lesson_progress.completed_at IS 'Время завершения урока (когда все задания сданы).';
COMMENT ON COLUMN lesson_progress.created_at IS 'Дата и время создания записи.';
COMMENT ON COLUMN lesson_progress.updated_at IS 'Дата и время последнего обновления.';

-- Ограничения lesson_progress
ALTER TABLE lesson_progress
    ADD CONSTRAINT student_lesson_unique UNIQUE (student_id, lesson_id);

ALTER TABLE lesson_progress
    ADD CONSTRAINT fk_lesson_progress_student
    FOREIGN KEY (student_id) REFERENCES users(id)
    ON DELETE CASCADE;

ALTER TABLE lesson_progress
    ADD CONSTRAINT fk_lesson_progress_lesson
    FOREIGN KEY (lesson_id) REFERENCES lessons(id)
    ON DELETE CASCADE;

ALTER TABLE lesson_progress
    ADD CONSTRAINT lesson_progress_status_check
    CHECK (status IN ('not_started', 'in_progress', 'completed', 'skipped'));

ALTER TABLE lesson_progress
    ADD CONSTRAINT dates_consistency_check
    CHECK (completed_at IS NULL OR started_at IS NOT NULL);

ALTER TABLE lesson_progress
    ADD CONSTRAINT completed_not_before_started_check
    CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at);

-- Индексы lesson_progress
CREATE INDEX idx_lesson_progress_student_id ON lesson_progress (student_id);
CREATE INDEX idx_lesson_progress_lesson_id ON lesson_progress (lesson_id);
CREATE INDEX idx_lesson_progress_student_status ON lesson_progress (student_id, status);
CREATE INDEX idx_lesson_progress_status ON lesson_progress (status);

-- Триггер lesson_progress
CREATE TRIGGER trg_lesson_progress_set_updated_at
    BEFORE UPDATE ON lesson_progress
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 4. Итоговая проверка целостности
-- =============================================================================

-- Функция для быстрой проверки: все ли таблицы созданы
CREATE OR REPLACE FUNCTION check_platform_schema()
RETURNS TABLE (table_name text, table_exists boolean, row_count bigint)
    LANGUAGE plpgsql
    SET search_path TO ''
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.table_name::text,
        EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = t.table_name
        ) AS table_exists,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = t.table_name
            )
            THEN pg_class.reltuples::bigint
            ELSE 0
        END AS row_count
    FROM (
        VALUES ('users'),
               ('student_profiles'),
               ('lessons'),
               ('tasks'),
               ('submissions'),
               ('lesson_progress')
    ) AS t(table_name)
    LEFT JOIN pg_class
        ON pg_class.relname = t.table_name
        AND pg_class.relnamespace = 'public'::regnamespace;
END;
$$;

COMMENT ON FUNCTION check_platform_schema() IS
    'Диагностическая функция: проверяет, что все 6 таблиц созданы, и показывает количество строк.';

-- =============================================================================
-- 5. Финал
-- =============================================================================

COMMIT;