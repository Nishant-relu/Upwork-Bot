
async def format_price(text:str) -> float|None:
    """Cleans and converts a price string to float."""

    try:
        cleaned = text.replace('$', '').replace(',', '').strip()
        price = round(float(cleaned))
    except (ValueError, AttributeError):
        price = None
    
    return price
