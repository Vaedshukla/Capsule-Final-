"""
Content Sanitizer — strips secrets and sensitive data before DB writes.

This runs on ALL message content before persistence.
Capsule stores AI conversations that may contain:
  - API keys accidentally pasted into prompts
  - Bearer tokens from debugging sessions
  - Database connection strings
  - Private keys from code reviews
  - Passwords from configuration discussions

Philosophy: redact silently, log counts only (never log the actual secret).
"""
import re
import structlog
from dataclasses import dataclass, field
from typing import List

logger = structlog.get_logger()


@dataclass
class SanitizationResult:
    content: str
    redaction_count: int
    patterns_matched: List[str] = field(default_factory=list)

    @property
    def was_redacted(self) -> bool:
        return self.redaction_count > 0


# ─── Secret Pattern Registry ──────────────────────────────────────────────────
# Each entry: (pattern_name, compiled_regex, replacement)

_PATTERNS: List[tuple] = [
    # OpenAI API keys: sk-... (old) and sk-proj-... (new format)
    ("openai_api_key",
     re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}', re.IGNORECASE),
     "[REDACTED:openai_key]"),

    # Anthropic API keys: sk-ant-...
    ("anthropic_api_key",
     re.compile(r'\bsk-ant-[A-Za-z0-9_\-]{20,}', re.IGNORECASE),
     "[REDACTED:anthropic_key]"),

    # GitHub tokens: ghp_, gho_, ghs_, ghr_
    ("github_token",
     re.compile(r'\bgh[psorl]_[A-Za-z0-9_]{36,}', re.IGNORECASE),
     "[REDACTED:github_token]"),

    # Slack tokens: xoxb-, xoxp-, xoxa-
    ("slack_token",
     re.compile(r'\bxox[bpas]-[A-Za-z0-9\-]{10,}', re.IGNORECASE),
     "[REDACTED:slack_token]"),

    # AWS access keys: AKIA...
    ("aws_access_key",
     re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
     "[REDACTED:aws_key]"),

    # JWTs: eyJ... (base64 header)
    ("jwt_token",
     re.compile(r'\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+'),
     "[REDACTED:jwt]"),

    # Bearer tokens in Authorization headers
    ("bearer_token",
     re.compile(r'(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}'),
     "Bearer [REDACTED]"),

    # Database connection strings
    ("db_connection_string",
     re.compile(
         r'(?i)(postgres|postgresql|mysql|mongodb|redis|sqlite)'
         r'(\+\w+)?://[^\s"\'<>]+',
     ),
     "[REDACTED:connection_string]"),

    # Generic key=value patterns for common secret fields
    ("generic_secret_kv",
     re.compile(
         r'(?i)(?:api[_\-]?key|secret[_\-]?key|auth[_\-]?token|'
         r'access[_\-]?token|private[_\-]?key|client[_\-]?secret'
         r'|password|passwd|pwd)'
         r'\s*[=:]\s*["\']?([A-Za-z0-9_\-\.\/\+]{8,})["\']?',
     ),
     "[REDACTED:secret_value]"),

    # PEM private keys
    ("pem_private_key",
     re.compile(
         r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'
         r'[\s\S]*?'
         r'-----END (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----',
         re.MULTILINE,
     ),
     "[REDACTED:private_key]"),
]


class ContentSanitizer:
    """
    Sanitizes message content by redacting known secret patterns.
    Thread-safe — all state is in class-level constants.
    """

    def sanitize(self, content: str) -> SanitizationResult:
        """
        Sanitize a single string.
        Returns SanitizationResult with cleaned content and metadata.
        """
        if not content:
            return SanitizationResult(content=content, redaction_count=0)

        result_content = content
        total_redactions = 0
        matched_patterns: List[str] = []

        for pattern_name, pattern, replacement in _PATTERNS:
            new_content, count = pattern.subn(replacement, result_content)
            if count > 0:
                result_content = new_content
                total_redactions += count
                matched_patterns.append(pattern_name)

        if total_redactions > 0:
            logger.warning(
                "content_sanitized",
                redaction_count=total_redactions,
                patterns=matched_patterns,
                # Intentionally do NOT log the original content
            )

        return SanitizationResult(
            content=result_content,
            redaction_count=total_redactions,
            patterns_matched=matched_patterns,
        )

    def sanitize_batch(self, contents: List[str]) -> List[SanitizationResult]:
        """Sanitize multiple strings efficiently."""
        return [self.sanitize(c) for c in contents]


# Module-level singleton
sanitizer = ContentSanitizer()
