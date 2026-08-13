from app.db.base import Base
from app.models import (
    Branch,
    Category,
    Customer,
    Organization,
    OrganizationMembership,
    Product,
    Role,
    Supplier,
    User,
)

EXPECTED_TABLES = {
    "organizations",
    "users",
    "roles",
    "organization_memberships",
    "branches",
    "categories",
    "products",
    "customers",
    "suppliers",
}


def test_phase2_models_import() -> None:
    assert Organization.__tablename__ == "organizations"
    assert User.__tablename__ == "users"
    assert Role.__tablename__ == "roles"
    assert OrganizationMembership.__tablename__ == "organization_memberships"
    assert Branch.__tablename__ == "branches"
    assert Category.__tablename__ == "categories"
    assert Product.__tablename__ == "products"
    assert Customer.__tablename__ == "customers"
    assert Supplier.__tablename__ == "suppliers"


def test_metadata_contains_phase2_tables() -> None:
    table_names = {table.name for table in Base.metadata.sorted_tables}
    assert EXPECTED_TABLES.issubset(table_names)


def test_unique_constraints_present() -> None:
    role_table = Base.metadata.tables["roles"]
    membership_table = Base.metadata.tables["organization_memberships"]

    role_unique_names = {
        constraint.name
        for constraint in role_table.constraints
        if getattr(constraint, "name", None)
    }
    membership_unique_names = {
        constraint.name
        for constraint in membership_table.constraints
        if getattr(constraint, "name", None)
    }

    assert "uq_roles_organization_name" in role_unique_names
    assert "uq_org_membership_org_user" in membership_unique_names


def test_model_imports_are_registered() -> None:
    import app.models

    assert hasattr(app.models, "Organization")
    assert hasattr(app.models, "OrganizationMembership")
    assert hasattr(app.models, "Product")
