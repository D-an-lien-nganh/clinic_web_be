from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter,OpenApiExample
from rest_framework import status
from .serializers import *

def position_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách chức vụ",
            description="API này trả về danh sách chức vụ với các bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã, tên chức vụ, phòng ban)"),
            ],
            responses={200: PositionSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách chức vụ",
                    description="Ví dụ về phản hồi trả về danh sách chức vụ.",
                    value={
                        "count": 1,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T12:00:00Z",
                                "user": 2,
                                "department": 3,
                                "department_name": "Phòng Kinh Doanh",
                                "code": "MG001",
                                "title": "Manager"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo chức vụ mới",
            description="API này cho phép tạo một chức vụ mới.",
            request=PositionSerializer,
            responses={201: PositionSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo chức vụ mới",
                    description="Ví dụ về request tạo chức vụ.",
                    request_only=True,
                    value={
                        "department": 3,
                        "code": "MG002",
                        "title": "Trưởng Phòng Nhân Sự"
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo chức vụ",
                    description="Ví dụ về phản hồi khi tạo chức vụ.",
                    response_only=True,
                    value={
                        "id": 2,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "department": 3,
                        "department_name": "Phòng Nhân Sự",
                        "code": "MG002",
                        "title": "Trưởng Phòng Nhân Sự"
                    }
                )
            ]
        )
    )

def department_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách phòng ban",
            description="API này trả về danh sách các phòng ban với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã, tên phòng ban, người dùng)"),
            ],
            responses={200: DepartmentSerialzier(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách phòng ban",
                    description="Ví dụ về phản hồi khi lấy danh sách phòng ban.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "code": "HR001",
                                "name": "Phòng Nhân Sự"
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "code": "IT001",
                                "name": "Phòng Công Nghệ Thông Tin"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo phòng ban mới",
            description="API này cho phép tạo một phòng ban mới.",
            request=DepartmentSerialzier,
            responses={201: DepartmentSerialzier},
            examples=[
                OpenApiExample(
                    name="Tạo phòng ban mới",
                    description="Ví dụ về request tạo phòng ban.",
                    request_only=True,
                    value={
                        "code": "HR002",
                        "name": "Phòng Đào Tạo"
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo phòng ban",
                    description="Ví dụ về phản hồi khi tạo phòng ban.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "code": "HR002",
                        "name": "Phòng Đào Tạo"
                    }
                )
            ]
        )
    )

def floor_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách tầng",
            description="API này trả về danh sách các tầng với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã, tên tầng, người dùng)"),
            ],
            responses={200: FloorSerialzier(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách tầng",
                    description="Ví dụ về phản hồi khi lấy danh sách tầng.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "code": "F001",
                                "name": "Tầng 1"
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "code": "F002",
                                "name": "Tầng 2"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo tầng mới",
            description="API này cho phép tạo một tầng mới.",
            request=FloorSerialzier,
            responses={201: FloorSerialzier},
            examples=[
                OpenApiExample(
                    name="Tạo tầng mới",
                    description="Ví dụ về request tạo tầng.",
                    request_only=True,
                    value={
                        "code": "F003",
                        "name": "Tầng 3"
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo tầng",
                    description="Ví dụ về phản hồi khi tạo tầng.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "code": "F003",
                        "name": "Tầng 3"
                    }
                )
            ]
        )
    )

def protocol_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách giao thức",
            description="API này trả về danh sách các giao thức với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (mã, tên giao thức, người dùng)"),
            ],
            responses={200: ProtocolSerialzier(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách giao thức",
                    description="Ví dụ về phản hồi khi lấy danh sách giao thức.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "code": "P001",
                                "name": "Giao thức A"
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "code": "P002",
                                "name": "Giao thức B"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo giao thức mới",
            description="API này cho phép tạo một giao thức mới.",
            request=ProtocolSerialzier,
            responses={201: ProtocolSerialzier},
            examples=[
                OpenApiExample(
                    name="Tạo giao thức mới",
                    description="Ví dụ về request tạo giao thức.",
                    request_only=True,
                    value={
                        "code": "P003",
                        "name": "Giao thức C"
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo giao thức",
                    description="Ví dụ về phản hồi khi tạo giao thức.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "code": "P003",
                        "name": "Giao thức C"
                    }
                )
            ]
        )
    )

def commission_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách hoa hồng",
            description="API này trả về danh sách các hoa hồng với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (phần trăm hoa hồng, người dùng)"),
            ],
            responses={200: CommissionSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách hoa hồng",
                    description="Ví dụ về phản hồi khi lấy danh sách hoa hồng.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "percentage": "10%"
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "percentage": "15%"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo hoa hồng mới",
            description="API này cho phép tạo một khoản hoa hồng mới.",
            request=CommissionSerializer,
            responses={201: CommissionSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo hoa hồng mới",
                    description="Ví dụ về request tạo hoa hồng.",
                    request_only=True,
                    value={
                        "percentage": "12%"
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo hoa hồng",
                    description="Ví dụ về phản hồi khi tạo hoa hồng.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "percentage": "12%"
                    }
                )
            ]
        )
    )
def discount_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách giảm giá",
            description="API này trả về danh sách các chương trình giảm giá với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (tên, mã giảm giá, phần trăm giảm, người dùng)"),
            ],
            responses={200: DiscountSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách giảm giá",
                    description="Ví dụ về phản hồi khi lấy danh sách giảm giá.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "name": "Giảm giá Tết",
                                "code": "TET2025",
                                "type": "Phần trăm",
                                "rate": 10,
                                "start_date": "2025-02-01",
                                "end_date": "2025-02-10",
                                "note": "Áp dụng cho tất cả sản phẩm."
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "name": "Giảm giá Sinh Nhật",
                                "code": "BDAY2025",
                                "type": "Giá cố định",
                                "rate": 50000,
                                "start_date": "2025-03-01",
                                "end_date": "2025-03-07",
                                "note": "Chỉ áp dụng cho thành viên VIP."
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo giảm giá mới",
            description="API này cho phép tạo một chương trình giảm giá mới.",
            request=DiscountSerializer,
            responses={201: DiscountSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo giảm giá mới",
                    description="Ví dụ về request tạo giảm giá.",
                    request_only=True,
                    value={
                        "name": "Giảm giá Hè",
                        "code": "SUMMER2025",
                        "type": "Phần trăm",
                        "rate": 15,
                        "start_date": "2025-06-01",
                        "end_date": "2025-06-30",
                        "note": "Áp dụng cho đơn hàng từ 1 triệu trở lên."
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo giảm giá",
                    description="Ví dụ về phản hồi khi tạo giảm giá.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "name": "Giảm giá Hè",
                        "code": "SUMMER2025",
                        "type": "Phần trăm",
                        "rate": 15,
                        "start_date": "2025-06-01",
                        "end_date": "2025-06-30",
                        "note": "Áp dụng cho đơn hàng từ 1 triệu trở lên."
                    }
                )
            ]
        )
    )

def lead_source_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách nguồn khách hàng",
            description="API này trả về danh sách các nguồn khách hàng với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (tên nguồn, người dùng)"),
            ],
            responses={200: LeadSourceSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách nguồn khách hàng",
                    description="Ví dụ về phản hồi khi lấy danh sách nguồn khách hàng.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "name": "Facebook Ads",
                                "color": "#0D6EFD",
                                "note": "Chạy quảng cáo trên Facebook."
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "name": "Google Search",
                                "color": "#FF5733",
                                "note": "Khách hàng từ Google tìm kiếm."
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo nguồn khách hàng mới",
            description="API này cho phép tạo một nguồn khách hàng mới.",
            request=LeadSourceSerializer,
            responses={201: LeadSourceSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo nguồn khách hàng mới",
                    description="Ví dụ về request tạo nguồn khách hàng.",
                    request_only=True,
                    value={
                        "name": "TikTok Ads",
                        "color": "#FF4500",
                        "note": "Quảng cáo từ TikTok."
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo nguồn khách hàng",
                    description="Ví dụ về phản hồi khi tạo nguồn khách hàng.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "name": "TikTok Ads",
                        "color": "#FF4500",
                        "note": "Quảng cáo từ TikTok."
                    }
                )
            ]
        )
    )

def time_frame_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách khung giờ",
            description="API này trả về danh sách các khung giờ với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Tìm kiếm theo người dùng."),
            ],
            responses={200: TimeFrameSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách khung giờ",
                    description="Ví dụ về phản hồi khi lấy danh sách khung giờ.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "start": "08:00",
                                "end": "10:00",
                                "note": "Ca sáng"
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "start": "14:00",
                                "end": "16:00",
                                "note": "Ca chiều"
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo khung giờ mới",
            description="API này cho phép tạo một khung giờ mới.",
            request=TimeFrameSerializer,
            responses={201: TimeFrameSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo khung giờ mới",
                    description="Ví dụ về request tạo khung giờ.",
                    request_only=True,
                    value={
                        "start": "18:00",
                        "end": "20:00",
                        "note": "Ca tối"
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo khung giờ",
                    description="Ví dụ về phản hồi khi tạo khung giờ.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "start": "18:00",
                        "end": "20:00",
                        "note": "Ca tối"
                    }
                )
            ]
        )
    )

def unit_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Lấy danh sách đơn vị",
            description="API này trả về danh sách các đơn vị với bộ lọc theo ngày tạo và từ khóa tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, description="Ngày bắt đầu (YYYY-MM-DD)"),
                OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, description="Ngày kết thúc (YYYY-MM-DD)"),
                OpenApiParameter(name="searchTerm", type=str, location=OpenApiParameter.QUERY, description="Từ khóa tìm kiếm (tên đơn vị, người dùng)"),
            ],
            responses={200: UnitSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Danh sách đơn vị",
                    description="Ví dụ về phản hồi khi lấy danh sách đơn vị.",
                    value={
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "created": "2025-03-02T10:00:00Z",
                                "user": 2,
                                "name": "Đơn vị A",
                                "color": "#0D6EFD",
                                "note": "Đơn vị quản lý chính."
                            },
                            {
                                "id": 2,
                                "created": "2025-03-02T11:00:00Z",
                                "user": 3,
                                "name": "Đơn vị B",
                                "color": "#FF5733",
                                "note": "Đơn vị hỗ trợ."
                            }
                        ]
                    }
                )
            ]
        ),
        create=extend_schema(
            summary="Tạo đơn vị mới",
            description="API này cho phép tạo một đơn vị mới.",
            request=UnitSerializer,
            responses={201: UnitSerializer},
            examples=[
                OpenApiExample(
                    name="Tạo đơn vị mới",
                    description="Ví dụ về request tạo đơn vị.",
                    request_only=True,
                    value={
                        "name": "Đơn vị C",
                        "color": "#FF4500",
                        "note": "Đơn vị quản lý khu vực phía Nam."
                    }
                ),
                OpenApiExample(
                    name="Phản hồi khi tạo đơn vị",
                    description="Ví dụ về phản hồi khi tạo đơn vị.",
                    response_only=True,
                    value={
                        "id": 3,
                        "created": "2025-03-02T12:05:00Z",
                        "user": 5,
                        "name": "Đơn vị C",
                        "color": "#FF4500",
                        "note": "Đơn vị quản lý khu vực phía Nam."
                    }
                )
            ]
        )
    )
def treatment_package_schema_view():
    return extend_schema_view(
    list=extend_schema(
        summary="Danh sách Gói Liệu Trình",
        description=(
            "Lấy danh sách tất cả các gói liệu trình. "
            "Có thể tìm kiếm theo tên hoặc mô tả bằng tham số `searchTerm`."
        ),
        parameters=[
            OpenApiParameter(
                name='searchTerm',
                type=str,
                required=False,
                description="Từ khóa tìm kiếm theo tên hoặc mô tả gói liệu trình."
            )
        ],
        responses=TreatmentPackageSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Chi tiết Gói Liệu Trình",
        description="Xem chi tiết thông tin của một gói liệu trình theo ID.",
        responses=TreatmentPackageSerializer,
    ),
    create=extend_schema(
        summary="Tạo mới Gói Liệu Trình",
        description="Tạo mới một gói liệu trình.",
        request=TreatmentPackageSerializer,
        responses=TreatmentPackageSerializer,
    ),
    update=extend_schema(
        summary="Cập nhật Gói Liệu Trình",
        description="Cập nhật toàn bộ thông tin của một gói liệu trình.",
        request=TreatmentPackageSerializer,
        responses=TreatmentPackageSerializer,
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần Gói Liệu Trình",
        description="Cập nhật một phần thông tin của một gói liệu trình.",
        request=TreatmentPackageSerializer,
        responses=TreatmentPackageSerializer,
    ),
    destroy=extend_schema(
        summary="Xóa Gói Liệu Trình",
        description="Xóa một gói liệu trình theo ID.",
        responses=None,
    ),
)
def test_service_schema_view():
    return extend_schema_view(
    list=extend_schema(
        summary="Danh sách Dịch vụ Xét nghiệm",
        description="Lấy danh sách tất cả dịch vụ xét nghiệm. Có thể tìm kiếm theo mã, tên hoặc mô tả.",
        parameters=[
            OpenApiParameter(
                name='searchTerm',
                type=str,
                required=False,
                description="Từ khóa tìm kiếm theo mã, tên hoặc mô tả dịch vụ xét nghiệm."
            )
        ],
        responses=TestServiceSerializer(many=True)
    ),
    retrieve=extend_schema(
        summary="Chi tiết Dịch vụ Xét nghiệm",
        description="Xem chi tiết thông tin một dịch vụ xét nghiệm theo ID.",
        responses=TestServiceSerializer
    ),
    create=extend_schema(
        summary="Tạo mới Dịch vụ Xét nghiệm",
        description="Tạo mới một dịch vụ xét nghiệm.",
        request=TestServiceSerializer,
        responses=TestServiceSerializer
    ),
    update=extend_schema(
        summary="Cập nhật Dịch vụ Xét nghiệm",
        description="Cập nhật toàn bộ thông tin của một dịch vụ xét nghiệm.",
        request=TestServiceSerializer,
        responses=TestServiceSerializer
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần Dịch vụ Xét nghiệm",
        description="Cập nhật một phần thông tin của một dịch vụ xét nghiệm.",
        request=TestServiceSerializer,
        responses=TestServiceSerializer
    ),
    destroy=extend_schema(
        summary="Xóa Dịch vụ Xét nghiệm",
        description="Xóa một dịch vụ xét nghiệm theo ID.",
        responses=None
    )
)