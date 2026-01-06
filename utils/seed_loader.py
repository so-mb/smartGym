import csv
from datetime import datetime
from config import ENCODING


def _blank_to_none(v):
    if v is None:
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


def _to_int(v):
    v = _blank_to_none(v)
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return v


def _to_float(v):
    v = _blank_to_none(v)
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return v


def _to_bool_yesno(v):
    v = _blank_to_none(v)
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("yes", "y", "true", "1", "-1"):
        return True
    if s in ("no", "n", "false", "0"):
        return False
    return v


def _to_datetime(v):
    v = _blank_to_none(v)
    if v is None:
        return None
    try:
        # Handles both 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS'
        return datetime.fromisoformat(str(v).strip())
    except Exception:
        return v


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
                    _blank_to_none(row.get("Phone")),
                    _to_datetime(row.get("DateOfBirth")),
                    _to_datetime(row.get("JoinDate")),
                    _blank_to_none(row.get("Status")),
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
                    _to_int(row.get("DurationMonths")),
                    _to_float(row.get("MonthlyFee")),
                    _to_bool_yesno(row.get("IncludesPTSessions", "No")),
                ],
            )
            # PlanName isn't unique in the seed (e.g. Basic 1 month vs Basic 6 months),
            # so we don't build a PlanName -> PlanID map here.

    print("  Loading MemberMemberships...")
    # CSV has MemberID and PlanID as 1-based indices, need to map to actual IDs
    member_list = sorted(member_email_map.values())
    # Plan IDs are deterministic by insertion order (AUTOINCREMENT starts at 1).
    cursor = conn.cursor()
    cursor.execute("SELECT PlanID FROM MembershipPlans ORDER BY PlanID")
    plan_list = [r[0] for r in cursor.fetchall()]

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
                            _to_datetime(row.get("StartDate")),
                            _to_datetime(row.get("EndDate")),
                            _blank_to_none(row.get("Status")),
                            _blank_to_none(row.get("CancelReason")),
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
                            _to_float(row.get("Amount")),
                            _to_datetime(row.get("PaidOn")),
                            _blank_to_none(row.get("Method")),
                            _blank_to_none(row.get("Status")),
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
                    _blank_to_none(row.get("MuscleGroup")),
                    _blank_to_none(row.get("EquipmentType")),
                    _to_int(row.get("Difficulty")),
                    _blank_to_none(row.get("VideoURL")),
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
                "INSERT INTO WorkoutPlans (PlanName, GoalType, [Level]) VALUES (?, ?, ?)",
                [
                    row["PlanName"],
                    _blank_to_none(row.get("GoalType")),
                    _blank_to_none(row.get("Level")),
                ],
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
                            _to_int(row.get("DayNumber")),
                            _to_int(row.get("SortOrder")),
                            _to_int(row.get("TargetSets")),
                            _to_int(row.get("TargetRepsMin")),
                            _to_int(row.get("TargetRepsMax")),
                            _to_float(row.get("TargetRPE")),
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
                            _to_datetime(row.get("SessionDateTime")),
                            _to_int(row.get("DurationMinutes")),
                            _blank_to_none(row.get("SessionType")),
                            _blank_to_none(row.get("Notes")),
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
                            _to_int(row.get("SortOrder")),
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
                            _to_int(row.get("SetNumber")),
                            _to_int(row.get("Reps")),
                            _to_float(row.get("WeightKg")),
                            _to_float(row.get("RPE")),
                            _to_bool_yesno(row.get("IsPR", "No")),
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
                            _to_datetime(row.get("MeasuredOn")),
                            _to_float(row.get("WeightKg")),
                            _to_float(row.get("BodyFatPct")),
                            _to_float(row.get("ChestCm")),
                            _to_float(row.get("WaistCm")),
                            _to_float(row.get("HipCm")),
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
                            _blank_to_none(row.get("GoalType")),
                            _to_float(row.get("TargetValue")),
                            _to_datetime(row.get("StartDate")),
                            _to_datetime(row.get("TargetDate")),
                            _blank_to_none(row.get("Status")),
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
                            _to_datetime(row.get("CreatedOn")),
                            _blank_to_none(row.get("RecommendationType")),
                            _blank_to_none(row.get("ReasonText")),
                            related_ex_id,
                        ],
                    )
            except (ValueError, IndexError):
                continue
