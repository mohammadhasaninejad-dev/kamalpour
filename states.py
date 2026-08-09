from aiogram.fsm.state import State, StatesGroup


class TextSearch(StatesGroup):
    waiting_query = State()


class AddProduct(StatesGroup):
    category = State()
    attr1 = State()
    attr2 = State()
    attr3 = State()
    attr4 = State()
    attr5 = State()
    brand = State()
    purchase_price = State()
    sale_price = State()
    wholesale_price = State()
    stock = State()
    barcode = State()
    seller_name = State()
    seller_code = State()
    photo = State()


class EditProduct(StatesGroup):
    waiting_id = State()
    field = State()
    value = State()


class DeleteProduct(StatesGroup):
    waiting_id = State()


class ImportExcel(StatesGroup):
    waiting_file = State()