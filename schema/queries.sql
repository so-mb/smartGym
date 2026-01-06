-- Query 1: Active Members with Current Plan and Last Payment Date
CREATE VIEW ActiveMembersWithPlan AS
SELECT 
    m.MemberID,
    m.FirstName,
    m.LastName,
    m.Email,
    mp.PlanName,
    mm.StartDate,
    mm.EndDate,
    MAX(p.PaidOn) AS LastPaymentDate
FROM Members m
INNER JOIN MemberMemberships mm ON m.MemberID = mm.MemberID
INNER JOIN MembershipPlans mp ON mm.PlanID = mp.PlanID
LEFT JOIN Payments p ON mm.MemberMembershipID = p.MemberMembershipID
WHERE m.Status = 'Active' AND mm.Status = 'Active'
GROUP BY m.MemberID, m.FirstName, m.LastName, m.Email, mp.PlanName, mm.StartDate, mm.EndDate;

-- Query 2: Monthly Revenue by Plan
CREATE VIEW MonthlyRevenueByPlan AS
SELECT 
    mp.PlanName,
    Year(p.PaidOn) AS PaymentYear,
    Month(p.PaidOn) AS PaymentMonth,
    SUM(p.Amount) AS TotalRevenue,
    COUNT(p.PaymentID) AS PaymentCount
FROM Payments p
INNER JOIN MemberMemberships mm ON p.MemberMembershipID = mm.MemberMembershipID
INNER JOIN MembershipPlans mp ON mm.PlanID = mp.PlanID
WHERE p.Status = 'Paid'
GROUP BY mp.PlanName, Year(p.PaidOn), Month(p.PaidOn);

-- Query 3: Members with Expiring Memberships in Next 14 Days
CREATE VIEW ExpiringMemberships AS
SELECT 
    m.MemberID,
    m.FirstName,
    m.LastName,
    m.Email,
    mp.PlanName,
    mm.EndDate,
    DateDiff('d', Date(), mm.EndDate) AS DaysUntilExpiry
FROM Members m
INNER JOIN MemberMemberships mm ON m.MemberID = mm.MemberID
INNER JOIN MembershipPlans mp ON mm.PlanID = mp.PlanID
WHERE mm.Status = 'Active' 
    AND mm.EndDate BETWEEN Date() AND DateAdd('d', 14, Date());

-- Query 4: Most Popular Exercises (by set logs count)
CREATE VIEW ExercisePopularity AS
SELECT 
    e.ExerciseID,
    e.Name,
    e.MuscleGroup,
    COUNT(sl.SetLogID) AS TotalSets,
    COUNT(DISTINCT se.SessionID) AS SessionCount,
    COUNT(DISTINCT se.SessionExerciseID) AS ExerciseInstanceCount
FROM Exercises e
INNER JOIN SessionExercises se ON e.ExerciseID = se.ExerciseID
INNER JOIN SetLogs sl ON se.SessionExerciseID = sl.SessionExerciseID
GROUP BY e.ExerciseID, e.Name, e.MuscleGroup
ORDER BY TotalSets DESC;

-- Query 5: PR Leaderboard - Highest Weight by Exercise This Month
CREATE VIEW PRLeaderboard AS
SELECT 
    m.MemberID,
    m.FirstName,
    m.LastName,
    e.Name AS ExerciseName,
    MAX(sl.WeightKg) AS MaxWeight,
    sl.Reps,
    ts.SessionDateTime
FROM Members m
INNER JOIN TrainingSessions ts ON m.MemberID = ts.MemberID
INNER JOIN SessionExercises se ON ts.SessionID = se.SessionID
INNER JOIN Exercises e ON se.ExerciseID = e.ExerciseID
INNER JOIN SetLogs sl ON se.SessionExerciseID = sl.SessionExerciseID
WHERE sl.IsPR = True
    AND Year(ts.SessionDateTime) = Year(Date())
    AND Month(ts.SessionDateTime) = Month(Date())
GROUP BY m.MemberID, m.FirstName, m.LastName, e.Name, sl.Reps, ts.SessionDateTime
ORDER BY MaxWeight DESC;

-- Query 6: Training Consistency - Sessions Per Member Per Week
CREATE VIEW TrainingConsistency AS
SELECT 
    m.MemberID,
    m.FirstName,
    m.LastName,
    COUNT(ts.SessionID) AS TotalSessions,
    COUNT(ts.SessionID) / (DateDiff('ww', m.JoinDate, Date()) + 1) AS AvgSessionsPerWeek,
    MAX(ts.SessionDateTime) AS LastSessionDate
FROM Members m
LEFT JOIN TrainingSessions ts ON m.MemberID = ts.MemberID
WHERE m.Status = 'Active'
GROUP BY m.MemberID, m.FirstName, m.LastName, m.JoinDate
ORDER BY AvgSessionsPerWeek DESC;

-- Query 7: Progress Tracking - Body Metrics Over Time
-- Note: Access doesn't support LAG(), so this shows all metrics with calculated differences
CREATE VIEW BodyMetricsProgress AS
SELECT 
    m.MemberID,
    m.FirstName,
    m.LastName,
    bm.MeasuredOn,
    bm.WeightKg,
    bm.BodyFatPct,
    bm.ChestCm,
    bm.WaistCm,
    bm.HipCm,
    (SELECT TOP 1 WeightKg FROM BodyMetrics bm2 
     WHERE bm2.MemberID = bm.MemberID AND bm2.MeasuredOn < bm.MeasuredOn 
     ORDER BY bm2.MeasuredOn DESC) AS PreviousWeight,
    bm.WeightKg - (SELECT TOP 1 WeightKg FROM BodyMetrics bm2 
                   WHERE bm2.MemberID = bm.MemberID AND bm2.MeasuredOn < bm.MeasuredOn 
                   ORDER BY bm2.MeasuredOn DESC) AS WeightChange
FROM Members m
INNER JOIN BodyMetrics bm ON m.MemberID = bm.MemberID
ORDER BY m.MemberID, bm.MeasuredOn DESC;

-- Query 8: Active Recommendations Summary
CREATE VIEW ActiveRecommendations AS
SELECT 
    m.MemberID,
    m.FirstName,
    m.LastName,
    r.RecommendationType,
    r.ReasonText,
    e.Name AS RelatedExercise,
    r.CreatedOn
FROM Members m
INNER JOIN Recommendations r ON m.MemberID = r.MemberID
LEFT JOIN Exercises e ON r.RelatedExerciseID = e.ExerciseID
WHERE r.CreatedOn >= DateAdd('d', -30, Date())
ORDER BY r.CreatedOn DESC;

-- Query 9: Member Goals Progress
CREATE VIEW GoalsProgress AS
SELECT 
    m.MemberID,
    m.FirstName,
    m.LastName,
    g.GoalType,
    g.TargetValue,
    g.StartDate,
    g.TargetDate,
    g.Status,
    IIf(g.GoalType = 'WeightLoss', 
        (SELECT TOP 1 WeightKg FROM BodyMetrics WHERE MemberID = m.MemberID ORDER BY MeasuredOn DESC),
        NULL) AS CurrentValue,
    DateDiff('d', Date(), g.TargetDate) AS DaysRemaining
FROM Members m
INNER JOIN Goals g ON m.MemberID = g.MemberID
WHERE g.Status = 'Active'
ORDER BY g.TargetDate;
