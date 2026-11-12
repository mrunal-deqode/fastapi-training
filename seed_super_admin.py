from database import SessionLocal
from models.orm import User
from utils.security import hash_password


def seed_super_admin():
    db = SessionLocal()

    try:
        email = "superadmin@test.com"

        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            #print("Super Admin already exists.")
            return

        super_admin = User(
            full_name="System Super Admin",
            email=email,
            hashed_password=hash_password("SuperAdmin@123"),
            phone="9876543212",
            role="super_admin",
            is_active=True,
        )

        db.add(super_admin)
        db.commit()

        #print("Super Admin created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_super_admin()
