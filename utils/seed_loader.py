import csv
from config import ENCODING


def load_csv_simple(conn, table_name, csv_path):
    """Load CSV where IDs are auto-generated and don't need mapping"""
    cursor = conn.cursor()
    with open(csv_path, newline="", encoding=ENCODING) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not any(row.values()):
                continue
            columns = [
                col
                for col in reader.fieldnames
                if col and row.get(col) is not None and row.get(col) != ""
            ]
            if not columns:
                continue
            placeholders = ",".join(["?"] * len(columns))
            column_list = ",".join(columns)
            sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
            cursor.execute(sql, [row[col] for col in columns])


def get_id_by_key(conn, table_name, key_col, key_value, id_col):
    """Get generated ID by natural key"""
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT {id_col} FROM {table_name} WHERE {key_col} = ?", [key_value]
    )
    row = cursor.fetchone()
    return row[0] if row else None


def load_seed_data(conn):
    print("  Loading Members...")
    member_email_map = {}  # email -> MemberID
    with open("seed/members.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("Email"):
                continue
            cursor.execute(
                "INSERT INTO Members (FirstName, LastName, Email, Phone, DateOfBirth, JoinDate, Status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    row["FirstName"],
                    row["LastName"],
                    row["Email"],
                    row.get("Phone", ""),
                    row.get("DateOfBirth", ""),
                    row.get("JoinDate", ""),
                    row.get("Status", ""),
                ],
            )
            member_id = get_id_by_key(
                conn, "Members", "Email", row["Email"], "MemberID"
            )
            if member_id:
                member_email_map[row["Email"]] = member_id

    print("  Loading MembershipPlans...")
    plan_name_map = {}  # plan_name -> PlanID
    with open("seed/membership_plans.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("PlanName"):
                continue
            cursor.execute(
                "INSERT INTO MembershipPlans (PlanName, DurationMonths, MonthlyFee, IncludesPTSessions) VALUES (?, ?, ?, ?)",
                [
                    row["PlanName"],
                    row.get("DurationMonths", ""),
                    row.get("MonthlyFee", ""),
                    row.get("IncludesPTSessions", "No"),
                ],
            )
            plan_id = get_id_by_key(
                conn, "MembershipPlans", "PlanName", row["PlanName"], "PlanID"
            )
            if plan_id:
                plan_name_map[row["PlanName"]] = plan_id

    print("  Loading MemberMemberships...")
    # CSV has MemberID and PlanID as 1-based indices, need to map to actual IDs
    member_list = sorted(member_email_map.values())
    plan_list = sorted(plan_name_map.values())

    membership_id_map = {}  # old_mm_index -> new MemberMembershipID
    with open("seed/member_memberships.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        mm_index = 1
        for row in reader:
            if not row.get("MemberID") or not row.get("PlanID"):
                continue
            try:
                member_idx = int(row["MemberID"]) - 1
                plan_idx = int(row["PlanID"]) - 1
                if 0 <= member_idx < len(member_list) and 0 <= plan_idx < len(
                    plan_list
                ):
                    cursor.execute(
                        "INSERT INTO MemberMemberships (MemberID, PlanID, StartDate, EndDate, Status, CancelReason) VALUES (?, ?, ?, ?, ?, ?)",
                        [
                            member_list[member_idx],
                            plan_list[plan_idx],
                            row.get("StartDate", ""),
                            row.get("EndDate", ""),
                            row.get("Status", ""),
                            row.get("CancelReason", ""),
                        ],
                    )
                    # Get the generated ID
                    cursor.execute(
                        "SELECT MAX(MemberMembershipID) FROM MemberMemberships"
                    )
                    new_id = cursor.fetchone()[0]
                    membership_id_map[mm_index] = new_id
                    mm_index += 1
            except (ValueError, IndexError):
                continue

    print("  Loading Payments...")
    with open("seed/payments.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("MemberMembershipID"):
                continue
            try:
                old_mm_id = int(row["MemberMembershipID"])
                new_mm_id = membership_id_map.get(old_mm_id)
                if new_mm_id:
                    cursor.execute(
                        "INSERT INTO Payments (MemberMembershipID, Amount, PaidOn, Method, Status) VALUES (?, ?, ?, ?, ?)",
                        [
                            new_mm_id,
                            row["Amount"],
                            row.get("PaidOn", ""),
                            row.get("Method", ""),
                            row.get("Status", ""),
                        ],
                    )
            except (ValueError, KeyError):
                continue

    print("  Loading Exercises...")
    exercise_name_map = {}  # exercise_name -> ExerciseID
    with open("seed/exercises.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("Name"):
                continue
            cursor.execute(
                "INSERT INTO Exercises (Name, MuscleGroup, EquipmentType, Difficulty, VideoURL) VALUES (?, ?, ?, ?, ?)",
                [
                    row["Name"],
                    row.get("MuscleGroup", ""),
                    row.get("EquipmentType", ""),
                    row.get("Difficulty", ""),
                    row.get("VideoURL", ""),
                ],
            )
            ex_id = get_id_by_key(conn, "Exercises", "Name", row["Name"], "ExerciseID")
            if ex_id:
                exercise_name_map[row["Name"]] = ex_id

    print("  Loading WorkoutPlans...")
    workout_plan_name_map = {}  # plan_name -> PlanTemplateID
    with open("seed/workout_plans.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("PlanName"):
                continue
            cursor.execute(
                "INSERT INTO WorkoutPlans (PlanName, GoalType, Level) VALUES (?, ?, ?)",
                [row["PlanName"], row.get("GoalType", ""), row.get("Level", "")],
            )
            wp_id = get_id_by_key(
                conn, "WorkoutPlans", "PlanName", row["PlanName"], "PlanTemplateID"
            )
            if wp_id:
                workout_plan_name_map[row["PlanName"]] = wp_id

    print("  Loading PlanExercises...")
    workout_plan_list = sorted(workout_plan_name_map.values())
    exercise_list = sorted(exercise_name_map.values())
    with open("seed/plan_exercises.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("PlanTemplateID") or not row.get("ExerciseID"):
                continue
            try:
                plan_idx = int(row["PlanTemplateID"]) - 1
                ex_idx = int(row["ExerciseID"]) - 1
                if 0 <= plan_idx < len(workout_plan_list) and 0 <= ex_idx < len(
                    exercise_list
                ):
                    cursor.execute(
                        "INSERT INTO PlanExercises (PlanTemplateID, ExerciseID, DayNumber, SortOrder, TargetSets, TargetRepsMin, TargetRepsMax, TargetRPE) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        [
                            workout_plan_list[plan_idx],
                            exercise_list[ex_idx],
                            row.get("DayNumber", ""),
                            row.get("SortOrder", ""),
                            row.get("TargetSets", ""),
                            row.get("TargetRepsMin", ""),
                            row.get("TargetRepsMax", ""),
                            row.get("TargetRPE", ""),
                        ],
                    )
            except (ValueError, IndexError):
                continue

    print("  Loading TrainingSessions...")
    session_id_map = {}  # old_session_index -> new SessionID
    with open("seed/training_sessions.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        session_index = 1
        for row in reader:
            if not row.get("MemberID"):
                continue
            try:
                member_idx = int(row["MemberID"]) - 1
                if 0 <= member_idx < len(member_list):
                    cursor.execute(
                        "INSERT INTO TrainingSessions (MemberID, SessionDateTime, DurationMinutes, SessionType, Notes) VALUES (?, ?, ?, ?, ?)",
                        [
                            member_list[member_idx],
                            row.get("SessionDateTime", ""),
                            row.get("DurationMinutes", ""),
                            row.get("SessionType", ""),
                            row.get("Notes", ""),
                        ],
                    )
                    cursor.execute("SELECT MAX(SessionID) FROM TrainingSessions")
                    new_id = cursor.fetchone()[0]
                    session_id_map[session_index] = new_id
                    session_index += 1
            except (ValueError, IndexError):
                continue

    print("  Loading SessionExercises...")
    session_ex_id_map = {}  # old_se_index -> new SessionExerciseID
    with open("seed/session_exercises.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        se_index = 1
        for row in reader:
            if not row.get("SessionID") or not row.get("ExerciseID"):
                continue
            try:
                session_idx = int(row["SessionID"])
                ex_idx = int(row["ExerciseID"]) - 1
                new_session_id = session_id_map.get(session_idx)
                if new_session_id and 0 <= ex_idx < len(exercise_list):
                    cursor.execute(
                        "INSERT INTO SessionExercises (SessionID, ExerciseID, SortOrder) VALUES (?, ?, ?)",
                        [
                            new_session_id,
                            exercise_list[ex_idx],
                            row.get("SortOrder", ""),
                        ],
                    )
                    cursor.execute(
                        "SELECT MAX(SessionExerciseID) FROM SessionExercises"
                    )
                    new_id = cursor.fetchone()[0]
                    session_ex_id_map[se_index] = new_id
                    se_index += 1
            except (ValueError, KeyError, IndexError):
                continue

    print("  Loading SetLogs...")
    with open("seed/set_logs.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("SessionExerciseID"):
                continue
            try:
                old_se_id = int(row["SessionExerciseID"])
                new_se_id = session_ex_id_map.get(old_se_id)
                if new_se_id:
                    cursor.execute(
                        "INSERT INTO SetLogs (SessionExerciseID, SetNumber, Reps, WeightKg, RPE, IsPR) VALUES (?, ?, ?, ?, ?, ?)",
                        [
                            new_se_id,
                            row.get("SetNumber", ""),
                            row.get("Reps", ""),
                            row.get("WeightKg", ""),
                            row.get("RPE", ""),
                            row.get("IsPR", "No"),
                        ],
                    )
            except (ValueError, KeyError):
                continue

    print("  Loading BodyMetrics...")
    with open("seed/body_metrics.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("MemberID"):
                continue
            try:
                member_idx = int(row["MemberID"]) - 1
                if 0 <= member_idx < len(member_list):
                    cursor.execute(
                        "INSERT INTO BodyMetrics (MemberID, MeasuredOn, WeightKg, BodyFatPct, ChestCm, WaistCm, HipCm) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        [
                            member_list[member_idx],
                            row.get("MeasuredOn", ""),
                            row.get("WeightKg", ""),
                            row.get("BodyFatPct", ""),
                            row.get("ChestCm", ""),
                            row.get("WaistCm", ""),
                            row.get("HipCm", ""),
                        ],
                    )
            except (ValueError, IndexError):
                continue

    print("  Loading Goals...")
    with open("seed/goals.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("MemberID"):
                continue
            try:
                member_idx = int(row["MemberID"]) - 1
                if 0 <= member_idx < len(member_list):
                    cursor.execute(
                        "INSERT INTO Goals (MemberID, GoalType, TargetValue, StartDate, TargetDate, Status) VALUES (?, ?, ?, ?, ?, ?)",
                        [
                            member_list[member_idx],
                            row.get("GoalType", ""),
                            row.get("TargetValue", ""),
                            row.get("StartDate", ""),
                            row.get("TargetDate", ""),
                            row.get("Status", ""),
                        ],
                    )
            except (ValueError, IndexError):
                continue

    print("  Loading Recommendations...")
    with open("seed/recommendations.csv", newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        cursor = conn.cursor()
        for row in reader:
            if not row.get("MemberID"):
                continue
            try:
                member_idx = int(row["MemberID"]) - 1
                if 0 <= member_idx < len(member_list):
                    related_ex_id = None
                    if row.get("RelatedExerciseID"):
                        ex_idx = int(row["RelatedExerciseID"]) - 1
                        if 0 <= ex_idx < len(exercise_list):
                            related_ex_id = exercise_list[ex_idx]
                    cursor.execute(
                        "INSERT INTO Recommendations (MemberID, CreatedOn, RecommendationType, ReasonText, RelatedExerciseID) VALUES (?, ?, ?, ?, ?)",
                        [
                            member_list[member_idx],
                            row.get("CreatedOn", ""),
                            row.get("RecommendationType", ""),
                            row.get("ReasonText", ""),
                            related_ex_id,
                        ],
                    )
            except (ValueError, IndexError):
                continue
