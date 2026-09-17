"""Backward-compat facade поверх pages.onboarding.*

Разбито на компоненты с одной ответственностью:
    pages/onboarding/
        locators.py            — только локаторы, без ассертов и логики
        step_visibility.py      — ассерты видимости конкретных шагов
        specialization_step.py   — взаимодействие с dropdown шага 2
        dismissal.py               — единая цепочка закрытия модалки (была продублирована 4 раза)
        modal.py                    — OnboardingModal, публичный фасад

Публичный API OnboardingModal не изменился — существующие тесты и фикстуры
продолжают работать без правок. В новом коде можно импортировать напрямую
из pages.onboarding.modal.
"""

from pages.interview.onboarding.modal import OnboardingModal

__all__ = ["OnboardingModal"]
