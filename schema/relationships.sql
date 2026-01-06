-- Core Business Relationships
ALTER TABLE MemberMemberships
ADD CONSTRAINT FK_MemberMemberships_Members
FOREIGN KEY (MemberID) REFERENCES Members(MemberID);

ALTER TABLE MemberMemberships
ADD CONSTRAINT FK_MemberMemberships_Plans
FOREIGN KEY (PlanID) REFERENCES MembershipPlans(PlanID);

ALTER TABLE Payments
ADD CONSTRAINT FK_Payments_MemberMemberships
FOREIGN KEY (MemberMembershipID) REFERENCES MemberMemberships(MemberMembershipID);

-- Training Domain Relationships
ALTER TABLE PlanExercises
ADD CONSTRAINT FK_PlanExercises_WorkoutPlans
FOREIGN KEY (PlanTemplateID) REFERENCES WorkoutPlans(PlanTemplateID);

ALTER TABLE PlanExercises
ADD CONSTRAINT FK_PlanExercises_Exercises
FOREIGN KEY (ExerciseID) REFERENCES Exercises(ExerciseID);

ALTER TABLE TrainingSessions
ADD CONSTRAINT FK_Sessions_Members
FOREIGN KEY (MemberID) REFERENCES Members(MemberID);

ALTER TABLE SessionExercises
ADD CONSTRAINT FK_SessionExercises_Sessions
FOREIGN KEY (SessionID) REFERENCES TrainingSessions(SessionID);

ALTER TABLE SessionExercises
ADD CONSTRAINT FK_SessionExercises_Exercises
FOREIGN KEY (ExerciseID) REFERENCES Exercises(ExerciseID);

ALTER TABLE SetLogs
ADD CONSTRAINT FK_SetLogs_SessionExercises
FOREIGN KEY (SessionExerciseID) REFERENCES SessionExercises(SessionExerciseID);

-- Progress Domain Relationships
ALTER TABLE BodyMetrics
ADD CONSTRAINT FK_BodyMetrics_Members
FOREIGN KEY (MemberID) REFERENCES Members(MemberID);

ALTER TABLE Goals
ADD CONSTRAINT FK_Goals_Members
FOREIGN KEY (MemberID) REFERENCES Members(MemberID);

ALTER TABLE Recommendations
ADD CONSTRAINT FK_Recommendations_Members
FOREIGN KEY (MemberID) REFERENCES Members(MemberID);

ALTER TABLE Recommendations
ADD CONSTRAINT FK_Recommendations_Exercises
FOREIGN KEY (RelatedExerciseID) REFERENCES Exercises(ExerciseID);
