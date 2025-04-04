-- Optimized query without FTS, adjusted for schema (Code=REAL, no Strength column)
-- ASSUMPTION: Standard B-tree index exists on 'Ncode' (PK). Indices on text fields may help exact matches.
-- NOTE: LIKE '%...%' clauses on text fields remain performance bottlenecks.

WITH SearchResults AS (
    SELECT
        -- Select all necessary columns from the DOT table EXCEPT 'Strength'
        Title as jobTitle, Ncode as NCode, Code as dotCodeReal, -- Renamed Code alias slightly
        Industry as industryDesignation, AltTitles as alternateTitles, CompleteTitle,
        GOE as goe_code, GOENum, GOE1 as goe_title, GOE2, GOE3, WFData, WFDataSig,
        WFPeople, WFPeopleSig, WFThings, WFThingsSig, GEDR, GEDM, GEDL, SVPNum,
        AptGenLearn, AptVerbal, AptNumerical, AptSpacial, AptFormPer, AptClericalPer,
        AptMotor, AptFingerDext, AptManualDext, AptEyeHandCoord, AptColorDisc,
        WField1 as workfield_code, WField1Short as workfield_description, WField2,
        WField2Short, WField3, WField3Short, MPSMS1 as mpsms_code,
        MPSMS1Short as mpsms_description, MPSMS2, MPSMS2Short, MPSMS3, MPSMS3Short,
        Temp1, Temp2, Temp3, Temp4, Temp5, StrengthNum, -- Select StrengthNum
        ClimbingNum, BalancingNum, StoopingNum, KneelingNum, CrouchingNum, CrawlingNum,
        ReachingNum, HandlingNum, FingeringNum, FeelingNum, TalkingNum, HearingNum, TastingNum,
        NearAcuityNum, FarAcuityNum, DepthNum, AccommodationNum, ColorVisionNum, FieldVisionNum,
        WeatherNum, ColdNum, HeatNum, WetNum, NoiseNum, VibrationNum, AtmosphereNum, MovingNum,
        ElectricityNum, HeightNum, RadiationNum, ExplosionNum, ToxicNum, OtherNum,
        Definitions as definition, DocumentNumber, DLU, OccGroup,

        -- Relevance scoring (Removed 'Code = :search_term' comparison)
        CASE
            -- 1. Exact DOT Ncode match (highest priority)
            -- Assumes Ncode is INTEGER in the DOT table
            WHEN Ncode = CAST(REPLACE(REPLACE(:search_term, '.', ''), '-', '') AS INTEGER) THEN 200

            -- 2. Exact title matches
            WHEN Title = :search_term COLLATE NOCASE THEN 100
            WHEN CompleteTitle = :search_term COLLATE NOCASE THEN 90

            -- 3. Partial title matches (Slow - relies on LIKE)
            WHEN Title LIKE '%' || :search_term || '%' COLLATE NOCASE THEN 70
            WHEN CompleteTitle LIKE '%' || :search_term || '%' COLLATE NOCASE THEN 60
            WHEN AltTitles LIKE '%' || :search_term || '%' COLLATE NOCASE THEN 50

            -- 4. No match
            ELSE 0
        END as relevance_score
    FROM DOT -- Assuming table name is DOT
    WHERE
        -- WHERE Clause: Filters based on Ncode exact match or text LIKE searches
        -- Exact Ncode match (can use PK index)
        Ncode = CAST(REPLACE(REPLACE(:search_term, '.', ''), '-', '') AS INTEGER)

        -- Title/Text matches (cannot use standard indices effectively for leading '%')
        OR Title LIKE '%' || :search_term || '%' COLLATE NOCASE
        OR CompleteTitle LIKE '%' || :search_term || '%' COLLATE NOCASE
        OR AltTitles LIKE '%' || :search_term || '%' COLLATE NOCASE
)
SELECT
    * -- Select all columns from the CTE
FROM SearchResults
WHERE relevance_score > 0 -- Filter out non-matches based on the CASE statement
ORDER BY
    relevance_score DESC, -- Best matches first
    jobTitle ASC -- Tie-breaker
LIMIT 1; -- Retrieve only the single most relevant result