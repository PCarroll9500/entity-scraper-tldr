"""
Static configuration: filter criteria for the two opportunity pools, and the
profile blurb used to rank/summarize results with an LLM.

Tune the NAICS codes / keyword lists here as you learn what SAM.gov actually
returns -- these are reasonable starting guesses, not guaranteed-exhaustive.
"""

# --- Job-related pool -------------------------------------------------------
# Radiance Technologies / NASIC / Modeling & Simulation work.
JOB_NAICS_CODES = [
    "541715",  # R&D in Physical, Engineering, and Life Sciences
    "541511",  # Custom Computer Programming Services
    "541512",  # Computer Systems Design Services
    "541330",  # Engineering Services
    "541990",  # All Other Professional, Scientific, and Technical Services
]

JOB_KEYWORDS = [
    "modeling and simulation",
    "M&S",
    "NASIC",
    "National Air and Space Intelligence Center",
    "synthetic environment",
    "digital twin",
    "simulation training",
    "wargaming",
]

# Free-text hint appended to job-pool queries where the API supports it
# (e.g. organization name search). Not a hard filter.
JOB_AGENCY_HINT = "Department of the Air Force"

# --- Hobby / "for funzies" pool ---------------------------------------------
# Hobby software, basic electrical/cabling, and small hauling/transport jobs.
HOBBY_NAICS_CODES = [
    "541511",  # Custom Computer Programming Services
    "238210",  # Electrical Contractors and Other Wiring Installation
    "484110",  # General Freight Trucking, Local
    "484121",  # General Freight Trucking, Long-Distance, Truckload
    "488991",  # Packing and Crating
]

HOBBY_KEYWORDS = [
    "software",
    "electrical",
    "cabling",
    "wiring",
    "hauling",
    "trucking",
    "transportation services",
    "moving services",
    "delivery services",
]

# --- Ranking profile ---------------------------------------------------------
PROFILE_BLURB = (
    "I work at Radiance Technologies in Dayton, Ohio, supporting the National "
    "Air and Space Intelligence Center (NASIC) in Modeling & Simulation. I'm "
    "most interested in M&S, synthetic environments, digital twins, and Air "
    "Force / DoD simulation and training work. I also enjoy hobby software "
    "projects, basic electrical work (terminating/cabling), and small "
    "hauling/transport jobs -- a friend and I have a pickup truck."
)

# --- Search window / limits --------------------------------------------------
LOOKBACK_DAYS = 7          # how many days back to search each run
MAX_RESULTS_PER_QUERY = 100  # SAM.gov API page size per individual query

# --- OpenAI ------------------------------------------------------------------
# Cheap model by default -- this is a small daily summarization job, not a
# reasoning-heavy task. Override via OPENAI_MODEL env var if you want better
# quality and don't mind the extra cost.
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

NUM_JOB_RECOMMENDATIONS = 9
NUM_FUN_RECOMMENDATIONS = 1
