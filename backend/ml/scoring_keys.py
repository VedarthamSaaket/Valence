HEXACO_FACETS = {
    "Honesty-Humility":  ["HSinc", "HFair", "HGree", "HMode"],
    "Emotionality":      ["EFear", "EAnxi", "EDepe", "ESent"],
    "Extraversion":      ["XExpr", "XSoci", "XSocB", "XLive"],
    "Agreeableness":     ["AForg", "AGent", "AFlex", "APati"],
    "Conscientiousness": ["COrga", "CDili", "CPerf", "CPrud"],
    "Openness":          ["OAesA", "OInqu", "OCrea", "OUnco"],
}

HEXACO_REVERSED = {
    "HSinc": [2, 3, 4, 5, 6, 7, 8, 9, 10], "HFair": [6, 7, 8, 9, 10],
    "HGree": [3, 4, 5, 6, 7, 8, 9, 10], "HMode": [5, 6, 7, 8, 9, 10],
    "EFear": [6, 7, 8, 9, 10], "EAnxi": [6, 7, 8, 9, 10], "EDepe": [], "ESent": [6, 7, 8, 9, 10],
    "XExpr": [6, 7, 8, 9, 10], "XSoci": [6, 7, 8, 9, 10], "XSocB": [6, 7, 8, 9, 10], "XLive": [9, 10],
    "AForg": [5, 6, 7, 8, 9, 10], "AGent": [5, 6, 7, 8, 9, 10],
    "AFlex": [3, 4, 5, 6, 7, 8, 9, 10], "APati": [6, 7, 8, 9, 10],
    "COrga": [6, 7, 8, 9, 10], "CDili": [6, 7, 8, 9, 10], "CPerf": [9, 10], "CPrud": [4, 5, 6, 7, 8, 9, 10],
    "OAesA": [6, 7, 8, 9, 10], "OInqu": [7, 8, 9, 10], "OCrea": [7, 8, 9, 10], "OUnco": [6, 7, 8, 9, 10],
}

HEXACO_REVERSED_ITEMS = {f"{facet}{i}" for facet, nums in HEXACO_REVERSED.items() for i in nums}

HSQ_SCALES = {
    "Affiliative":    [1, 5, 9, 13, 17, 21, 25, 29],
    "Self-Enhancing": [2, 6, 10, 14, 18, 22, 26, 30],
    "Aggressive":     [3, 7, 11, 15, 19, 23, 27, 31],
    "Self-Defeating": [4, 8, 12, 16, 20, 24, 28, 32],
}
HSQ_REVERSED = {1, 7, 9, 15, 16, 17, 22, 23, 25, 29, 31}

ECR_AVOIDANCE = list(range(1, 37, 2))
ECR_ANXIETY = list(range(2, 37, 2))
ECR_REVERSED = {3, 15, 19, 22, 25, 27, 29, 31, 33, 35}

AMBI_NEO_FACETS = {
    "Neuroticism": {
        "Anxiety": [(1, -1), (71, 1), (162, 1), (147, 1), (33, 1)],
        "Angry Hostility": [(123, 1), (33, 1), (62, -1), (24, 1), (60, 1)],
        "Depression": [(57, 1), (33, 1), (160, 1), (72, 1), (1, -1)],
        "Self-Consciousness": [(72, 1), (134, 1), (49, 1), (57, 1), (30, 1)],
        "Impulsiveness": [(2, 1), (126, -1), (136, 1), (165, 1), (14, -1)],
        "Vulnerability": [(57, 1), (162, 1), (33, 1), (72, 1), (147, 1)],
    },
    "Extraversion": {
        "Warmth": [(6, 1), (170, 1), (37, -1), (166, 1), (171, -1)],
        "Gregariousness": [(3, 1), (73, 1), (37, -1), (135, -1), (102, -1)],
        "Assertiveness": [(4, 1), (101, 1), (163, 1), (145, -1), (21, -1)],
        "Activity": [(5, 1), (22, 1), (31, -1), (101, 1), (163, 1)],
        "Excitement-Seeking": [(44, 1), (46, 1), (106, 1), (79, -1), (73, 1)],
        "Positive Emotions": [(6, 1), (99, 1), (123, -1), (133, 1), (37, -1)],
    },
    "Openness": {
        "Fantasy": [(74, -1), (138, -1), (142, 1), (115, 1), (59, -1)],
        "Aesthetics": [(7, -1), (75, 1), (109, 1), (26, -1), (27, 1)],
        "Feelings": [(19, 1), (85, -1), (179, 1), (150, -1), (148, 1)],
        "Actions": [(42, -1), (27, 1), (94, 1), (92, 1), (138, -1)],
        "Ideas": [(110, 1), (139, -1), (161, -1), (68, 1), (100, -1)],
        "Values": [(76, 1), (54, -1), (59, -1), (156, -1), (98, 1)],
    },
    "Agreeableness": {
        "Trust": [(8, -1), (123, -1), (160, -1), (166, 1), (125, -1)],
        "Straightforwardness": [(9, -1), (52, -1), (86, -1), (51, -1), (46, -1)],
        "Altruism": [(10, 1), (111, 1), (123, -1), (65, -1), (166, 1)],
        "Compliance": [(104, 1), (172, -1), (178, -1), (65, -1), (34, -1)],
        "Modesty": [(11, -1), (118, -1), (120, -1), (38, -1), (176, 1)],
        "Tender-Mindedness": [(12, 1), (77, 1), (111, 1), (114, 1), (177, 1)],
    },
    "Conscientiousness": {
        "Competence": [(167, 1), (57, -1), (116, -1), (137, 1), (101, 1)],
        "Order": [(13, 1), (112, 1), (90, -1), (14, 1), (137, 1)],
        "Dutifulness": [(151, -1), (14, 1), (45, -1), (41, 1), (116, -1)],
        "Achievement Striving": [(25, 1), (14, 1), (4, 1), (48, 1), (145, -1)],
        "Self-Discipline": [(14, 1), (116, -1), (152, -1), (81, 1), (167, 1)],
        "Deliberation": [(15, -1), (35, -1), (136, -1), (41, 1), (141, 1)],
    },
}
