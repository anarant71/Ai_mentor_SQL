import subprocess, json, sys

BASE = "http://localhost:8001"
PASS, FAIL = 0, 0

def check(step, expected, actual):
    global PASS, FAIL
    if expected in actual:
        print(f"  [✓] {step}")
        PASS += 1
    else:
        print(f"  [✗] {step}")
        print(f"    Expected: {expected}")
        print(f"    Got: {actual[:200]}")
        FAIL += 1

COOKIE_JAR = "/tmp/e2e_cookies.txt"

def api(method, path, data=None, token=None):
    cmd = ["curl", "-s", "-c", COOKIE_JAR, "-b", COOKIE_JAR,
           "-X", method, f"{BASE}{path}",
           "-H", "Content-Type: application/json"]
    if token:
        cmd.extend(["-H", f"Authorization: Bearer {token}"])
    if data:
        cmd.extend(["-d", json.dumps(data)])
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout

print("=" * 55)
print("  E2E TEST: AI-Mentor API")
print("=" * 55)

# 1. Register
print("\n--- Step 1: Register user ---")
reg = api("POST", "/api/v1/auth/register", {
    "display_name": "E2E Test", "email": "e2e_test@demo.com", "password": "test123456"
})
try:
    data = json.loads(reg)
    check("Register", "display_name", reg)
except:
    login = api("POST", "/api/v1/auth/login", {
        "email": "e2e_test@demo.com", "password": "test123456"
    })
    data = json.loads(login)
    check("Login existing", "display_name", login)
token = None  # Token is in HttpOnly cookie, not accessible from Python

# 2. /me
print("\n--- Step 2: GET /auth/me ---")
me_json = api("GET", "/api/v1/auth/me", token=token)
check("User data", "display_name", me_json)
me = json.loads(me_json)
print(f"  User: {me['display_name']} <{me['email']}> role={me['role']}")

# 3. Lessons
print("\n--- Step 3: GET /lessons ---")
lessons_json = api("GET", "/api/v1/lessons", token=token)
check("Lesson list", "lesson-01", lessons_json)
lessons = json.loads(lessons_json)
print(f"  Found {len(lessons)} lessons:")
for l in lessons:
    print(f"    {l['slug']}: {l['title']}")

# 4. Lesson content
print("\n--- Step 4: GET /lessons/lesson-01 ---")
l_json = api("GET", "/api/v1/lessons/lesson-01", token=token)
check("Lesson detail", "база данных", l_json)
l = json.loads(l_json)
print(f"  Title: {l['title']}")
print(f"  Content: {len(l['content'])} chars")

# 5. Tasks
print("\n--- Step 5: GET /lessons/lesson-01/tasks ---")
tasks_json = api("GET", "/api/v1/lessons/lesson-01/tasks", token=token)
check("Tasks", "task-01-01", tasks_json)
tasks = json.loads(tasks_json)
task_id = tasks[0]["id"]
print(f"  Found {len(tasks)} tasks, first ID: {task_id}")

# 6. Task detail
print(f"\n--- Step 6: GET /tasks/{task_id} ---")
td_json = api("GET", f"/api/v1/tasks/{task_id}", token=token)
check("Task detail", "instructions", td_json)
td = json.loads(td_json)
print(f"  Title: {td['title']}")
print(f"  Has hint: {td['hint'] is not None}")

# 7. Execute SQL
print("\n--- Step 7: POST /sandbox/execute ---")
sql = "SELECT material_code, material_name, category, current_price FROM materials LIMIT 3"
ex_json = api("POST", "/api/v1/sandbox/execute", {"sql": sql}, token=token)
check("Execute", "FAB", ex_json)
ex = json.loads(ex_json)
print(f"  {ex['row_count']} rows, {ex['execution_time_ms']}ms")
print(f"  Cols: {ex['columns']}")

# 8. Submit correct
print("\n--- Step 8: Submit correct answer ---")
correct = """SELECT
    material_code,
    material_name,
    category,
    unit,
    current_price,
    status
FROM materials;"""
sub_json = api("POST", f"/api/v1/tasks/{task_id}/submit",
               {"sql_text": correct}, token=token)
check("Submit correct", "correct", sub_json)
sub = json.loads(sub_json)
print(f"  Attempt #{sub['attempt_number']}: is_correct={sub['is_correct']}")
print(f"  Feedback: {sub['feedback']}")

# 9. Submit wrong
print("\n--- Step 9: Submit wrong answer ---")
wrong = "SELECT material_code, material_name FROM materials;"
wr_json = api("POST", f"/api/v1/tasks/{task_id}/submit",
              {"sql_text": wrong}, token=token)
check("Submit wrong", "correct", wr_json)
wr = json.loads(wr_json)
print(f"  is_correct={wr['is_correct']}, differences={len(wr.get('differences', []))}")
for d in wr.get("differences", []):
    print(f"    - {d[:100]}...")

# 10. Submission history
print(f"\n--- Step 10: GET /tasks/{task_id}/submissions ---")
hist_json = api("GET", f"/api/v1/tasks/{task_id}/submissions", token=token)
check("History", "attempt_number", hist_json)
hist = json.loads(hist_json)
print(f"  {len(hist)} attempts saved in DB:")
for h in hist:
    print(f"    #{h['attempt_number']}: correct={h['is_correct']}, status={h['execution_status']}")

print(f"\n{'=' * 55}")
print(f"  RESULTS: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("  ALL TESTS PASSED")
print(f"{'=' * 55}")