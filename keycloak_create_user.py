"""

Purpose: Keycloak user creation functionality for SaaS project, adaptor from SaaS platform to AFIS' Keycloak.

Author: Kirodh Boodhraj

02 December 2025

"""

import os
from keycloak import KeycloakAdmin, KeycloakGetError

# please fill these in for you admin user:
KEYCLOAK_SERVER_URL = "https://keycloak.afis.co.za/"
# test
KEYCLOAK_REALM = "SAAS-TEST"
# Production
# KEYCLOAK_REALM = "AS"

ADMIN_USERNAME = "saas@csir.co.za"
ADMIN_PASSWORD = "saas"

# -------------------------------------------------------
# 1. Connect using admin credentials
# -------------------------------------------------------
try:
    keycloak_admin = KeycloakAdmin(
        server_url=KEYCLOAK_SERVER_URL,
        username=ADMIN_USERNAME,
        password=ADMIN_PASSWORD,
        realm_name=KEYCLOAK_REALM,
        verify=True
    )
    print("Connected to Keycloak admin API.")
except Exception as e:
    print("Failed to connect to Keycloak:", e)
    raise


# -------------------------------------------------------
# 2. Create user function (safe)
# -------------------------------------------------------
def create_user(email, first_name, last_name, password, groups=None):
    """Safely create a Keycloak user with full exception handling."""

    # -----------------------
    # Check if user exists
    # -----------------------
    try:
        existing_id = keycloak_admin.get_user_id(email)
        if existing_id:
            print(f"Warning User already exists: {email} (ID: {existing_id})")
            return existing_id
    except KeycloakGetError:
        # User does NOT exist — good
        pass
    except Exception as e:
        print(f"Error checking existing user: {e}")
        return None

    # -----------------------
    # Create user payload
    # -----------------------
    user_data = {
        "email": email,
        "username": email,
        "firstName": first_name,
        "lastName": last_name,

        "enabled": True,
        "emailVerified": True,

        "attributes": {},
        "requiredActions": []
    }

    # -----------------------
    # Create user in Keycloak
    # -----------------------
    try:
        print("Creating user…")
        user_id = keycloak_admin.create_user(user_data)

        if not user_id:
            print("User creation returned no ID! Something is wrong.")
            return None

        print(f"User created: {user_id}")

    except Exception as e:
        print("Failed to create user:", e)
        return None

    # -----------------------
    # Set password
    # -----------------------
    try:
        print("Setting password…")
        keycloak_admin.set_user_password(
            user_id=user_id,
            password=password,
            temporary=False
        )
        print("Password set successfully.")
    except Exception as e:
        print(f"Failed to set password for user {user_id}: {e}")
        return None

    # -----------------------
    # Assign groups safely
    # -----------------------
    if groups:
        try:
            all_groups = keycloak_admin.get_groups()
        except Exception as e:
            print("Failed to fetch Keycloak groups:", e)
            return user_id  # user is created, no need to fail

        for group_name in groups:
            try:
                # find group
                group = next((g for g in all_groups if g["name"] == group_name), None)

                if not group:
                    print(f"Warning Group not found: {group_name} — skipping.")
                    continue

                group_id = group["id"]

                # Avoid duplicate membership
                try:
                    user_groups = keycloak_admin.get_user_groups(user_id)
                    if any(g["id"] == group_id for g in user_groups):
                        print(f"ℹ User already in group: {group_name}")
                        continue
                except Exception:
                    pass

                # Add user to group
                keycloak_admin.group_user_add(user_id, group_id)
                print(f"Added to group: {group_name}")

            except Exception as e:
                print(f"Error adding to group {group_name}: {e}")

    # -----------------------
    # Done!
    # -----------------------
    print("User creation complete:", email)
    return user_id


def delete_a_user(user_id):
    try:
        keycloak_admin.delete_user(user_id)
        print(f"User {user_id} deleted successfully.")
    except Exception as e:
        print(f"Error deleting user {user_id}: {e}")


if __name__ == '__main__':

    # Your values go here:
    # -------------------------------------------------------
    # 3. Run example
    # -------------------------------------------------------
    ## change these as well please.
    new_user_id = create_user(
        email="kj@gmail.com",
        first_name="Kiro",
        last_name="Bood",
        password="mumba",
        # Note only the root groups work, no subgroups. Use other code to shift users into groups.
        groups=["API"] # keep fixed...
    )

    print("\nFinal User ID:", new_user_id)

    # delete the user

    user_id = "9887633f-2f60-4c67-9c3d-a62d6604cf2d"
    delete_a_user(user_id)
