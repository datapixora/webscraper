"""
BidFax connector service for discovering and scraping vehicle listings.

Dedicated service for BidFax.info with full control over:
- Multi-page discovery (10 listings per page)
- Custom parsing for BidFax HTML structure
- Progress tracking
- CSV export
"""
import asyncio
import csv
import io
import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from app.scraper import scrape_url_with_settings

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


class BidFaxVehicle:
    """Represents a parsed BidFax vehicle listing."""

    def __init__(self, data: dict[str, Any]):
        self.url = data.get("url", "")
        self.image_url = data.get("image_url", "")
        self.price = data.get("price")
        self.title = data.get("title", "")
        self.vin = data.get("vin", "")
        self.auction = data.get("auction", "")
        self.location = data.get("location", "")
        self.lot_number = data.get("lot_number", "")
        self.condition = data.get("condition", "")
        self.damage = data.get("damage", "")
        self.mileage = data.get("mileage", "")
        self.date_of_sale = data.get("date_of_sale", "")
        self.status = data.get("status", "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "image_url": self.image_url,
            "price": self.price,
            "title": self.title,
            "vin": self.vin,
            "auction": self.auction,
            "location": self.location,
            "lot_number": self.lot_number,
            "condition": self.condition,
            "damage": self.damage,
            "mileage": self.mileage,
            "date_of_sale": self.date_of_sale,
            "status": self.status,
        }


class BidFaxConnector:
    """Service for BidFax vehicle discovery and scraping."""

    @staticmethod
    def _build_page_url(base_url: str, page_num: int) -> str:
        """
        Build paginated URL for BidFax.

        Args:
            base_url: Base URL (e.g., https://en.bidfax.info/nissan/)
            page_num: Page number (1-indexed)

        Returns:
            Full URL for the page
        """
        # Remove trailing slash for consistency
        base_url = base_url.rstrip("/")

        if page_num == 1:
            return base_url + "/"
        else:
            return f"{base_url}/page/{page_num}/"

    @staticmethod
    def _extract_listing_urls(html: str, base_url: str) -> list[str]:
        """
        Extract vehicle listing URLs from a BidFax page.

        Args:
            html: Page HTML
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute listing URLs
        """
        soup = BeautifulSoup(html, "html.parser")
        urls = []

        # Find all .offer divs (each contains one vehicle listing)
        offers = soup.find_all("div", class_="offer")

        for offer in offers:
            # Find the <a> tag with the detail URL
            link = offer.find("a", href=True)
            if link:
                href = link["href"]
                # Make absolute URL
                absolute_url = urljoin(base_url, href)
                urls.append(absolute_url)

        return urls

    @staticmethod
    async def discover_listings(
        db: AsyncSession,
        base_url: str,
        max_urls: int = 10,
        job_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Discover vehicle listing URLs from BidFax category pages.

        Args:
            db: Database session
            base_url: Category URL (e.g., https://en.bidfax.info/nissan/)
            max_urls: Maximum number of URLs to discover (0 = all)
            job_id: Optional job ID for proxy sticky sessions

        Returns:
            {
                "urls": [...],
                "count": int,
                "pages_scraped": int,
                "sample_urls": [...]  # First 10 for preview
            }
        """
        found_urls = []
        page_num = 1
        max_pages = 100  # Safety limit

        structured_logger.info(
            "bidfax_discovery_started",
            base_url=base_url,
            max_urls=max_urls,
        )

        while True:
            # Stop if we have enough URLs (unless max_urls=0 meaning "all")
            if max_urls > 0 and len(found_urls) >= max_urls:
                break

            # Stop if we've hit max pages
            if page_num > max_pages:
                structured_logger.warning("bidfax_max_pages_reached", pages=max_pages)
                break

            try:
                # Build page URL
                page_url = BidFaxConnector._build_page_url(base_url, page_num)

                structured_logger.info(
                    "bidfax_scraping_page",
                    page_num=page_num,
                    page_url=page_url,
                    found_so_far=len(found_urls),
                )

                # Scrape the page (uses proxy settings)
                result = await scrape_url_with_settings(
                    url=page_url,
                    db=db,
                    extraction_schema=None,
                    job_id=job_id,
                )

                html = result["raw_html"]

                # Check if blocked
                if result.get("blocked"):
                    structured_logger.error(
                        "bidfax_page_blocked",
                        page_num=page_num,
                        reason=result.get("block_reason"),
                    )
                    break

                # Extract listing URLs from this page
                page_urls = BidFaxConnector._extract_listing_urls(html, page_url)

                if not page_urls:
                    # No more listings found, we've reached the end
                    structured_logger.info("bidfax_no_more_listings", page_num=page_num)
                    break

                found_urls.extend(page_urls)

                # Log progress
                structured_logger.info(
                    "bidfax_page_completed",
                    page_num=page_num,
                    found_on_page=len(page_urls),
                    total_found=len(found_urls),
                )

                page_num += 1

            except Exception as exc:
                structured_logger.error(
                    "bidfax_page_error",
                    page_num=page_num,
                    error=str(exc),
                    exc_info=exc,
                )
                break

        # Trim to max_urls if specified
        if max_urls > 0:
            found_urls = found_urls[:max_urls]

        structured_logger.info(
            "bidfax_discovery_completed",
            total_urls=len(found_urls),
            pages_scraped=page_num - 1,
        )

        return {
            "urls": found_urls,
            "count": len(found_urls),
            "pages_scraped": page_num - 1,
            "sample_urls": found_urls[:10],  # First 10 for preview
        }

    @staticmethod
    def _parse_vehicle_listing(html: str, url: str) -> Optional[BidFaxVehicle]:
        """
        Parse a BidFax vehicle detail page.

        Args:
            html: Page HTML
            url: Page URL

        Returns:
            BidFaxVehicle object or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract data from the page structure
            data = {"url": url}

            # Image URL - find first .xfieldimage
            img_tag = soup.find("img", class_="xfieldimage")
            if img_tag and img_tag.get("src"):
                data["image_url"] = img_tag["src"]

            # Price - .prices span
            price_span = soup.find("span", class_="prices")
            if price_span:
                price_text = price_span.get_text(strip=True)
                # Remove non-digits
                price_digits = re.sub(r"[^\d]", "", price_text)
                if price_digits:
                    data["price"] = int(price_digits)

            # Title - h2 in .caption
            title_tag = soup.find("div", class_="caption")
            if title_tag:
                h2 = title_tag.find("h2")
                if h2:
                    data["title"] = h2.get_text(strip=True)

            # VIN - extract from title (format: "vin: XXXXX")
            if data.get("title"):
                vin_match = re.search(r"vin:\s*([A-Z0-9]+)", data["title"], re.IGNORECASE)
                if vin_match:
                    data["vin"] = vin_match.group(1)

            # Auction - look for .copart or similar
            auction_span = soup.find("span", class_="copart") or soup.find("span", class_="iaai")
            if auction_span:
                data["auction"] = auction_span.get_text(strip=True)

            # Location - .blackfont after "Auction:"
            short_story_tags = soup.find_all("p", class_=["short-story", "short-storyup", "short-story2"])
            for tag in short_story_tags:
                text = tag.get_text(strip=True)

                # Auction location
                if "Auction:" in text:
                    blackfont = tag.find("span", class_="blackfont")
                    if blackfont:
                        data["location"] = blackfont.get_text(strip=True)

                # Lot number
                elif "Lot number:" in text:
                    blackfont = tag.find("span", class_="blackfont")
                    if blackfont:
                        data["lot_number"] = blackfont.get_text(strip=True)

                # Condition
                elif "Condition:" in text:
                    blackfont = tag.find("span", class_="blackfont")
                    if blackfont:
                        data["condition"] = blackfont.get_text(strip=True)

                # Damage
                elif "Damage:" in text:
                    blackfont = tag.find("span", class_="blackfont")
                    if blackfont:
                        data["damage"] = blackfont.get_text(strip=True)

                # Mileage
                elif "Mileage:" in text:
                    blackfont = tag.find("span", class_="blackfont")
                    if blackfont:
                        data["mileage"] = blackfont.get_text(strip=True)

                # Date of sale
                elif "Date of sale:" in text:
                    blackfont = tag.find("span", class_="blackfont")
                    if blackfont:
                        data["date_of_sale"] = blackfont.get_text(strip=True)

            # Status - check for "Sold" badge
            sold_img = soup.find("img", alt="Sold")
            if sold_img:
                data["status"] = "Sold"

            return BidFaxVehicle(data)

        except Exception as exc:
            structured_logger.error("bidfax_parse_error", url=url, error=str(exc), exc_info=exc)
            return None

    @staticmethod
    async def parse_vehicle(
        db: AsyncSession,
        url: str,
        job_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Parse a single BidFax vehicle listing.

        Args:
            db: Database session
            url: Vehicle detail URL
            job_id: Optional job ID for proxy

        Returns:
            Parsed vehicle data dict or None
        """
        try:
            result = await scrape_url_with_settings(
                url=url,
                db=db,
                extraction_schema=None,
                job_id=job_id,
            )

            if result.get("blocked"):
                structured_logger.error("bidfax_vehicle_blocked", url=url)
                return None

            vehicle = BidFaxConnector._parse_vehicle_listing(result["raw_html"], url)
            return vehicle.to_dict() if vehicle else None

        except Exception as exc:
            structured_logger.error("bidfax_vehicle_parse_error", url=url, error=str(exc))
            return None

    @staticmethod
    def generate_csv(vehicles: list[dict[str, Any]]) -> str:
        """
        Generate CSV export of vehicle data.

        Args:
            vehicles: List of vehicle dicts

        Returns:
            CSV string
        """
        if not vehicles:
            return ""

        output = io.StringIO()
        fieldnames = [
            "url",
            "image_url",
            "price",
            "title",
            "vin",
            "auction",
            "location",
            "lot_number",
            "condition",
            "damage",
            "mileage",
            "date_of_sale",
            "status",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for vehicle in vehicles:
            writer.writerow({k: vehicle.get(k, "") for k in fieldnames})

        return output.getvalue()


# Singleton instance
bidfax_connector = BidFaxConnector()
