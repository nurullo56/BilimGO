from db.database import database
from db.repositories.course_repo import CourseRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.royalty_repo import RoyaltyLedgerRepository
from db.repositories.sale_repo import Sale
from db.repositories.tariff_quota_repo import TariffQuotaRepository


class RoyaltyService:
    """Litsenziya daraxti bo'ylab kaskad royalty taqsimoti.

    Mantiq: sotgan tugun o'z royalty_percent'i ulushini otasiga uzatadi.
    Ota esa o'ziga tegan ulushdan yana o'z royalty_percent'i bo'yicha
    bobosiga uzatadi — shu tarzda daraxt ildiziga qadar pasayib boradi.
    """

    def __init__(
        self,
        license_node_repo: LicenseNodeRepository,
        royalty_repo: RoyaltyLedgerRepository,
        tariff_quota_repo: TariffQuotaRepository | None = None,
        course_repo: CourseRepository | None = None,
    ) -> None:
        self._license_node_repo = license_node_repo
        self._royalty_repo = royalty_repo
        self._tariff_quota_repo = tariff_quota_repo
        self._course_repo = course_repo

    async def distribute_for_sale(self, sale: Sale) -> None:
        if await self._royalty_repo.exists_for_sale(sale.id):
            return  # idempotentlik — qayta ishlov berilmaydi

        conn = self._license_node_repo._conn
        try:
            current_node = await self._license_node_repo.get_by_id(sale.license_node_id)
            if current_node is None:
                return

            # 1-bosqich: 15 kunlik Limit davri tekshiruvi (Shartnoma 4.1-band)
            if current_node.stage == "limit":
                is_expired = await self._license_node_repo.is_limit_expired(current_node.id)

                if is_expired:
                    # 15 kun tugagan -> 'hamkorlik' bosqichiga avtomatik o'tkaziladi
                    await self._license_node_repo.update_stage(current_node.id, "hamkorlik", autocommit=False)
                    current_node = await self._license_node_repo.get_by_id(current_node.id)
                else:
                    # 15 kun ichida: Agar tarif bo'yicha limit bo'lsa, limitdan 1 ta yechamiz
                    if self._tariff_quota_repo and self._course_repo:
                        course = await self._course_repo.get_by_id(sale.course_id)
                        if course:
                            quota = await self._tariff_quota_repo.get_quota_for_course(current_node.id, course.title)
                            if quota and quota.remaining > 0:
                                await self._tariff_quota_repo.consume_quota(quota.id, autocommit=False)
                    # 15 kun ichida 100% daromad o'quvchida qoladi (Mentor 0% ulush oladi)
                    await conn.commit()
                    return

            current_amount = sale.amount

            while current_node is not None and current_node.parent_id is not None:
                share = round(current_amount * current_node.royalty_percent / 100, 2)
                if share > 0:
                    await self._royalty_repo.create_entry(
                        sale_id=sale.id,
                        node_id=current_node.parent_id,
                        percent_applied=current_node.royalty_percent,
                        amount=share,
                        autocommit=False,
                    )
                current_amount = share
                current_node = await self._license_node_repo.get_by_id(current_node.parent_id)

            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
