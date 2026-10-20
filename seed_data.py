"""
Sample Data Seeder - Officers Affairs Management System
Run this once to populate the database with realistic test data.
Usage: python seed_data.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.services import ServiceLocator
from models.models import (
    Officer, AttendanceRecord, LeaveRequest,
    DailyDuty, MealRecord, PromotionHistory
)


def random_date(start_year=2000, end_year=2022) -> str:
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")


def seed(db_path: str = "data/officers_affairs.db"):
    svc = ServiceLocator(db_path)

    print("Seeding officers...")
    first_names = ["Ahmed", "Mohammed", "Khalid", "Omar", "Ali", "Hassan",
                   "Ibrahim", "Youssef", "Tariq", "Samir", "Nasser", "Faisal",
                   "Walid", "Karim", "Bilal", "Ziad", "Rami", "Sami", "Adel", "Hani"]
    last_names  = ["Al-Rashid", "Al-Farsi", "Al-Mansouri", "Al-Zahrani",
                   "Al-Shehri", "Al-Otaibi", "Al-Qahtani", "Al-Harbi",
                   "Al-Dosari", "Al-Mutairi", "Al-Ghamdi", "Al-Shahrani",
                   "Al-Maliki", "Al-Anazi", "Al-Balawi"]

    ranks   = svc.reference.get_ranks()
    depts   = svc.reference.get_departments()
    units   = svc.reference.get_units()

    blood_types    = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
    marital_status = ["Single","Married","Divorced","Widowed"]
    statuses       = ["Active","Active","Active","Active","On Leave","Suspended","Retired"]

    officer_ids = []
    for i in range(1, 51):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        rank = random.choice(ranks)
        dept = random.choice(depts)
        unit = random.choice([u for u in units if u.department_id == dept.id] or units)

        o = Officer(
            officer_number   = f"OFC{i:04d}",
            full_name        = f"{fn} {ln}",
            rank_id          = rank.id,
            national_id      = f"{random.randint(1000000000, 9999999999)}",
            date_of_birth    = random_date(1970, 1998),
            address          = f"Block {random.randint(1,20)}, Street {random.randint(1,50)}, House {random.randint(1,100)}",
            phone            = f"05{random.randint(10000000, 99999999)}",
            emergency_contact= f"05{random.randint(10000000, 99999999)}",
            marital_status   = random.choice(marital_status),
            blood_type       = random.choice(blood_types),
            department_id    = dept.id,
            unit_id          = unit.id,
            job_position     = f"Field Officer Level {random.randint(1,5)}",
            date_of_joining  = random_date(2000, 2023),
            current_status   = random.choice(statuses),
        )
        ok, msg = svc.officers.save(o)
        if ok and o.id:
            officer_ids.append(o.id)
            print(f"  + {o.full_name} [{rank.name}]")

    print(f"\nSeeded {len(officer_ids)} officers.")

    # Promotions for some officers
    print("\nSeeding promotion history...")
    for oid in random.sample(officer_ids, min(15, len(officer_ids))):
        ph = PromotionHistory(
            officer_id    = oid,
            previous_rank = random.choice(ranks).name,
            new_rank      = random.choice(ranks).name,
            promotion_date= random_date(2010, 2024),
            notes         = "Based on performance review.",
        )
        svc.officers.add_promotion(ph)
    print("  Promotions seeded.")

    # Attendance - last 30 days for active officers
    print("\nSeeding attendance records (last 30 days)...")
    active_ids = [o.id for o in svc.officers.get_all(status="Active")]
    statuses_att = ["Present","Present","Present","Present","Present","Late","Absent","Leave"]
    today = datetime.now()
    att_count = 0
    for days_ago in range(29, -1, -1):
        date_str = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        for oid in active_ids[:30]:  # limit to 30 officers for speed
            rec = AttendanceRecord(
                officer_id = oid,
                date       = date_str,
                check_in   = f"{random.randint(6,9):02d}:{random.randint(0,59):02d}",
                check_out  = f"{random.randint(14,18):02d}:{random.randint(0,59):02d}",
                status     = random.choice(statuses_att),
            )
            svc.attendance.save(rec)
            att_count += 1
    print(f"  {att_count} attendance records seeded.")

    # Leave requests
    print("\nSeeding leave requests...")
    leave_types = svc.reference.get_leave_types()
    leave_statuses = ["Pending","Approved","Approved","Rejected"]
    for _ in range(25):
        oid   = random.choice(officer_ids)
        start = random_date(2024, 2025)
        sd    = datetime.strptime(start, "%Y-%m-%d")
        days  = random.randint(2, 14)
        end   = (sd + timedelta(days=days)).strftime("%Y-%m-%d")
        lt    = random.choice(leave_types)
        lr    = LeaveRequest(
            officer_id      = oid,
            leave_type_id   = lt.id,
            start_date      = start,
            end_date        = end,
            approval_status = random.choice(leave_statuses),
            notes           = "Requested via department.",
        )
        svc.leaves.save(lr)
    print("  25 leave requests seeded.")

    # Daily duties - last 7 days
    print("\nSeeding daily duties...")
    shifts      = ["Morning","Afternoon","Night","Full Day"]
    assignments = ["Patrol Duty","Gate Security","Investigation","Traffic Control",
                   "Community Patrol","Forensics Support","K9 Support","Administrative"]
    locations   = ["Zone A","Zone B","Zone C","HQ","North District",
                   "South District","Central Station","Airport"]
    duty_statuses = ["Pending","Completed","Completed","Partial","Cancelled"]
    for days_ago in range(6, -1, -1):
        date_str = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        for oid in random.sample(active_ids[:30], min(10, len(active_ids))):
            d = DailyDuty(
                officer_id       = oid,
                duty_date        = date_str,
                shift            = random.choice(shifts),
                assignment       = random.choice(assignments),
                duty_location    = random.choice(locations),
                completion_status= random.choice(duty_statuses),
                notes            = "",
            )
            svc.duties.save(d)
    print("  Duties seeded.")

    # Meals - last 7 days
    print("\nSeeding meal records...")
    meal_types = ["Breakfast","Lunch","Dinner"]
    for days_ago in range(6, -1, -1):
        date_str = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        for oid in active_ids[:30]:
            for mt in random.sample(meal_types, random.randint(1, 3)):
                m = MealRecord(
                    officer_id = oid,
                    meal_date  = date_str,
                    meal_type  = mt,
                    quantity   = random.randint(1, 2),
                )
                svc.meals.save(m)
    print("  Meal records seeded.")

    print("\n✅ Sample data seeding complete!")
    print(f"   Database: {os.path.abspath(db_path)}")


if __name__ == "__main__":
    seed()
