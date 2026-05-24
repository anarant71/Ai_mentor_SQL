-- AI Mentor MVP bootstrap script.
-- Target database: PostgreSQL 16+.
-- Safe to run repeatedly: it creates missing extensions, tables,
-- triggers, and indexes without dropping data.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL,
    password_hash text,
    display_name text NOT NULL,
    role text NOT NULL DEFAULT 'student',
    status text NOT NULL DEFAULT 'active',
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_role_check
        CHECK (role IN ('student', 'admin', 'mentor')),
    CONSTRAINT users_status_check
        CHECK (status IN ('active', 'inactive', 'blocked'))
);

CREATE TABLE IF NOT EXISTS student_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_goal text,
    current_level text NOT NULL DEFAULT 'beginner',
    preferred_language text NOT NULL DEFAULT 'ru',
    timezone text NOT NULL DEFAULT 'UTC',
    weekly_study_minutes integer NOT NULL DEFAULT 0,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT student_profiles_user_id_unique UNIQUE (user_id),
    CONSTRAINT student_profiles_current_level_check
        CHECK (current_level IN (
            'beginner',
            'junior',
            'middle',
            'strong_middle',
            'advanced'
        )),
    CONSTRAINT student_profiles_weekly_study_minutes_check
        CHECK (weekly_study_minutes >= 0)
);

CREATE TABLE IF NOT EXISTS skills (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL,
    title text NOT NULL,
    description text,
    category text,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT skills_code_unique UNIQUE (code),
    CONSTRAINT skills_status_check
        CHECK (status IN ('active', 'archived'))
);

CREATE TABLE IF NOT EXISTS student_skills (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id uuid NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    level integer NOT NULL DEFAULT 0,
    confidence numeric(4, 3) NOT NULL DEFAULT 0,
    attempts_count integer NOT NULL DEFAULT 0,
    successful_attempts_count integer NOT NULL DEFAULT 0,
    last_practiced_at timestamptz,
    evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT student_skills_student_skill_unique
        UNIQUE (student_id, skill_id),
    CONSTRAINT student_skills_level_check
        CHECK (level BETWEEN 0 AND 5),
    CONSTRAINT student_skills_confidence_check
        CHECK (confidence BETWEEN 0 AND 1),
    CONSTRAINT student_skills_attempts_count_check
        CHECK (attempts_count >= 0),
    CONSTRAINT student_skills_successful_attempts_count_check
        CHECK (successful_attempts_count >= 0),
    CONSTRAINT student_skills_successful_attempts_lte_attempts_check
        CHECK (successful_attempts_count <= attempts_count)
);

CREATE TABLE IF NOT EXISTS lessons (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_skill_id uuid REFERENCES skills(id) ON DELETE SET NULL,
    slug text NOT NULL,
    title text NOT NULL,
    summary text,
    content_path text NOT NULL,
    difficulty integer NOT NULL,
    estimated_minutes integer NOT NULL DEFAULT 0,
    status text NOT NULL DEFAULT 'draft',
    prerequisites jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT lessons_slug_unique UNIQUE (slug),
    CONSTRAINT lessons_difficulty_check
        CHECK (difficulty BETWEEN 1 AND 5),
    CONSTRAINT lessons_estimated_minutes_check
        CHECK (estimated_minutes >= 0),
    CONSTRAINT lessons_status_check
        CHECK (status IN ('draft', 'published', 'archived'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id uuid REFERENCES lessons(id) ON DELETE SET NULL,
    primary_skill_id uuid REFERENCES skills(id) ON DELETE SET NULL,
    slug text NOT NULL,
    title text NOT NULL,
    description text,
    task_type text NOT NULL,
    difficulty integer NOT NULL,
    instructions text NOT NULL,
    expected_answer jsonb,
    validation_strategy text NOT NULL DEFAULT 'ai',
    status text NOT NULL DEFAULT 'draft',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT tasks_slug_unique UNIQUE (slug),
    CONSTRAINT tasks_task_type_check
        CHECK (task_type IN (
            'sql',
            'text',
            'quiz',
            'project',
            'review',
            'diagnostic'
        )),
    CONSTRAINT tasks_difficulty_check
        CHECK (difficulty BETWEEN 1 AND 5),
    CONSTRAINT tasks_validation_strategy_check
        CHECK (validation_strategy IN (
            'ai',
            'exact_match',
            'sql_result',
            'manual'
        )),
    CONSTRAINT tasks_status_check
        CHECK (status IN ('draft', 'published', 'archived'))
);

CREATE TABLE IF NOT EXISTS submissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    answer jsonb NOT NULL,
    score numeric(4, 3),
    feedback text,
    status text NOT NULL DEFAULT 'submitted',
    submitted_at timestamptz NOT NULL DEFAULT now(),
    reviewed_at timestamptz,

    CONSTRAINT submissions_score_check
        CHECK (score IS NULL OR score BETWEEN 0 AND 1),
    CONSTRAINT submissions_status_check
        CHECK (status IN (
            'submitted',
            'reviewed',
            'accepted',
            'rejected',
            'needs_revision'
        )),
    CONSTRAINT submissions_reviewed_at_check
        CHECK (reviewed_at IS NULL OR reviewed_at >= submitted_at)
);

CREATE TABLE IF NOT EXISTS roadmaps (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title text NOT NULL,
    goal text,
    status text NOT NULL DEFAULT 'draft',
    version integer NOT NULL DEFAULT 1,
    starts_at timestamptz,
    completed_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT roadmaps_status_check
        CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    CONSTRAINT roadmaps_version_check
        CHECK (version >= 1),
    CONSTRAINT roadmaps_completed_at_check
        CHECK (completed_at IS NULL OR starts_at IS NULL OR completed_at >= starts_at)
);

CREATE TABLE IF NOT EXISTS roadmap_steps (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_id uuid NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    skill_id uuid REFERENCES skills(id) ON DELETE SET NULL,
    lesson_id uuid REFERENCES lessons(id) ON DELETE SET NULL,
    task_id uuid REFERENCES tasks(id) ON DELETE SET NULL,
    position integer NOT NULL,
    step_type text NOT NULL,
    title text NOT NULL,
    description text,
    difficulty integer,
    status text NOT NULL DEFAULT 'locked',
    expected_outcome text,
    due_at timestamptz,
    started_at timestamptz,
    completed_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT roadmap_steps_roadmap_position_unique
        UNIQUE (roadmap_id, position),
    CONSTRAINT roadmap_steps_position_check
        CHECK (position > 0),
    CONSTRAINT roadmap_steps_step_type_check
        CHECK (step_type IN (
            'lesson',
            'task',
            'practice',
            'review',
            'diagnostic',
            'mentor'
        )),
    CONSTRAINT roadmap_steps_difficulty_check
        CHECK (difficulty IS NULL OR difficulty BETWEEN 1 AND 5),
    CONSTRAINT roadmap_steps_status_check
        CHECK (status IN (
            'locked',
            'available',
            'in_progress',
            'completed',
            'skipped'
        )),
    CONSTRAINT roadmap_steps_completed_at_check
        CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);

CREATE TABLE IF NOT EXISTS mentor_conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context_type text NOT NULL DEFAULT 'general',
    context_id uuid,
    title text,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT mentor_conversations_context_type_check
        CHECK (context_type IN (
            'general',
            'lesson',
            'task',
            'roadmap',
            'submission'
        )),
    CONSTRAINT mentor_conversations_context_id_check
        CHECK (
            (context_type = 'general' AND context_id IS NULL)
            OR (context_type <> 'general' AND context_id IS NOT NULL)
        ),
    CONSTRAINT mentor_conversations_status_check
        CHECK (status IN ('active', 'archived'))
);

CREATE TABLE IF NOT EXISTS mentor_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL
        REFERENCES mentor_conversations(id) ON DELETE CASCADE,
    role text NOT NULL,
    content text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT mentor_messages_role_check
        CHECK (role IN ('student', 'assistant', 'system'))
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'users_set_updated_at'
          AND tgrelid = 'users'::regclass
    ) THEN
        CREATE TRIGGER users_set_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'student_profiles_set_updated_at'
          AND tgrelid = 'student_profiles'::regclass
    ) THEN
        CREATE TRIGGER student_profiles_set_updated_at
        BEFORE UPDATE ON student_profiles
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'skills_set_updated_at'
          AND tgrelid = 'skills'::regclass
    ) THEN
        CREATE TRIGGER skills_set_updated_at
        BEFORE UPDATE ON skills
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'student_skills_set_updated_at'
          AND tgrelid = 'student_skills'::regclass
    ) THEN
        CREATE TRIGGER student_skills_set_updated_at
        BEFORE UPDATE ON student_skills
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'lessons_set_updated_at'
          AND tgrelid = 'lessons'::regclass
    ) THEN
        CREATE TRIGGER lessons_set_updated_at
        BEFORE UPDATE ON lessons
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'tasks_set_updated_at'
          AND tgrelid = 'tasks'::regclass
    ) THEN
        CREATE TRIGGER tasks_set_updated_at
        BEFORE UPDATE ON tasks
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'roadmaps_set_updated_at'
          AND tgrelid = 'roadmaps'::regclass
    ) THEN
        CREATE TRIGGER roadmaps_set_updated_at
        BEFORE UPDATE ON roadmaps
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'roadmap_steps_set_updated_at'
          AND tgrelid = 'roadmap_steps'::regclass
    ) THEN
        CREATE TRIGGER roadmap_steps_set_updated_at
        BEFORE UPDATE ON roadmap_steps
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'mentor_conversations_set_updated_at'
          AND tgrelid = 'mentor_conversations'::regclass
    ) THEN
        CREATE TRIGGER mentor_conversations_set_updated_at
        BEFORE UPDATE ON mentor_conversations
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS users_status_idx
    ON users (status);

CREATE INDEX IF NOT EXISTS student_skills_student_id_idx
    ON student_skills (student_id);

CREATE INDEX IF NOT EXISTS student_skills_skill_id_idx
    ON student_skills (skill_id);

CREATE INDEX IF NOT EXISTS skills_status_idx
    ON skills (status);

CREATE INDEX IF NOT EXISTS lessons_status_difficulty_idx
    ON lessons (status, difficulty);

CREATE INDEX IF NOT EXISTS lessons_primary_skill_id_idx
    ON lessons (primary_skill_id);

CREATE INDEX IF NOT EXISTS tasks_status_difficulty_idx
    ON tasks (status, difficulty);

CREATE INDEX IF NOT EXISTS tasks_lesson_id_idx
    ON tasks (lesson_id);

CREATE INDEX IF NOT EXISTS tasks_primary_skill_id_idx
    ON tasks (primary_skill_id);

CREATE INDEX IF NOT EXISTS submissions_student_submitted_at_idx
    ON submissions (student_id, submitted_at DESC);

CREATE INDEX IF NOT EXISTS submissions_task_id_idx
    ON submissions (task_id);

CREATE INDEX IF NOT EXISTS submissions_status_idx
    ON submissions (status);

CREATE INDEX IF NOT EXISTS roadmaps_student_id_idx
    ON roadmaps (student_id);

CREATE UNIQUE INDEX IF NOT EXISTS roadmaps_one_active_per_student_idx
    ON roadmaps (student_id)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS roadmap_steps_roadmap_status_position_idx
    ON roadmap_steps (roadmap_id, status, position);

CREATE INDEX IF NOT EXISTS roadmap_steps_skill_id_idx
    ON roadmap_steps (skill_id);

CREATE INDEX IF NOT EXISTS roadmap_steps_lesson_id_idx
    ON roadmap_steps (lesson_id);

CREATE INDEX IF NOT EXISTS roadmap_steps_task_id_idx
    ON roadmap_steps (task_id);

CREATE INDEX IF NOT EXISTS mentor_conversations_student_updated_at_idx
    ON mentor_conversations (student_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS mentor_conversations_context_idx
    ON mentor_conversations (context_type, context_id);

CREATE INDEX IF NOT EXISTS mentor_messages_conversation_created_at_idx
    ON mentor_messages (conversation_id, created_at);
