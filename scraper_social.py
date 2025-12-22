"""
Scraper avancé pour les réseaux sociaux (Twitter/X, Facebook, Instagram, LinkedIn)
Utilise des techniques de contournement pour accéder aux contenus publics sans authentification
"""
import asyncio
import random
from playwright.async_api import async_playwright
import requests
from keywords import MOTS_CLES_NIGER
import json
from config import API_URL
from logger import setup_logger

logger = setup_logger(__name__)

async def random_sleep(min_s=2, max_s=5):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def scrape_twitter():
    """
    Twitter/X - Utilise Nitter (frontend alternatif open-source) pour contourner l'authentification
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # Instances Nitter publiques (miroirs de Twitter sans auth)
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.poast.org",
            "https://nitter.privacydev.net"
        ]

        for keyword in MOTS_CLES_NIGER[:10]:  # 10 premiers mots-clés
            logger.info(f"Twitter (via Nitter) - Recherche: {keyword}")
            
            for nitter_url in nitter_instances:
                try:
                    search_url = f"{nitter_url}/search?f=tweets&q={keyword}"
                    await page.goto(search_url, timeout=30000)
                    await random_sleep(2, 4)

                    # Sélecteurs Nitter (plus stables que Twitter direct)
                    tweets = await page.query_selector_all('.timeline-item')
                    
                    if len(tweets) > 0:
                        logger.info(f"{len(tweets)} tweets trouvés via {nitter_url}")
                        
                        for tweet in tweets[:5]:
                            try:
                                # Texte du tweet
                                text_el = await tweet.query_selector('.tweet-content')
                                text = await text_el.inner_text() if text_el else ""
                                
                                # Auteur
                                author_el = await tweet.query_selector('.fullname')
                                author = await author_el.inner_text() if author_el else "Twitter User"
                                
                                # Lien
                                link_el = await tweet.query_selector('.tweet-link')
                                link = await link_el.get_attribute("href") if link_el else ""
                                if link and not link.startswith("http"):
                                    link = f"{nitter_url}{link}"

                                if text and len(text) > 20:
                                    post_data = {
                                        "platform": "Twitter/X",
                                        "author": author[:100],
                                        "content": text[:4000],
                                        "media_type": "Tweet",
                                        "url": link
                                    }
                                    requests.post(API_URL, json=post_data)
                                    logger.info(f"Tweet sauvegardé: {text[:60]}...")
                            
                            except Exception as e:
                                continue
                        
                        break  # Instance fonctionnelle trouvée
                    
                except Exception as e:
                    logger.warning(f"{nitter_url} indisponible: {e}")
                    continue
            
            await random_sleep(5, 10)

        await browser.close()

async def scrape_instagram():
    """
    Instagram - Utilise Bibliogram/Imginn (frontends alternatifs) et recherche publique
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # Hashtags Instagram à surveiller
        hashtags = ["Niger", "Niamey", "AES", "CNSP", "SahelAES"]

        for hashtag in hashtags:
            logger.info(f"Instagram - Hashtag: #{hashtag}")
            
            try:
                # Imginn.com - Viewer Instagram public
                search_url = f"https://imginn.com/tag/{hashtag}/"
                await page.goto(search_url, timeout=30000)
                await random_sleep(3, 5)

                # Scroll pour charger le contenu
                for _ in range(2):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await random_sleep(2, 3)

                # Sélecteurs Imginn
                posts = await page.query_selector_all('.post-item, .photo')
                
                logger.info(f"Trouvé {len(posts)} posts Instagram")
                
                for post in posts[:5]:
                    try:
                        # Clic pour ouvrir le post
                        await post.click()
                        await random_sleep(1, 2)
                        
                        # Extraction du texte
                        caption_el = await page.query_selector('.photo-description, .caption')
                        caption = await caption_el.inner_text() if caption_el else ""
                        
                        # Auteur
                        author_el = await page.query_selector('.username, .author')
                        author = await author_el.inner_text() if author_el else "Instagram User"
                        
                        # Lien
                        link = page.url

                        if caption and len(caption) > 10:
                            post_data = {
                                "platform": "Instagram",
                                "author": author[:100],
                                "content": f"#{hashtag}\n\n{caption[:4000]}",
                                "media_type": "Post",
                                "url": link
                            }
                            requests.post(API_URL, json=post_data)
                            logger.info(f"Post Instagram sauvegardé: {caption[:60]}...")
                        
                        # Retour à la liste
                        await page.go_back()
                        await random_sleep(1, 2)
                    
                    except Exception as e:
                        continue
                
                await random_sleep(5, 10)
                
            except Exception as e:
                logger.error(f"Erreur Instagram pour #{hashtag}: {e}")
                continue

        await browser.close()

async def scrape_linkedin():
    """
    LinkedIn - Utilise Google Search pour trouver des posts publics LinkedIn
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        for keyword in MOTS_CLES_NIGER[:10]:
            logger.info(f"LinkedIn - Recherche: {keyword}")
            
            try:
                # Google Search avec site:linkedin.com pour trouver des posts publics
                search_query = f"site:linkedin.com/posts {keyword}"
                await page.goto(f"https://www.google.com/search?q={search_query}", timeout=30000)
                await random_sleep(2, 4)

                # Extraction des liens LinkedIn depuis les résultats Google
                results = await page.query_selector_all('div.g')
                
                linkedin_urls = []
                for result in results[:5]:
                    try:
                        link_el = await result.query_selector('a')
                        link = await link_el.get_attribute("href") if link_el else ""
                        
                        if "linkedin.com" in link and "/posts/" in link:
                            linkedin_urls.append(link)
                    except:
                        continue

                logger.info(f"Trouvé {len(linkedin_urls)} posts LinkedIn")

                # Visite de chaque post LinkedIn
                for url in linkedin_urls:
                    try:
                        linkedin_page = await context.new_page()
                        await linkedin_page.goto(url, timeout=20000)
                        await random_sleep(2, 3)

                        # Extraction du contenu (sélecteurs pour posts publics)
                        content_el = await linkedin_page.query_selector('.feed-shared-text, .attributed-text-segment-list__content')
                        content = await content_el.inner_text() if content_el else ""
                        
                        # Auteur
                        author_el = await linkedin_page.query_selector('.feed-shared-actor__name, .update-components-actor__name')
                        author = await author_el.inner_text() if author_el else "LinkedIn User"

                        if content and len(content) > 20:
                            post_data = {
                                "platform": "LinkedIn",
                                "author": author[:100],
                                "content": content[:4000],
                                "media_type": "Post",
                                "url": url
                            }
                            requests.post(API_URL, json=post_data)
                            logger.info(f"Post LinkedIn sauvegardé: {content[:60]}...")
                        
                        await linkedin_page.close()
                        await random_sleep(3, 5)
                    
                    except Exception as e:
                        logger.warning(f"Erreur visite post LinkedIn: {e}")
                        continue
                
                await random_sleep(10, 15)
                
            except Exception as e:
                logger.error(f"Erreur LinkedIn pour '{keyword}': {e}")
                continue

        await browser.close()

async def scrape_facebook():
    """
    Facebook - Utilise des pages publiques et recherche Google
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # Pages Facebook publiques Niger à surveiller
        public_pages = [
            "https://m.facebook.com/public?query=Niger",
            "https://m.facebook.com/public?query=CNSP",
            "https://m.facebook.com/public?query=AES%20Sahel"
        ]

        for search_url in public_pages:
            query = search_url.split('query=')[1].replace('%20', ' ')
            logger.info(f"Facebook - Recherche: {query}")
            
            try:
                # Version mobile (m.facebook.com) plus accessible
                await page.goto(search_url, timeout=30000)
                await random_sleep(3, 5)

                # Scroll
                for _ in range(2):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await random_sleep(2, 3)

                # Sélecteurs mobile Facebook
                posts = await page.query_selector_all('article, div[data-ft]')
                
                logger.info(f"Trouvé {len(posts)} posts Facebook")
                
                for post in posts[:3]:
                    try:
                        # Texte
                        text_el = await post.query_selector('p, div[data-ft] span')
                        text = await text_el.inner_text() if text_el else ""
                        
                        if text and len(text) > 20:
                            post_data = {
                                "platform": "Facebook",
                                "author": f"Page Publique - {query}",
                                "content": text[:4000],
                                "media_type": "Post",
                                "url": search_url
                            }
                            requests.post(API_URL, json=post_data)
                            logger.info(f"Post Facebook sauvegardé: {text[:60]}...")
                    
                    except Exception as e:
                        continue
                
                await random_sleep(5, 10)
                
            except Exception as e:
                logger.error(f"Erreur Facebook: {e}")
                continue

        await browser.close()

async def main():
    """
    Exécute le scraping complet des 4 réseaux sociaux
    """
    logger.info("=" * 70)
    logger.info("SCRAPING RÉSEAUX SOCIAUX COMPLET - VEILLE NIGER")
    logger.info("=" * 70)
    
    # Twitter (via Nitter)
    logger.info("Démarrage scraping Twitter (via Nitter)...")
    try:
        await scrape_twitter()
    except Exception as e:
        logger.error(f"Erreur globale Twitter: {e}", exc_info=True)
    
    # Instagram (via Imginn)
    logger.info("Démarrage scraping Instagram...")
    try:
        await scrape_instagram()
    except Exception as e:
        logger.error(f"Erreur globale Instagram: {e}", exc_info=True)
    
    # LinkedIn (via Google Search)
    logger.info("Démarrage scraping LinkedIn...")
    try:
        await scrape_linkedin()
    except Exception as e:
        logger.error(f"Erreur globale LinkedIn: {e}", exc_info=True)
    
    # Facebook (version mobile)
    logger.info("Démarrage scraping Facebook...")
    try:
        await scrape_facebook()
    except Exception as e:
        logger.error(f"Erreur globale Facebook: {e}", exc_info=True)
    
    logger.info("=" * 70)
    logger.info("Scraping réseaux sociaux terminé")
    logger.info("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
