from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter,OpenApiExample, OpenApiResponse
from rest_framework import status
from .serializers import *
from drf_spectacular.types import OpenApiTypes

def lead_status_schema():
    return extend_schema_view(
        list=extend_schema(
            tags=["app_lead"],
            summary="Danh sách trạng thái lead",
            description="Lấy danh sách tất cả các trạng thái lead trong hệ thống.",
            parameters=[
                OpenApiParameter(name="searchTerm", description="Tìm kiếm theo tên trạng thái", required=False, type=str),
                OpenApiParameter(name="startDate", description="Ngày bắt đầu (YYYY-MM-DD)", required=False, type=str),
                OpenApiParameter(name="endDate", description="Ngày kết thúc (YYYY-MM-DD)", required=False, type=str),
            ],
            responses=LeadStatusSerializer,  # Serializer trả về dữ liệu
        ),
        retrieve=extend_schema(
            tags=["app_lead"],
            summary="Chi tiết trạng thái lead",
            description="Lấy thông tin chi tiết của một trạng thái lead theo ID.",
            responses=LeadStatusSerializer,  # Serializer trả về dữ liệu
        ),
        create=extend_schema(
            tags=["app_lead"],
            summary="Tạo trạng thái lead mới",
            description="API để tạo một trạng thái lead mới.",
            request={
                "application/json": {
                    "name": "Trạng thái 1",
                    "description": "Mô tả trạng thái 1",
                }
            },
            responses=LeadStatusSerializer,  # Serializer trả về dữ liệu
        ),
        update=extend_schema(
            tags=["app_lead"],
            summary="Cập nhật trạng thái lead",
            description="API để cập nhật thông tin của một trạng thái lead theo ID.",
            request={
                "application/json": {
                    "name": "Trạng thái 1",
                    "description": "Mô tả trạng thái 1",
                }
            },
            responses=LeadStatusSerializer,  # Serializer trả về dữ liệu
        ),
        destroy=extend_schema(
            tags=["app_lead"],
            summary="Xóa trạng thái lead",
            description="API để xóa một trạng thái lead (is_active=False).",
            responses={200: {"detail": "Đã xóa trạng thái lead (is_active=false)."}},
        )
    )

def treatment_state_schema():
    return extend_schema_view(
        list=extend_schema(
            tags=["app_treatment"],
            summary="Danh sách trạng thái điều trị",
            description="Lấy danh sách tất cả các trạng thái điều trị trong hệ thống.",
            parameters=[
                OpenApiParameter(name="searchTerm", description="Tìm kiếm theo tên trạng thái", required=False, type=str),
                OpenApiParameter(name="startDate", description="Ngày bắt đầu (YYYY-MM-DD)", required=False, type=str),
                OpenApiParameter(name="endDate", description="Ngày kết thúc (YYYY-MM-DD)", required=False, type=str),
            ],
            responses=TreatmentStateSerializer,  # Serializer trả về dữ liệu
        ),
        retrieve=extend_schema(
            tags=["app_treatment"],
            summary="Chi tiết trạng thái điều trị",
            description="Lấy thông tin chi tiết của một trạng thái điều trị theo ID.",
            responses=TreatmentStateSerializer,  # Serializer trả về dữ liệu
    ),
        create=extend_schema(
            tags=["app_treatment"],
            summary="Tạo trạng thái điều trị mới",
            description="API để tạo một trạng thái điều trị mới.",
            request={
                "application/json": {
                    "name": "Trạng thái 1",
                    "description": "Mô tả trạng thái 1",
                }
            },
            responses=TreatmentStateSerializer,  # Serializer trả về dữ liệu
        ),
        update=extend_schema(
            tags=["app_treatment"],
            summary="Cập nhật trạng thái điều trị",
            description="API để cập nhật thông tin của một trạng thái điều trị theo ID.",
            request={
                "application/json": {
                    "name": "Trạng thái 1",
                    "description": "Mô tả trạng thái 1",
                }
            },
            responses=TreatmentStateSerializer,  # Serializer trả về dữ liệu
        ),
        destroy=extend_schema(
            tags=["app_treatment"],
            summary="Xóa trạng thái điều trị",
            description="API để xóa một trạng thái điều trị (is_active=False).",
            responses={200: {"detail": "Đã xóa trạng thái điều trị (is_active=false)."}},
        )
    )

def customer_level_schema():
    return extend_schema_view(
        list=extend_schema(
            tags=["app_customer"],
            summary="Danh sách cấp độ khách hàng",
            description="Lấy danh sách tất cả các cấp độ khách hàng trong hệ thống.",
            parameters=[
                OpenApiParameter(name="searchTerm", description="Tìm kiếm theo tên cấp độ", required=False, type=str),
            ],
            responses=CustomerLevelSerializer,  # Serializer trả về dữ liệu
        ),
        retrieve=extend_schema(
            tags=["app_customer"],
            summary="Chi tiết cấp độ khách hàng",
            description="Lấy thông tin chi tiết của một cấp độ khách hàng theo ID.",
            responses=CustomerLevelSerializer,  # Serializer trả về dữ liệu
        ),
        create=extend_schema(
            tags=["app_customer"],
            summary="Tạo cấp độ khách hàng mới",
            description="API để tạo một cấp độ khách hàng mới.",
            request={
                "application/json": {
                    "name": "Cấp độ 1",
                    "description": "Mô tả cấp độ 1",
                    "color": "#FF0000",
                    "priority": 1,
                }
            },
            responses=CustomerLevelSerializer,  # Serializer trả về dữ liệu
        ),
        update=extend_schema(
            tags=["app_customer"],
            summary="Cập nhật cấp độ khách hàng",
            description="API để cập nhật thông tin của cấp độ khách hàng.",
            request={
                "application/json": {
                    "name": "Cấp độ 1",
                    "description": "Mô tả cấp độ 1",
                    "color": "#FF0000",
                    "priority": 1,
                }
            },
            responses=CustomerLevelSerializer,  # Serializer trả về dữ liệu
        ),
        destroy=extend_schema(
            tags=["app_customer"],
            summary="Xóa cấp độ khách hàng",
            description="API để xóa một cấp độ khách hàng (is_active=False).",
            responses={200: {"detail": "Đã xóa cấp độ khách hàng (is_active=false)."}},
        )
    )

def customer_schema():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách khách hàng",
            description="Lấy danh sách khách hàng với các bộ lọc và tìm kiếm.",
            parameters=[
                OpenApiParameter(name="startDate", description="Ngày bắt đầu (YYYY-MM-DD)", required=False, type=str),
                OpenApiParameter(name="endDate", description="Ngày kết thúc (YYYY-MM-DD)", required=False, type=str),
                OpenApiParameter(name="searchTerm", description="Tìm kiếm theo tên, mã khách hàng, marketer hoặc ghi chú", required=False, type=str),
                OpenApiParameter(name="main-status", description="Lọc theo trạng thái chính", required=False, type=int),
                OpenApiParameter(name="lead-status", description="Lọc theo trạng thái khách hàng chưa mua", required=False, type=int),
                OpenApiParameter(name="treatment-status", description="Lọc theo trạng thái khách hàng đã mua hoặc đang mua", required=False, type=int),
            ],
        ),
        retrieve=extend_schema(
            summary="Chi tiết khách hàng",
            description="Lấy thông tin chi tiết của một khách hàng dựa trên ID.",
        ),
        create=extend_schema(
            summary="Tạo mới khách hàng",
            description="Tạo một khách hàng mới với đầy đủ thông tin. Nếu khách hàng mới đến và nhập mã giới thiệu (referrer_code), hệ thống sẽ tự động liên kết khách đó với người giới thiệu.",
            request=CustomerSerializer,
            examples=[
                OpenApiExample(
                    name="Tạo khách hàng mới",
                    description="Ví dụ về request tạo khách hàng mới.",
                    request_only=True,
                    value={
                        "name": "Nguyễn Văn A",
                        "gender": "MA",
                        "birth": "1990-05-20",
                        "marketer": 2,
                        "mobile": "0912345678",
                        "email": "nguyenvana@example.com",
                        "city": "Hà Nội",
                        "district": "Ba Đình",
                        "ward": "Điện Biên",
                        "address": "Số 123, Đường ABC",
                        "source": 1,
                        "source_link": "https://example.com",
                        "contact_date": "2025-03-02",
                        "time_frame": 8,
                        "service": [1],
                        "main_status": "1",
                        "lead_status": 1,
                        "customer_request": [1, 2, 0],
                        "treatment_status": None,
                        "customer_problems": [
                            {
                                "problem": "tai nạn",
                                "encounter_pain": "gãy xương",
                                "desire": "cần nhiều chân"
                            }
                        ],
                        "referrer_code": "ABC123",
                        "is_active": True
                    }
                )
            ],
            responses={201: CustomerSerializer},
        ),
        update=extend_schema(
            summary="Cập nhật thông tin khách hàng",
            description="Cập nhật thông tin khách hàng theo ID. Nếu cần thay đổi người giới thiệu, gửi thêm referrer_code.",
            request=CustomerSerializer,
            responses={200: CustomerSerializer},
        ),
        partial_update=extend_schema(
            summary="Cập nhật một phần thông tin khách hàng",
            description="Chỉ cập nhật một số trường của khách hàng theo ID. Nếu cần thay đổi người giới thiệu, gửi thêm referrer_code.",
            request=CustomerSerializer,
            responses={200: CustomerSerializer},
        ),
        destroy=extend_schema(
            summary="Xóa khách hàng (đặt `is_active=false`)",
            description="Đánh dấu khách hàng là không hoạt động thay vì xóa khỏi cơ sở dữ liệu.",
            responses={200: {"description": "Đã xóa khách hàng (is_active=false)."}},
        ),
    )

def customer_care_schema():
    return extend_schema_view(
        list=extend_schema(
                tags=["app_customer"],
                summary="Danh sách chăm sóc khách hàng",
                parameters=[
                    OpenApiParameter(name="startDate", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
                    OpenApiParameter(name="endDate",   type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
                    OpenApiParameter(name="searchTerm", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
                    OpenApiParameter(name="type", description="CSV (incoming,outgoing)", type=OpenApiTypes.STR,
                                    location=OpenApiParameter.QUERY, style="form", explode=False),
                ],
                responses={200: OpenApiResponse(response=CustomerCareSerializer(many=True))}
            ),
        retrieve=extend_schema(
            tags=["app_customer"],
            summary="Chi tiết dịch vụ chăm sóc khách hàng",
            description="Lấy thông tin chi tiết của yêu cầu chăm sóc khách hàng theo ID.",
            responses={
                200: OpenApiResponse(
                    description="Chi tiết yêu cầu chăm sóc khách hàng",
                    response=CustomerCareSerializer,
                    examples=[
                        OpenApiExample(
                            "Chi tiết yêu cầu chăm sóc",
                            value={
                                "id": 1,
                                "date": "2025-03-03",
                                "note": "Gọi lại khách hàng",
                                "type": "incoming",
                                "customer": 1,
                                "customer_name": "John Doe",
                                "customer_mobile": "1234567890"
                            }
                        )
                    ]
                ),
                404: OpenApiResponse(description="Không tìm thấy yêu cầu chăm sóc khách hàng"),
            }
        ),
        create=extend_schema(
            tags=["app_customer"],
            summary="Tạo yêu cầu chăm sóc khách hàng mới",
            description="API để tạo một yêu cầu chăm sóc khách hàng mới.",
            request=CustomerCareSerializer,
            responses={
                201: OpenApiResponse(
                    description="Yêu cầu chăm sóc được tạo thành công",
                    response=CustomerCareSerializer,
                    examples=[
                        OpenApiExample(
                            "Yêu cầu chăm sóc mới",
                            value={
                                "id": 1,
                                "date": "2025-03-03",
                                "note": "Gọi lại khách hàng",
                                "type": "incoming",
                                "customer": 1,
                                "customer_name": "John Doe",
                                "customer_mobile": "1234567890"
                            }
                        )
                    ]
                ),
                400: OpenApiResponse(description="Dữ liệu đầu vào không hợp lệ"),
            },
            examples=[
                OpenApiExample(
                    "Tạo yêu cầu chăm sóc khách hàng",
                    summary="Ví dụ tạo yêu cầu",
                    value={
                        "date": "2025-03-03",
                        "note": "Gọi lại khách hàng",
                        "type": "incoming",
                        "customer": 1
                    }
                )
            ]
        ),
        update=extend_schema(
            tags=["app_customer"],
            summary="Cập nhật yêu cầu chăm sóc khách hàng",
            description="API để cập nhật thông tin của yêu cầu chăm sóc khách hàng theo ID.",
            request=CustomerCareSerializer,
            responses={
                200: OpenApiResponse(
                    description="Yêu cầu chăm sóc được cập nhật thành công",
                    response=CustomerCareSerializer,
                    examples=[
                        OpenApiExample(
                            "Yêu cầu chăm sóc đã cập nhật",
                            value={
                                "id": 1,
                                "date": "2025-03-03",
                                "note": "Đã gọi lại khách hàng",
                                "type": "incoming",
                                "customer": 1,
                                "customer_name": "John Doe",
                                "customer_mobile": "1234567890"
                            }
                        )
                    ]
                ),
                400: OpenApiResponse(description="Dữ liệu đầu vào không hợp lệ"),
                404: OpenApiResponse(description="Không tìm thấy yêu cầu chăm sóc khách hàng"),
            },
            examples=[
                OpenApiExample(
                    "Cập nhật yêu cầu chăm sóc khách hàng",
                    summary="Ví dụ cập nhật yêu cầu",
                    value={
                        "date": "2025-03-03",
                        "note": "Đã gọi lại khách hàng",
                        "type": "incoming",
                        "customer": 1
                    }
                )
            ]
        ),
        partial_update=extend_schema(
            tags=["app_customer"],
            summary="Cập nhật một phần yêu cầu chăm sóc khách hàng",
            description="API để cập nhật một phần thông tin của yêu cầu chăm sóc khách hàng theo ID.",
            request=CustomerCareSerializer,
            responses={
                200: OpenApiResponse(
                    description="Yêu cầu chăm sóc được cập nhật một phần thành công",
                    response=CustomerCareSerializer
                ),
                400: OpenApiResponse(description="Dữ liệu đầu vào không hợp lệ"),
                404: OpenApiResponse(description="Không tìm thấy yêu cầu chăm sóc khách hàng"),
            }
        ),
        destroy=extend_schema(
            tags=["app_customer"],
            summary="Xóa yêu cầu chăm sóc khách hàng",
            description="API để xóa một yêu cầu chăm sóc khách hàng (thực tế không xóa mà đặt is_active=False nếu có logic tương ứng).",
            responses={
                200: OpenApiResponse(
                    description="Yêu cầu chăm sóc đã được xóa (is_active=False)",
                    examples=[
                        OpenApiExample(
                            "Kết quả xóa",
                            value={"detail": "Đã xóa yêu cầu chăm sóc khách hàng (is_active=false)."}
                        )
                    ]
                ),
                404: OpenApiResponse(description="Không tìm thấy yêu cầu chăm sóc khách hàng"),
            }
        )
    )
def feedback_schema():
    return extend_schema_view(
        list=extend_schema(
            tags=["app_customer"],
            description="Retrieve a paginated list of feedback records with optional filtering.",
            parameters=[
                OpenApiParameter(
                    name='startDate',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Filter feedback by start date (YYYY-MM-DD)',
                    required=False
                ),
                OpenApiParameter(
                    name='endDate',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Filter feedback by end date (YYYY-MM-DD)',
                    required=False
                ),
                OpenApiParameter(
                    name='searchTerm',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Search feedback by name, source name, source link, mobile, or email',
                    required=False
                ),
                OpenApiParameter(
                    name='format',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Filter feedback by format',
                    required=False
                ),
            ],
            responses={
                200: OpenApiResponse(
                    description="A paginated list of feedback records",
                    response=FeedBackSerializer(many=True),
                    examples=[
                        OpenApiExample(
                            "List Feedback Example",
                            value={
                                "count": 1,
                                "next": None,
                                "previous": None,
                                "results": [
                                    {
                                        "id": 1,
                                        "name": "John Doe",
                                        "source": 1,
                                        "source_name": "Website",
                                        "source_link": "https://example.com",
                                        "format": "online",
                                        "gender": "M",
                                        "email": "john@example.com",
                                        "mobile": "1234567890",
                                        "service": [1],
                                        "service_names": ["Consulting"],
                                        "satification_level": 4,
                                        "service_quality": 5,
                                        "examination_quality": 4,
                                        "serve_quality": 5,
                                        "customercare_quality": 4,
                                        "unsatify_note": "Slow response",
                                        "suggest_note": "Improve response time",
                                        "created": "2025-02-28T12:00:00Z"
                                    }
                                ]
                            }
                        )
                    ]
                ),
                400: OpenApiResponse(description="Bad request due to invalid parameters")
            }
        ),
        retrieve=extend_schema(
            tags=["app_customer"],
            description="Retrieve a specific feedback record by ID",
            responses={
                200: OpenApiResponse(
                    description="Feedback retrieved successfully",
                    response=FeedBackSerializer,
                    examples=[
                        OpenApiExample(
                            "Retrieve Feedback Example",
                            value={
                                "id": 1,
                                "name": "John Doe",
                                "source": 1,
                                "source_name": "Website",
                                "source_link": "https://example.com",
                                "format": "online",
                                "gender": "M",
                                "email": "john@example.com",
                                "mobile": "1234567890",
                                "service": [1],
                                "service_names": ["Consulting"],
                                "satification_level": 4,
                                "service_quality": 5,
                                "examination_quality": 4,
                                "serve_quality": 5,
                                "customercare_quality": 4,
                                "unsatify_note": "Slow response",
                                "suggest_note": "Improve response time",
                                "created": "2025-02-28T12:00:00Z"
                            }
                        )
                    ]
                ),
                404: OpenApiResponse(description="Không tìm thấy FeedBack")
            }
        ),
        create=extend_schema(
            tags=["app_customer"],
            description="Tạo một bản feedback mới",
            request=FeedBackSerializer,
            responses={
                201: OpenApiResponse(
                    description="Feedback created successfully",
                    response=FeedBackSerializer,
                    examples=[
                        OpenApiExample(
                            "Create Feedback Example",
                            value={
                                "id": 1,
                                "name": "John Doe",
                                "source": 1,
                                "source_name": "Website",
                                "source_link": "https://example.com",
                                "format": "online",
                                "gender": "M",
                                "email": "john@example.com",
                                "mobile": "1234567890",
                                "service": [1],
                                "service_names": ["Consulting"],
                                "satification_level": 4,
                                "service_quality": 5,
                                "examination_quality": 4,
                                "serve_quality": 5,
                                "customercare_quality": 4,
                                "unsatify_note": "Slow response",
                                "suggest_note": "Improve response time",
                                "created": "2025-02-28T12:00:00Z"
                            }
                        )
                    ]
                ),
                400: OpenApiResponse(description="Không tạo được FeedBack do dữ liệu không hợp lệ")
            },
            examples=[
                OpenApiExample(
                    "Create Feedback Request",
                    value={
                        "name": "John Doe",
                        "source": 1,
                        "source_link": "https://example.com",
                        "format": "online",
                        "gender": "M",
                        "email": "john@example.com",
                        "mobile": "1234567890",
                        "service": [1],
                        "satification_level": 4,
                        "service_quality": 5,
                        "examination_quality": 4,
                        "serve_quality": 5,
                        "customercare_quality": 4,
                        "unsatify_note": "Slow response",
                        "suggest_note": "Improve response time"
                    }
                )
            ]
        ),
        update=extend_schema(
            tags=["app_customer"],
            description="Cập nhật một bản feedback",
            request=FeedBackSerializer,
            responses={
                200: OpenApiResponse(
                    description="Feedback updated successfully",
                    response=FeedBackSerializer
                ),
                400: OpenApiResponse(description="Invalid input data"),
                404: OpenApiResponse(description="Feedback not found")
            }
        ),
        partial_update=extend_schema(
            tags=["app_customer"],
            description="Partially update an existing feedback record",
            request=FeedBackSerializer,
            responses={
                200: OpenApiResponse(
                    description="Feedback partially updated successfully",
                    response=FeedBackSerializer
                ),
                400: OpenApiResponse(description="Invalid input data"),
                404: OpenApiResponse(description="Feedback not found")
            }
        ),
        destroy=extend_schema(
            tags=["app_customer"],
            description="Xóa 1 bản feedback record",
            responses={
                204: OpenApiResponse(description="Feedback xóa thành công"),
                404: OpenApiResponse(description="Feedback not found")
            }
        )
    )