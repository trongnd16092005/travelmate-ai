import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class PlaceKnowledge:
    id: str
    name: str


@dataclass(frozen=True)
class DestinationKnowledge:
    id: str
    name: str
    aliases: tuple[str, ...]
    places: tuple[PlaceKnowledge, ...]
    foods: tuple[str, ...]

    @property
    def place_by_id(self) -> dict[str, PlaceKnowledge]:
        return {place.id: place for place in self.places}


RAW_DESTINATIONS: tuple[
    tuple[str, tuple[str, ...], tuple[str, str, str], tuple[str, str, str]], ...
] = (
    (
        "Đà Nẵng",
        ("Da Nang",),
        ("bán đảo Sơn Trà", "Ngũ Hành Sơn", "bãi biển Mỹ Khê"),
        ("mì Quảng", "bánh tráng cuốn thịt heo", "bún chả cá"),
    ),
    (
        "Huế",
        ("Thừa Thiên Huế", "Hue"),
        ("Đại Nội", "chùa Thiên Mụ", "lăng Khải Định"),
        ("bún bò Huế", "cơm hến", "bánh bèo"),
    ),
    (
        "Hội An",
        ("Hoi An",),
        ("Chùa Cầu", "phố cổ", "làng gốm Thanh Hà"),
        ("cao lầu", "cơm gà", "bánh mì Hội An"),
    ),
    (
        "Đà Lạt",
        ("Da Lat",),
        ("hồ Xuân Hương", "vườn hoa thành phố", "núi Langbiang"),
        ("bánh căn", "lẩu gà lá é", "sữa đậu nành"),
    ),
    (
        "Nha Trang",
        (),
        ("tháp Bà Ponagar", "hòn Chồng", "bãi biển Nha Trang"),
        ("bún cá", "nem nướng", "bánh căn hải sản"),
    ),
    (
        "Phú Quốc",
        ("Phu Quoc",),
        ("Bãi Sao", "Dinh Cậu", "vườn quốc gia Phú Quốc"),
        ("gỏi cá trích", "bún quậy", "hải sản"),
    ),
    (
        "Hà Nội",
        ("Ha Noi",),
        ("hồ Hoàn Kiếm", "Văn Miếu", "phố cổ Hà Nội"),
        ("phở", "bún chả", "chả cá"),
    ),
    (
        "TP. Hồ Chí Minh",
        ("TP.HCM", "TP HCM", "Hồ Chí Minh", "Sài Gòn", "Sai Gon"),
        ("Dinh Độc Lập", "Bưu điện Trung tâm", "chợ Bến Thành"),
        ("cơm tấm", "hủ tiếu", "bánh mì"),
    ),
    (
        "Sa Pa",
        ("Sapa",),
        ("bản Cát Cát", "Fansipan", "thung lũng Mường Hoa"),
        ("thắng cố", "cá hồi", "lợn cắp nách"),
    ),
    (
        "Ninh Bình",
        ("Ninh Binh",),
        ("Tràng An", "Hang Múa", "cố đô Hoa Lư"),
        ("cơm cháy", "dê núi", "miến lươn"),
    ),
    (
        "Hạ Long",
        ("Ha Long",),
        ("vịnh Hạ Long", "Bảo tàng Quảng Ninh", "Bãi Cháy"),
        ("chả mực", "bún bề bề", "sam biển"),
    ),
    (
        "Quy Nhơn",
        ("Quy Nhon",),
        ("Kỳ Co", "Eo Gió", "Ghềnh Ráng"),
        ("bánh xèo tôm nhảy", "bún chả cá", "tré"),
    ),
    (
        "Vũng Tàu",
        ("Vung Tau",),
        ("Bãi Sau", "tượng Chúa Kitô", "mũi Nghinh Phong"),
        ("bánh khọt", "lẩu cá đuối", "hải sản"),
    ),
    (
        "Cần Thơ",
        ("Can Tho",),
        ("chợ nổi Cái Răng", "nhà cổ Bình Thủy", "bến Ninh Kiều"),
        ("bánh cống", "lẩu mắm", "nem nướng Cái Răng"),
    ),
    (
        "Mũi Né",
        ("Mui Ne",),
        ("đồi cát", "Suối Tiên", "làng chài Mũi Né"),
        ("bánh căn", "gỏi cá mai", "hải sản"),
    ),
    (
        "Hà Giang",
        ("Ha Giang",),
        ("đèo Mã Pì Lèng", "phố cổ Đồng Văn", "cột cờ Lũng Cú"),
        ("cháo ấu tẩu", "bánh tam giác mạch", "thắng dền"),
    ),
    (
        "Cao Bằng",
        ("Cao Bang",),
        ("thác Bản Giốc", "động Ngườm Ngao", "hồ Thang Hen"),
        ("bánh cuốn", "vịt quay", "hạt dẻ Trùng Khánh"),
    ),
    (
        "Buôn Ma Thuột",
        ("Buon Ma Thuot",),
        ("Bảo tàng Thế giới Cà phê", "Buôn Đôn", "thác Dray Nur"),
        ("bún đỏ", "cơm lam", "gà nướng"),
    ),
    (
        "Tây Ninh",
        ("Tay Ninh",),
        ("núi Bà Đen", "Tòa Thánh Tây Ninh", "hồ Dầu Tiếng"),
        ("bánh canh Trảng Bàng", "bò tơ", "bánh tráng phơi sương"),
    ),
    (
        "Quảng Bình",
        ("Quang Binh",),
        ("Phong Nha", "động Thiên Đường", "suối Nước Moọc"),
        ("cháo canh", "bánh bột lọc", "khoai deo"),
    ),
)


def normalize_lookup_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold().strip()).replace("đ", "d")
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def slugify(value: str) -> str:
    return normalize_lookup_key(value).replace(" ", "-")


DESTINATIONS: tuple[DestinationKnowledge, ...] = tuple(
    DestinationKnowledge(
        id=slugify(name),
        name=name,
        aliases=aliases,
        places=tuple(
            PlaceKnowledge(id=f"{slugify(name)}:{slugify(place)}", name=place)
            for place in places
        ),
        foods=foods,
    )
    for name, aliases, places, foods in RAW_DESTINATIONS
)

DESTINATION_BY_KEY: dict[str, DestinationKnowledge] = {
    normalize_lookup_key(value): destination
    for destination in DESTINATIONS
    for value in (destination.name, *destination.aliases)
}


def resolve_destination(value: str) -> DestinationKnowledge | None:
    return DESTINATION_BY_KEY.get(normalize_lookup_key(value))
