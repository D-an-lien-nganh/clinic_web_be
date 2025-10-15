from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter,OpenApiExample,OpenApiResponse
from rest_framework import status
from .serializers import *

def booking_schema():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách Booking",
            description="Trả về danh sách Booking với bộ lọc thời gian, từ khóa và trạng thái trị liệu.",
            parameters=[
                OpenApiParameter(name="startDate", description="Lọc theo ngày bắt đầu (YYYY-MM-DD)", required=False, type=str),
                OpenApiParameter(name="endDate", description="Lọc theo ngày kết thúc (YYYY-MM-DD)", required=False, type=str),
                OpenApiParameter(name="searchTerm", description="Tìm theo tên/mã KH, username người tạo, hoặc ghi chú", required=False, type=str),
                OpenApiParameter(name="is_treatment", description="Lọc theo trạng thái trị liệu (true/false)", required=False, type=bool),
                OpenApiParameter(name="type", description="Lọc theo loại booking (examination, in_treatment, re_examination). Có thể truyền nhiều: ?type=a&type=b hoặc ?type=a,b", required=False, type=str),
            ]
        ),
        retrieve=extend_schema(
            summary="Chi tiết Booking",
            description="Trả về thông tin chi tiết của một Booking theo ID."
        ),
        create=extend_schema(
            summary="Tạo Booking mới",
            description=(
                "Tạo mới Booking. Các trường chính:\n"
                "- customer (bắt buộc)\n"
                "- type: examination | in_treatment | re_examination (mặc định examination)\n"
                "- note (tuỳ chọn)\n"
                "- receiving_day (yyyy-mm-dd) & set_date (hh:mm) nếu muốn hẹn lịch\n"
            ),
            request=BookingSerializer,
            examples=[
                OpenApiExample(
                    name="Ví dụ tạo Booking khám",
                    value={
                        "customer": 1,
                        "type": "examination",
                        "note": "Khách hàng đến khám lần đầu",
                        "receiving_day": "2025-08-30",
                        "set_date": "09:30"
                    },
                    request_only=True
                ),
                OpenApiExample(
                    name="Ví dụ tạo Booking trị liệu",
                    value={
                        "customer": 1,
                        "type": "in_treatment",
                        "note": "Buổi trị liệu 1",
                        "receiving_day": "2025-08-31",
                        "set_date": "14:00"
                    },
                    request_only=True
                )
            ]
        ),
        update=extend_schema(
            summary="Cập nhật Booking",
            description="Cập nhật thông tin một Booking."
        ),
        destroy=extend_schema(
            summary="Xóa Booking",
            description="Xóa một Booking."
        ),
        update_has_come=extend_schema(
            summary="Cập nhật trạng thái has_come",
            description="Đánh dấu khách hàng đã đến (has_come=True) nếu trước đó chưa cập nhật.",
            responses={
                200: OpenApiExample(name="Thành công", value={"message": "Cập nhật has_come thành công."}),
                400: OpenApiExample(name="Đã cập nhật trước đó", value={"error": "Trạng thái has_come đã được cập nhật trước đó."})
            }
        )
    )

def doctor_process_schema():
    return extend_schema_view(
    list=extend_schema(
        summary="Danh sách đơn thuốc",
        description="Trả về danh sách các đơn thuốc đã tạo sau khi khám lâm sàng.",
    ),
    retrieve=extend_schema(
        summary="Chi tiết đơn thuốc",
        description="Lấy chi tiết đơn thuốc theo ID.",
    ),
    create=extend_schema(
        summary="Tạo mới đơn thuốc",
        description="""
        Tạo đơn thuốc cho khách hàng đã hoàn thành khám lâm sàng. 
        Bao gồm danh sách thuốc, liều lượng, đơn vị và ghi chú.
        """,
        request={
            "application/json": {
                "example": {
                    "customer_id": 3,
                    "start_time": "2025-07-28T10:45:00Z",
                    "end_time": "2025-07-28T11:15:00Z",
                    "medicine_discount": 2,
                    "diagnosis_medicines": [
                        {
                            "product": 8,
                            "quantity": 2,
                            "unit": 1,
                            "dose": "2 viên/lần x 3 lần/ngày",
                            "note": "Uống sau ăn",
                            "price": "50000.00"
                        },
                        {
                            "product": 9,
                            "quantity": 1,
                            "unit": 1,
                            "dose": "1 viên/ngày",
                            "note": "",
                            "price": "70000.00"
                        }
                    ]
                }
            }
        }
    ),
    update=extend_schema(
        summary="Cập nhật đơn thuốc",
        description="Chỉnh sửa thông tin đơn thuốc và danh sách thuốc nếu chưa thanh toán.",
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần đơn thuốc",
        description="Chỉnh sửa một phần nội dung đơn thuốc.",
    ),
    destroy=extend_schema(
        summary="Xóa đơn thuốc",
        description="Xóa đơn thuốc nếu chưa có dữ liệu chỉ định hoặc chưa thanh toán."
    )
)
def service_assign_schema():
    return extend_schema_view(
        list=extend_schema(
            tags=["app_treatment"],
            summary="Danh sách chỉ định dịch vụ",
            description="Lấy danh sách tất cả chỉ định dịch vụ.",
            parameters=[
                OpenApiParameter(name="searchTerm", description="(tuỳ chọn) Từ khóa tìm kiếm", required=False, type=str),
            ],
            responses=ServiceAssignSerializer(many=True),
        ),
        retrieve=extend_schema(
            tags=["app_treatment"],
            summary="Chi tiết chỉ định dịch vụ",
            description="Xem chi tiết một chỉ định dịch vụ theo ID.",
            responses=ServiceAssignSerializer,
        ),
        create=extend_schema(
            tags=["app_treatment"],
            summary="Tạo chỉ định dịch vụ",
            description="Chỉ định nhiều dịch vụ cho một quy trình bác sĩ (DoctorProcess).",
            request=ServiceAssignSerializer,
            examples=[
                OpenApiExample(
                    name="Chỉ định qua DoctorProcess",
                    value={
                        "doctor_process_id": 1,
                        "assigned_expert": 2,
                        "treatment_method": "Phác đồ ví dụ",
                        "service_discount": 1,
                        "diagnosis_services": [
                            {"service": 1, "quantity": 2},
                            {"service": 3, "quantity": 1}
                        ]
                    },
                    request_only=True
                )
            ]
        ),
        update=extend_schema(
            tags=["app_treatment"],
            summary="Cập nhật chỉ định dịch vụ",
            description="Cập nhật thông tin chỉ định dịch vụ.",
            request=ServiceAssignSerializer,
            responses=ServiceAssignSerializer,
        )
    )
def bill_schema():
    return extend_schema_view(
        list=extend_schema(
            tags=["app_treatment"],
            summary="Danh sách bill",
            description="Lấy danh sách bill (lọc theo ngày tạo).",
            parameters=[
                OpenApiParameter(name="startDate", description="Ngày bắt đầu (YYYY-MM-DD)", required=False, type=str),
                OpenApiParameter(name="endDate", description="Ngày kết thúc (YYYY-MM-DD)", required=False, type=str),
                OpenApiParameter(name="customer_id", description="Lọc theo khách hàng", required=False, type=int),
            ],
        ),
        create=extend_schema(
            tags=["app_treatment"],
            summary="Tạo bill",
            description="Tạo hóa đơn mới. Bill liên kết trực tiếp tới Customer.",
            request=BillListSerializer,
            responses={201: BillListSerializer},
            examples=[
                OpenApiExample(
                    name="Ví dụ tạo bill",
                    value={
                        "user": 1,
                        "customer": 2,
                        "paid_ammount": "500000.00",
                        "method": "cash",
                        "note": "Thanh toán đợt 1"
                    },
                    request_only=True
                ),
            ]
        ),
    )

def nurse_process_schema():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách quy trình y tá",
            description="Lấy danh sách các quy trình y tá; hỗ trợ tìm theo tên/mã/số ĐT/email khách hàng.",
            parameters=[
                OpenApiParameter(name="searchTerm", description="Từ khóa tìm kiếm", required=False, type=str),
                OpenApiParameter(name="is_treatment", description="Lọc theo trạng thái trị liệu (true/false).", required=False, type=bool),
            ],
            responses={200: DoctorHealthCheckSerializer(many=True)},
        ),
        retrieve=extend_schema(
            summary="Chi tiết quy trình y tá",
            description="Lấy thông tin chi tiết quy trình y tá theo ID.",
            responses={200: DoctorHealthCheckSerializer},
        ),
        create=extend_schema(
            summary="Tạo mới quy trình y tá",
            description="Tạo một quy trình y tá mới cho khách hàng.",
            request=DoctorHealthCheckSerializer,
            responses={201: DoctorHealthCheckSerializer, 400: OpenApiResponse(description="Lỗi khi tạo")},
        ),
        update=extend_schema(
            summary="Cập nhật quy trình y tá",
            description="Cập nhật quy trình y tá.",
            request=DoctorHealthCheckSerializer,
            responses={200: DoctorHealthCheckSerializer, 400: OpenApiResponse(description="Không thể cập nhật")},
        ),
        partial_update=extend_schema(
            summary="Cập nhật một phần quy trình y tá",
            description="Cập nhật một phần quy trình y tá.",
            request=DoctorHealthCheckSerializer,
            responses={200: DoctorHealthCheckSerializer, 400: OpenApiResponse(description="Không thể cập nhật")},
        ),
        destroy=extend_schema(
            summary="Xóa quy trình y tá",
            description="Xóa quy trình y tá.",
            responses={204: OpenApiResponse(description="Xóa thành công"), 400: OpenApiResponse(description="Không thể xóa")},
        ),
    )

def payment_history_schema():
    return extend_schema_view(
        list=extend_schema(
            tags=["app_treatment"],
            summary="Danh sách lịch sử thanh toán",
            description="Lấy danh sách lịch sử thanh toán của khách hàng, có thể lọc theo từ khóa tìm kiếm, trạng thái thanh toán, và khoảng thời gian.",
            parameters=[
                OpenApiParameter(name='startDate', description='Lọc theo ngày bắt đầu', required=False, type=str),
                OpenApiParameter(name='endDate', description='Lọc theo ngày kết thúc', required=False, type=str),
                OpenApiParameter(name='bill_id', description='Lọc theo ID hóa đơn', required=False, type=int),
                OpenApiParameter(name='paid_method', description='Lọc theo phương thức thanh toán', required=False, type=str),

            ],
            responses={200: PaymentHistorySerializer(many=True)},
        ),
        retrieve=extend_schema(
            tags=["app_treatment"],
            summary="Chi tiết lịch sử thanh toán",
            description="Lấy thông tin chi tiết của một lịch sử thanh toán theo ID.",
            responses={200: PaymentHistorySerializer},
        ),
        create=extend_schema(
            tags=["app_treatment"],
            summary="Tạo mới lịch sử thanh toán",
            description="paid_method: cash, transfer; paid_type: service, product, both",
            request=PaymentHistorySerializer,
            responses={201: PaymentHistorySerializer, 400: OpenApiResponse(description="Lỗi khi tạo")},
        ),
        update=extend_schema(
            tags=["app_treatment"],
            summary="Không dùng API này",
        ),
        partial_update=extend_schema(
            tags=["app_treatment"],
            summary="Không dùng API này",
        ),
        destroy=extend_schema(
            tags=["app_treatment"],
            summary="Không dùng API này",
        ),
    )
def treatment_request_schema():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách yêu cầu trị liệu",
            description="Lấy danh sách tất cả yêu cầu trị liệu.",
            responses={200: TreatmentRequestSerializer(many=True)}
        ),
        retrieve=extend_schema(
            summary="Chi tiết yêu cầu trị liệu",
            description="Lấy thông tin chi tiết của một yêu cầu trị liệu theo ID.",
            responses={200: TreatmentRequestSerializer}
        ),
        create=extend_schema(
            summary="Tạo mới yêu cầu trị liệu",
            description="Tạo một yêu cầu trị liệu mới, bao gồm danh sách buổi trị liệu và các kỹ thuật liên quan.",
            request=TreatmentRequestSerializer,
            examples=[
                OpenApiExample(
                    name="Tạo yêu cầu trị liệu mới",
                    value={
                        "service_id": 1,
                        "bill": 5,
                        "note": "Phác đồ điều trị giảm đau vai gáy",
                        "sessions": [
                            {
                                "note": "Buổi 1 - Khởi động",
                                "techniques": [
                                    {
                                        "techical_setting_id": 2,
                                        "expert_ids": [3, 4]
                                    },
                                    {
                                        "techical_setting_id": 3,
                                        "expert_ids": [5]
                                    }
                                ]
                            },
                            {
                                "note": "Buổi 2 - Điều trị chuyên sâu",
                                "techniques": [
                                    {
                                        "techical_setting_id": 4,
                                        "expert_ids": [6]
                                    }
                                ]
                            }
                        ]
                    },
                    summary="Dữ liệu mẫu gửi lên khi tạo yêu cầu trị liệu",
                    request_only=True
                )
            ],
            responses={201: TreatmentRequestSerializer}
        )
    )