"""Support-ticket endpoints backed by an in-memory store.

No database, no auth — this exists to give the CI/CD pipeline
something to lint, test, build, and push.
"""

from itertools import count
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tickets", tags=["tickets"])

Priority = Literal["low", "normal", "high"]
Status = Literal["open", "closed"]


class TicketIn(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    priority: Priority = "normal"


class TicketOut(BaseModel):
    id: int
    subject: str
    message: str
    priority: Priority
    status: Status


_tickets: dict[int, TicketOut] = {}
_ids = count(1)


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(payload: TicketIn) -> TicketOut:
    ticket = TicketOut(id=next(_ids), status="open", **payload.model_dump())
    _tickets[ticket.id] = ticket
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets() -> list[TicketOut]:
    return sorted(_tickets.values(), key=lambda t: t.id)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int) -> TicketOut:
    ticket = _tickets.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket


@router.post("/{ticket_id}/close", response_model=TicketOut)
def close_ticket(ticket_id: int) -> TicketOut:
    ticket = _tickets.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    closed = ticket.model_copy(update={"status": "closed"})
    _tickets[ticket_id] = closed
    return closed
