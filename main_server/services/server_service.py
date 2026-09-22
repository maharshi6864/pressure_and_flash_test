from core.security import get_password_hash
from models.db_models import User
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from services.sync_service import sync_service


async def startup_checks(engine):
    # Ensure any new columns exist in the PostgreSQL database (safe migration)
    try:
        with engine.connect() as conn:
            # Users table migrations
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password VARCHAR;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))

            # Flash tests table migrations
            conn.execute(text("ALTER TABLE flash_tests ADD COLUMN IF NOT EXISTS flash_detected_image_path VARCHAR;"))
            conn.execute(text("ALTER TABLE flash_tests ADD COLUMN IF NOT EXISTS flash_image_path VARCHAR;"))

            # Proofs table migrations
            proof_columns = [
                ("detonator_type", "VARCHAR DEFAULT '356_LZ'"),
                ("sample_received_on", "DATE"),
                ("proof_results", "VARCHAR"),
                ("date_of_proof", "DATE"),
                ("schedule_ref", "VARCHAR"),
                ("drop_test_sample_size", "INTEGER"),
                ("drop_test_date", "DATE"),
                ("drop_test_obs", "VARCHAR"),
                ("drop_test_remarks", "VARCHAR"),
                ("sensitivity_test_sample_size", "INTEGER"),
                ("sensitivity_test_date", "DATE"),
                ("sensitivity_test_obs", "VARCHAR"),
                ("sensitivity_test_remarks", "VARCHAR"),
                ("sens_upper_sample_size", "INTEGER"),
                ("sens_upper_date", "DATE"),
                ("sens_upper_obs", "VARCHAR"),
                ("sens_upper_remarks", "VARCHAR"),
                ("sens_lower_sample_size", "INTEGER"),
                ("sens_lower_date", "DATE"),
                ("sens_lower_obs", "VARCHAR"),
                ("sens_lower_remarks", "VARCHAR"),
                ("flash_test_sample_size", "INTEGER"),
                ("flash_test_date", "DATE"),
                ("flash_test_obs", "VARCHAR"),
                ("flash_test_remarks", "VARCHAR"),
                ("pressure_test_sample_size", "INTEGER"),
                ("pressure_test_date", "DATE"),
                ("pressure_test_obs", "VARCHAR"),
                ("pressure_test_remarks", "VARCHAR"),
            ]
            for col_name, col_type in proof_columns:
                conn.execute(text(f"ALTER TABLE proofs ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))

            conn.commit()
    except Exception as e:
        print(f"[DB INIT] Column migration notice: {e}")

    with Session(engine) as session:
        admin_user = session.scalar(
            select(User).where(User.username == "admin")
        )

        if not admin_user:
            admin = User(
                name="Administrator",
                username="admin",
                password="admin",
                hashed_password="admin",
                role="admin"
            )
            session.add(admin)
            session.commit()
            print("[AUTH] Default admin user initialized with username: admin and password: admin")
        else:
            # Ensure admin has plain password and name populated
            if not admin_user.password:
                admin_user.password = "admin"
            if not admin_user.name:
                admin_user.name = "Administrator"
            admin_user.role = "admin"
            session.commit()
            print("[AUTH] Admin user verified")

    await sync_service.inform_servers_alive_status()