from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    """
    Представляет структуру данных банковской карты.
    """

    number_card: str
    expiry_date: str
    cvc: str


class CardPayload:
    """
    Набор тестовых банковских карт для формы оплаты Т-Банка.

    В текущем sandbox результат оплаты определяется номером карты:
    - SUCCESS_CARD проходит оплату
    - ALTERNATIVE_SUCCESS_CARD также проходит оплату и оставлена как запасная
    - DECLINED_CARD отклоняет оплату
    """

    SUCCESS_CARD = Card("4300 0000 0000 0777", "12/30", "111")
    ALTERNATIVE_SUCCESS_CARD = Card("4000 0000 0000 0119", "12/30", "111")
    DECLINED_CARD = Card("5000 0000 0000 0009", "12/30", "111")
