"""Reports built from iterators and generators (Release 2, scenario 11).

The reports never print: they return rows (dictionaries), so the same code
serves the menu, the tests and a future export. The patient iterators are
generators, so records are produced one at a time instead of building a big
list in memory.
"""

from datetime import date


class Reports:
    """Read-only reporting views over a :class:`Hospital`."""

    #: Revenue buckets of the daily report, in printing order.
    REVENUE_CATEGORIES = ("OPD", "IPD", "Pharmacy", "Refunds")

    def __init__(self, hospital):
        self.hospital = hospital

    def daily_revenue(self, on_date=None):
        """Rows for one day: OPD, IPD, Pharmacy and Refunds.

        Medicine lines are pulled out of the bills into the Pharmacy bucket,
        so the four buckets add up to the day's net revenue without counting
        a rupee twice. Refunds are negative.
        """
        day = on_date or date.today()
        totals = {"OPD": 0.0, "IPD": 0.0, "Pharmacy": 0.0, "Refunds": 0.0}
        for bill in self.hospital.bills:
            if bill.issued_on != day:
                continue
            pharmacy = bill.amount_for("medicines")
            totals["Pharmacy"] += pharmacy
            rest = round(bill.total - pharmacy, 2)
            if bill.care_type == "IPD":
                totals["IPD"] += rest
            else:
                totals["OPD"] += rest
        for refund in self.hospital.refunds:
            if refund["on_date"] == day:
                totals["Refunds"] -= refund["amount"]
        return [
            {"category": category, "amount": round(totals[category], 2)}
            for category in self.REVENUE_CATEGORIES
        ]

    def doctor_earnings(self):
        """Doctor-wise earnings from completed visits, highest first."""
        earnings = {}
        for doctor in self.hospital.all_doctors():
            earnings[doctor] = {"doctor": doctor, "consultations": 0,
                                "earnings": 0.0}
        for appointment in self.hospital.appointments:
            if not appointment.is_completed():
                continue
            row = earnings.setdefault(
                appointment.doctor,
                {"doctor": appointment.doctor, "consultations": 0,
                 "earnings": 0.0},
            )
            row["consultations"] += 1
            row["earnings"] += appointment.doctor.consultation_fee
        rows = list(earnings.values())
        for row in rows:
            row["earnings"] = round(row["earnings"], 2)
        rows.sort(key=lambda row: row["earnings"], reverse=True)
        return rows

    def ward_occupancy(self):
        """Occupancy percentage per ward, in registration order."""
        rows = []
        for ward in self.hospital.wards.values():
            percentage = (
                round(ward.occupied_count * 100 / ward.total_beds, 1)
                if ward.total_beds
                else 0.0
            )
            rows.append(
                {
                    "ward": ward.ward_type,
                    "occupied": ward.occupied_count,
                    "total": ward.total_beds,
                    "percentage": percentage,
                }
            )
        return rows

    def patients_admitted_longer_than(self, days):
        """Generator: admitted patients whose stay exceeds ``days``."""
        for patient in self.hospital:
            if patient.is_admitted and patient.days_admitted > days:
                yield patient

    def discharge_state_summary(self):
        """Counts per discharge state, for the operations dashboard."""
        summary = {}
        for patient in self.hospital:
            if patient.discharge_state is None:
                continue
            name = patient.discharge_state.name
            summary[name] = summary.get(name, 0) + 1
        return summary