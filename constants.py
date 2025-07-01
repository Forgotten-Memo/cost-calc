CATALYST_PROB_MAP = {
    "No Catalyst": 0.2,
    "Catalyst": 0.24,
    "Stable Catalyst": 0.24,
    "Potent Catalyst": 0.27,
    "3 Star Catalyst": 1,
    "4 Star Catalyst" : 1
}


PROB_CATALYST_MAP = {
    v: k for k, v in CATALYST_PROB_MAP.items()
}

TAP_COST = {
    15: 150000,
    16: 160000,
    17: 180000,
    18: 200000,
    19: 220000,
    20: 240000,
    21: 260000,
    22: 450000,
    23: 850000,
    24: 1250000
}


CATALYST_COST_MAP = {
    "No Catalyst": 0,
    "Catalyst": 100,
    "Stable Catalyst": 200,
    "Potent Catalyst": 800,
    "3 Star Catalyst": 8000,
    "4 Star Catalyst": 32000
}

CATALYST_MODIFIERS = {
    "No Catalyst": lambda x: x,
    "Catalyst": lambda x: min(x * 1.5, x + 0.04),
    "Stable Catalyst": lambda x: min(x * 1.5, x + 0.04),
    "Potent Catalyst": lambda x: min(x * 2.0, x + 0.07),
}

FAILSAFES = {
    15: [0.18, 0.22, 0.26, 0.3, 0.4, 0.5, 1],
    16: [0.16, 0.2, 0.25, 0.3, 0.4, 0.5, 1],
    17: [0.14, 0.19, 0.24, 0.3, 0.4, 0.5, 1],
    18: [0.12, 0.18, 0.24, 0.3, 0.4, 0.5, 1],
    19: [0.11, 0.17, 0.23, 0.3, 0.4, 0.5, 1],
    20: [0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 1],
    21: [0.08, 0.13, 0.19, 0.25, 0.35, 0.5, 1],
    22: [0.06, 0.1, 0.15, 0.2, 0.3, 0.5, 1],
    23: [0.04, 0.08, 0.12, 0.18, 0.25, 0.5, 1],
    24: [0.02, 0.04, 0.08, 0.12, 0.25, 0.5, 1]
}


FAILSAFE_TEXT = {
    0: "No Failsafe!",
    1: "Failsafe I",
    2: "Failsafe II",
    3: "Failsafe III",
    4: "Failsafe IV",
    5: "Failsafe V",
    6: "Failsafe VI :("
}