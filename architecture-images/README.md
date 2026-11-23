# SkillBridge AI — Architecture Diagrams Gallery

This directory contains high-definition **PNG** and **SVG** vector images of all core system architecture diagrams.

## Diagram Index

1. **System Topology & Overview**
   * PNG: [`01_system_topology.png`](./01_system_topology.png)
   * SVG: [`01_system_topology.svg`](./01_system_topology.svg)
   * *Description: High-level overview of the presentation layer, FastAPI core, AI cluster, and data tiers.*

2. **Multi-Tenant College Isolation Model**
   * PNG: [`02_multi_tenant_isolation.png`](./02_multi_tenant_isolation.png)
   * SVG: [`02_multi_tenant_isolation.svg`](./02_multi_tenant_isolation.svg)
   * *Description: Sequence diagram detailing JWT tenant claims and PostgreSQL Row-Level Security (RLS).*

3. **Hermes-Inspired Multi-Agent Engine**
   * PNG: [`03_multi_agent_engine.png`](./03_multi_agent_engine.png)
   * SVG: [`03_multi_agent_engine.svg`](./03_multi_agent_engine.svg)
   * *Description: Orchestrator vs Leaf agent hierarchy and dynamic 1d/3d/7d countdown generation.*

4. **Pluggable Free AI Model Router**
   * PNG: [`04_ai_model_router.png`](./04_ai_model_router.png)
   * SVG: [`04_ai_model_router.svg`](./04_ai_model_router.svg)
   * *Description: Multi-provider gateway for Gemini Flash, Groq, OpenRouter, and local Ollama.*

5. **Database Architecture & Entity Relationships (ERD)**
   * PNG: [`05_database_erd.png`](./05_database_erd.png)
   * SVG: [`05_database_erd.svg`](./05_database_erd.svg)
   * *Description: Relational schema and pgvector embeddings.*

6. **Voice Mock Interview & Coding Sandbox**
   * PNG: [`06_voice_and_coding_simulation.png`](./06_voice_and_coding_simulation.png)
   * SVG: [`06_voice_and_coding_simulation.svg`](./06_voice_and_coding_simulation.svg)
   * *Description: Web Speech API audio processing and Piston API remote code execution.*

7. **Notification & Telegram Bot Pipeline**
   * PNG: [`07_notification_pipeline.png`](./07_notification_pipeline.png)
   * SVG: [`07_notification_pipeline.svg`](./07_notification_pipeline.svg)
   * *Description: Automated drive alerts and batch cron delivery to Telegram.*

8. **Free Cloud Deployment Topology**
   * PNG: [`08_deployment_topology.png`](./08_deployment_topology.png)
   * SVG: [`08_deployment_topology.svg`](./08_deployment_topology.svg)
   * *Description: Complete zero-cost infrastructure topology (Vercel, Render/Railway, Supabase, Cloudflare).*
