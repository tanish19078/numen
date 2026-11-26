"""SQLite WAL ACID ledger for Numen vault, agent sub-accounts, AP2 mandates, cards, and audit log."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from .config import get_settings
from .crypto_ap2 import create_intent_mandate
from .models import (
    AgentAccount,
    AuditEvent,
    IntentMandate,
    MasterVault,
    PasskeyChallenge,
    SpendRequest,
    VirtualCard,
)

DEFAULT_VAULT_ID = "vault_acme_01"
DEFAULT_VAULT_NAME = "Acme AI Labs — Operating Vault"
DEFAULT_VAULT_BALANCE = 1840000.0


@contextmanager
def get_conn(db_path: str | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or get_settings().db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS master_vault (
                vault_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                balance_inr REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'INR'
            );

            CREATE TABLE IF NOT EXISTS agent_accounts (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                daily_limit_inr REAL NOT NULL,
                spent_today_inr REAL NOT NULL DEFAULT 0.0,
                allowed_mccs_json TEXT NOT NULL,
                intent_mandate_id TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mandates (
                mandate_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS virtual_cards (
                card_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS passkey_challenges (
                challenge_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS spend_history (
                seq_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                merchant_name TEXT NOT NULL,
                amount_inr REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                tx_id TEXT PRIMARY KEY,
                card_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                merchant_name TEXT NOT NULL,
                merchant_mcc TEXT NOT NULL,
                amount_inr REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                decision TEXT NOT NULL,
                summary TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def _seed_initial_data(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO master_vault (vault_id, name, balance_inr, currency) VALUES (?, ?, ?, 'INR')",
        (DEFAULT_VAULT_ID, DEFAULT_VAULT_NAME, DEFAULT_VAULT_BALANCE),
    )

    seeded_specs = [
        (
            "agent-devops",
            "DevOps-Agent",
            "Cloud Compute & GPU Auto-Scaler",
            25000.0,
            15000.0,
            ["CLOUD", "INFRA", "API"],
            "Auto-scale RunPod and GCP GPU compute plus inference APIs up to INR 25,000/day; zero recurring annual lock-ins.",
            False,
            "mandate_devops_01",
        ),
        (
            "agent-procurement",
            "Procurement-Agent",
            "Dataset & SaaS Vendor Buyer",
            15000.0,
            10000.0,
            ["DATA", "SAAS", "API"],
            "Compare NLP dataset vendors and purchase 1 verified dataset license under INR 15,000; no gift cards or vouchers.",
            False,
            "mandate_procure_01",
        ),
        (
            "agent-research",
            "Research-Agent",
            "Market & Academic Data Gatherer",
            5000.0,
            5000.0,
            ["DATA", "API", "RESEARCH"],
            "Purchase one-off academic or market data passes up to INR 5,000; strictly prohibit auto-renewing annual subscriptions.",
            False,
            "mandate_research_01",
        ),
    ]

    for aid, name, role, daily_lim, single_lim, mccs, nl_intent, allow_rec, mid in seeded_specs:
        mandate = create_intent_mandate(
            agent_id=aid,
            natural_language_intent=nl_intent,
            max_daily_inr=daily_lim,
            max_single_tx_inr=single_lim,
            allowed_mccs=mccs,
            allow_recurring=allow_rec,
            mandate_id=mid,
        )
        conn.execute(
            """
            INSERT INTO agent_accounts
            (agent_id, name, role, status, daily_limit_inr, spent_today_inr, allowed_mccs_json, intent_mandate_id)
            VALUES (?, ?, ?, 'ACTIVE', ?, 0.0, ?, ?)
            """,
            (aid, name, role, daily_lim, json.dumps(mccs), mandate.mandate_id),
        )
        conn.execute(
            "INSERT INTO mandates (mandate_id, kind, agent_id, payload_json, created_at) VALUES (?, 'INTENT', ?, ?, ?)",
            (mandate.mandate_id, aid, mandate.model_dump_json(), mandate.issued_at),
        )

    boot_event = AuditEvent(
        event_id=f"evt_{uuid4().hex[:8]}",
        trace_id="trace_boot",
        agent_id="system",
        event_type="TREASURY_INIT",
        decision="READY",
        summary="Initialized Acme Master Vault (INR 18,40,000) and signed 3 Ed25519 AP2 IntentMandates.",
        metadata={"agents": 3, "protocol": "AP2-Ed25519"},
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    conn.execute(
        """
        INSERT INTO audit_events (event_id, trace_id, agent_id, event_type, decision, summary, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            boot_event.event_id,
            boot_event.trace_id,
            boot_event.agent_id,
            boot_event.event_type,
            boot_event.decision,
            boot_event.summary,
            json.dumps(boot_event.metadata),
            boot_event.created_at,
        ),
    )


def init_and_seed_db(db_path: str | None = None) -> None:
    init_schema(db_path)
    with get_conn(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM master_vault").fetchone()
        if row and row["cnt"] == 0:
            _seed_initial_data(conn)


def reset_demo_state(db_path: str | None = None) -> None:
    init_schema(db_path)
    with get_conn(db_path) as conn:
        for tbl in [
            "audit_events",
            "transactions",
            "spend_history",
            "passkey_challenges",
            "virtual_cards",
            "mandates",
            "agent_accounts",
            "master_vault",
        ]:
            conn.execute(f"DELETE FROM {tbl}")
        _seed_initial_data(conn)


def get_vault(db_path: str | None = None) -> MasterVault:
    with get_conn(db_path) as conn:
        row = conn.execute("SELECT * FROM master_vault LIMIT 1").fetchone()
        if not row:
            raise RuntimeError("Master vault not initialized")
        return MasterVault(
            vault_id=row["vault_id"],
            name=row["name"],
            balance_inr=round(float(row["balance_inr"]), 2),
            currency=row["currency"],
        )


def list_agents(db_path: str | None = None) -> list[AgentAccount]:
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT * FROM agent_accounts ORDER BY agent_id").fetchall()
        return [
            AgentAccount(
                agent_id=r["agent_id"],
                name=r["name"],
                role=r["role"],
                status=r["status"],
                daily_limit_inr=float(r["daily_limit_inr"]),
                spent_today_inr=float(r["spent_today_inr"]),
                allowed_mccs=json.loads(r["allowed_mccs_json"]),
                intent_mandate_id=r["intent_mandate_id"],
            )
            for r in rows
        ]


def get_agent(agent_id: str, db_path: str | None = None) -> AgentAccount | None:
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM agent_accounts WHERE agent_id = ?", (agent_id,)).fetchone()
        if not r:
            return None
        return AgentAccount(
            agent_id=r["agent_id"],
            name=r["name"],
            role=r["role"],
            status=r["status"],
            daily_limit_inr=float(r["daily_limit_inr"]),
            spent_today_inr=float(r["spent_today_inr"]),
            allowed_mccs=json.loads(r["allowed_mccs_json"]),
            intent_mandate_id=r["intent_mandate_id"],
        )


def set_agent_status(agent_id: str, status: str, db_path: str | None = None) -> AgentAccount | None:
    with get_conn(db_path) as conn:
        conn.execute("UPDATE agent_accounts SET status = ? WHERE agent_id = ?", (status, agent_id))
    return get_agent(agent_id, db_path)


def get_intent_mandate(mandate_id: str, db_path: str | None = None) -> IntentMandate | None:
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT payload_json FROM mandates WHERE mandate_id = ?", (mandate_id,)).fetchone()
        if not r:
            return None
        return IntentMandate.model_validate_json(r["payload_json"])


def save_mandate(mandate_id: str, kind: str, agent_id: str, payload_json: str, created_at: str, db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO mandates (mandate_id, kind, agent_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (mandate_id, kind, agent_id, payload_json, created_at),
        )


def update_agent_intent_mandate(mandate: IntentMandate, db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO mandates (mandate_id, kind, agent_id, payload_json, created_at) VALUES (?, 'INTENT', ?, ?, ?)",
            (mandate.mandate_id, mandate.agent_id, mandate.model_dump_json(), mandate.issued_at),
        )
        conn.execute(
            "UPDATE agent_accounts SET daily_limit_inr = ?, allowed_mccs_json = ?, intent_mandate_id = ? WHERE agent_id = ?",
            (mandate.max_daily_inr, json.dumps(mandate.allowed_mccs), mandate.mandate_id, mandate.agent_id),
        )


def list_mandates(limit: int = 40, db_path: str | None = None) -> list[dict]:
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT kind, payload_json, created_at FROM mandates ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            data = json.loads(r["payload_json"])
            data["kind"] = r["kind"]
            out.append(data)
        return out


def save_virtual_card(card: VirtualCard, db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO virtual_cards (card_id, agent_id, payload_json, status, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            (card.card_id, card.agent_id, card.model_dump_json(), card.status, card.created_at, card.expires_at),
        )


def get_virtual_card(card_id: str, db_path: str | None = None) -> VirtualCard | None:
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT payload_json FROM virtual_cards WHERE card_id = ?", (card_id,)).fetchone()
        if not r:
            return None
        card = VirtualCard.model_validate_json(r["payload_json"])
        if card.status == "ACTIVE" and datetime.now(timezone.utc) > datetime.fromisoformat(card.expires_at):
            card = card.model_copy(update={"status": "EXPIRED"})
            conn.execute(
                "UPDATE virtual_cards SET payload_json = ?, status = 'EXPIRED' WHERE card_id = ?",
                (card.model_dump_json(), card_id),
            )
        return card


def list_virtual_cards(limit: int = 25, db_path: str | None = None) -> list[VirtualCard]:
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT card_id, payload_json FROM virtual_cards ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        cards: list[VirtualCard] = []
        now = datetime.now(timezone.utc)
        for r in rows:
            card = VirtualCard.model_validate_json(r["payload_json"])
            if card.status == "ACTIVE" and now > datetime.fromisoformat(card.expires_at):
                card = card.model_copy(update={"status": "EXPIRED"})
                conn.execute(
                    "UPDATE virtual_cards SET payload_json = ?, status = 'EXPIRED' WHERE card_id = ?",
                    (card.model_dump_json(), card.card_id),
                )
            cards.append(card)
        return cards


def record_settlement_and_debit(card: VirtualCard, amount_inr: float, db_path: str | None = None) -> MasterVault:
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE virtual_cards SET payload_json = ?, status = ? WHERE card_id = ?",
            (card.model_dump_json(), card.status, card.card_id),
        )
        conn.execute(
            "UPDATE master_vault SET balance_inr = balance_inr - ? WHERE vault_id = ?",
            (round(amount_inr, 2), DEFAULT_VAULT_ID),
        )
        conn.execute(
            "UPDATE agent_accounts SET spent_today_inr = spent_today_inr + ? WHERE agent_id = ?",
            (round(amount_inr, 2), card.agent_id),
        )
        conn.execute(
            "INSERT INTO transactions (tx_id, card_id, agent_id, merchant_name, merchant_mcc, amount_inr, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"tx_{uuid4().hex[:10]}", card.card_id, card.agent_id, card.merchant_name, card.merchant_mcc, round(amount_inr, 2), now_iso),
        )
    return get_vault(db_path)


def save_passkey_challenge(challenge: PasskeyChallenge, db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO passkey_challenges (challenge_id, agent_id, payload_json, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (challenge.challenge_id, challenge.agent_id, challenge.model_dump_json(), challenge.status, challenge.created_at),
        )


def get_passkey_challenge(challenge_id: str, db_path: str | None = None) -> PasskeyChallenge | None:
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT payload_json FROM passkey_challenges WHERE challenge_id = ?", (challenge_id,)).fetchone()
        if not r:
            return None
        return PasskeyChallenge.model_validate_json(r["payload_json"])


def list_passkeys(db_path: str | None = None) -> list[PasskeyChallenge]:
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT payload_json FROM passkey_challenges ORDER BY created_at DESC LIMIT 20").fetchall()
        return [PasskeyChallenge.model_validate_json(r["payload_json"]) for r in rows]


def record_spend_attempt_for_loop_check(agent_id: str, merchant_name: str, amount_inr: float, db_path: str | None = None) -> int:
    """Record attempt and return count of matching requests in the trailing 60-second window."""
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(seconds=60)).isoformat()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO spend_history (agent_id, merchant_name, amount_inr, created_at) VALUES (?, ?, ?, ?)",
            (agent_id, merchant_name.strip().lower(), round(float(amount_inr), 2), now.isoformat()),
        )
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM spend_history
            WHERE agent_id = ? AND merchant_name = ? AND amount_inr = ? AND created_at >= ?
            """,
            (agent_id, merchant_name.strip().lower(), round(float(amount_inr), 2), cutoff),
        ).fetchone()
        return int(row["cnt"]) if row else 1


def record_audit_event(
    trace_id: str,
    agent_id: str,
    event_type: str,
    decision: str,
    summary: str,
    metadata: dict | None = None,
    db_path: str | None = None,
) -> AuditEvent:
    evt = AuditEvent(
        event_id=f"evt_{uuid4().hex[:8]}",
        trace_id=trace_id,
        agent_id=agent_id,
        event_type=event_type,
        decision=decision,
        summary=summary,
        metadata=metadata or {},
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO audit_events (event_id, trace_id, agent_id, event_type, decision, summary, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evt.event_id,
                evt.trace_id,
                evt.agent_id,
                evt.event_type,
                evt.decision,
                evt.summary,
                json.dumps(evt.metadata),
                evt.created_at,
            ),
        )
    return evt


def list_audit_events(limit: int = 40, db_path: str | None = None) -> list[AuditEvent]:
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [
            AuditEvent(
                event_id=r["event_id"],
                trace_id=r["trace_id"],
                agent_id=r["agent_id"],
                event_type=r["event_type"],
                decision=r["decision"],
                summary=r["summary"],
                metadata=json.loads(r["metadata_json"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]
