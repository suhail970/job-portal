# Company Hiring Playbook: Amazon (Software Development Engineer - SDE-1)

**Role Target**: SDE-1 (Full-Time / Campus FTE)  
**Typical CTC Range**: ₹28 - ₹45 LPA  
**Interview Rounds**: Online Assessment (OA) $\rightarrow$ 3-4 Rounds Technical & Leadership Interviews $\rightarrow$ Bar Raiser Round

---

## 1. The Amazon Hiring Mindset: 16 Leadership Principles (LPs)

Amazon evaluates candidates 50% on technical problem solving and 50% on behavioral alignment with their **16 Leadership Principles**. In every single technical round, the first 15-20 minutes are devoted to LP behavioral scenarios using the **STAR method** (Situation, Task, Action, Result).

### Top 5 High-Frequency LPs for Campus SDE-1:
1. **Customer Obsession**: How you prioritized end-user stability or feedback over shortcuts.
2. **Ownership**: Stepping up to fix an unassigned bug or technical debt in a team college project.
3. **Bias for Action**: Making a sound engineering decision when full requirements or documentation were missing.
4. **Learn and Be Curious**: Exploring a new language, framework, or architecture outside academic requirements.
5. **Dive Deep**: Debugging a subtle performance bottleneck, race condition, or memory leak down to root cause.

---

## 2. Technical Evaluation Blueprint

### Round 1: Online Assessment (OA on HackerRank)
- **Time**: 90 minutes.
- **Section 1**: 2 LeetCode Medium/Hard algorithmic coding problems.
  - *Frequent Topics*: Monotonic Stacks, Sliding Window, Graph BFS/DFS, Binary Trees, Dijkstra's Algorithm, Dynamic Programming (Knapsack variants).
- **Section 2**: Work Simulation (Prioritizing sprint tickets, analyzing mock team trade-offs).
- **Section 3**: Work Style Assessment (Behavioral LP choices).

### Rounds 2 & 3: Technical Problem Solving & Data Structures
- **Focus**: Algorithmic optimality, clean object-oriented code, edge case consideration, and asymptotic complexity analysis ($O(V+E)$, $O(n \log n)$).
- **Key Patterns**:
  - LRU Cache implementation (`OrderedDict` or Hash Map + Doubly Linked List).
  - Trapping Rain Water / Container with Most Water (Two Pointers).
  - Course Schedule I & II (Topological Sort / Kahn's Algorithm).
  - Word Break / Longest Increasing Subsequence (DP).

### Round 4: Bar Raiser & Low-Level Design (LLD)
- Conducted by a certified Amazon Bar Raiser from an unrelated team.
- Focus: System extensibility, SOLID principles, design patterns (Strategy, Factory, Observer), and stress-testing candidate resilience under pushback.

---

## 3. High-Yield Practice Checklist

| Category | Problem / Topic | Difficulty | Recommended Strategy |
| :--- | :--- | :---: | :--- |
| **Data Structures** | LRU Cache | Medium | Implement doubly linked list + dictionary without built-in helper libraries. |
| **Two Pointers** | 3Sum & Container With Most Water | Medium | Sort array first; practice pointer convergence without duplicates. |
| **Trees & Graphs** | Lowest Common Ancestor (Binary Tree) | Medium | Recursive post-order traversal with early termination. |
| **Graphs** | Alien Dictionary / Course Schedule | Hard | Build adjacency list; detect cycles via in-degree array. |
| **OOP Design** | Parking Lot / Locker System | Medium | Define clean interfaces: `IParkingSpot`, `Vehicle`, `TicketMachine`. |

