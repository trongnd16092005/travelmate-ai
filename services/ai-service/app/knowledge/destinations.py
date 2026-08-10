import re
import unicodedata
from dataclasses import dataclass

from app.knowledge.province_catalog import (
    NATIONWIDE_RAW_PROVINCES,
    RUNTIME_TOURISM_PLACE_EXPANSIONS,
)


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
    region: str
    themes: tuple[str, ...]

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
    (
        "Cát Bà",
        ("Cat Ba", "đảo Cát Bà"),
        ("vịnh Lan Hạ", "Vườn quốc gia Cát Bà", "bãi Cát Cò"),
        ("tu hài", "sam biển", "bún tôm"),
    ),
    (
        "Cô Tô",
        ("Co To", "đảo Cô Tô"),
        ("bãi Hồng Vàn", "bãi Vàn Chảy", "hải đăng Cô Tô"),
        ("cù kỳ", "sá sùng", "hải sản"),
    ),
    (
        "Quan Lạn",
        ("Quan Lan", "đảo Quan Lạn", "Minh Châu"),
        ("bãi Quan Lạn", "bãi Minh Châu", "đình Quan Lạn"),
        ("sá sùng", "cầu gai", "hải sản"),
    ),
    (
        "Móng Cái",
        ("Mong Cai", "Trà Cổ", "Tra Co"),
        ("bãi biển Trà Cổ", "mũi Sa Vĩ", "đình Trà Cổ"),
        ("cù kỳ", "sam biển", "hải sản Trà Cổ"),
    ),
    (
        "Đồ Sơn",
        ("Do Son", "bãi biển Đồ Sơn"),
        ("bãi biển Đồ Sơn", "đảo Hòn Dấu", "dinh Bảo Đại"),
        ("bánh đa cua", "nem cua bể", "hải sản"),
    ),
    (
        "Mộc Châu",
        ("Moc Chau",),
        ("đồi chè trái tim", "thác Dải Yếm", "rừng thông Bản Áng"),
        ("bê chao", "cá suối", "sữa Mộc Châu"),
    ),
    (
        "Mai Châu",
        ("Mai Chau",),
        ("bản Lác", "đèo Thung Khe", "hang Chiều"),
        ("cơm lam", "gà đồi", "thịt lợn nướng"),
    ),
    (
        "Tam Đảo",
        ("Tam Dao",),
        ("nhà thờ đá Tam Đảo", "thác Bạc", "Cầu Mây"),
        ("ngọn su su", "gà đồi", "lợn mán"),
    ),
    (
        "Sầm Sơn",
        ("Sam Son", "Thanh Hóa", "Thanh Hoa"),
        ("bãi biển Sầm Sơn", "hòn Trống Mái", "đền Độc Cước"),
        ("nem chua", "chả tôm", "hải sản"),
    ),
    (
        "Cửa Lò",
        ("Cua Lo", "Nghệ An", "Nghe An"),
        ("bãi biển Cửa Lò", "đảo Lan Châu", "đảo Hòn Ngư"),
        ("cháo nghêu", "mực nháy", "lươn Nghệ An"),
    ),
    (
        "Phú Yên",
        ("Phu Yen", "Tuy Hòa", "Tuy Hoa"),
        ("Gành Đá Đĩa", "Bãi Xép", "Mũi Điện"),
        ("mắt cá ngừ đại dương", "sò huyết Ô Loan", "bánh hỏi lòng heo"),
    ),
    (
        "Lý Sơn",
        ("Ly Son", "đảo Lý Sơn"),
        ("cổng Tò Vò", "núi Thới Lới", "đảo Bé"),
        ("gỏi tỏi", "cua huỳnh đế", "ốc mặt trăng"),
    ),
    (
        "Côn Đảo",
        ("Con Dao", "Côn Sơn", "Con Son"),
        ("bãi Đầm Trầu", "Vườn quốc gia Côn Đảo", "Bảo tàng Côn Đảo"),
        ("ốc vú nàng", "mứt hạt bàng", "hải sản"),
    ),
    (
        "Châu Đốc",
        ("Chau Doc", "An Giang"),
        ("miếu Bà Chúa Xứ", "rừng tràm Trà Sư", "làng Chăm Châu Phong"),
        ("bún cá Châu Đốc", "mắm Châu Đốc", "tung lò mò"),
    ),
    (
        "Bến Tre",
        ("Ben Tre",),
        ("cồn Phụng", "cồn Quy", "làng hoa Chợ Lách"),
        ("cơm dừa", "bánh xèo ốc gạo", "kẹo dừa"),
    ),
)


DESTINATION_METADATA: dict[str, tuple[str, tuple[str, ...]]] = {
    "Đà Nẵng": ("Miền Trung", ("biển", "đô thị", "nghỉ dưỡng")),
    "Huế": ("Miền Trung", ("văn hóa", "lịch sử", "ẩm thực")),
    "Hội An": ("Miền Trung", ("văn hóa", "lịch sử", "biển")),
    "Đà Lạt": ("Tây Nguyên", ("thiên nhiên", "nghỉ dưỡng", "núi")),
    "Nha Trang": ("Miền Trung", ("biển", "nghỉ dưỡng", "đảo")),
    "Phú Quốc": ("Miền Nam", ("biển", "nghỉ dưỡng", "đảo")),
    "Hà Nội": ("Miền Bắc", ("văn hóa", "lịch sử", "đô thị", "ẩm thực")),
    "TP. Hồ Chí Minh": ("Miền Nam", ("đô thị", "văn hóa", "ẩm thực")),
    "Sa Pa": ("Miền Bắc", ("núi", "thiên nhiên", "văn hóa")),
    "Ninh Bình": ("Miền Bắc", ("thiên nhiên", "văn hóa", "lịch sử")),
    "Hạ Long": ("Miền Bắc", ("biển", "đảo", "thiên nhiên", "nghỉ dưỡng")),
    "Quy Nhơn": ("Miền Trung", ("biển", "nghỉ dưỡng", "ẩm thực")),
    "Vũng Tàu": ("Miền Nam", ("biển", "đô thị", "nghỉ dưỡng")),
    "Cần Thơ": ("Miền Nam", ("sông nước", "văn hóa", "ẩm thực")),
    "Mũi Né": ("Miền Trung", ("biển", "thiên nhiên", "nghỉ dưỡng")),
    "Hà Giang": ("Miền Bắc", ("núi", "thiên nhiên", "văn hóa")),
    "Cao Bằng": ("Miền Bắc", ("núi", "thiên nhiên", "văn hóa")),
    "Buôn Ma Thuột": ("Tây Nguyên", ("văn hóa", "thiên nhiên", "ẩm thực")),
    "Tây Ninh": ("Miền Nam", ("núi", "văn hóa", "tâm linh")),
    "Quảng Bình": ("Miền Trung", ("thiên nhiên", "hang động", "biển")),
    "Cát Bà": ("Miền Bắc", ("biển", "đảo", "thiên nhiên", "phiêu lưu")),
    "Cô Tô": ("Miền Bắc", ("biển", "đảo", "nghỉ dưỡng")),
    "Quan Lạn": ("Miền Bắc", ("biển", "đảo", "nghỉ dưỡng", "văn hóa")),
    "Móng Cái": ("Miền Bắc", ("biển", "văn hóa", "ẩm thực")),
    "Đồ Sơn": ("Miền Bắc", ("biển", "nghỉ dưỡng", "văn hóa")),
    "Mộc Châu": ("Miền Bắc", ("núi", "thiên nhiên", "nghỉ dưỡng")),
    "Mai Châu": ("Miền Bắc", ("núi", "thiên nhiên", "văn hóa")),
    "Tam Đảo": ("Miền Bắc", ("núi", "nghỉ dưỡng", "thiên nhiên")),
    "Sầm Sơn": ("Miền Trung", ("biển", "nghỉ dưỡng", "văn hóa")),
    "Cửa Lò": ("Miền Trung", ("biển", "nghỉ dưỡng", "đảo")),
    "Phú Yên": ("Miền Trung", ("biển", "thiên nhiên", "ẩm thực")),
    "Lý Sơn": ("Miền Trung", ("biển", "đảo", "thiên nhiên", "văn hóa")),
    "Côn Đảo": ("Miền Nam", ("biển", "đảo", "thiên nhiên", "lịch sử")),
    "Châu Đốc": ("Miền Nam", ("sông nước", "văn hóa", "tâm linh")),
    "Bến Tre": ("Miền Nam", ("sông nước", "văn hóa", "ẩm thực")),
}


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
        region=DESTINATION_METADATA[name][0],
        themes=DESTINATION_METADATA[name][1],
    )
    for name, aliases, places, foods in RAW_DESTINATIONS
)

NATIONWIDE_DESTINATIONS: tuple[DestinationKnowledge, ...] = tuple(
    DestinationKnowledge(
        id=f"vn-{code}-{slugify(name)}",
        name=name,
        aliases=aliases,
        places=tuple(
            PlaceKnowledge(id=f"vn-{code}:{slugify(place)}", name=place)
            for place in places
        ),
        foods=foods,
        region=region,
        themes=themes,
    )
    for code, name, aliases, places, foods, region, themes in NATIONWIDE_RAW_PROVINCES
)

RUNTIME_NATIONWIDE_DESTINATIONS: tuple[DestinationKnowledge, ...] = tuple(
    DestinationKnowledge(
        id=f"vn-{code}-{slugify(name)}",
        name=name,
        aliases=aliases,
        places=tuple(
            PlaceKnowledge(id=f"vn-{code}:{slugify(place)}", name=place)
            for place in (*places, *RUNTIME_TOURISM_PLACE_EXPANSIONS.get(name, ()))
        ),
        foods=foods,
        region=region,
        themes=themes,
    )
    for code, name, aliases, places, foods, region, themes in NATIONWIDE_RAW_PROVINCES
)

_legacy_names = {destination.name for destination in DESTINATIONS}
RUNTIME_DESTINATIONS: tuple[DestinationKnowledge, ...] = (
    *DESTINATIONS,
    *(
        destination
        for destination in RUNTIME_NATIONWIDE_DESTINATIONS
        if destination.name not in _legacy_names
    ),
)

# Frozen catalog used to reproduce the audited v1-v5 datasets. Runtime and v6 use
# DESTINATIONS, while old builders deliberately retain their original 20-item scope.
CORE_DESTINATIONS: tuple[DestinationKnowledge, ...] = DESTINATIONS[:20]

DESTINATION_BY_KEY: dict[str, DestinationKnowledge] = {
    normalize_lookup_key(value): destination
    for destination in (*DESTINATIONS, *RUNTIME_NATIONWIDE_DESTINATIONS)
    for value in (destination.name, *destination.aliases)
}


def resolve_destination(value: str) -> DestinationKnowledge | None:
    return DESTINATION_BY_KEY.get(normalize_lookup_key(value))


def find_destination_mentions(value: str) -> list[tuple[int, int, DestinationKnowledge]]:
    """Find catalog destinations in text, resolving legacy aliases to current units."""
    normalized = normalize_lookup_key(value)
    matches: list[tuple[int, int, DestinationKnowledge]] = []
    for key, destination in DESTINATION_BY_KEY.items():
        for match in re.finditer(rf"(?<!\w){re.escape(key)}(?!\w)", normalized):
            matches.append((match.start(), match.end(), destination))
    return matches


def grounded_place_by_id(destination: DestinationKnowledge) -> dict[str, PlaceKnowledge]:
    """Return current and backward-compatible place IDs for one province catalog entry."""
    places = dict(destination.place_by_id)
    for legacy_destination in DESTINATIONS:
        mapped_destination = DESTINATION_BY_KEY.get(
            normalize_lookup_key(legacy_destination.name)
        )
        if mapped_destination is not None and mapped_destination.name == destination.name:
            places.update(legacy_destination.place_by_id)
    return places


def format_grounded_catalog_context(destination: DestinationKnowledge) -> str:
    """Build the single source-of-truth context shared by runtime and training."""
    allowed_places = "; ".join(
        f"{place_id} | {place.name}"
        for place_id, place in grounded_place_by_id(destination).items()
    )
    allowed_foods = "; ".join(destination.foods)
    return (
        "[GROUNDED_CATALOG]\n"
        f"Tỉnh/thành hiện hành: {destination.name}\n"
        f"Địa điểm được phép: {allowed_places}\n"
        f"Ẩm thực được phép: {allowed_foods}\n"
        "Không tạo thêm tên địa điểm hoặc món ăn ngoài danh sách. Nếu dữ liệu không đủ, "
        "nói rõ chưa có trong catalog. Không khẳng định giá, giờ mở cửa, thời tiết hay "
        "tình trạng dịch vụ khi chưa có nguồn realtime.\n"
        "[/GROUNDED_CATALOG]"
    )


def recommend_destinations(
    region: str | None = None,
    themes: tuple[str, ...] = (),
    limit: int = 5,
) -> tuple[DestinationKnowledge, ...]:
    """Return catalog-grounded destinations ranked by region and requested themes."""
    theme_aliases = {"nghi ngoi": "nghi duong"}
    normalized_themes = {
        theme_aliases.get(normalize_lookup_key(theme), normalize_lookup_key(theme))
        for theme in themes
    }
    candidates = [
        destination
        for destination in RUNTIME_DESTINATIONS
        if region is None or destination.region == region
    ]
    ranked = sorted(
        candidates,
        key=lambda destination: -len(
            normalized_themes
            & {normalize_lookup_key(theme) for theme in destination.themes}
        ),
    )
    if normalized_themes:
        matching = [
            destination
            for destination in ranked
            if normalized_themes
            & {normalize_lookup_key(theme) for theme in destination.themes}
        ]
        if matching:
            ranked = matching
    return tuple(ranked[:limit])


def recommend_provinces(
    region: str | None = None,
    themes: tuple[str, ...] = (),
    limit: int = 5,
) -> tuple[DestinationKnowledge, ...]:
    """Recommend only current province-level units from the nationwide catalog."""
    normalized_themes = {normalize_lookup_key(theme) for theme in themes}
    candidates = [
        destination
        for destination in RUNTIME_NATIONWIDE_DESTINATIONS
        if region is None or destination.region == region
    ]
    ranked = sorted(
        candidates,
        key=lambda destination: -len(
            normalized_themes
            & {normalize_lookup_key(theme) for theme in destination.themes}
        ),
    )
    if normalized_themes:
        matching = [
            destination
            for destination in ranked
            if normalized_themes
            & {normalize_lookup_key(theme) for theme in destination.themes}
        ]
        if matching:
            ranked = matching
    return tuple(ranked[:limit])
