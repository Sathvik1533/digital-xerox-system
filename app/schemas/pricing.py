from pydantic import BaseModel, ConfigDict, Field


class QuoteRequest(BaseModel):
    """Request schema for calculating a live print pricing quote."""
    model_config = ConfigDict(extra="ignore")

    page_count: int = Field(..., description="Number of pages to print per copy")
    color_mode: str = Field(default="bw", description="Print color mode ('bw' or 'color')")
    paper_size: str = Field(default="A4", description="Paper size ('A4', 'A3', 'Letter')")
    copies: int = Field(default=1, description="Number of copies")
    double_sided: bool = Field(default=False, description="Whether to print double-sided")
    sidedness: str | None = Field(default=None, description="Print sidedness: 'SINGLE' or 'DOUBLE'")


class QuoteResponse(BaseModel):
    """Response schema for pricing quote."""
    model_config = ConfigDict(extra="ignore")

    page_count: int
    color_mode: str
    paper_size: str
    copies: int
    double_sided: bool
    sidedness: str
    sheets_per_copy: int
    total_sheets: int
    total_pages_printed: int
    base_rate_per_page_paise: int
    paper_multiplier: float
    unit_price_paise: int
    total_price_paise: int
    total_price_rupees: float
    currency: str = "INR"
