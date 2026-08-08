from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.chat import ApiModel

MissingItineraryField = Literal["destination", "durationDays", "numPeople", "budgetVnd"]
ItineraryStatus = Literal["needs_clarification", "ready"]


class ItineraryRequest(ApiModel):
    destination: str | None = Field(default=None, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    duration_days: int | None = Field(default=None, ge=1, le=14)
    num_people: int | None = Field(default=None, ge=1, le=50)
    budget_vnd: int | None = Field(default=None, ge=0)
    preferences: list[str] = Field(default_factory=list, max_length=8)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_dates(self) -> "ItineraryRequest":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("endDate phải bằng hoặc sau startDate")
        return self

    def resolved_duration_days(self) -> int | None:
        if self.duration_days is not None:
            return self.duration_days
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None


class ItineraryActivity(ApiModel):
    period: Literal["morning", "afternoon", "evening"]
    title: str = Field(min_length=1, max_length=160)
    place_name: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=300)


class ItineraryDay(ApiModel):
    day: int = Field(ge=1, le=14)
    title: str = Field(min_length=1, max_length=160)
    activities: list[ItineraryActivity] = Field(min_length=1, max_length=6)


class BudgetBreakdown(ApiModel):
    accommodation_vnd: int = Field(ge=0)
    food_vnd: int = Field(ge=0)
    transport_vnd: int = Field(ge=0)
    activities_vnd: int = Field(ge=0)
    reserve_vnd: int = Field(ge=0)
    total_vnd: int = Field(ge=0)


class ItineraryPlan(ApiModel):
    destination: str
    duration_days: int
    num_people: int
    summary: str = Field(min_length=1, max_length=500)
    assumptions: list[str] = Field(default_factory=list, max_length=8)
    days: list[ItineraryDay]
    budget: BudgetBreakdown


class ItineraryResponse(ApiModel):
    status: ItineraryStatus
    missing_fields: list[MissingItineraryField] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list, max_length=4)
    plan: ItineraryPlan | None = None
    provider: Literal["mock", "gemini", "local"] | None = None
