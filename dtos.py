from dataclasses import dataclass

@dataclass
class MenuDTO:
    id: int
    name: str
    price: int
    coffee_gram: int  
    condensed_milk_ml: int

@dataclass
class IngredientStock:
    coffee_gram: int  
    condensed_milk_ml: int

@dataclass
class OrderDTO:
    customer_name: str
    menu: MenuDTO
    quantity: int
    total: float = 0.0
    promo_applied: bool = False
