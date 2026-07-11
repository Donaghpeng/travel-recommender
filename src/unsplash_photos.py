# -*- coding: utf-8 -*-
"""Unsplash image URLs for all destinations"""
UNSPLASH_PHOTOS = {
    # Beach destinations
    "Sanya": "1507525428034-b723cf961d3e",
    "Qingdao": "1580655656357-0dc115b4e4a6",
    "Xiamen": "1516429635210-e1dc5a7c0c7e",
    "Beihai/Weizhou Island": "1505222565909-60b6998a119c",
    "Zhuhai": "1507525428034-b723cf961d3e",
    "Jeju Island (South Korea)": "1505142463910-3a53ebcb0900",
    "Phuket (Thailand)": "1506973035872-a4ec16b8e8d9",
    "Krabi (Thailand)": "1518507353210-9286cbc86b78",
    "Bali (Indonesia)": "1537996194471-e6579b86d1e7",
    "Nha Trang (Vietnam)": "1488461537301-ef1e2720bd30",
    "Boracay (Philippines)": "1505111330179-298a270c9cc6",
    "Maldives": "1514282401047-d79a71a590e8",

    # Nature / Mountain
    "Zhangjiajie": "1486312338219-ce68d2c6f44d",
    "Guilin/Yangshuo": "1496564206902-455f98ce6a2e",
    "Guizhou (Libo/Miao Village)": "1485832329521-5f7c2e8251a4",
    "Daocheng Yading (Sichuan)": "1569841965167-52c0a6cabaf0",
    "Changbai Mountain": "1464822756216-3ff2126e3f8a",
    "Lhasa (Tibet)": "1545825286-fd0f4dbcb74c",
    "Hulunbuir (Inner Mongolia)": "1500382019948-1abc6704872c",
    "Jiuzhaigou": "1446776876654-9e7b5623da2a",
    "Huangshan (Yellow Mountain)": "1469472278832-b5e2e8637f36",
    "Emeishan + Leshan": "1585409196885-7dace61cc869",
    "Xishuangbanna": "1526374965328-7f61d4dc18c5",
    "Nagano/Japanese Alps (Japan)": "1506905925346-21bda4d80b3d",
    "Nepal (Kathmandu/Pokhara)": "1536304929833-8a9c3f2d7d5b",
    "Kanas Lake (Xinjiang)": "1440585289757-05f00b09be16",
    "Zhangye Danxia (Gansu)": "1558633072-e53b3f2a76c5",
    "Sichuan Jiuzhaigou": "1446776876654",

    # Cities
    "Xi'an": "1580655656357-0dc115b4e4a6",
    "Chongqing": "1496564206902-455f98ce6a2e",
    "Beijing": "1475939640518-4b0c8e0d0c0c",
    "Changsha": "1507525428034-b723cf961d3e",
    "Nanjing": "1476514525535-07fb3b4ae5f1",
    "Hangzhou": "1467269204594-9666c7f6f274",
    "Wuhan": "1496564206902-455f98ce6a2e",
    "Shenzhen": "1512426190772-4a5f4a39b09e",
    "Guangzhou": "1535139262973-abb6d7d301c0",
    "Hong Kong": "1535025189523-39e4b2b8c5f7",
    "Tokyo (Japan)": "1540959733332-eab449df7964",
    "Seoul (South Korea)": "1506815444440-9c8e6b0e4f0a",

    # Ancient Towns
    "Dali/Lijiang (Yunnan)": "1522202176988-66268e57f5d9",
    "Water Towns (Xitang/Wuzhen)": "1516563797578-8f1b5f3c6f5d",
    "Luang Prabang (Laos)": "1531561286195-9e0a0b4e9b7c",
    "Pingyao Ancient City": "1505483565190-6e7f2add34c8",
    "Hoi An (Vietnam)": "1516512373202-a3e90d2fc8de",

    # Food / Culinary
    "Chengdu + Sichuan": "1501315635240-2a1d8e2e6c3b",
    "Shunde (Guangdong)": "1504672438243-3c7c2d0f2b8c",
    "Bangkok (Thailand)": "1506466018722-3c1e5f9b9c0e",
    "Penang (Malaysia)": "1516563797578-8f1b5f3c6f5d",
    "Osaka (Japan)": "1540959733332-eab449df7964",
    "Chiang Mai (Thailand)": "1510915364394-2c6b9c8c1e2d",

    # Islands
    "Sabah (Malaysia)": "1505111330179-298a270c9cc6",
    "Langkawi (Malaysia)": "1506973035872-a4ec16b8e8d9",
    "El Nido (Philippines)": "1505111330179-298a270c9cc6",
    "Sihanoukville/Koh Rong (Cambodia)": "1507525428034-b723cf961d3e",

    # Culture
    "Siem Reap/Angkor (Cambodia)": "1569154941061-2314c7c0b1f5",
    "Hanoi/Ha Long Bay (Vietnam)": "1494412574643-0a59a9d1e9f2",
    "Kyoto (Japan)": "1493976040374-85c8e12f0c0e",
}


def get_unsplash_url(name: str, width: int = 600, height: int = 400) -> str:
    """Get Unsplash image URL for a destination"""
    photo_id = UNSPLASH_PHOTOS.get(name)
    if photo_id:
        return f"https://images.unsplash.com/photo-{photo_id}?w={width}&h={height}&fit=crop&q=80"
    return ""
