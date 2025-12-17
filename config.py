# Configuration for the real estate platform

# Columbus, OH Zip Codes (including Franklin and Delaware counties)
COLUMBUS_ZIP_CODES = [
    43004, 43016, 43017, 43026, 43054, 43081, 43082, 43085, 43109, 43110,
    43119, 43123, 43125, 43126, 43137, 43147, 43201, 43202, 43203, 43204,
    43205, 43206, 43207, 43209, 43210, 43211, 43212, 43213, 43214, 43215,
    43216, 43217, 43218, 43219, 43220, 43221, 43222, 43223, 43224, 43227,
    43228, 43229, 43230, 43231, 43232, 43235, 43240
]

# Default settings
DEFAULT_DAYS_BACK = 7
DEFAULT_DOWN_PAYMENT = 20

# API Configuration
API_CONFIG = {
    "apify_enabled": True,
    "parcl_enabled": True,  # Enabled Parcl Labs support
    "rentcast_enabled": False
}
