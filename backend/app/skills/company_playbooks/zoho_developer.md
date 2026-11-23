# Company Hiring Playbook: Zoho Corporation (Software Developer)

**Role Target**: Software Developer / Member Technical Staff  
**Typical CTC Range**: ₹6.5 - ₹10 LPA  
**Interview Rounds**: 5 Rounds (Basic Coding $\rightarrow$ Advanced Coding $\rightarrow$ Low-Level Design $\rightarrow$ Technical HR $\rightarrow$ General HR)

---

## 1. The Zoho Hiring Philosophy: "Code from Scratch"

Zoho Corporation evaluates core algorithmic depth and machine-level understanding. **Zoho strictly discourages the use of standard library shortcuts** (e.g., `Collections.sort()`, `std::map`, `Arrays.copyOf()`). Candidates must demonstrate the ability to manipulate strings, arrays, matrices, and pointers manually in C, C++, or Java.

### Key Rules of Zoho Rounds:
- **No Built-in Methods**: Writing your own `string_length()`, `reverse_string()`, or `quick_sort()` is often expected.
- **Pointer & Memory Mastery**: Strong understanding of 2D memory arrays, stack vs. heap allocation, and recursion call stacks.
- **Production Code Style**: Proper variable naming, zero magic numbers, modular helper functions.

---

## 2. Round-by-Round Breakdown

### Round 1: Basic Written / Online Aptitude & C Programming
- **Time**: 90 minutes.
- **Section 1 (Aptitude)**: Quantitative math, permutations, probability, time & distance, clock problems.
- **Section 2 (C Code Debugging)**: Predicting output of pointer arithmetic, macro expansions, bitwise operators, and `struct` memory alignment.

### Round 2: Basic Programming (Matrix & String Challenges)
- Solve 5 algorithmic problems within 2 hours.
- *Classic Zoho Problems*:
  1. **Cross-Pattern Printing**: Print diagonal X pattern for odd-length strings (e.g., `PROGRAM`).
  2. **Run-Length Decoding**: Expand strings like `a1b10` $\rightarrow$ `abbbbbbbbbb`.
  3. **Spiral Matrix Traversal**: Print $N \times N$ matrix in clockwise spiral order.
  4. **Subarray with Given Sum**: Find contiguous subarray summing to $K$ in $O(n)$ time.
  5. **Roman to Integer / Currency Denomination Converter**.

### Round 3: Advanced Programming & Low-Level Design (LLD)
- Solve 1 comprehensive real-world simulation in 2.5 to 3 hours.
- Candidates must create a complete console-based application with interactive menus.
- *Frequent Zoho LLD Systems*:
  - **Railway Reservation System**: Berths (Lower, Middle, Upper, RAC, Waiting List), ticket cancellation, auto-allocation.
  - **Taxi Booking Application**: Fleet of 5 taxis, 6 equidistant points (A to F), booking allocation based on nearest idle taxi and lowest total earnings.
  - **Call Taxi / Lift Management System**: Directional elevator scheduling algorithm.
  - **Dungeon Game / Snake and Ladder**: Terminal grid pathfinding with obstacles.

### Rounds 4 & 5: Technical HR & General HR
- Review of the candidate's design decisions made in Round 3.
- Database fundamentals: Normalization (1NF to 3NF), Indexing, SQL Joins.
- Cultural alignment: Passion for craftsmanship, long-term tenure, continuous learning.

---

## 3. High-Yield Practice Checklist

| Category | Problem Description | Key Technique |
| :--- | :--- | :--- |
| **String Manipulation** | Expand alphanumeric strings (`b3c6` $\rightarrow$ `bbbcccccc`) | Character buffer scanning and numeric parsing |
| **Matrix Algorithms** | 90-Degree In-Place Matrix Rotation | Transpose matrix + reverse each row |
| **Pattern Generation** | Diamond, Hollow Rhombus, Matrix Spirals | Nested coordinate loops $(i, j)$ |
| **Object-Oriented Design** | Railway / Bus Seat Reservation Engine | Object modeling (`Passenger`, `Ticket`, `CoachManager`) |
| **Data Structures** | Custom Queue & Singly Linked List in C/Java | Dynamic node allocation without STL/Collections |

