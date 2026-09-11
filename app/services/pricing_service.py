import math
from app.core.config import Settings, get_settings
from app.models.order import PricingBreakdown, PrintConfig


class PricingValidationError(Exception):
    """Raised when print configuration or pricing input is invalid."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class PricingService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def normalize_color_mode(self, color_mode: str) -> str:
        """Validate and normalize color mode ('bw' vs 'color')."""
        mode = color_mode.strip().lower()
        if mode in ("bw", "b&w", "black_and_white", "grayscale", "mono"):
            return "bw"
        if mode in ("color", "colour"):
            return "color"
        raise PricingValidationError(
            "UNSUPPORTED_COLOR_MODE",
            f"Color mode '{color_mode}' is not supported. Supported modes: bw, color.",
        )

    def normalize_paper_size(self, paper_size: str) -> str:
        """Validate and normalize paper size ('A4', 'A3', 'Letter')."""
        size = paper_size.strip().upper()
        if size == "A4":
            return "A4"
        if size == "A3":
            return "A3"
        if size in ("LETTER", "LTR"):
            return "Letter"
        raise PricingValidationError(
            "UNSUPPORTED_PAPER_SIZE",
            f"Paper size '{paper_size}' is not supported. Supported sizes: A4, A3, Letter.",
        )

    def calculate_pricing(
        self,
        page_count: int,
        color_mode: str = "bw",
        paper_size: str = "A4",
        copies: int = 1,
        double_sided: bool = False,
    ) -> tuple[PrintConfig, PricingBreakdown]:
        """
        Calculate deterministic print pricing based on pages, color mode, paper size,
        copies, and single/double-sided options.
        All currency calculations are grounded in integer paise to avoid float errors.
        """
        if page_count < 1:
            raise PricingValidationError(
                "INVALID_PAGE_COUNT", "page_count must be at least 1."
            )
        if copies < 1:
            raise PricingValidationError(
                "INVALID_COPIES", "copies must be at least 1."
            )

        norm_color = self.normalize_color_mode(color_mode)
        norm_paper = self.normalize_paper_size(paper_size)

        # Base rate per page
        if norm_color == "color":
            base_rate = self.settings.price_per_page_color
        else:
            base_rate = self.settings.price_per_page_bw

        # Paper multiplier
        paper_multiplier = self.settings.paper_size_multipliers.get(
            norm_paper.lower(), 1.0
        )

        # Sheets per copy
        if double_sided:
            sheets_per_copy = (page_count + 1) // 2
            double_sheets = page_count // 2
            single_sheets = page_count % 2

            # 20% discount on print cost for 2-sided sheets
            cost_2sided_sheet = round(
                2 * base_rate * paper_multiplier * self.settings.double_sided_discount_factor
            )
            cost_single_sheet = round(1 * base_rate * paper_multiplier)
            unit_price_paise = (double_sheets * cost_2sided_sheet) + (
                single_sheets * cost_single_sheet
            )
        else:
            sheets_per_copy = page_count
            unit_price_paise = round(page_count * base_rate * paper_multiplier)

        total_sheets = sheets_per_copy * copies
        total_pages_printed = page_count * copies
        total_price_paise = unit_price_paise * copies
        total_price_rupees = round(total_price_paise / 100.0, 2)

        config = PrintConfig(
            page_count=page_count,
            color_mode=norm_color,
            paper_size=norm_paper,
            copies=copies,
            double_sided=double_sided,
        )

        breakdown = PricingBreakdown(
            base_rate_per_page_paise=base_rate,
            paper_multiplier=paper_multiplier,
            sheets_per_copy=sheets_per_copy,
            total_sheets=total_sheets,
            total_pages_printed=total_pages_printed,
            unit_price_paise=unit_price_paise,
            total_price_paise=total_price_paise,
            total_price_rupees=total_price_rupees,
            currency="INR",
        )

        return config, breakdown
