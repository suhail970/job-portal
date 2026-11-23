# SkillBridge AI — Feature Prioritization Matrix (MoSCoW)

**Document Reference**: `SB-DOC-11`  
**Version**: 1.0.0  
**Framework**: MoSCoW (Must-Have, Should-Have, Could-Have, Won't-Have) + Impact vs. Complexity Scoring

---

## 1. Prioritization Rubric

- **Impact Score (1-5)**: Value delivered to student placement outcomes and TPO time savings.
- **Complexity Score (1-5)**: Technical effort, architectural risk, and operational maintenance.
- **Priority Priority Index**: $\text{PPI} = \frac{\text{Impact} \times 2}{\text{Complexity}}$

---

## 2. Feature Classification Table

| Feature Description | Category | MoSCoW Tier | Impact (1-5) | Complexity (1-5) | PPI Score | Sprint Target |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Multi-Tenant College Isolation** | Core Arch | **Must-Have (P0)** | 5 | 2 | 5.0 | Sprint 1 |
| **TPO Campus Drive Publishing** | Placement Ops | **Must-Have (P0)** | 5 | 2 | 5.0 | Sprint 1 |
| **Zero-Cost Model Router (Gemini/Groq)**| AI Platform | **Must-Have (P0)** | 5 | 3 | 3.3 | Sprint 2 |
| **AI Resume ATS & Gap Analyzer** | Career Prep | **Must-Have (P0)** | 5 | 2 | 5.0 | Sprint 2 |
| **1d / 3d / 7d Countdown Prep Hub** | Career Prep | **Must-Have (P0)** | 4 | 2 | 4.0 | Sprint 3 |
| **Voice Mock Interview Simulator** | AI Simulation | **Must-Have (P0)** | 5 | 3 | 3.3 | Sprint 4 |
| **In-Browser Coding Sandbox** | Technical Prep | **Must-Have (P0)** | 4 | 3 | 2.7 | Sprint 4 |
| **Telegram Bot Live Alerts** | Integrations | **Should-Have (P1)**| 4 | 2 | 4.0 | Sprint 5 |
| **Local Offline Ollama Model Switcher**| AI Resilience | **Should-Have (P1)**| 4 | 2 | 4.0 | Sprint 5 |
| **Company Skill Playbooks (Amazon/Zoho/TCS)**| Content Engine | **Should-Have (P1)**| 4 | 2 | 4.0 | Sprint 3 |
| **TPO Excel Export of Shortlisted Students**| Placement Ops | **Should-Have (P1)**| 3 | 1 | 6.0 | Sprint 5 |
| **Multi-Tenant Custom Branding / Logos**| White-labeling| **Could-Have (P2)** | 3 | 2 | 3.0 | Post-MVP |
| **Peer-to-Peer Mock Interview Rooms** | Social Collab | **Could-Have (P2)** | 3 | 4 | 1.5 | Post-MVP |
| **Automated WhatsApp Business API Alerts**| Integrations | **Won't-Have (P3)** | 3 | 4 | 1.5 | Excluded (Requires Paid Meta API) |
| **Paid Monthly Subscription Billing** | Monetization | **Won't-Have (P3)** | 1 | 4 | 0.5 | Excluded (Committed to 100% Free) |

---

## 3. Scope Boundary Justifications

### Why WhatsApp Integration is P3 (Won't-Have)
The Meta WhatsApp Business Cloud API requires credit card registration and charges approximately ₹0.75 per template conversation message. For a college with 1,500 students receiving 10 drive notifications monthly, this creates an ongoing operational cost of ~₹11,250/month. **Telegram Bot API is 100% free with unlimited broadcasts**, perfectly upholding the ₹0 platform commitment.

### Why Commercial Subscription Billing is Excluded
SkillBridge AI is designed to democratize quality placement training for under-resourced engineering colleges. Paid paywalls conflict with the founding mission. All core capabilities (ATS resume analysis, countdown prep sprints, voice mock interviews, coding sandboxes) remain permanently free.

