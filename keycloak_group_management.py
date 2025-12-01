"""

Purpose: Keycloak group functionality for SaaS project, adaptor from SaaS platform to AFIS' Keycloak.

Author: Kirodh Boodhraj

12 November 2025

"""

import os
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError, KeycloakError
from dotenv import load_dotenv

# for development, you can load a .env

# Load environment variables from .env file
load_dotenv()


class KeycloakGroupManager:
    def __init__(self, server_url, realm_name, username, password, client_id="admin-cli", verify=True):
        self.kc = KeycloakAdmin(
            server_url=server_url,
            username=username,
            password=password,
            realm_name=realm_name,
            client_id=client_id,
            verify=verify
        )

    def get_user_id_by_email(self, email):
        # Query users with exact email (you may also search by username depending on your configuration)
        users = self.kc.get_users({"email": email})
        if not users:
            raise KeycloakGetError(f"No user found for email: {email}")
        # If there are multiple, pick first
        return users[0]["id"]

    def get_group_id_by_path(self, group_path):
        """
        Finds a group by its path (e.g., "/ParentGroup/SubGroup") or by name.
        """
        # Using get_group_by_path if available
        try:
            group = self.kc.get_group_by_path(group_path)
            return group["id"]
        except KeycloakGetError:
            # fallback: find by name
            groups = self.kc.get_groups({"search": group_path.strip("/")})
            for g in groups:
                if g["path"] == group_path:
                    return g["id"]
            raise KeycloakGetError(f"Group not found for path: {group_path}")

    def get_all_groups(self):
        try:
            groups = self.kc.get_groups()
            print(groups)
        except KeycloakError as e:
            raise KeycloakError(f"Failed to get all groups: {e}")

    def add_user_to_group(self, user_id, group_id):
        try:
            self.kc.group_user_add(user_id=user_id, group_id=group_id)
        except KeycloakError as e:
            raise KeycloakError(f"Failed to add user {user_id} to group {group_id}: {e}")

    def remove_user_from_group(self, user_id, group_id):
        try:
            self.kc.group_user_remove(user_id=user_id, group_id=group_id)
        except KeycloakError as e:
            raise KeycloakError(f"Failed to remove user {user_id} from group {group_id}: {e}")

    def move_user_between_groups(self, email, old_group_path, new_group_path):
        user_id = self.get_user_id_by_email(email)
        old_group_id = self.get_group_id_by_path(old_group_path)
        new_group_id = self.get_group_id_by_path(new_group_path)

        # Remove from old group (if present)
        try:
            self.remove_user_from_group(user_id, old_group_id)
            print(f"Removed user {email} from {old_group_path}")
        except KeycloakError as err_rem:
            print(f"Warning: could not remove user {email} from {old_group_path}: {err_rem}")

        # Add to new group
        self.add_user_to_group(user_id, new_group_id)
        print(f"Added user {email} to {new_group_path}")


if __name__ == "__main__":
    # Configure these settings
    SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL")
    REALM = os.getenv("KEYCLOAK_REALM")
    ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER")
    ADMIN_PASS = os.getenv("KEYCLOAK_ADMIN_PASS")

    manager = KeycloakGroupManager(
        server_url=SERVER_URL,
        realm_name=REALM,
        username=ADMIN_USER,
        password=ADMIN_PASS
    )

    # TODO NOTE:: you will need to parameterize this probably...
    email_to_move = "kboodhraj@gmail.com"
    old_group = "/afis_stats/fire_stats"  # e.g. path of group to remove from
    new_group = "/VIEWER"  # path of group to add to


    ####################################################
    ## select a function here to carry out an operation

    ## get all groups in realm
    manager.get_all_groups()

    ### To move a user between groups
    # manager.move_user_between_groups(email_to_move, old_group, new_group)

    ### note you need these two before doing an individual insert or remove from group operation
    user_id = manager.get_user_id_by_email(email_to_move)
    group_id = manager.get_group_id_by_path(new_group)

    ## to add user to group
    manager.add_user_to_group(user_id,group_id)

    ## to remove a user form the group
    # manager.remove_user_from_group(user_id, group_id)


# # Install python-keycloak package
