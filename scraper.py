"""
Scraper Google News avec deep scraping
Version refactorisée avec logging structuré et configuration centralisée
"""
import asyncio
import random
from playwright.async_api import async_playwright
import requests
import urllib.parse
from keywords import MOTS_CLES_NIGER
from logger import setup_logger
from config import (
    API_URL, SCRAPER_HEADLESS, SCRAPER_TIMEOUT,
    ARTICLE_TIMEOUT, USER_AGENT, MAX_ARTICLES_PER_KEYWORD
)
import os

logger = setup_logger(__name__)

async def random_sleep(min_s=3, max_s=7):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def scrape_platform():
    async with async_playwright() as p:
        try:
            # Lancement du navigateur
            browser = await p.chromium.launch(headless=SCRAPER_HEADLESS)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()
            
            logger.info(f"Scraper démarré (headless={SCRAPER_HEADLESS})")
            
            # Gestion des cookies
            try:
                consent_button = await page.query_selector(
                    'button:has-text("Tout accepter"), button:has-text("J\'accepte"), button:has-text("Accept all")'
                )
                if consent_button:
                    await consent_button.click()
                    await random_sleep(1, 2)
                    logger.debug("Bannière cookies acceptée")
            except Exception as e:
                logger.debug(f"Pas de bannière cookies: {e}")
            
            # Collecte sur TOUS les mots-clés
            for keyword in MOTS_CLES_NIGER:
                logger.info(f"Recherche: {keyword}")
                
                try:
                    await page.goto(
                        f"https://www.google.com/search?q={keyword}&tbm=nws",
                        timeout=SCRAPER_TIMEOUT
                    )
                except Exception as e:
                    logger.error(f"Erreur navigation pour '{keyword}': {e}")
                    continue
                
                await random_sleep(2, 4)
                
                # Scroll
                for _ in range(2):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await random_sleep(1, 2)
                
                # Stratégies de sélection
                selector_strategies = [
                    {
                        "container": "div.Gx5Zad.xpd",
                        "title": "div.UFvD1, h3",
                        "link": "a",
                        "source": "div.BamJPe, div.XR4uSe"
                    },
                    {
                        "container": "div.SoaBEf, div.NiLAwe, article",
                        "title": "h3, div[role='heading']",
                        "link": "a",
                        "source": ".NUnG9d, .MgUUmf, span"
                    },
                    {
                        "container": "div.g",
                        "title": "h3",
                        "link": "a",
                        "source": "span"
                    }
                ]
                
                articles = []
                strategy_used = None
                
                for strategy in selector_strategies:
                    found = await page.query_selector_all(strategy["container"])
                    if len(found) > 0:
                        articles = found
                        strategy_used = strategy
                        logger.debug(f"Stratégie: {strategy['container']} ({len(articles)} éléments)")
                        break
                
                if not articles:
                    logger.warning(f"Aucun article trouvé pour '{keyword}'")
                    await page.screenshot(path="debug_scraper_failed.png")
                    content = await page.content()
                    with open("debug_page.html", "w", encoding="utf-8") as f:
                        f.write(content)
                    continue
                
                seen_urls = set()
                valid_links = []
                
                for article in articles:
                    try:
                        link_el = await article.query_selector("a")
                        if not link_el:
                            continue
                        raw_link = await link_el.get_attribute("href")
                        if not raw_link:
                            continue
                        
                        real_link = ""
                        if "/url?" in raw_link:
                            try:
                                parsed = urllib.parse.urlparse(raw_link)
                                qp = urllib.parse.parse_qs(parsed.query)
                                if 'q' in qp:
                                    real_link = qp['q'][0]
                                elif 'url' in qp:
                                    real_link = qp['url'][0]
                            except Exception as e:
                                logger.debug(f"Erreur parsing URL: {e}")
                                continue
                        elif raw_link.startswith("http"):
                            real_link = raw_link
                        
                        if real_link and "google.com" not in real_link and real_link not in seen_urls:
                            seen_urls.add(real_link)
                            
                            # Métadonnées
                            title = "Titre Inconnu"
                            if strategy_used.get("title"):
                                t_el = await article.query_selector(strategy_used["title"])
                                if t_el:
                                    title = await t_el.inner_text()
                            
                            author = "Source Inconnue"
                            if strategy_used.get("source"):
                                a_el = await article.query_selector(strategy_used["source"])
                                if a_el:
                                    author = await a_el.inner_text()
                            
                            valid_links.append({"url": real_link, "title": title, "author": author})
                            
                            # Limiter le nombre d'articles par mot-clé
                            if len(valid_links) >= MAX_ARTICLES_PER_KEYWORD:
                                break
                    
                    except Exception as e:
                        logger.debug(f"Erreur extraction lien: {e}")
                        continue
                
                logger.info(f"Liens extraits: {len(valid_links)} pour '{keyword}'")
                
                # Deep Scraping
                for item in valid_links:
                    logger.debug(f"Visite: {item['title'][:40]}...")
                    page_article = await context.new_page()
                    try:
                        await page_article.goto(item['url'], timeout=ARTICLE_TIMEOUT)
                        
                        # Extraction contenu
                        content_text = ""
                        paragraphs = await page_article.query_selector_all("p")
                        for p in paragraphs:
                            txt = await p.inner_text()
                            if len(txt) > 50:
                                content_text += txt + "\n\n"
                        
                        if len(content_text) < 100:
                            body = await page_article.query_selector("body")
                            if body:
                                content_text = await body.inner_text()
                        
                        # Sauvegarde
                        final_content = content_text[:4000] if content_text else item['title']
                        
                        post_data = {
                            "platform": "Google News (Deep)",
                            "author": item['author'][:50],
                            "content": f"{item['title']}\n\n{final_content}",
                            "media_type": "Article",
                            "url": item['url']
                        }
                        
                        try:
                            response = requests.post(API_URL, json=post_data, timeout=5)
                            response.raise_for_status()
                            logger.info(f"Article sauvegardé: {item['title'][:30]}...")
                        except requests.exceptions.RequestException as e:
                            logger.error(f"Erreur API: {e}")
                    
                    except Exception as e:
                        logger.warning(f"Erreur visite article: {e}")
                    finally:
                        await page_article.close()
                        await random_sleep(1, 3)
            
            await browser.close()
            logger.info("Scraping terminé avec succès")
        
        except Exception as e:
            logger.error(f"Erreur critique scraper: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    # Récupérer l'intervalle de scraping (en minutes) depuis l'environnement
    # Si non défini, tourne une seule fois
    interval_min = os.getenv("SCRAPER_INTERVAL")
    
    try:
        if interval_min:
            interval_sec = int(interval_min) * 60
            logger.info(f"Mode boucle activé: Scraping toutes les {interval_min} minutes")
            while True:
                asyncio.run(scrape_platform())
                logger.info(f"Attente de {interval_min} minutes avant la prochaine collecte...")
                import time
                time.sleep(interval_sec)
        else:
            asyncio.run(scrape_platform())
    except KeyboardInterrupt:
        logger.info("Scraper arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
