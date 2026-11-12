from database import SessionLocal
from models.orm import User
from utils.security import hash_password


admins = [
    {
        "full_name": "Rahul Sharma",
        "email": "rahul.admin@test.com",
        "password": "Admin@12345",
        "phone": "9876543210",
    },
    {
        "full_name": "Priya Verma",
        "email": "priya.admin@test.com",
        "password": "Admin@67890",
        "phone": "9876543211",
    },
]


def seed_admins():
    db = SessionLocal()

    try:
        for admin in admins:
            existing_user = db.query(User).filter(
                User.email == admin["email"]
            ).first()

            if existing_user:
                # print(f"Already exists: {admin['email']}")
                continue

            new_admin = User(
                full_name=admin["full_name"],
                email=admin["email"],
                hashed_password=hash_password(admin["password"]),
                phone=admin["phone"],
                role="admin",
                is_active=True,
            )

            db.add(new_admin)
            # print(f"Created admin: {admin['email']}")

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_admins()
