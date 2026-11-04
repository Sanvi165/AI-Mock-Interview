"""Demo-mode data: a built-in question bank, demo follow-ups and demo history seeding.

Used when GEMINI_API_KEY is missing or the AI call fails.
"""
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

QUESTION_BANK: list[dict] = [
    # ---------- Technical (indices 0-9) ----------
    {
        "type": "Technical", "topic": "Python Basics", "difficulty": "easy",
        "text": "What is the difference between a list and a tuple in Python?",
        "keywords": ["mutable", "immutable", "tuple", "list", "hashable"],
        "model_answer": "A list is mutable, so you can add, remove or change its items after creation. A tuple is immutable, so it cannot change once created, which makes a tuple hashable when its items are hashable and safe to use as a dictionary key. A tuple is also slightly faster and uses less memory than a list, so I use a tuple for fixed data and a list for data that changes.",
    },
    {
        "type": "Technical", "topic": "Data Structures", "difficulty": "medium",
        "text": "How does a Python dictionary store and find values?",
        "keywords": ["hash", "key", "collision", "lookup", "o(1)"],
        "model_answer": "A dictionary is a hash table. Python computes the hash of each key and uses it to pick a slot in an internal array, so a lookup by key takes O(1) time on average. When two keys land in the same slot, which is called a collision, Python resolves it by probing for another free slot. Keys must be hashable, and the table is resized as it grows to keep the lookup fast.",
    },
    {
        "type": "Technical", "topic": "OOP", "difficulty": "easy",
        "text": "What are the four pillars of object-oriented programming? Give a short example of each.",
        "keywords": ["encapsulation", "inheritance", "polymorphism", "abstraction", "class"],
        "model_answer": "The four pillars are encapsulation, inheritance, polymorphism and abstraction. Encapsulation bundles data and methods inside a class and hides internal details, like a BankAccount class with a private balance. Inheritance lets a child class reuse a parent class, like Dog extending Animal. Polymorphism lets different classes respond to the same method in their own way, like speak() on Dog and Cat. Abstraction exposes only the essential interface, like a Shape class with an area() method.",
    },
    {
        "type": "Technical", "topic": "DBMS", "difficulty": "medium",
        "text": "What is normalization in a database and why is it used?",
        "keywords": ["redundancy", "anomaly", "1nf", "2nf", "3nf", "dependency"],
        "model_answer": "Normalization is organizing tables to reduce data redundancy and avoid update, insert and delete anomaly problems. It works in steps: 1NF removes repeating groups so every value is atomic, 2NF removes partial dependency on part of a composite key, and 3NF removes transitive dependency between non-key columns. The result is smaller, consistent tables connected by foreign keys, although too much normalization can make queries need more joins.",
    },
    {
        "type": "Technical", "topic": "SQL", "difficulty": "medium",
        "text": "Explain the difference between INNER JOIN and LEFT JOIN with an example.",
        "keywords": ["inner join", "left join", "matching", "null", "left table"],
        "model_answer": "An INNER JOIN returns only the rows that have matching values in both tables. A LEFT JOIN returns every row from the left table and the matching rows from the right table, and it fills the right side with NULL when there is no match. For example, joining students with marks using INNER JOIN hides students without marks, while a LEFT JOIN still lists them with NULL marks.",
    },
    {
        "type": "Technical", "topic": "Web and REST APIs", "difficulty": "easy",
        "text": "What is a REST API and which HTTP methods are commonly used?",
        "keywords": ["stateless", "resource", "http", "post", "delete", "json"],
        "model_answer": "A REST API lets clients work with resources over HTTP using URLs, and each request is stateless, so the server does not remember earlier requests. The common methods are GET to read a resource, POST to create one, PUT to update one and DELETE to remove one. Data is usually exchanged as JSON and the server replies with status codes such as 200, 201 or 404.",
    },
    {
        "type": "Technical", "topic": "Operating Systems", "difficulty": "easy",
        "text": "What is the difference between a process and a thread?",
        "keywords": ["process", "thread", "memory", "share", "context switch"],
        "model_answer": "A process is an independent program in execution with its own memory space, while a thread is a lightweight unit of execution inside a process. Threads of the same process share memory and resources, so communication is fast but needs synchronization to avoid race conditions. A context switch between threads is cheaper than between processes, but a crash in one thread can bring down the whole process.",
    },
    {
        "type": "Technical", "topic": "Algorithms", "difficulty": "medium",
        "text": "How does binary search work and what is its time complexity?",
        "keywords": ["sorted", "middle", "half", "o(log n)", "compare"],
        "model_answer": "Binary search works on a sorted array. It compares the target with the middle element and, if they differ, discards half of the array and repeats on the remaining half. Because the search space halves each step, the time complexity is O(log n), compared with O(n) for linear search.",
    },
    {
        "type": "Technical", "topic": "Operating Systems", "difficulty": "hard",
        "text": "What is a deadlock and how can it be prevented?",
        "keywords": ["mutual exclusion", "hold and wait", "no preemption", "circular wait"],
        "model_answer": "A deadlock happens when processes wait for each other forever and none can proceed. It needs four conditions together: mutual exclusion, hold and wait, no preemption and circular wait. Prevention breaks at least one of them, for example by acquiring all resources at once, allowing preemption, or ordering resources so circular wait cannot form.",
    },
    {
        "type": "Technical", "topic": "Computer Networks", "difficulty": "medium",
        "text": "Explain the TCP three-way handshake.",
        "keywords": ["syn", "syn-ack", "ack", "connection", "reliable"],
        "model_answer": "The three-way handshake sets up a reliable TCP connection before data is sent. First the client sends a SYN to request a connection. The server replies with SYN-ACK to acknowledge and agree. Finally the client sends an ACK, and both sides can start sending data.",
    },
    # ---------- HR (indices 10-15) ----------
    {
        "type": "HR", "topic": "Self Introduction", "difficulty": "easy",
        "text": "Tell me about yourself.",
        "keywords": ["education", "skills", "project", "goal", "interest"],
        "model_answer": "I am a final-year engineering student, and my education has given me a strong base in programming and problem solving. My main skills are Python and web development, and I built a project that applied them to a real problem. I am interested in backend engineering, and my goal is to grow into a developer who builds reliable software for users.",
    },
    {
        "type": "HR", "topic": "Self Awareness", "difficulty": "easy",
        "text": "What are your biggest strengths and one weakness you are improving?",
        "keywords": ["strength", "weakness", "example", "improving", "learn"],
        "model_answer": "One strength is that I learn quickly, for example I picked up a new framework in a week to finish a project. My weakness is that I used to hesitate to ask for help, and I am improving it by asking questions early and noting what I learn each time.",
    },
    {
        "type": "HR", "topic": "Motivation", "difficulty": "easy",
        "text": "Why do you want to work in this role?",
        "keywords": ["interest", "skills", "growth", "contribute", "learn"],
        "model_answer": "I am interested in this role because it matches my skills in programming and problem solving. I want to contribute to real products, learn from experienced engineers and have room for growth in my career.",
    },
    {
        "type": "HR", "topic": "Teamwork", "difficulty": "medium",
        "text": "Describe a time you worked in a team to finish a project.",
        "keywords": ["team", "role", "communication", "result", "challenge"],
        "model_answer": "In my final-year project our team of four had a tight deadline. My role was building the backend, and we held short daily meetings to keep communication clear. A challenge was merging conflicting code, which we solved with Git branches, and the result was a working demo delivered on time.",
    },
    {
        "type": "HR", "topic": "Learning from Failure", "difficulty": "medium",
        "text": "Tell me about a failure and what you learned from it.",
        "keywords": ["mistake", "learned", "responsibility", "improved", "outcome"],
        "model_answer": "In one project I made a mistake by skipping testing, and a bug appeared during the demo. I took responsibility, fixed it that night and learned to write tests early. The outcome was that my later projects improved a lot because I tested every feature before submitting.",
    },
    {
        "type": "HR", "topic": "Career Goals", "difficulty": "easy",
        "text": "Where do you see yourself in five years?",
        "keywords": ["goal", "learn", "skills", "growth", "role"],
        "model_answer": "My goal is to grow into a strong engineer with deep skills in my field. In five years I want to keep learning, take on more responsibility and move into a leadership role while still contributing technically. I see steady growth coming from good projects and mentors.",
    },
    # ---------- Situational (indices 16-21) ----------
    {
        "type": "Situational", "topic": "Problem Solving", "difficulty": "medium",
        "text": "Your deadline is tomorrow and you find a serious bug. What do you do?",
        "keywords": ["prioritize", "reproduce", "communicate", "fix", "test"],
        "model_answer": "I would first reproduce the bug and judge how serious it is, then prioritize it over lower-risk work. I would communicate with my manager about the situation and the risk. Then I would fix the root cause, test the fix carefully, and if it cannot be done safely I would propose a workaround.",
    },
    {
        "type": "Situational", "topic": "Teamwork", "difficulty": "medium",
        "text": "A teammate is not contributing to the group project. How do you handle it?",
        "keywords": ["talk", "understand", "support", "escalate", "communication"],
        "model_answer": "I would talk to the teammate privately to understand the reason, because there may be a personal or skill problem. I would offer support, such as splitting the work into smaller tasks, and keep communication open. If nothing improves, I would escalate to the mentor or manager with facts, not blame.",
    },
    {
        "type": "Situational", "topic": "Communication", "difficulty": "hard",
        "text": "You disagree with your manager's technical decision. What do you do?",
        "keywords": ["listen", "data", "respect", "discuss", "decision"],
        "model_answer": "I would listen first to understand the reasoning behind the decision. Then I would respectfully discuss my concern with data, such as benchmarks or examples, and offer an alternative. If the manager still chooses the original option, I would respect the decision and support it fully.",
    },
    {
        "type": "Situational", "topic": "Learning Agility", "difficulty": "medium",
        "text": "You must learn a new technology in one week. How do you start?",
        "keywords": ["documentation", "basics", "project", "practice", "plan"],
        "model_answer": "I would make a plan for the week and start with the official documentation to learn the basics. Then I would build a small project to practice each concept and ask for help when I get stuck. By the end of the week I would summarize what I learned in notes.",
    },
    {
        "type": "Situational", "topic": "Debugging", "difficulty": "hard",
        "text": "A client reports that your application is slow. How will you investigate?",
        "keywords": ["reproduce", "measure", "profile", "logs", "bottleneck"],
        "model_answer": "I would reproduce the slowness and measure response times to get a baseline. Then I would check the logs and profile the code and database queries to find the bottleneck. After fixing it, for example by adding an index or caching, I would measure again to confirm the improvement.",
    },
    {
        "type": "Situational", "topic": "Time Management", "difficulty": "medium",
        "text": "You are given two tasks with the same deadline. How do you prioritize?",
        "keywords": ["priority", "impact", "deadline", "communicate", "plan"],
        "model_answer": "I would compare the impact and urgency of both tasks to set a priority, then plan my time for each. I would communicate with the manager about the shared deadline and ask whether one can move. If needed I would deliver the most important task first and finish the other right after.",
    },
]


def find_bank_entry(question_text: str) -> Optional[dict]:
    """Return the bank entry for a question text (used for rule-based scoring)."""
    for entry in QUESTION_BANK:
        if entry["text"] == question_text:
            return entry
    return None


def pick_demo_questions(interview_type: str, count: int) -> list[dict]:
    """Choose demo questions. May return fewer than requested if the bank is small."""
    rng = random.Random()
    types = ("Technical", "HR", "Situational")
    pools = {t: [e for e in QUESTION_BANK if e["type"] == t] for t in types}

    if interview_type == "Mixed":
        shuffled = {t: rng.sample(pool, len(pool)) for t, pool in pools.items()}
        ordered: list[dict] = []
        for i in range(max(len(p) for p in shuffled.values())):
            for t in types:
                if i < len(shuffled[t]):
                    ordered.append(shuffled[t][i])
        chosen = ordered[:count]
    else:
        pool = pools[interview_type]
        chosen = rng.sample(pool, min(count, len(pool)))

    return [
        {"text": e["text"], "topic": e["topic"], "difficulty": e["difficulty"]} for e in chosen
    ]


def demo_followup(topic: str, mode: str) -> dict:
    """Template-based follow-up used in demo mode. mode = 'followup' or 'simpler'."""
    if mode == "simpler":
        return {
            "text": (
                f"Let's simplify. In two or three plain sentences, what is the basic idea "
                f"behind {topic}? Give one small example."
            ),
            "topic": topic,
            "difficulty": "easy",
        }
    return {
        "text": (
            f"Good answer. Can you describe a real project or situation where you applied "
            f"{topic}, and what trade-offs or problems you faced?"
        ),
        "topic": topic,
        "difficulty": "hard",
    }


# ---------- demo history seeding (so charts have data without taking 4 interviews) ----------
SEED_ANSWER = "(Seeded demo answer - this sample data was not written by you.)"

# answers = (question bank index, overall score)
DEMO_SESSIONS = [
    {"days_ago": 28, "role": "Software Engineer", "domain": "Python Backend",
     "level": "Fresher", "type": "Technical",
     "answers": [(0, 55), (3, 35), (5, 48), (6, 50)]},
    {"days_ago": 18, "role": "Software Engineer", "domain": "Python Backend",
     "level": "Fresher", "type": "Technical",
     "answers": [(1, 60), (4, 52), (8, 58), (3, 45)]},
    {"days_ago": 9, "role": "Software Engineer", "domain": "Python Backend",
     "level": "Fresher", "type": "Mixed",
     "answers": [(2, 70), (10, 62), (16, 66), (9, 64)]},
    {"days_ago": 2, "role": "Software Engineer", "domain": "Python Backend",
     "level": "Fresher", "type": "Technical",
     "answers": [(0, 82), (3, 68), (5, 74), (7, 79)]},
]


def _spread_scores(overall: float) -> dict:
    base = overall / 10
    deltas = {
        "relevance": 0.5, "correctness": -0.5, "clarity": 0.3,
        "completeness": -0.3, "problem_solving": 0.0,
    }
    return {k: round(max(0.0, min(10.0, base + d)), 1) for k, d in deltas.items()}


def seed_demo_history(user_id: int) -> int:
    """Insert 4 completed sample sessions for one user. Returns how many were created."""
    # Imported here to avoid circular imports at module load time.
    from app.database import repositories
    from app.services import evaluation_service

    now = datetime.now(timezone.utc)
    created = 0
    for demo in DEMO_SESSIONS:
        when = (now - timedelta(days=demo["days_ago"])).isoformat(timespec="seconds")
        questions = [
            {
                "text": QUESTION_BANK[i]["text"],
                "topic": QUESTION_BANK[i]["topic"],
                "difficulty": QUESTION_BANK[i]["difficulty"],
            }
            for i, _ in demo["answers"]
        ]
        setup = {
            "role": demo["role"], "domain": demo["domain"],
            "experience_level": demo["level"], "interview_type": demo["type"],
        }
        session_id = repositories.create_session(
            user_id, setup, questions, "demo", created_at=when
        )
        stored = repositories.get_questions(session_id)

        for stored_q, (bank_index, target) in zip(stored, demo["answers"]):
            entry = QUESTION_BANK[bank_index]
            scores = _spread_scores(target)
            overall = evaluation_service.calculate_overall(scores)
            feedback = {
                "strengths": ["Sample strength (demo data)."],
                "weaknesses": ["Sample weakness (demo data)."] if overall < 70 else [],
                "missing_concepts": entry["keywords"][:3] if overall < 70 else [],
                "improvements": ["Sample improvement tip (demo data)."],
                "stronger_answer": entry["model_answer"],
            }
            metrics = evaluation_service.compute_metrics(SEED_ANSWER, 60, False).model_dump()
            repositories.save_answer(
                question_id=stored_q["id"], session_id=session_id, answer_text=SEED_ANSWER,
                time_taken_seconds=60, speech_used=False, scores=scores,
                overall_score=overall, feedback=feedback, metrics=metrics,
                source="demo", created_at=when,
            )

        results = repositories.get_results(session_id)
        overall_score, summary = evaluation_service.summarize_session(results)
        repositories.complete_session(
            session_id, overall_score, summary.model_dump(), completed_at=when
        )
        created += 1
    return created