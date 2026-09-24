import hashlib
import re
from typing import Dict, List, Tuple


class SecurityService:
    """Enterprise AI Security & Privacy Guardrails for Health & Social Care applications.
    
    Addresses the WMG 'Secure by Design' mandate:
    1. Prompt Injection & Adversarial Payload Detection.
    2. PII / PHI Redaction complying with UK GDPR & Caldicott Principles.
    3. Tamper-evident Cryptographic Hashing (SHA-256) for audit trails.
    """

    # Common prompt injection patterns across multiple phrasing styles
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(previous|all)\s+instructions",
        r"(?i)system\s*:\s*override",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)disregard\s+prior\s+(rules|guidelines|context)",
        r"(?i)reveal\s+(internal|system)\s+prompt",
        r"(?i)act\s+as\s+(an?\s+)?unrestricted\s+ai",
        r"(?i)forget\s+all\s+rules",
        r"(?i)jailbreak",
        r"(?i)DAN\s+mode",
    ]

    # UK NHS Number (3 digits, 3 digits, 4 digits with optional spaces)
    NHS_NUMBER_REGEX = r"\b[0-9]{3}\s?[0-9]{3}\s?[0-9]{4}\b"

    # UK Phone numbers (Mobile and landlines, e.g. 07123 456789, +44 (0) 2079 460123)
    PHONE_REGEX = r"(?:\+44\s?(?:\(0\)\s?)?|\b0)(?:[1-9]\d{1,4}\s?\d{3,4}\s?\d{3,4}|\d{4}\s?\d{6}|\d{3}\s?\d{7}|\d{5}\s?\d{4,5})\b"

    # UK Postcodes
    POSTCODE_REGEX = r"\b[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}\b"

    # Email Addresses
    EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"

    @classmethod
    def check_prompt_injection(cls, text: str) -> Tuple[bool, str]:
        """Scans input text for potential prompt injection attempts.
        
        Returns:
            (is_safe, reason)
        """
        if not text:
            return True, ""

        for pattern in cls.INJECTION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return False, f"Potential adversarial prompt injection detected: '{match.group(0)}'"

        # Check for abnormal control characters or massive prompt stuffing
        if len(text) > 15000:
            return False, "Input exceeds maximum safe token length (15,000 characters)"

        return True, "Safe"

    @classmethod
    def redact_pii(cls, text: str) -> Tuple[str, bool, Dict[str, str]]:
        """Redacts PII / PHI from care worker logs before sending to external LLMs.
        
        Protects patient privacy under UK Caldicott Principles & GDPR.
        Returns:
            (sanitized_text, has_pii, redaction_map)
        """
        if not text:
            return "", False, {}

        sanitized = text
        redaction_map = {}
        counter = 1

        # 1. Redact NHS Numbers
        nhs_matches = re.findall(cls.NHS_NUMBER_REGEX, sanitized)
        for match in nhs_matches:
            token = f"[REDACTED_NHS_NO_{counter}]"
            redaction_map[token] = match
            sanitized = sanitized.replace(match, token)
            counter += 1

        # 2. Redact Phone Numbers
        phone_matches = re.findall(cls.PHONE_REGEX, sanitized)
        for match in phone_matches:
            token = f"[REDACTED_TEL_{counter}]"
            redaction_map[token] = match
            sanitized = sanitized.replace(match, token)
            counter += 1

        # 3. Redact Postcodes
        postcode_matches = re.findall(cls.POSTCODE_REGEX, sanitized, re.IGNORECASE)
        for match in postcode_matches:
            token = f"[REDACTED_POSTCODE_{counter}]"
            redaction_map[token] = match
            sanitized = sanitized.replace(match, token)
            counter += 1

        # 4. Redact Emails
        email_matches = re.findall(cls.EMAIL_REGEX, sanitized)
        for match in email_matches:
            token = f"[REDACTED_EMAIL_{counter}]"
            redaction_map[token] = match
            sanitized = sanitized.replace(match, token)
            counter += 1

        has_pii = len(redaction_map) > 0
        return sanitized, has_pii, redaction_map

    @classmethod
    def generate_sha256_audit_hash(cls, payload: str) -> str:
        """Generates a cryptographic SHA-256 checksum for audit and integrity verification."""
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def verify_audit_hash(cls, payload: str, expected_hash: str) -> bool:
        """Verifies if the stored cryptographic hash matches the current payload."""
        computed = cls.generate_sha256_audit_hash(payload)
        return computed == expected_hash
