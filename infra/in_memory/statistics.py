from dataclasses import dataclass, field
from uuid import UUID

from core.constants import ADMIN_API_KEY
from core.errors import AccessError
from core.statistics import Statistic


@dataclass
class StatisticInMemory:
    statistic: Statistic = field(default_factory=Statistic)

    def get(self, key: UUID) -> Statistic:
        if key == ADMIN_API_KEY:
            return self.statistic
        raise AccessError("User does not have access to statistics.")

    def update(self, commission: float) -> None:
        self.statistic.transaction_number += 1
        self.statistic.profit_in_satoshis += commission
