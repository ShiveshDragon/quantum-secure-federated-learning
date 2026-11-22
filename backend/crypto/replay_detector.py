"""Replay Protection Module for Quantum FL-IoT.

Tracks accepted client updates, message IDs, and round numbers to reject
replay attacks, duplicate updates, and stale round messages.
"""
import time
from typing import Set, Tuple, Optional, Dict


class ReplayDetector:
    """Detects and rejects replayed or stale messages based on client, round, and message IDs."""

    def __init__(self, max_round_window: int = 1, ttl_seconds: float = 300.0):
        self.seen_signatures: Set[Tuple[str, int, str]] = set()
        self.client_latest_round: Dict[str, int] = {}
        self.max_round_window = max_round_window
        self.ttl_seconds = ttl_seconds
        self.rejection_count = 0

    def check_and_record(
        self,
        client_id: str,
        round_number: int,
        message_id: Optional[str] = None,
        timestamp: Optional[float] = None,
        current_server_round: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Validate whether a message is fresh or a replay attempt.
        
        Returns:
            (True, "OK") if message is fresh and accepted.
            (False, reason_message) if message is a duplicate, stale, or expired.
        """
        if not client_id:
            self.rejection_count += 1
            return False, "Missing client_id"

        if round_number is None or round_number < 1:
            self.rejection_count += 1
            return False, f"Invalid round_number: {round_number}"

        # 1. Stale round check against current server round
        if current_server_round is not None:
            if round_number < current_server_round:
                self.rejection_count += 1
                return False, f"Stale round: message round {round_number} is older than current server round {current_server_round}"
            if round_number > current_server_round + self.max_round_window:
                self.rejection_count += 1
                return False, f"Future round out of window: message round {round_number} vs server round {current_server_round}"

        # 2. Timestamp freshness check (if timestamp provided)
        if timestamp is not None:
            now = time.time()
            if abs(now - timestamp) > self.ttl_seconds:
                self.rejection_count += 1
                return False, f"Timestamp expired: delta {abs(now - timestamp):.1f}s exceeds TTL {self.ttl_seconds}s"

        # 3. Duplicate detection
        msg_sig = (client_id, round_number, message_id if message_id else f"default_{round_number}")
        if msg_sig in self.seen_signatures:
            self.rejection_count += 1
            return False, f"Replay detected: duplicate message {msg_sig} already accepted"

        # 4. Check if client already submitted an update for this round
        last_accepted = self.client_latest_round.get(client_id, 0)
        if round_number == last_accepted and (client_id, round_number, None) in [
            (c, r, None) for (c, r, _) in self.seen_signatures
        ]:
            self.rejection_count += 1
            return False, f"Duplicate round submission: client {client_id} already submitted update for round {round_number}"

        # Message is valid - record it
        self.seen_signatures.add(msg_sig)
        self.client_latest_round[client_id] = max(last_accepted, round_number)
        return True, "OK"

    def reset(self):
        """Reset internal state between experiments."""
        self.seen_signatures.clear()
        self.client_latest_round.clear()
        self.rejection_count = 0
