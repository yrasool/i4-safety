"""
Every constant the pipeline shares. Defined once, imported everywhere.

Before this file, YEARS was declared independently in three scripts, the USDOT
cost table in two, the MEP defaults in two, and the Amsterdam weight was a named
constant in one script and a bare literal in another. None of them disagreed
yet. Nothing prevented them from disagreeing after the next edit, and a cost
table updated in one file but not its twin would have produced two different
answers with no error and no warning.
"""

# --- Study period -------------------------------------------------------------
# Crash records span January 2019 through November 2025, and November is itself
# incomplete. Never quote a 2025 total.
FIRST_YEAR = 2019
LAST_YEAR = 2025
YEARS = 6.9

# --- Study area ---------------------------------------------------------------
# FDOT District 7.
COUNTIES = {"057": "Hillsborough", "103": "Pinellas", "101": "Pasco",
            "053": "Hernando", "017": "Citrus"}
STATE_FP = "12"

TRANSIT_AGENCIES = ["Hillsborough Area", "Pinellas Suncoast"]

# --- Crash costs --------------------------------------------------------------
# USDOT Benefit-Cost Analysis Guidance, 2026 Update, Appendix A Table A-1a.
# Value per INJURED PERSON, 2024 dollars. K is the VSL itself.
#
# Correct here because this pipeline's numerator is CASUALTIES. FHWA-SA-25-021
# values attach to a CRASH and must not be used with person counts - pairing
# them was one third of an error that compounded to 8x.
COST_PER_PERSON = {"K": 13_700_000, "A": 1_302_300, "B": 256_300,
                   "C": 122_400, "O": 5_500}

# FHWA-SA-25-021 comprehensive cost PER CRASH, 2024 dollars. Kept for reference
# and sensitivity only. Do NOT apply to casualty counts.
COST_PER_CRASH = {"K": 15_988_000, "A": 1_705_100, "B": 384_000,
                  "C": 204_600, "O": 18_100}

# --- Exposure -----------------------------------------------------------------
# FDOT Transportation Data & Analytics, "Public Road Mileage and Miles Traveled
# 2025". Five-county daily VMT, all public roads. Measured.
DVMT_5COUNTY = 102_108_727
VMT_ANNUAL = DVMT_5COUNTY * 365

# Vehicle occupancy, MEASURED from NHTS 2022 microdata by step 17 - person-miles
# over vehicle-miles across driver-reported trips in cars, vans, SUVs and
# pickups. South Atlantic large-MSA cut, 2,091 driver trips. The US figure is
# 1.523 on 20,415 trips, so the regional value is not an artefact of the smaller
# sample.
#
# THIS REPLACES TWO WRONG VALUES, and the second one matters more:
#   1.67   NHTS 2017. Superseded by the survey step 17 already reads for f_k.
#   a fabricated derivation claiming MEP's $0.48/passenger-mile is AAA's
#          $0.796/car-mile divided by 1.67. AAA publishes no $0.796 figure. The
#          reference implementation cites AAA 2018 "Your Driving Costs", whose
#          headline is about 59 cents per VEHICLE-mile, which recovers neither
#          1.5 nor 1.67. MEP's $0.48 cannot be back-solved to an occupancy from
#          anything published, so occupancy is measured instead of inferred.
#
# Occupancy converts FDOT vehicle-miles into the passenger-miles that MEP's cost
# and energy terms are denominated in. Changing it scales r_drive by 1/occupancy.
OCCUPANCY = 1.502

# --- MEP ----------------------------------------------------------------------
# Published defaults. Energy kWh/PMT, cost $/PMT.
#
# SOURCE OF RECORD is FDOT BDV29-977-66 (June 2023) Table 7, "Energy Intensity
# and Cost Values", which is the MEP tool's own default table as used by NREL
# and FIU. This settles a value that was ambiguous across secondary sources:
# transit cost is 0.85, not 0.86 and not 1.05.
MEP_DEFAULTS = {"drive":      {"e": 0.90, "c": 0.48},
                "transit":    {"e": 0.65, "c": 0.85},
                "bike":       {"e": 0.00, "c": 0.00},
                "walk":       {"e": 0.00, "c": 0.00},
                "tnc":        {"e": 1.80, "c": 1.54},
                "paratransit":{"e": 4.13, "c": 2.25}}

# Weighting factors from the MEP formulation. Beta (time) is unused here: SLD
# publishes one 45-minute threshold for both modes, so exp(beta*t) factors out
# of every before/after comparison. If the surface is ever rebuilt on MEP's own
# 10/20/30/40 bands, that cancellation fails and beta comes back.
ALPHA = -0.5      # energy
BETA = -0.08      # time
GAMMA = -0.5      # cost

# [CHOICE] A dollar of injury is a dollar of cost, so it takes the weight the
# metric already gives to dollars. Requires no new evidence.
DELTA_BASE = -0.5

# Asadi et al. (2025), from Mouter et al. (2017): people trade time against
# casualties very differently reasoning as citizens than as consumers. Dutch,
# with no US equivalent found. Reported as sensitivity, never as the base case.
AMSTERDAM_WEIGHT = 11.32

SCENARIOS = {"base": DELTA_BASE,
             "amsterdam": DELTA_BASE * AMSTERDAM_WEIGHT}

# --- Benchmark ----------------------------------------------------------------
# Cui & Levinson (2019), Twin Cities, JTLU 12(1):649-672, Table 3, "$/veh-km".
#
# THREE MISMATCHES HAVE TO BE CORRECTED BEFORE THIS IS COMPARABLE, and each one
# was found only after a version of this test had already printed PASS:
#
#   UNITS   their figure is per VEHICLE-km; r_drive is per PASSENGER-mile.
#           Multiply by KM_PER_MILE and by OCCUPANCY.
#   DOLLARS their unit costs are Blincoe et al. 2015, in 2010 DOLLARS. This
#           project uses USDOT 2024 dollars. Roughly half of what looked like a
#           Florida safety penalty was currency inflation.
#   SCOPE   their internal/external split is precisely this project's occupant
#           vs non-motorist split - "crash cost borne by involved travellers"
#           against "collisions that injure or kill non-motorists". So each of
#           the project's two specifications has its own matched comparator, and
#           neither may be compared against the wrong one.
# VERIFIED AGAINST THE SOURCE, 2026-09-10. The paper is now on disk at
# data/raw/cui_levinson_2019_full_cost_by_auto.txt. Until then all four
# attributes below were taken on trust from this comment, which an audit
# correctly flagged: this is the project's load-bearing external benchmark and
# nothing had checked it.
#
#   VALUE   Table 3, "($/veh-km)", row Internal, column Safety: 0.040 (s.d.
#           0.063). Row External, Safety: 0.023 (s.d. 0.022). Both confirmed
#           verbatim.
#   UNITS   The Table 3 header is literally "($/veh-km)". Per VEHICLE-km, so
#           the conversion to passenger-miles needs both KM_PER_MILE and
#           OCCUPANCY.
#   SEVERITY  Table 2 prices five levels - fatal, incapacitating,
#           non-incapacitating, complaint of pain, property-damage only - and
#           the text says the crash model considers "all types of crashes".
#           So all-KABCO, which is why our K-and-A-only figure is a LOWER bound.
#   DOLLARS Table 2 sources crash cost to Blincoe et al. (2015), whose
#           "Cost per Injuried Person" for a fatality is $9,134,786. That is
#           the 2010-dollar comprehensive cost, and it is the exact number
#           DEFLATOR_2010_2024 divides into. Note their fuel and maintenance
#           costs are 2014 dollars - the paper mixes years across components -
#           but only the SAFETY row is used here, so 2010 is the right basis.
CL_INTERNAL_PER_VEHKM = 0.040        # borne by vehicle occupants, 2010 $
CL_EXTERNAL_PER_VEHKM = 0.023        # inflicted on non-motorists, 2010 $
CL_BLINCOE_FATAL_2010 = 9_134_786    # their Table 2, per injured person
KM_PER_MILE = 1.609344

# Value per death, 13,700,000 / 9,134,786 = 1.4998. CPI-U over the same span
# gives 1.4386. The VSL basis is used because both sides of the comparison are
# dominated by the value of a life rather than by a general price level.
DEFLATOR_2010_2024 = 1.50

CL_INTERNAL_2024_PER_MILE = (CL_INTERNAL_PER_VEHKM * KM_PER_MILE
                             * DEFLATOR_2010_2024)          # 0.0966
CL_FULL_2024_PER_MILE = ((CL_INTERNAL_PER_VEHKM + CL_EXTERNAL_PER_VEHKM)
                         * KM_PER_MILE * DEFLATOR_2010_2024)  # 0.1521

# The old band was 0.5-4.0, which passed the mis-united 1.49x, the unit-fixed
# 2.49x AND the external-inclusive 3.7x alike. A test that cannot fail is not a
# test. Floor 1.2: Florida's fatality rate per VMT is ~1.9-2.0x Minnesota's, so
# below this the exposure or the counts are misaligned. Ceiling 3.0: this
# project prices K and A only while Cui & Levinson price all five KABCO levels,
# which biases the ratio upward by a real but unquantifiable amount.
ACCEPT_LO, ACCEPT_HI = 1.2, 3.0

# --- Crash-caused delay -------------------------------------------------------
# DISABLED. Set to zero, deliberately, and this is the reasoning.
#
# The term added minutes to MEP's time input to represent congestion caused by
# crashes. Its value was (0.39, 0.89) minutes on a 30-minute drive, hardcoded as
# a literal in BOTH 23_mep.py and 26_validate.py, absent from this file, and
# derived by NO script. The chain from TTI's 112.4 million annual hours to 0.39
# minutes existed only as prose in a comment, and TTI's figure is not on disk.
# An audit could get within about 10% of 0.39 by assuming a 15-mile trip, and
# could not reproduce it.
#
# Every other input in this project is either computed by a step or read from a
# pinned file. This was the last one that was neither.
#
# It is dropped rather than repaired because:
#   1. It cost 2.4 points of a 25-point result, so no conclusion rested on it.
#   2. Dropping it also retires the free-flow-speeds argument entirely. That
#      argument was only ever needed to show the delay term was not double
#      counting congestion already inside MEP's travel times. With no delay
#      term there is nothing to double count, and one whole line of attack
#      disappears.
#   3. A number that cannot be reproduced cannot be defended, and defending it
#      was worth less than the 2.4 points it added.
#
# To re-enable: source TTI's Urban Mobility Report figure for Tampa-St
# Petersburg to a file in data/raw/, write a step that derives the minutes from
# it, and set this from that step's output. Do not retype a literal here.
DELAY_MINUTES = (0.0, 0.0)

# --- Population ---------------------------------------------------------------
# SLD TotPop sums to 3,173,134, which is pre-2020 and BELOW the 2020 census
# count for the same five counties. Using it against a 2019-2025 numerator
# overstated cost per resident by 9.3%. Census PEP vintage 2024, July 2022 -
# the study period's midpoint falls in mid-June 2022, so this needs no
# interpolation.
MIDPERIOD_POP = 3_468_871
CENSUS_2020_POP = 3_329_130

# --- Sources ------------------------------------------------------------------
CRASH_CSV = r"C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv"
SLD_LAYER = ("https://geodata.epa.gov/arcgis/rest/services/OA/"
             "SmartLocationDatabase/MapServer/1")
NTD_SERVICE = "https://data.transportation.gov/resource/6y83-7vuw.json"
NTD_SAFETY = "https://data.transportation.gov/resource/9ivb-8ae9.json"
# Passenger miles BY MODE. Required, not preferred: NTD_SERVICE is aggregated by
# agency and carries NO `mode` field at all, so it cannot be filtered to bus.
NTD_PMT_BY_MODE = "https://data.transportation.gov/resource/npsm-38gk.json"

# --- Transit comparison -------------------------------------------------------
# THE TRANSIT SIDE MUST BE FATALITY-ONLY, AND THE DRIVE SIDE MUST MATCH.
#
# All fourteen NTD serious-injury columns are ZERO for Bus and Ferry in every
# year 2014-2026, while non-serious injury columns are richly populated (bus
# rider injuries 22,054 over 2019-2024). Serious injury is a RAIL-ONLY concept
# in NTD, inherited from the State Safety Oversight regime (49 CFR Part 674),
# which covers rail fixed-guideway systems. There is no alternative field.
#
# So a KSI comparison is impossible, not merely awkward. A supplies 47% of the
# drive side's cost, and keeping it while bus structurally cannot have it
# inflated the drive:bus ratio by 1.89x on that basis alone.
FATALITY_ONLY_COMPARISON = True

# Fixed-route bus. This is what HART and PSTA run. Demand Response (DR) and
# Vanpool (VP) are "Other Non-Rail" and are excluded.
BUS_MODES = ["MB", "RB", "CB", "TB", "PB"]

# Traffic collisions only. Security events - assault, homicide, robbery - are
# 57.8% of rider fatalities and 70.0% of rider serious injuries nationally, and
# the drive side counts police-reported traffic crashes only. Pricing crime on
# one side of a comparison and not the other is not a like-for-like rate.
COLLISION_CATEGORIES = ["Non-RGX Collision", "RGX Collision"]

# Numerator and denominator on the identical span.
TRANSIT_SPAN = (2015, 2024)

# Poisson uncertainty on 12 observed bus fatalities. The binding constraint is
# sample size, not method - report the interval, never the point estimate bare.
TRANSIT_K_OBSERVED = 12
TRANSIT_R_CI = (0.000541, 0.001830)

# Savage (2013), Research in Transportation Economics 43:9-22. Bus passengers
# 0.11 fatalities per billion passenger-miles; car and light-truck occupants
# 7.3, a ratio of 66x. This pipeline reproduces 0.1211 on Savage's own basis
# (collisions plus in-vehicle falls) using fifteen-years-newer data.
SAVAGE_BUS_PER_BN_PMT = 0.11
SAVAGE_CAR_PER_BN_PMT = 7.3
USER_AGENT = {"User-Agent": "tampa-mep/1.0 (research)"}

# EPA's no-data sentinel. NOT a value.
NODATA = -99999
