-- Core Business: Memberships
CREATE TABLE Members (
    MemberID AUTOINCREMENT PRIMARY KEY,
    FirstName TEXT(50) NOT NULL,
    LastName TEXT(50) NOT NULL,
    Email TEXT(120),
    Phone TEXT(20),
    DateOfBirth DATETIME,
    JoinDate DATETIME,
    Status TEXT(20)
);

CREATE TABLE MembershipPlans (
    PlanID AUTOINCREMENT PRIMARY KEY,
    PlanName TEXT(100) NOT NULL,
    DurationMonths INTEGER,
    MonthlyFee DOUBLE,
    IncludesPTSessions YESNO
);

CREATE TABLE MemberMemberships (
    MemberMembershipID AUTOINCREMENT PRIMARY KEY,
    MemberID LONG NOT NULL,
    PlanID LONG NOT NULL,
    StartDate DATETIME,
    EndDate DATETIME,
    Status TEXT(20),
    CancelReason TEXT(255)
);

CREATE TABLE Payments (
    PaymentID AUTOINCREMENT PRIMARY KEY,
    MemberMembershipID LONG NOT NULL,
    Amount DOUBLE,
    PaidOn DATETIME,
    Method TEXT(20),
    Status TEXT(20)
);

-- Training Domain: Plans + Sessions + Logs
CREATE TABLE Exercises (
    ExerciseID AUTOINCREMENT PRIMARY KEY,
    Name TEXT(100) NOT NULL,
    MuscleGroup TEXT(50),
    EquipmentType TEXT(50),
    Difficulty INTEGER,
    VideoURL TEXT(255)
);

CREATE TABLE WorkoutPlans (
    PlanTemplateID AUTOINCREMENT PRIMARY KEY,
    PlanName TEXT(100),
    GoalType TEXT(50),
    Level TEXT(30)
);

CREATE TABLE PlanExercises (
    PlanExerciseID AUTOINCREMENT PRIMARY KEY,
    PlanTemplateID LONG NOT NULL,
    ExerciseID LONG NOT NULL,
    DayNumber INTEGER,
    SortOrder INTEGER,
    TargetSets INTEGER,
    TargetRepsMin INTEGER,
    TargetRepsMax INTEGER,
    TargetRPE DOUBLE
);

CREATE TABLE TrainingSessions (
    SessionID AUTOINCREMENT PRIMARY KEY,
    MemberID LONG NOT NULL,
    SessionDateTime DATETIME,
    DurationMinutes INTEGER,
    SessionType TEXT(30),
    Notes TEXT(255)
);

CREATE TABLE SessionExercises (
    SessionExerciseID AUTOINCREMENT PRIMARY KEY,
    SessionID LONG NOT NULL,
    ExerciseID LONG NOT NULL,
    SortOrder INTEGER
);

CREATE TABLE SetLogs (
    SetLogID AUTOINCREMENT PRIMARY KEY,
    SessionExerciseID LONG NOT NULL,
    SetNumber INTEGER,
    Reps INTEGER,
    WeightKg DOUBLE,
    RPE DOUBLE,
    IsPR YESNO
);

-- Progress, Goals, Recommendations
CREATE TABLE BodyMetrics (
    MetricID AUTOINCREMENT PRIMARY KEY,
    MemberID LONG NOT NULL,
    MeasuredOn DATETIME,
    WeightKg DOUBLE,
    BodyFatPct DOUBLE,
    ChestCm DOUBLE,
    WaistCm DOUBLE,
    HipCm DOUBLE
);

CREATE TABLE Goals (
    GoalID AUTOINCREMENT PRIMARY KEY,
    MemberID LONG NOT NULL,
    GoalType TEXT(50),
    TargetValue DOUBLE,
    StartDate DATETIME,
    TargetDate DATETIME,
    Status TEXT(20)
);

CREATE TABLE Recommendations (
    RecommendationID AUTOINCREMENT PRIMARY KEY,
    MemberID LONG NOT NULL,
    CreatedOn DATETIME,
    RecommendationType TEXT(50),
    ReasonText TEXT(255),
    RelatedExerciseID LONG
);
