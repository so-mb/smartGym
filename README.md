# smartGym

A comprehensive Access database system for managing a smart gym, including memberships, workout plans, training sessions, progress tracking, and AI-powered recommendations.

## Project Overview

This database implements a "Smart Gym" management system that goes beyond simple data storage. It includes:

- **Membership Management**: Track members, plans, subscriptions, and payments
- **Workout Planning**: Exercise library, workout plan templates, and plan-to-exercise mappings
- **Training Logs**: Detailed session tracking with granular set-by-set logging
- **Progress Tracking**: Body metrics, goals, and progress monitoring
- **Smart Recommendations**: AI-like recommendations based on training patterns

## Database Structure

### Core Business Tables (Memberships)
- **Members**: Member information and status
- **MembershipPlans**: Available membership tiers (Basic, Premium, PT Bundle)
- **MemberMemberships**: Subscription history (allows tracking multiple subscriptions per member)
- **Payments**: Payment records linked to memberships

### Training Domain Tables
- **Exercises**: Exercise library with muscle groups, equipment, difficulty
- **WorkoutPlans**: Template workout plans (Push/Pull/Legs, Full Body, etc.)
- **PlanExercises**: M:N relationship between plans and exercises (with targets)
- **TrainingSessions**: Actual workout sessions performed by members
- **SessionExercises**: Exercises performed in each session
- **SetLogs**: Granular tracking of sets, reps, weights, RPE, and PRs

### Progress & Goals Tables
- **BodyMetrics**: Weight, body fat, measurements over time
- **Goals**: Member goals (weight loss, strength targets, etc.)
- **Recommendations**: System-generated recommendations for members

## Key Relationships

### 1:N Relationships
- Members → MemberMemberships → Payments
- Members → TrainingSessions → SessionExercises → SetLogs
- Members → BodyMetrics, Goals, Recommendations
- WorkoutPlans → PlanExercises
- Exercises → PlanExercises, SessionExercises

### M:N Relationships
- **WorkoutPlans ↔ Exercises** (via PlanExercises)
- **TrainingSessions ↔ Exercises** (via SessionExercises)

## Sample Queries

The database includes 9 pre-built views/queries:

1. **ActiveMembersWithPlan**: Active members with their current plan and last payment
2. **MonthlyRevenueByPlan**: Revenue breakdown by plan type and month
3. **ExpiringMemberships**: Memberships expiring in the next 14 days
4. **ExercisePopularity**: Most popular exercises by set count
5. **PRLeaderboard**: Personal records achieved this month
6. **TrainingConsistency**: Average sessions per week per member
7. **BodyMetricsProgress**: Weight and measurement changes over time
8. **ActiveRecommendations**: Recent recommendations for members
9. **GoalsProgress**: Active goals with progress tracking

## Setup Instructions

### Prerequisites
- **Windows** (Access database requires Windows)
- **Python 3.10+**
- **Microsoft Access Database Engine** (64-bit)
  - Download from: https://www.microsoft.com/en-us/download/details.aspx?id=54920
- **Microsoft Access** (for database creation, or use pywin32)

### Installation

1. **Install Python dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
   
   Or manually:
   ```powershell
   pip install pyodbc pywin32
   ```

2. **Run the build script:**
   ```powershell
   python build.py
   ```

3. **Output:**
   The script will create `smart_gym.accdb` in the project root directory.

### Build Process

The `build.py` script:
1. Removes existing database (if present)
2. Creates all tables from `schema/tables.sql`
3. Loads seed data from CSV files in `seed/`
4. Creates foreign key relationships from `schema/relationships.sql`
5. Creates views/queries from `schema/queries.sql`

## Project Structure

```
smart-gym-db/
│
├── build.py                 # Main build script
├── config.py                # Database configuration
├── smart_gym.accdb          # Generated Access database (after build)
│
├── schema/
│   ├── tables.sql          # Table definitions
│   ├── relationships.sql   # Foreign key constraints
│   └── queries.sql         # Views and queries
│
├── seed/
│   ├── members.csv
│   ├── membership_plans.csv
│   ├── member_memberships.csv
│   ├── payments.csv
│   ├── exercises.csv
│   ├── workout_plans.csv
│   ├── plan_exercises.csv
│   ├── training_sessions.csv
│   ├── session_exercises.csv
│   ├── set_logs.csv
│   ├── body_metrics.csv
│   ├── goals.csv
│   └── recommendations.csv
│
├── utils/
│   ├── db.py               # Database connection utilities
│   └── seed_loader.py      # CSV data loader
│
├─ .github/
│   └─ workflows/
│       └─ build-access-db.yml
│
└── README.md
```

## Use Case

This database solves the problem of managing a modern gym that needs to:
- Track member subscriptions and payments over time
- Provide structured workout plans to members
- Log detailed training sessions (not just "worked out", but specific exercises, sets, reps, weights)
- Monitor progress through body metrics
- Set and track goals
- Generate intelligent recommendations (e.g., "increase weight", "deload", "add cardio")

## Notes

- The database uses Access SQL syntax (AUTOINCREMENT, YESNO, etc.)
- Some advanced SQL features (window functions) may need adjustment for older Access versions
- Date functions use Access-specific syntax (DATEDIFF, DATEADD)
- The seed data includes realistic sample data for testing queries

## Troubleshooting

**Error: "Microsoft Access Driver not found"**
- Install Microsoft Access Database Engine (64-bit) from Microsoft's website
- Ensure Python and Access Engine are both 64-bit or both 32-bit

**Error: "win32com not available"**
- Install pywin32: `pip install pywin32`
- Or manually create an empty Access database file named `smart_gym.accdb` in the project root, then run the script

**Error: "Table already exists"**
- The build script automatically removes existing database
- If issues persist, manually delete `smart_gym.accdb` before running

**Queries not working**
- Some queries use Access-specific functions that may vary by version
- Test queries individually in Access if needed

**Running on macOS/Linux**
- This project requires Windows to create Access databases
- You can develop the code on any OS, but must run `build.py` on Windows
- Consider using a Windows VM, Azure VM, or a friend's Windows computer for the final build
