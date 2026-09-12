from __future__ import annotations

import logging
import re
from typing import Any
from anthropic import AsyncAnthropic

from core.config import settings
from db.repositories.ai_token_repo import AITokenRepository
from db.repositories.assessment_criteria_repo import AssessmentCriteriaRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.lesson_repo import LessonRepository
from db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# Domain expert personalities and specific context for each course
COURSE_DOMAIN_PROFILES: dict[str, dict[str, Any]] = {
    "logistika": {
        "role_name": "Logistika va Dispetcherlik bo'yicha Bosh Ustoz",
        "description": "Mahalliy va xalqaro yuk tashuvlar, fura va yuk topish, fraxt hisoblash, dispetcherlik shartnomalari va komissiya olish bo'yicha mutaxassis.",
        "key_terms": [
            "Fraxt (yuk tashish narxi / yo'l haqi)",
            "Dispetcherlik komissiyasi (odatiy stavka 5-10%)",
            "Fura turlari (Tent, Refrijerator, Zernavoz, Samosval, Isuzu, Labo)",
            "Obratka (qaytish yo'nalishidagi arzonroq bo'sh fura)",
            "Dagro'z (qo'shimcha yuk ortish / konsolidatsiya)",
            "TTN, CMR, Faktura (yuk kuzatuv hujjatlari)",
            "Yuk birjalari va Telegram guruhlar orqali yuk yopish",
        ],
        "tone": "Amaliy, tajribali, biznesga yo'naltirilgan, har bir qadamni aniq hisob-kitob bilan tushuntiruvchi",
    },
    "telegram": {
        "role_name": "Telegram Ads va Target bo'yicha Yetakchi Ekspert",
        "description": "Rasmiy Telegram Ads platformasi, TON/Stars byudjetlashtirish, auditoriya segmentatsiyasi, CPV/CPM optimallashtirish va konversiya oshirish bo'yicha mutaxassis.",
        "key_terms": [
            "Telegram Ads rasmiy kabineti",
            "CPV (Cost Per View) va CPM (1000 ko'rish narxi)",
            "TON va Stars orqali to'lovlar",
            "Targeting (kanallar, geo, tillar, mavzular bo'yicha)",
            "Reklama moderatsiyasi talablari",
            "A/B testlash va CTA (Call to Action)",
        ],
        "tone": "Raqamlar va metrikalarga asoslangan, marketing psixologiyasini tushuntiruvchi, do'stona va aniq",
    },
    "konkurs": {
        "role_name": "Marketing va Virusli Aksiyalar Bo'yicha Mutaxassis",
        "description": "Telegram va ijtimoiy tarmoqlarda konkurslar, sovrinli o'yinlar, referal voronkalar va obunachilarni xaridorga aylantirish bo'yicha mutaxassis.",
        "key_terms": [
            "Sovg'a fondini shakllantirish",
            "Referal va bot mexanikalari",
            "Shaffof randomizer va jonli efir",
            "Auditoriyani saqlab qolish (Retensiya)",
            "Konkursdan keyingi sotuv voronkasi",
        ],
        "tone": "Kreativ, ruhlantiruvchi, virusli o'sish va auditoriya ishonchini qozonishga yo'naltirilgan",
    },
    "sayt": {
        "role_name": "Veb-saytlar va Internet Monetizatsiyasi Mutaxassisi",
        "description": "Veb-saytlarni yaratish, Google AdSense, Yandex Direct, SEO organik trafik va affiliate (sheriklik) marketing orqali daromad olish bo'yicha ekspert.",
        "key_terms": [
            "Google AdSense va Yandex Direct",
            "SEO (Qidiruv tizimlarida birinchi o'ringa chiqish)",
            "Organik trafik va kalit so'zlar",
            "Affiliate (CPA) sheriklik dasturlari",
            "Passiv daromad oqimlari",
        ],
        "tone": "Texnik jihatdan puxta, bosqichma-bosqich yo'l-yo'riq ko'rsatuvchi va amaliy",
    },
    "xitoy": {
        "role_name": "Xitoydan Import va Kargo Bo'yicha Bosh Maslahatchi",
        "description": "1688, Taobao, Alibaba orqali to'g'ridan-to'g'ri zavodlardan tovar xarid qilish, kargo logistikasi, bojxona va O'zbekistonda yuqori marja bilan sotish mutaxassisi.",
        "key_terms": [
            "1688.com (Ulgurji narxlar) va Taobao",
            "AliPay va xavfsiz to'lovlar",
            "Kargo turlari (Avia, Avto, Temir yo'l)",
            "Kub va og'irlik (kg) hisob-kitobi",
            "Sinov namunasi (Sample) va sifat nazorati",
            "Bojxona to'lovlari va O'zbekistonda sotish marjasi",
        ],
        "tone": "Tadbirkorlikka asoslangan, xatarlardan himoyalovchi, xarajatlarni tejash sirlarini o'rgatuvchi",
    },
}


def _detect_domain(course_title: str, lesson_title: str) -> str:
    combined = f"{course_title} {lesson_title}".lower()
    if "logistika" in combined or "dispetcher" in combined or "fura" in combined or "fraxt" in combined:
        return "logistika"
    if "telegram" in combined or "ads" in combined:
        return "telegram"
    if "konkurs" in combined or "aksiya" in combined or "tanlov" in combined:
        return "konkurs"
    if "sayt" in combined or "adsense" in combined or "seo" in combined:
        return "sayt"
    if "xitoy" in combined or "import" in combined or "1688" in combined or "kargo" in combined:
        return "xitoy"
    return "logistika"


class AITutorService:
    """Har bir video dars tagidagi maxsus AI Ustoz — talabaning savollariga
    aniq kurs va dars kontekstida javob beradi va tokenni mentoriga hisoblaydi."""

    def __init__(
        self,
        ai_token_repo: AITokenRepository,
        lesson_repo: LessonRepository,
        course_repo: CourseRepository,
        criteria_repo: AssessmentCriteriaRepository,
        user_repo: UserRepository,
        client: AsyncAnthropic | None = None,
    ) -> None:
        self._ai_token_repo = ai_token_repo
        self._lesson_repo = lesson_repo
        self._course_repo = course_repo
        self._criteria_repo = criteria_repo
        self._user_repo = user_repo
        self._client = client or (AsyncAnthropic(api_key=settings.anthropic.api_key) if settings.anthropic.api_key else None)

    async def resolve_student_mentor_id(self, student_id: int) -> int:
        """Talabaning shaxsiy ustozi (mentor_id)ni aniqlaydi."""
        cursor = await self._ai_token_repo._conn.execute(
            """
            SELECT ln.owner_user_id AS mentor_id
            FROM cabinet_members cm
            JOIN cabinets c ON c.id = cm.cabinet_id
            JOIN license_nodes ln ON ln.id = c.owner_node_id
            WHERE cm.user_id = ?
            LIMIT 1
            """,
            (student_id,),
        )
        row = await cursor.fetchone()
        if row and row["mentor_id"]:
            return row["mentor_id"]
        return 1

    async def ask_lesson_ai(
        self,
        student_id: int,
        lesson_id: int,
        user_message: str,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        course_title = "Logistika Asoslari"
        course_description = ""
        if lesson:
            course = await self._course_repo.get_by_id(lesson.course_id)
            if course:
                course_title = course.title
                course_description = course.description or ""

        lesson_title = lesson.title if lesson else "Dars"
        domain_key = _detect_domain(course_title, lesson_title)
        domain_profile = COURSE_DOMAIN_PROFILES.get(domain_key, COURSE_DOMAIN_PROFILES["logistika"])

        criteria = await self._criteria_repo.get_by_lesson(lesson_id)
        key_concepts = criteria.key_concepts if criteria else "Mavzuning amaliy tushunchalari va qo'llanilishi"

        # Build deep, domain-specific System Prompt
        system_prompt = (
            f"Sen «BilimGo» ta'lim platformasining professional, samimiy va tajribali «{domain_profile['role_name']}»san.\n\n"
            f"🎓 O'QUV YO'NALISHI VA KONTEKST:\n"
            f"• Kurs: «{course_title}»\n"
            f"• Kurs tavsifi: {course_description or domain_profile['description']}\n"
            f"• Joriy Dars: «{lesson_title}» (Dars #{lesson_id})\n"
            f"• Darsning asosiy o'quv mavzulari: {key_concepts}\n"
            f"• Yo'nalishning asosiy atamalari: {', '.join(domain_profile['key_terms'])}\n"
            f"• Javob berish uslubi: {domain_profile['tone']}\n\n"
            f"🎯 TALABALAR BILAN ISHLASH QOIDALARI:\n"
            f"1. Faqat o'zbek tilida, nihoyatda tushunarli, aniq, muloyim va amaliy misollar bilan javob ber.\n"
            f"2. Talabaning savoli ushbu dars va kurs yo'nalishiga qanchalik mos ekanligini hisobga ol.\n"
            f"3. Murakkab atamalarni hayotiy, kundalik misollar orqali tushuntir (masalan, fura qidirish, fraxt hisoblash, narx kelishish).\n"
            f"4. Javobingni chiroyli formatda: emoji belgilar, qisqa xatboshilar va muhim nuqtalarni qalin (bold) qilib taqdim et.\n"
            f"5. Javob oxirida talabaga motivatsiya ber va mavzu bo'yicha bitta kichik amaliy maslahat qo'sh."
        )

        messages: list[dict[str, str]] = []
        if history:
            for item in history[-6:]:
                role = item.get("role") or item.get("sender") or "user"
                content = item.get("content") or item.get("text") or ""
                if role in ("assistant", "bot", "ai"):
                    role = "assistant"
                else:
                    role = "user"
                if content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        input_tokens = 160
        output_tokens = 220
        reply_text = ""

        if self._client and settings.anthropic.api_key and not settings.debug:
            try:
                response = await self._client.messages.create(
                    model=settings.anthropic.model,
                    max_tokens=800,
                    system=system_prompt,
                    messages=messages,
                )
                reply_text = "".join(b.text for b in response.content if b.type == "text").strip()
                if hasattr(response, "usage") and response.usage:
                    input_tokens = response.usage.input_tokens
                    output_tokens = response.usage.output_tokens
            except Exception as exc:
                logger.exception("Claude AI javob berishda xatolik, kontekstli generator ishga tushdi: %s", exc)
                reply_text = self._generate_contextual_response(domain_key, course_title, lesson_title, key_concepts, user_message)
        else:
            # High-precision Domain Context Generator for Local/Dev/Offline mode
            reply_text = self._generate_contextual_response(domain_key, course_title, lesson_title, key_concepts, user_message)

        # 1000 ta token narxi taxminan 30 so'm (UZS)
        cost_sum = round((input_tokens * 0.02 + output_tokens * 0.08), 2)

        # Mentor hisobiga tokenni avtomatik yozish
        mentor_id = await self.resolve_student_mentor_id(student_id)
        await self._ai_token_repo.record_usage(
            mentor_id=mentor_id,
            student_id=student_id,
            lesson_id=lesson_id,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            cost_sum=cost_sum,
        )

        return {
            "reply": reply_text,
            "answer": reply_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_sum": cost_sum,
        }

    def _generate_contextual_response(
        self,
        domain_key: str,
        course_title: str,
        lesson_title: str,
        key_concepts: str,
        question: str,
    ) -> str:
        """Har bir kurs va dars bo'yicha to'liq kontekstli va chuqur amaliy javob generatori."""
        q = question.lower()

        # 1. Xulosa va umumiy mazmun so'ralganda
        if any(w in q for w in ["xulosa", "haqida", "mazmun", "umumiy", "qisqacha", "nima degani"]):
            if domain_key == "logistika":
                return (
                    f"📌 **«{lesson_title}» darsining asosiy mazmuni va amaliy xulosasi:**\n\n"
                    f"1. **Mavzuning o'rni:** {key_concepts}.\n"
                    f"2. **Amaliy qoida:** Logistika va dispetcherlikda har bir daqiqa muhim. Yuk ma'lumotlarini aniq olish (hajm, og'irlik, yo'nalish) va furachiga to'g'ri yetkazish xatolarning 90% oldini oladi.\n"
                    f"3. **Daromad kaliti:** Fraxt narxini to'g'ri hisoblab, yuk egasi va haydovchi o'rtasida o'z xizmat haqingizni (odatda 5-10% yoki fiks komissiya) kelishib oling.\n\n"
                    f"💡 *Maslahat:* Darsdagi shablonlarni daftaringizga yozib oling va bugunoq birinchi qo'ng'iroqni sinab ko'ring! Yana qaysi qismiga tushunmadingiz?"
                )
            elif domain_key == "telegram":
                return (
                    f"🎯 **«{lesson_title}» darsi bo'yicha muhim xulosa:**\n\n"
                    f"1. **Asosiy tamoyil:** {key_concepts}.\n"
                    f"2. **Byudjet va CPV:** Telegram Ads da obunachini arzon jalb qilish uchun tor va to'g'ri kanallarni tanlash lozim.\n"
                    f"3. **Konversiya:** Reklama matnida aniq taklif (Offer) va kuchli Call-to-Action (CTA) bo'lishi shart.\n\n"
                    f"🚀 *Keyingi qadam:* Kichik byudjet bilan test reklama qo'yib, natijalarni tahlil qilib boring!"
                )
            elif domain_key == "xitoy":
                return (
                    f"📦 **«{lesson_title}» darsining muhim xulosasi:**\n\n"
                    f"1. **Asosiy qoida:** {key_concepts}.\n"
                    f"2. **Zavod bilan ishlash:** 1688 dan eng arzon va sifatli zavodni topib, doimo sinov namunasi (sample) so'rang.\n"
                    f"3. **Kargo va marja:** Tovarning tannarxiga kargo xarajatini qo'shib, O'zbekiston bozorida 2x-3x marja bilan sotishni rejalashtiring.\n\n"
                    f"💰 *Eslatma:* AliPay orqali to'lovlarda xavfsizlik qoidalariga qat'iy amal qiling!"
                )
            else:
                return (
                    f"📚 **«{lesson_title}» darsining asosiy nuqtalari:**\n\n"
                    f"• **Asosiy tushuncha:** {key_concepts}.\n"
                    f"• **Amaliyot:** Darsda ko'rsatilgan bosqichlarni o'z loyihangizda ketma-ket qo'llang.\n"
                    f"• **Natija:** Doimiy takrorlash va tahlil orqali professional natijaga erishasiz.\n\n"
                    f"Savolingiz bo'lsa, bemalol davom ettiring!"
                )

        # 2. Narx, Fraxt, Komissiya yoki Hisob-kitob haqida so'ralganda
        if any(w in q for w in ["narx", "fraxt", "pul", "komissiya", "daromad", "haq", "hisob", "stavka", "qancha"]):
            if domain_key == "logistika":
                return (
                    f"💰 **Logistikada Fraxt va Dispetcherlik haqi qanday hisoblanadi?**\n\n"
                    f"1. **Fraxt shakllanishi:** Masofa (km), yuk og'irligi (tonna), mashina turi (masalan, Ref yoki Tent) va yoqilg'i narxiga bog'liq.\n"
                    f"2. **Dispetcher komissiyasi:** Odatda umumiy fraxtning **5% dan 10% gacha** qismi yoki har bir qatnov uchun kelishilgan fiks summa (masalan, 200,000 – 1,000,000 so'm) olinadi.\n"
                    f"3. **Xavfsiz to'lov:** Yuk mashinaga yuklanib, yo'lga chiqqan paytda yoki manzilga yetib borishidan oldin to'lov shartlarini shartnomada aniq ko'rsatish zarur.\n\n"
                    f"Misol uchun: 10,000,000 so'mlik yukda 7% komissiya sizga sof **700,000 so'm** daromad keltiradi! 🤝"
                )
            elif domain_key == "telegram":
                return (
                    f"💳 **Telegram Ads byudjeti va xarajatlar:**\n\n"
                    f"• **Minimal byudjet:** Stars yoki TON orqali kichik summadan boshlash mumkin.\n"
                    f"• **CPM / CPV narxi:** Maqsadli kanallar qamrovi va raqobatga qarab o'zgaradi.\n"
                    f"• **Optimallashtirish:** Eng yuqori konversiya bergan e'lonlarga byudjetni oshirib, samarasizlarini o'z vaqtida to'xtatish kerak."
                )

        # 3. Qanday boshlash, fura/yuk/tovar topish yoki amaliy qadamlar so'ralganda
        if any(w in q for w in ["qanday", "qayerdan", "boshlash", "topish", "usul", "nima qilish", "maslahat"]):
            if domain_key == "logistika":
                return (
                    f"🚛 **«{lesson_title}» bo'yicha amaliy qadamlar:**\n\n"
                    f"1. **1-Qadam:** Yuk beruvchi korxona yoki fermer bilan bog'lanib, yuk tafsilotlarini oling (og'irligi, qayerdan qayerga, qachon yuklanadi).\n"
                    f"2. **2-Qadam:** Haydovchilar guruhi yoki bazangizdan mos mashinani (masalan, {lesson_title}) toping.\n"
                    f"3. **3-Qadam:** Yozishmadan ko'ra telefon orqali gaplashib, narxni kelishtiring va yuklash lokatsiyasini yuboring.\n"
                    f"4. **4-Qadam:** Yuk manzilga yetib borguncha aloqada bo'ling va o'z xizmatingiz haqini qabul qiling.\n\n"
                    f"Har bir muvaffaqiyatli kelishuv sizga doimiy mijozlar bazasini shakllantiradi! 📈"
                )
            elif domain_key == "xitoy":
                return (
                    f"🛒 **Xitoydan import qilish bo'yicha 3 ta oltin qoida:**\n\n"
                    f"1. 1688.com saytida ishlab chiqaruvchining reytingi va qancha vaqtdan beri faoliyat yuritayotganini tekshiring.\n"
                    f"2. Narxni tushirish uchun menejer bilan Wechat yoki AliPay chatida to'g'ridan-to'g'ri savdolashing.\n"
                    f"3. Kargo kompaniyasi omboriga tovar yetib borgach, fotohisobot (tekshiruv) so'rang.\n\n"
                    f"Bu sizni har qanday kutilmagan brak yoki xatolikdan 100% asraydi!"
                )

        # 4. Standart chuqur tushuntirish
        return (
            f"Assalomu alaykum! «{course_title}» kursi, **«{lesson_title}»** darsi bo'yicha savolingiz juda o'rinli.\n\n"
            f"📌 **Asosiy tushuncha:** {key_concepts}.\n\n"
            f"🔍 **Amaliy tahlil:** Ushbu darsda o'rganilgan mavzuni muvaffaqiyatli qo'llash uchun jarayonni bosqichma-bosqich bajarish va intizomli bo'lish zarur. "
            f"Savolingizdagi vaziyatni hal qilishda doimo avval barcha ma'lumotlarni to'liq tekshirib, keyin qaror qabul qiling.\n\n"
            f"✨ *Sizda yana qanday amaliy savol yoki tushunarsiz nuqta bor? Bemalol batafsil yozing, birga tahlil qilamiz!* 🚀"
        )
