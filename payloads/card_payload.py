from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Card:
    """
    Представляет структуры данных банковской карты
    Атрибуты:
        number_card - номер карты
        expiry_date - срок действия карты
        cvc - секретный код крты
    """
    number_card:str
    expiry_date:str
    cvc:str

class CardPayload:
    """
    Набор готовых банковских карт для тестирования
    Содержит статические обекты класса Card
    *Если нужно данные преобразовать в JSON, в код нужно импортировать метод **from dataclasses import asdict**
    """
    VISA =  Card("4300 0000 0000 0777", "12/30", "111")
    INVALID_NUMBER_CARD = Card("4300 0000 1234 0777", "12/30", "111")
    CARD_EXPIRED = Card("4300 0000 1234 0777", "12/25", "111")
    INVALID_CVC = Card("4300 0000 1234 0777", "12/30", "222")

