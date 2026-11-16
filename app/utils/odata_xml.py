import os

from datetime import datetime, timezone
from urllib.parse import quote
from xml.etree.ElementTree import (
    Element,
    SubElement,
    tostring,
    register_namespace,
    fromstring,
)

# --------------------------------------------------
# OData V2 Configuration
# --------------------------------------------------

ATOM_NS = "http://www.w3.org/2005/Atom"

DATA_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices"

METADATA_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"

SCHEME_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices/scheme"

SERVICE_ROOT = (
    os.getenv(
        "ODATA_SERVICE_ROOT",
        "https://employee-odata-service.onrender.com/odata/v2/",
    ).rstrip("/")
    + "/"
)

ENTITY_TYPE = "EmployeeService.Employee"
ENTITY_SET = "Employees"

register_namespace("", ATOM_NS)
register_namespace("d", DATA_NS)
register_namespace("m", METADATA_NS)


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------


def current_timestamp():
    """Return current UTC timestamp in ISO 8601 format."""

    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def employee_resource_url(employee_id):
    """Generate absolute OData employee resource URL."""

    escaped_id = str(employee_id).replace("'", "''")

    encoded_id = quote(
        escaped_id,
        safe="()'",
    )

    return f"{SERVICE_ROOT}{ENTITY_SET}('{encoded_id}')"


# --------------------------------------------------
# Create Single Employee Atom XML Entry
# --------------------------------------------------


def create_employee_entry(employee):
    """Convert one employee into an OData Atom XML entry."""

    employee_id = employee["EmployeeID"]
    resource_url = employee_resource_url(employee_id)

    entry = Element(f"{{{ATOM_NS}}}entry")

    SubElement(
        entry,
        f"{{{ATOM_NS}}}id",
    ).text = resource_url

    SubElement(
        entry,
        f"{{{ATOM_NS}}}title",
        {"type": "text"},
    )

    SubElement(
        entry,
        f"{{{ATOM_NS}}}updated",
    ).text = current_timestamp()

    author = SubElement(
        entry,
        f"{{{ATOM_NS}}}author",
    )

    SubElement(
        author,
        f"{{{ATOM_NS}}}name",
    ).text = "EmployeeService"

    SubElement(
        entry,
        f"{{{ATOM_NS}}}category",
        {
            "term": ENTITY_TYPE,
            "scheme": SCHEME_NS,
        },
    )

    SubElement(
        entry,
        f"{{{ATOM_NS}}}link",
        {
            "rel": "self",
            "title": ENTITY_SET,
            "href": f"{ENTITY_SET}('{employee_id}')",
        },
    )

    SubElement(
        entry,
        f"{{{ATOM_NS}}}link",
        {
            "rel": "edit",
            "title": ENTITY_SET,
            "href": f"{ENTITY_SET}('{employee_id}')",
        },
    )

    content = SubElement(
        entry,
        f"{{{ATOM_NS}}}content",
        {"type": "application/xml"},
    )

    properties = SubElement(
        content,
        f"{{{METADATA_NS}}}properties",
    )

    for field in [
        "EmployeeID",
        "Name",
        "Department",
        "Salary",
    ]:

        value = employee[field]

        attributes = {}

        if field == "Salary":
            attributes[f"{{{METADATA_NS}}}type"] = "Edm.Double"

        SubElement(
            properties,
            f"{{{DATA_NS}}}{field}",
            attributes,
        ).text = str(value)

    return tostring(
        entry,
        encoding="utf-8",
        xml_declaration=True,
    )


# --------------------------------------------------
# Create Employee Atom XML Feed
# --------------------------------------------------


def create_employee_feed(employees):
    """Convert employee records into an OData Atom XML feed."""

    feed = Element(f"{{{ATOM_NS}}}feed")

    SubElement(
        feed,
        f"{{{ATOM_NS}}}id",
    ).text = (
        SERVICE_ROOT + ENTITY_SET
    )

    SubElement(
        feed,
        f"{{{ATOM_NS}}}title",
        {"type": "text"},
    ).text = ENTITY_SET

    SubElement(
        feed,
        f"{{{ATOM_NS}}}updated",
    ).text = current_timestamp()

    author = SubElement(
        feed,
        f"{{{ATOM_NS}}}author",
    )

    SubElement(
        author,
        f"{{{ATOM_NS}}}name",
    ).text = "EmployeeService"

    SubElement(
        feed,
        f"{{{ATOM_NS}}}link",
        {
            "rel": "self",
            "title": ENTITY_SET,
            "href": ENTITY_SET,
        },
    )

    for employee in employees:

        entry_xml = create_employee_entry(employee)

        feed.append(fromstring(entry_xml))

    return tostring(
        feed,
        encoding="utf-8",
        xml_declaration=True,
    )


# --------------------------------------------------
# Parse Incoming Employee Atom XML
# --------------------------------------------------


def parse_employee_xml(xml_data):
    """Extract employee fields from an OData Atom XML entry."""

    try:
        root = fromstring(xml_data)

    except Exception as error:
        raise ValueError("Invalid employee XML.") from error

    properties = root.find(f".//{{{METADATA_NS}}}properties")

    if properties is None:
        raise ValueError("Employee properties not found in XML.")

    employee = {}

    for field in [
        "EmployeeID",
        "Name",
        "Department",
        "Salary",
    ]:

        element = properties.find(f"{{{DATA_NS}}}{field}")

        if element is None or element.text is None:
            raise ValueError(f"Missing employee field: {field}")

        employee[field] = element.text

    try:
        employee["Salary"] = float(employee["Salary"])

    except ValueError as error:
        raise ValueError("Salary must be a valid number.") from error

    return employee


# --------------------------------------------------
# Local Testing
# --------------------------------------------------

if __name__ == "__main__":

    employees = [
        {
            "EmployeeID": "EMP1001",
            "Name": "Rahul",
            "Department": "IT",
            "Salary": 45000,
        },
        {
            "EmployeeID": "EMP1002",
            "Name": "Amit",
            "Department": "HR",
            "Salary": 50000,
        },
    ]

    print("\n--- Employee Atom XML Entry ---")

    print(create_employee_entry(employees[0]).decode("utf-8"))

    print("\n--- Employee Atom XML Feed ---")

    print(create_employee_feed(employees).decode("utf-8"))

    print("\n--- Employee XML Parsing Test ---")

    xml_data = create_employee_entry(employees[0])

    parsed_employee = parse_employee_xml(xml_data)

    print(parsed_employee)
