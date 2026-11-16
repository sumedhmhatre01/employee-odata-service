ODATA_METADATA = """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx
    Version="1.0"
    xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx"
    xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">

    <edmx:DataServices m:DataServiceVersion="2.0">

        <Schema
            Namespace="EmployeeService"
            xmlns="http://schemas.microsoft.com/ado/2008/09/edm"
            xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">

            <EntityType Name="Employee">

                <Key>
                    <PropertyRef Name="EmployeeID"/>
                </Key>

                <Property
                    Name="EmployeeID"
                    Type="Edm.String"
                    Nullable="false"
                    MaxLength="20"/>

                <Property
                    Name="Name"
                    Type="Edm.String"
                    Nullable="false"
                    MaxLength="100"/>

                <Property
                    Name="Department"
                    Type="Edm.String"
                    Nullable="false"
                    MaxLength="50"/>

                <Property
                    Name="Salary"
                    Type="Edm.Double"
                    Nullable="false"/>

            </EntityType>

            <EntityContainer
                Name="EmployeeServiceEntities"
                m:IsDefaultEntityContainer="true">

                <EntitySet
                    Name="Employees"
                    EntityType="EmployeeService.Employee"/>

            </EntityContainer>

        </Schema>

    </edmx:DataServices>
</edmx:Edmx>
"""
