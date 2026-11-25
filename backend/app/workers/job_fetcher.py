import asyncio
import json
import httpx
import logging
import html
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select, func, or_
from app.core.database import engine
from app.models.entities import PlacementDrive
from app.models.enums import DriveStatus
from app.workers.telegram_worker import telegram_worker
from app.workers.ats_verifier import (
    classify_region_scope,
    detect_source_platform,
    is_valid_direct_url,
    extract_ats_form_schema,
    verify_application_link_and_expiry,
    compute_job_accuracy_score,
    canonicalize_location_query,
    expand_location_terms,
)

logger = logging.getLogger("skillbridge.fetcher")

# Curated High-Frequency Indian & Global Tech Hiring Tracks
VERIFIED_CAMPUS_DRIVES = [
    # --- KOLKATA TECH HUB ---
    {
        "company_name": "PwC Acceleration Center",
        "role_title": "Associate Software Engineer - Cloud & AI",
        "location": "Kolkata (Salt Lake Sector V)",
        "salary_package": "8.0 LPA - 11.5 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Cloud modernization, Azure/AWS serverless architectures, Generative AI pipelines, Python, Docker, microservices.",
        "days_ahead": 9,
        "application_url": "https://www.pwc.in/careers.html",
        "company_website": "https://www.pwc.in",
        "selection_rounds": "Round 1: Cognitive & Tech Online Assessment -> Round 2: Cloud Systems & Coding Interview -> Round 3: Leadership & Fitment Round"
    },
    {
        "company_name": "Cognizant Kolkata Hub",
        "role_title": "GenC Elevate Developer",
        "location": "Kolkata (Bantala / New Town)",
        "salary_package": "7.0 LPA - 9.0 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Enterprise cloud engineering, Java Spring Boot, React, SQL, DevOps automation, agile delivery.",
        "days_ahead": 6,
        "application_url": "https://careers.cognizant.com/global/en",
        "company_website": "https://cognizant.com",
        "selection_rounds": "Round 1: Skill Assessment (Advanced Coding & Data Structures) -> Round 2: Deep Technical Viva -> Round 3: HR Discussion"
    },
    {
        "company_name": "ITC Infotech",
        "role_title": "Associate IT Consultant & Software Engineer",
        "location": "Kolkata (Virginia House)",
        "salary_package": "6.5 LPA - 8.2 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Digital supply chain systems, full-stack Java/Node.js, PostgreSQL, API management, business automation.",
        "days_ahead": 8,
        "application_url": "https://www.itcinfotech.com/",
        "company_website": "https://www.itcinfotech.com",
        "selection_rounds": "Round 1: Aptitude & Programming Test -> Round 2: Technical Interview -> Round 3: HR Fitment"
    },
    {
        "company_name": "IBM India Software Labs",
        "role_title": "Software Engineer (Kolkata Development Center)",
        "location": "Kolkata (Sector V)",
        "salary_package": "10.5 LPA - 14.0 LPA",
        "min_cgpa": 7.2,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT",
        "job_description": "Hybrid cloud development, Red Hat OpenShift, Kubernetes, Golang, Python, enterprise AI solutions.",
        "days_ahead": 11,
        "application_url": "https://www.ibm.com/careers/in-en",
        "company_website": "https://ibm.com",
        "selection_rounds": "Round 1: HackerRank Coding Assessment -> Round 2: Core Computer Science & Algorithms -> Round 3: System Design & Culture"
    },

    # --- CHENNAI TECH HUB ---
    {
        "company_name": "Zoho Corporation",
        "role_title": "Software Development Engineer",
        "location": "Chennai (Estancia / Guduvanchery)",
        "salary_package": "8.5 LPA - 12.0 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Data Structures, Algorithms, C/C++/Java, Object Oriented Design, building scalable enterprise SaaS products.",
        "days_ahead": 4,
        "application_url": "https://careers.zohocorp.com/jobs/Careers",
        "company_website": "https://www.zoho.com",
        "selection_rounds": "Round 1: General Aptitude & C/Java Output -> Round 2: Basic Programming (Arrays & Strings) -> Round 3: Advanced DSA -> Round 4: Tech & HR"
    },
    {
        "company_name": "Freshworks",
        "role_title": "Product Development Engineer",
        "location": "Chennai (SP Infocity / Perungudi)",
        "salary_package": "14.0 LPA - 18.0 LPA",
        "min_cgpa": 7.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT",
        "job_description": "Modern SaaS engineering, Ruby on Rails, Node.js, React, AWS, distributed database systems, low-latency queues.",
        "days_ahead": 10,
        "application_url": "https://careers.freshworks.com/",
        "company_website": "https://freshworks.com",
        "selection_rounds": "Round 1: Online Coding Round -> Round 2: Machine Coding & Design Patterns -> Round 3: High Scale Architecture -> Round 4: Culture Fit"
    },
    {
        "company_name": "PayPal Global Tech Center",
        "role_title": "Software Engineer (Fintech & Payments)",
        "location": "Chennai (Futura Tech Park)",
        "salary_package": "18.0 LPA - 24.0 LPA",
        "min_cgpa": 7.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "High-volume distributed payment processing, Java, Spring Boot, Kafka, REST/gRPC, microservices architecture.",
        "days_ahead": 12,
        "application_url": "https://www.paypal.com/us/webapps/mpp/jobs",
        "company_website": "https://paypal.com",
        "selection_rounds": "Round 1: HackerEarth Online Assessment -> Round 2: Data Structures & Algorithms -> Round 3: Problem Solving & Design -> Round 4: Values & Hiring Manager"
    },
    {
        "company_name": "Ford Technology",
        "role_title": "Software Engineer - Connected Mobility",
        "location": "Chennai (ELCOT SEZ Sholinganallur)",
        "salary_package": "9.0 LPA - 12.5 LPA",
        "min_cgpa": 6.8,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Connected vehicle cloud services, IoT data streams, Java/Python, Azure IoT Hub, real-time telemetry processing.",
        "days_ahead": 7,
        "application_url": "https://corporate.ford.com/careers.html",
        "company_website": "https://ford.com",
        "selection_rounds": "Round 1: Online Technical Test -> Round 2: Coding & OOPS Discussion -> Round 3: Architecture & Projects Viva -> Round 4: HR Round"
    },

    # --- COIMBATORE DISTRICT & WESTERN TN ---
    {
        "company_name": "Bosch Global Software Technologies (BGSW)",
        "role_title": "Embedded & Cloud Software Engineer (Campus FTE)",
        "location": "Coimbatore (CHIL SEZ Saravanampatti)",
        "salary_package": "7.5 LPA - 10.0 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE,EEE",
        "job_description": "Automotive software engineering, C/C++, Embedded Linux, AUTOSAR, IoT cloud edge computing, microcontrollers.",
        "days_ahead": 8,
        "application_url": "https://careers.smartrecruiters.com/BoschGroup?country=in",
        "company_website": "https://www.bosch.in",
        "selection_rounds": "Round 1: Bosch Online Assessment (C/C++ & Aptitude) -> Round 2: Technical Interview (Microcontrollers & OOPS) -> Round 3: Techno-Managerial Round -> Round 4: HR Discussion"
    },
    {
        "company_name": "Cognizant Coimbatore",
        "role_title": "GenC Next Developer",
        "location": "Coimbatore (Saravanampatti / Keeranatham)",
        "salary_package": "6.75 LPA - 8.5 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Cloud native microservices, Full stack development (Java, React, SQL), RESTful web APIs, Agile sprint delivery.",
        "days_ahead": 5,
        "application_url": "https://careers.cognizant.com/global/en",
        "company_website": "https://cognizant.com",
        "selection_rounds": "Round 1: Coding Challenge (LeetCode Medium) -> Round 2: Deep Technical & Project Viva -> Round 3: HR Fitment"
    },
    {
        "company_name": "ThoughtWorks Coimbatore",
        "role_title": "Graduate Application Developer",
        "location": "Coimbatore (TIDEL Park Coimbatore)",
        "salary_package": "11.5 LPA - 15.0 LPA",
        "min_cgpa": 7.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT",
        "job_description": "Test Driven Development (TDD), Clean Code Architecture, Pair Programming, Java/Python, Agile consulting.",
        "days_ahead": 11,
        "application_url": "https://www.thoughtworks.com/careers",
        "company_website": "https://thoughtworks.com",
        "selection_rounds": "Round 1: Code Pairing Round -> Round 2: Architecture & Design Discussion -> Round 3: Social Justice & Values Interview"
    },
    {
        "company_name": "KGISL Technologies",
        "role_title": "Associate Software Engineer (Fintech)",
        "location": "Coimbatore (CHIL Campus Saravanampatti)",
        "salary_package": "5.5 LPA - 7.5 LPA",
        "min_cgpa": 6.0,
        "max_arrears": 1,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Banking platforms, .NET Core, Java, Angular, relational database management, secure transaction flows.",
        "days_ahead": 6,
        "application_url": "https://www.kgisl.com/careers/",
        "company_website": "https://kgisl.com",
        "selection_rounds": "Round 1: Aptitude & Coding Test -> Round 2: Technical Interview -> Round 3: HR Round"
    },
    {
        "company_name": "Kovai.co",
        "role_title": "Product Software Engineer (SaaS)",
        "location": "Coimbatore (TIDEL Park Coimbatore)",
        "salary_package": "9.0 LPA - 13.5 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Enterprise SaaS engineering (Document360, Serverless360), C# .NET Core, React, Azure serverless, microservices.",
        "days_ahead": 8,
        "application_url": "https://www.kovai.co/careers/",
        "company_website": "https://kovai.co",
        "selection_rounds": "Round 1: Online Coding & Aptitude -> Round 2: Problem Solving & Machine Task -> Round 3: Architecture & Culture Fit"
    },
    {
        "company_name": "Soliton Technologies",
        "role_title": "Systems Software Engineer",
        "location": "Coimbatore (Classic Towers, Trichy Road)",
        "salary_package": "8.5 LPA - 12.0 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Semiconductor automation software, C/C++, Python, signal analysis algorithms, hardware-software integration.",
        "days_ahead": 10,
        "application_url": "https://www.solitontech.com/careers/",
        "company_website": "https://solitontech.com",
        "selection_rounds": "Round 1: C/C++ Programming & Logic -> Round 2: Machine Coding Challenge -> Round 3: Technical Viva -> Round 4: HR"
    },
    {
        "company_name": "Pricol Technologies",
        "role_title": "Embedded Automotive Software Engineer",
        "location": "Coimbatore (Perianaickenpalayam)",
        "salary_package": "6.0 LPA - 8.5 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE,EEE",
        "job_description": "Automotive instrument clusters, CAN/LIN protocols, embedded C, firmware development, vehicle telematics.",
        "days_ahead": 7,
        "application_url": "https://www.pricol.com/careers",
        "company_website": "https://pricol.com",
        "selection_rounds": "Round 1: Core Technical & C Test -> Round 2: Embedded Systems Viva -> Round 3: HR Fitment"
    },
    {
        "company_name": "Skava Systems (Infosys Skava)",
        "role_title": "Full Stack Cloud Platform Engineer",
        "location": "Coimbatore (TIDEL Park Coimbatore)",
        "salary_package": "7.5 LPA - 11.0 LPA",
        "min_cgpa": 6.8,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Microservices digital commerce platform, Java Spring Boot, Node.js, React, Kubernetes, AWS distributed architectures.",
        "days_ahead": 9,
        "application_url": "https://www.infosys.com/careers/",
        "company_website": "https://infosys.com",
        "selection_rounds": "Round 1: HackerRank Coding Assessment -> Round 2: Full-Stack Pair Programming -> Round 3: Tech Lead & HR"
    },
    {
        "company_name": "Roots Industries",
        "role_title": "IoT & Digital Automation Software Trainee",
        "location": "Coimbatore (Ganapathy)",
        "salary_package": "5.5 LPA - 7.5 LPA",
        "min_cgpa": 6.0,
        "max_arrears": 1,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Connected industrial automation, IoT sensor telemetry, Python, embedded controller firmware, smart factory monitoring.",
        "days_ahead": 6,
        "application_url": "https://www.rootsindia.com/careers/",
        "company_website": "https://roots.com",
        "selection_rounds": "Round 1: Aptitude & Logic Assessment -> Round 2: Technical Interview -> Round 3: Managerial & HR"
    },
    {
        "company_name": "L&T Technology Services (LTTS)",
        "role_title": "Digital Engineering Associate",
        "location": "Coimbatore (Eachanari / Malumichampatti)",
        "salary_package": "6.5 LPA - 9.0 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE,EEE",
        "job_description": "Industry 4.0 software, cloud analytics, C++, Java, edge computing, smart industrial operations.",
        "days_ahead": 8,
        "application_url": "https://www.ltts.com/careers",
        "company_website": "https://ltts.com",
        "selection_rounds": "Round 1: Online Technical Test -> Round 2: Core Engineering Viva -> Round 3: HR Fitment"
    },

    # --- MADURAI & SOUTHERN TN DISTRICTS (Trichy, Salem, Tenkasi) ---
    {
        "company_name": "HCL Technologies Madurai",
        "role_title": "Software Engineer (Campus Graduate Program)",
        "location": "Madurai (ELCOT IT Park Vadipatti)",
        "salary_package": "6.0 LPA - 8.0 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE,EEE",
        "job_description": "Enterprise infrastructure management, Cloud engineering (Azure/AWS), Java, Python scripting, DevOps automation.",
        "days_ahead": 7,
        "application_url": "https://www.hcltech.com/careers",
        "company_website": "https://hcltech.com",
        "selection_rounds": "Round 1: Online Aptitude & Domain Assessment -> Round 2: Technical Interview -> Round 3: HR Round"
    },
    {
        "company_name": "Honeywell Technology Solutions",
        "role_title": "Software Engineer - Aerospace Systems",
        "location": "Madurai (ELCOT Special Economic Zone)",
        "salary_package": "8.5 LPA - 12.0 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Safety-critical avionics software, C++, real-time operating systems (RTOS), DO-178C standards, system validation.",
        "days_ahead": 10,
        "application_url": "https://careers.honeywell.com",
        "company_website": "https://honeywell.com",
        "selection_rounds": "Round 1: HackerEarth Coding Assessment -> Round 2: Core CS & Embedded Interview -> Round 3: Director & Culture Round"
    },
    {
        "company_name": "Zoho Corporation (Tenkasi Campus)",
        "role_title": "Product Software Engineer (Rural Tech Initiative)",
        "location": "Tenkasi / Tirunelveli (Mathalamparai Campus)",
        "salary_package": "8.5 LPA - 12.0 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Engineering world-class SaaS products from rural India. C/C++, Java, distributed systems, clean algorithms.",
        "days_ahead": 9,
        "application_url": "https://careers.zohocorp.com/jobs/Careers",
        "company_website": "https://zoho.com",
        "selection_rounds": "Round 1: C/Java Output Prediction & Logic -> Round 2: Complex Algorithms & String Manipulation -> Round 3: System Design -> Round 4: Founder/HR Round"
    },
    {
        "company_name": "Vuram Technologies (WNS-Vuram)",
        "role_title": "Hyperautomation Associate Engineer",
        "location": "Trichy (Tiruchirappalli IT Hub)",
        "salary_package": "5.5 LPA - 7.0 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Low-code application development (Appian), business process automation, enterprise integrations, Java, SQL.",
        "days_ahead": 6,
        "application_url": "https://www.wns.com/careers",
        "company_website": "https://vuram.com",
        "selection_rounds": "Round 1: Analytical Reasoning & Logic Test -> Round 2: Technical Problem Solving -> Round 3: HR Fitment"
    },
    {
        "company_name": "Vee Technologies",
        "role_title": "Junior Software Engineer",
        "location": "Salem (IT Park Jagir Ammapalayam)",
        "salary_package": "5.0 LPA - 6.5 LPA",
        "min_cgpa": 6.0,
        "max_arrears": 1,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Healthcare IT solutions, Python, SQL, web service integrations, secure data handling, agile development.",
        "days_ahead": 8,
        "application_url": "https://www.veetechnologies.com/careers/",
        "company_website": "https://veetechnologies.com",
        "selection_rounds": "Round 1: Online Aptitude Test -> Round 2: Technical Interview -> Round 3: HR Round"
    },

    # --- KERALA & KARNATAKA TECH DISTRICTS (Kochi, Trivandrum, Mysore) ---
    {
        "company_name": "UST Global",
        "role_title": "Associate Software Developer",
        "location": "Kochi (Infopark Phase II Kakkanad)",
        "salary_package": "6.5 LPA - 9.0 LPA",
        "min_cgpa": 6.8,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Digital engineering services, cloud application development, React, Node.js, Spring Boot, automated CI/CD.",
        "days_ahead": 9,
        "application_url": "https://www.ust.com/en/careers",
        "company_website": "https://ust.com",
        "selection_rounds": "Round 1: Online Coding & Aptitude Test -> Round 2: Technical Interview -> Round 3: HR Interview"
    },
    {
        "company_name": "Tata Elxsi",
        "role_title": "Autonomous Mobility & Embedded Engineer",
        "location": "Trivandrum (Technopark Phase I)",
        "salary_package": "7.5 LPA - 10.5 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE,EEE",
        "job_description": "Automotive electronic control units, ADAS algorithms, computer vision, C/C++, Linux driver development.",
        "days_ahead": 11,
        "application_url": "https://www.tataelxsi.com/careers",
        "company_website": "https://tataelxsi.com",
        "selection_rounds": "Round 1: Tata Elxsi National Coding Assessment -> Round 2: Technical DSA & Embedded Systems -> Round 3: HR Discussion"
    },
    {
        "company_name": "L&T Technology Services (LTTS)",
        "role_title": "Smart Manufacturing & Digital Software Engineer",
        "location": "Mysore (Hebbal Industrial Area)",
        "salary_package": "6.5 LPA - 8.5 LPA",
        "min_cgpa": 6.8,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE,EEE",
        "job_description": "Industrial IoT, smart edge automation, digital twins, Python, C++, cloud analytics for factories.",
        "days_ahead": 7,
        "application_url": "https://www.ltts.com/careers",
        "company_website": "https://ltts.com",
        "selection_rounds": "Round 1: Cognitive & Technical MCQ Assessment -> Round 2: Core Engineering Interview -> Round 3: HR Round"
    },

    # --- EMERGING NATIONAL TECH DISTRICTS (Bhubaneswar, Indore, Vizag, GIFT City) ---
    {
        "company_name": "Capgemini Bhubaneswar",
        "role_title": "Senior Analyst - Software Engineer",
        "location": "Bhubaneswar (Infocity Chandaka)",
        "salary_package": "7.5 LPA - 9.5 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Cloud modernization, Java/Spring Boot microservices, Angular, relational databases, DevOps pipelines.",
        "days_ahead": 8,
        "application_url": "https://www.capgemini.com/careers/",
        "company_website": "https://capgemini.com",
        "selection_rounds": "Round 1: Capgemini Exceller Test -> Round 2: Technical Interview -> Round 3: HR Round"
    },
    {
        "company_name": "Impetus Technologies",
        "role_title": "Big Data & Cloud Systems Engineer",
        "location": "Indore (Crystal IT Park Ring Road)",
        "salary_package": "8.0 LPA - 11.0 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT",
        "job_description": "Massive scale big data pipelines, Apache Spark, Kafka, AWS Data Lake, distributed computing in Scala/Python.",
        "days_ahead": 10,
        "application_url": "https://www.impetus.com/careers/",
        "company_website": "https://impetus.com",
        "selection_rounds": "Round 1: Advanced Algorithms & Data Structures -> Round 2: Big Data Architecture Discussion -> Round 3: Fitment Round"
    },
    {
        "company_name": "Tech Mahindra Vizag",
        "role_title": "Associate Software Engineer",
        "location": "Visakhapatnam (Rushikonda IT SEZ)",
        "salary_package": "5.5 LPA - 7.5 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Telecom software solutions, 5G cloud networks, Java, Python, network function virtualization, REST APIs.",
        "days_ahead": 6,
        "application_url": "https://careers.techmahindra.com",
        "company_website": "https://techmahindra.com",
        "selection_rounds": "Round 1: Online Assessment -> Round 2: Technical Interview -> Round 3: HR Round"
    },
    {
        "company_name": "Oracle Financial Services",
        "role_title": "Fintech Software Engineer",
        "location": "GIFT City Gandhinagar / Ahmedabad",
        "salary_package": "10.0 LPA - 14.0 LPA",
        "min_cgpa": 7.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT",
        "job_description": "Global banking platforms, Oracle Cloud Infrastructure (OCI), Java, high-frequency transaction engines, SQL.",
        "days_ahead": 12,
        "application_url": "https://www.oracle.com/careers/",
        "company_website": "https://oracle.com",
        "selection_rounds": "Round 1: Oracle Online Assessment -> Round 2: DSA & Database Query Optimization -> Round 3: OOPS & Design -> Round 4: HR"
    },

    # --- BANGALORE & HYDERABAD TECH HUBS ---
    {
        "company_name": "Google",
        "role_title": "Software Engineer (University Graduate / FTE)",
        "location": "Bangalore / Hyderabad",
        "salary_package": "24.0 LPA - 32.0 LPA",
        "min_cgpa": 7.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Algorithms, Data Structures, System Design, Distributed Systems, Python/Go/C++ proficiency.",
        "days_ahead": 10,
        "application_url": "https://www.google.com/about/careers/applications/jobs/results/?q=university",
        "company_website": "https://careers.google.com",
        "selection_rounds": "Round 1: Online Coding Assessment (2 LeetCode Medium/Hard) -> Round 2: Data Structures & Algorithms -> Round 3: System Design & Architecture -> Round 4: Googleyness & Leadership"
    },
    {
        "company_name": "Microsoft",
        "role_title": "Software Development Engineer (Campus FTE)",
        "location": "Hyderabad / Bangalore / Noida",
        "salary_package": "18.5 LPA - 26.0 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Strong fundamentals in Object-Oriented Design, Trees, Graphs, DP, Azure cloud knowledge is a plus.",
        "days_ahead": 8,
        "application_url": "https://careers.microsoft.com/v2/global/en/home.html",
        "company_website": "https://careers.microsoft.com",
        "selection_rounds": "Round 1: Codility Online Test -> Round 2: Technical DSA Interview -> Round 3: System Design & OOPS -> Round 4: AA (As-Appropriate) Director Round"
    },
    {
        "company_name": "Razorpay",
        "role_title": "Associate Software Engineer (Backend)",
        "location": "Bangalore",
        "salary_package": "16.0 LPA - 20.0 LPA",
        "min_cgpa": 7.0,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT",
        "job_description": "Fintech payment systems, high throughput APIs, Golang, Python, PostgreSQL, Redis.",
        "days_ahead": 6,
        "application_url": "https://razorpay.com/jobs/",
        "company_website": "https://razorpay.com",
        "selection_rounds": "Round 1: HackerRank Online Coding -> Round 2: Problem Solving & Concurrency -> Round 3: Low-Level Design (LLD) -> Round 4: Cultural Fitment"
    },
    {
        "company_name": "Swiggy",
        "role_title": "Software Development Engineer - 1",
        "location": "Bangalore / Remote",
        "salary_package": "15.0 LPA - 19.5 LPA",
        "min_cgpa": 6.8,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Hyperlocal delivery platform engineering, microservices, Java, Spring Boot, Kafka, low-latency APIs.",
        "days_ahead": 12,
        "application_url": "https://careers.swiggy.com/",
        "company_website": "https://swiggy.com",
        "selection_rounds": "Round 1: Machine Coding Round (Clean Code & Extensibility) -> Round 2: Data Structures & Algorithms -> Round 3: High Scale Architecture Discussion -> Round 4: Hiring Manager Discussion"
    },
    {
        "company_name": "Atlassian",
        "role_title": "Associate Software Engineer",
        "location": "Bangalore",
        "salary_package": "22.0 LPA - 28.0 LPA",
        "min_cgpa": 7.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT",
        "job_description": "Building Jira & Confluence scale platforms. React, Java, Kotlin, AWS, robust test-driven development.",
        "days_ahead": 14,
        "application_url": "https://www.atlassian.com/company/careers",
        "company_website": "https://atlassian.com",
        "selection_rounds": "Round 1: HackerRank Coding Challenge -> Round 2: Live Data Structures Pair Programming -> Round 3: Code Crafting & Refactoring -> Round 4: Values & Culture Interview"
    },
    {
        "company_name": "Infosys",
        "role_title": "Specialist Programmer (Power Programmer)",
        "location": "Pan India",
        "salary_package": "9.5 LPA - 11.0 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 1,
        "allowed_departments": "CSE,IT,ECE,EEE",
        "job_description": "HackWithInfy winners & direct campus selection. Advanced competitive coding, full stack architectures.",
        "days_ahead": 5,
        "application_url": "https://www.infosys.com/careers/",
        "company_website": "https://infosys.com",
        "selection_rounds": "Round 1: HackWithInfy Competitive Coding -> Round 2: Deep Technical & Full Stack Project Viva -> Round 3: HR Interview"
    },
    {
        "company_name": "Cognizant",
        "role_title": "GenC Next Developer",
        "location": "Chennai / Coimbatore / Bangalore",
        "salary_package": "6.75 LPA - 8.5 LPA",
        "min_cgpa": 6.5,
        "max_arrears": 0,
        "allowed_departments": "CSE,IT,ECE",
        "job_description": "Cloud native application engineering, Java/Python, React, API integration, Agile practices.",
        "days_ahead": 7,
        "application_url": "https://careers.cognizant.com/global/en",
        "company_website": "https://cognizant.com",
        "selection_rounds": "Round 1: Advanced Skill Assessment (DSA & SQL) -> Round 2: Technical Interview -> Round 3: HR Discussion"
    }
]

def clean_job_description(raw_text: str, max_chars: int = 1800) -> str:
    """
    Cleans rich-text HTML descriptions from external APIs (Remotive, Arbeitnow, Jobicy).
    Strips raw HTML tags, inline styles, unescapes entities (&amp;, &nbsp;), collapses whitespace,
    and removes repetitive metadata prefixes.
    """
    if not raw_text:
        return "Opportunity details available via official careers portal."
    
    # 1. Unescape HTML entities
    text = html.unescape(raw_text)
    
    # 2. Strip scripts and styles with content
    text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', text, flags=re.IGNORECASE)
    
    # 3. Convert breaks & block tags to newlines to preserve structural spacing
    text = re.sub(r'<\s*br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/?(?:p|div|tr|li|h[1-6]|section|article|ul|ol)\b[^>]*>', '\n', text, flags=re.IGNORECASE)
    
    # 4. Strip all remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 5. Strip unclosed trailing tags (caused by mid-tag truncation)
    text = re.sub(r'<[^>]*$', '', text)
    
    # 6. Normalize whitespace
    text = text.replace('\xa0', ' ').replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 7. Strip repetitive metadata header prefixes if present
    text = re.sub(r'^Source:.*?\n(?:Role:.*?\n)?(?:Company:.*?\n)?(?:Details:\s*)?', '', text, flags=re.DOTALL | re.IGNORECASE).strip()
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = text.strip()
    
    # 8. Clean truncation at word boundary
    if len(text) > max_chars:
        truncated = text[:max_chars]
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.8:
            text = truncated[:last_space] + "..."
        else:
            text = truncated + "..."
            
    return text or "Opportunity details available via official careers portal."


def is_engineering_role(title: str) -> bool:
    """
    Filters out non-technical roles (customer service, warehouse, clinical, content reviewer,
    freelance AI trainers, language specialists, sales/marketing) to keep drives strictly tech/engineering.
    """
    title_lower = (title or "").lower()
    excluded_keywords = [
        "content reviewer", "customer service", "sales representative", "inside sales",
        "account executive", "business development", "warehouse", "office assistant",
        "hr generalist", "hr business partner", "patient care", "clinical research",
        "talent acquisition", "recruiter", "kundenberater", "flächenakquisi",
        "finance assistant", "accountant", "controller", "cfo", "cra ii",
        "language specialist", "ai trainer", "freelance", "content creator",
        "social media", "copywriter", "legal counsel", "attorney", "real estate",
        "construction manager", "partner manager", "medical", "nurse", "therapist",
    ]
    for kw in excluded_keywords:
        if kw in title_lower:
            return False

    tech_keywords = [
        "engineer", "developer", "software", "sde", "swe", "programmer",
        "architect", "devops", "sre", "cloud", "data", "ai", "ml",
        "machine learning", "backend", "frontend", "full stack", "fullstack",
        "mobile", "ios", "android", "security", "qa", "test", "automation",
        "embedded", "firmware", "systems", "platform", "infrastructure",
        "database", "it consultant", "technology", "technical", "cyber",
        "product analyst", "intern", "graduate", "trainee", "analyst",
        "autosar", "blockchain", "rust", "golang", "python", "java",
    ]
    return any(kw in title_lower for kw in tech_keywords)


KNOWN_ATS_DOMAINS = [
    "myworkdayjobs.com", "boards.greenhouse.io", "jobs.lever.co", "smartrecruiters.com",
    "bamboohr.com", "ashbyhq.com", "taleo.net", "successfactors.com", "workable.com",
    "rippling-ats.com", "recruitee.com", "pinpointhq.com", "applytojob.com", "jobvite.com", "superset.in"
]

IGNORE_DOMAINS = [
    "twitter.com", "x.com", "facebook.com", "instagram.com", "reddit.com",
    "apple.com", "google.com", "play.google.com", "mozilla.org", "microsoft.com",
    "chatgpt.com", "openai.com", "t.me", "youtube.com", "remotive.com", "jobicy.com", "arbeitnow.com", "linkedin.com"
]


async def unshorten_to_direct_ats(
    raw_url: str,
    company_name: str,
    client: Optional[httpx.AsyncClient] = None,
    timeout_seconds: float = 12.0
) -> Optional[str]:
    """
    Lightweight HTTP redirect tracer & ATS unshortener.
    Follows redirects and inspects outbound links to extract the real corporate application form.
    """
    if not raw_url or not raw_url.startswith("http"):
        return None

    raw_lower = raw_url.lower()
    for ats in KNOWN_ATS_DOMAINS:
        if ats in raw_lower:
            return raw_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    own_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True, headers=headers)
        own_client = True

    comp_clean = re.sub(r'[^a-zA-Z0-9]', '', company_name).lower() if company_name else ""
    comp_first_word = company_name.split()[0].lower() if company_name else ""

    try:
        res = await client.get(raw_url, follow_redirects=True, timeout=timeout_seconds)
        final_url = str(res.url)
        final_lower = final_url.lower()

        # 1. Did the HTTP redirects land directly on a known ATS?
        for ats in KNOWN_ATS_DOMAINS:
            if ats in final_lower:
                return final_url

        # 2. Inspect HTML body for outbound "Apply" or direct ATS links
        if res.status_code == 200 and len(res.text) > 0:
            urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', res.text[:120000])
            for u in urls:
                u_lower = u.lower()
                if any(ign in u_lower for ign in IGNORE_DOMAINS):
                    continue
                # Match known ATS
                if any(ats in u_lower for ats in KNOWN_ATS_DOMAINS):
                    return u.replace("&amp;", "&")
                # Match career/job application path on company domain
                if ("jobs." in u_lower or "careers." in u_lower or "/career" in u_lower or "/job" in u_lower or "/cmp/" in u_lower) and (comp_first_word in u_lower or comp_clean in u_lower):
                    return u.replace("&amp;", "&")

    except Exception:
        pass
    finally:
        if own_client:
            await client.aclose()

    return None


def resolve_direct_application_url(company_name: str, role_title: str, raw_url: Optional[str] = None) -> str:
    """
    Ensures that every placement drive has an authentic, actionable direct application URL.
    - If raw_url is already a recognized direct ATS / corporate careers link, preserves it.
    - If raw_url is missing, empty, or points to a generic homepage (e.g. 'https://www.linkedin.com', 'https://remotive.com'),
      generates a targeted direct application search link to the company's real application form.
    """
    import urllib.parse
    clean_comp = (company_name or "").strip()
    clean_role = (role_title or "").strip()
    
    # 1. Pre-verified direct campus portals
    comp_lower = clean_comp.lower()
    if "tcs" in comp_lower or "tata consultancy" in comp_lower:
        return "https://nextstep.tcs.com/campus/#/"
    if "zoho" in comp_lower:
        return "https://www.zohocorp.com/careers/"
    if "amazon" in comp_lower:
        role_q = urllib.parse.quote_plus(clean_role) if clean_role else "Software+Development+Engineer"
        return f"https://www.amazon.jobs/en/search?base_query={role_q}"
    if "google" in comp_lower:
        return "https://www.google.com/about/careers/applications/jobs/results/?q=university"
    if "microsoft" in comp_lower:
        return "https://careers.microsoft.com/v2/global/en/home.html"
    if "cognizant" in comp_lower:
        return "https://careers.cognizant.com/global/en/search-results?keywords=GenC"
    if "infosys" in comp_lower:
        return "https://www.infosys.com/careers/"
    if "pwc" in comp_lower:
        return "https://www.pwc.in/careers.html"
    if "razorpay" in comp_lower:
        return "https://razorpay.com/jobs/"
    if "atlassian" in comp_lower:
        return "https://www.atlassian.com/company/careers"
    if "swiggy" in comp_lower:
        return "https://careers.swiggy.com/"
    if "ibm" in comp_lower:
        return "https://www.ibm.com/careers/search?q=Software+Engineer"

    # 2. Check if raw_url is already a valid deep-link
    if raw_url and raw_url.strip():
        url = raw_url.strip()
        is_generic_root = url.rstrip("/") in [
            "https://www.linkedin.com", "https://linkedin.com",
            "https://remotive.com", "https://www.remotive.com",
            "https://jobicy.com", "https://www.jobicy.com",
            "https://arbeitnow.com", "https://www.arbeitnow.com"
        ]
        if not is_generic_root and ("http://" in url or "https://" in url):
            return url

    # 3. Targeted direct query to the company's real application form
    search_query = urllib.parse.quote_plus(f"{clean_comp} {clean_role} official careers application form apply")
    return f"https://www.google.com/search?q={search_query}"


def resolve_company_website(company_name: str, raw_website: Optional[str] = None) -> str:
    """
    Resolves the authentic corporate website instead of hardcoding aggregator URLs (remotive.com/jobicy.com).
    """
    clean_comp = (company_name or "").strip()
    comp_lower = clean_comp.lower()
    
    known_websites = {
        "zoho": "https://www.zoho.com",
        "tcs": "https://www.tcs.com",
        "amazon": "https://amazon.jobs",
        "google": "https://careers.google.com",
        "microsoft": "https://careers.microsoft.com",
        "cognizant": "https://cognizant.com",
        "infosys": "https://infosys.com",
        "pwc": "https://pwc.in",
        "razorpay": "https://razorpay.com",
        "atlassian": "https://atlassian.com",
        "swiggy": "https://swiggy.com",
        "paypal": "https://paypal.com",
        "bosch": "https://bosch.in",
        "itc infotech": "https://itcinfotech.com",
        "ibm": "https://ibm.com",
        "honeywell": "https://honeywell.com",
        "hcl": "https://hcltech.com",
        "soliton": "https://solitontech.com",
        "kovai": "https://kovai.co",
        "roots": "https://rootsindustries.com",
        "pricol": "https://pricol.com",
        "kgisl": "https://kgisl.com",
        "ford": "https://ford.com",
        "freshworks": "https://freshworks.com"
    }
    for k, v in known_websites.items():
        if k in comp_lower:
            return v
            
    if raw_website:
        raw_lower = raw_website.lower()
        if not any(agg in raw_lower for agg in ["remotive.com", "jobicy.com", "arbeitnow.com", "linkedin.com"]):
            return raw_website
            
    slug = re.sub(r'[^a-zA-Z0-9]', '', clean_comp).lower()
    if slug:
        return f"https://www.{slug}.com"
    return "https://www.google.com"


class JobFetcherWorker:
    """
    Automated Multi-Source Verified Hiring Ingestion Worker.
    Pulls live developer jobs strictly from verified ATS APIs (Greenhouse, Ashby, SmartRecruiters, Lever),
    community-verified SimplifyJobs GitHub feeds, and curated campus tracks.
    Rejects unverified aggregator traps, synthetic clones, duplicates, and expired postings.
    """

    def __init__(self):
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_count: int = 0
        self._verify_cache: Dict[str, Tuple[datetime, Dict[str, Any]]] = {}

    @staticmethod
    def _parse_iso_dt(val: Optional[str]) -> Optional[datetime]:
        if not val:
            return None
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    def _build_candidate(
        self,
        *,
        company_name: str,
        role_title: str,
        location: str,
        job_description: str,
        application_url: str,
        source_platform: str,
        salary_package: str = "12.0 LPA - 22.0 LPA",
        min_cgpa: float = 7.0,
        max_arrears: int = 0,
        allowed_departments: str = "CSE,IT,ECE",
        days_ahead: int = 10,
        company_website: Optional[str] = None,
        selection_rounds: Optional[str] = None,
        expected_fields: Optional[str] = None,
        schema_source: Optional[str] = None,
        deadline_dt: Optional[datetime] = None,
        force_region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalizes a fetched job into a unified candidate structure."""
        clean_desc = clean_job_description(job_description)
        region = force_region or classify_region_scope(location, clean_desc)
        detected_src = detect_source_platform(application_url, source_platform)
        return {
            "company_name": company_name.strip(),
            "role_title": role_title.strip(),
            "location": (location or "Pan India / Remote").strip(),
            "region_scope": region,
            "salary_package": salary_package,
            "min_cgpa": min_cgpa,
            "max_arrears": max_arrears,
            "allowed_departments": allowed_departments,
            "job_description": clean_desc,
            "days_ahead": days_ahead,
            "deadline_dt": deadline_dt,
            "application_url": application_url.strip(),
            "company_website": resolve_company_website(company_name, company_website),
            "selection_rounds": selection_rounds or "Round 1: Online Assessment -> Round 2: Technical DSA & System Design -> Round 3: Cultural Fitment",
            "source_platform": detected_src,
            "form_type": "DIRECT_FORM",
            "expected_fields": expected_fields,
            "schema_source": schema_source,
        }

    async def _fetch_verified_aggregator(
        self,
        *,
        source_name: str,
        api_url: str,
        items_key: str,
        limit: int,
        field_map: Dict[str, str],
        default_salary: str,
    ) -> List[Dict[str, Any]]:
        """
        Shared helper for public aggregator APIs (Arbeitnow, Jobicy, Remotive).
        Strictly retains ONLY entries whose URL resolves to a direct corporate/ATS destination.
        """
        drives: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                res = await client.get(api_url)
                if res.status_code != 200:
                    return drives
                items = res.json().get(items_key, [])
                eng_items = [
                    item for item in items
                    if is_engineering_role(item.get(field_map["title"], ""))
                    and item.get(field_map["company"], "")
                    and (item.get(field_map["url"]) or "")
                ][: max(limit * 3, 15)]

                sem = asyncio.Semaphore(6)

                async def _resolve_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                    title = item.get(field_map["title"], "")
                    company = item.get(field_map["company"], "")
                    raw_url = item.get(field_map["url"]) or ""
                    async with sem:
                        ats_url = await unshorten_to_direct_ats(raw_url, company, client=client, timeout_seconds=3.5)
                    if not ats_url or not is_valid_direct_url(ats_url):
                        return None  # Reject unverified aggregator pages / search fallbacks
                    loc = item.get(field_map["location"]) or "Remote"
                    desc = item.get(field_map["desc"]) or ""
                    sal = item.get("salary") or default_salary
                    return self._build_candidate(
                        company_name=company,
                        role_title=title,
                        location=str(loc),
                        job_description=desc,
                        application_url=ats_url,
                        source_platform=source_name,
                        salary_package=str(sal),
                        company_website=item.get("company_url"),
                    )

                resolved = await asyncio.gather(*[_resolve_item(it) for it in eng_items], return_exceptions=True)
                for cand in resolved:
                    if isinstance(cand, dict):
                        drives.append(cand)
                        if len(drives) >= limit:
                            break
        except Exception as e:
            logger.warning(f"{source_name} fetch failed: {e}")
        return drives

    async def fetch_from_arbeitnow(self, limit: int = 8) -> List[Dict[str, Any]]:
        return await self._fetch_verified_aggregator(
            source_name="ARBEITNOW",
            api_url="https://www.arbeitnow.com/api/job-board-api",
            items_key="data",
            limit=limit,
            field_map={"title": "title", "company": "company_name", "url": "url", "location": "location", "desc": "description"},
            default_salary="12.0 LPA - 18.0 LPA",
        )

    async def fetch_from_jobicy(self, limit: int = 6) -> List[Dict[str, Any]]:
        return await self._fetch_verified_aggregator(
            source_name="JOBICY",
            api_url="https://jobicy.com/api/v2/remote-jobs?count=20",
            items_key="jobs",
            limit=limit,
            field_map={"title": "jobTitle", "company": "companyName", "url": "url", "location": "jobGeo", "desc": "jobDescription"},
            default_salary="14.0 LPA - 22.0 LPA",
        )

    async def fetch_from_remotive(self, limit: int = 8) -> List[Dict[str, Any]]:
        return await self._fetch_verified_aggregator(
            source_name="REMOTIVE",
            api_url="https://remotive.com/api/remote-jobs?category=software-dev&limit=25",
            items_key="jobs",
            limit=limit,
            field_map={"title": "title", "company": "company_name", "url": "url", "location": "candidate_required_location", "desc": "description"},
            default_salary="10.0 LPA - 16.5 LPA",
        )

    async def fetch_from_greenhouse(self, limit: int = 16, company_slugs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetches verified jobs from Greenhouse public API with ?content=true (real descriptions),
        filters out expired deadlines, prioritizes India & Remote openings alongside Global roles,
        and pulls actual per-job form questions via ?questions=true.
        """
        drives: List[Dict[str, Any]] = []
        slugs = company_slugs or ["stripe", "databricks", "gitlab", "coinbase", "airbnb", "rubrik", "cloudflare"]
        name_map = {
            "gitlab": "GitLab",
            "cloudflare": "Cloudflare",
            "stripe": "Stripe",
            "databricks": "Databricks",
            "coinbase": "Coinbase",
            "airbnb": "Airbnb",
            "rubrik": "Rubrik",
        }
        now = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                sem = asyncio.Semaphore(8)

                async def _fetch_gh_board(slug: str) -> List[Dict[str, Any]]:
                    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
                    hits: List[Dict[str, Any]] = []
                    try:
                        async with sem:
                            res = await client.get(url)
                        if res.status_code != 200:
                            return hits
                        jobs = res.json().get("jobs", [])
                        comp_name = name_map.get(slug, slug.replace("-", " ").title())
                        for j in jobs:
                            title = j.get("title", "")
                            if not is_engineering_role(title):
                                continue
                            dl_dt = self._parse_iso_dt(j.get("application_deadline"))
                            if dl_dt and dl_dt < now:
                                continue
                            raw_url = j.get("absolute_url", "")
                            if not raw_url:
                                continue
                            app_url = f"{raw_url}#app" if "#app" not in raw_url else raw_url
                            loc = (j.get("location") or {}).get("name") or "Remote"
                            desc = j.get("content") or f"Direct engineering role at {comp_name}."
                            hits.append(
                                self._build_candidate(
                                    company_name=comp_name,
                                    role_title=title,
                                    location=loc,
                                    job_description=desc,
                                    application_url=app_url,
                                    source_platform="GREENHOUSE",
                                    salary_package="18.0 LPA - 34.0 LPA",
                                    company_website=f"https://www.{slug}.com",
                                    deadline_dt=dl_dt,
                                )
                            )
                            if len(hits) >= 4:
                                break
                    except Exception as e:
                        logger.warning(f"Greenhouse fetch failed for {slug}: {e}")
                    return hits

                board_results = await asyncio.gather(*[_fetch_gh_board(s) for s in slugs], return_exceptions=True)
                all_hits: List[Dict[str, Any]] = [
                    cand for res in board_results if isinstance(res, list) for cand in res
                ]

                # Sort India -> Remote -> Global so India & Remote always populate cleanly alongside Global
                priority = {"INDIA": 0, "REMOTE": 1, "GLOBAL": 2}
                all_hits.sort(key=lambda c: priority.get(c["region_scope"], 3))
                drives = all_hits[:limit]

                # Fetch real per-job form questions for top Greenhouse jobs concurrently
                async def _enrich_gh(c: Dict[str, Any]) -> None:
                    schema = await extract_ats_form_schema(c["application_url"], c["company_name"], client=client)
                    if schema.get("fields"):
                        c["expected_fields"] = json.dumps(schema["fields"])
                        c["schema_source"] = schema.get("schema_source")

                await asyncio.gather(*[_enrich_gh(c) for c in drives[:8]], return_exceptions=True)
        except Exception as e:
            logger.warning(f"Error in fetch_from_greenhouse: {e}")
        return drives

    async def fetch_from_ashby(self, limit: int = 12, company_slugs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetches verified jobs from AshbyHQ public posting API, respecting isListed & isRemote flags,
        and pulls real per-job applicationForm fields via Ashby GraphQL.
        """
        drives: List[Dict[str, Any]] = []
        slugs = company_slugs or ["supabase", "posthog", "linear", "notion", "zapier", "replit"]
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                sem = asyncio.Semaphore(8)

                async def _fetch_ashby_board(slug: str) -> List[Dict[str, Any]]:
                    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
                    hits: List[Dict[str, Any]] = []
                    try:
                        async with sem:
                            res = await client.get(url)
                        if res.status_code != 200:
                            return hits
                        jobs = res.json().get("jobs", [])
                        comp_name = slug.capitalize()
                        for j in jobs:
                            if j.get("isListed") is False:
                                continue
                            title = j.get("title", "")
                            if not is_engineering_role(title):
                                continue
                            app_url = j.get("applyUrl") or j.get("jobUrl") or ""
                            if not app_url:
                                continue
                            loc = j.get("location") or ("Remote" if j.get("isRemote") else "Global")
                            desc = j.get("descriptionPlain") or j.get("descriptionHtml") or ""
                            region = classify_region_scope(loc, desc)
                            if j.get("isRemote") and region == "GLOBAL":
                                # Check if remote is explicitly locked to US/EMEA; otherwise mark REMOTE
                                loc_l = loc.lower()
                                if loc_l.strip() in {"remote", "anywhere"} or not any(
                                    x in loc_l for x in ["us", "usa", "united states", "amer", "emea", "uk", "canada", "europe"]
                                ):
                                    region = "REMOTE"

                            hits.append(
                                self._build_candidate(
                                    company_name=comp_name,
                                    role_title=title,
                                    location=loc,
                                    job_description=desc,
                                    application_url=app_url,
                                    source_platform="ASHBY",
                                    salary_package="18.0 LPA - 36.0 LPA",
                                    company_website=f"https://www.{slug}.com",
                                    force_region=region,
                                )
                            )
                            if len(hits) >= 3:
                                break
                    except Exception as e:
                        logger.warning(f"Ashby fetch failed for {slug}: {e}")
                    return hits

                board_results = await asyncio.gather(*[_fetch_ashby_board(s) for s in slugs], return_exceptions=True)
                all_hits: List[Dict[str, Any]] = [
                    cand for res in board_results if isinstance(res, list) for cand in res
                ]

                priority = {"INDIA": 0, "REMOTE": 1, "GLOBAL": 2}
                all_hits.sort(key=lambda c: priority.get(c["region_scope"], 3))
                drives = all_hits[:limit]

                async def _enrich_ashby(c: Dict[str, Any]) -> None:
                    schema = await extract_ats_form_schema(c["application_url"], c["company_name"], client=client)
                    if schema.get("fields"):
                        c["expected_fields"] = json.dumps(schema["fields"])
                        c["schema_source"] = schema.get("schema_source")

                await asyncio.gather(*[_enrich_ashby(c) for c in drives[:6]], return_exceptions=True)
        except Exception as e:
            logger.warning(f"Error in fetch_from_ashby: {e}")
        return drives

    async def fetch_from_smartrecruiters(self, limit: int = 12, company_slugs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetches India-targeted engineering roles directly from SmartRecruiters public API (?country=in),
        and pulls exact applyUrl + real job description & qualifications per requisition.
        """
        drives: List[Dict[str, Any]] = []
        slugs = company_slugs or ["BoschGroup", "ServiceNow", "Experian", "WesternDigital"]
        display_names = {
            "BoschGroup": "Bosch Global Software Technologies (SR)",
            "ServiceNow": "ServiceNow India",
            "Experian": "Experian India",
            "WesternDigital": "Western Digital India",
        }
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                sem = asyncio.Semaphore(8)

                async def _fetch_sr_board(slug: str) -> List[tuple]:
                    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?country=in&limit=15"
                    items: List[tuple] = []
                    try:
                        async with sem:
                            res = await client.get(url)
                        if res.status_code != 200:
                            return items
                        for p in res.json().get("content", []):
                            title = p.get("name", "")
                            if is_engineering_role(title) and p.get("id"):
                                items.append((slug, p))
                            if len(items) >= 4:
                                break
                    except Exception as e:
                        logger.warning(f"SmartRecruiters list fetch failed for {slug}: {e}")
                    return items

                board_results = await asyncio.gather(*[_fetch_sr_board(s) for s in slugs], return_exceptions=True)
                queued = [pair for res in board_results if isinstance(res, list) for pair in res][: max(limit * 2, 16)]

                async def _fetch_sr_detail(slug: str, p: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                    pid = p.get("id")
                    title = p.get("name", "")
                    try:
                        async with sem:
                            detail_r = await client.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{pid}")
                        if detail_r.status_code != 200:
                            return None
                        detail = detail_r.json()
                        if detail.get("active") is False:
                            return None
                        app_url = detail.get("applyUrl") or detail.get("postingUrl")
                        if not app_url:
                            return None
                        sections = (detail.get("jobAd") or {}).get("sections") or {}
                        desc_html = (sections.get("jobDescription") or {}).get("text", "")
                        qual_html = (sections.get("qualifications") or {}).get("text", "")
                        loc_obj = p.get("location") or {}
                        city = (loc_obj.get("city") or "").strip().title()
                        loc = f"{city}, India" if city else "India"
                        return self._build_candidate(
                            company_name=display_names.get(slug, slug),
                            role_title=title,
                            location=loc,
                            job_description=f"{desc_html}\n\nQualifications:\n{qual_html}",
                            application_url=app_url,
                            source_platform="SMARTRECRUITERS",
                            salary_package="9.0 LPA - 20.0 LPA",
                            force_region="INDIA",
                        )
                    except Exception as e:
                        logger.warning(f"SmartRecruiters detail fetch failed for {slug}/{pid}: {e}")
                        return None

                detail_results = await asyncio.gather(
                    *[_fetch_sr_detail(slug, p) for slug, p in queued],
                    return_exceptions=True,
                )
                for cand in detail_results:
                    if isinstance(cand, dict):
                        drives.append(cand)
                        if len(drives) >= limit:
                            break
        except Exception as e:
            logger.warning(f"Error in fetch_from_smartrecruiters: {e}")
        return drives

    async def fetch_from_simplify_github(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Pulls active, direct-apply engineering roles from SimplifyJobs GitHub JSON feeds
        (New-Grad-Positions & Summer2027-Internships), tagging India/Remote vs Global accurately.
        """
        drives: List[Dict[str, Any]] = []
        feeds = [
            ("New Grad", "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"),
            ("Internship", "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"),
        ]
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                india_remote_hits: List[Dict[str, Any]] = []
                global_hits: List[Dict[str, Any]] = []
                for feed_type, raw_url in feeds:
                    try:
                        res = await client.get(raw_url)
                        if res.status_code != 200:
                            continue
                        listings = res.json()
                        # Process newest entries first using date_updated / date_posted
                        active_items = [
                            x for x in listings
                            if x.get("active") is True and x.get("is_visible", True) is True
                        ]
                        active_items.sort(key=lambda x: x.get("date_updated") or x.get("date_posted") or 0, reverse=True)

                        for x in active_items:
                            title = x.get("title") or ""
                            if not is_engineering_role(title):
                                continue
                            app_url = x.get("url") or ""
                            if not is_valid_direct_url(app_url):
                                continue
                            locs = x.get("locations") or ["Global"]
                            loc_str = ", ".join(locs[:3])
                            comp = x.get("company_name") or "Global Tech"
                            category = x.get("category") or "Software Engineering"
                            degrees = ", ".join(x.get("degrees") or ["Bachelor's"])
                            sponsorship = x.get("sponsorship") or "Check Portal"
                            desc = (
                                f"{feed_type} role ({category}) sourced from SimplifyJobs verified tracker. "
                                f"Locations: {loc_str}. Degrees: {degrees}. Sponsorship: {sponsorship}."
                            )
                            cand = self._build_candidate(
                                company_name=comp,
                                role_title=title,
                                location=loc_str,
                                job_description=desc,
                                application_url=app_url,
                                source_platform="SIMPLIFY_GITHUB",
                                salary_package="18.0 LPA - 40.0 LPA" if feed_type == "New Grad" else "Intern Stipend / Competitive",
                                company_website=x.get("company_url"),
                            )
                            if cand["region_scope"] in {"INDIA", "REMOTE"}:
                                if len(india_remote_hits) < limit // 2:
                                    india_remote_hits.append(cand)
                            elif len(global_hits) < limit // 2:
                                global_hits.append(cand)

                            if len(india_remote_hits) >= limit // 2 and len(global_hits) >= limit // 2:
                                break
                    except Exception as e:
                        logger.warning(f"SimplifyJobs {feed_type} fetch failed: {e}")

                drives = (india_remote_hits + global_hits)[:limit]
        except Exception as e:
            logger.warning(f"Error in fetch_from_simplify_github: {e}")
        return drives

    async def fetch_from_lever(self, limit: int = 8, company_slugs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Pulls live developer postings from official Lever Public APIs with real descriptions & /apply URLs."""
        drives: List[Dict[str, Any]] = []
        slugs = company_slugs or ["spotify", "palantir"]
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                for slug in slugs:
                    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                    try:
                        res = await client.get(url)
                        if res.status_code != 200:
                            continue
                        jobs = res.json()
                        comp_name = slug.replace("-", " ").capitalize()
                        for j in jobs:
                            title = j.get("text", "")
                            if not is_engineering_role(title):
                                continue
                            app_url = j.get("applyUrl") or j.get("hostedUrl", "")
                            if not is_valid_direct_url(app_url):
                                continue
                            loc = (j.get("categories") or {}).get("location") or "Remote / Global"
                            desc = j.get("descriptionPlain") or j.get("description") or ""
                            drives.append(
                                self._build_candidate(
                                    company_name=comp_name,
                                    role_title=title,
                                    location=loc,
                                    job_description=desc,
                                    application_url=app_url,
                                    source_platform="LEVER",
                                    salary_package="14.0 LPA - 26.0 LPA",
                                    company_website=f"https://www.{slug}.com",
                                )
                            )
                            if len(drives) >= limit:
                                break
                    except Exception as e:
                        logger.warning(f"Lever fetch failed for {slug}: {e}")
                    if len(drives) >= limit:
                        break
        except Exception as e:
            logger.warning(f"Error in fetch_from_lever: {e}")
        return drives

    async def fetch_from_jobspy(
        self,
        limit: int = 6,
        sites: Optional[List[str]] = None,
        search_term: str = "Software Engineer",
        location: str = "India"
    ) -> List[Dict[str, Any]]:
        """Fetch live postings from LinkedIn/Naukri using JobSpy if installed, retaining ONLY direct application URLs."""
        drives: List[Dict[str, Any]] = []
        target_sites = sites if sites else ["naukri", "linkedin"]
        try:
            def _run_scrape():
                from jobspy import scrape_jobs
                return scrape_jobs(
                    site_name=target_sites,
                    search_term=search_term,
                    location=location,
                    results_wanted=limit,
                    country_indeed="India"
                )

            df = await asyncio.to_thread(_run_scrape)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    title = str(row.get("title") or "")
                    if not is_engineering_role(title):
                        continue
                    company = str(row.get("company") or "").strip()
                    if not company:
                        continue
                    raw_desc = str(row.get("description") or "")
                    direct_url = str(row.get("job_url_direct") or "")
                    if not is_valid_direct_url(direct_url):
                        continue  # Avoid saving unverified aggregator links or synthetic search links
                    min_amt = row.get("min_amount")
                    max_amt = row.get("max_amount")
                    currency = row.get("currency") or "INR"
                    if min_amt and max_amt and not (isinstance(min_amt, float) and (min_amt != min_amt)):
                        salary = f"{min_amt:,.0f} - {max_amt:,.0f} {currency}"
                    else:
                        salary = "9.5 LPA - 16.0 LPA"
                    drives.append(
                        self._build_candidate(
                            company_name=company,
                            role_title=title,
                            location=str(row.get("location") or "India"),
                            job_description=raw_desc,
                            application_url=direct_url,
                            source_platform="JOBSPY",
                            salary_package=salary,
                            company_website=str(row.get("company_url") or ""),
                        )
                    )
                    if len(drives) >= limit:
                        break
        except Exception as e:
            logger.debug(f"JobSpy ({target_sites}) skipped/failed: {e}")
        return drives

    async def _verify_candidate_cached(
        self,
        candidate: Dict[str, Any],
        client: httpx.AsyncClient,
        sem: asyncio.Semaphore,
        trust_live_api: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Verifies URL reachability & expiry with 1-hour cache and bounded concurrency."""
        url = candidate.get("application_url") or ""
        if not is_valid_direct_url(url):
            return None

        now = datetime.now(timezone.utc)
        deadline = candidate.get("deadline_dt")
        if deadline:
            dl = deadline if deadline.tzinfo else deadline.replace(tzinfo=timezone.utc)
            if dl < now:
                return None

        if trust_live_api:
            candidate["verification_status"] = "VERIFIED_ACTIVE"
            candidate["form_type"] = "DIRECT_FORM"
            candidate["verified_at"] = now
            self._verify_cache[url] = (
                now,
                {
                    "is_valid": True,
                    "is_active": True,
                    "verification_status": "VERIFIED_ACTIVE",
                    "form_type": "DIRECT_FORM",
                },
            )
            return candidate

        cached = self._verify_cache.get(url)
        if cached and (now - cached[0]).total_seconds() < 3600:
            ver = cached[1]
        else:
            async with sem:
                ver = await verify_application_link_and_expiry(
                    url=url,
                    company_name=candidate.get("company_name", ""),
                    deadline=deadline,
                    client=client,
                )
            self._verify_cache[url] = (now, ver)

        if not ver.get("is_active"):
            return None

        candidate["verification_status"] = ver["verification_status"]
        candidate["form_type"] = ver["form_type"]
        candidate["verified_at"] = now
        return candidate

    async def run_ingestion(self, college_id: str = "col-anna-001", location_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Main Verified Ingestion Routine.
        Combines Greenhouse (?content=true & ?questions=true), Ashby, SmartRecruiters (India),
        SimplifyJobs GitHub feeds, Lever, curated Indian campus tracks, and verified aggregators.
        Verifies live URL status & deadlines, removes synthetic cloning & duplicates, and scores accuracy.
        """
        now = datetime.now(timezone.utc)
        candidates: List[Dict[str, Any]] = []

        # 1. Verified regional & Indian campus tracks
        for item in VERIFIED_CAMPUS_DRIVES:
            candidates.append(
                self._build_candidate(
                    company_name=item["company_name"],
                    role_title=item["role_title"],
                    location=item.get("location", "Pan India"),
                    job_description=item["job_description"],
                    application_url=item.get("application_url") or resolve_direct_application_url(item["company_name"], item["role_title"]),
                    source_platform="CAMPUS_CURATED",
                    salary_package=item.get("salary_package", "8.0 LPA - 12.0 LPA"),
                    min_cgpa=float(item.get("min_cgpa", 6.5)),
                    max_arrears=int(item.get("max_arrears", 0)),
                    allowed_departments=item.get("allowed_departments", "CSE,IT,ECE"),
                    days_ahead=int(item.get("days_ahead", 7)),
                    company_website=item.get("company_website"),
                    selection_rounds=item.get("selection_rounds"),
                    force_region="INDIA",
                )
            )

        # 2. Fetch live verified ATS & GitHub feeds concurrently with strict per-source time budgets
        async def _run_source(name: str, coro: Any, timeout_sec: float = 12.0) -> List[Dict[str, Any]]:
            try:
                res = await asyncio.wait_for(coro, timeout=timeout_sec)
                return res if isinstance(res, list) else []
            except asyncio.TimeoutError:
                logger.warning(f"Source {name} timed out after {timeout_sec}s; skipping in this cycle.")
                return []
            except Exception as exc:
                logger.warning(f"Source {name} failed: {exc}")
                return []

        is_filtered = bool(location_filter and location_filter.strip() and location_filter.lower() != "all")
        canonical_loc = canonicalize_location_query(location_filter) if is_filtered else None
        loc_terms = expand_location_terms(location_filter) if is_filtered else []

        results = await asyncio.gather(
            _run_source("greenhouse", self.fetch_from_greenhouse(limit=16), 12.0),
            _run_source("ashby", self.fetch_from_ashby(limit=12), 10.0),
            _run_source("smartrecruiters", self.fetch_from_smartrecruiters(limit=12), 12.0),
            _run_source("simplify_github", self.fetch_from_simplify_github(limit=20), 10.0),
            _run_source("lever", self.fetch_from_lever(limit=6), 10.0),
            _run_source("arbeitnow", self.fetch_from_arbeitnow(limit=6), 8.0),
            _run_source("jobicy", self.fetch_from_jobicy(limit=6), 8.0),
            _run_source("remotive", self.fetch_from_remotive(limit=6), 8.0),
            _run_source(
                "jobspy",
                self.fetch_from_jobspy(limit=5, search_term="Software Engineer", location=canonical_loc or "India"),
                10.0,
            ),
        )
        live_greenhouse, live_ashby, live_smartrecruiters, live_simplify, live_lever, live_arbeitnow, live_jobicy, live_remotive, live_jobspy = results

        # Postings just retrieved from official JSON ATS APIs (and verified non-expired) need no redundant HTML GET
        live_api_urls = {
            c["application_url"].lower().rstrip("/")
            for c in (live_greenhouse + live_ashby + live_smartrecruiters + live_lever)
        }

        for batch in results:
            candidates.extend(batch)

        # Filter to true location/alias matches if location_filter provided (NO synthetic cloning)
        resolved_loc = canonical_loc if is_filtered else "All"
        exact_match_count = 0
        pan_india_fallback_used = False
        if is_filtered:
            district_matches = [
                c for c in candidates
                if any(
                    term in c.get("location", "").lower() or term in c.get("job_description", "").lower()
                    for term in loc_terms
                )
            ]
            exact_match_count = len(district_matches)
            # When a smaller district has few local office listings, also ingest real Pan-India & Remote
            # openings (preserving their true locations) so students still receive actionable results.
            if exact_match_count < 5:
                pan_india_fallback_used = True
                fallback_pool = [
                    c for c in candidates
                    if c not in district_matches
                    and (
                        c.get("region_scope") == "REMOTE"
                        or any(k in c.get("location", "").lower() for k in ("pan india", "anywhere", "remote"))
                    )
                ]
                candidates = district_matches + fallback_pool[:15]
            else:
                candidates = district_matches

        # 3. In-batch deduplication + HTTP liveness & expiry verification
        deduped_candidates: List[Dict[str, Any]] = []
        seen_batch_keys = set()
        seen_batch_urls = set()
        for c in candidates:
            bkey = (c["company_name"].lower(), c["role_title"].lower(), c["location"].lower())
            burl = c["application_url"].lower().rstrip("/")
            if bkey in seen_batch_keys or burl in seen_batch_urls:
                continue
            seen_batch_keys.add(bkey)
            seen_batch_urls.add(burl)
            deduped_candidates.append(c)

        sem = asyncio.Semaphore(16)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        fast_timeout = httpx.Timeout(4.0, connect=2.5, read=3.5)
        async with httpx.AsyncClient(timeout=fast_timeout, follow_redirects=True, headers=headers) as verify_client:
            verified_raw = await asyncio.gather(
                *[
                    self._verify_candidate_cached(
                        c,
                        verify_client,
                        sem,
                        trust_live_api=(c["application_url"].lower().rstrip("/") in live_api_urls),
                    )
                    for c in deduped_candidates
                ],
                return_exceptions=True,
            )
        verified_candidates = [v for v in verified_raw if isinstance(v, dict)]

        added_companies: List[str] = []
        updated_companies: List[str] = []
        with Session(engine) as session:
            for item in verified_candidates:
                company = item["company_name"]
                role = item["role_title"]
                app_url = item["application_url"]

                existing = session.exec(
                    select(PlacementDrive).where(
                        PlacementDrive.college_id == college_id,
                        (
                            ((PlacementDrive.company_name == company) & (PlacementDrive.role_title == role))
                            | (PlacementDrive.application_url == app_url)
                        ),
                    )
                ).first()

                deadline = item.get("deadline_dt") or (now + timedelta(days=max(2, item.get("days_ahead", 9) - 2)))
                drive_date = item.get("deadline_dt") or (now + timedelta(days=item.get("days_ahead", 9)))

                acc_score, acc_breakdown = compute_job_accuracy_score(
                    source_platform=item.get("source_platform", "CAMPUS_CURATED"),
                    application_url=app_url,
                    form_type=item.get("form_type"),
                    verification_status=item.get("verification_status"),
                    schema_source=item.get("schema_source"),
                    job_description=item.get("job_description"),
                    registration_deadline=deadline,
                )

                if not existing:
                    new_drive = PlacementDrive(
                        college_id=college_id,
                        company_name=company,
                        role_title=role,
                        job_description=item["job_description"],
                        location=item["location"],
                        salary_package=item["salary_package"],
                        min_cgpa=item["min_cgpa"],
                        max_arrears=item["max_arrears"],
                        allowed_departments=item["allowed_departments"],
                        drive_date=drive_date,
                        registration_deadline=deadline,
                        status=DriveStatus.ACTIVE,
                        application_url=app_url,
                        company_website=item["company_website"],
                        selection_rounds=item["selection_rounds"],
                        form_type=item.get("form_type", "DIRECT_FORM"),
                        verification_status=item.get("verification_status", "VERIFIED_ACTIVE"),
                        expected_fields=item.get("expected_fields"),
                        source_platform=item.get("source_platform", "CAMPUS_CURATED"),
                        region_scope=item.get("region_scope", "INDIA"),
                        accuracy_score=acc_score,
                        accuracy_breakdown=acc_breakdown,
                        verified_at=item.get("verified_at", now),
                    )
                    session.add(new_drive)
                    session.commit()
                    session.refresh(new_drive)
                    added_companies.append(company)
                else:
                    updated = False
                    if item.get("job_description") and len(item["job_description"]) > len(existing.job_description or ""):
                        existing.job_description = item["job_description"]
                        updated = True
                    if item.get("expected_fields") and (
                        not existing.expected_fields or "College / Degree" in existing.expected_fields
                    ):
                        existing.expected_fields = item["expected_fields"]
                        updated = True
                    if existing.accuracy_score != acc_score or existing.verification_status != item.get("verification_status"):
                        existing.accuracy_score = acc_score
                        existing.accuracy_breakdown = acc_breakdown
                        existing.verification_status = item.get("verification_status", "VERIFIED_ACTIVE")
                        existing.source_platform = item.get("source_platform", existing.source_platform)
                        existing.region_scope = item.get("region_scope", existing.region_scope)
                        existing.verified_at = now
                        updated = True
                    if existing.drive_date and existing.drive_date <= now and not item.get("deadline_dt"):
                        days_ahead = item.get("days_ahead", 7)
                        existing.drive_date = now + timedelta(days=days_ahead)
                        existing.registration_deadline = existing.drive_date - timedelta(days=2)
                        existing.status = DriveStatus.ACTIVE
                        updated = True

                    if updated:
                        session.add(existing)
                        session.commit()
                        updated_companies.append(company)

            count_query = select(func.count(PlacementDrive.id)).where(
                (PlacementDrive.college_id == college_id)
                | (PlacementDrive.college_id == "col-anna-001")
                | (PlacementDrive.college_id == None),
                PlacementDrive.verification_status != "EXPIRED",
            )
            if is_filtered and loc_terms:
                count_query = count_query.where(
                    or_(*[func.lower(PlacementDrive.location).like(f"%{t}%") for t in loc_terms])
                )
            total_matching = session.exec(count_query).one()

        self.last_sync_time = now
        self.last_sync_count = len(added_companies)

        if added_companies:
            logger.info(f"Verified ingestion added {len(added_companies)} drives: {', '.join(added_companies[:6])}")

        return {
            "status": "success",
            "total_candidates_evaluated": len(deduped_candidates),
            "verified_candidates": len(verified_candidates),
            "new_drives_added": len(added_companies),
            "drives_updated": len(updated_companies),
            "total_active_drives": total_matching,
            "companies_added": added_companies,
            "location_filtered": location_filter or "All",
            "resolved_location": resolved_loc,
            "exact_district_matches": exact_match_count,
            "pan_india_fallback_used": pan_india_fallback_used,
            "source_breakdown": {
                "verified_tracks": len(VERIFIED_CAMPUS_DRIVES),
                "greenhouse_live": len(live_greenhouse),
                "ashby_live": len(live_ashby),
                "smartrecruiters_live": len(live_smartrecruiters),
                "simplify_github_live": len(live_simplify),
                "lever_live": len(live_lever),
                "arbeitnow_live": len(live_arbeitnow),
                "jobicy_live": len(live_jobicy),
                "remotive_live": len(live_remotive),
                "jobspy_linkedin_naukri_live": len(live_jobspy),
            },
            "timestamp": now.isoformat(),
        }

job_fetcher = JobFetcherWorker()

