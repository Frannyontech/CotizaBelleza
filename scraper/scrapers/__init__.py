# Scrapers submodule

# DBS Scraper
from .dbs_selenium_scraper import (
    DBSProduct,
    DBSSeleniumScraper,
    scrapear_pagina_dbs,
    scrapear_catalogo_dbs,
    scrapear_todas_categorias as scrapear_todas_categorias_dbs
)

# Preunic Scraper
from .preunic_selenium_scraper import (
    scrape_preunic_list,
    main_scraper_preunic
)

# Maicao Scraper
from .maicao_selenium_scraper import (
    MaicaoProduct,
    MaicaoSeleniumScraper,
    scrape_maicao_all_categories
)

__all__ = [
    'DBSProduct',
    'DBSSeleniumScraper', 
    'scrapear_pagina_dbs',
    'scrapear_catalogo_dbs',
    'scrapear_todas_categorias_dbs',
    'scrape_preunic_list',
    'main_scraper_preunic',
    'MaicaoProduct',
    'MaicaoSeleniumScraper',
    'scrape_maicao_all_categories'
] 