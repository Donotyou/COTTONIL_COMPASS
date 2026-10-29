import os
TABLES_PATH = os.getenv("COTTONIL_TABLES", "../02_TABLES/")  
CATALOG_PATH = os.getenv("COTTONIL_CATALOG", "../01_CATALOG/")
EXCLUDE_OPEX_MARKETING = True   # avoid counting marketing twice (campaigns table is the reference)
RECENT_MONTHS = 3               # window used to compare "now" against the best period
MODEL = "claude-sonnet-5-5"     # model used by the AI assistant
COLORS = ["#3B8FE0", "#F59A3D", "#2EAF94", "#8B6FD6", "#E5648A", "#5C7FA3", "#E0B52E"]
