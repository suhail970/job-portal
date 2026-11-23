from sqlmodel import SQLModel, create_engine, Session, select, func
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.security import hash_password
from app.models.enums import UserRole, DriveStatus
from app.models.entities import College, Department, User, StudentProfile, PlacementDrive, CronJob, CronExecution, CompanyPlaybook

# Configure database engine
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)
    
    # Auto-migrate SQLite schema for missing columns on existing tables
    if settings.DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            try:
                result = conn.execute(text("PRAGMA table_info(placement_drives)")).fetchall()
                col_names = [r[1] for r in result]
                if "application_url" not in col_names:
                    conn.execute(text("ALTER TABLE placement_drives ADD COLUMN application_url VARCHAR"))
                if "company_website" not in col_names:
                    conn.execute(text("ALTER TABLE placement_drives ADD COLUMN company_website VARCHAR"))
                if "selection_rounds" not in col_names:
                    conn.execute(text("ALTER TABLE placement_drives ADD COLUMN selection_rounds VARCHAR"))
                conn.commit()
            except Exception as e:
                print(f"Schema migration notice: {e}")

    with Session(engine) as session:
        # Check if default Hermes Cron Jobs exist
        try:
            from croniter import croniter
            existing_col = session.exec(select(College)).first()
            active_col_id = existing_col.id if existing_col else "col-anna-001"

            # Align any legacy college_ids
            if existing_col:
                legacy_jobs = session.exec(select(CronJob).where(CronJob.college_id == "col-anna-001")).all()
                for lj in legacy_jobs:
                    lj.college_id = existing_col.id
                    session.add(lj)
                legacy_drives = session.exec(select(PlacementDrive).where(PlacementDrive.college_id == "col-anna-001")).all()
                for ld in legacy_drives:
                    ld.college_id = existing_col.id
                    session.add(ld)
                session.commit()

            job_count = session.exec(select(func.count(CronJob.id))).one()
            if job_count == 0:
                now = datetime.now(timezone.utc)
                default_jobs = [
                    CronJob(
                        name="Morning Campus Ingestion",
                        description="Daily 9:00 AM aggregate of live web job feeds and verified campus drives.",
                        cron_expr="0 9 * * *",
                        target_location="All",
                        college_id=active_col_id,
                        enabled=True,
                        next_run_at=croniter("0 9 * * *", now).get_next(datetime),
                        grace_minutes=120
                    ),
                    CronJob(
                        name="Afternoon Placement Sync",
                        description="Midday 2:00 PM sync of campus hiring opportunities.",
                        cron_expr="0 14 * * *",
                        target_location="All",
                        college_id=active_col_id,
                        enabled=True,
                        next_run_at=croniter("0 14 * * *", now).get_next(datetime),
                        grace_minutes=120
                    ),
                    CronJob(
                        name="Evening Hiring Digest",
                        description="Evening 8:00 PM compilation of verified campus hiring updates.",
                        cron_expr="0 20 * * *",
                        target_location="All",
                        college_id=active_col_id,
                        enabled=True,
                        next_run_at=croniter("0 20 * * *", now).get_next(datetime),
                        grace_minutes=120
                    ),
                    CronJob(
                        name="Coimbatore Regional Watcher",
                        description="Specialized 11:00 AM monitor for Coimbatore district IT & R&D parks (Bosch, Cognizant, ThoughtWorks, KGISL).",
                        cron_expr="0 11 * * *",
                        target_location="Coimbatore",
                        college_id=active_col_id,
                        enabled=True,
                        next_run_at=croniter("0 11 * * *", now).get_next(datetime),
                        grace_minutes=120
                    )
                ]
                session.add_all(default_jobs)
                session.commit()
                print("Hermes-grade Cron Jobs seeded successfully.")
        except Exception as e:
            print(f"Notice during cron job seed check: {e}")

        # Sanitize HTML descriptions in existing PlacementDrive records
        try:
            from app.workers.job_fetcher import clean_job_description
            all_drives = session.exec(select(PlacementDrive)).all()
            sanitized_any = False
            for d in all_drives:
                if d.job_description and ('<' in d.job_description or d.job_description.startswith('Source:')):
                    d.job_description = clean_job_description(d.job_description)
                    session.add(d)
                    sanitized_any = True
            if sanitized_any:
                session.commit()
        except Exception as e:
            print(f"Notice during drive description sanitization: {e}")

        # Check if already seeded
        existing_admin = session.exec(select(User).where(User.email == "admin@skillbridge.ai")).first()
        if existing_admin:
            return

        print("Seeding initial demonstration database...")
        
        # 1. Create College
        college = College(
            name="Anna University - CEG Campus",
            code="CEG-001",
            address="Guindy, Chennai, Tamil Nadu 600025",
            website="https://www.annauniv.edu"
        )
        session.add(college)
        session.commit()
        session.refresh(college)

        # 2. Create Departments
        dept_cse = Department(college_id=college.id, name="Computer Science and Engineering", code="CSE")
        dept_it = Department(college_id=college.id, name="Information Technology", code="IT")
        dept_ece = Department(college_id=college.id, name="Electronics and Communication Engineering", code="ECE")
        session.add_all([dept_cse, dept_it, dept_ece])
        session.commit()
        session.refresh(dept_cse)

        # 3. Create Users
        admin_user = User(
            email="admin@skillbridge.ai",
            hashed_password=hash_password("Admin@123"),
            full_name="Global Platform Administrator",
            role=UserRole.ADMIN,
            college_id=None
        )
        
        tpo_user = User(
            email="tpo@ceg.edu",
            hashed_password=hash_password("Tpo@123"),
            full_name="Dr. K. Ramanathan (Chief Placement Officer)",
            role=UserRole.TPO,
            college_id=college.id
        )

        student_user = User(
            email="student@ceg.edu",
            hashed_password=hash_password("Student@123"),
            full_name="Aravind Swaminathan",
            role=UserRole.STUDENT,
            college_id=college.id
        )
        session.add_all([admin_user, tpo_user, student_user])
        session.commit()
        session.refresh(student_user)

        # 4. Create Student Profile
        student_profile = StudentProfile(
            user_id=student_user.id,
            college_id=college.id,
            department_id=dept_cse.id,
            roll_number="2022CSE042",
            cgpa=8.65,
            standing_arrears=0,
            history_arrears=0,
            graduation_year=2026,
            phone_number="+91 98765 43210",
            bio="Passionate Fullstack & AI developer interested in scalable cloud backends and distributed systems.",
            github_url="https://github.com/demo-aravind",
            linkedin_url="https://linkedin.com/in/demo-aravind"
        )
        session.add(student_profile)

        # 5. Create Sample Placement Drives
        now = datetime.now(timezone.utc)
        drive_zoho = PlacementDrive(
            college_id=college.id,
            company_name="Zoho Corporation",
            role_title="Software Developer Engineer",
            job_description="Looking for proficient problem solvers with deep knowledge of Data Structures, Algorithms, C/C++/Java, and OOP design patterns.",
            location="Chennai / Tenkasi",
            salary_package="8.5 LPA - 12 LPA",
            min_cgpa=7.0,
            max_arrears=0,
            allowed_departments="CSE,IT,ECE",
            drive_date=now + timedelta(days=3),
            registration_deadline=now + timedelta(days=2),
            status=DriveStatus.ACTIVE,
            application_url="https://www.zohocorp.com/careers/",
            company_website="https://www.zoho.com",
            selection_rounds="Round 1: General Aptitude & C/Java Output Predictor -> Round 2: Basic Programming (Strings & Arrays) -> Round 3: Advanced DSA -> Round 4: Technical & HR Fitment"
        )

        drive_tcs = PlacementDrive(
            college_id=college.id,
            company_name="TCS Digital",
            role_title="Systems Engineer - AI & Cloud",
            job_description="Hiring innovators with strong analytical reasoning, Python, Java, SQL, and understanding of Cloud computing architectures.",
            location="Pan India",
            salary_package="7.5 LPA",
            min_cgpa=6.5,
            max_arrears=1,
            allowed_departments="CSE,IT,ECE",
            drive_date=now + timedelta(days=7),
            registration_deadline=now + timedelta(days=5),
            status=DriveStatus.UPCOMING,
            application_url="https://nextstep.tcs.com/campus/#/",
            company_website="https://www.tcs.com",
            selection_rounds="Round 1: TCS NQT (Numerical, Verbal, Advanced Coding) -> Round 2: Technical Interview (Core CS & Projects) -> Round 3: Managerial & HR Interview"
        )

        drive_amazon = PlacementDrive(
            college_id=college.id,
            company_name="Amazon",
            role_title="Software Development Engineer (SDE-1)",
            job_description="Candidate must excel in Algorithms, System Design basics, Tree/Graph traversals, and demonstrate Amazon Leadership Principles.",
            location="Bengaluru / Hyderabad",
            salary_package="28 LPA - 44 LPA",
            min_cgpa=8.0,
            max_arrears=0,
            allowed_departments="CSE,IT",
            drive_date=now + timedelta(days=1), # 1 Day remaining!
            registration_deadline=now + timedelta(hours=18),
            status=DriveStatus.ACTIVE,
            application_url="https://www.amazon.jobs/en/job_categories/software-development",
            company_website="https://amazon.jobs",
            selection_rounds="Round 1: Online Assessment (Coding + Work Style Assessment) -> Round 2: Technical DSA (Trees/DP/Graphs) -> Round 3: Problem Solving & OOP Design -> Round 4: Bar Raiser & Amazon Leadership Principles"
        )
        session.add_all([drive_zoho, drive_tcs, drive_amazon])
        session.commit()
        print("Database initialized and demo data seeded successfully.")

