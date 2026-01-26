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

def clean_google_url(raw_url: str) -> str:
    """Nettoie les URLs de redirection Google (/url?q=...)"""
    if not raw_url:
        return ""
    
    if raw_url.startswith("/url?"):
        try:
            parsed = urllib.parse.urlparse(raw_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            return query_params.get("q", [raw_url])[0]
        except Exception:
            return raw_url
    
    return raw_url

async def random_sleep(min_s=3, max_s=7):
    await asyncio.sleep(random.uniform(min_s, max_s))

def parse_relative_date(date_str: str) -> str:
    """Convertit une date relative (Il y a X heures) en ISO format"""
    if not date_str:
        return None
    
    try:
        now = datetime.now()
        date_str = date_str.lower().strip()
        
        if "il y a" in date_str:
            # Extraction du nombre
            import re
            match = re.search(r'(\d+)', date_str)
            if match:
                val = int(match.group(1))
                if "minute" in date_str:
                    return (now - datetime.timedelta(minutes=val)).isoformat()
                elif "heure" in date_str:
                    return (now - datetime.timedelta(hours=val)).isoformat()
                elif "jour" in date_str:
                    return (now - datetime.timedelta(days=val)).isoformat()
        
        return None
    except Exception as e:
        return None

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
                        f"https://www.google.com/search?q={keyword}&tbm=nws&tbs=qdr:d2",
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
                        "source": "div.BamJPe, div.XR4uSe",
                        "time": "div.Ad0q5d"
                    },
                    {
                        "container": "div.SoaBEf, div.NiLAwe, article",
                        "title": "h3, div[role='heading']",
                        "link": "a",
                        "source": ".NUnG9d, .MgUUmf, span",
                        "time": "div.OSrXXb span, span.WG9Pyb"
                    },
                    {
                        "container": "div.g",
                        "title": "h3",
                        "link": "a",
                        "source": "span",
                        "time": "span.WG9Pyb"
                    },
                    {
                        "container": "a.WlydOe",
                        "title": "div.MBeuO",
                        "source": "div.NUnG9d span",
                        "time": "div.OSrXXb span"
                    },
                    {
                       "container": "div.MjjYud", 
                       "title": "h3", 
                       "source": "div.NUnG9d span",
                       "time": "div.OSrXXb span"
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
                        
                        real_link = clean_google_url(raw_link)
                            
                        if real_link and real_link.startswith("http"):
                            if "google.com" not in real_link and real_link not in seen_urls:
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
                            
                            snippet_date = None
                            if strategy_used.get("time"):
                                t_el = await article.query_selector(strategy_used["time"])
                                if t_el:
                                    raw_date = await t_el.inner_text()
                                    snippet_date = parse_relative_date(raw_date)

                            valid_links.append({"url": real_link, "title": title, "author": author, "snippet_date": snippet_date})
                            
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
                        
                        # Extraction Date de publication
                        pub_date = None
                        try:
                            # 1. Meta tags standards
                            meta_date = await page_article.query_selector("meta[property='article:published_time'], meta[name='date'], meta[name='pubdate']")
                            if meta_date:
                                pub_date = await meta_date.get_attribute("content")
                            
                            # 2. Balise <time>
                            if not pub_date:
                                time_el = await page_article.query_selector("time[datetime]")
                                if time_el:
                                    pub_date = await time_el.get_attribute("datetime")
                            
                            # 3. JSON-LD (Approximation)
                            if not pub_date:
                                script_json = await page_article.query_selector("script[type='application/ld+json']")
                                if script_json:
                                    json_content = await script_json.inner_text()
                                    if "datePublished" in json_content:
                                        import json
                                        try:
                                            data = json.loads(json_content)
                                            # Support structure simple ou graph
                                            if isinstance(data, dict):
                                                pub_date = data.get("datePublished")
                                            elif isinstance(data, list):
                                                for item in data:
                                                    if "datePublished" in item:
                                                        pub_date = item["datePublished"]
                                                        break
                                        except:
                                            pass
                        except Exception as e:
                            logger.debug(f"Erreur extraction date: {e}")

                        # Fallback: Date du snippet Google
                        if not pub_date and item.get("snippet_date"):
                            pub_date = item["snippet_date"]

                        
                        # Sauvegarde
                        final_content = content_text[:4000] if content_text else item['title']
                        
                        post_data = {
                            "platform": "Google News (Deep)",
                            "author": item['author'][:50],
                            "content": f"{item['title']}\n\n{final_content}",
                            "media_type": "Article",
                            "url": item['url'],
                            "publication_date": pub_date
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
            # Take screenshot on failure if possible
            try:
                if 'page' in locals():
                    await page.screenshot(path="logs/scraper_crash.png")
            except:
                pass
            raise
        finally:
             logger.info("Fin du processus de scraping")

async def scrape_platform_thematic(theme: str, config: dict):
    """
    Scraper thématique utilisant les mots-clés spécifiques d'un thème.
    Utilisé par les membres pour un scraping ciblé sur leur thématique.
    
    Args:
        theme: Nom du thème (ex: "Agriculture", "Politique")
        config: Configuration du thème depuis theme_configs.py
    """
    async with async_playwright() as p:
        try:
            # Lancement du navigateur
            browser = await p.chromium.launch(headless=SCRAPER_HEADLESS)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()
            
            keywords = config["keywords"]
            max_articles = config["scraping_params"]["max_articles"]
            
            logger.info(f"🎯 Scraper thématique démarré: {theme}")
            logger.info(f"   Mots-clés à traiter: {len(keywords)}")
            logger.info(f"   Max articles par mot-clé: {max_articles}")
            
            # Gestion des cookies
            try:
                consent_button = await page.query_selector(
                    'button:has-text("Tout accepter"), button:has-text("J\'accepte"), button:has-text("Accept all")'
                )
                if consent_button:
                    await consent_button.click()
                    await random_sleep(1, 2)
            except Exception as e:
                logger.debug(f"Pas de bannière cookies: {e}")
            
            # Collecte sur les mots-clés du thème
            articles_collected = 0
            for keyword in keywords:
                logger.info(f"🔍 Recherche thématique: {keyword}")
                
                try:
                    await page.goto(
                        f"https://www.google.com/search?q={keyword}&tbm=nws&tbs=qdr:d2",
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
                
                # Utiliser les mêmes stratégies de sélection que le scraper global
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
                        break
                
                if not articles:
                    logger.warning(f"Aucun article trouvé pour '{keyword}'")
                    continue
                
                # Traiter les articles (limité par max_articles)
                for i, article in enumerate(articles[:max_articles]):
                    try:
                        title_elem = await article.query_selector(strategy_used["title"])
                        link_elem = await article.query_selector(strategy_used["link"])
                        source_elem = await article.query_selector(strategy_used["source"])
                        
                        if not title_elem or not link_elem:
                            continue
                        
                        title = await title_elem.inner_text()
                        url = await link_elem.get_attribute("href")
                        source = await source_elem.inner_text() if source_elem else "Inconnu"
                        
                        # Envoyer à l'API avec le thème pré-assigné
                        payload = {
                            "platform": "Google News (Deep)",
                            "author": source.strip(),
                            "content": title.strip(),
                            "media_type": "Article",
                            "url": url,
                            "assigned_theme": theme  # Thème pré-assigné
                        }
                        
                        try:
                            response = requests.post(API_URL, json=payload, timeout=10)
                            if response.status_code == 200:
                                articles_collected += 1
                                logger.info(f"✅ [{theme}] Article envoyé: {title[:60]}...")
                            else:
                                logger.warning(f"Erreur API ({response.status_code}): {response.text[:100]}")
                        except Exception as e:
                            logger.error(f"Erreur envoi API: {e}")
                    
                    except Exception as e:
                        logger.warning(f"Erreur traitement article: {e}")
                
                await random_sleep(3, 6)
            
            await browser.close()
            logger.info(f"✅ Scraping thématique terminé: {theme}")
            logger.info(f"   Articles collectés: {articles_collected}")
        
        except Exception as e:
            logger.error(f"Erreur critique scraper thématique: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    import argparse
    
    # Parser pour les arguments en ligne de commande
    parser = argparse.ArgumentParser(description='Scraper Google News pour Veille Niger')
    parser.add_argument('--theme', type=str, help='Scraper un thème spécifique (ex: Agriculture, Politique)')
    parser.add_argument('--all-themes', action='store_true', help='Scraper tous les thèmes séquentiellement')
    parser.add_argument('--interval', type=int, help='Intervalle de scraping en minutes (mode boucle)')
    
    args = parser.parse_args()
    
    # Récupérer l'intervalle depuis args ou environnement
    interval_min = args.interval or os.getenv("SCRAPER_INTERVAL")
    
    try:
        if args.theme:
            # Mode scraping thématique
            from theme_configs import get_theme_config, get_all_themes
            
            config = get_theme_config(args.theme)
            if not config:
                logger.error(f"Thème inconnu: {args.theme}")
                logger.info(f"Thèmes disponibles: {', '.join(get_all_themes())}")
                exit(1)
            
            logger.info(f"🎯 MODE SCRAPING THÉMATIQUE: {args.theme}")
            logger.info(f"   Mots-clés: {len(config['keywords'])}")
            logger.info(f"   Priorité: {config['scraping_params']['priority']}")
            
            # Lancer le scraping avec les mots-clés du thème
            asyncio.run(scrape_platform_thematic(args.theme, config))
            
        elif args.all_themes:
            # Mode scraping de tous les thèmes
            from theme_configs import get_all_themes
            
            themes = get_all_themes()
            logger.info(f"🌍 MODE SCRAPING TOUS LES THÈMES: {len(themes)} thèmes")
            
            for theme in themes:
                logger.info(f"\n{'='*60}")
                logger.info(f"Scraping du thème: {theme}")
                logger.info(f"{'='*60}\n")
                
                config = get_theme_config(theme)
                asyncio.run(scrape_platform_thematic(theme, config))
                
                # Pause entre thèmes
                import time
                time.sleep(30)
            
        elif interval_min:
            # Mode boucle avec scraping global (admin)
            interval_sec = int(interval_min) * 60
            logger.info(f"🔄 MODE BOUCLE GLOBAL (ADMIN): Scraping toutes les {interval_min} minutes")
            while True:
                asyncio.run(scrape_platform())
                logger.info(f"Attente de {interval_min} minutes avant la prochaine collecte...")
                import time
                time.sleep(interval_sec)
        else:
            # Mode scraping global unique (admin)
            logger.info("🌐 MODE SCRAPING GLOBAL (ADMIN)")
            asyncio.run(scrape_platform())
            
    except KeyboardInterrupt:
        logger.info("Scraper arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
