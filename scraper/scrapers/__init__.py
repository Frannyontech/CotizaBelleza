# Scrapers submodule

# DBS Scraper
from .dbs_selenium_scraper import (
    DBSProduct,
    DBSSeleniumScraper,
    scrapear_todas_categorias as scrapear_todas_categorias_dbs
)

# Preunic Scraper
from .preunic_selenium_scraper import (
    scrape_all_categories
)

# Maicao Scraper
from .maicao_selenium_scraper import (
    MaicaoProduct,
    MaicaoSeleniumScraper,
    scrape_maicao_all_categories
)

__all__ = [
    "DBSProduct",
    "DBSSeleniumScraper", 
    "scrapear_todas_categorias_dbs",
    "scrape_all_categories",
    "MaicaoProduct",
    "MaicaoSeleniumScraper",
    "scrape_maicao_all_categories"
]
