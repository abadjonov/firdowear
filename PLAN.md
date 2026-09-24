# Firdowear — o‘g‘il bolalar kiyim do‘koni (ma’lumotlar modeli)

Faqat reja. Kod yo‘q. Do‘kon: o‘g‘il bolalar, 0–18 yosh, deyarli barcha turdagi kiyim.

---

## 1. Nima uchun oddiy “mahsulot” yetarli emas

Bitta “qora hoodie” aslida 20–40 ta savdo birligidir:

- 110 sm, qora — 2 ta
- 122 sm, qora — 0 ta (tugagan)
- 122 sm, kulrang — 5 ta

Ota-ona esa boshqacha qidiradi: “7 yoshga jinsi”, “qishki kurtka 134”, “maktab oq ko‘ylak”.

Shuning uchun **mahsulot** (umumiy kartochka) va **variant** (o‘lcham + rang + qoldiq) alohida.

---

## 2. Asosiy jadvallar va bog‘lanishlar

```
AgeGroup ────────┐
                 │  M2M
Category ─── 1:N ── Product ─── 1:N ── ProductImage
                 │     │                    │
                 │     │                    └── ixtiyoriy: Color (rang bo‘yicha galereya)
                 │     │
                 │     └── 1:N ── ProductVariant
                 │                      │
Color ───────────┴──────────────────────┤
                                        │
SizeType ─── 1:N ── Size ───────────────┘
                                        │
                                   stock, sku, narx
```

Keyinchalik (3-bosqich, hozir yaratilmaydi): `Customer`, `Order`, `OrderItem` → `ProductVariant`.

---

## 3. Har bir jadval nima saqlaydi

### 3.1. AgeGroup — yosh guruhi

Kiyim turidan **alohida**. Sabab: “jinsi” ham 4 yoshda, ham 16 yoshda bor. Yoshni kategoriya ichiga ko‘mib qo‘ysangiz, filtr keyin qiynaladi.

| Maydon | Maqsad |
|---|---|
| name | Chaqaloq, Kichkintoy, Maktab yoshi, O‘smir |
| slug | URL: `/catalog/osmir/` |
| min_age_months / max_age_months | 0–24, 24–84, 84–156, 156–216 |
| height_from_cm / height_to_cm | Qidiruvda “bo‘y 128” ni yoshga bog‘lash |
| sort_order | Sahifada tartib |
| is_active | Vaqtincha yashirish |

Tavsiya etilgan 4 guruh:

| Guruh | Yosh | Taxminiy bo‘y |
|---|---|---|
| Chaqaloq | 0–2 | 50–92 sm |
| Kichkintoy | 2–6 | 92–122 sm |
| Maktab yoshi | 7–12 | 122–152 sm |
| O‘smir | 13–18 | 152–182 sm |

Mahsulot **bir nechta** guruhga tushishi mumkin (masalan, 122 sm jinsi — kichkintoy va maktab yoshi chegarasida). Shuning uchun Product ↔ AgeGroup **ko‘p-ko‘p**.

---

### 3.2. Category — kiyim turi (daraxt)

O‘zini o‘ziga bog‘langan (`parent`). Ikki daraja yetarli, uchinchisi odatda ortiqcha.

**1-daraja (bo‘lim):**

1. Ustki kiyim
2. Pastki kiyim
3. Tashqi kiyim (qish/bahor)
4. Sport
5. Maktab
6. Ichki kiyim va paypoq
7. Poyabzal
8. Aksessuarlar
9. Komplektlar (sport kostyum, 2–3 qismli to‘plam)

**2-daraja (misol):**

- Ustki → futbolka, polo, ko‘ylak, hoodie, sviter, jemper, termal
- Pastki → jinsi, klassik shim, sport shim, shorti, bridj
- Tashqi → kurtka, palto, parka, jilet, yomg‘irpalto
- Sport → sport kostyum, futbolka, shorti
- Maktab → oq ko‘ylak, klassik shim, jilet, galstuk
- Poyabzal → krossovka, botinka, tufli, sandal, rezina etak
- Aksessuar → shapka, qo‘lqop, sharf, kamar, ryukzak

Maydonlar: `name`, `slug`, `parent`, `image`, `sort_order`, `is_active`, `meta_title`, `meta_description`.

Qoida: mahsulot **eng pastki** kategoriyaga bog‘lanadi (futbolka), ota-kategoriya (ustki kiyim) avtomatik yig‘adi.

---

### 3.3. SizeType va Size — o‘lcham tizimi (eng muhim)

O‘g‘il bolalar 0–18 da **bitta o‘lcham ustuni ishlamaydi**.

| SizeType kodi | Qayerda | Misollar |
|---|---|---|
| `height_cm` | Deyarli barcha kiyim (MDH standarti) | 50, 56, 62, 68, 74, 80, 86, 92, 98, 104, 110, 116, 122, 128, 134, 140, 146, 152, 158, 164, 170, 176, 182 |
| `age_month` | Chaqaloq, yordamchi yorliq | 0–3, 3–6, 6–9, 9–12, 12–18, 18–24 oy |
| `letter` | Ba’zi o‘smir / brend kiyim | XS, S, M, L, XL |
| `waist` | O‘smir jinsi / klassik shim | 26, 27, 28, 29, 30, 32, 34 |
| `eu_shoe` | Poyabzal | 16 … 45 |
| `underwear` | Ichki kiyim (ixtiyoriy) | 110, 122 … yoki 5–6 / 7–8 |

**Size** maydonlari:

- `size_type` — qaysi tizim
- `code` — saqlash: `134`, `28`, `32`
- `label` — ko‘rsatish: `134 sm` yoki `134 (8–9 yosh)`
- `age_from_years` / `age_to_years` — filtr: “7 yosh”
- `sort_order`

**Qoida:** kiyim uchun asosiy o‘lcham — **bo‘y (sm)**. Yosh faqat yorliq. Ota-ona “7 yoshga” deb qidiradi, ombor “128/134” deb yuritiladi.

Har bir **kategoriya** (yoki mahsulot) qaysi `SizeType` ishlatishini bilishi kerak. Futbolkaga poyabzal o‘lchamini chiqarmaslik uchun:

- `Category.default_size_type` yoki
- `Product.size_type`

Ikkinchisi aniqroq: bir brend jinsida bel, boshqasida bo‘y bo‘lishi mumkin.

---

### 3.4. Color — rang

| Maydon | Maqsad |
|---|---|
| name | Qora, Ko‘k, Bezheviy |
| slug | `qora` |
| hex_code | Kartochkada rang doirasi `#111111` |
| sort_order | |

Erkin matn yozmang. Aks holda “qora”, “Qora”, “black” uch xil bo‘lib ketadi.

O‘zbekistonda ko‘p ishlatiladigan boshlang‘ich palitra: qora, oq, kulrang, to‘q ko‘k, ko‘k, haki, bezheviy, jiyda, yashil, qizil, sariq, ko‘p rangli.

---

### 3.5. Product — vitrina kartochkasi

Bu yerda **qoldiq yo‘q**. Faqat odam o‘qiydigan ma’lumot.

| Maydon | Izoh |
|---|---|
| name | Qora klassik hoodie |
| slug | `qora-klassik-hoodie` — URL’da ID yo‘q |
| sku_prefix | Ixtiyoriy, variant SKU uchun |
| category | Eng pastki kategoriya |
| age_groups | Ko‘p-ko‘p |
| size_type | Shu mahsulot qaysi o‘lchamda |
| description | Matn |
| material | Paxta 80%, poliester 20% |
| season | spring / summer / autumn / winter / all |
| brand | Firdowear yoki tashqi brend (ixtiyoriy jadval) |
| price | Asosiy narx, **Decimal**, so‘m, butun yoki 2 xona |
| sale_price | Chegirma, bo‘sh bo‘lishi mumkin |
| is_new / is_on_sale / is_featured | Bosh sahifa bloklari |
| is_active | Yashirish (o‘chirmaslik) |
| care_notes | Yuvish |
| meta_title / meta_description | SEO |
| created_at / updated_at | |

**Narx qoidasi:** asosiy narx `Product`da. Agar 176 sm qimmatroq bo‘lsa, `ProductVariant.price_override`. Katalogda “N so‘mdan” ko‘rsatiladi.

**Chegirma:** `sale_price < price` bo‘lsa `is_on_sale` avtomatik hisoblanishi mumkin. Qo‘lda belgilash ham bo‘ladi.

**Komplekt:** 1-bosqichda oddiy mahsulot. Keyin `is_set` yoki alohida `ProductSet` — hozir shart emas.

---

### 3.6. ProductImage — rasmlar

| Maydon | Izoh |
|---|---|
| product | Qaysi mahsulot |
| color | Ixtiyoriy: qora rasmlar / ko‘k rasmlar |
| image | Fayl (media) |
| alt | SEO / maxsus imkoniyat |
| is_primary | Katalogdagi asosiy rasm |
| sort_order | |

Bitta mahsulotga ko‘p rasm. Rang tanlanganda galereya shu rangga almashadi — kiyim do‘konida bu muhim.

---

### 3.7. ProductVariant — haqiqiy ombor birligi

“134 sm, qora hoodie — 3 ta qolgan”.

| Maydon | Izoh |
|---|---|
| product | |
| size | |
| color | |
| sku | Unikal: `FW-HOOD-BLK-134` |
| stock | Butun son, 0 = tugagan |
| price_override | Bo‘sh = mahsulot narxi |
| is_active | Ayrim o‘lchamni yashirish |

**Unikal juftlik:** bir mahsulotda `(size, color)` takrorlanmaydi.

Sahifada:

- Rang tugmalari — qaysi ranglarda umuman `stock > 0`
- O‘lcham tugmalari — tanlangan rangda nima bor
- Tugagan o‘lcham ko‘rinadi, lekin bosilmaydi (“134 — tugagan”)

Admin: mahsulot sahifasida **inline** — tezkor qoldiq yangilash. Offlayn do‘kon uchun shu eng muhim qulaylik.

---

### 3.8. Brand — majburiy (do‘kon ko‘p brendli)

Firdowear — do‘kon nomi, brend emas. Do‘konda turli brendlar sotiladi, shuning uchun alohida jadval:

| Maydon | Izoh |
|---|---|
| name | Brend nomi (tarjima qilinmaydi) |
| slug | `/brand/nike/` |
| logo | Ixtiyoriy |
| country | Ixtiyoriy: Turkiya, Xitoy, O‘zbekiston — ota-onalar shuni so‘raydi |
| sort_order / is_active | |

`Product.brand` — FK, **bo‘sh bo‘lishi mumkin** (nomsiz / bozor mahsulotlari uchun). Filtrda “Brend” alohida chiqadi.

Sahifa: `/brand/<slug>/` — brend bo‘yicha katalog.

---

### 3.9. Ikki til (o‘zbek + rus) modelda qanday turadi

Ikki xil matn bor, ikkalasi turlicha hal qilinadi:

**A. Interfeys matnlari** — “Savat”, “Narx”, “Tugagan”, tugmalar. Django i18n: `gettext`, `.po` fayllar, `/uz/...` va `/ru/...` URL prefiksi. Bazaga tegmaydi.

**B. Bazadagi kontent** — mahsulot nomi, tavsif, kategoriya, rang. Bu `.po` bilan bo‘lmaydi, jadvalda **ikki maydon** kerak:

| Jadval | Tarjima qilinadigan maydonlar |
|---|---|
| Category | name, meta_title, meta_description |
| AgeGroup | name |
| Color | name |
| Size | label (`134 sm (8–9 yosh)` / `134 см (8–9 лет)`) |
| Product | name, description, material, care_notes, meta_* |
| ProductImage | alt |
| Brand, SizeType | tarjima yo‘q |

Usul: **`django-modeltranslation`** — mavjud maydonga avtomatik `name_uz`, `name_ru` qo‘shadi, admin’da ikki ustun chiqadi, kodda `product.name` joriy tilni o‘zi qaytaradi. Qo‘lda `name_uz`/`name_ru` yozishdan ko‘ra kamroq xato.

Qoidalar:

- **Asosiy til — o‘zbek** (`LANGUAGE_CODE = 'uz'`), rus — ikkinchi. Rus bo‘sh bo‘lsa, o‘zbekcha ko‘rinadi (fallback), sahifa bo‘sh qolmaydi.
- **Slug bitta**, tarjima qilinmaydi: `/ru/product/qora-hoodie/` — SEO uchun yetarli, ikki slug — ortiqcha murakkablik.
- Narx, o‘lcham kodi, SKU, rang hex — tarjimasiz.
- Admin panelda ikkala tilni to‘ldirish majburiy emas, lekin **o‘zbekchasi majburiy**.

URL:

```
/uz/catalog/tashqi-kiyim/
/ru/catalog/tashqi-kiyim/
```

Tanlagich header’da: UZ | RU. Birinchi kirishda brauzer tili bo‘yicha.

---

## 4. Hozir yaratilmaydigan, lekin joyni qoldirish kerak bo‘lgan narsalar

| Jadval | Qachon | Bog‘lanish |
|---|---|---|
| Customer | 4-bosqich | telefon, ism |
| Order | 3-bosqich | status, jami, Telegram chat |
| OrderItem | 3-bosqich | variant + soni + o‘sha paytdagi narx |
| Favorite | 4-bosqich | |

`OrderItem` mahsulotga emas, **variantga** bog‘lanadi. Aks holda “qaysi o‘lcham ketdi” yo‘qoladi.

Narx buyurtma paytida **nusxa** qilib yoziladi. Keyin mahsulot narxi o‘zgarsa, eski buyurtma buzilmaydi.

---

## 5. Qidiruv va filtr qanday ishlaydi (2-bosqich, lekin model shunga tayyor)

Ota-ona odatda shunday qidiradi:

1. Yosh yoki bo‘y
2. Kiyim turi
3. Fasl (qishki kurtka)
4. Narx
5. Rang
6. Maktab / sport

Filtrlar:

- `category` (+ bola-kategoriyalar)
- `age_group`
- `size` (yoki bo‘y oralig‘i)
- `color`
- `season`
- `price` min–max
- `is_new` / `is_on_sale`
- `in_stock` (hech bo‘lmaganda 1 variant `stock > 0`)

Shuning uchun yosh, o‘lcham, rang mahsulotning matn maydonida **bo‘lmasligi** kerak.

---

## 6. Admin panelda kunlik ish

Offlayn do‘konda sayt faqat shunda yashaydi:

1. Yangi kiyim: Product → rasmlar → variantlar (rang × o‘lcham × soni)
2. Sotuvdan keyin: shu kuniyoq `stock` ni kamaytirish (inline)
3. Tugaganini o‘chirmaslik — `stock = 0`. Kartochka qoladi, “buyurtma qilish / so‘rash” yoki yashirish
4. Chegirma: `sale_price` qo‘yish

Tezlik uchun: variantlarni admin’da jadval ko‘rinishida, `stock` ni bir klikda tahrirlash.

---

## 7. URL’lar (slug)

```
/                           bosh sahifa
/catalog/                   barcha
/catalog/tashqi-kiyim/      kategoriya
/catalog/osmir/             yosh guruhi (ixtiyoriy)
/product/qora-klassik-hoodie/
/page/manzil/
/search/?q=jinsi+134
```

ID raqam URL’da yo‘q.

---

## 8. 1-bosqichda nima bor, nima yo‘q

**Bor (modellarda):**

- AgeGroup, Category, SizeType, Size, Color
- Product, ProductImage, ProductVariant
- Brand (agar kerak)
- `created_at`, `is_active`, slug, Decimal narx

**Yo‘q:**

- Savat, buyurtma, to‘lov
- Foydalanuvchi kabineti
- “Sevimlilar”

Sahifalar 1-bosqich: bosh, katalog, mahsulot, manzil, Django admin.

---

## 9. O‘zbekiston / o‘g‘il bolalar uchun qo‘shimcha qoidalar

1. **Asosiy o‘lcham — sm (bo‘y).** Yosh — yordamchi yozuv.
2. **Poyabzal alohida tizim** — kiyim o‘lchami bilan aralashtirilmaydi.
3. **Fasl maydoni** — qishki tashqi kiyim savdoning katta qismi.
4. **Maktab** — alohida 1-daraja kategoriya. Ota-onalar shu yo‘l bilan kiradi.
5. **Narx — so‘m, Decimal yoki butun son.** Float yo‘q.
6. **Til:** o‘zbek asosiy, rus ikkinchi — boshidanoq. Kontent `django-modeltranslation`, interfeys `gettext` (3.9-bo‘lim).
8. **Poyabzal** — `eu_shoe` o‘lcham tizimi, alohida 1-daraja kategoriya, tashqi kiyim bilan aralashmaydi.
9. **Brend** — alohida jadval, filtr va `/brand/<slug>/` sahifa. Firdowear — do‘kon nomi, brend emas.
7. **Komplekt** (sport kostyum) 1-bosqichda bitta mahsulot + o‘lcham. Ikki qismni alohida ombor qilish — keyingi versiya.

---

## 10. Misollar (qanday yoziladi)

### Misol A — qora hoodie

- Category: Ustki kiyim → Hoodie
- AgeGroup: Maktab yoshi, O‘smir
- SizeType: height_cm
- Color: Qora, Kulrang
- Variantlar: 128/134/140/146/152 × 2 rang
- Narx: 189 000 so‘m, sale yo‘q

### Misol B — qishki kurtka

- Category: Tashqi kiyim → Parka
- AgeGroup: Kichkintoy, Maktab yoshi
- Season: winter
- Variantlar: 104–140, rang: haki, to‘q ko‘k
- sale_price: 320 000 (eski 410 000)

### Misol C — krossovka

- Category: Poyabzal → Krossovka
- SizeType: eu_shoe
- Variantlar: 28–39
- Product.size_type = eu_shoe — sahifada 134 sm chiqmaydi

### Misol D — chaqaloq bodisi

- AgeGroup: Chaqaloq
- SizeType: height_cm, label’da “80 sm (9–12 oy)”
- Category: Ustki yoki alohida “Chaqaloq” 2-darajasi — ikkalasi ham ishlaydi, lekin AgeGroup filtrini asosiy qiling

---

## 11. Qochish kerak bo‘lgan xatolar (shu do‘konga xos)

- O‘lchamni Product’da `CharField`: `"110, 116, 122"` — qoldiq va filtr o‘ladi
- Hammasini “Bolalar” degan bitta kategoriyaga tiqish
- Chaqaloq oyi, bo‘y va poyabzalni bitta ro‘yxatga aralashtirish
- Tugagan variantni o‘chirish (statistika va SEO yo‘qoladi)
- Narxni float
- Har bir rangni alohida Product qilish — o‘xshash kiyimlar katalogni shishiradi; rang = variant

---

## 12. Qabul qilingan qarorlar

| Savol | Qaror | Modelga ta’siri |
|---|---|---|
| Brend | Ko‘p brend, Firdowear — do‘kon nomi | `Brand` jadvali majburiy, `Product.brand` FK (bo‘sh bo‘lishi mumkin) |
| Poyabzal | Bor | `SizeType = eu_shoe`, kategoriya “Poyabzal”, `Product.size_type` majburiy |
| Til | O‘zbek + rus | `django-modeltranslation`, `LANGUAGE_CODE='uz'`, URL prefiksi `/uz/` `/ru/` |

## 13. Keyingi qadam

Reja tayyor. Keyingi suhbatda Django loyihasini shu tartibda yozamiz:

1. Loyiha + `.env` + `products` app
2. Modellar: Brand, AgeGroup, Category, SizeType, Size, Color, Product, ProductImage, ProductVariant
3. `modeltranslation` sozlash (uz/ru)
4. Admin: variantlar inline, ikki tilli maydonlar
5. Boshlang‘ich ma’lumotlar: kategoriyalar, o‘lchamlar (50–182 sm, poyabzal 16–45), ranglar, yosh guruhlari
6. Sahifalar: bosh, katalog, mahsulot, manzil
