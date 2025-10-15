from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiTypes
)
from rest_framework import status
from .serializers import FacilitySerializer, FixScheduleSerializer, MaintenanceSerializer, ServiceSerializer, ProductSerializer, StockInSerializer, StockOutSerializer, SupplierSerializer, WarehouseSerializer


def service_schema():
    """
    Decorator sinh tài liệu OpenAPI cho ServiceViewSet.
    """
    return extend_schema_view(
        # -------- LIST ------------------------------------------------------
        list=extend_schema(
            tags=["app_product"],
            summary="Lấy danh sách dịch vụ",
            description=(
                "Trả về danh sách dịch vụ.\n"
                "- Lọc theo ngày tạo (startDate, endDate)\n"
                "- Tìm kiếm theo tên, mã, trạng thái (searchTerm)\n"
                "- Lọc theo trạng thái (status)"
            ),
            parameters=[
                OpenApiParameter("startDate", str, False, description="YYYY-MM-DD"),
                OpenApiParameter("endDate", str, False, description="YYYY-MM-DD"),
                OpenApiParameter("searchTerm", str, False,
                                 description="Từ khóa (tên, mã, trạng thái)"),
                OpenApiParameter("status", str, False, description="Trạng thái dịch vụ"),
            ],
            responses={200: ServiceSerializer(many=True)},
        ),

        # -------- RETRIEVE --------------------------------------------------
        retrieve=extend_schema(
            tags=["app_product"],
            summary="Lấy chi tiết dịch vụ",
            description="Chi tiết một dịch vụ theo ID.",
            responses={200: ServiceSerializer},
        ),

        # -------- CREATE ----------------------------------------------------
        create=extend_schema(
            tags=["app_product"],
            summary="Tạo dịch vụ mới",
            description=("Tạo mới dịch vụ, kèm gói liệu trình (treatment_packages) "
                         "và kỹ thuật (technical_settings)."),
            request=ServiceSerializer,
            examples=[
                OpenApiExample(
                    "Tạo dịch vụ mới",
                    value={
                        "name": "Dịch vụ thải hàn khí từ bụng lên",
                        "status": "active",
                        "type": "TLCB",
                        "treatment_packages": [
                            {"treatment_package_id": 1, "price": 100_000, "duration": 60},
                            {"treatment_package_id": 2, "price": 200_000, "duration": 120}
                        ],
                        "technical_settings": [1, 2, 3]
                    },
                )
            ],
            responses={201: ServiceSerializer},
        ),

        # -------- UPDATE ----------------------------------------------------
        update=extend_schema(
            tags=["app_product"],
            summary="Cập nhật dịch vụ",
            description="Cập nhật toàn bộ dịch vụ (PUT).",
            request=ServiceSerializer,
            examples=[
                OpenApiExample(
                    "Cập nhật dịch vụ",
                    value={
                        "name": "Dịch vụ Detox bụng – cập nhật",
                        "status": "active",
                        "type": "TLDS",
                        "treatment_packages": [
                            {"treatment_package_id": 2, "price": 250_000}
                        ],
                        "technical_settings": [2, 4]
                    },
                )
            ],
            responses={200: ServiceSerializer},
        ),

        # -------- PARTIAL UPDATE -------------------------------------------
        partial_update=extend_schema(
            tags=["app_product"],
            summary="Cập nhật một phần dịch vụ",
            description="Chỉ gửi các trường cần cập nhật (PATCH).",
            request=ServiceSerializer,
            examples=[
                OpenApiExample(
                    "PATCH thay đổi trạng thái",
                    value={"status": "inactive"},
                )
            ],
            responses={200: ServiceSerializer},
        ),

        # -------- DESTROY ---------------------------------------------------
        destroy=extend_schema(
            tags=["app_product"],
            summary="Xóa dịch vụ",
            description="Xóa dịch vụ theo ID.",
            responses={status.HTTP_204_NO_CONTENT: None},
        ),
    )
def product_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách sản phẩm",
            description="API này trả về danh sách các sản phẩm với bộ lọc theo ngày tạo, từ khóa tìm kiếm và trạng thái.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã, tên, công dụng, mô tả, xuất xứ)"),
                OpenApiParameter(name="status", type=str, location=OpenApiParameter.QUERY, description="Trạng thái sản phẩm"),
            ],
            responses={200: ProductSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách sản phẩm",
                    description="Ví dụ về phản hồi khi lấy danh sách sản phẩm.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "code": "SP001",
                                "name": "Sản phẩm A",
                                "description": "Mô tả sản phẩm A",
                                "effect": "Hiệu quả của sản phẩm A",
                                "origin": "Việt Nam",
                                "sell_price": "150000.00",
                                "unit": 1,
                                "unit_name": "Hộp"
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "code": "SP002",
                                "name": "Sản phẩm B",
                                "description": "Mô tả sản phẩm B",
                                "effect": "Hiệu quả của sản phẩm B",
                                "origin": "Nhật Bản",
                                "sell_price": "250000.00",
                                "unit": 2,
                                "unit_name": "Chai"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo sản phẩm mới",
            description="API này cho phép tạo một sản phẩm mới.",
            request=ProductSerializer,
            responses={201: ProductSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo sản phẩm mới",
                    description="Ví dụ về request tạo sản phẩm.",
                    request_only=True,
                    value={
                        "name": "Sản phẩm C",
                        "description": "Mô tả sản phẩm C",
                        "effect": "Công dụng của sản phẩm C",
                        "origin": "Mỹ",
                        "sell_price": "350000.00",
                        "unit": 3,
                        "product_type":1
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo sản phẩm",
                    description="Ví dụ về phản hồi khi tạo sản phẩm.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "code": "SP003",
                        "name": "Sản phẩm C",
                        "description": "Mô tả sản phẩm C",
                        "effect": "Công dụng của sản phẩm C",
                        "origin": "Mỹ",
                        "sell_price": "350000.00",
                        "unit": 3,
                        "unit_name": "Gói"
                    }
                )
            ]
        )
    )

def maintenance_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách bảo trì",
            description="API này trả về danh sách các lần bảo trì với bộ lọc theo cơ sở vật chất.",
            parameters=[
                OpenApiParameter(name="facility_id", type=int, location=OpenApiParameter.QUERY, description="Lọc theo ID của cơ sở vật chất"),
            ],
            responses={200: MaintenanceSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách bảo trì",
                    description="Ví dụ về phản hồi khi lấy danh sách bảo trì.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "date": "2025-03-01",
                                "note": "Kiểm tra định kỳ",
                                "status": "1",
                                "status_name": "Chờ xử lý",
                                "is_maintenanced": False,
                                "facility": 1,
                                "facility_name": "Máy điều hòa"
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "date": "2025-02-25",
                                "note": "Thay thế bộ lọc",
                                "status": "2",
                                "status_name": "Đã hoàn thành",
                                "is_maintenanced": True,
                                "facility": 2,
                                "facility_name": "Máy lọc nước"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo yêu cầu bảo trì mới",
            description="API này cho phép tạo một yêu cầu bảo trì mới.",
            request=MaintenanceSerializer,
            responses={201: MaintenanceSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo bảo trì mới",
                    description="Ví dụ về request tạo bảo trì.",
                    request_only=True,
                    value={
                        "date": "2025-04-10",
                        "note": "Sửa chữa động cơ",
                        "status": "1",
                        "is_maintenanced": False,
                        "facility": 3
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo bảo trì",
                    description="Ví dụ về phản hồi khi tạo bảo trì.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "date": "2025-04-10",
                        "note": "Sửa chữa động cơ",
                        "status": "1",
                        "status_name": "Chờ xử lý",
                        "is_maintenanced": False,
                        "facility": 3,
                        "facility_name": "Máy phát điện"
                    }
                )
            ]
        )
    )

def fix_schedule_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách lịch sửa chữa",
            description="API này trả về danh sách các lịch sửa chữa với bộ lọc theo cơ sở vật chất.",
            parameters=[
                OpenApiParameter(name="facility_id", type=int, location=OpenApiParameter.QUERY, description="Lọc theo ID của cơ sở vật chất"),
            ],
            responses={200: FixScheduleSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách lịch sửa chữa",
                    description="Ví dụ về phản hồi khi lấy danh sách lịch sửa chữa.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "date": "2025-03-15",
                                "note": "Thay linh kiện hỏng",
                                "status": "1",
                                "is_fixed": False,
                                "facility": 1,
                                "facility_name": "Máy điều hòa"
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "date": "2025-02-28",
                                "note": "Sửa động cơ",
                                "status": "2",
                                "is_fixed": True,
                                "facility": 2,
                                "facility_name": "Máy bơm nước"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo lịch sửa chữa mới",
            description="API này cho phép tạo một lịch sửa chữa mới.",
            request=FixScheduleSerializer,
            responses={201: FixScheduleSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo lịch sửa chữa mới",
                    description="Ví dụ về request tạo lịch sửa chữa.",
                    request_only=True,
                    value={
                        "date": "2025-04-20",
                        "note": "Bảo dưỡng động cơ",
                        "status": "1",
                        "is_fixed": False,
                        "facility": 3
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo lịch sửa chữa",
                    description="Ví dụ về phản hồi khi tạo lịch sửa chữa.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "date": "2025-04-20",
                        "note": "Bảo dưỡng động cơ",
                        "status": "1",
                        "is_fixed": False,
                        "facility": 3,
                        "facility_name": "Máy phát điện"
                    }
                )
            ]
        )
    )

def facility_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách cơ sở vật chất",
            description="API này trả về danh sách các cơ sở vật chất với bộ lọc theo ngày tạo, từ khóa tìm kiếm, trạng thái và tình trạng hỏng hóc.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã, tên, công dụng, mô tả, xuất xứ)"),
                OpenApiParameter(name="status", type=str, location=OpenApiParameter.QUERY, description="Trạng thái của cơ sở vật chất"),
                OpenApiParameter(name="is_malfunction", type=bool, location=OpenApiParameter.QUERY, description="Lọc theo tình trạng hỏng hóc (true/false)"),
            ],
            responses={200: FacilitySerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách cơ sở vật chất",
                    description="Ví dụ về phản hồi khi lấy danh sách cơ sở vật chất.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "code": "FAC001",
                                "name": "Máy điều hòa",
                                "origin": "Nhật Bản",
                                "quantity": 5,
                                "import_price": "15000000.00",
                                "status": "new",
                                "is_malfunction": False,
                                "effect": "Làm lạnh nhanh",
                                "malfunction_status": "",
                                "unit": 1,
                                "is_active": True
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "code": "FAC002",
                                "name": "Máy lọc nước",
                                "origin": "Hàn Quốc",
                                "quantity": 3,
                                "import_price": "5000000.00",
                                "status": "used",
                                "is_malfunction": True,
                                "effect": "Lọc nước sạch",
                                "malfunction_status": "Cần thay lõi lọc",
                                "unit": 2,
                                "is_active": True
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo cơ sở vật chất mới",
            description="API này cho phép tạo một cơ sở vật chất mới.",
            request=FacilitySerializer,
            responses={201: FacilitySerializer},
            examples=[
                OpenApiExample(
                    name="Tạo cơ sở vật chất mới",
                    description="Ví dụ về request tạo cơ sở vật chất.",
                    request_only=True,
                    value={
                        "name": "Máy phát điện",
                        "origin": "Mỹ",
                        "quantity": 2,
                        "import_price": "25000000.00",
                        "status": "new",
                        "is_malfunction": False,
                        "effect": "Cung cấp điện dự phòng",
                        "unit": 3
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo cơ sở vật chất",
                    description="Ví dụ về phản hồi khi tạo cơ sở vật chất.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "code": "FAC003",
                        "name": "Máy phát điện",
                        "origin": "Mỹ",
                        "quantity": 2,
                        "import_price": "25000000.00",
                        "status": "new",
                        "is_malfunction": False,
                        "effect": "Cung cấp điện dự phòng",
                        "malfunction_status": "",
                        "unit": 3,
                        "is_active": True
                    }
                )
            ]
        ),
    )

def supplier_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách nhà cung cấp",
            description="API này trả về danh sách các nhà cung cấp với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã, tên, MST, người liên hệ, số điện thoại, email)"),
            ],
            responses={200: SupplierSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách nhà cung cấp",
                    description="Ví dụ về phản hồi khi lấy danh sách nhà cung cấp.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "code": "SUP001",
                                "name": "Công ty TNHH ABC",
                                "MST": "0101234567",
                                "contact_person": "Nguyễn Văn A",
                                "mobile": "0987654321",
                                "email": "abc@supplier.com",
                                "address": "123 Đường ABC, Hà Nội",
                                "is_active": True
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "code": "SUP002",
                                "name": "Công ty CP XYZ",
                                "MST": "0207654321",
                                "contact_person": "Trần Thị B",
                                "mobile": "0976543210",
                                "email": "xyz@supplier.com",
                                "address": "456 Đường XYZ, TP. Hồ Chí Minh",
                                "is_active": True
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo nhà cung cấp mới",
            description="API này cho phép tạo một nhà cung cấp mới.",
            request=SupplierSerializer,
            responses={201: SupplierSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo nhà cung cấp mới",
                    description="Ví dụ về request tạo nhà cung cấp.",
                    request_only=True,
                    value={
                        "name": "Công ty TNHH DEF",
                        "MST": "0309876543",
                        "contact_person": "Lê Văn C",
                        "mobile": "0965432109",
                        "email": "def@supplier.com",
                        "address": "789 Đường DEF, Đà Nẵng"
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo nhà cung cấp",
                    description="Ví dụ về phản hồi khi tạo nhà cung cấp.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "code": "SUP003",
                        "name": "Công ty TNHH DEF",
                        "MST": "0309876543",
                        "contact_person": "Lê Văn C",
                        "mobile": "0965432109",
                        "email": "def@supplier.com",
                        "address": "789 Đường DEF, Đà Nẵng",
                        "is_active": True
                    }
                )
            ]
        )
    )

def stock_in_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách đơn nhập kho",
            description=(
                "API trả về danh sách phiếu nhập kho. Hỗ trợ lọc theo khoảng ngày, loại chứng từ (product/facility), "
                "nhà cung cấp, sản phẩm, vật tư, trạng thái thanh toán và kích hoạt.\n\n"
                "**Lưu ý:** Mỗi phiếu nhập **chỉ chọn 1 trong 2**: `product` **hoặc** `facility` (ràng buộc XOR)."
            ),
            parameters=[
                OpenApiParameter(name="startDate", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY,
                                 description="Ngày bắt đầu (YYYY-MM-DD), so theo `created` hoặc `import_date` tùy triển khai."),
                OpenApiParameter(name="endDate", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY,
                                 description="Ngày kết thúc (YYYY-MM-DD)."),
                OpenApiParameter(name="itemType", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                                 description="Lọc theo loại chứng từ: `product` hoặc `facility`."),
                OpenApiParameter(name="supplier", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                                 description="ID Nhà cung cấp."),
                OpenApiParameter(name="product", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                                 description="ID Sản phẩm (chỉ áp dụng khi itemType=product)."),
                OpenApiParameter(name="facility", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                                 description="ID Vật tư (chỉ áp dụng khi itemType=facility)."),
                OpenApiParameter(name="full_paid", type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY,
                                 description="Đã thanh toán đủ hay chưa."),
                OpenApiParameter(name="is_active", type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY,
                                 description="Bản ghi còn hiệu lực."),
                OpenApiParameter(name="code", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                                 description="Tìm theo mã phiếu nhập."),
                OpenApiParameter(name="searchTerm", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                                 description="Từ khóa chung (mã, tên NCC, tên SP/VT, người duyệt)."),
            ],
            responses={200: StockInSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách phiếu nhập (mixed product & facility)",
                    description="Ví dụ phản hồi khi lấy danh sách phiếu nhập gồm cả sản phẩm và vật tư.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-08-01T10:00:00Z",
                                "user": 2,
                                "code": "SI20250801100000",
                                "supplier": 1,
                                "supplier_name": "Công ty TNHH ABC",
                                "product": 1,
                                "product_name": "Máy điều hòa",
                                "facility": None,
                                "facility_name": None,
                                "quantity": 10,
                                "import_price": "15000000.00",
                                "full_paid": False,
                                "import_date": "2025-08-01",
                                "approver": 3,
                                "approver_username": "admin",
                                "note": "Nhập đợt 1",
                                "is_active": True
                            },
                            {
                                "id": 2,
                                "created": "2025-08-02T11:00:00Z",
                                "user": 3,
                                "code": "SI20250802110000",
                                "supplier": 1,
                                "supplier_name": "Công ty TNHH ABC",
                                "product": None,
                                "product_name": None,
                                "facility": 5,
                                "facility_name": "Micro không dây",
                                "quantity": 20,
                                "import_price": "1500000.00",
                                "full_paid": True,
                                "import_date": "2025-08-02",
                                "approver": 4,
                                "approver_username": "manager",
                                "note": "Nhập vật tư hội trường",
                                "is_active": True
                            }
                        ]
                    },
                )
            ],
        ),
        create=extend_schema(
            summary="Tạo phiếu nhập kho mới",
            description=(
                "API tạo mới phiếu nhập kho cho **sản phẩm** hoặc **vật tư**.\n\n"
                "**Ràng buộc:** `product` XOR `facility` (chỉ 1 trong 2 được điền)."
            ),
            request=StockInSerializer,
            responses={201: StockInSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo phiếu nhập **sản phẩm**",
                    description="Ví dụ request/response khi tạo phiếu nhập cho SẢN PHẨM.",
                    request_only=True,
                    value={
                        "supplier": 1,
                        "product": 1,
                        "facility": None,
                        "quantity": 20,
                        "import_price": "14000000.00",
                        "import_date": "2025-08-03",
                        "approver": 3,
                        "note": "Nhập đợt 2 (SP)"
                    },
                ),
                OpenApiExample(
                    name="Phản hồi tạo phiếu nhập **sản phẩm**",
                    description="Ví dụ response khi tạo thành công.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-08-03T12:05:00Z",
                        "user": 5,
                        "code": "SI20250803120500",
                        "supplier": 1,
                        "supplier_name": "Công ty TNHH ABC",
                        "product": 1,
                        "product_name": "Máy điều hòa",
                        "facility": None,
                        "facility_name": None,
                        "quantity": 20,
                        "import_price": "14000000.00",
                        "full_paid": False,
                        "import_date": "2025-08-03",
                        "approver": 3,
                        "approver_username": "admin",
                        "note": "Nhập đợt 2 (SP)",
                        "is_active": True
                    },
                ),
                OpenApiExample(
                    name="Tạo phiếu nhập **vật tư**",
                    description="Ví dụ request tạo phiếu nhập cho VẬT TƯ.",
                    request_only=True,
                    value={
                        "supplier": 1,
                        "product": None,
                        "facility": 5,
                        "quantity": 12,
                        "import_price": "1200000.00",
                        "import_date": "2025-08-04",
                        "approver": 4,
                        "note": "Nhập vật tư (VT)"
                    },
                ),
                OpenApiExample(
                    name="Phản hồi tạo phiếu nhập **vật tư**",
                    description="Ví dụ response khi tạo thành công.",
                    response_only=True,
                    value={
                        "id": 4,
                        "created": "2025-08-04T09:30:00Z",
                        "user": 5,
                        "code": "SI20250804093000",
                        "supplier": 1,
                        "supplier_name": "Công ty TNHH ABC",
                        "product": None,
                        "product_name": None,
                        "facility": 5,
                        "facility_name": "Micro không dây",
                        "quantity": 12,
                        "import_price": "1200000.00",
                        "full_paid": False,
                        "import_date": "2025-08-04",
                        "approver": 4,
                        "approver_username": "manager",
                        "note": "Nhập vật tư (VT)",
                        "is_active": True
                    },
                ),
            ],
        ),
    )

def stock_out_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách đơn xuất kho",
            description="API này trả về danh sách các đơn xuất kho với bộ lọc theo ngày tạo, trạng thái, loại xuất kho và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="status", type=str, location=OpenApiParameter.QUERY, description="Trạng thái đơn xuất"),
                OpenApiParameter(name="type", type=str, location=OpenApiParameter.QUERY, description="Loại xuất kho"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã, nhà cung cấp, sản phẩm, người duyệt)"),
            ],
            responses={200: StockOutSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách đơn xuất kho",
                    description="Ví dụ về phản hồi khi lấy danh sách đơn xuất kho.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "code": "SO20250302100000",
                                "supplier": 1,
                                "supplier_name": "Công ty TNHH ABC",
                                "product": 1,
                                "product_name": "Máy điều hòa",
                                "quantity": 5,
                                "export_date": "2025-03-01",
                                "approver": 3,
                                "approver_username": "admin",
                                "type": "Bán hàng",
                                "actual_stockout_price": "75000000.00",
                                "note": "Xuất bán cho khách hàng",
                                "is_active": True
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "code": "SO20250302110000",
                                "supplier": 2,
                                "supplier_name": "Công ty CP XYZ",
                                "product": 2,
                                "product_name": "Máy lọc nước",
                                "quantity": 3,
                                "export_date": "2025-02-28",
                                "approver": 4,
                                "approver_username": "manager",
                                "type": "Xuất hỏng",
                                "actual_stockout_price": "15000000.00",
                                "note": "Xuất để sửa chữa",
                                "is_active": True
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo đơn xuất kho mới",
            description="API này cho phép tạo một đơn xuất kho mới.",
            request=StockOutSerializer,
            responses={201: StockOutSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo đơn xuất kho mới",
                    description="Ví dụ về request tạo đơn xuất kho.",
                    request_only=True,
                    value={
                        "supplier": 1,
                        "product": 1,
                        "quantity": 10,
                        "export_date": "2025-04-01",
                        "approver": 3,
                        "type": "Bán hàng",
                        "actual_stockout_price": "150000000.00",
                        "note": "Xuất kho theo đơn đặt hàng"
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo đơn xuất kho",
                    description="Ví dụ về phản hồi khi tạo đơn xuất kho.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "code": "SO20250302120500",
                        "supplier": 1,
                        "supplier_name": "Công ty TNHH ABC",
                        "product": 1,
                        "product_name": "Máy điều hòa",
                        "quantity": 10,
                        "export_date": "2025-04-01",
                        "approver": 3,
                        "approver_username": "admin",
                        "type": "Bán hàng",
                        "actual_stockout_price": "150000000.00",
                        "note": "Xuất kho theo đơn đặt hàng",
                        "is_active": True
                    }
                )
            ]
        ),
        # update=extend_schema(
        #     summary="Cập nhật đơn xuất kho",
        #     description="Chỉ có thể cập nhật khi trạng thái đơn xuất là 'pending'.",
        #     responses={403: OpenApiExample(
        #         name="Không thể cập nhật",
        #         description="Ví dụ về phản hồi khi không thể cập nhật đơn xuất kho.",
        #         value={"detail": "Không thể sửa khi trạng thái không phải là 'pending'."}
        #     )}
        # ),
        # partial_update=extend_schema(
        #     summary="Cập nhật một phần đơn xuất kho",
        #     description="Chỉ có thể cập nhật khi trạng thái đơn xuất là 'pending'.",
        #     responses={403: OpenApiExample(
        #         name="Không thể cập nhật",
        #         description="Ví dụ về phản hồi khi không thể cập nhật đơn xuất kho.",
        #         value={"detail": "Không thể sửa khi trạng thái không phải là 'pending'."}
        #     )}
        # ),
        # destroy=extend_schema(
        #     summary="Xóa đơn xuất kho",
        #     description="Chỉ có thể xóa khi trạng thái đơn xuất là 'pending'. Hành động này chỉ đặt `is_active` thành `False` thay vì xóa vĩnh viễn.",
        #     responses={
        #         200: OpenApiExample(
        #             name="Xóa đơn xuất kho",
        #             description="Ví dụ về phản hồi khi xóa đơn xuất kho.",
        #             value={"detail": "Đã xóa đơn xuất (is_active=false)."}
        #         ),
        #         403: OpenApiExample(
        #             name="Không thể xóa",
        #             description="Ví dụ về phản hồi khi không thể xóa đơn xuất kho.",
        #             value={"detail": "Không thể xóa khi trạng thái không phải là 'pending'."}
        #         )
        #     }
        # )
    )

def warehouse_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách kho hàng",
            description="API này trả về danh sách kho hàng với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã kho, nhà cung cấp, sản phẩm)"),
            ],
            responses={200: WarehouseSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách kho hàng",
                    description="Ví dụ về phản hồi khi lấy danh sách kho hàng.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "code": "WH20250302100000",
                                "supplier": 1,
                                "supplier_name": "Công ty TNHH ABC",
                                "product": 1,
                                "product_name": "Máy điều hòa",
                                "quantity": 50,
                                "import_date": "2025-03-01",
                                "export_date": None
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "code": "WH20250302110000",
                                "supplier": 2,
                                "supplier_name": "Công ty CP XYZ",
                                "product": 2,
                                "product_name": "Máy lọc nước",
                                "quantity": 30,
                                "import_date": "2025-02-28",
                                "export_date": "2025-03-10"
                            }
                        ]
                    }
                )
            ]
        )
    )
def service_treatment_package_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách các gói dịch vụ điều trị",
            description="Trả về danh sách tất cả các mối quan hệ giữa Dịch vụ và Gói điều trị.",
            tags=["Gói dịch vụ điều trị"]
        ),
        retrieve=extend_schema(
            summary="Chi tiết gói dịch vụ điều trị",
            description="Trả về thông tin chi tiết của một mối quan hệ giữa Dịch vụ và Gói điều trị cụ thể.",
            tags=["Gói dịch vụ điều trị"]
        ),
        create=extend_schema(
            summary="Tạo mới gói dịch vụ điều trị",
            description="Tạo mới một mối quan hệ giữa Dịch vụ và Gói điều trị.",
            tags=["Gói dịch vụ điều trị"]
        ),
        update=extend_schema(
            summary="Cập nhật toàn bộ gói dịch vụ điều trị",
            description="Cập nhật toàn bộ thông tin của một mối quan hệ giữa Dịch vụ và Gói điều trị.",
            tags=["Gói dịch vụ điều trị"]
        ),
        partial_update=extend_schema(
            summary="Cập nhật một phần gói dịch vụ điều trị",
            description="Cập nhật một phần thông tin của một mối quan hệ giữa Dịch vụ và Gói điều trị.",
            tags=["Gói dịch vụ điều trị"]
        ),
        destroy=extend_schema(
            summary="Xoá gói dịch vụ điều trị",
            description="Xoá một mối quan hệ giữa Dịch vụ và Gói điều trị khỏi hệ thống.",
            tags=["Gói dịch vụ điều trị"]
        ),
    )