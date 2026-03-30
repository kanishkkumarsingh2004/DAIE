"""
Agent Marketplace Module

Provides functionality to share and discover agent configurations
in a decentralized marketplace. Supports local file-based storage
and P2P discovery via mDNS and DHT.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
import os
import time
import socket
import hashlib

logger = logging.getLogger(__name__)

# Optional imports for mDNS and DHT
try:
    from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf
    MDNS_AVAILABLE = True
except ImportError:
    MDNS_AVAILABLE = False
    logger.warning("zeroconf not installed. mDNS marketplace discovery disabled.")

try:
    from kademlia.network import Server
    DHT_AVAILABLE = True
except ImportError:
    DHT_AVAILABLE = False
    logger.warning("kademlia not installed. DHT marketplace discovery disabled.")


class MarketplaceListing:
    """
    Represents a single agent configuration listing in the marketplace.
    """
    
    def __init__(
        self,
        listing_id: str,
        agent_config: Dict[str, Any],
        publisher_id: str,
        description: str = "",
        tags: List[str] = None,
        version: str = "1.0.0",
        price: float = 0.0,
        license: str = "MIT"
    ):
        self.listing_id = listing_id
        self.agent_config = agent_config
        self.publisher_id = publisher_id
        self.description = description
        self.tags = tags or []
        self.version = version
        self.price = price
        self.license = license
        self.created_at = time.time()
        self.updated_at = time.time()
        self.downloads = 0
        self.rating = 0.0
        self.rating_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert listing to dictionary format"""
        return {
            "listing_id": self.listing_id,
            "agent_config": self.agent_config,
            "publisher_id": self.publisher_id,
            "description": self.description,
            "tags": self.tags,
            "version": self.version,
            "price": self.price,
            "license": self.license,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "downloads": self.downloads,
            "rating": self.rating,
            "rating_count": self.rating_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketplaceListing":
        """Create listing from dictionary format"""
        listing = cls(
            listing_id=data["listing_id"],
            agent_config=data["agent_config"],
            publisher_id=data["publisher_id"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0"),
            price=data.get("price", 0.0),
            license=data.get("license", "MIT")
        )
        listing.created_at = data.get("created_at", time.time())
        listing.updated_at = data.get("updated_at", time.time())
        listing.downloads = data.get("downloads", 0)
        listing.rating = data.get("rating", 0.0)
        listing.rating_count = data.get("rating_count", 0)
        return listing
    
    def update_rating(self, new_rating: float):
        """Update the listing rating with a new review"""
        if new_rating < 0.0 or new_rating > 5.0:
            raise ValueError("Rating must be between 0.0 and 5.0")
        
        total_rating = self.rating * self.rating_count
        self.rating_count += 1
        self.rating = (total_rating + new_rating) / self.rating_count
        self.updated_at = time.time()
    
    def increment_downloads(self):
        """Increment the download counter"""
        self.downloads += 1
        self.updated_at = time.time()


class AgentMarketplace:
    """
    Decentralized Agent Marketplace for sharing and discovering agent configurations.
    
    Provides functionality to publish, discover, and manage agent configurations
    in a decentralized marketplace. Supports local file-based storage and P2P
    discovery via mDNS for local networks and DHT for federated discovery.
    
    Features:
    - Publish agent configurations to the marketplace
    - Discover available agent configurations
    - Search agents by capabilities, tags, or keywords
    - Rate and review agent configurations
    - Track download statistics
    - P2P discovery via mDNS and DHT
    """
    
    def __init__(
        self,
        marketplace_file: str = "agent_marketplace.json",
        enable_mdns: bool = True,
        enable_dht: bool = False,
        dht_port: int = 8469
    ):
        """
        Initialize the Agent Marketplace.
        
        Args:
            marketplace_file: Path to the marketplace storage file
            enable_mdns: Whether to enable mDNS discovery for local networks
            enable_dht: Whether to enable DHT discovery for federated networks
            dht_port: Port for DHT server (default: 8469)
        """
        self.marketplace_file = marketplace_file
        self._listings: Dict[str, MarketplaceListing] = {}
        
        # mDNS support
        self._enable_mdns = enable_mdns and MDNS_AVAILABLE
        self._zeroconf = None
        self._mdns_browser = None
        self._mdns_services: Dict[str, ServiceInfo] = {}
        
        # DHT support
        self._enable_dht = enable_dht and DHT_AVAILABLE
        self._dht_server = None
        self._dht_port = dht_port
        
        # Initialize from file if it exists
        self._load_marketplace()
        
        # Start discovery services
        if self._enable_mdns:
            self._start_mdns()
        if self._enable_dht:
            self._start_dht()
    
    def _load_marketplace(self):
        """Load marketplace listings from file"""
        if os.path.exists(self.marketplace_file):
            try:
                with open(self.marketplace_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for listing_id, listing_data in data.items():
                        self._listings[listing_id] = MarketplaceListing.from_dict(listing_data)
                logger.info(f"Loaded {len(self._listings)} listings from marketplace")
            except Exception as e:
                logger.error(f"Failed to load marketplace: {e}")
                self._listings = {}
    
    def _save_marketplace(self):
        """Save marketplace listings to file"""
        try:
            data = {
                listing_id: listing.to_dict()
                for listing_id, listing in self._listings.items()
            }
            with open(self.marketplace_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save marketplace: {e}")
    
    def _generate_listing_id(self, agent_config: Dict[str, Any], publisher_id: str) -> str:
        """Generate a unique listing ID based on config and publisher"""
        config_str = json.dumps(agent_config, sort_keys=True)
        hash_input = f"{publisher_id}:{config_str}:{time.time()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _start_mdns(self):
        """Start mDNS service for local network marketplace discovery"""
        if not MDNS_AVAILABLE:
            logger.warning("mDNS not available. Install zeroconf package.")
            return
        
        try:
            self._zeroconf = Zeroconf()
            logger.info("mDNS service started for marketplace discovery")
        except Exception as e:
            logger.error(f"Failed to start mDNS: {e}")
            self._enable_mdns = False
    
    def _start_dht(self):
        """Start DHT service for federated marketplace discovery"""
        if not DHT_AVAILABLE:
            logger.warning("DHT not available. Install kademlia package.")
            return
        
        try:
            self._dht_server = Server()
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(self._dht_server.listen(self._dht_port))
            logger.info(f"DHT service started on port {self._dht_port}")
        except Exception as e:
            logger.error(f"Failed to start DHT: {e}")
            self._enable_dht = False
    
    def _stop_mdns(self):
        """Stop mDNS service"""
        if self._zeroconf:
            try:
                self._zeroconf.close()
                logger.info("mDNS service stopped")
            except Exception as e:
                logger.error(f"Error stopping mDNS: {e}")
    
    def _stop_dht(self):
        """Stop DHT service"""
        if self._dht_server:
            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(self._dht_server.stop())
                logger.info("DHT service stopped")
            except Exception as e:
                logger.error(f"Error stopping DHT: {e}")
    
    def _publish_mdns_listing(self, listing: MarketplaceListing, network_url: str):
        """Publish marketplace listing via mDNS"""
        if not self._enable_mdns or not self._zeroconf:
            return
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(network_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8000
            
            service_type = "_daie-marketplace._tcp.local."
            service_name = f"{listing.listing_id}.{service_type}"
            
            txt_data = {
                "listing_id": listing.listing_id,
                "publisher_id": listing.publisher_id,
                "description": listing.description[:100],
                "tags": json.dumps(listing.tags),
                "version": listing.version
            }
            
            service_info = ServiceInfo(
                service_type,
                service_name,
                addresses=[socket.inet_aton(host)],
                port=port,
                properties=txt_data,
                server=f"{listing.listing_id}.local.",
            )
            
            self._zeroconf.register_service(service_info)
            self._mdns_services[listing.listing_id] = service_info
            logger.info(f"Published mDNS listing {listing.listing_id}")
        except Exception as e:
            logger.error(f"Failed to publish mDNS listing: {e}")
    
    def _unpublish_mdns_listing(self, listing_id: str):
        """Unpublish marketplace listing from mDNS"""
        if not self._enable_mdns or not self._zeroconf:
            return
        
        try:
            if listing_id in self._mdns_services:
                self._zeroconf.unregister_service(self._mdns_services[listing_id])
                del self._mdns_services[listing_id]
                logger.info(f"Unpublished mDNS listing {listing_id}")
        except Exception as e:
            logger.error(f"Failed to unpublish mDNS listing: {e}")
    
    async def _publish_dht_listing(self, listing: MarketplaceListing, network_url: str):
        """Publish marketplace listing to DHT"""
        if not self._enable_dht or not self._dht_server:
            return
        
        try:
            listing_data = {
                "listing": listing.to_dict(),
                "network_url": network_url,
                "timestamp": time.time()
            }
            
            await self._dht_server.set(f"marketplace:{listing.listing_id}", json.dumps(listing_data))
            logger.info(f"Published DHT listing {listing.listing_id}")
        except Exception as e:
            logger.error(f"Failed to publish DHT listing: {e}")
    
    async def _discover_dht_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Discover marketplace listing from DHT"""
        if not self._enable_dht or not self._dht_server:
            return None
        
        try:
            result = await self._dht_server.get(f"marketplace:{listing_id}")
            if result:
                return json.loads(result)
        except Exception as e:
            logger.error(f"Failed to discover DHT listing: {e}")
        return None
    
    def publish_listing(
        self,
        agent_config: Dict[str, Any],
        publisher_id: str,
        description: str = "",
        tags: List[str] = None,
        version: str = "1.0.0",
        price: float = 0.0,
        license: str = "MIT",
        network_url: Optional[str] = None
    ) -> str:
        """
        Publish an agent configuration to the marketplace.
        
        Args:
            agent_config: Agent configuration dictionary
            publisher_id: ID of the publisher
            description: Description of the agent
            tags: List of tags for categorization
            version: Version string
            price: Price (0.0 for free)
            license: License type
            network_url: Network URL for P2P distribution
            
        Returns:
            Listing ID of the published configuration
        """
        listing_id = self._generate_listing_id(agent_config, publisher_id)
        
        listing = MarketplaceListing(
            listing_id=listing_id,
            agent_config=agent_config,
            publisher_id=publisher_id,
            description=description,
            tags=tags or [],
            version=version,
            price=price,
            license=license
        )
        
        self._listings[listing_id] = listing
        self._save_marketplace()
        
        # Publish to mDNS if enabled
        if self._enable_mdns and network_url:
            self._publish_mdns_listing(listing, network_url)
        
        # Publish to DHT if enabled
        if self._enable_dht and network_url:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._publish_dht_listing(listing, network_url))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._publish_dht_listing(listing, network_url))
        
        logger.info(f"Published listing {listing_id} to marketplace")
        return listing_id
    
    def unpublish_listing(self, listing_id: str) -> bool:
        """
        Remove a listing from the marketplace.
        
        Args:
            listing_id: ID of the listing to remove
            
        Returns:
            True if successful, False otherwise
        """
        if listing_id in self._listings:
            del self._listings[listing_id]
            self._save_marketplace()
            
            # Unpublish from mDNS
            if self._enable_mdns:
                self._unpublish_mdns_listing(listing_id)
            
            # Remove from DHT
            if self._enable_dht and self._dht_server:
                try:
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self._dht_server.set(f"marketplace:{listing_id}", ""))
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self._dht_server.set(f"marketplace:{listing_id}", ""))
                except Exception as e:
                    logger.error(f"Failed to remove DHT listing: {e}")
            
            logger.info(f"Unpublished listing {listing_id} from marketplace")
            return True
        return False
    
    def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific marketplace listing.
        
        Args:
            listing_id: ID of the listing
            
        Returns:
            Listing dictionary or None if not found
        """
        listing = self._listings.get(listing_id)
        return listing.to_dict() if listing else None
    
    def search_listings(
        self,
        query: str = None,
        tags: List[str] = None,
        publisher_id: str = None,
        min_rating: float = 0.0,
        max_price: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search marketplace listings with various filters.
        
        Args:
            query: Search query for description and config
            tags: Filter by tags
            publisher_id: Filter by publisher
            min_rating: Minimum rating filter
            max_price: Maximum price filter
            limit: Maximum number of results
            
        Returns:
            List of matching listings
        """
        results = []
        
        for listing in self._listings.values():
            # Apply filters
            if publisher_id and listing.publisher_id != publisher_id:
                continue
            
            if min_rating > 0 and listing.rating < min_rating:
                continue
            
            if max_price is not None and listing.price > max_price:
                continue
            
            if tags:
                if not any(tag in listing.tags for tag in tags):
                    continue
            
            if query:
                query_lower = query.lower()
                search_text = (
                    f"{listing.description} {json.dumps(listing.agent_config)} "
                    f"{' '.join(listing.tags)}"
                ).lower()
                if query_lower not in search_text:
                    continue
            
            results.append(listing.to_dict())
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_all_listings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all marketplace listings.
        
        Args:
            limit: Maximum number of listings to return
            
        Returns:
            List of all listings
        """
        listings = []
        for listing in list(self._listings.values())[:limit]:
            listings.append(listing.to_dict())
        return listings
    
    def download_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Download a listing (increment download counter and return config).
        
        Args:
            listing_id: ID of the listing to download
            
        Returns:
            Agent configuration or None if not found
        """
        listing = self._listings.get(listing_id)
        if listing:
            listing.increment_downloads()
            self._save_marketplace()
            logger.info(f"Downloaded listing {listing_id}")
            return listing.agent_config
        return None
    
    def rate_listing(self, listing_id: str, rating: float) -> bool:
        """
        Rate a marketplace listing.
        
        Args:
            listing_id: ID of the listing to rate
            rating: Rating value (0.0 to 5.0)
            
        Returns:
            True if successful, False otherwise
        """
        listing = self._listings.get(listing_id)
        if listing:
            try:
                listing.update_rating(rating)
                self._save_marketplace()
                logger.info(f"Rated listing {listing_id} with {rating}")
                return True
            except ValueError as e:
                logger.error(f"Invalid rating: {e}")
        return False
    
    def get_listings_by_publisher(self, publisher_id: str) -> List[Dict[str, Any]]:
        """
        Get all listings from a specific publisher.
        
        Args:
            publisher_id: Publisher ID
            
        Returns:
            List of listings from the publisher
        """
        return [
            listing.to_dict()
            for listing in self._listings.values()
            if listing.publisher_id == publisher_id
        ]
    
    def get_popular_listings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular listings by download count.
        
        Args:
            limit: Maximum number of listings to return
            
        Returns:
            List of popular listings
        """
        sorted_listings = sorted(
            self._listings.values(),
            key=lambda x: x.downloads,
            reverse=True
        )
        return [listing.to_dict() for listing in sorted_listings[:limit]]
    
    def get_top_rated_listings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top-rated listings.
        
        Args:
            limit: Maximum number of listings to return
            
        Returns:
            List of top-rated listings
        """
        sorted_listings = sorted(
            self._listings.values(),
            key=lambda x: (x.rating, x.rating_count),
            reverse=True
        )
        return [listing.to_dict() for listing in sorted_listings[:limit]]
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """
        Get marketplace statistics.
        
        Returns:
            Dictionary with marketplace statistics
        """
        total_listings = len(self._listings)
        total_downloads = sum(l.downloads for l in self._listings.values())
        avg_rating = 0.0
        
        rated_listings = [l for l in self._listings.values() if l.rating_count > 0]
        if rated_listings:
            avg_rating = sum(l.rating for l in rated_listings) / len(rated_listings)
        
        publishers = set(l.publisher_id for l in self._listings.values())
        
        return {
            "total_listings": total_listings,
            "total_downloads": total_downloads,
            "average_rating": round(avg_rating, 2),
            "total_publishers": len(publishers),
            "mdns_enabled": self._enable_mdns,
            "dht_enabled": self._enable_dht
        }
    
    def discover_listings_mdns(self, timeout: float = 2.0) -> List[Dict[str, Any]]:
        """
        Discover marketplace listings on the local network using mDNS.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            List of discovered listings
        """
        if not self._enable_mdns or not self._zeroconf:
            logger.warning("mDNS discovery not enabled")
            return []
        
        results = []
        try:
            service_type = "_daie-marketplace._tcp.local."
            browser = ServiceBrowser(self._zeroconf, service_type, handlers=[self._on_mdns_service_added])
            
            time.sleep(timeout)
            browser.cancel()
            
            for listing_id, service_info in self._mdns_services.items():
                if listing_id in self._listings:
                    results.append(self._listings[listing_id].to_dict())
            
            logger.info(f"Discovered {len(results)} listings via mDNS")
        except Exception as e:
            logger.error(f"mDNS discovery failed: {e}")
        
        return results
    
    def _on_mdns_service_added(self, zeroconf, service_type, name):
        """Callback for mDNS service discovery"""
        try:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                listing_id = name.split(".")[0]
                
                if listing_id not in self._listings:
                    tags = []
                    if info.properties:
                        tags_str = info.properties.get(b"tags", b"[]").decode("utf-8")
                        tags = json.loads(tags_str)
                    
                    publisher_id = ""
                    if info.properties:
                        publisher_id = info.properties.get(b"publisher_id", b"").decode("utf-8")
                    
                    description = ""
                    if info.properties:
                        description = info.properties.get(b"description", b"").decode("utf-8")
                    
                    version = "1.0.0"
                    if info.properties:
                        version = info.properties.get(b"version", b"1.0.0").decode("utf-8")
                    
                    if info.addresses:
                        host = socket.inet_ntoa(info.addresses[0])
                        port = info.port
                        network_url = f"http://{host}:{port}"
                        
                        logger.info(f"Discovered listing {listing_id} via mDNS at {network_url}")
        except Exception as e:
            logger.error(f"Error processing mDNS service: {e}")
    
    async def discover_listings_dht(self, listing_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Discover marketplace listings from DHT by their IDs.
        
        Args:
            listing_ids: List of listing IDs to discover
            
        Returns:
            List of discovered listings
        """
        if not self._enable_dht or not self._dht_server:
            logger.warning("DHT discovery not enabled")
            return []
        
        results = []
        try:
            for listing_id in listing_ids:
                listing_data = await self._discover_dht_listing(listing_id)
                if listing_data and "listing" in listing_data:
                    listing_dict = listing_data["listing"]
                    if listing_id not in self._listings:
                        self._listings[listing_id] = MarketplaceListing.from_dict(listing_dict)
                        results.append(listing_dict)
                        logger.info(f"Discovered listing {listing_id} via DHT")
            
            logger.info(f"Discovered {len(results)} listings via DHT")
        except Exception as e:
            logger.error(f"DHT discovery failed: {e}")
        
        return results
    
    def close(self):
        """Close the marketplace and cleanup resources"""
        self._stop_mdns()
        self._stop_dht()
        logger.info("Marketplace closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
