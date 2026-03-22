from fastapi import FastAPI, Query, Response
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# DATA

menu = [
    {"id": 1, "name": "Margherita Pizza", "price": 250, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Veg Burger", "price": 120, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Chicken Burger", "price": 150, "category": "Burger", "is_available": True},
    {"id": 4, "name": "Coke", "price": 50, "category": "Drink", "is_available": True},
    {"id": 5, "name": "Chocolate Cake", "price": 180, "category": "Dessert", "is_available": False},
    {"id": 6, "name": "Pepperoni Pizza", "price": 320, "category": "Pizza", "is_available": True}
]
orders = []
order_counter = 1
cart = []

# MODELS

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: str = "delivery"

class NewMenuItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    is_available: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)


# HELPERS

def find_menu_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None

def calculate_bill(price, quantity, order_type):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total

def filter_menu_logic(category, max_price, is_available):
    result = menu
    if category is not None:
        result = [i for i in result if i["category"].lower() == category.lower()]
    if max_price is not None:
        result = [i for i in result if i["price"] <= max_price]
    if is_available is not None:
        result = [i for i in result if i["is_available"] == is_available]
    return result

# DAY 1 ROUTES

@app.get("/")
def home():
    return {"message": "Welcome to QuickBite Food Delivery"}

@app.get("/menu")
def get_menu():
    return {"total": len(menu), "items": menu}

@app.get("/menu/summary")
def menu_summary():
    available = [i for i in menu if i["is_available"]]
    unavailable = [i for i in menu if not i["is_available"]]
    categories = list(set(i["category"] for i in menu))
    return {
        "total_items": len(menu),
        "available": len(available),
        "unavailable": len(unavailable),
        "categories": categories
    }

@app.get("/orders")
def get_orders():
    return {"total_orders": len(orders), "orders": orders}

# DAY 3 FILTER

@app.get("/menu/filter")
def filter_menu(
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    is_available: Optional[bool] = None
):
    filtered = filter_menu_logic(category, max_price, is_available)
    return {"count": len(filtered), "items": filtered}

# DAY 6 SEARCH / SORT / PAGINATION

@app.get("/menu/search")
def search_menu(keyword: str):
    result = [
        i for i in menu
        if keyword.lower() in i["name"].lower()
        or keyword.lower() in i["category"].lower()
    ]
    if not result:
        return {"message": "No matching items found"}
    return {"total_found": len(result), "items": result}

@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort_by"}
    if order not in ["asc", "desc"]:
        return {"error": "Invalid order"}
    reverse = True if order == "desc" else False
    sorted_menu = sorted(menu, key=lambda x: x[sort_by], reverse=reverse)
    return {"sorted_by": sort_by, "order": order, "items": sorted_menu}

@app.get("/menu/page")
def paginate_menu(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    total = len(menu)
    start = (page - 1) * limit
    items = menu[start:start + limit]
    total_pages = math.ceil(total / limit)
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "items": items
    }

@app.get("/menu/browse")
def browse_menu(
    keyword: Optional[str] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = menu
    if keyword:
        result = [
            i for i in result
            if keyword.lower() in i["name"].lower()
            or keyword.lower() in i["category"].lower()
        ]
    reverse = True if order == "desc" else False
    result = sorted(result, key=lambda x: x.get(sort_by, ""), reverse=reverse)
    total = len(result)
    start = (page - 1) * limit
    items = result[start:start + limit]
    total_pages = math.ceil(total / limit)
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "items": items
    }

# DAY 2 ORDER CREATION

@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter
    item = find_menu_item(order.item_id)
    if not item:
        return {"error": "Item not found"}
    if not item["is_available"]:
        return {"error": "Item not available"}
    total = calculate_bill(item["price"], order.quantity, order.order_type)
    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item_name": item["name"],
        "quantity": order.quantity,
        "total_price": total,
        "address": order.delivery_address
    }
    orders.append(new_order)
    order_counter += 1
    return new_order

# DAY 4 CRUD

@app.post("/menu")
def add_menu_item(item: NewMenuItem, response: Response):
    for i in menu:
        if i["name"].lower() == item.name.lower():
            return {"error": "Item already exists"}
    new_id = max(i["id"] for i in menu) + 1
    new_item = {
        "id": new_id,
        "name": item.name,
        "price": item.price,
        "category": item.category,
        "is_available": item.is_available
    }
    menu.append(new_item)
    response.status_code = 201
    return new_item

@app.put("/menu/{item_id}")
def update_menu(item_id: int, price: Optional[int] = None, is_available: Optional[bool] = None):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Item not found"}
    if price is not None:
        item["price"] = price
    if is_available is not None:
        item["is_available"] = is_available
    return item

@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Item not found"}
    menu.remove(item)
    return {"message": f"{item['name']} deleted"}

# DAY 5 CART WORKFLOW

@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Item not found"}
    if not item["is_available"]:
        return {"error": "Item unavailable"}
    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            return {"message": "Quantity updated", "cart": cart}
    cart.append({
        "item_id": item_id,
        "name": item["name"],
        "price": item["price"],
        "quantity": quantity
    })
    return {"message": "Item added", "cart": cart}

@app.get("/cart")
def view_cart():
    total = sum(i["price"] * i["quantity"] for i in cart)
    return {"items": cart, "grand_total": total}

@app.delete("/cart/{item_id}")
def remove_cart(item_id: int):

    for c in cart:
        if c["item_id"] == item_id:
            cart.remove(c)
            return {"message": "Item removed"}

    return {"error": "Item not in cart"}

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest, response: Response):
    global order_counter
    if not cart:
        return {"error": "Cart empty"}
    created_orders = []
    grand_total = 0
    for c in cart:
        total = calculate_bill(c["price"], c["quantity"], "delivery")
        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "item_name": c["name"],
            "quantity": c["quantity"],
            "total_price": total,
            "address": data.delivery_address
        }
        orders.append(order)
        created_orders.append(order)
        grand_total += total
        order_counter += 1
    cart.clear()
    response.status_code = 201
    return {"orders": created_orders, "grand_total": grand_total}

# LAST VARIABLE ROUTE

@app.get("/menu/{item_id}")
def get_menu_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Item not found"}
    return item
