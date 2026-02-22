import re
import socket
import whois
import requests
from urllib.parse import urlparse
from datetime import datetime

class FeatureExtractor:
    def __init__(self):
        pass

    def extract_features(self, url):
        features = {
            "urllen": len(url),
            "domainlen": 0,
            "subdomain": 0,
            "havedash": 0,
            "is@": 0,
            "isip": 0,
            "isredirect": 0,
            "valid": 1,
            "rank": 0,
            "ranking": 0,
            "domain_reg_len": 0,
            "activeduration": 0,
            "tinyurl": 0,
            "nosofsubdomain": 0,
            "isvalid": 1,
            "longurl": 0
        }

        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path

            # Domain length
            features["domainlen"] = len(domain)

            # URL length
            features["urllen"] = len(url)

            # Number of subdomains
            features["nosofsubdomain"] = domain.count('.')
            features["subdomain"] = features["nosofsubdomain"]

            # Has dash ("-")
            features["havedash"] = 1 if "-" in domain else 0

            # Has '@' symbol
            features["is@"] = 1 if "@" in url else 0

            # Redirect detection
            features["isredirect"] = 1 if "//" in path else 0

            # Check if URL contains an IP
            features["isip"] = 1 if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain) else 0

            # Tiny URL or shortening service
            features["tinyurl"] = 1 if any(short in url for short in [
                "bit.ly", "goo.gl", "t.co", "tinyurl", "ow.ly", "is.gd"
            ]) else 0

            # Long URL flag
            features["longurl"] = 1 if len(url) > 75 else 0

            # Domain registration info
            try:
                w = whois.whois(domain)
                creation = w.creation_date
                expiration = w.expiration_date

                if isinstance(creation, list):
                    creation = creation[0]
                if isinstance(expiration, list):
                    expiration = expiration[0]

                if creation and expiration:
                    features["domain_reg_len"] = (expiration - creation).days if expiration > creation else 0
                    features["activeduration"] = (datetime.now() - creation).days
                else:
                    features["domain_reg_len"] = 0
                    features["activeduration"] = 0
            except Exception:
                features["domain_reg_len"] = 0
                features["activeduration"] = 0

            # Rank / Alexa / Tranco substitute
            try:
                features["rank"] = self.get_rank(domain)
                features["ranking"] = round(1 - (features["rank"] / 100.0), 3)
            except Exception:
                features["rank"] = 50
                features["ranking"] = 0.5

            # Domain validity (DNS check)
            try:
                socket.gethostbyname(domain)
                features["valid"] = 1
                features["isvalid"] = 1
            except:
                features["valid"] = 0
                features["isvalid"] = 0

        except Exception as e:
            print("[ERROR] Feature extraction failed:", e)
            features["isvalid"] = 0
            features["valid"] = 0

        # Normalize numeric scales (important for model consistency)
        features["urllen"] = min(features["urllen"] / 200.0, 1.0)
        features["domainlen"] = min(features["domainlen"] / 50.0, 1.0)
        features["nosofsubdomain"] = min(features["nosofsubdomain"] / 5.0, 1.0)
        features["domain_reg_len"] = min(features["domain_reg_len"] / 3650.0, 1.0)
        features["activeduration"] = min(features["activeduration"] / 3650.0, 1.0)
        features["rank"] = min(features["rank"] / 100.0, 1.0)

        return features

    def get_rank(self, domain):
        """
        Placeholder for domain popularity rank.
        For real deployment, you can integrate Alexa/Tranco API.
        For now, we simulate using a simple heuristic.
        """
        trusted_domains = ["google.com", "microsoft.com", "amazon.com", "youtube.com", "wikipedia.org"]
        if any(t in domain for t in trusted_domains):
            return 1
        elif domain.endswith(".gov") or domain.endswith(".edu"):
            return 5
        elif len(domain) < 10:
            return 20
        elif "-" in domain or len(domain) > 20:
            return 70
        else:
            return 50