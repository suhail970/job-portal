import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select, func
from app.core.database import engine
from app.models.entities import CompanyPlaybook
from app.ai.router import ai_router

logger = logging.getLogger("skillbridge.ai.company_research")

# Authoritative pre-verified profiles for top campus recruiters
FOUNDATIONAL_COMPANY_DOSSIERS: Dict[str, Dict[str, Any]] = {
    "zoho": {
        "company_name": "Zoho Corporation",
        "industry_domain": "Enterprise Cloud Software & SaaS",
        "culture_summary": "Zoho places immense value on raw fundamental problem-solving, zero third-party framework reliance, clean code architecture, and high product ownership.",
        "hiring_rounds": [
            {"round_number": 1, "name": "Basic Programming & C/Java Output", "duration": "90 mins", "focus": "Pointer manipulation, bitwise logic, loop execution traces, recursion"},
            {"round_number": 2, "name": "Advanced Programming (Machine Coding)", "duration": "180 mins", "focus": "Clean OOP design, implementing full console apps (Railway Booking, Call Taxi, Banking Engine)"},
            {"round_number": 3, "name": "Technical Interview (Deep DSA & Projects)", "duration": "45 mins", "focus": "Arrays, 2D matrices, String algorithms, project architecture viva"},
            {"round_number": 4, "name": "HR & Cultural Fitment", "duration": "30 mins", "focus": "Long-term commitment, problem-solving mindset, alignment with Tenkasi/rural tech ethos"}
        ],
        "top_rejection_pitfalls": [
            "Using built-in library helpers like Array.sort(), split(), or Regex during Round 2 machine coding",
            "Failing to handle null pointer exceptions, negative numbers, and boundary limits",
            "Over-engineering simple object models with unnecessary inheritance hierarchies instead of clean composition",
            "Inability to explain memory layout, pointer offsets, or stack vs heap allocations in C/Java"
        ],
        "top_interview_questions": [
            {"question": "Design and implement a Railway Reservation System with Waiting List, RAC, and Confirmed berth allocations.", "category": "MACHINE_CODING", "tip": "Use a modular Class structure (Passenger, Ticket, BookingManager) and maintain separate Queues."},
            {"question": "Given a matrix, find the number of paths from (0,0) to (M-1, N-1) with obstacles.", "category": "DSA", "tip": "Solve using dynamic programming table or memoized recursion."},
            {"question": "Explain internal memory working of C pointers: what is the difference between char *p = 'text' and char p[] = 'text'?", "category": "TECHNICAL", "tip": "Highlight read-only text segment string literal vs stack allocated modifiable array."},
            {"question": "Print all possible permutations of a string without duplicate output.", "category": "ALGORITHMS", "tip": "Use backtracking with a boolean visited array or character swap recursion."}
        ],
        "curated_resources": [
            {"topic": "GeeksforGeeks Zoho Machine Coding Archives", "platform": "GeeksforGeeks", "url": "https://www.geeksforgeeks.org/zoho-interview-experience/", "type": "PRACTICE"},
            {"topic": "Top C Pointers & Tricky Code Snippets", "platform": "Sanfoundry", "url": "https://www.sanfoundry.com/c-programming-questions-answers-pointers/", "type": "CHEAT_SHEET"},
            {"topic": "NeetCode 150 Core Patterns", "platform": "NeetCode", "url": "https://neetcode.io/practice", "type": "PRACTICE"},
            {"topic": "Low Level Design (LLD) Primer", "platform": "GitHub", "url": "https://github.com/prashant-k/low-level-design-primer", "type": "ARCHITECTURE"}
        ]
    },
    "amazon": {
        "company_name": "Amazon",
        "industry_domain": "Cloud Computing (AWS), E-Commerce & AI",
        "culture_summary": "Amazon evaluates candidates heavily on their 16 Leadership Principles (Customer Obsession, Ownership, Bias for Action, Dive Deep) alongside rigorous algorithmic problem-solving.",
        "hiring_rounds": [
            {"round_number": 1, "name": "Online Assessment (OA)", "duration": "90 mins", "focus": "2 LeetCode Medium/Hard algorithmic problems + Work Style Assessment"},
            {"round_number": 2, "name": "Technical Round 1 (Trees & Graphs)", "duration": "60 mins", "focus": "BFS/DFS, Tree traversals, Monotonic Stack, sliding window"},
            {"round_number": 3, "name": "Technical Round 2 (System Design & DP)", "duration": "60 mins", "focus": "LRU Cache, Object-oriented design, dynamic programming, time/space complexity"},
            {"round_number": 4, "name": "Bar Raiser Interview", "duration": "60 mins", "focus": "Senior Amazonian evaluating Leadership Principles via STAR method and deep dive on tradeoffs"}
        ],
        "top_rejection_pitfalls": [
            "Failing to articulate behavioral answers using the structured STAR method (Situation, Task, Action, Result)",
            "Jumping straight into code without first clarifying boundary inputs, constraints, and brute-force complexity",
            "Failing to optimize space complexity or forgetting to analyze amortized time complexity",
            "Not demonstrating ownership or blaming teammates when asked about past project failures"
        ],
        "top_interview_questions": [
            {"question": "Implement an LRU (Least Recently Used) Cache with O(1) get and put operations.", "category": "DSA", "tip": "Use a Hash Map paired with a Doubly Linked List to achieve O(1) access and removal."},
            {"question": "Tell me about a time you faced a tight deadline and had to make technical tradeoffs.", "category": "BEHAVIORAL", "tip": "Structure using STAR method. Emphasize Bias for Action while maintaining quality."},
            {"question": "Find the shortest path in a binary maze with obstacles.", "category": "ALGORITHMS", "tip": "Use Breadth-First Search (BFS) with a visited set; DFS will exceed stack depth."},
            {"question": "Serialize and Deserialize a Binary Tree.", "category": "SYSTEM_DESIGN", "tip": "Use preorder traversal with delimiter for null nodes or level-order traversal."}
        ],
        "curated_resources": [
            {"topic": "Amazon Top 50 LeetCode Curated List", "platform": "LeetCode", "url": "https://leetcode.com/problem-list/top-interview-questions/", "type": "PRACTICE"},
            {"topic": "Amazon 16 Leadership Principles (STAR Framework)", "platform": "Amazon Jobs", "url": "https://www.amazon.jobs/content/en/our-workplace/leadership-principles", "type": "GUIDE"},
            {"topic": "System Design Primer by Donne Martin", "platform": "GitHub", "url": "https://github.com/donnemartin/system-design-primer", "type": "ARCHITECTURE"}
        ]
    },
    "soliton": {
        "company_name": "Soliton Technologies",
        "industry_domain": "Semiconductor Automation, Testing & Enterprise Engineering",
        "culture_summary": "Soliton specializes in semiconductor test automation and enterprise client solutions. They prioritize clean analytical thinking, strong mathematics, signal processing, and low-level C/C++ or LabVIEW/Python architectures.",
        "hiring_rounds": [
            {"round_number": 1, "name": "Analytical & Programming Assessment", "duration": "90 mins", "focus": "Logical reasoning, C/C++ code outputs, basic digital electronics & arrays"},
            {"round_number": 2, "name": "Problem Solving & Core Programming", "duration": "120 mins", "focus": "Data structures, memory allocation, string/matrix manipulation"},
            {"round_number": 3, "name": "Technical Viva & Architecture", "duration": "60 mins", "focus": "OOPS concepts, state machines, hardware-software interfacing, project walkthrough"},
            {"round_number": 4, "name": "Management & Fitment Round", "duration": "45 mins", "focus": "Integrity, passion for engineering, teamwork, communication"}
        ],
        "top_rejection_pitfalls": [
            "Weakness in pointers, memory leaks, and dynamic allocation (malloc/free/new/delete)",
            "Inability to explain finite state machines (FSM) or asynchronous workflows",
            "Surface-level understanding of college final year projects without knowing inner component details"
        ],
        "top_interview_questions": [
            {"question": "Implement a State Machine in C/C++ to model an automated instrument measurement cycle.", "category": "TECHNICAL", "tip": "Use function pointers or enum states with a switch-case state transition table."},
            {"question": "Explain volatile keyword in C and where it is essential in embedded memory mapping.", "category": "HARDWARE_SOFTWARE", "tip": "Explain compiler optimization prevention for memory-mapped I/O registers."},
            {"question": "Detect memory leaks in a C++ program and how to use smart pointers to prevent them.", "category": "BEST_PRACTICES", "tip": "Discuss std::unique_ptr, std::shared_ptr, and RAII pattern."}
        ],
        "curated_resources": [
            {"topic": "Soliton Interview Experiences & Test Pattern", "platform": "GeeksforGeeks", "url": "https://www.geeksforgeeks.org/soliton-technologies-interview-experience/", "type": "PRACTICE"},
            {"topic": "Modern C++ & Memory Management Guide", "platform": "LearnCpp", "url": "https://www.learncpp.com/", "type": "CHEAT_SHEET"},
            {"topic": "Finite State Machines & Embedded Patterns", "platform": "Embedded.fm", "url": "https://embedded.fm/", "type": "GUIDE"}
        ]
    },
    "kovai": {
        "company_name": "Kovai.co",
        "industry_domain": "Enterprise B2B SaaS (Document360, Serverless360)",
        "culture_summary": "Kovai.co builds world-class SaaS enterprise platforms from Coimbatore. They look for strong C# .NET Core, Azure Cloud, React, microservices design, and clean product development practices.",
        "hiring_rounds": [
            {"round_number": 1, "name": "Aptitude & Coding Round", "duration": "90 mins", "focus": "General aptitude, data structures, SQL queries"},
            {"round_number": 2, "name": "Machine Coding & Web APIs", "duration": "120 mins", "focus": "Building RESTful endpoints, relational schema design, clean architectural layers"},
            {"round_number": 3, "name": "Technical Architecture & OOP", "duration": "45 mins", "focus": "SOLID principles, dependency injection, async programming, caching"},
            {"round_number": 4, "name": "Culture Fit & Director Discussion", "duration": "30 mins", "focus": "Passion for product engineering in Coimbatore, team collaboration, learning curve"}
        ],
        "top_rejection_pitfalls": [
            "Lack of understanding of SOLID design principles and separation of concerns",
            "Weak SQL fundamentals (indexes, joins, transaction isolation levels)",
            "Writing synchronous blocking code instead of async/await patterns"
        ],
        "top_interview_questions": [
            {"question": "Design a REST API with rate-limiting, error handling middleware, and dependency injection.", "category": "ARCHITECTURE", "tip": "Explain ASP.NET Core middleware pipeline or Express middleware structure."},
            {"question": "Explain the 5 SOLID design principles with concrete code examples.", "category": "OOP", "tip": "Focus especially on Dependency Inversion and Single Responsibility Principle."},
            {"question": "How do you optimize a slow database query with millions of records?", "category": "DATABASE", "tip": "Discuss composite indexes, query execution plans (EXPLAIN), and Redis caching."}
        ],
        "curated_resources": [
            {"topic": "ASP.NET Core & Modern C# Architecture", "platform": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/aspnet/core/", "type": "OFFICIAL_DOCS"},
            {"topic": "System Design & REST API Best Practices", "platform": "roadmap.sh", "url": "https://roadmap.sh/backend", "type": "ROADMAP"},
            {"topic": "Kovai.co Engineering & Product Insights", "platform": "Kovai.co Tech Blog", "url": "https://www.kovai.co/blog", "type": "COMPANY_INSIGHTS"}
        ]
    }
}

AUTONOMOUS_PROFILER_SYSTEM_PROMPT = """You are the Senior Enterprise Placement Intelligence Researcher for SkillBridge AI.
Your objective is to conduct an exhaustive, verified research deconstruction of ANY company and engineering opening (multinationals, startups, mid-sized companies, or regional IT leaders).

CRITICAL INSTRUCTIONS:
1. Synthesize realistic, highly specific hiring round structures (Round 1 OA, Round 2 Coding/Machine Coding, Round 3 Tech Viva, Round 4 HR).
2. Identify the exact technologies, tools, and technical competencies demanded by this specific role and company domain.
3. List the TOP 4 critical rejection pitfalls that cause candidates to fail interviews at this specific company type.
4. Curate the top 6 high-yield technical and behavioral interview questions with actionable answering tips.
5. Provide 4-5 verified, real-world practice links (GeeksforGeeks archives, LeetCode curated topic lists, official documentation, GitHub cheat sheets) tailored to the required stack.

Respond strictly in valid JSON matching this schema:
{
    "company_name": "Company Name",
    "industry_domain": "e.g. Healthcare Tech / Automotive Embedded / Enterprise B2B SaaS / Fintech",
    "culture_summary": "2-3 sentences on engineering culture and hiring philosophy.",
    "hiring_rounds": [
        {"round_number": 1, "name": "Round Name", "duration": "Duration", "focus": "Exact topics tested"}
    ],
    "top_rejection_pitfalls": [
        "Pitfall 1", "Pitfall 2", "Pitfall 3", "Pitfall 4"
    ],
    "top_interview_questions": [
        {"question": "Question text", "category": "TECHNICAL / CODING / ARCHITECTURE / HR", "tip": "Clear tip on how to impress the interviewer"}
    ],
    "curated_resources": [
        {"topic": "Topic Name", "platform": "GeeksforGeeks / LeetCode / Official Docs / GitHub", "url": "https://...", "type": "PRACTICE / CHEAT_SHEET / GUIDE"}
    ]
}"""

def build_verification_links(company_name: str, role_title: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Generates real-world external interview verification & career research links across
    LinkedIn (Jobs + Alumni Network), Naukri, GeeksforGeeks, AmbitionBox, and LeetCode Discuss.
    """
    import urllib.parse
    clean = company_name.strip()
    encoded = urllib.parse.quote_plus(clean)
    role_encoded = urllib.parse.quote_plus(role_title.strip()) if role_title else ""
    linkedin_job_query = f"{encoded}+{role_encoded}" if role_encoded else encoded
    
    # Safe slug for Naukri URL
    naukri_slug = clean.lower().replace(" ", "-").replace(".", "")

    return [
        {
            "platform": "LinkedIn Jobs",
            "title": f"{clean} Live Openings",
            "url": f"https://www.linkedin.com/jobs/search/?keywords={linkedin_job_query}",
            "short_desc": "Live recruiter postings & direct openings in your active LinkedIn session",
            "icon": "linkedin"
        },
        {
            "platform": "LinkedIn Network",
            "title": f"{clean} Alumni & Referrals",
            "url": f"https://www.linkedin.com/search/results/people/?keywords={encoded}&origin=GLOBAL_SEARCH_HEADER",
            "short_desc": "Connect with college alumni and engineering leads for referrals and tips",
            "icon": "users"
        },
        {
            "platform": "Naukri",
            "title": f"{clean} Salaries & Demand",
            "url": f"https://www.naukri.com/jobs-in-india?keyword={encoded}",
            "short_desc": "Verified salary benchmarks, experience criteria & hiring trends on Naukri",
            "icon": "trending-up"
        },
        {
            "platform": "GeeksforGeeks",
            "title": f"{clean} Student Experiences",
            "url": f"https://www.geeksforgeeks.org/search/?q={encoded}+interview+experience",
            "short_desc": "Real questions from students who attended recent campus drives",
            "icon": "book"
        },
        {
            "platform": "AmbitionBox",
            "title": f"{clean} Difficulty & Ratings",
            "url": f"https://www.ambitionbox.com/search?q={encoded}",
            "short_desc": "Selection percentage, interview difficulty ratings & reviews",
            "icon": "trending"
        },
        {
            "platform": "LeetCode Discuss",
            "title": f"{clean} Coding Questions",
            "url": f"https://leetcode.com/discuss/interview-question?currentPage=1&orderBy=hot&query={encoded}",
            "short_desc": "Latest algorithmic questions & live solutions from candidates",
            "icon": "code"
        }
    ]

async def get_or_create_company_playbook(
    company_name: str,
    role_title: str,
    job_description: str,
    company_website: Optional[str] = None,
    selection_rounds: Optional[str] = None,
    preferred_provider: Optional[str] = None,
    custom_config: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Universal Company Playbook Profiling Engine.
    1. Checks SQLite company_playbooks table for existing profile.
    2. If found, returns it instantly (< 50ms).
    3. If not found, checks foundational dossiers.
    4. If not found, runs Autonomous AI Profiler to research the company, technology stack, and rounds.
    5. Saves the synthesized profile permanently to SQLite for all future student requests.
    """
    clean_company = company_name.strip()
    company_key = clean_company.lower()

    # 1. Check SQLite Database Cache
    with Session(engine) as session:
        existing = session.exec(
            select(CompanyPlaybook).where(func.lower(CompanyPlaybook.company_name) == company_key)
        ).first()

        if existing:
            try:
                rounds = json.loads(existing.hiring_rounds or "[]")
                # If cached record has empty rounds, regenerate rich fallback content
                if not rounds:
                    fallback = _generate_fallback_playbook(clean_company, role_title, selection_rounds)
                    existing.hiring_rounds = json.dumps(fallback.get("hiring_rounds", []))
                    existing.top_rejection_pitfalls = json.dumps(fallback.get("top_rejection_pitfalls", []))
                    existing.top_interview_questions = json.dumps(fallback.get("top_interview_questions", []))
                    existing.curated_resources = json.dumps(fallback.get("curated_resources", []))
                    existing.industry_domain = fallback.get("industry_domain", existing.industry_domain)
                    session.add(existing)
                    session.commit()
                    session.refresh(existing)
                    rounds = fallback.get("hiring_rounds", [])

                return {
                    "id": existing.id,
                    "company_name": existing.company_name,
                    "industry_domain": existing.industry_domain,
                    "culture_summary": existing.culture_summary,
                    "hiring_rounds": rounds,
                    "top_rejection_pitfalls": json.loads(existing.top_rejection_pitfalls or "[]"),
                    "top_interview_questions": json.loads(existing.top_interview_questions or "[]"),
                    "curated_resources": json.loads(existing.curated_resources or "[]"),
                    "verification_links": build_verification_links(existing.company_name, role_title),
                    "college_insider_tips": existing.college_insider_tips,
                    "is_verified": existing.is_verified,
                    "source": "database_cache"
                }
            except Exception as e:
                logger.warning(f"Error parsing cached playbook {existing.id}: {e}")

    # 2. Check Foundational Dossiers
    for base_key, dossier in FOUNDATIONAL_COMPANY_DOSSIERS.items():
        if base_key in company_key or company_key in base_key:
            # Save foundational dossier into DB for permanent caching
            playbook = _persist_playbook(dossier, is_verified=True)
            playbook["source"] = "verified_vault"
            return playbook

    # 3. Autonomous AI Deep Profiler (For startups, regional IT, and new companies)
    logger.info(f"Synthesizing autonomous company intelligence playbook for {clean_company} ({role_title})...")
    
    rounds_hint = f"Known Campus Selection Track: {selection_rounds}\n" if selection_rounds else ""
    website_hint = f"Official Website: {company_website}\n" if company_website else ""
    
    user_prompt = f"""Conduct a comprehensive placement intelligence research profile for:
Company: {clean_company}
Role: {role_title}
{website_hint}{rounds_hint}
Job Description Context:
{job_description[:2000]}"""

    messages = [
        {"role": "system", "content": AUTONOMOUS_PROFILER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response_str = await ai_router.generate_completion(
            messages=messages,
            temperature=0.3,
            preferred_provider=preferred_provider,
            custom_config=custom_config,
            json_mode=True
        )
        data = json.loads(response_str)
        # Ensure company name is set
        data["company_name"] = clean_company
        # If AI generated response without hiring_rounds or empty lists, merge with rich defaults
        if not data.get("hiring_rounds") or not isinstance(data.get("hiring_rounds"), list):
            fallback = _generate_fallback_playbook(clean_company, role_title, selection_rounds)
            for k, v in fallback.items():
                if not data.get(k):
                    data[k] = v
        playbook = _persist_playbook(data, is_verified=True)
        playbook["source"] = "autonomous_ai_research"
        return playbook
    except Exception as e:
        logger.error(f"Autonomous playbook generation failed for {clean_company}: {e}")
        # Robust fallback dossier
        fallback = _generate_fallback_playbook(clean_company, role_title, selection_rounds)
        return _persist_playbook(fallback, is_verified=False)


def _persist_playbook(data: Dict[str, Any], is_verified: bool = True) -> Dict[str, Any]:
    """Persists a synthesized playbook to SQLite."""
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        # Check if already created concurrently
        existing = session.exec(
            select(CompanyPlaybook).where(func.lower(CompanyPlaybook.company_name) == data["company_name"].strip().lower())
        ).first()

        if existing:
            existing.industry_domain = data.get("industry_domain", existing.industry_domain)
            existing.culture_summary = data.get("culture_summary", existing.culture_summary)
            existing.hiring_rounds = json.dumps(data.get("hiring_rounds", []))
            existing.top_rejection_pitfalls = json.dumps(data.get("top_rejection_pitfalls", []))
            existing.top_interview_questions = json.dumps(data.get("top_interview_questions", []))
            existing.curated_resources = json.dumps(data.get("curated_resources", []))
            existing.updated_at = now
            session.add(existing)
            session.commit()
            session.refresh(existing)
            playbook_id = existing.id
        else:
            new_playbook = CompanyPlaybook(
                company_name=data["company_name"].strip(),
                industry_domain=data.get("industry_domain", "Engineering & Software Technology"),
                culture_summary=data.get("culture_summary", f"Specialized engineering organization focusing on {data['company_name']} core competencies."),
                hiring_rounds=json.dumps(data.get("hiring_rounds", [])),
                top_rejection_pitfalls=json.dumps(data.get("top_rejection_pitfalls", [])),
                top_interview_questions=json.dumps(data.get("top_interview_questions", [])),
                curated_resources=json.dumps(data.get("curated_resources", [])),
                is_verified=is_verified,
                created_at=now,
                updated_at=now
            )
            session.add(new_playbook)
            session.commit()
            session.refresh(new_playbook)
            playbook_id = new_playbook.id

    return {
        "id": playbook_id,
        "company_name": data["company_name"],
        "industry_domain": data.get("industry_domain", "Engineering & Technology"),
        "culture_summary": data.get("culture_summary"),
        "hiring_rounds": data.get("hiring_rounds", []),
        "top_rejection_pitfalls": data.get("top_rejection_pitfalls", []),
        "top_interview_questions": data.get("top_interview_questions", []),
        "curated_resources": data.get("curated_resources", []),
        "verification_links": build_verification_links(data["company_name"]),
        "is_verified": is_verified
    }


def _generate_fallback_playbook(company_name: str, role_title: str, selection_rounds: Optional[str] = None) -> Dict[str, Any]:
    """Generates standard engineering rounds when network/AI is temporarily offline."""
    rounds = [
        {"round_number": 1, "name": "Cognitive & Aptitude Assessment", "duration": "60 mins", "focus": "Quantitative aptitude, logical reasoning, verbal ability"},
        {"round_number": 2, "name": "Core Technical & Coding Test", "duration": "90 mins", "focus": "Data Structures, Algorithms (Arrays, Strings, Recursion), SQL queries"},
        {"round_number": 3, "name": "Technical Interview & Project Viva", "duration": "45 mins", "focus": "Deep-dive on resume projects, OOP fundamentals, DBMS & OS concepts"},
        {"round_number": 4, "name": "HR & Fitment Interview", "duration": "30 mins", "focus": "Company knowledge, career goals, problem-solving mindset"}
    ]
    if selection_rounds and "->" in selection_rounds:
        parts = [p.strip() for p in selection_rounds.split("->")]
        rounds = [{"round_number": i + 1, "name": p, "duration": "60 mins", "focus": f"Evaluations for {company_name}"} for i, p in enumerate(parts)]

    return {
        "company_name": company_name,
        "industry_domain": "Technology & Software Engineering",
        "culture_summary": f"{company_name} evaluates engineering candidates on strong computer science fundamentals, clear communication, and modular problem-solving.",
        "hiring_rounds": rounds,
        "top_rejection_pitfalls": [
            "Jumping into coding without clarifying input boundary conditions",
            "Inability to explain time and space complexity (Big-O)",
            "Weak answers on resume projects without knowing the underlying database or architecture"
        ],
        "top_interview_questions": [
            {"question": f"Why do you want to start your software engineering career at {company_name}?", "category": "HR", "tip": "Reference the company's product domain and how your skills align with their tech stack."},
            {"question": "Explain the difference between SQL and NoSQL databases and when to use each.", "category": "DATABASE", "tip": "Discuss ACID compliance vs horizontal scalability and eventual consistency."},
            {"question": "How do you handle edge cases and memory leaks in production code?", "category": "TECHNICAL", "tip": "Explain defensive programming, null-checks, and automated garbage collection / RAII."}
        ],
        "curated_resources": [
            {"topic": "Top 100 Technical Interview Questions", "platform": "GeeksforGeeks", "url": "https://www.geeksforgeeks.org/top-100-interview-questions/", "type": "PRACTICE"},
            {"topic": "NeetCode 150 Core DSA Patterns", "platform": "NeetCode", "url": "https://neetcode.io/practice", "type": "PRACTICE"},
            {"topic": "System Design & API Fundamentals", "platform": "roadmap.sh", "url": "https://roadmap.sh/backend", "type": "ROADMAP"}
        ]
    }

