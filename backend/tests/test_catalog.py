"""Tests for catalog endpoints — list, create, update products."""

import pytest


@pytest.mark.asyncio
async def test_list_products_empty(client, auth_headers):
    """List products for new company returns empty."""
    response = await client.get("/api/catalog/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_product(client, auth_headers):
    """Create a new product."""
    response = await client.post(
        "/api/catalog/",
        headers=auth_headers,
        json={
            "name": "Casa Modelo A",
            "slug": "casa-modelo-a",
            "category": "casas",
            "price": 185000,
            "price_currency": "USD",
            "short_desc": "Casa 3 dormitorios",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Casa Modelo A"
    assert data["slug"] == "casa-modelo-a"
    assert float(data["price"]) == 185000
    return data["id"]


@pytest.mark.asyncio
async def test_create_and_update_product(client, auth_headers):
    """Create then update a product."""
    # Create
    create_resp = await client.post(
        "/api/catalog/",
        headers=auth_headers,
        json={
            "name": "Casa Modelo B",
            "slug": "casa-modelo-b",
            "category": "casas",
            "price": 220000,
            "price_currency": "USD",
        },
    )
    assert create_resp.status_code == 201
    product_id = create_resp.json()["id"]

    # Update
    update_resp = await client.patch(
        f"/api/catalog/{product_id}",
        headers=auth_headers,
        json={"price": 210000, "short_desc": "Precio rebajado"},
    )
    assert update_resp.status_code == 200
    assert float(update_resp.json()["price"]) == 210000
    assert update_resp.json()["short_desc"] == "Precio rebajado"


@pytest.mark.asyncio
async def test_list_products_after_create(client, auth_headers):
    """List products shows created products."""
    # Create a product first
    await client.post(
        "/api/catalog/",
        headers=auth_headers,
        json={
            "name": "Producto List Test",
            "slug": "producto-list-test",
            "price": 100,
        },
    )

    response = await client.get("/api/catalog/", headers=auth_headers)
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 1
    names = [p["name"] for p in products]
    assert "Producto List Test" in names
