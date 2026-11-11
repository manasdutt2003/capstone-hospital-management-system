"""Release 3 Feature 2: health check-up packages.

A package bundles lab tests and/or other packages (nesting). It answers
``price()`` exactly like a single ``LabTest`` so bills and menus can treat
either uniformly. A flat percentage discount is applied on the total.
"""


class HealthPackage:
    """A named bundle of tests and/or nested packages."""

    def __init__(self, name, items=None, discount_rate=0.0):
        if not str(name).strip():
            raise ValueError("A package needs a name.")
        if not 0.0 <= float(discount_rate) <= 0.9:
            raise ValueError("Discount rate must be between 0.0 and 0.9.")
        self.name = str(name).strip()
        self.items = list(items or [])
        self.discount_rate = float(discount_rate)

    def add(self, item):
        """Add a ``LabTest``/``HealthPackage`` (or anything with ``price()``)."""
        if not hasattr(item, "price"):
            raise ValueError("Package items must answer price().")
        self.items.append(item)
        return item

    def gross(self):
        """Sum of the nested prices before discount."""
        return round(sum(float(item.price()) for item in self.items), 2)

    def price(self):
        """Net price after the package discount (same name as LabTest)."""
        return round(self.gross() * (1.0 - self.discount_rate), 2)

    def to_bill_item(self):
        """Return the ``(description, amount)`` row for a bill."""
        return (f"Package: {self.name} ({len(self.items)} items, "
                f"{self.discount_rate:.0%} off)", self.price())

    def get_details(self):
        return (f"[Package] {self.name} | {len(self.items)} item(s) | "
                f"gross Rs.{self.gross():,.2f} | "
                f"net Rs.{self.price():,.2f}")

    def __str__(self):
        return f"{self.name}: Rs.{self.price():,.2f}"

    def __repr__(self):
        return (f"HealthPackage(name={self.name!r}, "
                f"items={len(self.items)!r})")

    def __len__(self):
        return len(self.items)

    def __contains__(self, item):
        return item in self.items
