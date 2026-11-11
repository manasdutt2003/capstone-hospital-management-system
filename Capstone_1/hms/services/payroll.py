"""Release 3 Feature 4: staff payroll.

Salary = ``base_salary`` + role allowance, less 10% tax on the amount above
Rs.50,000. ``calculate_salary(staff)`` works per staff type without any
``isinstance`` chain in calling code beyond role lookup; ``Payroll`` keeps
the payout ledger.
"""

#: Tax applies only above this monthly amount.
TAX_THRESHOLD = 50000.0
#: Tax rate on the slice above the threshold.
TAX_RATE = 0.10

#: Night-shift allowance for nurses.
NIGHT_ALLOWANCE = 2000.0
#: Senior-doctor responsibility allowance.
SENIOR_ALLOWANCE = 15000.0
#: Doctor procedure allowance (10% of consultation fee, one visit proxy).
DOCTOR_PROC_RATE = 0.10


def gross_salary(staff):
    """Return the pre-tax monthly salary for any staff object."""
    base = float(getattr(staff, "base_salary", 0.0))
    role = staff.get_role() if hasattr(staff, "get_role") else ""
    extra = 0.0
    if role == "Senior doctor":
        extra += SENIOR_ALLOWANCE
    elif role == "Doctor":
        extra += float(getattr(staff, "consultation_fee", 0.0)) * DOCTOR_PROC_RATE
    elif role == "Nurse" and getattr(staff, "shift", "") == "Night":
        extra += NIGHT_ALLOWANCE
    return round(base + extra, 2)


def tax_on(gross):
    """Return the 10% tax on the slice above Rs.50,000."""
    if gross <= TAX_THRESHOLD:
        return 0.0
    return round((gross - TAX_THRESHOLD) * TAX_RATE, 2)


def calculate_salary(staff):
    """Return the net monthly salary for ``staff``."""
    gross = gross_salary(staff)
    return round(gross - tax_on(gross), 2)


class Payroll:
    """Ledger of salary payouts."""

    def __init__(self):
        self.records = []  # (staff_id, name, role, gross, tax, net)

    def pay(self, staff):
        gross = gross_salary(staff)
        tax = tax_on(gross)
        net = round(gross - tax, 2)
        record = (staff.person_id, staff.name, staff.get_role(),
                  gross, tax, net)
        self.records.append(record)
        return net

    def total_payout(self):
        return round(sum(r[5] for r in self.records), 2)

    def __len__(self):
        return len(self.records)
