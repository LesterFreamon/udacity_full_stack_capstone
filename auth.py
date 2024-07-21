from flask import Flask
from flask_principal import Permission, RoleNeed, identity_loaded, UserNeed
from flask_login import current_user

# Define roles
user_role = RoleNeed('user')
admin_role = RoleNeed('admin')

# Define permissions
user_permission = Permission(user_role)
admin_permission = Permission(admin_role)

# Define combined permissions
admin_or_user_permission = Permission(user_role, admin_role)

def setup_security(app: Flask):
    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        # Set the identity user object
        identity.user = current_user

        # Add the UserNeed to the identity
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        # Assuming the current_user has roles attribute which is a list of Role objects
        if hasattr(current_user, 'roles'):
            for role in current_user.roles:
                # Make sure to add the role name to the identity
                identity.provides.add(RoleNeed(role.name))
