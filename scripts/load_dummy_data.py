"""Load dummy data into ChromaDB for testing the full pipeline.

Usage:
    python -m scripts.load_dummy_data
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

from mindpalace.models import Document, ContentType
from mindpalace.pipeline.chunker import chunk_document
from mindpalace.pipeline.embedder import embed_chunks
from mindpalace.store.vectordb import upsert_chunks, delete_by_document_id

_NOW = datetime.now(timezone.utc)


def _dummy_documents() -> list[Document]:
    return [
        # --- Emails ---
        Document(
            source="gmail",
            source_id="msg_001",
            title="Your Amazon order has shipped",
            content=(
                "Hi Siddhant,\n\n"
                "Great news! Your order #112-9834567-1234567 has shipped.\n\n"
                "Items:\n"
                "- Sony WH-1000XM5 Headphones — $278.00\n"
                "- USB-C Cable 6ft (2-pack) — $9.99\n\n"
                "Estimated delivery: April 20, 2026\n"
                "Tracking number: 1Z999AA10123456784\n\n"
                "Thank you for shopping with us!\n"
                "Amazon.com"
            ),
            content_type=ContentType.EMAIL,
            created_at=_NOW - timedelta(days=2),
            metadata={
                "sender": "shipment-tracking@amazon.com",
                "recipients": ["siddhant@example.com"],
                "subject": "Your Amazon order has shipped",
                "labels": ["Inbox", "Purchases"],
                "thread_id": "thread_amazon_001",
                "has_attachments": False,
            },
        ),
        Document(
            source="gmail",
            source_id="msg_002",
            title="Flight Confirmation - DEL to BLR",
            content=(
                "Booking Confirmed!\n\n"
                "Passenger: Siddhant Kushwaha\n"
                "Flight: 6E 2145\n"
                "Route: New Delhi (DEL) → Bengaluru (BLR)\n"
                "Date: May 5, 2026\n"
                "Departure: 06:30 AM\n"
                "Arrival: 09:15 AM\n"
                "PNR: ABC123\n"
                "Booking Reference: INDIG-789456\n\n"
                "Total paid: ₹4,532.00\n\n"
                "Please arrive at the airport at least 2 hours before departure.\n"
                "Web check-in opens 48 hours before the flight."
            ),
            content_type=ContentType.EMAIL,
            created_at=_NOW - timedelta(days=5),
            metadata={
                "sender": "booking@goindigo.in",
                "recipients": ["siddhant@example.com"],
                "subject": "Flight Confirmation - DEL to BLR",
                "labels": ["Inbox", "Travel"],
                "thread_id": "thread_indigo_001",
                "has_attachments": True,
                "attachment_names": ["e-ticket.pdf"],
            },
        ),
        Document(
            source="gmail",
            source_id="msg_003",
            title="Monthly credit card statement - April 2026",
            content=(
                "HDFC Bank Credit Card Statement\n"
                "Statement Period: March 1 - March 31, 2026\n"
                "Card ending: **4589\n\n"
                "Transactions:\n"
                "Mar 02  Swiggy             ₹456.00\n"
                "Mar 05  Netflix             ₹649.00\n"
                "Mar 08  Amazon              ₹2,399.00\n"
                "Mar 12  Uber                ₹234.00\n"
                "Mar 15  Spotify             ₹119.00\n"
                "Mar 18  BigBasket           ₹1,876.00\n"
                "Mar 22  Zomato              ₹389.00\n"
                "Mar 28  Apple iCloud        ₹75.00\n\n"
                "Total Due: ₹6,197.00\n"
                "Minimum Due: ₹310.00\n"
                "Due Date: April 18, 2026\n"
            ),
            content_type=ContentType.EMAIL,
            created_at=_NOW - timedelta(days=1),
            metadata={
                "sender": "statements@hdfcbank.net",
                "recipients": ["siddhant@example.com"],
                "subject": "Your HDFC Credit Card Statement - April 2026",
                "labels": ["Inbox", "Finance"],
                "thread_id": "thread_hdfc_001",
                "has_attachments": True,
                "attachment_names": ["statement_april_2026.pdf"],
            },
        ),
        # --- Notes ---
        Document(
            source="google_keep",
            source_id="note_001",
            title="Project Ideas",
            content=(
                "Project Ideas:\n\n"
                "1. MindPalace - Personal RAG agent that indexes all my data\n"
                "2. Recipe organizer with nutrition tracking\n"
                "3. Automated resume tailoring using job descriptions\n"
                "4. Home automation dashboard with energy monitoring\n"
                "5. Reading list tracker with Goodreads integration"
            ),
            content_type=ContentType.NOTE,
            created_at=_NOW - timedelta(days=30),
            metadata={
                "labels": ["Ideas", "Tech"],
                "color": "BLUE",
                "is_pinned": True,
                "is_archived": False,
            },
        ),
        Document(
            source="google_keep",
            source_id="note_002",
            title="Grocery List",
            content=(
                "Grocery List:\n"
                "- Milk\n"
                "- Eggs (1 dozen)\n"
                "- Bread (whole wheat)\n"
                "- Bananas\n"
                "- Chicken breast (1 kg)\n"
                "- Rice (5 kg basmati)\n"
                "- Onions\n"
                "- Tomatoes\n"
                "- Olive oil\n"
                "- Greek yogurt"
            ),
            content_type=ContentType.CHECKLIST,
            created_at=_NOW - timedelta(days=1),
            metadata={
                "labels": ["Shopping"],
                "color": "GREEN",
                "is_pinned": False,
                "is_archived": False,
            },
        ),
        Document(
            source="google_keep",
            source_id="note_003",
            title="Workout Routine",
            content=(
                "Weekly Workout Routine:\n\n"
                "Monday: Chest + Triceps\n"
                "- Bench press 4x8\n"
                "- Incline dumbbell press 3x10\n"
                "- Cable flyes 3x12\n"
                "- Tricep dips 3x10\n\n"
                "Tuesday: Back + Biceps\n"
                "- Deadlift 4x6\n"
                "- Pull-ups 3x8\n"
                "- Barbell rows 3x10\n"
                "- Hammer curls 3x12\n\n"
                "Wednesday: Rest / Light cardio\n\n"
                "Thursday: Shoulders + Abs\n"
                "- OHP 4x8\n"
                "- Lateral raises 3x12\n"
                "- Face pulls 3x15\n"
                "- Planks 3x60s\n\n"
                "Friday: Legs\n"
                "- Squats 4x8\n"
                "- Leg press 3x10\n"
                "- Romanian deadlift 3x10\n"
                "- Calf raises 4x15\n\n"
                "Saturday & Sunday: Rest"
            ),
            content_type=ContentType.NOTE,
            created_at=_NOW - timedelta(days=14),
            metadata={
                "labels": ["Fitness"],
                "color": "RED",
                "is_pinned": True,
                "is_archived": False,
            },
        ),
        # --- Bookmarks ---
        Document(
            source="chrome_bookmarks",
            source_id="bk_001",
            title="FastAPI Documentation",
            content=(
                "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ "
                "based on standard Python type hints. Key features include automatic API documentation with Swagger UI, "
                "dependency injection, async support, data validation via Pydantic, WebSocket support, "
                "and performance on par with NodeJS and Go. FastAPI is built on top of Starlette for the web parts "
                "and Pydantic for the data parts."
            ),
            content_type=ContentType.BOOKMARK,
            url="https://fastapi.tiangolo.com/",
            created_at=_NOW - timedelta(days=60),
            metadata={
                "folder_path": "Bookmarks Bar/Dev/Python",
                "date_added": (_NOW - timedelta(days=60)).isoformat(),
            },
        ),
        Document(
            source="chrome_bookmarks",
            source_id="bk_002",
            title="ChromaDB - the AI-native open-source embedding database",
            content=(
                "Chroma is the open-source AI-native embedding database. Chroma makes it easy to build LLM apps "
                "by making knowledge, facts, and skills pluggable for LLMs. Key features: simple API, "
                "runs in-process or client-server, supports filtering by metadata, "
                "integrates with LangChain, LlamaIndex, and OpenAI. "
                "Chroma stores embeddings alongside metadata and documents, "
                "enabling hybrid search with vector similarity and metadata filtering."
            ),
            content_type=ContentType.BOOKMARK,
            url="https://www.trychroma.com/",
            created_at=_NOW - timedelta(days=45),
            metadata={
                "folder_path": "Bookmarks Bar/Dev/AI",
                "date_added": (_NOW - timedelta(days=45)).isoformat(),
            },
        ),
        # --- Documents ---
        Document(
            source="google_drive",
            source_id="doc_001",
            title="Meeting Notes - Q1 2026 Planning",
            content=(
                "Q1 2026 Planning Meeting\n"
                "Date: January 10, 2026\n"
                "Attendees: Siddhant, Priya, Rohit, Ananya\n\n"
                "Agenda:\n"
                "1. Review Q4 2025 results\n"
                "2. Set Q1 2026 OKRs\n"
                "3. Budget allocation\n"
                "4. Hiring plan\n\n"
                "Key Decisions:\n"
                "- Increase infra budget by 20% for GPU instances\n"
                "- Hire 2 ML engineers and 1 backend engineer by March\n"
                "- Launch internal AI assistant pilot by end of February\n"
                "- Migrate remaining services to Kubernetes by Q1 end\n\n"
                "Action Items:\n"
                "- Siddhant: Draft AI assistant PRD by Jan 20\n"
                "- Priya: Finalize hiring JDs by Jan 15\n"
                "- Rohit: K8s migration timeline by Jan 17\n"
                "- Ananya: Budget proposal to finance by Jan 22"
            ),
            content_type=ContentType.DOCUMENT,
            created_at=_NOW - timedelta(days=90),
            metadata={
                "mime_type": "application/vnd.google-apps.document",
                "owner": "siddhant@example.com",
                "shared_with": ["priya@example.com", "rohit@example.com", "ananya@example.com"],
                "folder_path": "Work/Meetings/2026",
            },
        ),
        Document(
            source="google_drive",
            source_id="doc_002",
            title="Apartment Lease Agreement",
            content=(
                "RESIDENTIAL LEASE AGREEMENT\n\n"
                "Landlord: Rajesh Sharma\n"
                "Tenant: Siddhant Kushwaha\n\n"
                "Property: Flat 402, Tower B, Prestige Lakeside Habitat, Whitefield, Bengaluru 560066\n\n"
                "Lease Term: 11 months\n"
                "Start Date: March 1, 2026\n"
                "End Date: January 31, 2027\n\n"
                "Monthly Rent: ₹35,000\n"
                "Security Deposit: ₹1,05,000 (3 months rent)\n"
                "Maintenance: ₹4,500/month (paid separately to society)\n\n"
                "Payment: Due on 1st of each month via bank transfer\n"
                "Account: HDFC Bank, A/C 50100XXXXXXX789, IFSC: HDFC0001234\n\n"
                "Notice Period: 2 months from either party\n"
                "Lock-in Period: 6 months"
            ),
            content_type=ContentType.DOCUMENT,
            created_at=_NOW - timedelta(days=45),
            metadata={
                "mime_type": "application/pdf",
                "owner": "siddhant@example.com",
                "folder_path": "Personal/Housing",
                "file_size": 245000,
            },
        ),
    ]


def ingest_documents(docs: list[Document]) -> int:
    total_chunks = 0
    for doc in docs:
        # Delete any existing chunks for this document (re-ingestion)
        delete_by_document_id(doc.id)
        # Chunk → Embed → Upsert
        chunks = chunk_document(doc)
        chunks = embed_chunks(chunks)
        upsert_chunks(chunks)
        total_chunks += len(chunks)
        print(f"  [{doc.source}] {doc.title} → {len(chunks)} chunks")
    return total_chunks


def main():
    import sys
    user_id = sys.argv[1] if len(sys.argv) > 1 else ""
    docs = _dummy_documents()
    if user_id:
        for doc in docs:
            doc.user_id = user_id
        print(f"Loading {len(docs)} dummy documents for user {user_id}...")
    else:
        print(f"Loading {len(docs)} dummy documents (no user scope)...")
    total = ingest_documents(docs)
    print(f"Done! {total} chunks indexed.")


if __name__ == "__main__":
    main()
