from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductRecord:
    name: str
    description: str
    price: str
    billing_period: str
    features: tuple[str, ...]
    keywords: tuple[str, ...]


PRODUCT_CATALOG: tuple[ProductRecord, ...] = (
    ProductRecord(
        name="Starter",
        description="Entry plan for individuals and small teams.",
        price="$19",
        billing_period="per month",
        features=("Basic analytics", "Email support", "Up to 3 users"),
        keywords=("starter", "basic", "entry", "individual"),
    ),
    ProductRecord(
        name="Growth",
        description="Best for growing teams that need automation and collaboration.",
        price="$49",
        billing_period="per month",
        features=("Advanced analytics", "Priority support", "Up to 15 users", "Automation workflows"),
        keywords=("growth", "team", "automation", "collaboration"),
    ),
    ProductRecord(
        name="Pro",
        description="Full feature set for larger teams and commercial usage.",
        price="$99",
        billing_period="per month",
        features=("Unlimited projects", "Dedicated support", "Custom reporting", "SSO"),
        keywords=("pro", "enterprise", "commercial", "advanced"),
    ),
)


def find_relevant_products(query: str) -> list[ProductRecord]:
    normalized_query = query.lower()
    ranked_products: list[tuple[int, ProductRecord]] = []

    for product in PRODUCT_CATALOG:
        score = 0
        if product.name.lower() in normalized_query:
            score += 3
        if any(keyword in normalized_query for keyword in product.keywords):
            score += 2
        if "price" in normalized_query or "pricing" in normalized_query:
            score += 1
        if score > 0:
            ranked_products.append((score, product))

    if ranked_products:
        ranked_products.sort(key=lambda item: (-item[0], item[1].name))
        return [product for _, product in ranked_products]

    return list(PRODUCT_CATALOG)


def render_catalog(products: list[ProductRecord] | tuple[ProductRecord, ...] | None = None) -> str:
    selected_products = list(products) if products is not None else list(PRODUCT_CATALOG)
    lines: list[str] = []
    for product in selected_products:
        features = ", ".join(product.features)
        lines.append(
            f"- {product.name}: {product.description} Price: {product.price} {product.billing_period}. Features: {features}."
        )
    return "\n".join(lines)
